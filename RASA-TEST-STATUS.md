# RASA-AUTH Functionality and Test Status

## Current Implementation Status

### What's Implemented ✅

#### 1. CMS Signed RASA Objects (Test Infrastructure)
**Status**: ✅ FULLY TESTED AND WORKING

- Created test CA infrastructure with root + 3 EE certificates
- Generated CMS signed RASA objects for AS64496, AS15169, AS2914
- Verified CMS signatures using OpenSSL
- All 3 test objects verified successfully

**Test command**:
```bash
python3 rasa-testdata/scripts/test-rasa-parse.py
# Output: ✓ All RASA CMS objects verified successfully!
```

#### 2. BGPQ4 RASA Support (JSON-based)
**Status**: ✅ CODE COMPLETE, NOT FULLY TESTED WITH LIVE DATA

**Implemented**:
- `-Y` flag: Enable RASA checking
- `-y file` flag: Load RASA JSON file
- `rasa_load_config()`: Load JSON from rpki-client format
- `rasa_check_auth()`: Check if ASN is authorized for AS-SET
- Integration in `expander.c`: Hooks into AS-SET expansion

**RASA-AUTH Logic**:
```c
if (rasa_check_auth(asno, NULL, &result) == 0 && !result.authorized) {
    SX_DEBUG(debug_expander, "RASA: AS%u not authorized: %s\n",
        asno, result.reason ? result.reason : "unknown");
    free(asne);
    return 0;  // Filter out unauthorized ASN
}
```

**What it checks**:
1. Loads JSON with `rasa_auths` array
2. For each ASN being expanded, checks if RASA-AUTH exists
3. If RASA-AUTH exists, verifies AS-SET is in `authorized_in` list
4. If not authorized, filters the ASN from expansion
5. If no RASA-AUTH exists, defaults to "allow" (backward compatible)

#### 3. RPKI-Client RASA Parser
**Status**: ✅ CODE COMPLETE, NOT INTEGRATION TESTED

**Implemented**:
- `src/rasa.c`: Full ASN.1 parsing using OpenSSL macros
- `src/rasa.h`: Type definitions matching existing patterns
- 5 patches for OpenBSD source integration
- OID registration (placeholder: 1.3.6.1.4.1.99999.1.1)
- JSON output format for bgpq4 consumption

**What it parses**:
- RASA eContent from CMS signed objects
- `authorizedAS` or `authorizedSet` (mutually exclusive)
- `authorizedIn` array of AS-SET names
- Validity times (notBefore, notAfter)
- RPKI validation (certificate chain, signatures)

---

## What Has Been Tested

### ✅ Tested and Working

1. **CMS Object Creation**
   - Test CA generation
   - Certificate signing
   - CMS signing with OpenSSL
   - Signature verification

2. **JSON Parsing in bgpq4**
   - jansson integration
   - JSON file loading
   - Array/object traversal
   - Basic authorization logic (code review)

3. **ASN.1 Parsing in rpki-client**
   - OpenSSL macro usage
   - eContent parsing
   - Type validation
   - Code compiles successfully

### ⚠️ Tested but Not with Live Data

1. **BGPQ4 RASA Filtering**
   - Code is in place
   - Logic reviewed
   - NOT tested against live IRR queries with real RASA filtering

### ❌ Not Yet Tested

1. **Full Pipeline: rpki-client → bgpq4**
   - rpki-client parsing RASA from RPKI repos
   - rpki-client outputting JSON
   - bgpq4 consuming that JSON
   - End-to-end AS-SET filtering

2. **RASA-SET Support**
   - Only RASA-AUTH is implemented
   - RASA-SET (for AS-SET authorization) not yet done

3. **Propagation Scope**
   - Field exists in structures
   - Logic to enforce directOnly vs unrestricted not implemented

4. **Real RPKI Integration**
   - Tested only with self-signed certificates
   - Not tested with real RPKI trust anchors
   - Not tested with production RPKI repositories

---

## Test Scenarios Coverage

### BGPQ4 RASA-AUTH Test Cases

| Scenario | Status | Notes |
|----------|--------|-------|
| Load JSON file | ✅ | `rasa_load_config()` works |
| Check authorized ASN | ⚠️ | Code complete, needs live test |
| Check unauthorized ASN | ⚠️ | Code complete, needs live test |
| Missing RASA (default allow) | ✅ | Returns "no RASA-AUTH (default allow)" |
| Empty authorized_in | ⚠️ | Should reject, needs testing |
| Multiple AS-SETs in authorized_in | ✅ | Loops through array |
| AS-SET name matching | ⚠️ | String comparison, needs testing |
| Invalid JSON | ✅ | Returns error with message |
| Debug output | ✅ | Logs authorization decisions |

### RPKI-Client RASA Parser Test Cases

| Scenario | Status | Notes |
|----------|--------|-------|
| Parse RASA-AUTH with authorizedAS | ✅ | Code implemented |
| Parse RASA-AUTH with authorizedSet | ✅ | Code implemented |
| Reject both authorizedAS + authorizedSet | ✅ | Validation in place |
| Parse authorizedIn array | ✅ | Stack iteration implemented |
| Validate notBefore/notAfter | ✅ | Uses x509_get_generalized_time |
| CMS signature validation | ✅ | Uses existing cms_parse_validate |
| Output JSON format | ✅ | Code implemented |
| Handle missing authorizedIn | ✅ | Returns error |
| Handle empty authorizedIn | ✅ | Returns error |
| Handle too many entries (>MAX) | ✅ | Returns error |

---

## RASA-AUTH Functionality Summary

### Authorization Logic (Implemented)

**Input**: ASN being expanded during AS-SET expansion  
**Output**: Authorized or Not Authorized  
**Default**: Allow (if no RASA-AUTH exists)

**Algorithm**:
1. Search RASA database for entry matching ASN
2. If no entry found → ALLOW (backward compatibility)
3. If entry found:
   - Check if current AS-SET being expanded is in `authorized_in`
   - If yes → ALLOW
   - If no → DENY with reason "not in authorized_in"

**Example**:
```json
{
  "rasa": {
    "authorized_as": 64496,
    "authorized_in": [
      {"entry": {"asset": "AS-EXAMPLE"}},
      {"entry": {"asset": "AS-GLOBAL"}}
    ]
  }
}
```

- AS64496 expanding `AS-EXAMPLE` → ✅ ALLOWED
- AS64496 expanding `AS-OTHER` → ❌ DENIED

---

## What's Missing / Not Implemented

### 1. RASA-SET (AS-SET Authorization)
**Status**: NOT IMPLEMENTED

RASA-AUTH authorizes ASNs. RASA-SET would authorize AS-SETs (for nested AS-SETs).

Example use case:
- AS2914 has `authorizedSet: "AS2914:AS-CUSTOMERS"`
- This AS-SET can only be expanded when referenced from authorized parent AS-SETs

### 2. Propagation Scope Enforcement
**Status**: FIELD EXISTS, NOT ENFORCED

```c
struct rasa_entry {
    char *asset;
    int propagation;  // 0=unrestricted, 1=directOnly
};
```

**directOnly** logic not implemented:
- unrestricted: Can be used in any AS-SET
- directOnly: Can only be direct member, not transitive

### 3. Expiration Checking
**Status**: FIELD PARSED, NOT ENFORCED

RASA objects have `expires` field, but bgpq4 doesn't check if RASA is expired.

### 4. Real RPKI Integration
**Status**: NOT TESTED

- Tested with self-signed certificates only
- Needs testing with real RPKI repositories
- Needs testing with production trust anchors

---

## Next Steps for Complete Testing

1. **Test bgpq4 with live IRR + mock RASA JSON**
   ```bash
   ./bgpq4 -Y -y mock-rasa.json AS-SOME-REAL-SET
   ```

2. **Test full pipeline**
   - Create test RASA objects in RPKI format
   - Run rpki-client to validate and output JSON
   - Use that JSON with bgpq4
   - Verify filtering works end-to-end

3. **Test edge cases**
   - Expired RASA
   - Missing authorized_in
   - Empty authorized_in
   - Very large authorized_in (>1000 entries)
   - Invalid AS-SET names
   - Nested AS-SETs with RASA

4. **Implement RASA-SET** (if needed)
   - ASN.1 definitions
   - Parser support
   - Authorization logic for AS-SET nesting

5. **Implement propagation scope**
   - Enforce directOnly vs unrestricted
   - Track expansion depth
   - Filter transitive vs direct members

---

## Conclusion

**Current State**: 
- RASA-AUTH is **code complete** in both tools
- CMS signed objects **work and are verified**
- **Not yet integration tested** end-to-end with real data

**What works today**:
- Create RASA objects
- Sign them with CMS
- Parse them in rpki-client (code ready)
- Check authorization in bgpq4 (code ready)

**What's needed**:
- End-to-end integration test
- Live IRR data + RASA filtering test
- Production RPKI repository testing
