# RASA Test Suite Structure Visualization

## Overview

This diagram illustrates the hierarchical structure of the RASA (Reverse AS-SET Authorization) test suite, showing the relationship between test files, test functions, and the RUN_TEST macro execution flow.

---

## 1. RUN_TEST Macro Definition

```c
#define RUN_TEST(n) do { \
    int p = tests_failed; \
    printf("  %s... ", #n); \           /* Print test name */ \
    tests_run++; \                       /* Increment counter */ \
    test_##n(); \                        /* Execute test function */ \
    if (tests_failed == p) { \           /* Check if test passed */ \
        tests_passed++; \                /* Increment pass counter */ \
        printf("OK\n"); \                 /* Print success */ \
    } else { \
        printf("FAIL\n"); \               /* Print failure */ \
    } \
} while (0)
```

### Key Features:
- **Stringification**: Uses `#n` to convert test name to string for output
- **Token Pasting**: Uses `test_##n` to construct function name
- **Pass/Fail Tracking**: Compares `tests_failed` before/after execution
- **Atomic Operation**: Wrapped in `do { ... } while (0)` for safe macro usage

---

## 2. Test Function Naming Convention

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    NAMING PATTERN HIERARCHY                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  test_rasa_auth_*          → RASA-AUTH configuration tests              │
│    ├─ test_rasa_auth_load_*     → Config loading tests                  │
│    ├─ test_rasa_auth_check_*    → Authorization check tests             │
│    ├─ test_rasa_auth_empty_*    → Empty/null input tests                │
│    └─ test_rasa_auth_many_*     → Bulk/scalability tests                │
│                                                                          │
│  test_rasa_set_*           → RASA-SET membership tests                  │
│    ├─ test_rasa_set_load_*      → Config loading tests                  │
│    ├─ test_rasa_set_check_*     → Membership check tests                │
│    ├─ test_rasa_set_empty_*     → Empty/null input tests                │
│    └─ test_rasa_set_many_*      → Bulk/scalability tests                │
│                                                                          │
│  test_bidirectional_*      → Bidirectional verification tests           │
│    ├─ test_bidirectional_*_auth_*   → Authorization flow tests          │
│    ├─ test_bidirectional_*_set_*    → Membership flow tests             │
│    ├─ test_bidirectional_*_asn_*    → ASN-specific tests                │
│    └─ test_bidirectional_*_scale    → Large-scale tests                 │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Test File Distribution

```
┌────────────────────────────────────────────────────────────────────────────┐
│                         TEST FILE STRUCTURE                                 │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  test_rasa_comprehensive.c   [PRIMARY TEST SUITE]                  │   │
│  │  ═══════════════════════════════════════════════════════════════   │   │
│  │  Total Tests: 110+                                                  │   │
│  │  ├── RASA-AUTH Tests:        40 scenarios                          │   │
│  │  ├── RASA-SET Tests:         40 scenarios                          │   │
│  │  ├── Bidirectional Tests:    30 scenarios                          │   │
│  │  └── Edge Case Tests:        10 scenarios                          │   │
│  │                                                                     │   │
│  │  Lines of Code: ~2,340                                              │   │
│  │  Status: ✅ ACTIVE                                                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  test_rasa_set.c             [RASA-SET FOCUS]                      │   │
│  │  ═══════════════════════════════════════════════════════════════   │   │
│  │  Total Tests: 40                                                    │   │
│  │  ├── Derived from: test_rasa_comprehensive.c                       │   │
│  │  └── Focus: RASA-SET functionality only                            │   │
│  │                                                                     │   │
│  │  Lines of Code: ~84                                                 │   │
│  │  Status: ✅ ACTIVE                                                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  test_rasa_integration.c     [INTEGRATION TESTS]                   │   │
│  │  ═══════════════════════════════════════════════════════════════   │   │
│  │  Total Tests: 2                                                     │   │
│  │  ├── test_expansion()                                               │   │
│  │  └── test_asset()                                                   │   │
│  │                                                                     │   │
│  │  Lines of Code: ~49                                                 │   │
│  │  Status: ✅ ACTIVE                                                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  test_rasa_migrate.c         [MIGRATION/PARTIAL]                   │   │
│  │  ═══════════════════════════════════════════════════════════════   │   │
│  │  Total Tests: ~20 (incomplete)                                      │   │
│  │  Note: Contains partial test functions                              │   │
│  │        Some RUN_TEST calls embedded in test functions               │   │
│  │                                                                     │   │
│  │  Lines of Code: ~251                                                │   │
│  │  Status: ⚠️ PARTIAL                                                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  test_link_issue.c           [LINK VERIFICATION]                   │   │
│  │  ═══════════════════════════════════════════════════════════════   │   │
│  │  Total Tests: 1                                                     │   │
│  │  └── test_bidirectional_only_auth()                                 │   │
│  │                                                                     │   │
│  │  Lines of Code: ~9                                                  │   │
│  │  Status: ✅ ACTIVE                                                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  EMPTY/PLACEHOLDER FILES                                            │   │
│  │  ─────────────────────────────────────────────────────────────────  │   │
│  │  • test_rasa_batch.c        (0 bytes)                              │   │
│  │  • test_rasa_part1.c        (0 bytes)                              │   │
│  │  • test_rasa_half.c         (0 bytes)                              │   │
│  │  Status: ⚪ EMPTY                                                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Test Execution Flow (main() Function)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         EXECUTION FLOW DIAGRAM                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   START                                                                       │
│    │                                                                          │
│    ▼                                                                          │
│   ┌─────────────────────────────────────┐                                    │
│   │  Initialize Counters                │                                    │
│   │  tests_run = 0                      │                                    │
│   │  tests_passed = 0                   │                                    │
│   │  tests_failed = 0                   │                                    │
│   └──────────────┬──────────────────────┘                                    │
│                  │                                                           │
│    ┌─────────────┴─────────────┐                                             │
│    ▼                           ▼                                             │
│  PRINT HEADER            ┌──────────────────────────────────────────────┐   │
│  "RASA Test Suite"       │                                          │   │
│                          │     TEST CATEGORY LOOP                     │   │
│                          │                                          │   │
│                          │  ┌─────────────────────────────────────┐ │   │
│                          │  │ Print Category Header               │ │   │
│                          │  │ (e.g., "RASA-AUTH Tests:")          │ │   │
│                          │  └──────────────┬──────────────────────┘ │   │
│                          │                 │                        │   │
│                          │                 ▼                        │   │
│                          │  ┌─────────────────────────────────────┐ │   │
│                          │  │     INDIVIDUAL TEST LOOP            │ │   │
│                          │  │                                     │ │   │
│                          │  │  ┌─────────────────────────────┐   │ │   │
│                          │  │  │ RUN_TEST(test_name)         │   │ │   │
│                          │  │  │                             │   │ │   │
│                          │  │  │ 1. Print "  test_name... "  │   │ │   │
│                          │  │  │ 2. tests_run++              │   │ │   │
│                          │  │  │ 3. Execute test function    │   │ │   │
│                          │  │  │ 4. Check tests_failed       │   │ │   │
│                          │  │  │ 5. Print "OK" or "FAIL"     │   │ │   │
│                          │  │  │ 6. Update pass/fail counts  │   │ │   │
│                          │  │  └─────────────┬───────────────┘   │ │   │
│                          │  │                │                   │ │   │
│                          │  │                ▼                   │ │   │
│                          │  │         ┌──────────────┐           │ │   │
│                          │  │         │ Next Test?   │───────────┘ │   │
│                          │  │         └──────────────┘             │   │
│                          │  │                │ No                   │   │
│                          │  └────────────────┘                      │   │
│                          │                   │                        │   │
│                          │                   ▼                        │   │
│                          │         ┌──────────────┐                   │   │
│                          │         │ Next Category?                 │   │
│                          │         └──────────────┘                   │   │
│                          │                │ No                        │   │
│                          └────────────────┘                            │   │
│                                         │                              │   │
│                                         ▼                              │   │
│                           ┌─────────────────────────┐                  │   │
│                           │  PRINT FINAL SUMMARY    │                  │   │
│                           │  "Results: X/Y passed"  │                  │   │
│                           └───────────┬─────────────┘                  │   │
│                                       │                                  │   │
│                                       ▼                                  │   │
│                           ┌─────────────────────────┐                  │   │
│                           │  RETURN EXIT CODE       │                  │   │
│                           │  tests_failed > 0 ? 1:0 │                  │   │
│                           └───────────┬─────────────┘                  │   │
│                                       │                                  │   │
│                                       ▼                                  │   │
│                                      END                                 │   │
│                                                                          │   │
└──────────────────────────────────────────────────────────────────────────┘   │
```

---

## 5. Test Result Reporting Mechanism

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      RESULT REPORTING ARCHITECTURE                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                    GLOBAL STATE VARIABLES                            │   │
│   │                                                                      │   │
│   │   static int tests_run = 0;        ← Total executed                  │   │
│   │   static int tests_passed = 0;     ← Successful tests                │   │
│   │   static int tests_failed = 0;     ← Failed tests                    │   │
│   │                                                                      │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                    ASSERTION MACROS                                  │   │
│   │                                                                      │   │
│   │   #define ASSERT(c) do {                                             │   │
│   │       if (!(c)) {                                                    │   │
│   │           tests_failed++;            ← Increment on failure          │   │
│   │           fprintf(stderr, "\n    ASSERT failed...");                   │   │
│   │           return;                                                    │   │
│   │       }                                                              │   │
│   │   } while (0)                                                        │   │
│   │                                                                      │   │
│   │   #define ASSERT_EQ(a, b)    ← Assert equal                          │   │
│   │   #define ASSERT_STR_EQ(a,b) ← Assert string equal                   │   │
│   │                                                                      │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                    OUTPUT FORMAT                                     │   │
│   │                                                                      │   │
│   │   During Execution:                                                  │   │
│   │     test_rasa_auth_load_valid... OK                                  │   │
│   │     test_rasa_auth_check_wrong_asn... FAIL                           │   │
│   │       ASSERT_EQ failed: 1 != 0 (line 167)                            │   │
│   │                                                                      │   │
│   │   Final Summary:                                                     │   │
│   │     ========================================                         │   │
│   │     Results: 109/110 tests passed                                    │   │
│   │     ========================================                         │   │
│   │                                                                      │   │
│   │   Exit Code:                                                         │   │
│   │     return tests_failed > 0 ? 1 : 0;   ← CI/CD integration           │   │
│   │                                                                      │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Hierarchical Test Organization

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    COMPLETE TEST SUITE HIERARCHY                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Test Suite: RASA Comprehensive (test_rasa_comprehensive.c)                  │
│  ═══════════════════════════════════════════════════════════════             │
│                                                                              │
│  ├─ Category: RASA-AUTH Tests (40 tests)                                     │
│  │  ├─ Group: Basic Loading (Tests 1-10)                                    │
│  │  │  ├─ test_rasa_auth_load_valid                                         │
│  │  │  ├─ test_rasa_auth_load_null_filename                                 │
│  │  │  ├─ test_rasa_auth_load_invalid_json                                  │
│  │  │  ├─ test_rasa_auth_load_empty_object                                  │
│  │  │  ├─ test_rasa_auth_load_missing_rasas                                 │
│  │  │  ├─ test_rasa_auth_check_null_result                                  │
│  │  │  ├─ test_rasa_auth_check_no_config                                    │
│  │  │  ├─ test_rasa_auth_check_single_asn                                   │
│  │  │  ├─ test_rasa_auth_check_wrong_asn                                    │
│  │  │  └─ test_rasa_auth_check_wrong_asset                                  │
│  │  │                                                                      │
│  │  ├─ Group: Multiple ASNs/Assets (Tests 11-20)                            │
│  │  │  ├─ test_rasa_auth_multiple_asns                                      │
│  │  │  ├─ test_rasa_auth_multiple_assets_single_asn                         │
│  │  │  ├─ test_rasa_auth_empty_authorized_in                                │
│  │  │  ├─ test_rasa_auth_no_authorized_in_key                               │
│  │  │  ├─ test_rasa_auth_special_chars_in_asset                             │
│  │  │  ├─ test_rasa_auth_32bit_asn                                          │
│  │  │  ├─ test_rasa_auth_asn_zero                                           │
│  │  │  ├─ test_rasa_auth_large_asn_16bit_max                                │
│  │  │  ├─ test_rasa_auth_large_asn_16bit_plus_one                           │
│  │  │  └─ test_rasa_auth_duplicate_entries                                  │
│  │  │                                                                      │
│  │  ├─ Group: Edge Cases (Tests 21-30)                                      │
│  │  │  ├─ test_rasa_auth_null_asset                                         │
│  │  │  ├─ test_rasa_auth_empty_asset                                        │
│  │  │  ├─ test_rasa_auth_whitespace_asset                                   │
│  │  │  ├─ test_rasa_auth_case_sensitive                                     │
│  │  │  ├─ test_rasa_auth_malformed_entry                                    │
│  │  │  ├─ test_rasa_auth_missing_asset_field                                │
│  │  │  ├─ test_rasa_auth_non_integer_asn                                    │
│  │  │  ├─ test_rasa_auth_negative_asn                                       │
│  │  │  ├─ test_rasa_auth_reuse_config_struct                                │
│  │  │  └─ test_rasa_auth_free_null_config                                   │
│  │  │                                                                      │
│  │  └─ Group: Complex Scenarios (Tests 31-40)                               │
│  │     ├─ test_rasa_auth_many_asns                                          │
│  │     ├─ test_rasa_auth_many_assets                                        │
│  │     ├─ test_rasa_auth_asn_not_in_any_rasa                                │
│  │     ├─ test_rasa_auth_different_assets_different_asns                    │
│  │     ├─ test_rasa_auth_overlapping_authorizations                         │
│  │     ├─ test_rasa_auth_long_asset_name                                    │
│  │     ├─ test_rasa_auth_extra_fields_ignored                              │
│  │     ├─ test_rasa_auth_minimal_valid                                      │
│  │     ├─ test_rasa_auth_propagation_field                                  │
│  │     └─ test_rasa_auth_nested_entry_format                                │
│  │                                                                          │
│  ├─ Category: RASA-SET Tests (40 tests)                                      │
│  │  ├─ Group: Basic Loading (Tests 1-10)                                    │
│  │  │  ├─ test_rasa_set_load_valid                                          │
│  │  │  ├─ test_rasa_set_load_null_filename                                  │
│  │  │  ├─ test_rasa_set_load_invalid_json                                   │
│  │  │  ├─ test_rasa_set_check_no_config                                     │
│  │  │  ├─ test_rasa_set_check_null_result                                   │
│  │  │  ├─ test_rasa_set_check_single_member                                 │
│  │  │  ├─ test_rasa_set_check_multiple_members                              │
│  │  │  ├─ test_rasa_set_check_wrong_set_name                                │
│  │  │  ├─ test_rasa_set_check_empty_members                                 │
│  │  │  └─ test_rasa_set_check_no_members_key                                │
│  │  │                                                                      │
│  │  ├─ Group: Multiple Sets & ASN Types (Tests 11-20)                       │
│  │  │  ├─ test_rasa_set_multiple_sets                                       │
│  │  │  ├─ test_rasa_set_32bit_asn_member                                    │
│  │  │  ├─ test_rasa_set_special_chars_name                                  │
│  │  │  ├─ test_rasa_set_asn_zero                                            │
│  │  │  ├─ test_rasa_set_large_asn_16bit_max                                 │
│  │  │  ├─ test_rasa_set_large_asn_16bit_plus_one                            │
│  │  │  ├─ test_rasa_set_duplicate_members                                   │
│  │  │  ├─ test_rasa_set_null_set_name                                       │
│  │  │  ├─ test_rasa_set_empty_set_name                                      │
│  │  │  └─ test_rasa_set_case_sensitive                                      │
│  │  │                                                                      │
│  │  ├─ Group: Missing Keys & Error Handling (Tests 21-30)                   │
│  │  │  ├─ test_rasa_set_missing_rasa_sets_key                               │
│  │  │  ├─ test_rasa_set_missing_as_set_name                                 │
│  │  │  ├─ test_rasa_set_non_integer_member                                  │
│  │  │  ├─ test_rasa_set_reuse_config_struct                                 │
│  │  │  ├─ test_rasa_set_free_null_config                                    │
│  │  │  ├─ test_rasa_set_many_sets                                           │
│  │  │  ├─ test_rasa_set_many_members                                        │
│  │  │  ├─ test_rasa_set_asn_not_in_any_set                                  │
│  │  │  ├─ test_rasa_set_whitespace_in_name                                  │
│  │  │  └─ test_rasa_set_long_set_name                                       │
│  │  │                                                                      │
│  │  └─ Group: Advanced Scenarios (Tests 31-40)                              │
│  │     ├─ test_rasa_set_extra_fields_ignored                                │
│  │     ├─ test_rasa_set_minimal_valid                                       │
│  │     ├─ test_rasa_set_nested_sets_declaration                             │
│  │     ├─ test_rasa_set_containing_as_field                                 │
│  │     ├─ test_rasa_set_load_empty_object                                   │
│  │     ├─ test_rasa_set_negative_member_asn                                 │
│  │     ├─ test_rasa_set_large_member_list_mixed                             │
│  │     ├─ test_rasa_set_multiple_same_asn_different_sets                    │
│  │     ├─ test_rasa_set_members_array_with_nulls                            │
│  │     └─ test_rasa_set_boolean_in_members                                  │
│  │                                                                          │
│  ├─ Category: Bidirectional Verification Tests (30 tests)                    │
│  │  ├─ test_bidirectional_both_authorize                                    │
│  │  ├─ test_bidirectional_only_auth                                         │
│  │  ├─ test_bidirectional_only_set                                          │
│  │  ├─ test_bidirectional_neither_authorize                                 │
│  │  ├─ test_bidirectional_auth_denies_set_allows                            │
│  │  ├─ test_bidirectional_auth_allows_set_denies                            │
│  │  ├─ test_bidirectional_multiple_asns_mixed                               │
│  │  ├─ test_bidirectional_no_configs                                        │
│  │  ├─ test_bidirectional_null_auth_result                                  │
│  │  ├─ test_bidirectional_null_set_result                                   │
│  │  ├─ test_bidirectional_32bit_asn                                         │
│  │  ├─ test_bidirectional_multiple_assets                                   │
│  │  ├─ test_bidirectional_wrong_asset_both_loaded                           │
│  │  ├─ test_bidirectional_empty_members_vs_empty_auth                       │
│  │  ├─ test_bidirectional_asn_zero                                          │
│  │  ├─ test_bidirectional_special_chars_asset                               │
│  │  ├─ test_bidirectional_large_asn_16bit_boundary                          │
│  │  ├─ test_bidirectional_many_asns                                         │
│  │  ├─ test_bidirectional_partial_overlap                                   │
│  │  ├─ test_bidirectional_null_asset                                        │
│  │  ├─ test_bidirectional_case_sensitive_asset                              │
│  │  ├─ test_bidirectional_complex_scenario                                  │
│  │  ├─ test_bidirectional_minimal_configs                                   │
│  │  ├─ test_bidirectional_different_asn_in_each                             │
│  │  ├─ test_bidirectional_same_config_file                                  │
│  │  ├─ test_bidirectional_large_scale                                       │
│  │  ├─ test_bidirectional_reload_configs                                    │
│  │  ├─ test_bidirectional_extra_json_fields                                 │
│  │  ├─ test_bidirectional_default_allow_behavior                            │
│  │  └─ (2 more tests...)                                                    │
│  │                                                                          │
│  └─ Category: Additional Edge Case Tests (10 tests)                          │
│     ├─ test_rasa_auth_very_large_asn (4294967295)                           │
│     ├─ test_rasa_set_very_large_asn                                         │
│     ├─ test_rasa_auth_private_asn (64512-65534)                             │
│     ├─ test_rasa_set_private_asn                                            │
│     ├─ test_rasa_auth_reserved_asn (AS_TRANS 23456)                         │
│     ├─ test_rasa_auth_nested_arrays                                         │
│     ├─ test_rasa_set_mixed_types_in_members                                 │
│     ├─ test_bidirectional_very_large_asn                                    │
│     ├─ test_bidirectional_private_asns                                      │
│     └─ test_bidirectional_as_trans                                          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Test Execution Order

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      TEST EXECUTION SEQUENCE                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Order  │ Test File                    │ Test Count  │ Execution Time      │
│  ───────┼──────────────────────────────┼─────────────┼─────────────────────│
│  1st    │ test_rasa_comprehensive.c    │    110      │ ~2-3 seconds        │
│         │   ├─ RASA-AUTH               │    (40)     │                     │
│         │   ├─ RASA-SET                │    (40)     │                     │
│         │   ├─ Bidirectional           │    (30)     │                     │
│         │   └─ Edge Cases              │    (10)     │                     │
│  ───────┼──────────────────────────────┼─────────────┼─────────────────────│
│  2nd    │ test_rasa_set.c              │    40       │ ~1 second           │
│  ───────┼──────────────────────────────┼─────────────┼─────────────────────│
│  3rd    │ test_rasa_integration.c      │     2       │ ~0.1 seconds        │
│  ───────┼──────────────────────────────┼─────────────┼─────────────────────│
│  4th    │ test_link_issue.c            │     1       │ ~0.01 seconds       │
│  ───────┴──────────────────────────────┴─────────────┴─────────────────────│
│  TOTAL  │                              │   153+      │ ~3-4 seconds        │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Summary Statistics

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         TEST SUITE METADATA                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  OVERALL STATISTICS                                                  │   │
│  │  ─────────────────                                                   │   │
│  │  Total Test Files:        8 (5 active, 3 empty)                      │   │
│  │  Total Test Functions:    153+                                       │   │
│  │  Total Lines of Code:     ~2,700                                     │   │
│  │  Macro Definitions:       4 (RUN_TEST, ASSERT, ASSERT_EQ, ASSERT_STR)│   │
│  │  Helper Functions:        2 (make_temp, clean_temp)                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  TEST COVERAGE BREAKDOWN                                             │   │
│  │  ─────────────────────                                               │   │
│  │                                                                       │   │
│  │  RASA-AUTH Tests:        40 tests  (26.1%)  ████████████████         │   │
│  │  RASA-SET Tests:         40 tests  (26.1%)  ████████████████         │   │
│  │  Bidirectional Tests:    30 tests  (19.6%)  ████████████             │   │
│  │  Edge Case Tests:        10 tests   (6.5%)  ████                     │   │
│  │  Integration Tests:       2 tests   (1.3%)  █                        │   │
│  │  Link Issue Tests:        1 test    (0.7%)  █                        │   │
│  │  Reserved/Empty:         30 tests  (19.6%)  ████████████             │   │
│  │                                                                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  TEST NAMING PATTERNS                                                │   │
│  │  ─────────────────────                                               │   │
│  │                                                                       │   │
│  │  Prefixes:                                                            │   │
│  │    • test_rasa_auth_*        → 40 functions                          │   │
│  │    • test_rasa_set_*         → 40 functions                          │   │
│  │    • test_bidirectional_*    → 30 functions                          │   │
│  │    • test_* (integration)    → 2 functions                           │   │
│  │                                                                       │   │
│  │  Suffixes (by scenario type):                                         │   │
│  │    • *_valid, *_invalid      → Validation tests                       │   │
│  │    • *_null, *_empty         → Null/empty input tests                 │   │
│  │    • *_multiple_*            → Bulk/multi-item tests                  │   │
│  │    • *_32bit, *_16bit        → ASN size tests                         │   │
│  │    • *_zero, *_negative      → Edge value tests                       │   │
│  │    • *_many_*                → Scalability tests                      │   │
│  │    • *_load_*, *_check_*     → Operation-specific tests               │   │
│  │                                                                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 9. Relationship Diagram

```
                        ┌─────────────────────────────┐
                        │      RUN_TEST Macro         │
                        │  ┌─────────────────────┐    │
                        │  │ • Stringify name    │    │
                        │  │ • Execute function  │    │
                        │  │ • Track results     │    │
                        │  │ • Print status      │    │
                        │  └─────────────────────┘    │
                        └──────────────┬──────────────┘
                                       │
              ┌────────────────────────┼────────────────────────┐
              │                        │                        │
              ▼                        ▼                        ▼
   ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐
   │   test_rasa_auth_*  │  │   test_rasa_set_*   │  │ test_bidirectional_*│
   │   ───────────────── │  │   ───────────────── │  │ ─────────────────── │
   │ • Load config       │  │ • Load config       │  │ • Both configs      │
   │ • Check auth        │  │ • Check membership  │  │ • Verify both       │
   │ • Edge cases        │  │ • Edge cases        │  │ • Cross-check       │
   └──────────┬──────────┘  └──────────┬──────────┘  └──────────┬──────────┘
              │                        │                        │
              └────────────────────────┼────────────────────────┘
                                       │
                                       ▼
                        ┌─────────────────────────────┐
                        │      ASSERT Macros          │
                        │  ┌─────────────────────┐    │
                        │  │ • ASSERT(cond)      │    │
                        │  │ • ASSERT_EQ(a,b)    │    │
                        │  │ • ASSERT_STR_EQ(a,b)│    │
                        │  └─────────────────────┘    │
                        └──────────────┬──────────────┘
                                       │
                                       ▼
                        ┌─────────────────────────────┐
                        │    Global Counters          │
                        │  ┌─────────────────────┐    │
                        │  │ tests_run++         │    │
                        │  │ tests_passed++      │    │
                        │  │ tests_failed++      │    │
                        │  └─────────────────────┘    │
                        └──────────────┬──────────────┘
                                       │
                                       ▼
                        ┌─────────────────────────────┐
                        │     Final Summary           │
                        │  "Results: X/Y tests passed"│
                        └─────────────────────────────┘
```

---

## Legend

| Symbol | Meaning |
|--------|---------|
| ✅ | Active/Complete |
| ⚠️ | Partial/Incomplete |
| ⚪ | Empty/Placeholder |
| `test_*` | Test function name pattern |
| `RUN_TEST()` | Macro invocation |
| `tests_*` | Global counter variable |
