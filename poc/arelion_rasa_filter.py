#!/usr/bin/env python3
"""
RASA Authorization Filter Example: DigitalOcean in Arelion AS-SET
"""

import json
import os
from typing import Set
from irr_fetcher import fetch_asset, is_asn


def generate_junos_accept(peer_asn: int, peer_name: str, allowed_asns: Set[int]) -> str:
    lines = [
        f"# NTT import policy for {peer_name} (AS{peer_asn})",
        f"# Accepting {len(allowed_asns)} ASNs from peer's AS-SET",
        "",
        f"policy-statement AS{peer_asn}-in {{",
        "    term accept-customers {",
        "        from {",
    ]
    
    if allowed_asns:
        lines.append(f"            as-path-group AS{peer_asn}-allowed;")
    
    lines.extend([
        "        }",
        "        then accept;",
        "    }",
        "    term reject {",
        "        then reject;",
        "    }",
        "}",
        "",
        f"as-path-group AS{peer_asn}-allowed {{",
    ])
    
    for asn in sorted(allowed_asns):
        lines.append(f'    as-path allow-{asn} ".* {asn} .*";')
    
    lines.append("}")
    
    return "\n".join(lines)


def main():
    print("=" * 70)
    print("RASA AUTHORIZATION FILTER: DigitalOcean in Arelion AS-SET")
    print("=" * 70)
    print()
    
    # Step 1: Fetch DigitalOcean AS-SET
    print("-" * 70)
    print("Step 1: Fetch AS-14061 (DigitalOcean)")
    print("-" * 70)
    
    do_asset = fetch_asset("AS-14061")
    if not do_asset:
        print("Failed to fetch AS-14061")
        return
    
    do_asns = set()
    for m in do_asset.members:
        if is_asn(m):
            do_asns.add(int(m[2:]))
    
    print(f"\nDigitalOcean AS-SET (AS-14061):")
    print(f"  Source: {do_asset.source}")
    print(f"  Members: {do_asset.members}")
    print(f"  ASNs: {[f'AS{a}' for a in sorted(do_asns)]}")
    
    # Step 2: Mock RASA-AUTH from DigitalOcean
    print()
    print("-" * 70)
    print("Step 2: DigitalOcean publishes RASA-AUTH objects")
    print("-" * 70)
    
    arelion_asset = "AS1299:AS-TWELVE99-NA-V4"
    
    # Load RASA database from JSON file
    rasa_file = os.path.join(os.path.dirname(__file__), 'mock_rasa', 'digitalocean_strict.json')
    with open(rasa_file, 'r') as f:
        rasa_data = json.load(f)
    rasa_db = rasa_data.get('rasa_auth', {})
    
    print("\nDigitalOcean RASA-AUTH for each ASN:")
    print("{")
    print('  "authorizedAS": <asn>,')
    print('  "authorizedIn": [')
    print('    {"asSetName": "AS2914:AS-GLOBAL", "propagation": "unrestricted"},')
    print('    {"asSetName": "AS3356:AS-LEVEL3", "propagation": "unrestricted"}')
    print(f'    // NOTE: {arelion_asset} (Arelion) NOT authorized!')
    print('  ],')
    print('  "strictMode": true')
    print("}")
    
    # Step 3: Apply RASA filtering
    print()
    print("-" * 70)
    print("Step 3: NTT applies RASA authorization filter")
    print("-" * 70)
    
    print(f"\nChecking DigitalOcean ASNs against RASA-AUTH:")
    print(f"  Arelion AS-SET: {arelion_asset}")
    print()
    
    authorized_asns = set()
    rejected_asns = set()
    
    for asn in sorted(do_asns):
        auth = rasa_db.get(f"AS{asn}")
        if auth:
            authorized_sets = [e.get("asSetName") for e in auth.get("authorizedIn", [])]
            if arelion_asset in authorized_sets:
                print(f"  ✓ AS{asn}: Authorized in {arelion_asset}")
                authorized_asns.add(asn)
            else:
                print(f"  ✗ AS{asn}: REJECTED - {arelion_asset} not in authorizedIn")
                print(f"           Authorized only in: {authorized_sets}")
                rejected_asns.add(asn)
    
    # Step 4: Show config difference
    print()
    print("-" * 70)
    print("Step 4: Configuration Impact")
    print("-" * 70)
    
    print("\nWITHOUT RASA (baseline):")
    print(f"  NTT would accept all {len(do_asns)} DigitalOcean ASNs from Arelion")
    print(f"  ASNs: {sorted(do_asns)}")
    
    print("\nWITH RASA (after filtering):")
    print(f"  NTT accepts: {len(authorized_asns)} ASNs")
    if authorized_asns:
        print(f"  ASNs: {sorted(authorized_asns)}")
    else:
        print(f"  ASNs: (none - all rejected)")
    
    print(f"\n  NTT rejects: {len(rejected_asns)} ASNs")
    print(f"  ASNs: {sorted(rejected_asns)}")
    
    # Step 5: Generate JunOS configs
    print()
    print("-" * 70)
    print("Step 5: Generated JunOS Configurations")
    print("-" * 70)
    
    # Generate and write configs
    config_without = generate_junos_accept(1299, "Arelion", do_asns)
    config_with = generate_junos_accept(1299, "Arelion", authorized_asns)
    
    # Write config to files in poc/ directory
    poc_dir = os.path.dirname(os.path.abspath(__file__))
    without_file = os.path.join(poc_dir, "arelion_without_rasa.conf")
    with_file = os.path.join(poc_dir, "arelion_with_rasa.conf")
    
    with open(without_file, "w") as f:
        f.write(config_without)
    
    with open(with_file, "w") as f:
        f.write(config_with)
    
    # Print from generated files
    print("\n" + "=" * 50)
    print("CONFIG A: Without RASA (accept all)")
    print("=" * 50)
    with open(without_file, "r") as f:
        print(f.read())
    
    print("\n" + "=" * 50)
    print("CONFIG B: With RASA (filtered)")
    print("=" * 50)
    with open(with_file, "r") as f:
        print(f.read())
    
    # Summary
    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print()
    print("Scenario: DigitalOcean (AS-14061) is member of Arelion's AS-SET")
    print(f"          ({arelion_asset})")
    print()
    print("DigitalOcean RASA-AUTH authorizes:")
    print("  ✓ AS2914:AS-GLOBAL (NTT)")
    print("  ✓ AS3356:AS-LEVEL3 (Lumen)")
    print(f"  ✗ {arelion_asset} (Arelion) - NOT authorized")
    print()
    print(f"Result: {len(rejected_asns)} of {len(do_asns)} DigitalOcean ASNs")
    print("        are REJECTED from Arelion peer due to RASA strictMode")
    print()
    print("Files written:")
    print("  - arelion_without_rasa.conf")
    print("  - arelion_with_rasa.conf")


if __name__ == "__main__":
    main()
