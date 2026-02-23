#!/usr/bin/env python3
"""
Operational Example 6: Partial Deployment Scenario

Demonstrates the partial deployment fallback behavior from Section 10.6.
Shows how validators handle AS-SETs with and without RASA during transition.
"""

from rasa_validator import (
    RASAValidator, create_rasa_set, create_rasa_auth,
    RasaFlags, PropagationScope
)


def operational_partial_deployment():
    """Demonstrate partial deployment with IRR fallback."""
    
    print("=" * 70)
    print("OPERATIONAL EXAMPLE 6: Partial Deployment Scenario")
    print("=" * 70)
    print("\nScenario from draft Section 10.6, Example 6")
    print("Demonstrates IRR fallback during RASA transition period")
    print("-" * 70)
    
    # Setup: Mixed RASA deployment
    print("\n📋 DEPLOYMENT STATE: Mixed RASA Adoption")
    print("-" * 70)
    
    print("\nAS-SETs with RASA:")
    print("  ✓ AS2914:AS-GLOBAL (NTT) - Full RASA deployed")
    print("  ✓ AS15169:AS-GOOGLE (Google) - Full RASA deployed")
    
    print("\nAS-SETs WITHOUT RASA:")
    print("  ✗ AS-HURRICANE (Hurricane Electric) - No RASA")
    print("  ✗ AS-AMAZON (Amazon) - No RASA")
    print("  ✗ AS-LEVEL3 (Lumen) - No RASA")
    
    print("\nTransition period: Some AS-SETs have RASA, others don't")
    print("Validators must handle both cases gracefully")
    
    # Create partial RASA database
    rasa_set_ntt = create_rasa_set(
        name="AS2914:AS-GLOBAL",
        containing_as=2914,
        members=[64496, 64497, 15169],
        flags=RasaFlags(authoritative=True)
    )
    
    rasa_set_google = create_rasa_set(
        name="AS15169:AS-GOOGLE",
        containing_as=15169,
        members=[15169, 16509, 36040],
        flags=RasaFlags(authoritative=True, doNotInherit=True)
    )
    
    auth_google = create_rasa_auth(
        asn=15169,
        authorized_in=[("AS2914:AS-GLOBAL", PropagationScope.UNRESTRICTED)],
        strict_mode=True
    )
    
    # Partial RASA database - many AS-SETs missing
    rasa_db = {
        "AS2914:AS-GLOBAL": rasa_set_ntt,
        "AS15169:AS-GOOGLE": rasa_set_google,
        "AS15169": auth_google
    }
    
    # Scenario 1: RASA-available AS-SET
    print("\n" + "=" * 70)
    print("SCENARIO 1: AS-SET WITH RASA (AS2914:AS-GLOBAL)")
    print("=" * 70)
    
    print("\nOperator wants to expand AS2914:AS-GLOBAL")
    print("\nValidator logic:")
    print("  1. Query RPKI for RASA-SET 'AS2914:AS-GLOBAL'")
    print("     Result: ✓ Found, authoritative=TRUE")
    print("\n  2. Check RASA-AUTH for each member:")
    
    validator = RASAValidator(rasa_db)
    
    for asn in [64496, 64497, 15169]:
        is_auth, reason = validator.check_member_auth(asn, "AS2914:AS-GLOBAL")
        status = "✓" if is_auth else "✗"
        auth_type = "RASA-AUTH" if f"AS{asn}" in rasa_db else "None (default allow)"
        print(f"     AS{asn}: {status} {auth_type} - {reason}")
    
    print("\n  Result: Use RASA-SET members, skip IRR query")
    print("  Filter includes: AS64496, AS64497, AS15169")
    
    # Scenario 2: RASA-unavailable AS-SET (fallback to IRR)
    print("\n" + "=" * 70)
    print("SCENARIO 2: AS-SET WITHOUT RASA (AS-HURRICANE)")
    print("=" * 70)
    
    print("\nOperator wants to expand AS-HURRICANE")
    print("\nValidator logic:")
    print("  1. Query RPKI for RASA-SET 'AS-HURRICANE'")
    print("     Result: ✗ Not found")
    print("\n  2. Fallback to IRR:")
    print("     Query whois.radb.net for AS-HURRICANE")
    print("     Result: ✓ Found (simulated)")
    print("     Members: AS1, AS2, AS3, ... AS6939, ...")
    print("\n  3. No RASA-AUTH validation (RASA not available)")
    print("     All IRR members included")
    
    print("\n  ⚠ WARNING: Using IRR data without cryptographic verification")
    print("     This is expected during partial deployment")
    
    # Scenario 3: Operator configuration options
    print("\n" + "=" * 70)
    print("SCENARIO 3: Operator Configuration Options")
    print("=" * 70)
    
    print("\nConfiguration options for RASA-unavailable AS-SETs:")
    
    print("\n  Option A: Default allow (backward compatible)")
    print("    Behavior: Use IRR data when RASA unavailable")
    print("    Risk: Potential for unauthorized inclusion")
    print("    Use case: General operations during transition")
    
    print("\n  Option B: Require RASA for specific AS-SETs")
    print("    Config: require_rasa = [\"AS2914:AS-GLOBAL\", \"AS15169:AS-GOOGLE\"]")
    print("    Behavior: Reject expansion if RASA not found")
    print("    Risk: May break existing filters")
    print("    Use case: High-security requirements")
    
    print("\n  Option C: Log warnings")
    print("    Config: log_warnings = True")
    print("    Behavior: Use IRR but log warning")
    print("    Example log: 'WARNING: Using IRR for AS-HURRICANE (no RASA)'")
    print("    Use case: Monitoring and gradual transition")
    
    # Scenario 4: Monitoring dashboard
    print("\n" + "=" * 70)
    print("SCENARIO 4: Monitoring Dashboard Example")
    print("=" * 70)
    
    print("\nRASA Adoption Statistics:")
    print(f"{'─' * 70}")
    print(f"{'AS-SET':<25} {'Has RASA':<12} {'IRR Fallback':<15} {'Status':<15}")
    print(f"{'─' * 70}")
    
    assets = [
        ("AS2914:AS-GLOBAL", True, "No", "✓ Secured"),
        ("AS15169:AS-GOOGLE", True, "No", "✓ Secured"),
        ("AS-HURRICANE", False, "Yes", "⚠ Fallback"),
        ("AS-AMAZON", False, "Yes", "⚠ Fallback"),
        ("AS-LEVEL3", False, "Yes", "⚠ Fallback"),
    ]
    
    for asset, has_rasa, fallback, status in assets:
        rasa_status = "Yes" if has_rasa else "No"
        print(f"{asset:<25} {rasa_status:<12} {fallback:<15} {status:<15}")
    
    print(f"{'─' * 70}")
    
    secured = sum(1 for _, has_rasa, _, _ in assets if has_rasa)
    total = len(assets)
    print(f"\nRASA Adoption: {secured}/{total} ({secured/total*100:.0f}%)")
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    print("\n✅ Partial Deployment Strategy:")
    print("  • RASA-available AS-SETs: Use cryptographic verification")
    print("  • RASA-unavailable AS-SETs: Fallback to IRR with warnings")
    print("  • No flag day required - incremental adoption")
    print("  • Operators can configure strictness per AS-SET")
    
    print("\n⚠️ Security Considerations:")
    print("  • IRR fallback bypasses cryptographic verification")
    print("  • Operators should monitor fallback usage")
    print("  • Gradually increase RASA requirements over time")
    print("  • High-value AS-SETs should require RASA first")
    
    print("\n💡 Transition Best Practices:")
    print("  1. Start with high-value AS-SETs (Tier-1s, content providers)")
    print("  2. Enable logging to monitor IRR fallback usage")
    print("  3. Notify operators when their AS-SETs lack RASA")
    print("  4. Provide tooling for easy RASA object creation")
    print("  5. After sufficient adoption, require RASA for all")
    
    return True


if __name__ == "__main__":
    operational_partial_deployment()
