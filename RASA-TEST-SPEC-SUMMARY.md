# RASA Integration Test Specification Summary

## Overview

This document provides a comprehensive summary of test cases designed to verify RASA (RPKI AS-SET Authorization) integration in bgpq4. The test suite covers all fallback modes and real-world scenarios.

## Test Suite Components

### 1. Main Test Specification: `RASA-INTEGRATION-TEST-SPECIFICATION.md`
- **irrLock mode tests** (5 test cases)
  - Locking to specific IRR sources
  - Handling AS-SET across multiple databases
  - Error handling for missing irr_source

### 2. rasaOnly Mode Tests: `RASA-TEST-CASES-rasaOnly.md`
- **rasaOnly mode tests** (4 test cases)
  - Using only RASA members, ignoring IRR
  - Handling empty members
  - Nested set processing
  - Partial RASA-AUTH scenarios

### 3. irrFallback Mode Tests: `RASA-TEST-CASES-irrFallback.md`
- **irrFallback mode tests** (4 test cases)
  - Merging RASA and IRR data
  - Conflict handling
  - RASA-AUTH validation during expansion
  - Nested set processing with fallback

### 4. Edge Case Tests: `RASA-TEST-CASES-edge-cases.md`
- **Edge case tests** (6 test cases)
  - AS-SET without RASA object
  - Invalid RASA data (malformed JSON, missing fields, invalid values)
  - Circular dependencies
  - Expired RASA objects
  - Large AS-SET performance
  - Duplicate RASA objects

### 5. Real-World Scenarios: `RASA-TEST-CASES-real-world.md`
- **Real-world scenario tests** (6 test cases)
  - AS-HURRICANE protection (massive AS-SET)
  - Content provider AS-SETs (Google, Amazon)
  - Tier-1 provider patterns (NTT, Arelion)
  - Multi-homed customer scenarios

## Test Coverage Summary

| Category | Test Count | Key Areas Covered |
|----------|-----------|-------------------|
| irrLock | 5 | RADB, RIPE, multi-DB, error handling |
| rasaOnly | 4 | Isolated RASA-only, empty members, nesting |
| irrFallback | 4 | RASA+IRR merging, validation, conflicts |
| Edge Cases | 6 | Errors, invalid data, performance, expiry |
| Real-World | 6 | Production scenarios from major providers |
| **Total** | **25** | **Comprehensive coverage** |

## Test Execution Framework

### Test Structure

Each test case includes:
```
Test ID: RASA-MODE-XXX
Description: What is being tested

Inputs:
  - RASA JSON: RASA configuration
  - IRR State: Simulated IRR database contents
  
Expected Behavior:
  - How bgpq4 should process the inputs
  
Expected Output:
  - Prefix lists or error messages
```

### Test Data Location

Test data files should be stored in:
```
rasa-testdata/
├── test-irrlock-radb.json
├── test-irrlock-ripe.json
├── test-rasaonly-basic.json
├── test-rasaonly-nested.json
├── test-irrfallback-merge.json
├── test-irrfallback-validation.json
├── test-edge-malformed.json
├── test-edge-circular.json
├── test-real-hurricane.json
├── test-real-google.json
└── test-real-ntt.json
```

## Implementation Checklist

- [ ] Create test runner script
- [ ] Mock IRR server for deterministic testing
- [ ] Generate sample RPKI-RASA JSON files
- [ ] Implement test assertions
- [ ] Add integration tests to CI/CD pipeline
- [ ] Performance benchmarking for large AS-SETs
- [ ] Memory usage validation
- [ ] Cross-platform testing (Linux, FreeBSD, macOS)

## Integration with bgpq4

### Command Line Examples

```bash
# irrLock mode (lock to specific IRR)
bgpq4 -Jl peer-filter -rasa-config /etc/rasa/ntt.json AS2914:AS-GLOBAL

# rasaOnly mode (no IRR queries)
bgpq4 -Jl peer-filter -rasa-config /etc/rasa/google.json -rasa-only AS-GOOGLE

# irrFallback mode (default)
bgpq4 -Jl peer-filter -rasa-config /etc/rasa/default.json AS-CUSTOMER

# With bidirectional verification
gpqa -Jl peer-filter -rasa-config /etc/rasa/rasa-auth.json -rasa-set-config /etc/rasa/rasa-set.json AS-TEST
```

### Exit Codes

- `0`: Success, prefix list generated
- `1`: Configuration error (invalid RASA, missing files)
- `2`: Network error (IRR unreachable)
- `3`: Authorization failure (RASA validation failed)
- `4`: Partial success (some ASNs excluded due to RASA)

## Verification Metrics

**Functional Testing**:
- All 25 test cases pass
- Correct AS-SET expansion in each mode
- Proper RASA-AUTH validation

**Performance Testing**:
- 100 ASNs: < 30 seconds
- 1000 ASNs: < 5 minutes
- Memory usage: < 512MB for large AS-SETs

**Security Testing**:
- Unauthorized ASNs excluded
- IRR poisoning attacks blocked
- Complete RASA validation coverage

## Test Execution Priority

**Priority 1 (Critical)**:
- irrLock tests (1.1, 1.2, 1.3)
- rasaOnly basic test (2.1)
- irrFallback merging (3.1)
- Real-world AS-HURRICANE (5.1)

**Priority 2 (High)**:
- All irrLock tests (1.x)
- rasaOnly nested sets (2.3)
- irrFallback validation (3.3)
- Edge case: no RASA object (4.1)

**Priority 3 (Medium)**:
- All rasaOnly tests (2.x)
- irrFallback nested sets (3.4)
- Edge cases (4.2-4.6)
- Real-world scenarios (5.2-5.6)

## Files Generated

1. `RASA-INTEGRATION-TEST-SPECIFICATION.md` - Main test spec
2. `RASA-TEST-CASES-rasaOnly.md` - rasaOnly mode tests
3. `RASA-TEST-CASES-irrFallback.md` - irrFallback mode tests
4. `RASA-TEST-CASES-edge-cases.md` - Edge cases
5. `RASA-TEST-CASES-real-world.md` - Real-world scenarios
6. `RASA-TEST-SPEC-SUMMARY.md` - This summary document

## Next Steps

1. **Review and approval** of test specifications
2. **Implement test framework** using existing bgpq4 test infrastructure
3. **Create mock data** for all test cases
4. **Implement test runner** with assertions
5. **Execute test suite** and validate results
6. **Integrate with CI/CD** for automated testing
7. **Performance testing** with production-scale data

## Contributing

To add new test cases:
1. Determine appropriate category sheet
2. Follow existing test case format
3. Include clear inputs and expected outputs
4. Update this summary
5. Submit for review

For questions or issues, contact the RASA implementation team.
