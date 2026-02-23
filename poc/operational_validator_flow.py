#!/usr/bin/env python3
"""
Operational Example 3: Complete Validator Decision Flow

Demonstrates the step-by-step validator decision flow from Section 10.3.
Shows exactly how a router configuration generator processes RASA objects.
"""

from rasa_validator import (
    RASAValidator, create_rasa_set, create_rasa_auth,
    RasaFlags, PropagationScope
)


def operational_validator_flow():
    """Demonstrate complete validator decision flow step-by-step."""
    
    print("=" * 70)
    print("OPERATIONAL EXAMPLE 3: Complete Validator Decision Flow")
    print("=" * 70)
    print("\nScenario from draft Section 10.3, Example 3")
    print("Step-by-step validator processing AS2914:AS-GLOBAL")
    print("-" * 70)
    
    # Setup: Create RASA database
    print("\n📋 SETUP: RASA Database")
    print("-" * 70)
    
    # NTT publishes RASA-SET
    rasa_set = create_rasa_set(
        name="AS2914:AS-GLOBAL",
        containing_as=2914,
        members=[64496, 64497, 64498],
        nested_sets=["AS64496:CUSTOMERS"],
        flags=RasaFlags(authoritative=True)
    )
    
    # Customers publish various RASA-AUTH
    auth_64496 = create_rasa_auth(
        asn=64496,
        authorized_in=[("AS2914:AS-GLOBAL", PropagationScope.UNRESTRICTED)],
        strict_mode=False
    )
    
    auth_64497 = create_rasa_auth(
        asn=64497,
        authorized_in=[],  # Empty list = refuses all inclusion
        strict_mode=False
    )
    
    # AS64498 has NO RASA-AUTH
    
    rasa_db = {
        "AS2914:AS-GLOBAL": rasa_set,
        "AS64496": auth_64496,
        "AS64497": auth_64497
    }
    
    print("RASA Objects in Database:")
    print(f"  RASA-SET: AS2914:AS-GLOBAL")
    print(f"    members: [64496, 64497, 64498]")
    print(f"    nestedSets: [AS64496:CUSTOMERS]")
    print(f"    authoritative: TRUE")
    print(f"\n  RASA-AUTH: AS64496")
    print(f"    authorizedIn: [AS2914:AS-GLOBAL]")
    print(f"    strictMode: FALSE")
    print(f"\n  RASA-AUTH: AS64497")
    print(f"    authorizedIn: [] (empty = refuses inclusion)")
    print(f"    strictMode: FALSE")
    print(f"\n  RASA-AUTH: AS64498")
    print(f"    None published")
    
    # Step 1: Query RPKI for RASA-SET
    print("\n" + "=" * 70)
    print("STEP 1: Query RPKI for RASA-SET")
    print("=" * 70)
    
    print("\nAction: Query RPKI for \"AS2914:AS-GLOBAL\"")
    print("Result: Found valid RASA-SET from AS2914")
    print(f"\nRASA-SET Properties:")
    print(f"  authoritative=TRUE")
    print(f"  members=[64496, 64497, 64498]")
    print(f"  nestedSets=[AS64496:CUSTOMERS]")
    
    print("\n✓ Decision: Use ONLY RASA-SET data (authoritative=TRUE)")
    print("  IRR data is NOT queried for this AS-SET")
    
    # Step 2: Check RASA-AUTH for each member
    print("\n" + "=" * 70)
    print("STEP 2: Check RASA-AUTH for Each Member")
    print("=" * 70)
    
    validator = RASAValidator(rasa_db)
    results = []
    
    # Process each member
    members = [64496, 64497, 64498]
    
    for i, asn in enumerate(members, 1):
        print(f"\n{'─' * 70}")
        print(f"Member {i}: AS{asn}")
        print('─' * 70)
        
        print(f"\n  2.{i}.1 Query RPKI for RASA-AUTH from AS{asn}")
        
        auth_key = f"AS{asn}"
        if auth_key in rasa_db:
            auth_obj = rasa_db[auth_key]
            print(f"  Result: RASA-AUTH found")
            print(f"\n  2.{i}.2 Check authorizedIn list:")
            
            authorized = False
            for entry in auth_obj.authorizedIn:
                print(f"    Checking: \"{entry.asSetName}\" == \"AS2914:AS-GLOBAL\"?")
                if entry.asSetName == "AS2914:AS-GLOBAL":
                    print(f"    ✓ MATCH FOUND!")
                    authorized = True
                    break
            
            if not authorized:
                print(f"    ✗ AS2914:AS-GLOBAL NOT in authorizedIn")
        else:
            print(f"  Result: No RASA-AUTH published")
            authorized = True
            print(f"\n  2.{i}.2 Decision: INCLUDE (no objection)")
        
        is_auth, reason = validator.check_member_auth(asn, "AS2914:AS-GLOBAL")
        results.append((asn, is_auth, reason))
        
        status = "✓ INCLUDE" if is_auth else "✗ EXCLUDE"
        print(f"\n  2.{i}.3 FINAL DECISION: {status}")
        print(f"    Reason: {reason}")
    
    # Step 3: Process nestedSets
    print("\n" + "=" * 70)
    print("STEP 3: Process nestedSets")
    print("=" * 70)
    
    print("\nnestedSets: [AS64496:CUSTOMERS]")
    print("\n3.1 Check doNotInherit flag:")
    print(f"  doNotInherit: FALSE")
    print("  Action: Proceed with expansion")
    
    print("\n3.2 Check authorization for nested AS-SET:")
    print("  Query RPKI for RASA-AUTH from AS64496:CUSTOMERS...")
    print("  Result: Not found (no authorization needed for AS-SET as member)")
    print("  Decision: Include reference AS64496:CUSTOMERS")
    
    print("\n3.3 Recursive expansion:")
    print("  Would recursively expand AS64496:CUSTOMERS...")
    print("  (Demonstration stops at first level)")
    
    # Step 4: Final member list
    print("\n" + "=" * 70)
    print("STEP 4: Final Member List")
    print("=" * 70)
    
    print("\nValidation Results Summary:")
    print(f"{'─' * 70}")
    print(f"{'ASN':<10} {'Status':<15} {'Reason':<45}")
    print(f"{'─' * 70}")
    
    for asn, is_auth, reason in results:
        status = "INCLUDE" if is_auth else "EXCLUDE"
        print(f"AS{asn:<8} {status:<15} {reason:<45}")
    
    print(f"{'─' * 70}")
    
    authorized_count = sum(1 for _, is_auth, _ in results if is_auth)
    print(f"\nTotal: {authorized_count} of {len(results)} ASNs authorized")
    
    # Step 5: Show detailed log
    print("\n" + "=" * 70)
    print("STEP 5: Complete Validation Log")
    print("=" * 70)
    
    for entry in validator.log:
        print(f"\n  {entry}")
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    print("\n✅ Validator Workflow:")
    print("  1. Query RPKI for RASA-SET")
    print("  2. For each member, query RPKI for RASA-AUTH")
    print("  3. Check if containing AS-SET is in authorizedIn")
    print("  4. Apply strictMode logic if not authorized")
    print("  5. Process nestedSets with doNotInherit check")
    print("  6. Return final authorized member list")
    
    print("\n📊 This Example Demonstrates:")
    print("  • Explicit authorization (AS64496)")
    print("  • Explicit refusal (AS64497 with empty authorizedIn)")
    print("  • Default allow (AS64498 with no RASA-AUTH)")
    print("  • Authoritative RASA-SET (IRR bypassed)")
    print("  • Nested AS-SET processing")
    
    return True


if __name__ == "__main__":
    operational_validator_flow()
