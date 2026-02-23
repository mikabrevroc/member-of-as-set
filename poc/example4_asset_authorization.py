#!/usr/bin/env python3
"""
Example 4: AS-SET Authorization (Nested AS-SET Authorized)

Demonstrates the scenario from Section 6.2.2 where a nested AS-SET
is authorized to be included in a parent AS-SET.

Scenario:
- AS2914 publishes RASA-SET with nestedSets containing AS1299:AS-TWELVE99
- AS1299 publishes RASA-AUTH with authorizedSet authorizing inclusion in AS2914:AS-GLOBAL
- Result: AS1299:AS-TWELVE99 is INCLUDED (authorized)
"""

from rasa_validator import (
    RASAValidator, create_rasa_set, create_rasa_auth,
    RasaFlags, PropagationScope
)


def example4_nested_set_authorized():
    """Demonstrate nested AS-SET authorization (Example 4 from spec)."""
    
    print("=" * 70)
    print("EXAMPLE 4: AS-SET Authorization (Nested AS-SET Authorized)")
    print("=" * 70)
    print("\nScenario from draft Section 6.2.2, Example 4")
    print("-" * 70)
    
    # Step 1: AS2914 publishes RASA-SET containing nested AS-SET
    print("\nStep 1: AS2914 publishes RASA-SET")
    print("-" * 70)
    
    rasa_set = create_rasa_set(
        name="AS2914:AS-GLOBAL",
        containing_as=2914,
        members=[64496, 64497],  # Direct ASNs
        nested_sets=["AS1299:AS-TWELVE99"],  # Nested AS-SET
        flags=RasaFlags(authoritative=True, doNotInherit=False)
    )
    
    print(f"RASA-SET (AS2914 publishes):")
    print(f"  asSetName:    \"{rasa_set.asSetName}\"")
    print(f"  containingAS: {rasa_set.containingAS}")
    print(f"  members:      {rasa_set.members}")
    print(f"  nestedSets:   {rasa_set.nestedSets}")
    print(f"  flags:        authoritative={rasa_set.flags.authoritative}")
    
    # Step 2: AS1299 publishes RASA-AUTH authorizing the nested set
    print("\nStep 2: AS1299 publishes RASA-AUTH")
    print("-" * 70)
    
    rasa_auth = create_rasa_auth(
        asset_set="AS1299:AS-TWELVE99",  # Note: authorizedSet, not authorizedAS
        authorized_in=[
            ("AS2914:AS-GLOBAL", PropagationScope.UNRESTRICTED)
        ],
        strict_mode=True
    )
    
    print(f"RASA-AUTH (AS1299 publishes):")
    print(f"  authorizedEntity:")
    print(f"    authorizedSet: \"{rasa_auth.authorizedSet}\"")
    print(f"  authorizedIn:")
    for entry in rasa_auth.authorizedIn:
        print(f"    - asSetName: \"{entry.asSetName}\"")
        print(f"      propagation: {entry.propagation.name}")
    print(f"  strictMode: {rasa_auth.flags.strictMode}")
    
    # Step 3: Validate authorization
    print("\nStep 3: Validator checks authorization")
    print("-" * 70)
    
    # Create RASA database
    rasa_db = {
        "AS2914:AS-GLOBAL": rasa_set,
        "AS1299:AS-TWELVE99": rasa_auth
    }
    
    validator = RASAValidator(rasa_db)
    
    # Check if AS1299:AS-TWELVE99 is authorized in AS2914:AS-GLOBAL
    is_auth, reason = validator.check_asset_set_auth(
        "AS1299:AS-TWELVE99", 
        "AS2914:AS-GLOBAL"
    )
    
    print(f"\nChecking: AS1299:AS-TWELVE99 in AS2914:AS-GLOBAL")
    print(f"Result: {'✓ INCLUDED' if is_auth else '✗ EXCLUDED'} ({reason})")
    
    # Step 4: Show expansion result
    print("\nStep 4: AS-SET Expansion Result")
    print("-" * 70)
    
    if is_auth:
        print("AS-SET Expansion proceeds:")
        print("  1. Include direct members: AS64496, AS64497")
        print("  2. Nested AS-SET AS1299:AS-TWELVE99 is AUTHORIZED")
        print("  3. Recursively expand AS1299:AS-TWELVE99...")
        print("     (Would fetch members from IRR or RASA-SET)")
        print("\n  Final result: All members included")
    else:
        print("AS-SET Expansion:")
        print("  1. Include direct members: AS64496, AS64497")
        print("  2. Nested AS-SET AS1299:AS-TWELVE99 is NOT AUTHORIZED")
        print("  3. Skip nested AS-SET")
        print("\n  Final result: Only direct members included")
    
    # Show validation log
    print("\nValidator Log:")
    print("-" * 70)
    for entry in validator.log:
        status = "✓" if entry.get("authorized", False) else "✗"
        print(f"  {status} {entry.get('reason', entry)}")
    
    print("\n" + "=" * 70)
    print("RESULT: AS1299:AS-TWELVE99 is INCLUDED (authorized)")
    print("=" * 70)
    
    return is_auth


if __name__ == "__main__":
    example4_nested_set_authorized()
