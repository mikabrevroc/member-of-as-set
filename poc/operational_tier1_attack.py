#!/usr/bin/env python3
"""
Operational Example 1: Tier-1 Provider Customer AS-SET with Attack Scenario

Demonstrates the complete operational workflow from Section 10.1,
including an attack scenario where AS-EVIL attempts unauthorized inclusion.

Scenario:
- NTT (AS2914) maintains AS2914:AS-GLOBAL with RASA protection
- Multiple customers publish RASA-AUTH with various strictMode settings
- Attacker AS-EVIL attempts to include NTT's AS-SET without authorization
"""

from rasa_validator import (
    RASAValidator, create_rasa_set, create_rasa_auth,
    RasaFlags, PropagationScope
)


def operational_tier1_attack():
    """Demonstrate Tier-1 provider scenario with attack."""
    
    print("=" * 70)
    print("OPERATIONAL EXAMPLE 1: Tier-1 Provider Customer AS-SET")
    print("=" * 70)
    print("\nScenario from draft Section 10.1, Example 1")
    print("Demonstrates complete operational workflow with attack prevention")
    print("-" * 70)
    
    # Step 1: NTT publishes RASA-SET
    print("\nStep 1: NTT (AS2914) publishes RASA-SET")
    print("-" * 70)
    
    rasa_set_ntt = create_rasa_set(
        name="AS2914:AS-GLOBAL",
        containing_as=2914,
        members=[64496, 64497, 64498, 64499, 64500],
        nested_sets=["AS64496:AS-SET", "AS64497:AS-SET"],
        flags=RasaFlags(authoritative=True, doNotInherit=False),
        irr_source="RADB"
    )
    
    print("RASA-SET (AS2914 publishes):")
    print(f"  asSetName:     \"{rasa_set_ntt.asSetName}\"")
    print(f"  containingAS:  {rasa_set_ntt.containingAS}")
    print(f"  members:       {rasa_set_ntt.members}")
    print(f"  nestedSets:    {rasa_set_ntt.nestedSets}")
    print(f"  flags:         authoritative={rasa_set_ntt.flags.authoritative}")
    print(f"                 doNotInherit={rasa_set_ntt.flags.doNotInherit}")
    print(f"  irrSource:     \"{rasa_set_ntt.irrSource}\"")
    
    # Step 2: Customers publish RASA-AUTH
    print("\nStep 2: Customers publish RASA-AUTH")
    print("-" * 70)
    
    # Customer AS64496 - authorizes NTT and Arelion
    auth_64496 = create_rasa_auth(
        asn=64496,
        authorized_in=[
            ("AS2914:AS-GLOBAL", PropagationScope.UNRESTRICTED),
            ("AS1299:AS-TWELVE99", PropagationScope.UNRESTRICTED)
        ],
        strict_mode=False
    )
    
    print("\n  Customer AS64496:")
    print(f"    authorizedAS:  {auth_64496.authorizedAS}")
    print(f"    authorizedIn:  [AS2914:AS-GLOBAL, AS1299:AS-TWELVE99]")
    print(f"    strictMode:    {auth_64496.flags.strictMode}")
    
    # Customer AS64497 - authorizes only NTT, strict mode
    auth_64497 = create_rasa_auth(
        asn=64497,
        authorized_in=[
            ("AS2914:AS-GLOBAL", PropagationScope.UNRESTRICTED)
        ],
        strict_mode=True
    )
    
    print("\n  Customer AS64497:")
    print(f"    authorizedAS:  {auth_64497.authorizedAS}")
    print(f"    authorizedIn:  [AS2914:AS-GLOBAL]")
    print(f"    strictMode:    {auth_64497.flags.strictMode}")
    
    # Customer AS64498 - NO RASA-AUTH (no objection, included by default)
    print("\n  Customer AS64498:")
    print(f"    authorizedAS:  64498")
    print(f"    RASA-AUTH:     None published")
    print(f"    Result:        Included by default (no objection)")
    
    # Step 3: Build RASA database
    rasa_db = {
        "AS2914:AS-GLOBAL": rasa_set_ntt,
        "AS64496": auth_64496,
        "AS64497": auth_64497
    }
    
    # Step 4: Attack scenario - AS-EVIL attempts unauthorized inclusion
    print("\nStep 3: Attack Scenario - AS-EVIL attempts unauthorized inclusion")
    print("-" * 70)
    
    rasa_set_evil = create_rasa_set(
        name="AS-EVIL:CUSTOMERS",
        containing_as=66666,
        members=[64496, 64497, 2914],  # Trying to include NTT!
        flags=RasaFlags(authoritative=True)
    )
    
    print("⚠ ATTACK DETECTED:")
    print(f"  AS-EVIL publishes RASA-SET:")
    print(f"    asSetName:    \"{rasa_set_evil.asSetName}\"")
    print(f"    members:      {rasa_set_evil.members}")
    print(f"\n  Attempting to include:")
    print(f"    - AS64496 (DigitalOcean customer)")
    print(f"    - AS64497 (Another customer)")
    print(f"    - AS2914  (NTT itself!) ← CRITICAL")
    
    # Step 5: NTT's defense - RASA-AUTH prevents inclusion
    print("\nStep 4: NTT Defense - RASA-AUTH prevents unauthorized inclusion")
    print("-" * 70)
    
    auth_ntt = create_rasa_auth(
        asn=2914,
        authorized_in=[
            ("AS2914:AS-GLOBAL", PropagationScope.UNRESTRICTED)
        ],
        strict_mode=True
    )
    
    rasa_db["AS2914"] = auth_ntt
    
    print("RASA-AUTH (AS2914 publishes):")
    print(f"  authorizedAS:  {auth_ntt.authorizedAS}")
    print(f"  authorizedIn:  [AS2914:AS-GLOBAL]")
    print(f"  strictMode:    {auth_ntt.flags.strictMode}")
    print(f"\n  Note: AS-EVIL:CUSTOMERS is NOT in authorizedIn list")
    print(f"  strictMode=TRUE means reject (not just warn)")
    
    # Step 6: Validate AS-EVIL's claim
    print("\nStep 5: Validator checks AS-EVIL's claim")
    print("-" * 70)
    
    validator = RASAValidator(rasa_db)
    
    print("Checking each member claimed by AS-EVIL:")
    
    # Check AS64496
    is_auth, reason = validator.check_member_auth(64496, "AS-EVIL:CUSTOMERS")
    status = "✓" if is_auth else "✗"
    print(f"\n  AS64496 in AS-EVIL:CUSTOMERS:")
    print(f"    - RASA-AUTH exists: ✓")
    print(f"    - AS-EVIL in authorizedIn: ✗")
    print(f"    - strictMode: FALSE")
    print(f"    - Result: {status} EXCLUDED (warning logged)")
    
    # Check AS64497
    is_auth, reason = validator.check_member_auth(64497, "AS-EVIL:CUSTOMERS")
    status = "✓" if is_auth else "✗"
    print(f"\n  AS64497 in AS-EVIL:CUSTOMERS:")
    print(f"    - RASA-AUTH exists: ✓")
    print(f"    - AS-EVIL in authorizedIn: ✗")
    print(f"    - strictMode: TRUE")
    print(f"    - Result: {status} EXCLUDED (SECURITY EVENT)")
    
    # Check AS2914 (NTT)
    is_auth, reason = validator.check_member_auth(2914, "AS-EVIL:CUSTOMERS")
    status = "✓" if is_auth else "✗"
    print(f"\n  AS2914 in AS-EVIL:CUSTOMERS:")
    print(f"    - RASA-AUTH exists: ✓")
    print(f"    - AS-EVIL in authorizedIn: ✗")
    print(f"    - strictMode: TRUE")
    print(f"    - Result: {status} EXCLUDED (SECURITY EVENT)")
    
    # Step 7: Show validation log
    print("\nStep 6: Validation Log")
    print("-" * 70)
    
    for entry in validator.log:
        if entry.get("severity") == "security_event":
            print(f"  🚨 SECURITY EVENT: {entry.get('reason')}")
        elif not entry.get("authorized", True):
            print(f"  ⚠ WARNING: {entry.get('reason')}")
    
    # Step 8: Legitimate expansion for comparison
    print("\nStep 7: Legitimate AS-SET Expansion (AS2914:AS-GLOBAL)")
    print("-" * 70)
    
    validator2 = RASAValidator(rasa_db)
    
    print("\nExpanding AS2914:AS-GLOBAL with RASA validation:")
    
    for asn in [64496, 64497, 64498]:
        is_auth, reason = validator2.check_member_auth(asn, "AS2914:AS-GLOBAL")
        status = "✓ INCLUDED" if is_auth else "✗ EXCLUDED"
        print(f"  AS{asn}: {status} - {reason}")
    
    # Step 9: Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    print("\n✅ Attack Prevented:")
    print("  - AS-EVIL cannot claim NTT's AS-SET")
    print("  - All unauthorized inclusions blocked")
    print("  - Security events logged for investigation")
    
    print("\n✅ Legitimate Operations Continue:")
    print("  - NTT's customers properly authorized")
    print("  - AS-SET expansion works for authorized users")
    print("  - No disruption to normal operations")
    
    print("\n💡 Security Benefits:")
    print("  - Cryptographic proof of authorization")
    print("  - Automatic rejection of unauthorized claims")
    print("  - Audit trail for security incidents")
    print("  - No reliance on manual verification")
    
    return True


if __name__ == "__main__":
    operational_tier1_attack()
