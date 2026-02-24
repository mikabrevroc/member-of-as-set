# RASA Project: Comprehensive Analysis and Implementation Plan

## Executive Summary

**Current Status**: Strong foundation with working components in all three repositories
- **123/123 tests passing** in bgpq4
- **RPKI-client** has ASN.1 parsing and CMS verification
- **POC** demonstrates 14 scenarios with real IRR data

**Critical Gap**: No end-to-end integration demonstration showing the full chain:
```
Mock RASA Objects → rpki-client (CMS validation) → JSON → bgpq4 (AS-SET filtering)
```

---

## 1. Current State Analysis

### 1.1 Documentation (✅ Strong)
- **RFC Draft**: `draft-carbonara-rpki-as-set-auth-04.xml` - Complete specification
- **Implementation Guide**: `IMPLEMENTATION-GUIDE.md` - Operational guidance
- **POC README**: 14 scenarios documented with real IRR data
- **Status Docs**: Multiple tracking documents (some redundant)

### 1.2 BGPQ4 Implementation (✅ Strong)
**Files**:
- `rasa.c` (271 lines): RASA-AUTH and RASA-SET JSON parsing
- `rasa.h`: Type definitions
- 8 test files with 123 tests passing (100%)

**Capabilities**:
- ✅ JSON parsing via jansson
- ✅ RASA-AUTH: Check if ASN authorizes being in AS-SET
- ✅ RASA-SET: Check if AS-SET declares ASN as member
- ✅ Bidirectional verification
- ✅ Build system integration (Makefile.am)
- ⚠️ **Not yet integrated into main bgpq4 workflow** (expander.c not modified)

### 1.3 RPKI-Client Implementation (✅ Strong)
**Files**:
- `src/rasa.c` (785 lines): Full ASN.1 parsing with OpenSSL
- `src/rasa.h`: Type definitions
- 5 patches for OpenBSD integration

**Capabilities**:
- ✅ ASN.1 parsing using OpenSSL macros
- ✅ CMS signature verification
- ✅ OID registration (placeholder 1.3.6.1.4.1.99999.1.1)
- ✅ JSON output generation
- ⚠️ **Not tested with actual RASA objects** (per RASA-IMPLEMENTATION-STATUS.md)

### 1.4 Proof of Concept (✅ Strong)
**Files**: 14 Python scripts demonstrating scenarios

**Capabilities**:
- ✅ IRR caching for fast demos
- ✅ Real WHOIS data from RADB/RIPE/APNIC
- ✅ 14 scenarios including attacks, delegation, edge cases
- ✅ JunOS config generation
- ✅ Mock RASA JSON objects

**Scenarios Covered**:
1. Basic AS-SET expansion
2. RASA authorization
3. Peer-lock (propagation=directOnly)
4. AS-SET authorization (RADB-only)
5. Rejection (strictMode)
6-14. Nested AS-SETs, delegation, Tier-1 attacks, circular detection, etc.

### 1.5 Test Data Infrastructure (✅ Good)
**Structure**:
```
rasa-testdata/
├── ca/                     # Test CA infrastructure
│   ├── root.crt/.key      # Root CA
│   ├── AS64496.crt/.key   # EE certificates
│   ├── AS15169.crt/.key
│   ├── AS2914.crt/.key
│   └── test.tal           # Trust Anchor Locator
├── objects/               # RASA objects
│   ├── AS64496.rasa      # Raw DER
│   ├── AS64496.rasa.cms  # CMS signed
│   ├── rasa.json         # JSON for bgpq4 testing
│   └── ...
└── scripts/               # Test scripts
    ├── create-test-certs.sh
    ├── create-rasa-content.py
    ├── sign-rasa-objects.sh
    └── test-rasa-parse.py
```

**Test Results**:
- ✅ CMS signing test passes (all 3 objects)
- ✅ BGPQ4 integration test works with JSON
- ⚠️ **Full rpki-client → bgpq4 chain not tested**

---

## 2. Critical Gaps Identified

### Gap 1: End-to-End Integration (🔴 CRITICAL)
**Problem**: No demonstration of complete workflow:
```
RASA objects (DER/CMS) → rpki-client → JSON → bgpq4 → Filtered AS-SET
```

**Evidence**:
- RASA-IMPLEMENTATION-STATUS.md states: "Need to test rpki-client with signed RASA objects"
- No script exists that runs rpki-client and feeds output to bgpq4
- Unknown if rpki-client JSON format matches bgpq4 expectations

### Gap 2: BGPQ4 Integration (🟡 HIGH)
**Problem**: bgpq4 has RASA library but main workflow not modified

**Evidence**:
- `expander.c` not modified to call RASA functions
- No `-Y` or `-y` flag handling in main.c (per status docs)
- RASA exists as library but not integrated into AS-SET expansion

### Gap 3: JSON Format Compatibility (🟡 HIGH)
**Problem**: Unverified if rpki-client JSON matches bgpq4 expectations

**Evidence**:
- rpki-client produces JSON (patches/0008-Add-RASA-JSON-output.patch)
- bgpq4 expects specific JSON format (rasa.c lines 55-60, 180-184)
- No validation that formats match

### Gap 4: Real RPKI Integration (🟢 MEDIUM)
**Problem**: rpki-client not tested with actual RPKI validation

**Evidence**:
- Blocker: rpki-client requires `/usr/local/etc/rpki` for TAL
- TAL must be fetchable via rsync:// or https:// (not file://)
- No workaround implemented yet

### Gap 5: Documentation Redundancy (🟢 LOW)
**Problem**: Multiple overlapping status documents

**Evidence**:
- `RASA-IMPLEMENTATION-STATUS.md`
- `RASA_IMPLEMENTATION_STATUS.md`
- `RASA_PROGRESS_SUMMARY.md`
- `RASA-TEST-STATUS.md`
- `TEST_SUITE_STATUS.md` (in bgpq4)
- Content overlaps significantly

---

## 3. Code Review Findings

### 3.1 bgpq4 rasa.c (Quality: ✅ Good)
**Strengths**:
- Clean separation of concerns (RASA-AUTH vs RASA-SET)
- Proper jansson error handling
- NULL checks added recently
- Empty array handling
- 123 tests passing

**Issues**:
- No TODOs or FIXMEs in code
- Documentation comments minimal
- No integration with main bgpq4 workflow

### 3.2 rpki-client rasa.c (Quality: ✅ Good)
**Strengths**:
- Full ASN.1 implementation with OpenSSL
- CMS signature verification
- Proper error handling with warnx()
- Follows OpenBSD style

**Issues**:
- Complex ASN.1 (OpenSSL macros)
- Placeholder OID needs IANA assignment
- Not yet tested end-to-end

### 3.3 Test Suite (Quality: ✅ Excellent)
**Strengths**:
- 123 tests passing (100%)
- Split into focused test files
- Comprehensive coverage: auth, set, bidirectional, edge cases
- Tests JSON parsing, NULL handling, error conditions

---

## 4. Implementation Plan

### Phase 1: End-to-End Integration (Priority: 🔴 CRITICAL)

#### Task 1.1: Create Integration Test Script
**Goal**: Demonstrate full workflow from RASA objects to bgpq4

**Steps**:
1. Create `test-e2e-integration.sh`:
   ```bash
   #!/bin/bash
   # 1. Start with CMS-signed RASA objects (from rasa-testdata/objects/)
   # 2. Run rpki-client with local TAL
   # 3. Capture JSON output
   # 4. Run bgpq4 with JSON file
   # 5. Verify AS-SET filtering works
   ```

2. Workaround rpki-client TAL requirement:
   - Option A: Use `-f` flag for file mode (no TAL required)
   - Option B: Start local HTTP server for test CA
   - Option C: Set custom sysconfdir

3. Verify JSON compatibility:
   - Compare rpki-client JSON output format
   - Compare bgpq4 expected format
   - Create adapter if needed

**Deliverable**: Working end-to-end demonstration

#### Task 1.2: Fix JSON Format Compatibility (if needed)
**Goal**: Ensure rpki-client output matches bgpq4 expectations

**Investigation**:
- rpki-client JSON format (check patches/0008)
- bgpq4 expected format (rasa.c):
  ```json
  {
    "rasas": [{"rasa": {"authorized_as": 64496, "authorized_in": [{"entry": {"asset": "AS-TEST"}}]}}],
    "rasa_sets": [{"rasa_set": {"as_set_name": "AS-TEST", "members": [64496]}}]
  }
  ```

**Action**: Create format adapter if mismatch found

---

### Phase 2: BGPQ4 Integration (Priority: 🟡 HIGH)

#### Task 2.1: Integrate RASA into bgpq4 Main Workflow
**Goal**: Make bgpq4 actually use RASA for AS-SET filtering

**Steps**:
1. Modify `expander.c` to call RASA functions during AS-SET expansion
2. Add `-Y` flag to enable RASA authorization
3. Add `-y <file>` flag to specify RASA JSON file
4. For each ASN in AS-SET expansion:
   - Check RASA-AUTH authorization
   - Prune unauthorized ASNs
   - Log pruned ASNs

**Deliverable**: bgpq4 with working RASA integration

#### Task 2.2: Add RASA-SET Support to bgpq4
**Goal**: Support RASA-SET declarations in addition to RASA-AUTH

**Steps**:
1. Extend expander to check both RASA-AUTH and RASA-SET
2. Implement bidirectional verification logic
3. Handle edge cases (no RASA data, partial data, etc.)

---

### Phase 3: Real RPKI Testing (Priority: 🟢 MEDIUM)

#### Task 3.1: Test rpki-client with Real RPKI Infrastructure
**Goal**: Validate CMS-signed RASA objects with real RPKI

**Steps**:
1. Set up local HTTP server for test CA
2. Configure rpki-client with test TAL
3. Run rpki-client against test RASA objects
4. Verify JSON output

**Deliverable**: Verified rpki-client RASA handling

#### Task 3.2: Create Production Deployment Guide
**Goal**: Document how operators deploy this

**Content**:
- rpki-client configuration for RASA
- bgpq4 integration steps
- Monitoring and troubleshooting
- Migration from IRR-only to RASA

---

### Phase 4: Documentation Consolidation (Priority: 🟢 LOW)

#### Task 4.1: Consolidate Status Documents
**Goal**: Single source of truth for implementation status

**Action**: Merge redundant docs into `IMPLEMENTATION_STATUS.md`

#### Task 4.2: Create Operator Guide
**Goal**: Complete guide for network operators

**Content**:
- What is RASA and why use it
- How to create RASA objects
- How to configure rpki-client
- How to use bgpq4 with RASA
- Troubleshooting

---

## 5. Success Criteria

### Immediate (Phase 1 Complete)
- [ ] End-to-end script runs successfully
- [ ] Mock RASA objects → rpki-client → JSON → bgpq4 works
- [ ] AS-SET expansion properly filters based on RASA

### Short-term (Phase 2 Complete)
- [ ] bgpq4 has working RASA integration flags (-Y, -y)
- [ ] Real IRR data can be filtered using RASA
- [ ] Integration tests pass

### Long-term (Phase 3-4 Complete)
- [ ] Production deployment guide
- [ ] Operator documentation complete
- [ ] Reference implementation demonstrated

---

## 6. Next Steps

**Priority Order**:

1. **Create end-to-end integration test** (🔴 Today)
   - Script that ties rpki-client → bgpq4 together
   - Verify JSON compatibility
   - Document any gaps found

2. **Fix any JSON format issues** (🟡 This week)
   - Align rpki-client output with bgpq4 expectations
   - Create adapter if needed

3. **Integrate RASA into bgpq4 main workflow** (🟡 This week)
   - Modify expander.c
   - Add CLI flags
   - Test with real IRR data

4. **Document and consolidate** (🟢 Next week)
   - Clean up redundant docs
   - Create operator guide

---

## 7. Resources

**Repositories**:
- Parent: `mikabrevroc/member-of-as-set` (main branch)
- bgpq4: `mikabrevroc/bgpq4` (feature/rasa-support branch)
- rpki-client: `mikabrevroc/rpki-client-portable` (feature/rasa-support branch)

**Key Files**:
- Specification: `draft-carbonara-rpki-as-set-auth-04.xml`
- POC: `poc/` directory with 14 scenarios
- Test Data: `rasa-testdata/` with CA and objects
- Status: `RASA-IMPLEMENTATION-STATUS.md`

---

**Ultraworked with Sisyphus**

*Analysis Date: 2026-02-24*
