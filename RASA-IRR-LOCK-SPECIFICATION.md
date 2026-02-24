# RASA IRR Database Lock Specification

## Executive Summary

This document specifies extensions to the RASA protocol to support **IRR Database Lock Mode** - enabling operators to cryptographically lock which IRR database (RADB, RIPE, etc.) their AS-SET is authoritative from, without requiring full migration away from IRR.

## Core Use Case: AS2914 Example

**Scenario:**
- AS2914 has `AS2914:AS-GLOBAL` in RADB
- They want cryptographic assurance that tools only accept their AS-SET from RADB
- They DON'T want to maintain a separate RASA-SET with duplicate members

**Solution:**
```asn1
RasaSetContent ::= SEQUENCE {
  version          [0] INTEGER DEFAULT 0,
  asSetName            UTF8String,          -- "AS2914:AS-GLOBAL"
  containingAS         ASID,                -- 2914
  members              SEQUENCE OF ASID,    -- EMPTY for lock-only mode
  nestedSets           SEQUENCE OF UTF8String OPTIONAL,
  irrSource            UTF8String,          -- "RADB" (REQUIRED for lock mode)
  fallbackMode         FallbackMode,        -- irrLock(1)
  flags                RasaFlags OPTIONAL,
  notBefore            GeneralizedTime,
  notAfter             GeneralizedTime
}
```

**Result:**
- RASA-aware tools query ONLY RADB for AS2914:AS-GLOBAL
- Same AS-SET from RIPE/ARIN is cryptographically rejected
- AS2914 maintains single AS-SET in RADB (no duplication)
- Incremental deployment without changing IRR workflow

---

## Specification Changes

### 1. New ASN.1 Types

#### FallbackMode Enumeration
```asn1
FallbackMode ::= ENUMERATED {
    irrFallback(0),    -- Use IRR alongside RASA (default, backward compatible)
    irrLock(1),        -- Lock to specific IRR database only
    rasaOnly(2)        -- RASA data only, ignore IRR
}
```

**Semantics:**
- **irrFallback(0)**: Default behavior. RASA data supplements IRR data. Tools may query both.
- **irrLock(1)**: Cryptographic lock. Tools MUST query only the specified IRR database (`irrSource`). Reject same AS-SET from other databases.
- **rasaOnly(2)**: RASA replaces IRR. Tools use only RASA data, no IRR queries.

#### Updated RasaSetContent
```asn1
RasaSetContent ::= SEQUENCE {
  version          [0] INTEGER DEFAULT 0,
  asSetName            UTF8String,
  containingAS         ASID,
  members              SEQUENCE OF ASID,
  nestedSets           SEQUENCE OF UTF8String OPTIONAL,
  irrSource            UTF8String OPTIONAL,  -- REQUIRED when fallbackMode=irrLock
  fallbackMode         FallbackMode DEFAULT irrFallback,
  flags                RasaFlags OPTIONAL,
  notBefore            GeneralizedTime,
  notAfter             GeneralizedTime
}
```

#### Updated RasaAuthContent
```asn1
RasaAuthContent ::= SEQUENCE {
  version          [0] INTEGER DEFAULT 0,
  authorizedEntity CHOICE {
     authorizedAS        ASID,
     authorizedSet       UTF8String
  },
  authorizedIn         SEQUENCE OF AuthorizedEntry,
  fallbackMode         FallbackMode OPTIONAL,  -- Per-AS-SET override
  flags                RasaAuthFlags OPTIONAL,
  notBefore            GeneralizedTime,
  notAfter             GeneralizedTime
}
```

### 2. JSON Output Format Extensions

#### RASA-SET JSON (for bgpq4/rpki-client)
```json
{
  "rasasets": [
    {
      "rasaset": {
        "version": 0,
        "asset": "AS2914:AS-GLOBAL",
        "containing_as": 2914,
        "members": [],
        "nested_sets": [],
        "irr_source": "RADB",
        "fallback_mode": "irrLock",
        "flags": [],
        "not_before": "2024-01-01T00:00:00Z",
        "not_after": "2025-01-01T00:00:00Z"
      }
    }
  ]
}
```

#### Tool Behavior Matrix

| fallback_mode | Members Empty | Tool Behavior |
|---------------|---------------|---------------|
| irrFallback | No | Use RASA members + query IRR |
| irrFallback | Yes | Query IRR only |
| irrLock | No | **Error**: Cannot lock with explicit members |
| irrLock | Yes | Query ONLY specified IRR database |
| rasaOnly | No | Use RASA members only |
| rasaOnly | Yes | **Error**: Empty AS-SET with no fallback |

### 3. IRR Source Namespace Registry

Standard IRR database identifiers:

| Identifier | Database | Description |
|------------|----------|-------------|
| RADB | Routing Arbiter Database | Original IRR, global |
| RIPE | RIPE Database | European RIR |
| ARIN | ARIN Database | American RIR |
| APNIC | APNIC Database | Asia-Pacific RIR |
| LACNIC | LACNIC Database | Latin America RIR |
| AFRINIC | AFRINIC Database | Africa RIR |
| NTTCOM | NTT Communications | Private IRR |
| ALTDB | ALTDB | Alternative database |
| BELL | Bell Canada | Private IRR |
| LEVEL3 | Level3/CenturyLink | Private IRR |

**Note**: Private IRR identifiers are maintained by the respective organizations.

### 4. Validation Rules

#### RASA-SET Validation
1. **fallbackMode=irrLock**:
   - MUST have empty `members` sequence
   - MUST have empty `nestedSets` (if present)
   - MUST have `irrSource` field present
   - MUST have valid IRR source identifier

2. **fallbackMode=irrFallback** (default):
   - MAY have `members` and/or query IRR
   - Standard bidirectional verification applies

3. **fallbackMode=rasaOnly**:
   - MUST have non-empty `members`
   - Tools MUST NOT query IRR
   - Authoritative RASA replaces IRR

#### Tool Implementation Requirements

For tools implementing IRR Database Lock:

```python
def expand_asset(asset_name, rasa_config):
    rasa_set = lookup_rasa_set(asset_name)
    
    if rasa_set:
        if rasa_set.fallback_mode == "irrLock":
            # Query ONLY the locked IRR database
            return query_irr(asset_name, source=rasa_set.irr_source)
        elif rasa_set.fallback_mode == "rasaOnly":
            # Use RASA members only
            return rasa_set.members
        else:  # irrFallback
            # Merge RASA + IRR (standard behavior)
            rasa_members = rasa_set.members
            irr_members = query_irr(asset_name)
            return merge(rasa_members, irr_members)
    else:
        # No RASA, query all IRR databases (legacy behavior)
        return query_irr(asset_name)
```

### 5. Namespace Collision Handling

**Problem:** Same AS-SET name exists on multiple IRR databases:
- AS-EXAMPLE in RADB: members = [AS1, AS2]
- AS-EXAMPLE in RIPE: members = [AS3, AS4]

**Solution with IRR Lock:**
1. AS-EXAMPLE owner publishes RASA-SET with `fallbackMode=irrLock` and `irrSource=RADB`
2. RASA-aware tools reject AS-EXAMPLE from RIPE
3. Only RADB version is accepted

**Without IRR Lock:**
1. AS-EXAMPLE owner publishes RASA-SET with `fallbackMode=irrFallback`
2. Tools merge members from both sources: [AS1, AS2, AS3, AS4]
3. RASA-AUTH provides authorization filtering

---

## Deployment Scenarios

### Scenario 1: Pure IRR Lock (Recommended First Step)
**Actor:** AS2914 with AS2914:AS-GLOBAL in RADB  
**Goal:** Prevent AS-SET hijacking from other databases  
**Action:**
```asn1
RasaSetContent {
  asSetName: "AS2914:AS-GLOBAL",
  containingAS: 2914,
  members: [],           -- Empty!
  irrSource: "RADB",
  fallbackMode: irrLock  -- Lock to RADB only
}
```
**Result:**
- Zero changes to IRR workflow
- Cryptographic assurance of data source
- Tools reject RIPE/ARIN versions

### Scenario 2: Hybrid with Member Override
**Actor:** AS64496 with RASA-capable customers  
**Goal:** Use RASA for customers, IRR for legacy  
**Action:**
```asn1
RasaSetContent {
  asSetName: "AS64496:AS-CUSTOMERS",
  containingAS: 64496,
  members: [AS65001, AS65002],  -- RASA-managed customers
  irrSource: "RADB",
  fallbackMode: irrFallback     -- Merge RASA + IRR
}
```
**Result:**
- New customers added via RASA
- Legacy customers still in RADB
- Gradual migration path

### Scenario 3: Full RASA Replacement
**Actor:** New network, no IRR legacy  
**Goal:** Use RASA exclusively  
**Action:**
```asn1
RasaSetContent {
  asSetName: "AS65000:AS-NETWORK",
  containingAS: 65000,
  members: [AS65001, AS65002, AS65003],
  fallbackMode: rasaOnly  -- No IRR queries
}
```
**Result:**
- Pure RASA deployment
- No IRR dependencies
- Future-proof architecture

---

## Backward Compatibility

### RPKI-Only Tools
Tools without RASA support ignore RASA objects, query all IRR databases as before.

### RASA-Aware Tools
- **Old format** (no fallbackMode): Treat as `irrFallback(0)`
- **New format**: Respect `fallbackMode` setting

### IRR Database Operators
- No changes required to IRR software
- RASA is external verification layer
- Existing workflows unaffected

---

## Security Considerations

### 1. IRR Database Compromise
If RADB is compromised and AS-SET modified:
- RASA-SET still validates cryptographic signature
- Attack requires compromising both RADB AND RPKI
- Detection possible via monitoring

### 2. RPKI Key Compromise
If AS2914's RPKI key is compromised:
- Attacker can publish malicious RASA-SET
- Mitigation: RPKI revocation (standard procedure)
- Monitoring can detect unexpected changes

### 3. Partial Adoption Attacks
Attacker publishes fake AS-SET on unlocked database:
- RASA-aware tools reject (locked to authorized source)
- Legacy tools may accept (operational risk)
- Incentive for operators to adopt RASA-lock

---

## Implementation Checklist

### Phase 1: Specification (This Document)
- [x] ASN.1 schema definitions
- [x] JSON output format
- [x] Validation rules
- [x] Deployment scenarios

### Phase 2: Reference Implementation
- [ ] Update rpki-client ASN.1 parser
- [ ] Add fallbackMode to JSON output
- [ ] Update bgpq4 RASA library
- [ ] Implement IRR lock logic

### Phase 3: Testing
- [ ] Unit tests for each fallbackMode
- [ ] Integration tests with real IRR data
- [ ] End-to-end validation
- [ ] Performance benchmarks

### Phase 4: Documentation
- [ ] Operator deployment guide
- [ ] Migration cookbook
- [ ] Troubleshooting guide
- [ ] Security best practices

---

## IANA Considerations

### RPKI Signed Objects Registry
Add to "RPKI Signed Objects" registry:

| Name | OID | Specification |
|------|-----|---------------|
| RASA-SET | 1.2.840.113549.1.9.16.1.42 | This document |
| RASA-AUTH | 1.2.840.113549.1.9.16.1.43 | This document |

### IRR Source Identifiers Registry
Create new registry "RASA IRR Source Identifiers":
- Managed by IETF Standards Action
- Initial values: RADB, RIPE, ARIN, APNIC, LACNIC, AFRINIC
- Private identifiers allowed (prefix with organization name)

---

## References

- RFC 2622: Routing Policy Specification Language (RPSL)
- RFC 3779: X.509 Extensions for IP Addresses and AS Identifiers
- RFC 5652: Cryptographic Message Syntax (CMS)
- RFC 6482: A Profile for Route Origin Authorizations (ROAs)
- RFC 6487: A Profile for X.509 PKIX Resource Certificates
- RFC 6488: Signed Object Template for the Resource Public Key Infrastructure (RPKI)

---

## Document History

- 2026-02-24: Initial specification draft

---

## Acknowledgments

This specification extends the RASA protocol to support real-world deployment scenarios where operators need cryptographic assurance without full infrastructure migration.
