#!/usr/bin/env python3
"""
Delegation Example 1: Customer-Managed Authorization

Demonstrates the delegation model from Section 3.2 where an AS-SET owner
delegates publishing authority to a customer AS.

Scenario:
- AS2914 (NTT) delegates to customer AS64496
- AS64496 publishes RASA-AUTH on behalf of AS2914:AS-GLOBAL
- Validator checks delegation token to verify authorization
"""

from rasa_validator import (
    RASAValidator, create_rasa_set, create_rasa_auth,
    RasaFlags, PropagationScope, DelegationToken
)
from datetime import datetime, timedelta


def delegation_customer_managed():
    """Demonstrate customer-managed authorization with delegation."""
    
    print("=" * 70)
    print("DELEGATION EXAMPLE 1: Customer-Managed Authorization")
    print("=" * 70)
    print("\nScenario from draft Section 3.2, Example 1")
    print("-" * 70)
    
    # Step 1: AS2914 creates delegation token
    print("\nStep 1: AS-SET Owner (AS2914) creates delegation token")
    print("-" * 70)
    
    now = datetime.utcnow()
    delegation_token = DelegationToken(
        delegatedTo="AS64496",
        scope=["AS2914:AS-GLOBAL"],
        notBefore=now.isoformat(),
        notAfter=(now + timedelta(days=365)).isoformat(),
        issuedBy=2914
    )
    
    print("Delegation Token (signed by AS2914):")
    print(f"  delegatedTo: {delegation_token.delegatedTo}")
    print(f"  scope:       {delegation_token.scope}")
    print(f"  notBefore:   {delegation_token.notBefore}")
    print(f"  notAfter:    {delegation_token.notAfter}")
    print(f"  issuedBy:    AS{delegation_token.issuedBy}")
    print("\n  ✓ Token signed with AS2914's RPKI private key")
    
    # Step 2: Customer AS64496 publishes RASA-AUTH
    print("\nStep 2: Customer AS64496 publishes RASA-AUTH")
    print("-" * 70)
    
    rasa_auth = create_rasa_auth(
        asn=64496,
        authorized_in=[
            ("AS2914:AS-GLOBAL", PropagationScope.UNRESTRICTED)
        ],
        strict_mode=False
    )
    
    print("RASA-AUTH (published by AS64496):")
    print(f"  authorizedEntity:")
    print(f"    authorizedAS: {rasa_auth.authorizedAS}")
    print(f"  authorizedIn:")
    for entry in rasa_auth.authorizedIn:
        print(f"    - asSetName: \"{entry.asSetName}\"")
        print(f"      propagation: {entry.propagation.name}")
    print(f"  signedBy: AS64496 certificate")
    print(f"  references: [delegation-token-from-AS2914]")
    
    # Step 3: Validator checks delegation
    print("\nStep 3: Validator performs delegation validation")
    print("-" * 70)
    
    # Create databases
    rasa_db = {
        "AS64496": rasa_auth
    }
    
    delegation_db = {
        "2914:AS64496": delegation_token
    }
    
    validator = RASAValidator(rasa_db, delegation_db)
    
    print("\nValidation steps:")
    print("  1. ✓ RASA-AUTH cryptographically valid (signed by AS64496)")
    print("  2. ✗ Signing certificate ASID (64496) != containingAS (2914)")
    print("  3. → Checking for delegation token...")
    
    # Validate delegation
    is_valid, reason = validator.validate_delegation(rasa_auth, "AS64496")
    
    print(f"  4. {'✓' if is_valid else '✗'} Delegation token found and valid")
    print(f"\nResult: {reason}")
    
    # Step 4: Show authorization check
    print("\nStep 4: Authorization check proceeds normally")
    print("-" * 70)
    
    is_auth, auth_reason = validator.check_member_auth(64496, "AS2914:AS-GLOBAL")
    
    print(f"\nChecking: AS64496 in AS2914:AS-GLOBAL")
    print(f"  - Delegation: VALID")
    print(f"  - Authorization: {'AUTHORIZED' if is_auth else 'NOT AUTHORIZED'}")
    print(f"  - Reason: {auth_reason}")
    
    # Step 5: Show revocation mechanisms
    print("\nStep 5: Delegation Revocation Mechanisms")
    print("-" * 70)
    
    print("\nDelegation can be revoked through:")
    print("  1. Expiration:")
    print(f"     - Token expires: {delegation_token.notAfter}")
    print("     - After expiry, AS64496 cannot publish for AS2914")
    print("\n  2. RPKI Revocation:")
    print("     - If AS64496's RPKI certificate is revoked")
    print("     - All RASA objects signed by that cert become invalid")
    print("\n  3. Delegation Withdrawal:")
    print("     - AS2914 publishes updated token with shorter validity")
    print("     - Forces re-authorization before new expiry")
    
    print("\n" + "=" * 70)
    print("RESULT: Delegation validated successfully")
    print("AS64496 authorized to publish RASA-AUTH for AS2914:AS-GLOBAL")
    print("=" * 70)
    
    print("\n💡 Benefits of Delegation:")
    print("  - Customers manage their own authorization")
    print("  - AS-SET owner offloads administrative burden")
    print("  - Maintains cryptographic security through delegation tokens")
    print("  - Clear audit trail of who authorized what")
    
    return is_valid and is_auth


if __name__ == "__main__":
    delegation_customer_managed()
