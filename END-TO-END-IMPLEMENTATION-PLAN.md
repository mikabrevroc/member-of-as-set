# RASA End-to-End Implementation Plan

**Objective**: Achieve complete feature coverage from RPKI objects through JSON to working AS-SET filtering.

**Status**: Critical gaps identified, implementation required

---

## Feature Coverage Matrix

| Feature | Spec | rpki-client ASN.1 | rpki-client JSON | bgpq4 JSON | bgpq4 Logic | Status |
|---------|------|-------------------|------------------|------------|-------------|--------|
| **RASA-AUTH** |
| version | ✅ | ✅ | ? | N/A | N/A | ⚠️ Need JSON verify |
| authorizedAS/authorizedSet | ✅ | ✅ | ? | N/A | N/A | ⚠️ Need JSON verify |
| authorizedIn (with propagation) | ✅ | ❌ (just strings) | ? | N/A | N/A | 🔴 **CRITICAL GAP** |
| flags (strictMode) | ✅ | ✅ (unused) | ? | N/A | N/A | ⚠️ Need JSON verify |
| notBefore/notAfter | ✅ | ✅ | ? | N/A | N/A | ⚠️ Need JSON verify |
| **RASA-SET** |
| version | ✅ | ✅ | ? | N/A | N/A | ⚠️ Need JSON verify |
| asSetName | ✅ | ✅ | ? | ✅ | ✅ | ⚠️ Need JSON verify |
| containingAS | ✅ | ✅ | ? | ❌ | ❌ | 🔴 **MISSING** |
| members | ✅ | ✅ | ? | ✅ | ✅ | ⚠️ Need JSON verify |
| nestedSets | ✅ | ✅ | ? | ❌ | ❌ | 🔴 **MISSING** |
| irrSource | ✅ | ✅ | ? | ❌ | ❌ | 🔴 **MISSING** |
| flags (doNotInherit/authoritative) | ✅ | ✅ | ? | ❌ | ❌ | 🔴 **MISSING** |
| notBefore/notAfter | ✅ | ✅ | ? | ❌ | ❌ | 🔴 **MISSING** |
| **NEW: fallbackMode** | ✅ | ❌ | ❌ | ❌ | ❌ | 🔴 **NOT IMPLEMENTED** |
| **Integration** |
| expander.c RASA integration | N/A | N/A | N/A | ❌ | ❌ | 🔴 **CRITICAL GAP** |

**Legend:**
- ✅ Implemented
- ❌ Not implemented
- ? Unknown/needs verification
- 🔴 Critical gap blocking end-to-end functionality
- ⚠️ Needs verification

---

## Critical Path to End-to-End Functionality

### Phase 1: ASN.1 Schema Corrections (Foundation)

#### Task 1.1: Fix authorizedIn Structure
**Problem**: Current rpki-client parses authorizedIn as `SEQUENCE OF UTF8String`, but spec requires `SEQUENCE OF AuthorizedEntry` with propagation scope.

**Current (wrong):**
```asn1
-- Current implementation
authorizedIn SEQUENCE OF UTF8String  -- Just AS-SET names
```

**Required (correct):**
```asn1
-- Specification
AuthorizedEntry ::= SEQUENCE {
    asSetName        UTF8String,
    propagation      PropagationScope OPTIONAL  -- 0=unrestricted, 1=directOnly
}

authorizedIn SEQUENCE OF AuthorizedEntry
```

**Files to modify:**
- `rpki-client-portable/src/rasa.c`: Lines 45-54 (RasaAuthContent_st struct)
- `rpki-client-portable/src/rasa.c`: Lines 56-65 (ASN1_SEQUENCE template)
- `rpki-client-portable/src/rasa.c`: Lines 123-163 (parsing logic)
- `rpki-client-portable/src/rasa.h`: Lines 31-34 (struct rasa_entry)

**Changes needed:**
1. Create new ASN.1 type `RasaAuthorizedEntry`
2. Update `RasaAuthContent_st.authorizedIn` to use new type
3. Update ASN.1 template with proper SEQUENCE OF
4. Update parsing loop to extract propagation field
5. Update `struct rasa_entry` to store propagation

#### Task 1.2: Add fallbackMode to RASA-SET
**Problem**: fallbackMode (irrFallback/irrLock/rasaOnly) not in ASN.1 schema.

**Required:**
```asn1
FallbackMode ::= ENUMERATED {
    irrFallback(0),
    irrLock(1),
    rasaOnly(2)
}

RasaSetContent ::= SEQUENCE {
  version          [0] INTEGER DEFAULT 0,
  asSetName            UTF8String,
  containingAS         ASID,
  members              SEQUENCE OF ASID,
  nestedSets           SEQUENCE OF UTF8String OPTIONAL,
  irrSource            UTF8String OPTIONAL,
  fallbackMode         FallbackMode DEFAULT irrFallback,  -- NEW
  flags                RasaFlags OPTIONAL,
  notBefore            GeneralizedTime,
  notAfter             GeneralizedTime
}
```

**Files to modify:**
- `rpki-client-portable/src/rasa.c`: Lines 407-418 (RasaSetContent_st struct)
- `rpki-client-portable/src/rasa.c`: Lines 421-431 (ASN1_SEQUENCE template)
- `rpki-client-portable/src/rasa.c`: Lines 544-551 (irrSource parsing - add after)
- `rpki-client-portable/src/rasa.h`: Lines 56-76 (struct rasa_set)
- `rpki-client-portable/src/rasa.h`: Add FallbackMode enum

#### Task 1.3: Parse RasaFlags Bits
**Problem**: doNotInherit and authoritative flags parsed but not extracted.

**Required:**
```asn1
RasaFlags ::= BIT STRING {
    doNotInherit(0),
    authoritative(1)
}
```

**Files to modify:**
- `rpki-client-portable/src/rasa.c`: Add flag extraction after parsing
- `rpki-client-portable/src/rasa.h`: Lines 71 (struct rasa_set - add flag fields)

---

### Phase 2: JSON Output Format (Bridge)

#### Task 2.1: Document Current JSON Output
**Action**: Determine what JSON rpki-client actually produces.

**Files to check:**
- `rpki-client-portable/src/output-json.c`: Find RASA JSON output functions
- Look for `output_json_rasa()` or similar
- Check if RASA-SET is output separately

**Expected format (for bgpq4 compatibility):**
```json
{
  "rasas": [
    {
      "rasa": {
        "version": 0,
        "authorized_as": 64496,
        "authorized_set": null,
        "authorized_in": [
          {
            "asset": "AS-TEST",
            "propagation": 0
          }
        ],
        "flags": [],
        "not_before": "2024-01-01T00:00:00Z",
        "not_after": "2025-01-01T00:00:00Z"
      }
    }
  ],
  "rasa_sets": [
    {
      "rasa_set": {
        "version": 0,
        "as_set_name": "AS2914:AS-GLOBAL",
        "containing_as": 2914,
        "members": [64496, 65001],
        "nested_sets": ["AS-CHILD"],
        "irr_source": "RADB",
        "fallback_mode": "irrLock",
        "flags": ["doNotInherit"],
        "not_before": "2024-01-01T00:00:00Z",
        "not_after": "2025-01-01T00:00:00Z"
      }
    }
  ]
}
```

#### Task 2.2: Implement/Fix JSON Output
**If JSON output doesn't exist or doesn't match:**

**Files to modify:**
- `rpki-client-portable/src/output-json.c`: Add RASA output functions
- Need functions: `output_json_rasa()`, `output_json_rasa_set()`

**Required output fields:**
- All parsed fields from both RASA-AUTH and RASA-SET
- Proper nesting structure (rasas[] and rasa_sets[])
- ISO 8601 timestamps
- String enums for fallback_mode

---

### Phase 3: bgpq4 Library Updates (Consumer)

#### Task 3.1: Update JSON Parsing
**Current bgpq4 expects:**
```json
{"rasas": [{"rasa": {...}}]}
{"rasa_sets": [{"rasa_set": {"as_set_name": "...", "members": [...]}}]}
```

**Required updates:**
- Handle new fields: containing_as, nested_sets, irr_source, fallback_mode, flags
- Handle authorizedIn with propagation objects (not just strings)

**Files to modify:**
- `bgpq4/rasa.c`: Lines 36-119 (rasa_check_auth function)
- `bgpq4/rasa.c`: Lines 142-233 (rasa_check_set_membership function)
- `bgpq4/rasa.h`: Add new fields to structs

#### Task 3.2: Implement fallbackMode Logic
**Three modes to implement:**

**irrFallback(0) - Default:**
```c
if (rasa_set->fallback_mode == IRR_FALLBACK) {
    // Merge RASA members with IRR query
    members = rasa_set->members;
    irr_members = query_irr(asset_name);
    return merge_unique(members, irr_members);
}
```

**irrLock(1) - Database Lock:**
```c
if (rasa_set->fallback_mode == IRR_LOCK) {
    // Query ONLY specified IRR database
    assert(rasa_set->members == NULL || num_members == 0);
    assert(rasa_set->irr_source != NULL);
    return query_irr(asset_name, source=rasa_set->irr_source);
}
```

**rasaOnly(2) - RASA Replacement:**
```c
if (rasa_set->fallback_mode == RASA_ONLY) {
    // Use only RASA members, no IRR query
    assert(rasa_set->members != NULL && num_members > 0);
    return rasa_set->members;
}
```

**Files to modify:**
- `bgpq4/rasa.c`: Add fallback mode handling
- `bgpq4/rasa.h`: Add FallbackMode enum and fields

#### Task 3.3: Implement Nested Set Expansion
**Recursive expansion of nestedSets:**
```c
int expand_rasa_set(const char *asset_name, uint32_t **members, size_t *num_members) {
    rasa_set = lookup_rasa_set(asset_name);
    if (!rasa_set) return -1;
    
    // Add direct members
    for (i = 0; i < rasa_set->num_members; i++) {
        add_member(members, rasa_set->members[i].asid);
    }
    
    // Recursively expand nested sets
    for (i = 0; i < rasa_set->num_nested; i++) {
        expand_rasa_set(rasa_set->nested_sets[i], members, num_members);
    }
    
    return 0;
}
```

**Files to modify:**
- `bgpq4/rasa.c`: Add `rasa_expand_set()` function

#### Task 3.4: Implement Propagation Scope Handling
**Propagation values:**
- 0 = unrestricted (default) - Normal behavior
- 1 = directOnly - Signal for peer locking

**Usage:**
- Store propagation value per authorizedIn entry
- Expose to bgpq4 for policy decisions
- May affect BGP import policy (future use)

---

### Phase 4: Critical Integration (expander.c)

#### Task 4.1: Hook RASA into AS-SET Expansion
**Problem**: bgpq4 has RASA library, but `expander.c` doesn't call it.

**Current flow (expander.c):**
```
expand_as_set(asset_name):
  query IRR for asset_name
  return members
```

**Required flow:**
```
expand_as_set(asset_name):
  rasa_set = lookup_rasa_set(asset_name)
  
  if (rasa_set):
    switch (rasa_set->fallback_mode):
      case IRR_LOCK:
        return query_irr(asset_name, source=rasa_set->irr_source)
      case RASA_ONLY:
        return rasa_set->members + expand_nested(rasa_set->nested_sets)
      case IRR_FALLBACK:
        rasa_members = rasa_set->members + expand_nested(rasa_set->nested_sets)
        irr_members = query_irr(asset_name)
        return merge(rasa_members, irr_members)
  else:
    return query_irr(asset_name)  // Legacy behavior
```

**Files to modify:**
- `bgpq4/expander.c`: Find `expand_as_set()` or similar function
- Add RASA lookup and logic
- Handle nested set recursion

#### Task 4.2: Add Command-Line Flags
**New flags needed:**
- `-Y`: Enable RASA verification mode
- `-y <file>`: Load RASA JSON file
- `-y source=<db>`: Override IRR source preference

**Files to modify:**
- `bgpq4/main.c`: Add option parsing
- `bgpq4/expander.c`: Pass RASA config to expansion functions

#### Task 4.3: Implement Bidirectional Filtering
**Current RASA library does:**
- Check if ASN authorizes AS-SET (RASA-AUTH)
- Check if AS-SET declares ASN (RASA-SET)

**Required in expander.c:**
- For each ASN from expansion, verify bidirectional authorization
- If RASA-AUTH says "not authorized", filter out the ASN
- Log filtered ASNs for debugging

```c
for each asn in expanded_members:
    if (rasa_enabled):
        auth_result = rasa_check_auth(asn, asset_name)
        if (!auth_result.authorized):
            log("Filtering ASN %u - not authorized by RASA-AUTH", asn)
            continue
    add_to_final_list(asn)
```

---

### Phase 5: Testing & Verification

#### Task 5.1: Create Test RPKI Objects
**Test data needed:**
1. RASA-AUTH with propagation scope
2. RASA-SET with all fields (members, nestedSets, irrSource, fallbackMode)
3. RASA-SET with fallbackMode=irrLock (empty members)
4. RASA-SET with fallbackMode=rasaOnly

**Location**: `rasa-testdata/objects/`

#### Task 5.2: Test rpki-client Parsing
**Verify:**
- All ASN.1 fields parse correctly
- JSON output matches expected format
- Error handling for malformed objects

#### Task 5.3: Test bgpq4 Integration
**Test cases:**
1. Load JSON with all new fields
2. Test fallbackMode=irrLock (query specific DB)
3. Test fallbackMode=rasaOnly (no IRR query)
4. Test nested set expansion
5. Test bidirectional filtering

#### Task 5.4: End-to-End Test
**Full chain:**
1. Create test RASA objects
2. Sign with test CA
3. Run through rpki-client
4. Verify JSON output
5. Load into bgpq4
6. Test AS-SET expansion with RASA
7. Verify correct filtering

---

## Implementation Priority

### 🔴 CRITICAL (Blocking end-to-end functionality)
1. **Task 1.1**: Fix authorizedIn structure (propagation scope)
2. **Task 1.2**: Add fallbackMode to RASA-SET
3. **Task 2.1/2.2**: JSON output format verification/fix
4. **Task 4.1**: Hook RASA into expander.c (THE critical integration)

### 🟡 HIGH (Required for complete feature set)
5. **Task 3.1**: Update bgpq4 JSON parsing for new fields
6. **Task 3.2**: Implement fallbackMode logic in bgpq4
7. **Task 3.3**: Implement nested set expansion
8. **Task 4.2**: Add command-line flags

### 🟢 MEDIUM (Enhancement)
9. **Task 1.3**: Parse RasaFlags bits
10. **Task 3.4**: Propagation scope handling
11. **Task 4.3**: Bidirectional filtering in expander.c
12. **Task 5.x**: Comprehensive testing

---

## File Summary

### rpki-client-portable/src/
| File | Lines | Changes |
|------|-------|---------|
| rasa.c | 45-65 | Fix authorizedIn ASN.1 structure |
| rasa.c | 123-163 | Parse AuthorizedEntry with propagation |
| rasa.c | 407-431 | Add fallbackMode to RASA-SET |
| rasa.c | 544-551 | Add fallbackMode parsing |
| rasa.h | 31-34 | Update struct rasa_entry |
| rasa.h | 56-76 | Add fallbackMode to struct rasa_set |
| output-json.c | TBD | Add/improve JSON output |

### bgpq4/
| File | Lines | Changes |
|------|-------|---------|
| rasa.h | All | Add new fields and enums |
| rasa.c | 36-119 | Parse authorizedIn with propagation |
| rasa.c | 142-233 | Handle all RASA-SET fields |
| rasa.c | New | Add fallbackMode logic |
| rasa.c | New | Add nested set expansion |
| expander.c | TBD | Integrate RASA into expansion |
| main.c | TBD | Add -Y and -y flags |

---

## Success Criteria

✅ **Phase 1 Complete**: rpki-client parses all ASN.1 fields correctly  
✅ **Phase 2 Complete**: JSON output verified to match bgpq4 expectations  
✅ **Phase 3 Complete**: bgpq4 handles all new JSON fields  
✅ **Phase 4 Complete**: bgpq4 expander.c uses RASA for actual filtering  
✅ **Phase 5 Complete**: End-to-end test passes with all features  

**Final Verification:**
```bash
# Create test RASA-SET with fallbackMode=irrLock
cd rasa-testdata && ./create-test-rasa-set.sh

# Process with rpki-client
rpki-client -f test-rasa-set.cms -o output.json

# Verify JSON has fallback_mode: "irrLock"
grep -q '"fallback_mode": "irrLock"' output.json

# Use with bgpq4
bgpq4 -Y -y output.json -Jl test AS2914:AS-GLOBAL

# Verify it only queries RADB (not RIPE/ARIN)
# Verify correct members returned
```

---

## Document History

- 2026-02-24: Initial implementation plan created
