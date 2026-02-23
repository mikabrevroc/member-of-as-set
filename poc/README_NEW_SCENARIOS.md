# RASA POC - New Scenarios Documentation

This directory contains comprehensive proof-of-concept implementations for the RASA (RPKI AS-SET Authorization) protocol.

## New Scenarios (9 Additional POCs)

### Conflict Examples (Section 6.2)

#### `example4_asset_authorization.py`
**Example 4: AS-SET Authorization (Nested AS-SET Authorized)**

Demonstrates when a nested AS-SET is properly authorized to be included in a parent AS-SET.

**Scenario:**
- AS2914 publishes RASA-SET with nestedSets containing AS1299:AS-TWELVE99
- AS1299 publishes RASA-AUTH with authorizedSet authorizing inclusion in AS2914:AS-GLOBAL
- Result: AS1299:AS-TWELVE99 is INCLUDED (authorized)

**Key Concepts:**
- `authorizedSet` field (vs `authorizedAS`)
- Nested AS-SET authorization
- AS-SET-level authorization (not just ASN-level)

#### `example5_asset_denied.py`
**Example 5: AS-SET Authorization Denied**

Demonstrates when a nested AS-SET is NOT authorized, showing strictMode behavior.

**Scenario:**
- AS-EVIL attempts to include AS1299:AS-TWELVE99 without authorization
- AS1299's RASA-AUTH does NOT authorize AS-EVIL:CUSTOMERS
- strictMode=TRUE means security event is logged
- Result: AS1299:AS-TWELVE99 is EXCLUDED

**Key Concepts:**
- Unauthorized AS-SET inclusion blocked
- strictMode security events
- Attack prevention

---

### Delegation Examples (Section 3.2)

#### `delegation_customer_managed.py`
**Delegation Example 1: Customer-Managed Authorization**

Shows how AS-SET owners can delegate publishing authority to customers.

**Scenario:**
- AS2914 creates delegation token for AS64496
- AS64496 publishes RASA-AUTH using their own certificate
- Validator checks delegation token to verify authorization

**Key Concepts:**
- Delegation tokens
- Publishing on behalf of another AS
- Token expiration and revocation

#### `delegation_third_party.py`
**Delegation Example 2: Third-Party AS-SET Management Service**

Demonstrates multiple AS-SET owners delegating to a management service.

**Scenario:**
- AS6939, AS1299, and AS2914 delegate to AS-SET-MGMT
- Management service publishes RASA-SETs for each owner
- Scope enforcement prevents unauthorized AS-SET publishing

**Key Concepts:**
- Multi-party delegation
- Scope limitations
- Third-party management

---

### Operational Examples (Section 10)

#### `operational_tier1_attack.py`
**Operational Example 1: Tier-1 Provider with Attack Scenario**

Complete operational workflow showing attack prevention.

**Scenario:**
- NTT (AS2914) maintains AS2914:AS-GLOBAL with RASA protection
- Multiple customers with various strictMode settings
- AS-EVIL attempts to include NTT and NTT's customers
- Attack blocked with security events logged

**Key Concepts:**
- Complete operational workflow
- Attack detection and prevention
- Security event logging
- Legitimate operations continue unaffected

#### `operational_content_donotinherit.py`
**Operational Example 2: Content Provider Multi-AS Protection**

Demonstrates the critical doNotInherit flag for preventing transitive attacks.

**Scenario:**
- Google aggregates multiple ASNs under AS15169:AS-GOOGLE
- doNotInherit=TRUE prevents nested expansion
- Malicious AS-SET can reference AS-GOOGLE but cannot see member ASNs
- Comparison shows what happens without protection

**Key Concepts:**
- doNotInherit flag
- Transitive attack prevention
- Chain-of-trust breaking
- Content provider protection

#### `operational_validator_flow.py`
**Operational Example 3: Complete Validator Decision Flow**

Step-by-step walkthrough of validator processing.

**Scenario:**
- Validator processes AS2914:AS-GLOBAL
- Shows exact algorithm steps:
  1. Query RPKI for RASA-SET
  2. For each member, query RPKI for RASA-AUTH
  3. Check authorizedIn list
  4. Apply strictMode logic
  5. Process nestedSets with doNotInherit check
  6. Return final authorized member list

**Key Concepts:**
- Complete validator algorithm
- Step-by-step decision flow
- Different authorization outcomes:
  - Explicit authorization (included)
  - Explicit refusal (excluded)
  - Default allow (no RASA-AUTH)

#### `operational_partial_deployment.py`
**Operational Example 6: Partial Deployment Scenario**

Shows IRR fallback behavior during transition period.

**Scenario:**
- Some AS-SETs have RASA (AS2914:AS-GLOBAL, AS15169:AS-GOOGLE)
- Some AS-SETs don't (AS-HURRICANE, AS-AMAZON)
- Validators use RASA when available, fallback to IRR when not
- Monitoring dashboard shows adoption statistics

**Key Concepts:**
- Partial deployment strategy
- IRR fallback
- No flag day required
- Operator configuration options
- Transition best practices

---

### Security Features (Section 9)

#### `circular_detection.py`
**Circular Reference Detection**

Prevents infinite loops during AS-SET expansion.

**Scenario:**
- AS2914:AS-GLOBAL contains AS64496:AS-SET
- AS64496:AS-SET (erroneously) contains AS2914:AS-GLOBAL
- Algorithm detects circular reference
- Expansion stops to prevent infinite loop

**Key Concepts:**
- Circular reference detection algorithm
- "seen" set tracking
- Backtracking and valid reuse
- DoS prevention

---

## Shared Infrastructure

### `rasa_validator.py`
Core validation library providing:
- `RASAValidator` class implementing specification algorithms
- Data classes: `RasaSetContent`, `RasaAuthContent`, `DelegationToken`
- Helper functions: `create_rasa_set()`, `create_rasa_auth()`
- Validation methods:
  - `check_member_auth()` - ASN authorization
  - `check_asset_set_auth()` - AS-SET authorization
  - `validate_delegation()` - Delegation verification
  - `expand_with_rasa()` - Full AS-SET expansion

---

## Running the Scenarios

### Run All Scenarios
```bash
python3 demo_all_complete.py
```

### Run Individual Scenarios
```bash
# Conflict Examples
python3 example4_asset_authorization.py
python3 example5_asset_denied.py

# Delegation Examples
python3 delegation_customer_managed.py
python3 delegation_third_party.py

# Operational Examples
python3 operational_tier1_attack.py
python3 operational_content_donotinherit.py
python3 operational_validator_flow.py
python3 operational_partial_deployment.py

# Security Features
python3 circular_detection.py
```

### Test the Validator Library
```bash
python3 rasa_validator.py
```

---

## Scenario Coverage Summary

| Section | Example | File | Status |
|---------|---------|------|--------|
| 6.2 | Example 4 | `example4_asset_authorization.py` | ✅ Implemented |
| 6.2 | Example 5 | `example5_asset_denied.py` | ✅ Implemented |
| 3.2 | Example 1 | `delegation_customer_managed.py` | ✅ Implemented |
| 3.2 | Example 2 | `delegation_third_party.py` | ✅ Implemented |
| 10 | Example 1 | `operational_tier1_attack.py` | ✅ Implemented |
| 10 | Example 2 | `operational_content_donotinherit.py` | ✅ Implemented |
| 10 | Example 3 | `operational_validator_flow.py` | ✅ Implemented |
| 10 | Example 6 | `operational_partial_deployment.py` | ✅ Implemented |
| 9 | Algorithm | `circular_detection.py` | ✅ Implemented |

**Total: 9 new scenarios implemented**

---

## Key RASA Concepts Demonstrated

1. **Two-Object Design**
   - RASA-SET: Published by AS-SET owner, defines membership
   - RASA-AUTH: Published by ASN/AS-SET owner, authorizes inclusion

2. **Authorization Types**
   - ASN authorization (authorizedAS)
   - AS-SET authorization (authorizedSet)

3. **Flags**
   - `authoritative`: Use only RASA data, ignore IRR
   - `doNotInherit`: Prevent transitive inclusion
   - `strictMode`: Reject vs warn on unauthorized inclusion

4. **Propagation Scope**
   - `unrestricted`: Default behavior
   - `directOnly`: Peer-lock signal for BGP import policy

5. **Delegation**
   - Customer-managed authorization
   - Third-party management services
   - Delegation token validation

6. **Security Features**
   - Cryptographic verification via RPKI
   - Automatic unauthorized inclusion blocking
   - Security event logging
   - Circular reference prevention

7. **Deployment**
   - Incremental adoption (no flag day)
   - IRR fallback for non-RASA AS-SETs
   - Monitoring and transition tools
