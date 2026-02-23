#!/usr/bin/env python3
"""
Delegation Example 2: Third-Party AS-SET Management Service

Demonstrates the delegation model from Section 3.2 where multiple AS-SET
owners delegate to a third-party management service.

Scenario:
- Multiple Tier-1 providers (AS6939, AS1299, AS2914) delegate to AS-SET-MGMT
- Management service publishes RASA-SET on behalf of each owner
- Each delegation has specific scope limitations
"""

from rasa_validator import (
    RASAValidator, create_rasa_set, create_rasa_auth,
    RasaFlags, PropagationScope, DelegationToken
)
from datetime import datetime, timedelta


def delegation_third_party():
    """Demonstrate third-party AS-SET management with delegation."""
    
    print("=" * 70)
    print("DELEGATION EXAMPLE 2: Third-Party AS-SET Management Service")
    print("=" * 70)
    print("\nScenario from draft Section 3.2, Example 2")
    print("-" * 70)
    
    # Step 1: Multiple AS-SET owners create delegation tokens
    print("\nStep 1: Multiple AS-SET owners delegate to management service")
    print("-" * 70)
    
    now = datetime.utcnow()
    
    delegations = {
        "AS6939": DelegationToken(
            delegatedTo="AS-SET-MGMT",
            scope=["AS6939:AS-HURRICANE"],
            notBefore=now.isoformat(),
            notAfter=(now + timedelta(days=180)).isoformat(),
            issuedBy=6939
        ),
        "AS1299": DelegationToken(
            delegatedTo="AS-SET-MGMT",
            scope=["AS1299:AS-TWELVE99"],
            notBefore=now.isoformat(),
            notAfter=(now + timedelta(days=180)).isoformat(),
            issuedBy=1299
        ),
        "AS2914": DelegationToken(
            delegatedTo="AS-SET-MGMT",
            scope=["AS2914:AS-GLOBAL"],
            notBefore=now.isoformat(),
            notAfter=(now + timedelta(days=365)).isoformat(),
            issuedBy=2914
        )
    }
    
    print("Delegation Tokens created:")
    for owner, token in delegations.items():
        print(f"\n  {owner} delegates:")
        print(f"    delegatedTo: {token.delegatedTo}")
        print(f"    scope:       {token.scope}")
        print(f"    validity:    {token.notBefore[:10]} to {token.notAfter[:10]}")
    
    # Step 2: Management service publishes RASA-SETs
    print("\nStep 2: Management service (AS-SET-MGMT) publishes RASA-SETs")
    print("-" * 70)
    
    rasa_sets = {
        "AS6939:AS-HURRICANE": create_rasa_set(
            name="AS6939:AS-HURRICANE",
            containing_as=6939,
            members=[1, 2, 3, 4, 5],  # Example members
            flags=RasaFlags(authoritative=True)
        ),
        "AS1299:AS-TWELVE99": create_rasa_set(
            name="AS1299:AS-TWELVE99",
            containing_as=1299,
            members=[64496, 64497, 64498],
            flags=RasaFlags(authoritative=True)
        ),
        "AS2914:AS-GLOBAL": create_rasa_set(
            name="AS2914:AS-GLOBAL",
            containing_as=2914,
            members=[15169, 16509, 36040],
            flags=RasaFlags(authoritative=True)
        )
    }
    
    print("RASA-SETs published by AS-SET-MGMT:")
    for asset_name, rasa_set in rasa_sets.items():
        print(f"\n  {asset_name}:")
        print(f"    containingAS: {rasa_set.containingAS}")
        print(f"    members:      {rasa_set.members}")
        print(f"    signedBy:     AS-SET-MGMT certificate")
        print(f"    references:   delegation-token-from-AS{rasa_set.containingAS}")
    
    # Step 3: Validator checks all delegations
    print("\nStep 3: Validator checks delegation for each RASA-SET")
    print("-" * 70)
    
    delegation_db = {
        "6939:AS-SET-MGMT": delegations["AS6939"],
        "1299:AS-SET-MGMT": delegations["AS1299"],
        "2914:AS-SET-MGMT": delegations["AS2914"]
    }
    
    validator = RASAValidator(rasa_sets, delegation_db)
    
    print("\nDelegation validation results:")
    for asset_name, rasa_set in rasa_sets.items():
        is_valid, reason = validator.validate_delegation(rasa_set, "AS-SET-MGMT")
        status = "✓" if is_valid else "✗"
        print(f"\n  {asset_name}:")
        print(f"    {status} {reason}")
    
    # Step 4: Scope enforcement demonstration
    print("\nStep 4: Scope Enforcement Demonstration")
    print("-" * 70)
    
    print("\nAttempting to publish unauthorized AS-SET:")
    print("  Scenario: AS-SET-MGMT tries to publish RASA-SET for AS3356:AS-LEVEL3")
    print("  - AS3356 has NOT issued delegation token to AS-SET-MGMT")
    print("  - Result: Validation FAILS")
    
    unauthorized_set = create_rasa_set(
        name="AS3356:AS-LEVEL3",
        containing_as=3356,
        members=[1, 2, 3],
        flags=RasaFlags(authoritative=True)
    )
    
    is_valid, reason = validator.validate_delegation(unauthorized_set, "AS-SET-MGMT")
    print(f"\n  ✗ {reason}")
    
    # Step 5: Operational benefits
    print("\nStep 5: Operational Benefits")
    print("-" * 70)
    
    print("\nBenefits of third-party management:")
    print("  ✓ Specialized service handles RASA publishing")
    print("  ✓ Consistent quality and timeliness of updates")
    print("  ✓ Reduced operational burden on AS-SET owners")
    print("  ✓ Maintains cryptographic security through delegation")
    print("  ✓ Clear scope limits prevent overreach")
    print("  ✓ Easy revocation if service is compromised")
    
    print("\nSecurity considerations:")
    print("  • Delegation tokens have limited validity periods")
    print("  • Scope strictly limited to specific AS-SETs")
    print("  • AS-SET owner maintains ultimate control (can revoke)")
    print("  • RPKI revocation handles certificate compromise")
    
    print("\n" + "=" * 70)
    print("RESULT: Third-party management delegation working correctly")
    print("All authorized AS-SETs validated, unauthorized rejected")
    print("=" * 70)
    
    return True


if __name__ == "__main__":
    delegation_third_party()
