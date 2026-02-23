#!/usr/bin/env python3
"""
Real RASA Pipeline using live IRR data via WHOIS.
Fetches actual AS-SETs and generates real JunOS configs.
"""

import subprocess
import re
import sys
from typing import Set, Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class ASSET:
    name: str
    members: List[str]
    source: str


def fetch_asset_whois(asset_name: str, server: str = "whois.radb.net") -> Optional[ASSET]:
    """Fetch AS-SET from IRR via WHOIS."""
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
                # Check if this is a continuation line (starts with whitespace in raw)
                # or if it's a new field (starts with uppercase letter at column 0)
                if not line:
                    in_members = False
                elif raw_line and raw_line[0].isupper() and not raw_line.startswith(' '):
                    in_members = False
                else:
                    members.extend(parse_members(line))
        
        return ASSET(name=asset_name, members=members, source=source)
        
    except Exception as e:
        print(f"Error fetching {asset_name}: {e}", file=sys.stderr)
        return None


def parse_members(member_str: str) -> List[str]:
    """Parse member list from WHOIS format."""
    members = []
    for part in member_str.split(','):
        member = part.strip()
        if member:
            members.append(member)
    return members


def is_asn(member: str) -> bool:
    """Check if member is an ASN (AS12345) not an AS-SET."""
    return bool(re.match(r'^AS\d+$', member))


def expand_asset(asset_name: str, max_depth: int = 5, 
                seen: Set[str] = None) -> Tuple[Set[int], Set[str], List[dict]]:
    """
    Recursively expand AS-SET to get all ASNs.
    Returns (asns, nested_sets, log).
    """
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
            # Recursively expand
            sub_asns, sub_sets, sub_log = expand_asset(member, max_depth - 1, seen)
            asns.update(sub_asns)
            nested_sets.update(sub_sets)
            log.extend(sub_log)
    
    return asns, nested_sets, log


class RASAFilter:
    def __init__(self, rasa_db: Dict):
        self.rasa_db = rasa_db
    
    def check_auth(self, asn: int, asset: str) -> Tuple[bool, str]:
        key = f"AS{asn}"
        auth = self.rasa_db.get(key)
        
        if not auth:
            return True, "No RASA (allow)"
        
        for entry in auth.get("authorizedIn", []):
            if entry.get("asSetName") == asset:
                return True, f"Authorized ({entry.get('propagation', 'unrestricted')})"
        
        if auth.get("strictMode"):
            return False, "REJECTED (strictMode)"
        
        return False, "REJECTED (not authorized)"
    
    def filter_asns(self, asset: str, asns: Set[int]) -> Tuple[Set[int], List[dict]]:
        authorized = set()
        log = []
        
        for asn in sorted(asns):
            is_auth, reason = self.check_auth(asn, asset)
            log.append({"asn": asn, "authorized": is_auth, "reason": reason})
            if is_auth:
                authorized.add(asn)
        
        return authorized, log


def generate_junos_as_path(asns: Set[int], name: str) -> str:
    if not asns:
        return f"as-path-group {name} {{\n    as-path {name}-empty \"^$\";\n}}"
    
    lines = [f"as-path-group {name} {{"]
    for asn in sorted(asns):
        lines.append(f'    as-path {name}-{asn} ".* {asn} .*";')
    lines.append("}")
    return "\n".join(lines)


def generate_junos_peer_filter(peer_asn: int, allowed_asns: Set[int]) -> str:
    """Generate JunOS policy-statement for a peer."""
    name = f"AS{peer_asn}"
    as_list = sorted(allowed_asns)
    
    lines = [
        f"policy-statement {name}-in {{",
        "    term as-path-allow {",
        "        from {"
    ]
    
    if as_list:
        lines.append(f"            as-path-group {name}-customers;")
    
    lines.extend([
        "        }",
        "        then accept;",
        "    }",
        "    term reject {",
        "        then reject;",
        "    }",
        "}",
        "",
        generate_junos_as_path(allowed_asns, f"{name}-customers")
    ])
    
    return "\n".join(lines)


def main():
    print("=" * 70)
    print("REAL RASA PIPELINE - Using live IRR data")
    print("=" * 70)
    
    # Fetch real AS-SET
    asset_name = "AS2914:AS-US"
    print(f"\nFetching {asset_name} from IRR...")
    
    # Limit depth to avoid timeout - depth 1 = direct members only
    asns, nested, log = expand_asset(asset_name, max_depth=1)
    
    print(f"Found {len(asns)} ASNs, {len(nested)} nested AS-SETs")
    print(f"Nested AS-SETs: {sorted(nested)[:5]}...")
    print(f"Sample ASNs: {sorted(asns)[:20]}...")
    
    # Scenario: Apply RASA filtering
    print("\n" + "=" * 70)
    print("SCENARIO: Some customers publish RASA-AUTH")
    print("=" * 70)
    
    # Mock RASA database - some ASNs authorize inclusion
    rasa_db = {
        "AS3949": {
            "authorizedAS": 3949,
            "authorizedIn": [{"asSetName": asset_name, "propagation": "unrestricted"}],
            "strictMode": False
        },
        # Most ASNs don't publish RASA - they're included by default
    }
    
    # Apply filtering
    rasa = RASAFilter(rasa_db)
    authorized, auth_log = rasa.filter_asns(asset_name, asns)
    
    print(f"\nRASA Authorization Results:")
    for entry in auth_log[:10]:
        status = "✓" if entry["authorized"] else "✗"
        print(f"  {status} AS{entry['asn']}: {entry['reason']}")
    if len(auth_log) > 10:
        print(f"  ... and {len(auth_log) - 10} more")
    
    print(f"\nFinal: {len(authorized)} of {len(asns)} ASNs authorized")
    
    # Generate JunOS config
    print("\n" + "=" * 70)
    print("GENERATED JUNOS CONFIGURATION")
    print("=" * 70)
    
    config = generate_junos_peer_filter(6939, authorized)  # Hurricane Electric peer
    print("\nFor peer Hurricane Electric (AS6939):")
    print("-" * 50)
    print(config[:1000])
    print("...")
    
    # Peer-lock scenario
    print("\n" + "=" * 70)
    print("PEER-LOCK SCENARIO")
    print("=" * 70)
    
    # Add peer-lock signal for one ASN
    rasa_db_lock = {
        "AS3949": {
            "authorizedAS": 3949,
            "authorizedIn": [{"asSetName": asset_name, "propagation": "directOnly"}],
            "strictMode": False
        }
    }
    
    print("\nAS3949 sets propagation=directOnly")
    print("NTT should reject AS3949 routes from HE unless direct session")
    
    # Generate peer-lock config
    peerlock_lines = [
        "# Peer-lock policy for Hurricane Electric",
        "policy-statement AS6939-in-peerlock {",
        "    term reject-indirect {",
        "        from {",
        "            as-path AS3949-peerlock;",
        "        }",
        "        then reject;",
        "    }",
        "    term accept-others {",
        "        then accept;",
        "    }",
        "}",
        "",
        "as-path AS3949-peerlock \".* 3949 .*\";"
    ]
    print("\n".join(peerlock_lines))


if __name__ == "__main__":
    main()
