# Test Function Analysis: test_rasa_comprehensive.c

## Summary

Found **44 test functions** in `test_rasa_comprehensive.c` that start with `test_rasa_auth_`.

All functions are `static void` and follow the naming convention `test_rasa_auth_<description>`.

## List of Test Functions

```
static void test_rasa_auth_load_valid(void) {
static void test_rasa_auth_load_null_filename(void) {
static void test_rasa_auth_load_invalid_json(void) {
static void test_rasa_auth_load_empty_object(void) {
static void test_rasa_auth_load_missing_rasas(void) {
static void test_rasa_auth_check_null_result(void) {
static void test_rasa_auth_check_no_config(void) {
static void test_rasa_auth_check_single_asn(void) {
static void test_rasa_auth_check_wrong_asn(void) {
static void test_rasa_auth_check_wrong_asset(void) {
static void test_rasa_auth_multiple_asns(void) {
static void test_rasa_auth_multiple_assets_single_asn(void) {
static void test_rasa_auth_empty_authorized_in(void) {
static void test_rasa_auth_no_authorized_in_key(void) {
static void test_rasa_auth_special_chars_in_asset(void) {
static void test_rasa_auth_32bit_asn(void) {
static void test_rasa_auth_asn_zero(void) {
static void test_rasa_auth_large_asn_16bit_max(void) {
static void test_rasa_auth_large_asn_16bit_plus_one(void) {
static void test_rasa_auth_duplicate_entries(void) {
static void test_rasa_auth_null_asset(void) {
static void test_rasa_auth_empty_asset(void) {
static void test_rasa_auth_whitespace_asset(void) {
static void test_rasa_auth_case_sensitive(void) {
static void test_rasa_auth_malformed_entry(void) {
static void test_rasa_auth_missing_asset_field(void) {
static void test_rasa_auth_non_integer_asn(void) {
static void test_rasa_auth_negative_asn(void) {
static void test_rasa_auth_reuse_config_struct(void) {
static void test_rasa_auth_free_null_config(void) {
static void test_rasa_auth_many_asns(void) {
static void test_rasa_auth_many_assets(void) {
static void test_rasa_auth_asn_not_in_any_rasa(void) {
static void test_rasa_auth_different_assets_different_asns(void) {
static void test_rasa_auth_overlapping_authorizations(void) {
static void test_rasa_auth_long_asset_name(void) {
static void test_rasa_auth_extra_fields_ignored(void) {
static void test_rasa_auth_minimal_valid(void) {
static void test_rasa_auth_propagation_field(void) {
static void test_rasa_auth_nested_entry_format(void) {
static void test_rasa_auth_very_large_asn(void) {
static void test_rasa_auth_private_asn(void) {
static void test_rasa_auth_reserved_asn(void) {
static void test_rasa_auth_nested_arrays(void) {
```

## Verification

- Source file: `/Users/mabrahamsson/src/reverse-as-set/tests/test_rasa_comprehensive.c`
- Search pattern: `static void test_rasa_auth_`
- Match count: 44
- All matches confirmed to be valid test functions
- No false positives or naming mismatches found

## Next Steps

- [ ] Review test coverage for authentication-related edge cases
- [ ] Consider adding new tests for untested edge cases
- [ ] Document test categories for future maintenance

> ✅ Task completed: Successfully identified and listed all 44 `test_rasa_auth_` functions in `test_rasa_comprehensive.c`.