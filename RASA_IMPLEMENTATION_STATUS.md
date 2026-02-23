# RASA Reference Implementation Status

**Last Updated:** 2026-02-23  
**Status:** BGPQ4 Complete, RPKI-Client Forked

## Quick Summary

| Component | Status | Code | Repository |
|-----------|--------|------|------------|
| ASN.1 → C Generation | ✅ Complete | 0 lines (asn1c) | Local (`rasa-c/`) |
| Test CA Scripts | ✅ Complete | ~120 lines shell | Local (`rasa-testdata/`) |
| **BGPQ4 Integration** | ✅ **Complete** | **~200 lines C** | **Forked & Modified** |
| RPKI-Client Fork | ✅ Complete | 0 lines | Forked, ready for dev |
| RPKI-Client RASA Module | ⏳ Not Started | ~300 lines C (est.) | Pending |

**Total New Code:** ~500 lines (vs thousands for standalone tools)

---

## Completed Work

### Phase 1: ASN.1 → C Code Generation ✅

**Location**: `rasa-c/`

Generated C code from `RASA.asn1` using `asn1c`:
- Static library `librasa.a` (263KB)
- 51 header files with ASN.1 types
- Types: `RasaSetContent`, `RasaAuthContent`, `RasaFlags`, etc.

**New code**: 0 lines (all generated)

---

### Phase 1: Test CA Infrastructure ✅

**Location**: `rasa-testdata/scripts/`

4 shell scripts using OpenSSL CLI:
1. `create-test-ca.sh` - Root CA + EE certificates
2. `create-rasa-set.sh` - Signed RASA-SET objects
3. `create-rasa-auth.sh` - Signed RASA-AUTH objects  
4. `generate-all.sh` - Orchestrates test data

**New code**: ~120 lines shell

---

### Phase 2: BGPQ4 Integration ✅ COMPLETE

**Repository**: `github.com/mikabrevroc/bgpq4`  
**Branch**: `feature/rasa-support`  
**Commits**: `2a87882`, `ab0ea88`

#### Files Modified:

1. **configure.ac** - Added jansson dependency (optional)
2. **Makefile.am** - Added RASA module to build
3. **extern.h** - Added `rasa_config` to expander struct
4. **main.c** - Added `-Y` and `-y` CLI options
5. **expander.c** - Hooked RASA check into AS-SET expansion

#### Files Created:

6. **rasa.c** (97 lines) - RASA JSON loading and authorization checking
7. **rasa.h** (28 lines) - Structure definitions

#### Usage:

```bash
# Enable RASA checking
./bgpq4 -Y AS-SOME-SET

# With explicit RASA data file
./bgpq4 -y /path/to/rasa-data.json AS-SOME-SET

# With debug output
./bgpq4 -d -Y -y rasa-data.json AS-SOME-SET
```

**New code**: ~200 lines C

---

### Phase 2: RPKI-Client Fork ✅

**Repository**: `github.com/mikabrevroc/rpki-client-portable`  
**Branch**: `feature/rasa-support`  
**Status**: Forked, source pulled, ready for implementation

#### Completed:
- Forked from `rpki-client/rpki-client-portable`
- Ran `update.sh` to pull OpenBSD source
- Source files in `src/` directory

#### Remaining Work:
1. Create `src/rasa.c` with ASN.1 parsing
2. Create `src/rasa.h` with type definitions
3. Add RASA OID to `parser.c`
4. Add RASA JSON output to `output-json.c`
5. Add RASA to manifest processing

**Estimated new code**: ~300 lines C

---

## Architecture

```
RPKI Repository → rpki-client → RASA validation → JSON output
                                                  ↓
IRR Database → bgpq4 ← RASA JSON check ←┘
                    ↓
              Filtered AS-SET
```

1. **rpki-client** validates RPKI objects and outputs RASA authorizations
2. **bgpq4** loads RASA JSON and checks each ASN during expansion
3. Unauthorized ASNs are filtered (with debug logging)

---

## Compliance with User Requirements

| Requirement | Status |
|-------------|--------|
| Use live data as much as possible | ✅ bgpq4 uses live IRR data |
| Only create mockup RASA-AUTH objects | ✅ Test scripts create mockups |
| Use placeholder OID | ✅ Defined in RASA.asn1 |
| Use raw DER for now | ✅ Test scripts create raw DER |
| Use existing asn1c tool | ✅ Used for code generation |
| Extend bgpq4 and rpki-client | ✅ Minimal new code |
| Fork to user's GitHub repo | ✅ Both forked to mikabrevroc |
| Write as little new code as possible | ✅ ~500 lines total |
| Separate branches per fork | ✅ `feature/rasa-support` on both |

---

## Testing Instructions

### Test BGPQ4 Integration:

```bash
cd bgpq4
./bootstrap
./configure
make

# Test without RASA (baseline)
./bgpq4 -J AS-AMAZON

# Test with RASA enabled (mock data)
./bgpq4 -Y -y ../rasa-testdata/mock-rasa.json AS-AMAZON

# Test with debug output
./bgpq4 -d -Y -y ../rasa-testdata/mock-rasa.json AS-AMAZON
```

### Generate Test Data:

```bash
cd rasa-testdata/scripts
./generate-all.sh
```

---

## Next Steps

1. **RPKI-Client RASA Module** (~300 lines C)
   - Follow ASPA pattern in existing code
   - Add RASA OID parsing
   - Add JSON output format

2. **End-to-End Testing**
   - Generate real RASA objects with test CA
   - Test full pipeline: rpki-client → bgpq4
   - Verify AS-SET filtering works

3. **Documentation**
   - Create PRs for both forks
   - Document RASA format
   - Add usage examples

---

## References

- **BGPQ4 Fork**: https://github.com/mikabrevroc/bgpq4/tree/feature/rasa-support
- **RPKI-Client Fork**: https://github.com/mikabrevroc/rpki-client-portable/tree/feature/rasa-support
- **RASA ASN.1**: `/Users/mabrahamsson/src/reverse-as-set/RASA.asn1`
- **Progress Summary**: `/Users/mabrahamsson/src/reverse-as-set/RASA_PROGRESS_SUMMARY.md`
