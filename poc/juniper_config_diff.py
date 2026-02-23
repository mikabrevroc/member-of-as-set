#!/usr/bin/env python3

import subprocess
import re
import difflib
from typing import Set, Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from irr_cache import get_cached, set_cached


@dataclass
class ASSET:
    name: str
    members: List[str]
    source: str


def fetch_asset_whois(asset_name: str, server: str = "whois.radb.net") -> Optional[ASSET]:
    try:
        result = subprocess.run(
            ["whois", "-h", server, asset_name],
            capture_output=True, text=True, timeout=10
        )
        
        if result.returncode != 0:
            return None
        
        lines = result.stdout.split('\n')
        members = []
        source = "UNKNOWN"
        
        in_members = False
        for raw_line in lines:
            line = raw_line.strip()
            
            if line.startswith('source:'):
                source = line.split(':', 1)[1].strip()
            
            if line.startswith('members:'):
                in_members = True
                member_str = line.split(':', 1)[1].strip()
                members.extend(parse_members(member_str))
            elif in_members:
                if not line:
                    in_members = False
                elif raw_line and raw_line[0].isupper() and not raw_line.startswith(' '):
                    in_members = False
                else:
                    members.extend(parse_members(line))
        
        return ASSET(name=asset_name, members=members, source=source)
        
    except Exception as e:
        print(f"Error fetching {asset_name}: {e}")
        return None


def parse_members(member_str: str) -> List[str]:
    members = []
    for part in member_str.split(','):
        member = part.strip()
        if member:
            members.append(member)
    return members


def is_asn(member: str) -> bool:
    return bool(re.match(r'^AS\d+$', member))


def expand_asset(asset_name: str, max_depth: int = 5, 
                seen: Set[str] = None) -> Tuple[Set[int], Set[str], List[dict]]:
    if seen is None:
        seen = set()
    
    if asset_name in seen:
        return set(), set(), [{"asset": asset_name, "action": "circular_skip"}]
    
    if max_depth <= 0:
        return set(), set(), [{"asset": asset_name, "action": "max_depth"}]
    
    seen.add(asset_name)
    
    asset = fetch_asset_whois(asset_name)
    if not asset:
        return set(), set(), [{"asset": asset_name, "action": "not_found"}]
    
    asns = set()
    nested_sets = set()
    log = [{"asset": asset_name, "source": asset.source, "action": "expanded"}]
    
    for member in asset.members:
        if is_asn(member):
            asns.add(int(member[2:]))
        elif member.startswith('AS'):
            nested_sets.add(member)
            sub_asns, sub_sets, sub_log = expand_asset(member, max_depth - 1, seen)
            asns.update(sub_asns)
            nested_sets.update(sub_sets)
            log.extend(sub_log)
    
    return asns, nested_sets, log


def generate_peer_config(peer_name: str, peer_asn: int, allowed_asns: Set[int]) -> str:
    lines = [
        f"# Standard import policy for {peer_name} (AS{peer_asn})",
        f"# Generated from AS-GOOGLE expansion",
        "",
        f"policy-statement AS{peer_asn}-in {{",
        "    term as-path-allow {",
        "        from {",
    ]
    
    if allowed_asns:
        lines.append(f"            as-path-group AS{peer_asn}-customers;")
    
    lines.extend([
        "        }",
        "        then accept;",
        "    }",
        "    term reject {",
        "        then reject;",
        "    }",
        "}",
        "",
        f"as-path-group AS{peer_asn}-customers {{",
    ])
    
    for asn in sorted(allowed_asns):
        lines.append(f'    as-path AS{peer_asn}-customers-{asn} ".* {asn} .*";')
    
    lines.append("}")
    
    return "\n".join(lines)


def generate_peerlock_config(peer_name: str, peer_asn: int, blocked_asns: Set[int]) -> str:
    lines = [
        f"# Peer-lock import policy for {peer_name} (AS{peer_asn})",
        f"# Google (AS-GOOGLE) sets propagation=directOnly",
        f"# Blocks {len(blocked_asns)} Google ASNs from this peer",
        "",
        f"as-path-group AS{peer_asn}-peerlock {{",
    ]
    
    for asn in sorted(blocked_asns):
        lines.append(f'    as-path block-google-{asn} ".* {asn} .*";')
    
    lines.extend([
        "}",
        "",
        f"policy-statement AS{peer_asn}-in-peerlock {{",
        "    term reject-google {",
        "        from {",
        f"            as-path-group AS{peer_asn}-peerlock;",
        "        }",
        "        then reject;",
        "    }",
        "    term accept-others {",
        "        then accept;",
        "    }",
        "}",
        "",
        f"# Apply to {peer_name} import policy chain:",
        f"# import [ AS{peer_asn}-in-peerlock AS{peer_asn}-in ]",
    ])
    
    return "\n".join(lines)


def main():
    print("=" * 70)
    print("JUNIPER CONFIG COMPARISON: Without vs With RASA")
    print("=" * 70)
    print()
    
    # Fetch AS-GOOGLE
    print("Fetching AS-GOOGLE from IRR...")
    google_asns, google_sets, google_log = expand_asset("AS-GOOGLE", max_depth=1)
    print(f"Found {len(google_asns)} Google ASNs\n")
    
    peers = [
        {"name": "Hurricane Electric", "asn": 6939},
        {"name": "Arelion", "asn": 1299},
    ]
    
    # Config 1: WITHOUT RASA (baseline)
    print("-" * 70)
    print("CONFIG 1: WITHOUT RASA (baseline)")
    print("-" * 70)
    
    config_without_rasa = []
    config_without_rasa.append("# Juniper JunOS Configuration")
    config_without_rasa.append("# Generated: Standard IRR expansion without RASA")
    config_without_rasa.append("# Source: AS-GOOGLE")
    config_without_rasa.append("")
    
    for peer in peers:
        config_without_rasa.append(generate_peer_config(
            peer_name=peer["name"],
            peer_asn=peer["asn"],
            allowed_asns=google_asns
        ))
        config_without_rasa.append("")
    
    without_rasa_text = "\n".join(config_without_rasa)
    print(without_rasa_text[:1500])
    print("...")
    
    # Config 2: WITH RASA (peer-lock)
    print("\n" + "-" * 70)
    print("CONFIG 2: WITH RASA (peer-lock applied)")
    print("-" * 70)
    
    config_with_rasa = []
    config_with_rasa.append("# Juniper JunOS Configuration")
    config_with_rasa.append("# Generated: IRR expansion with RASA authorization")
    config_with_rasa.append("# Google sets propagation=directOnly for AS-GOOGLE")
    config_with_rasa.append("")
    
    for peer in peers:
        config_with_rasa.append(generate_peerlock_config(
            peer_name=peer["name"],
            peer_asn=peer["asn"],
            blocked_asns=google_asns
        ))
        config_with_rasa.append("")
    
    with_rasa_text = "\n".join(config_with_rasa)
    print(with_rasa_text[:1500])
    print("...")
    
    # Write files
    without_file = "juniper_without_rasa.conf"
    with_file = "juniper_with_rasa.conf"
    
    with open(without_file, 'w') as f:
        f.write(without_rasa_text)
    
    with open(with_file, 'w') as f:
        f.write(with_rasa_text)
    
    print(f"\n✓ Written: {without_file}")
    print(f"✓ Written: {with_file}")
    
    # Generate diff
    print("\n" + "=" * 70)
    print("DIFF: Without RASA vs With RASA")
    print("=" * 70)
    print()
    
    without_lines = without_rasa_text.splitlines(keepends=True)
    with_lines = with_rasa_text.splitlines(keepends=True)
    
    diff = list(difflib.unified_diff(
        without_lines,
        with_lines,
        fromfile=without_file,
        tofile=with_file,
        lineterm=''
    ))
    
    if diff:
        for line in diff[:100]:
            print(line.rstrip())
        if len(diff) > 100:
            print(f"\n... ({len(diff) - 100} more lines)")
    else:
        print("No differences found")
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print()
    print(f"Configuration without RASA:")
    print(f"  - File: {without_file}")
    print(f"  - Lines: {len(without_rasa_text.splitlines())}")
    print(f"  - Policy: Accept all {len(google_asns)} Google ASNs from peers")
    print()
    print(f"Configuration with RASA:")
    print(f"  - File: {with_file}")
    print(f"  - Lines: {len(with_rasa_text.splitlines())}")
    print(f"  - Policy: Reject all {len(google_asns)} Google ASNs from peers (directOnly)")
    print()
    print("Peers affected:")
    for peer in peers:
        print(f"  - {peer['name']} (AS{peer['asn']})")
    print()
    print("RASA impact: Peer-lock applied to prevent Google route propagation")


if __name__ == "__main__":
    main()
