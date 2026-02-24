# RASA vs IRR AS-SET Gap Analysis

**Objective**: Ensure RASA-SET and RASA-AUTH can fully replace IRR AS-SETs for Internet routing security.

**Date**: 2026-02-24  
**Status**: Draft - Needs Review

---

## Executive Summary

| Feature | IRR AS-SET | RASA-SET | Gap? |
|---------|-----------|----------|------|
| Hierarchical AS-SETs (AS-SET within AS-SET) | ✅ Yes | ⚠️ Partial | **NEEDS SPEC** |
| Member AS declaration | ✅ Yes | ✅ Yes | None |
| mbrs-by-ref (indirect membership) | ✅ Yes | ❌ No | **CRITICAL GAP** |
| tech-c/admin-c contacts | ✅ Yes | ❌ No | Minor gap |
| last-modified tracking | ✅ Yes | ⚠️ Partial | Via RPKI timestamps |
| Source attribution (RADB, RIPE, etc.) | ✅ Yes | ✅ Yes | Via RPKI repository |
| Cryptographic validation | ❌ No | ✅ Yes | **RASA ADVANTAGE** |
| Bidirectional verification | ❌ No | ✅ Yes | **RASA ADVANTAGE** |

---

## 1. Hierarchical AS-SET Support

### Current IRR Behavior
```
AS-PARENT:  members: AS-CHILD, AS64496
AS-CHILD:   members: AS65001, AS65002
```
When expanding AS-PARENT, IRR tools recursively expand AS-CHILD.

### Current RASA-SET Implementation
```json
{
  "rasasets": [
    {
      "rasaset": {
        "asset": "AS-PARENT",
        "members": [
          {"member": "AS-CHILD"},
          {"member": 64496}
        ]
      }
    }
  ]
}
```

### Gap Analysis
- **Issue**: RASA-SET `members` field only supports ASN integers, not AS-SET strings
- **Impact**: Cannot express hierarchical AS-SET relationships
- **Evidence**: See `bgpq4/tests/test_rasa_set.c` - no test for nested AS-SET members

### Recommendation
**SPEC CHANGE REQUIRED**: Extend RASA-SET member type to support both:
1. Integer ASNs: `{"member": 64496}`
2. String AS-SETs: `{"member": "AS-CHILD"}`

**JSON Schema Change**:
```json
{
  "rasaset": {
    "asset": "AS-PARENT",
    "members": [
      {"member": {"type": "asn", "value": 64496}},
      {"member": {"type": "asset", "value": "AS-CHILD"}}
    ]
  }
}
```

---

## 2. mbrs-by-ref Support

### Current IRR Behavior
`mbrs-by-ref: ANY` allows route objects to claim membership in an AS-SET without the AS-SET explicitly listing them.

**Use Case**: Content providers (Google, Cloudflare) want to be included in customer AS-SETs without the customer explicitly listing them.

### Current RASA-SET Implementation
No equivalent mechanism exists.

### Gap Analysis
- **Issue**: RASA-SET requires explicit member enumeration
- **Impact**: Cannot support dynamic membership models
- **Risk**: Major operational change for large networks

### Recommendation
**SPEC CHANGE REQUIRED**: Add optional `mbrs-by-ref` field to RASA-SET:

```json
{
  "rasaset": {
    "asset": "AS-CUSTOMER",
    "mbrs-by-ref": ["AS15169", "AS13335"],
    "members": [
      {"member": 64496}
    ]
  }
}
```

**Alternative**: Use RASA-AUTH as implicit mbrs-by-ref:
- If AS15169 has a RASA-AUTH authorizing AS-CUSTOMER, treat as implicit member
- This aligns with RASA's bidirectional philosophy

---

## 3. Real-World Operator Workflows

### Current IRR Workflow (bgpq4)
```bash
# Generate prefix-list from AS-SET
bgpq4 -Jl customer-filter AS-CUSTOMER

# What happens:
# 1. Query IRR for AS-CUSTOMER members
# 2. Recursively expand all member AS-SETs
# 3. Query route objects for each ASN
# 4. Generate prefix-list
```

### Target RASA Workflow
```bash
# Generate prefix-list with RASA verification
bgpq4 -Jl -Y customer-filter AS-CUSTOMER

# What should happen:
# 1. Query IRR for AS-CUSTOMER members
# 2. For each ASN, check RASA-AUTH (does ASN authorize AS-CUSTOMER?)
# 3. Check RASA-SET (does AS-CUSTOMER declare ASN as member?)
# 4. Only include ASNs where both agree
# 5. Query route objects for authorized ASNs
# 6. Generate prefix-list
```

### Gap Analysis
- **Issue**: bgpq4 expander.c not integrated with RASA library
- **Impact**: RASA verification not happening during AS-SET expansion
- **Status**: rasa.c library exists but not called from expander.c

### Recommendation
**IMPLEMENTATION REQUIRED**: Modify bgpq4 expander.c to:
1. Load RASA JSON files via `-y` flag
2. Call `rasa_verify_bidirectional()` for each ASN during expansion
3. Filter out unauthorized ASNs
4. Log authorization decisions for debugging

---

## 4. JSON Format Compatibility

### bgpq4 Expected Format (RASA-AUTH)
```json
{
  "rasas": [
    {
      "rasa": {
        "authorized_as": 64496,
        "authorized_in": [
          {"entry": {"asset": "AS-TEST"}}
        ]
      }
    }
  ]
}
```

### rpki-client Output Format (Unknown)
**CRITICAL GAP**: rpki-client's RASA JSON output format is not documented or tested against bgpq4 expectations.

### Recommendation
**VERIFICATION REQUIRED**:
1. Build rpki-client with RASA patches
2. Process test RASA CMS objects
3. Verify output JSON matches bgpq4 expected format
4. Document any format mismatches
5. Update either rpki-client or bgpq4 to align formats

---

## 5. Missing Features for Production Deployment

### 5.1. RASA-SET Expiration Handling
- IRR AS-SETs have implicit expiration via last-modified
- RASA objects have explicit validity periods via RPKI
- **Gap**: bgpq4 doesn't check RASA object validity dates

### 5.2. Multiple RASA Sources
- Operators may have RASA objects from multiple RPKI repositories
- **Gap**: No mechanism to merge/validate multiple RASA JSON files

### 5.3. Logging and Debugging
- **Gap**: No standardized logging format for RASA authorization decisions
- Operators need audit trails for filter generation

### 5.4. Graceful Degradation
- **Gap**: No policy for "RASA verification failed, fallback to IRR only"
- Need `-Y strict` vs `-Y permissive` modes

---

## 6. Critical Path to Production

### Phase 1: Fix Hierarchical AS-SETs (URGENT)
- [ ] Update RFC specification to support AS-SET members
- [ ] Update rpki-client ASN.1 parser
- [ ] Update bgpq4 rasa_set_check_membership()
- [ ] Add test cases for nested AS-SETs

### Phase 2: mbrs-by-ref Support (HIGH)
- [ ] Decide: explicit field vs implicit via RASA-AUTH
- [ ] Update specification
- [ ] Implement in rpki-client
- [ ] Implement in bgpq4

### Phase 3: bgpq4 Integration (HIGH)
- [ ] Modify expander.c to call RASA functions
- [ ] Add `-Y` flag for RASA mode
- [ ] Add `-y <file>` flag for RASA JSON input
- [ ] Add logging for authorization decisions

### Phase 4: End-to-End Testing (MEDIUM)
- [ ] Create test RASA objects
- [ ] Run through rpki-client
- [ ] Verify JSON output
- [ ] Test with bgpq4
- [ ] Validate against real IRR data

### Phase 5: Documentation (MEDIUM)
- [ ] Operator deployment guide
- [ ] Migration guide from IRR-only to RASA
- [ ] Troubleshooting guide

---

## 7. Open Questions

1. **Should RASA-SET support `members` as AS-SET references?**
   - Pro: Matches IRR behavior
   - Con: Increases complexity, potential for loops

2. **Should we support mbrs-by-ref?**
   - Pro: Needed for content provider use cases
   - Con: Against bidirectional philosophy

3. **How to handle RASA verification failures?**
   - Option A: Fail closed (reject AS-SET expansion)
   - Option B: Fail open (accept with warning)
   - Option C: Configurable policy

4. **What about AS-SETs with thousands of members?**
   - Current JSON format scales poorly
   - Consider binary or compressed formats?

---

## 8. Recommendations

### Immediate Actions (This Week)
1. **Test rpki-client JSON output** against bgpq4 expectations
2. **Implement bgpq4 expander.c integration** with RASA library
3. **Add test** for hierarchical AS-SET support

### Short Term (Next 2 Weeks)
1. **Update RFC specification** to support AS-SET members in RASA-SET
2. **Implement mbrs-by-ref** or document workaround
3. **Create end-to-end test** with real IRR data

### Medium Term (Next Month)
1. **Production deployment guide**
2. **Operator testing** with volunteer networks
3. **Performance testing** with large AS-SETs

---

## Appendix: Test Data Locations

- Test CA: `/Users/mabrahamsson/src/reverse-as-set/rasa-testdata/ca/`
- Test objects: `/Users/mabrahamsson/src/reverse-as-set/rasa-testdata/objects/`
- POC scenarios: `/Users/mabrahamsson/src/reverse-as-set/poc/`
- bgpq4 tests: `/Users/mabrahamsson/src/reverse-as-set/bgpq4/tests/`

---

## Document History

- 2026-02-24: Initial gap analysis created
