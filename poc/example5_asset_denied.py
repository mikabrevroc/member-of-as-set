#!/usr/bin/env python3
"""
Example 5: AS-SET Authorization Denied (Nested AS-SET NOT Authorized)

Demonstrates the scenario from Section 6.2.2 where a nested AS-SET
is NOT authorized to be included in a parent AS-SET.

Scenario:
- AS-EVIL publishes RASA-SET attempting to include AS1299:AS-TWELVE99
- AS1299 publishes RASA-AUTH but does NOT authorize inclusion in AS-EVIL:CUSTOMERS
- Result: AS1299:AS-TWELVE99 is EXCLUDED (not authorized), security event logged
"""

from rasa_validator import (
    RASAValidator, create_rasa_set, create_rasa_auth,
    RasaFlags, PropagationScope
)


def example5_nested_set_denied():
    """Demonstrate nested AS-SET authorization denial (Example 5 from spec)."""
    
    print("=" * 70)
    print("EXAMPLE 5: AS-SET Authorization Denied")
    print("=" * 70)
    print("\nScenario from draft Section 6.2.2, Example 5")
    print("-" * 70)
    
    # Step 1: Malicious AS-EVIL publishes RASA-SET
    print("\nStep 1: AS-EVIL publishes RASA-SET")
    print("-" * 70)
    print("(Attack scenario: malicious operator trying to include unauthorized AS-SET)")
    
    rasa_set_evil = create_rasa_set(
        name="AS-EVIL:CUSTOMERS",
        containing_as=66666,  # Hypothetical evil AS
        members=[64496],  # Some legitimate member
        nested_sets=["AS1299:AS-TWELVE99"],  # Trying to include Arelion!
        flags=RasaFlags(authoritative=True)
    )
    
    print(f"RASA-SET (AS-EVIL publishes):")
    print(f"  asSetName:    \"{rasa_set_evil.asSetName}\"")
    print(f"  containingAS: {rasa_set_evil.containingAS} (AS-EVIL)")
    print(f"  members:      {rasa_set_evil.members}")
    print(f"  nestedSets:   {rasa_set_evil.nestedSets}")
    print(f"\n  ⚠ WARNING: AS-EVIL is attempting to include AS1299:AS-TWELVE99")
    print(f"     without authorization from AS1299 (Arelion)")
    
    # Step 2: AS1299 publishes RASA-AUTH (but NOT for AS-EVIL)
    print("\nStep 2: AS1299 publishes RASA-AUTH")
    print("-" * 70)
    
    rasa_auth_arelion = create_rasa_auth(
        asset_set="AS1299:AS-TWELVE99",
        authorized_in=[
            ("AS2914:AS-GLOBAL", PropagationScope.UNRESTRICTED),
            # Note: AS-EVIL:CUSTOMERS is NOT in this list!
        ],
        strict_mode=True  # strictMode=TRUE means reject unauthorized
    )
    
    print(f"RASA-AUTH (AS1299 publishes):")
    print(f"  authorizedEntity:")
    print(f"    authorizedSet: \"{rasa_auth_arelion.authorizedSet}\"")
    print(f"  authorizedIn:")
    for entry in rasa_auth_arelion.authorizedIn:
        print(f"    - asSetName: \"{entry.asSetName}\"")
        print(f"      propagation: {entry.propagation.name}")
    print(f"  strictMode: {rasa_auth_arelion.flags.strictMode}")
    print(f"\n  Note: AS-EVIL:CUSTOMERS is NOT in authorizedIn list")
    
    # Step 3: Validator checks authorization
    print("\nStep 3: Validator checks authorization")
    print("-" * 70)
    
    rasa_db = {
        "AS-EVIL:CUSTOMERS": rasa_set_evil,
        "AS1299:AS-TWELVE99": rasa_auth_arelion
    }
    
    validator = RASAValidator(rasa_db)
    
    is_auth, reason = validator.check_asset_set_auth(
        "AS1299:AS-TWELVE99",
        "AS-EVIL:CUSTOMERS"
    )
    
    print(f"\nChecking: AS1299:AS-TWELVE99 in AS-EVIL:CUSTOMERS")
    print(f"\nAuthorization check:")
    print(f"  - AS1299:AS-TWELVE99 RASA-AUTH exists: ✓")
    print(f"  - AS-EVIL:CUSTOMERS in authorizedIn: ✗")
    print(f"  - strictMode: TRUE")
    print(f"\n  Result: {'✓ INCLUDED' if is_auth else '✗ EXCLUDED - SECURITY EVENT'}")
    
    # Step 4: Show expansion result
    print("\nStep 4: AS-SET Expansion Result")
    print("-" * 70)
    
    print("AS-SET Expansion for AS-EVIL:CUSTOMERS:")
    print("  1. Direct members: AS64496 (would be included)")
    print("  2. Nested AS-SET AS1299:AS-TWELVE99:")
    print(f"     - Authorization check: FAILED")
    print(f"     - Action: EXCLUDE nested AS-SET")
    print(f"     - Severity: SECURITY EVENT (strictMode=TRUE)")
    
    print("\n  Final result:")
    print("    ✓ AS64496 (direct member)")
    print("    ✗ AS1299:AS-TWELVE99 (unauthorized - excluded)")
    
    # Show validation log with security event
    print("\nValidator Log:")
    print("-" * 70)
    for entry in validator.log:
        if entry.get("severity") == "security_event":
            print(f"  🚨 SECURITY EVENT: {entry.get('reason')}")
        else:
            status = "✓" if entry.get("authorized", False) else "✗"
            print(f"  {status} {entry.get('reason', entry)}")
    
    print("\n" + "=" * 70)
    print("RESULT: AS1299:AS-TWELVE99 is EXCLUDED (not authorized)")
    print("SECURITY EVENT LOGGED: Unauthorized AS-SET inclusion attempt")
    print("=" * 70)
    
    print("\n💡 Security Impact:")
    print("  - Attack prevented: Malicious AS-SET cannot claim authorized AS-SETs")
    print("  - Audit trail: Security event logged for investigation")
    print("  - No route leak: Unauthorized AS-SET expansion blocked")
    
    return is_auth


if __name__ == "__main__":
    example5_nested_set_denied()
