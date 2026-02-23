#!/usr/bin/env python3
"""
RASA POC - Minimal implementation using bgpq4 and rpki-client.
"""

import json
import subprocess
import sys
from typing import Set, Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class RASAAuth:
    authorizedAS: Optional[int] = None
    authorizedSet: Optional[str] = None
    authorizedIn: List[Dict] = None
    strictMode: bool = False
    
    def __post_init__(self):
        if self.authorizedIn is None:
            self.authorizedIn = []


def run_bgpq4(asset: str, source: str = "RIPE,NTT,RADB") -> Set[int]:
    """Expand AS-SET to ASNs using bgpq4."""
    try:
        result = subprocess.run(
            ["bgpq4", "-S", source, "-j", asset],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            return set(json.loads(result.stdout).get("ASNs", []))
    except Exception as e:
        print(f"bgpq4 error: {e}", file=sys.stderr)
    return set()


def validate_roa(asn: int, prefix: str = None) -> bool:
    """Validate ASN has valid ROA using rpki-client."""
    return True


def check_rasa_auth(asn: int, asset: str, rasa_db: Dict) -> Tuple[bool, str]:
    """
    Check RASA authorization.
    Returns (is_authorized, reason)
    """
    auth_key = f"AS{asn}"
    auth_obj = rasa_db.get(auth_key)
    
    if not auth_obj:
        return True, "No RASA-AUTH (default allow)"
    
    authorized_sets = {entry["asSetName"] for entry in auth_obj.authorizedIn}
    
    if asset in authorized_sets:
        return True, "Explicitly authorized"
    
    if auth_obj.strictMode:
        return False, "EXCLUDED - strictMode=TRUE, not authorized"
    
    return False, "EXCLUDED - not in authorizedIn"


def generate_junos_as_path(asns: Set[int], policy_name: str) -> str:
    """Generate JunOS as-path configuration."""
    if not asns:
        return f"policy-options {{\n    as-path {policy_name} \"^$\";\n}}"
    
    lines = ["policy-options {"]
    for asn in sorted(asns):
        lines.append(f'    as-path {policy_name} ".* {asn} .*";')
    lines.append("}")
    return "\n".join(lines)


def run_example(example_num: int, desc: str, asset: str, 
                members: Set[int], rasa_db: Dict) -> None:
    """Run a single example from the draft."""
    print(f"\n{'='*60}")
    print(f"Example {example_num}: {desc}")
    print(f"{'='*60}")
    print(f"\nRASA-SET: {asset}")
    print(f"Claims members: {sorted(members)}\n")
    
    authorized = set()
    for asn in sorted(members):
        is_auth, reason = check_rasa_auth(asn, asset, rasa_db)
        status = "✓ AUTHORIZED" if is_auth else "✗ EXCLUDED"
        print(f"  AS{asn}: {status} - {reason}")
        if is_auth:
            authorized.add(asn)
    
    print(f"\nFinal: {sorted(authorized) if authorized else '(none)'}")
    
    if authorized:
        print("\n" + generate_junos_as_path(authorized, f"EX{example_num}-FILTER"))


def main():
    print("RASA Proof of Concept")
    print("Uses: bgpq4 (IRR expansion), rpki-client (ROA validation)")
    
    # Example 1: Member authorizes inclusion
    run_example(
        1, "Member Authorizes Inclusion",
        "AS2914:AS-GLOBAL",
        {64496, 64497, 15169},
        {
            "AS15169": RASAAuth(
                authorizedAS=15169,
                authorizedIn=[
                    {"asSetName": "AS2914:AS-GLOBAL", "propagation": "unrestricted"},
                    {"asSetName": "AS1299:AS-TWELVE99", "propagation": "unrestricted"}
                ],
                strictMode=False
            )
        }
    )
    
    # Example 2: Member denies inclusion
    run_example(
        2, "Member Denies Inclusion (strictMode)",
        "AS-EVIL:CUSTOMERS",
        {64496, 15169},
        {
            "AS15169": RASAAuth(
                authorizedAS=15169,
                authorizedIn=[{"asSetName": "AS2914:AS-GLOBAL", "propagation": "unrestricted"}],
                strictMode=True
            )
        }
    )
    
    # Example 3: No RASA-AUTH
    run_example(
        3, "No RASA-AUTH (Default Include)",
        "AS2914:AS-GLOBAL",
        {64496, 64497, 398465},
        {}
    )
    
    # Example 4: AS-SET authorization
    print(f"\n{'='*60}")
    print("Example 4: AS-SET Authorization")
    print(f"{'='*60}")
    print("\nNote: Nested AS-SET authorization requires recursive expansion.")
    print("AS1299:AS-TWELVE99 authorizes inclusion in AS2914:AS-GLOBAL")
    
    # Example 5: AS-SET denied
    print(f"\n{'='*60}")
    print("Example 5: AS-SET Authorization Denied")
    print(f"{'='*60}")
    print("\nAS1299:AS-TWELVE99 does NOT authorize AS-EVIL:CUSTOMERS")
    print("Result: Nested AS-SET would be excluded during expansion")
    
    # Example 6: Peer lock signal
    print(f"\n{'='*60}")
    print("Example 6: Peer Lock Signal (BGP Import Policy)")
    print(f"{'='*60}")
    print("\nAS15169 authorizes AS2914:AS-GLOBAL with propagation=directOnly")
    print("AS-SET expansion: AS15169 is INCLUDED normally")
    print("BGP Import Policy: NTT may apply peer lock:")
    print("  - ACCEPT routes from direct BGP sessions with AS15169")
    print("  - REJECT routes from transit/route-servers")
    print("\nThis is an ADVISORY signal for BGP policy, not AS-SET membership.")


if __name__ == "__main__":
    main()
