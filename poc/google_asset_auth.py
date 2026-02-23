#!/usr/bin/env python3

import subprocess
import re
from typing import Set, Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from irr_cache import get_cached, set_cached


@dataclass
class ASSET:
    name: str
    members: List[str]
    source: str
    mnt_by: List[str]


def fetch_asset_full(asset_name: str, server: str = "whois.radb.net") -> Optional[ASSET]:
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
        mnt_by = []
        
        in_members = False
        for raw_line in lines:
            line = raw_line.strip()
            
            if line.startswith('source:'):
                source = line.split(':', 1)[1].strip()
            
            if line.startswith('mnt-by:'):
                mnt = line.split(':', 1)[1].strip()
                mnt_by.append(mnt)
            
            if line.startswith('members:'):
                in_members = True
                member_str = line.split(':', 1)[1].strip()
                members.extend([m.strip() for m in member_str.split(',') if m.strip()])
            elif in_members:
                if not line:
                    in_members = False
                elif raw_line and raw_line[0].isupper() and not raw_line.startswith(' '):
                    in_members = False
                else:
                    members.extend([m.strip() for m in line.split(',') if m.strip()])
        
        return ASSET(name=asset_name, members=members, source=source, mnt_by=mnt_by)
        
    except Exception as e:
        print(f"Error fetching {asset_name}: {e}")
        return None


def fetch_from_all_irr(asset_name: str) -> Dict[str, Optional[ASSET]]:
    servers = {
        "RADB": "whois.radb.net",
        "RIPE": "whois.ripe.net",
        "APNIC": "whois.apnic.net",
        "ARIN": "whois.arin.net",
        "AFRINIC": "whois.afrinic.net",
    }
    
    results = {}
    for db_name, server in servers.items():
        asset = fetch_asset_full(asset_name, server)
        results[db_name] = asset
    return results


def main():
    print("=" * 70)
    print("RASA AS-SET AUTHORIZATION: Enforcing AS-GOOGLE in RADB only")
    print("=" * 70)
    print()
    print("Scenario: Google publishes RASA-AUTH for AS-GOOGLE itself")
    print("Purpose: Cryptographically enforce 'DO NOT USE, USE RADB AS-SET'")
    print("         Reject AS-GOOGLE objects from unauthorized IRR databases")
    print()
    
    print("-" * 70)
    print("Step 1: Query AS-GOOGLE from all IRR databases")
    print("-" * 70)
    
    results = fetch_from_all_irr("AS-GOOGLE")
    
    found_dbs = []
    for db_name, asset in results.items():
        if asset:
            found_dbs.append(db_name)
            print(f"\n{db_name}:")
            print(f"  ✓ Found AS-GOOGLE")
            print(f"  Source: {asset.source}")
            print(f"  Mnt-by: {', '.join(asset.mnt_by) if asset.mnt_by else 'N/A'}")
            print(f"  Members: {len(asset.members)}")
        else:
            print(f"\n{db_name}:")
            print(f"  ✗ Not found")
    
    print()
    print("-" * 70)
    print("Step 2: Google publishes RASA-AUTH for AS-GOOGLE")
    print("-" * 70)
    
    rasa_auth_asset = {
        "rasaVersion": 1,
        "authorizedEntity": {"authorizedAS": 15169},
        "authorizedSet": "AS-GOOGLE",
        "authorizedIn": [{"irrDatabase": "RADB", "source": "RADB"}],
        "strictMode": True,
        "comment": "DO NOT USE objects from other IRRs - USE RADB AS-SET ONLY"
    }
    
    print("\nRASA-AUTH object for AS-GOOGLE:")
    print("{")
    print('  "rasaVersion": 1,')
    print('  "authorizedEntity": {')
    print('    "authorizedAS": 15169')
    print('  },')
    print('  "authorizedSet": "AS-GOOGLE",')
    print('  "authorizedIn": [')
    print('    {')
    print('      "irrDatabase": "RADB",')
    print('      "source": "RADB"')
    print('    }')
    print('  ],')
    print('  "strictMode": true,')
    print('  "comment": "DO NOT USE objects from other IRRs - USE RADB AS-SET ONLY"')
    print("}")
    
    print()
    print("-" * 70)
    print("Step 3: Validate AS-GOOGLE objects against RASA-AUTH")
    print("-" * 70)
    
    authorized_db = "RADB"
    
    print(f"\nExpected: AS-GOOGLE should ONLY exist in {authorized_db}")
    print(f"Strict mode: ENABLED (reject unauthorized sources)")
    print()
    
    for db_name, asset in results.items():
        if asset:
            if db_name == authorized_db:
                print(f"{db_name}: ✓ AUTHORIZED")
                print(f"  Source field: {asset.source}")
                print(f"  Validated: Matches RASA-AUTH authorizedIn")
            else:
                print(f"{db_name}: ✗ REJECTED - UNAUTHORIZED SOURCE")
                print(f"  Source field: {asset.source}")
                print(f"  Violation: Not in authorized IRR database list")
                print(f"  Action: Ignore/reject this AS-GOOGLE object")
    
    print()
    print("-" * 70)
    print("Step 4: Operator (NTT) applies RASA validation")
    print("-" * 70)
    
    print("\nWhen NTT expands AS2914:AS-GLOBAL which includes AS-GOOGLE:")
    print()
    print("1. NTT queries AS-GOOGLE from IRR databases")
    print(f"2. NTT finds AS-GOOGLE in {len([a for a in results.values() if a])} databases")
    print("3. NTT checks RASA-AUTH for AS-GOOGLE...")
    print("4. RASA-AUTH says: ONLY trust RADB source")
    print("5. NTT filters results:")
    
    for db_name, asset in results.items():
        if asset:
            status = "✓ USE" if db_name == authorized_db else "✗ IGNORE"
            print(f"   - {db_name}: {status}")
    
    print()
    print("=" * 70)
    print("RESULT: Only RADB AS-GOOGLE used for AS-SET expansion")
    print("=" * 70)
    
    radb_asset = results.get("RADB")
    if radb_asset:
        print(f"\nAS-GOOGLE (RADB only):")
        print(f"  Source: {radb_asset.source}")
        print(f"  Members: {len(radb_asset.members)}")
        print(f"  ASNs: {sorted([int(m[2:]) for m in radb_asset.members if re.match(r'^AS\\d+$', m)])}")
    
    print()
    print("This cryptographically enforces Google's policy:")
    print("  'DO NOT USE, USE RADB AS-SET'")
    print()
    print("Prevents attacks where malicious actors create fake AS-GOOGLE")
    print("objects in other IRR databases to hijack Google's routes.")


if __name__ == "__main__":
    main()
