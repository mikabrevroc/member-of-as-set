# RASA Proof of Concept

Demonstrates RPKI AS-SET Authorization (RASA) concepts using real IRR data.

## Features

- **IRR Caching**: WHOIS results cached locally for 24 hours (instant 2nd runs)
- **Small AS-SETs**: Fast demos using AS-14061 (DigitalOcean, 4 ASNs)
- **Real Data**: Fetches actual IRR data from RADB/RIPE/APNIC/etc.
- **JunOS Output**: Generates actual router configurations

## Quick Start

```bash
# Run all demos (cached, fast)
python3 demo_all.py

# Individual demos
python3 rasa_poc_cached.py          # Basic expansion
python3 google_peerlock.py          # Peer-lock scenario
python3 google_asset_auth.py        # AS-SET authorization
python3 arelion_rasa_filter.py      # Rejection scenario

# View cache stats
python3 irr_cache.py

# Clear cache
python3 irr_cache.py clear
```

## Removed

The following toy/mock implementations were removed:
- `demo.sh` - Bash demo with simulated data
- `as-set-expander.sh` - Bash AS-SET expander
- `juniper-generator.sh` - Bash config generator
- `simulated-irr/` - Mock IRR database
- `rasa_poc.py` - Mock-based Python POC

All replaced with real WHOIS-based implementations.

## Files

| File | Description |
|------|-------------|
| `demo_all.py` | All demos in one script |
| `demo_all_complete.py` | All 14 scenarios including new POCs |
| `rasa_poc_cached.py` | Basic RASA with caching |
| `google_peerlock.py` | Google peer-lock to HE/Arelion |
| `google_asset_auth.py` | Enforce RADB-only for AS-GOOGLE |
| `arelion_rasa_filter.py` | DigitalOcean rejected from Arelion |
| `juniper_config_diff.py` | Generate config comparisons |
| `irr_cache.py` | WHOIS caching module |
| `rasa_validator.py` | Core RASA validation library |
| `small_as_sets.json` | List of small AS-SETs for testing |

### New POC Scenarios (Draft Examples)

| File | Description | Draft Section |
|------|-------------|---------------|
| `example4_asset_authorization.py` | Nested AS-SET authorized | 6.2 Example 4 |
| `example5_asset_denied.py` | Nested AS-SET denied (strictMode) | 6.2 Example 5 |
| `delegation_customer_managed.py` | Customer-managed delegation | 3.2 Example 1 |
| `delegation_third_party.py` | Third-party management service | 3.2 Example 2 |
| `operational_tier1_attack.py` | Tier-1 provider attack scenario | 10 Example 1 |
| `operational_content_donotinherit.py` | Content provider protection | 10 Example 2 |
| `operational_validator_flow.py` | Complete validator decision flow | 10 Example 3 |
| `operational_partial_deployment.py` | Partial deployment with IRR fallback | 10 Example 6 |
| `circular_detection.py` | Circular reference detection | 9 |

### Mock RASA Objects

| File | Description |
|------|-------------|
| `mock_rasa/google_peerlock.json` | Google ASNs with propagation=directOnly |
| `mock_rasa/google_asset_radbonly.json` | Google AS-SET RADB-only enforcement |
| `mock_rasa/digitalocean_basic.json` | DigitalOcean unrestricted |
| `mock_rasa/digitalocean_strict.json` | DigitalOcean strictMode (no Arelion) |
| `mock_rasa/README.md` | Documentation for mock objects |

## AS-SETs Used

**Small (Fast):**
- AS-14061 (DigitalOcean) - 4 ASNs
- AS-NETFLIX - 5-10 ASNs

**Medium:**
- AS-GOOGLE - 31 ASNs
- AS-AMAZON - 20-30 ASNs
- AS-FACEBOOK - 15-20 ASNs

**Large (Slow without cache):**
- AS2914:AS-US - 200-300 ASNs

## Generated Configs

- `juniper_without_rasa.conf` - Baseline config
- `juniper_with_rasa.conf` - With RASA peer-lock
- `arelion_without_rasa.conf` - Accept all
- `arelion_with_rasa.conf` - Rejected (empty)

## Scenarios Demonstrated

### 1. Basic AS-SET Expansion
Expand AS-14061 and show member ASNs

### 2. RASA Authorization
AS14061 publishes RASA-AUTH, others don't → All authorized

### 3. Peer-Lock (propagation=directOnly)
DigitalOcean sets directOnly → Blocked from HE/Arelion peers

### 4. AS-SET Authorization (RADB-only)
Google's "DO NOT USE" comment cryptographically enforced

### 5. Rejection (strictMode)
DigitalOcean authorizes NTT/Lumen but NOT Arelion → Rejected from Arelion


## Running All Scenarios

### Original 5 Scenarios (Real IRR Data)
python3 demo_all.py

### All 14 Scenarios (Including New Draft Examples)
python3 demo_all_complete.py

### Individual New Scenarios
```bash
# Conflict Examples (Section 6.2)
python3 example4_asset_authorization.py        # Nested AS-SET authorized
python3 example5_asset_denied.py               # Nested AS-SET denied

# Delegation Examples (Section 3.2)
python3 delegation_customer_managed.py         # Customer-managed delegation
python3 delegation_third_party.py              # Third-party management

# Operational Examples (Section 10)
python3 operational_tier1_attack.py            # Tier-1 attack scenario
python3 operational_content_donotinherit.py    # Content provider protection
python3 operational_validator_flow.py          # Validator decision flow
python3 operational_partial_deployment.py      # Partial deployment

# Security Features (Section 9)
python3 circular_detection.py                  # Circular reference detection
```

## New Scenarios Detail

### 6. Nested AS-SET Authorization (Example 4)
**File:** `example4_asset_authorization.py`

Demonstrates when a nested AS-SET is properly authorized to be included in a parent AS-SET.

- AS2914 publishes RASA-SET with nestedSets containing AS1299:AS-TWELVE99
- AS1299 publishes RASA-AUTH with authorizedSet authorizing inclusion
- **Result:** AS1299:AS-TWELVE99 is INCLUDED

### 7. Nested AS-SET Denied (Example 5)
**File:** `example5_asset_denied.py`

Demonstrates unauthorized nested AS-SET inclusion with strictMode.

- AS-EVIL attempts to include AS1299:AS-TWELVE99 without authorization
- AS1299's RASA-AUTH does NOT authorize AS-EVIL:CUSTOMERS
- strictMode=TRUE triggers security event
- **Result:** AS1299:AS-TWELVE99 is EXCLUDED

### 8. Delegation - Customer Managed (Example 1)
**File:** `delegation_customer_managed.py`

Shows how AS-SET owners can delegate publishing authority to customers.

- AS2914 creates delegation token for AS64496
- AS64496 publishes RASA-AUTH using their own certificate
- Validator checks delegation token to verify authorization

### 9. Delegation - Third Party (Example 2)
**File:** `delegation_third_party.py`

Demonstrates multiple AS-SET owners delegating to a management service.

- AS6939, AS1299, and AS2914 delegate to AS-SET-MGMT
- Management service publishes RASA-SETs for each owner
- Scope enforcement prevents unauthorized AS-SET publishing

### 10. Tier-1 Provider Attack (Operational Example 1)
**File:** `operational_tier1_attack.py`

Complete operational workflow showing attack prevention.

- NTT (AS2914) maintains AS2914:AS-GLOBAL with RASA protection
- AS-EVIL attempts to include NTT and NTT's customers
- Attack blocked with security events logged
- Legitimate operations continue unaffected

### 11. Content Provider Protection (Operational Example 2)
**File:** `operational_content_donotinherit.py`

Demonstrates the doNotInherit flag for preventing transitive attacks.

- Google aggregates multiple ASNs under AS15169:AS-GOOGLE
- doNotInherit=TRUE prevents nested expansion
- Malicious AS-SET can reference AS-GOOGLE but cannot see member ASNs

### 12. Validator Decision Flow (Operational Example 3)
**File:** `operational_validator_flow.py`

Step-by-step walkthrough of validator processing.

1. Query RPKI for RASA-SET
2. For each member, query RPKI for RASA-AUTH
3. Check authorizedIn list
4. Apply strictMode logic
5. Process nestedSets with doNotInherit check
6. Return final authorized member list

### 13. Partial Deployment (Operational Example 6)
**File:** `operational_partial_deployment.py`

Shows IRR fallback behavior during transition period.

- Some AS-SETs have RASA (AS2914:AS-GLOBAL, AS15169:AS-GOOGLE)
- Some AS-SETs don't (AS-HURRICANE, AS-AMAZON)
- Validators use RASA when available, fallback to IRR when not

### 14. Circular Reference Detection (Section 9)
**File:** `circular_detection.py`

Prevents infinite loops during AS-SET expansion.

- AS2914:AS-GLOBAL contains AS64496:AS-SET
- AS64496:AS-SET (erroneously) contains AS2914:AS-GLOBAL
- Algorithm detects circular reference
- Expansion stops to prevent infinite loop

## RASA Core Concepts

### Two-Object Design
- **RASA-SET**: Published by AS-SET owner, defines membership
- **RASA-AUTH**: Published by ASN/AS-SET owner, authorizes inclusion

### Authorization Types
- `authorizedAS` - ASN-level authorization
- `authorizedSet` - AS-SET-level authorization

### Flags
- `authoritative` - Use only RASA data, ignore IRR
- `doNotInherit` - Prevent transitive inclusion
- `strictMode` - Reject vs warn on unauthorized inclusion

### Propagation Scope
- `unrestricted` - Default behavior
- `directOnly` - Peer-lock signal for BGP import policy

### Security Features
- Cryptographic verification via RPKI
- Automatic unauthorized inclusion blocking
- Security event logging
- Circular reference prevention

### Deployment
- Incremental adoption (no flag day)
- IRR fallback for non-RASA AS-SETs
- Monitoring and transition tools