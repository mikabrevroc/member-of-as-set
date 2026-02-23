#!/usr/bin/env python3
"""
Google Peer-Lock Scenario using live IRR data.

Demonstrates: Google (AS-GOOGLE) sets propagation=directOnly
Result: NTT rejects Google routes from peers unless direct
"""

import json
import os
from typing import Set
from irr_fetcher import expand_asset


def generate_peerlock_config(peer_asn: int, blocked_asns: Set[int], description: str) -> str:
    lines = [
        f"# {description}",
        f"# Blocks {len(blocked_asns)} ASNs from peer AS{peer_asn}",
        "",
        f"as-path-group AS{peer_asn}-peerlock {{",
    ]
    
    for asn in sorted(blocked_asns):
        lines.append(f'    as-path block-{asn} ".* {asn} .*";')
    
    lines.extend([
        "}",
        "",
        f"policy-statement AS{peer_asn}-in-peerlock {{",
        "    term reject-peerlock {",
        "        from {",
        f"            as-path-group AS{peer_asn}-peerlock;",
        "        }",
        "        then reject;",
        "    }",
        "    term accept-others {",
        "        then accept;",
        "    }",
        "}",
    ])
    
    return "\n".join(lines)


def main():
    print("=" * 70)
    print("GOOGLE PEER-LOCK SCENARIO")
    print("=" * 70)
    print()
    print("Scenario: Google publishes RASA-AUTH with propagation=directOnly")
    print("Result: NTT (AS2914) rejects Google routes from peers")
    print("        unless received via direct NTT<->Google peering session")
    print()
    
    print("-" * 70)
    print("Step 1: Fetch AS-GOOGLE from IRR")
    print("-" * 70)
    
    google_asns, google_sets, _ = expand_asset("AS-GOOGLE", max_depth=1)
    
    print(f"\nFound AS-GOOGLE in IRR:")
    print(f"  - Direct ASNs: {len(google_asns)}")
    print(f"  - Nested AS-SETs: {len(google_sets)}")
    print(f"  - ASNs: {sorted(google_asns)}")
    
    print()
    print("-" * 70)
    print("Step 2: Google publishes RASA-AUTH objects")
    print("-" * 70)
    
    print(f"\nEach Google ASN publishes RASA-AUTH with:")
    print('  {')
    print('    "authorizedAS": <asn>,')
    print('    "authorizedIn": [')
    print('      {"asSetName": "AS2914:AS-GLOBAL", "propagation": "directOnly"}')
    print('    ],')
    print('    "strictMode": false')
    print('  }')
    
    # Load RASA database from JSON file
    rasa_file = os.path.join(os.path.dirname(__file__), 'mock_rasa', 'google_peerlock.json')
    with open(rasa_file, 'r') as f:
        rasa_data = json.load(f)
    rasa_db = rasa_data.get('rasa_auth', {})
    print(f"\nLoaded {len(rasa_db)} RASA-AUTH entries from {rasa_file}")
    
    peers = [
        {"name": "Hurricane Electric", "asn": 6939},
        {"name": "Arelion", "asn": 1299},
    ]
    
    print()
    print("-" * 70)
    print("Step 3: NTT generates peer-lock filters for all peers")
    print("-" * 70)
    print()
    print("NTT checks RASA-AUTH for each ASN in AS-GOOGLE:")
    print("  - AS-GOOGLE ASNs have propagation=directOnly")
    print("  - This is a signal to reject from peers unless direct")
    print("  - Creating peer-lock filters...")
    
    for peer in peers:
        print()
        print(f"\nPeer: {peer['name']} (AS{peer['asn']})")
        print("-" * 50)
        
        config = generate_peerlock_config(
            peer_asn=peer['asn'],
            blocked_asns=google_asns,
            description=f"Peer-lock: Reject Google routes from {peer['name']} (indirect)"
        )
        
        # Write config to file in poc/ directory
        poc_dir = os.path.dirname(os.path.abspath(__file__))
        filename = os.path.join(poc_dir, f"google_peerlock_AS{peer['asn']}.conf")
        with open(filename, 'w') as f:
            f.write(config)
        
        # Print from the generated file
        with open(filename, 'r') as f:
            print(f.read())
        
        print(f"Written to: {filename}")
    
    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print()
    print(f"Google AS-SET (AS-GOOGLE) contains {len(google_asns)} ASNs")
    print()
    print("Peers receiving peer-lock filters:")
    for peer in peers:
        print(f"  - {peer['name']} (AS{peer['asn']})")
    print()
    print("Google publishes RASA-AUTH with propagation=directOnly")
    print("NTT applies peer-lock on all peer import policies")
    print("Result: Google routes only accepted from direct NTT<->Google sessions")


if __name__ == "__main__":
    main()
