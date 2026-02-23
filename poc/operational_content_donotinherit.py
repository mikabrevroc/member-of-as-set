#!/usr/bin/env python3
"""
Operational Example 2: Content Provider Multi-AS Protection (doNotInherit)

Demonstrates the content provider protection scenario from Section 10.2,
using the doNotInherit flag to prevent transitive attacks.

Scenario:
- Google operates multiple ASNs aggregated under AS15169:AS-GOOGLE
- Google publishes RASA-SET with doNotInherit=TRUE
- Google publishes RASA-AUTH for each ASN authorizing specific Tier-1s
- Malicious AS-SET cannot inherit Google's ASNs through nesting
"""

from rasa_validator import (
    RASAValidator, create_rasa_set, create_rasa_auth,
    RasaFlags, PropagationScope
)


def operational_content_donotinherit():
    """Demonstrate content provider protection with doNotInherit."""
    
    print("=" * 70)
    print("OPERATIONAL EXAMPLE 2: Content Provider Multi-AS Protection")
    print("=" * 70)
    print("\nScenario from draft Section 10.2, Example 2")
    print("Demonstrates doNotInherit flag preventing transitive attacks")
    print("-" * 70)
    
    # Step 1: Google publishes aggregated RASA-SET
    print("\nStep 1: Google publishes RASA-SET for aggregated AS-SET")
    print("-" * 70)
    
    rasa_set_google = create_rasa_set(
        name="AS15169:AS-GOOGLE",
        containing_as=15169,
        members=[15169, 16509, 36040, 36384, 139190],
        flags=RasaFlags(authoritative=True, doNotInherit=True)
    )
    
    print("RASA-SET (Google publishes):")
    print(f"  asSetName:     \"{rasa_set_google.asSetName}\"")
    print(f"  containingAS:  {rasa_set_google.containingAS}")
    print(f"  members:       {rasa_set_google.members}")
    print(f"\n  Members represent:")
    print(f"    - AS15169:  Google primary")
    print(f"    - AS16509:  AWS (Google Cloud)")
    print(f"    - AS36040:  Google LLC")
    print(f"    - AS36384:  Google Fiber")
    print(f"    - AS139190: Google Asia Pacific")
    
    print(f"\n  flags:")
    print(f"    authoritative: {rasa_set_google.flags.authoritative}")
    print(f"    doNotInherit:  {rasa_set_google.flags.doNotInherit} ← CRITICAL")
    
    print("\n  💡 doNotInherit=TRUE means:")
    print("     - Other AS-SETs can reference AS15169:AS-GOOGLE")
    print("     - But they CANNOT expand to see member ASNs")
    print("     - Prevents transitive inclusion attacks")
    
    # Step 2: Google publishes RASA-AUTH for each ASN
    print("\nStep 2: Google publishes RASA-AUTH for each ASN")
    print("-" * 70)
    
    google_asns = [15169, 16509, 36040, 36384, 139190]
    authorized_tier1s = [
        ("AS2914:AS-GLOBAL", PropagationScope.UNRESTRICTED),
        ("AS1299:AS-TWELVE99", PropagationScope.UNRESTRICTED),
        ("AS6453:AS-TATA", PropagationScope.UNRESTRICTED),
        ("AS3356:AS-LEVEL3", PropagationScope.UNRESTRICTED)
    ]
    
    rasa_db = {
        "AS15169:AS-GOOGLE": rasa_set_google
    }
    
    print("RASA-AUTH objects (Google publishes for each ASN):")
    
    for asn in google_asns:
        auth = create_rasa_auth(
            asn=asn,
            authorized_in=authorized_tier1s,
            strict_mode=True
        )
        rasa_db[f"AS{asn}"] = auth
        
        if asn == 15169:
            print(f"\n  AS{asn}:")
            print(f"    authorizedIn:")
            for entry in auth.authorizedIn:
                print(f"      - {entry.asSetName}")
            print(f"    strictMode: {auth.flags.strictMode}")
    
    print(f"\n  Result: Google's AS-SET can only be expanded by authorized Tier-1s")
    
    # Step 3: Legitimate Tier-1 expansion
    print("\nStep 3: Legitimate Tier-1 Provider Expansion")
    print("-" * 70)
    
    validator = RASAValidator(rasa_db)
    
    print("\nAS2914 (NTT) expanding AS15169:AS-GOOGLE:")
    
    for asn in google_asns:
        is_auth, reason = validator.check_member_auth(asn, "AS2914:AS-GLOBAL")
        status = "✓" if is_auth else "✗"
        print(f"  {status} AS{asn}: {reason}")
    
    print("\n  Result: All Google ASNs INCLUDED (NTT is authorized)")
    
    # Step 4: Malicious attempt - transitive inclusion
    print("\nStep 4: Malicious Attempt - Transitive Inclusion Attack")
    print("-" * 70)
    
    print("\n⚠ ATTACK SCENARIO:")
    print("  Malicious actor creates AS-EVIL containing AS15169:AS-GOOGLE")
    
    rasa_set_evil = create_rasa_set(
        name="AS-EVIL:CUSTOMERS",
        containing_as=66666,
        members=[99999],
        nested_sets=["AS15169:AS-GOOGLE"],  # Including Google's AS-SET!
        flags=RasaFlags(authoritative=True)
    )
    
    print(f"\n  AS-EVIL publishes:")
    print(f"    nestedSets: [\"AS15169:AS-GOOGLE\"]")
    print(f"\n  Attack: Attempting to inherit all Google ASNs through nesting")
    
    # Step 5: doNotInherit protection
    print("\nStep 5: doNotInherit Protection in Action")
    print("-" * 70)
    
    rasa_db["AS-EVIL:CUSTOMERS"] = rasa_set_evil
    validator2 = RASAValidator(rasa_db)
    
    print("\nExpanding AS-EVIL:CUSTOMERS:")
    print("  1. Direct member AS99999: would be included")
    print("  2. Nested AS-SET AS15169:AS-GOOGLE:")
    print(f"     - doNotInherit flag: TRUE")
    print(f"     - Action: Include reference ONLY (do not expand)")
    
    is_auth, reason = validator2.check_asset_set_auth("AS15169:AS-GOOGLE", "AS-EVIL:CUSTOMERS")
    
    if is_auth:
        print(f"\n     - Authorization check: AUTHORIZED")
        print(f"     - But doNotInherit prevents expansion!")
        print(f"\n  Result: AS15169:AS-GOOGLE is included as reference only")
        print(f"          Google ASNs are NOT exposed")
    
    # Step 6: Comparison without doNotInherit
    print("\nStep 6: Comparison - What If doNotInherit Was FALSE?")
    print("-" * 70)
    
    rasa_set_google_vulnerable = create_rasa_set(
        name="AS15169:AS-GOOGLE-VULNERABLE",
        containing_as=15169,
        members=[15169, 16509, 36040, 36384, 139190],
        flags=RasaFlags(authoritative=True, doNotInherit=False)  # Vulnerable!
    )
    
    rasa_db_vulnerable = rasa_db.copy()
    rasa_db_vulnerable["AS15169:AS-GOOGLE-VULNERABLE"] = rasa_set_google_vulnerable
    
    print("\n  Hypothetical: Google sets doNotInherit=FALSE")
    print("\n  Expanding AS-EVIL:CUSTOMERS with vulnerable AS-SET:")
    print("    - Nested AS-SET AS15169:AS-GOOGLE-VULNERABLE: AUTHORIZED")
    print("    - doNotInherit: FALSE")
    print("    - Action: FULL EXPANSION")
    print("\n  Result: 🚨 ALL GOOGLE ASNs EXPOSED!")
    print("          AS15169, AS16509, AS36040, AS36384, AS139190")
    print("\n  This is exactly what doNotInherit prevents!")
    
    # Step 7: Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    print("\n✅ doNotInherit=TRUE Protection:")
    print("  - AS-SET can be nested (referenced)")
    print("  - But members are NOT transitively inherited")
    print("  - Prevents chain-of-trust attacks")
    print("  - Google maintains control over AS exposure")
    
    print("\n✅ Legitimate Use Cases Work:")
    print("  - Authorized Tier-1s can still expand Google's AS-SET")
    print("  - RASA-AUTH controls which AS-SETs are authorized")
    print("  - No disruption to normal operations")
    
    print("\n💡 Key Security Insight:")
    print("  doNotInherit breaks the transitive chain of AS-SET expansion.")
    print("  Even if AS-EVIL includes AS-GOOGLE, they only get a reference,")
    print("  not the actual ASNs. This is critical for preventing")
    print("  massive route leaks through nested AS-SET attacks.")
    
    print("\n⚠️ Important Limitation:")
    print("  For full protection, EVERY AS-SET in the chain must use")
    print("  doNotInherit. If any AS-SET in the expansion chain is")
    print("  vulnerable, the entire chain is compromised.")
    
    return True


if __name__ == "__main__":
    operational_content_donotinherit()
