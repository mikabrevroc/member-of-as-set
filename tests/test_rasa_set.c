/*
 * RASA-SET Test Suite
 * Generated from test_rasa_comprehensive.c
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "test_framework.h"
#include "rasa_set.h"
#include "rasa_auth.h"

// Helper functions
static char * make_temp(const char *prefix) {
    char *temp = malloc(256);
    snprintf(temp, 256, "%sXXXXXX", prefix);
    mktemp(temp);
    return temp;
}

static void clean_temp(const char *path) {
    if (path) {
        unlink(path);
    }
}

// Test functions
// (All 40 RASA-SET test functions)
// ... (function bodies copied from lines 623-1160)

// New main function
int main(void) {
    printf("\n========================================\n");
    printf("RASA-SET Test Suite\n");
    printf("========================================\n\n");

    // All 40 RASA-SET RUN_TEST calls here
    RUN_TEST(rasa_set_load_valid);
    RUN_TEST(rasa_set_load_null_filename);
    RUN_TEST(rasa_set_load_invalid_json);
    RUN_TEST(rasa_set_check_no_config);
    RUN_TEST(rasa_set_check_null_result);
    RUN_TEST(rasa_set_check_single_member);
    RUN_TEST(rasa_set_check_multiple_members);
    RUN_TEST(rasa_set_check_wrong_set_name);
    RUN_TEST(rasa_set_check_empty_members);
    RUN_TEST(rasa_set_check_no_members_key);
    RUN_TEST(rasa_set_multiple_sets);
    RUN_TEST(rasa_set_32bit_asn_member);
    RUN_TEST(rasa_set_special_chars_name);
    RUN_TEST(rasa_set_asn_zero);
    RUN_TEST(rasa_set_large_asn_16bit_max);
    RUN_TEST(rasa_set_large_asn_16bit_plus_one);
    RUN_TEST(rasa_set_duplicate_members);
    RUN_TEST(rasa_set_null_set_name);
    RUN_TEST(rasa_set_empty_set_name);
    RUN_TEST(rasa_set_case_sensitive);
    RUN_TEST(rasa_set_missing_rasa_sets_key);
    RUN_TEST(rasa_set_missing_as_set_name);
    RUN_TEST(rasa_set_non_integer_member);
    RUN_TEST(rasa_set_reuse_config_struct);
    RUN_TEST(rasa_set_free_null_config);
    RUN_TEST(rasa_set_many_sets);
    RUN_TEST(rasa_set_many_members);
    RUN_TEST(rasa_set_asn_not_in_any_set);
    RUN_TEST(rasa_set_whitespace_in_name);
    RUN_TEST(rasa_set_long_set_name);
    RUN_TEST(rasa_set_extra_fields_ignored);
    RUN_TEST(rasa_set_minimal_valid);
    RUN_TEST(rasa_set_nested_sets_declaration);
    RUN_TEST(rasa_set_containing_as_field);
    RUN_TEST(rasa_set_load_empty_object);
    RUN_TEST(rasa_set_negative_member_asn);
    RUN_TEST(rasa_set_large_member_list_mixed);
    RUN_TEST(rasa_set_multiple_same_asn_different_sets);
    RUN_TEST(rasa_set_members_array_with_nulls);
    RUN_TEST(rasa_set_boolean_in_members);

    printf("\n========================================\n");
    printf("Results: %d/%d tests passed\n", tests_passed, tests_run);
    printf("========================================\n\n");

    return tests_failed > 0 ? 1 : 0;
}