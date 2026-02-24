static void test_rasa_auth_load_valid(void) {
    struct rasa_config cfg = {0};
    const char *json = "{\"rasas\":[{\"rasa\":{\"authorized_as\":64496}}]}";
    char *path = make_temp(json);
    ASSERT(path);
    ASSERT_EQ(rasa_load_config(&cfg, path), 0);
    ASSERT_EQ(cfg.enabled, 1);
    rasa_free_config(&cfg);
    clean_temp(path);
}

static void test_rasa_auth_load_null_filename(void) {
    struct rasa_config cfg = {0};
    ASSERT_EQ(rasa_load_config(&cfg, NULL), -1);
}

static void test_rasa_auth_load_invalid_json(void) {
    struct rasa_config cfg = {0};
    const char *json = "{invalid json";
    char *path = make_temp(json);
    ASSERT(path);
    ASSERT_EQ(rasa_load_config(&cfg, path), -1);
    clean_temp(path);
}

static void test_rasa_auth_load_empty_object(void) {
    struct rasa_config cfg = {0};
    const char *json = "{}";
    char *path = make_temp(json);
    ASSERT(path);
    ASSERT_EQ(rasa_load_config(&cfg, path), 0);
    ASSERT_EQ(cfg.enabled, 1);
    rasa_free_config(&cfg);
    clean_temp(path);
}

static void test_rasa_auth_load_missing_rasas(void) {
    struct rasa_config cfg = {0};
    const char *json = "{\"other_key\": \"value\"}";
    char *path = make_temp(json);
    ASSERT(path);
    ASSERT_EQ(rasa_load_config(&cfg, path), 0);
    rasa_free_config(&cfg);
    clean_temp(path);
}

static void test_rasa_auth_check_null_result(void) {
    ASSERT_EQ(rasa_check_auth(64496, "AS-TEST", NULL), -1);
}

static void test_rasa_auth_check_no_config(void) {
    struct rasa_auth result = {0};
    ASSERT_EQ(rasa_check_auth(64496, "AS-TEST", &result), 0);
    ASSERT_EQ(result.authorized, 1);
}

static void test_rasa_auth_check_single_asn(void) {
    struct rasa_config cfg = {0};
    struct rasa_auth result = {0};
    const char *json = "{\"rasas\":[{\"rasa\":{\"authorized_as\":64496,\"authorized_in\":[{\"entry\":{\"asset\":\"AS-TEST\"}}]}}]}";
    char *path = make_temp(json);
    ASSERT(path);
    rasa_load_config(&cfg, path);
    ASSERT_EQ(rasa_check_auth(64496, "AS-TEST", &result), 0);
    ASSERT_EQ(result.authorized, 1);
    rasa_free_config(&cfg);
    clean_temp(path);
}

static void test_rasa_auth_check_wrong_asn(void) {
    struct rasa_config cfg = {0};
    struct rasa_auth result = {0};
    const char *json = "{\"rasas\":[{\"rasa\":{\"authorized_as\":64496,\"authorized_in\":[{\"entry\":{\"asset\":\"AS-TEST\"}}]}}]}";
    char *path = make_temp(json);
    ASSERT(path);
    rasa_load_config(&cfg, path);
    ASSERT_EQ(rasa_check_auth(64497, "AS-TEST", &result), 0);
    ASSERT_EQ(result.authorized, 0);
    rasa_free_config(&cfg);
    clean_temp(path);
}

static void test_rasa_auth_check_wrong_asset(void) {
    struct rasa_config cfg = {0};
    struct rasa_auth result = {0};
    const char *json = "{\"rasas\":[{\"rasa\":{\"authorized_as\":64496,\"authorized_in\":[{\"entry\":{\"asset\":\"AS-TEST\"}}]}}]}";
    char *path = make_temp(json);
    ASSERT(path);
    rasa_load_config(&cfg, path);
    ASSERT_EQ(rasa_check_auth(64496, "AS-OTHER", &result), 0);
    ASSERT_EQ(result.authorized, 0);
    rasa_free_config(&cfg);
    clean_temp(path);
}


/* Test 11-20: Multiple ASNs and assets */

/* ========== Batch 2: Tests 11-20 ========== */

static void test_rasa_auth_multiple_asns(void) {
    struct rasa_config cfg = {0};
    struct rasa_auth result = {0};
    const char *json = "{\"rasas\":[{\"rasa\":{\"authorized_as\":64496,\"authorized_in\":[{\"entry\":{\"asset\":\"AS-SHARED\"}}]}},{\"rasa\":{\"authorized_as\":64497,\"authorized_in\":[{\"entry\":{\"asset\":\"AS-SHARED\"}}]}}]}";
    char *path = make_temp(json);
    ASSERT(path);
    rasa_load_config(&cfg, path);
    ASSERT_EQ(rasa_check_auth(64496, "AS-SHARED", &result), 0);
    ASSERT_EQ(result.authorized, 1);
    ASSERT_EQ(rasa_check_auth(64497, "AS-SHARED", &result), 0);
    ASSERT_EQ(result.authorized, 1);
    rasa_free_config(&cfg);
    clean_temp(path);
}

static void test_rasa_auth_multiple_assets_single_asn(void) {
    struct rasa_config cfg = {0};
    struct rasa_auth result = {0};
    const char *json = "{\"rasas\":[{\"rasa\":{\"authorized_as\":64496,\"authorized_in\":[{\"entry\":{\"asset\":\"AS-TEST1\"}},{\"entry\":{\"asset\":\"AS-TEST2\"}},{\"entry\":{\"asset\":\"AS-TEST3\"}}]}}]}";
    char *path = make_temp(json);
    ASSERT(path);
    rasa_load_config(&cfg, path);
    ASSERT_EQ(rasa_check_auth(64496, "AS-TEST1", &result), 0);
    ASSERT_EQ(result.authorized, 1);
    ASSERT_EQ(rasa_check_auth(64496, "AS-TEST2", &result), 0);
    ASSERT_EQ(result.authorized, 1);
    ASSERT_EQ(rasa_check_auth(64496, "AS-TEST3", &result), 0);
    ASSERT_EQ(result.authorized, 1);
    ASSERT_EQ(rasa_check_auth(64496, "AS-TEST4", &result), 0);
    ASSERT_EQ(result.authorized, 0);
    rasa_free_config(&cfg);
    clean_temp(path);
}

static void test_rasa_auth_empty_authorized_in(void) {
    struct rasa_config cfg = {0};
    struct rasa_auth result = {0};
    const char *json = "{\"rasas\":[{\"rasa\":{\"authorized_as\":64496,\"authorized_in\":[]}}]}";
    char *path = make_temp(json);
    ASSERT(path);
    rasa_load_config(&cfg, path);
    ASSERT_EQ(rasa_check_auth(64496, "AS-TEST", &result), 0);
    ASSERT_EQ(result.authorized, 0);
    rasa_free_config(&cfg);
    clean_temp(path);
}

static void test_rasa_auth_no_authorized_in_key(void) {
    struct rasa_config cfg = {0};
    struct rasa_auth result = {0};
    const char *json = "{\"rasas\":[{\"rasa\":{\"authorized_as\":64496}}]}";
    char *path = make_temp(json);
    ASSERT(path);
    rasa_load_config(&cfg, path);
    ASSERT_EQ(rasa_check_auth(64496, "AS-TEST", &result), 0);
    ASSERT_EQ(result.authorized, 0);
    rasa_free_config(&cfg);
    clean_temp(path);
}

static void test_rasa_auth_special_chars_in_asset(void) {
    struct rasa_config cfg = {0};
    struct rasa_auth result = {0};
    const char *json = "{\"rasas\":[{\"rasa\":{\"authorized_as\":64496,\"authorized_in\":[{\"entry\":{\"asset\":\"AS2914:AS-GLOBAL\"}}]}}]}";
    char *path = make_temp(json);
    ASSERT(path);
    rasa_load_config(&cfg, path);
    ASSERT_EQ(rasa_check_auth(64496, "AS2914:AS-GLOBAL", &result), 0);
    ASSERT_EQ(result.authorized, 1);
    rasa_free_config(&cfg);
    clean_temp(path);
}

static void test_rasa_auth_32bit_asn(void) {
    struct rasa_config cfg = {0};
    struct rasa_auth result = {0};
    const char *json = "{\"rasas\":[{\"rasa\":{\"authorized_as\":4200000000,\"authorized_in\":[{\"entry\":{\"asset\":\"AS-TEST\"}}]}}]}";
    char *path = make_temp(json);
    ASSERT(path);

    printf("nBatch 2: More RASA-AUTH testsn");
    RUN_TEST(rasa_auth_multiple_asns);
    RUN_TEST(rasa_auth_multiple_assets_single_asn);
    RUN_TEST(rasa_auth_empty_authorized_in);
    RUN_TEST(rasa_auth_no_authorized_in_key);
    RUN_TEST(rasa_auth_special_chars_in_asset);
    RUN_TEST(rasa_auth_32bit_asn);
    RUN_TEST(rasa_auth_asn_zero);
    RUN_TEST(rasa_auth_large_asn_16bit_max);
    RUN_TEST(rasa_auth_large_asn_16bit_plus_one);
    RUN_TEST(rasa_auth_duplicate_entries);
    rasa_load_config(&cfg, path);
    ASSERT_EQ(rasa_check_auth(4200000000U, "AS-TEST", &result), 0);
    ASSERT_EQ(result.authorized, 1);
    rasa_free_config(&cfg);
    clean_temp(path);
}

static void test_rasa_auth_asn_zero(void) {
    struct rasa_config cfg = {0};
    struct rasa_auth result = {0};
    const char *json = "{\"rasas\":[{\"rasa\":{\"authorized_as\":0,\"authorized_in\":[{\"entry\":{\"asset\":\"AS-TEST\"}}]}}]}";
    char *path = make_temp(json);
    ASSERT(path);
    rasa_load_config(&cfg, path);
    ASSERT_EQ(rasa_check_auth(0, "AS-TEST", &result), 0);
    ASSERT_EQ(result.authorized, 1);
    rasa_free_config(&cfg);
    clean_temp(path);
}

static void test_rasa_auth_large_asn_16bit_max(void) {
    struct rasa_config cfg = {0};
    struct rasa_auth result = {0};
    const char *json = "{\"rasas\":[{\"rasa\":{\"authorized_as\":65535,\"authorized_in\":[{\"entry\":{\"asset\":\"AS-TEST\"}}]}}]}";
    char *path = make_temp(json);
    ASSERT(path);
    rasa_load_config(&cfg, path);
    ASSERT_EQ(rasa_check_auth(65535, "AS-TEST", &result), 0);
    ASSERT_EQ(result.authorized, 1);
    rasa_free_config(&cfg);
    clean_temp(path);
}

static void test_rasa_auth_large_asn_16bit_plus_one(void) {
    struct rasa_config cfg = {0};
    struct rasa_auth result = {0};
    const char *json = "{\"rasas\":[{\"rasa\":{\"authorized_as\":65536,\"authorized_in\":[{\"entry\":{\"asset\":\"AS-TEST\"}}]}}]}";
    char *path = make_temp(json);
    ASSERT(path);
    rasa_load_config(&cfg, path);
    ASSERT_EQ(rasa_check_auth(65536, "AS-TEST", &result), 0);
    ASSERT_EQ(result.authorized, 1);
    rasa_free_config(&cfg);
    clean_temp(path);
}

static void test_rasa_auth_duplicate_entries(void) {
    struct rasa_config cfg = {0};
    struct rasa_auth result = {0};
    const char *json = "{\"rasas\":[{\"rasa\":{\"authorized_as\":64496,\"authorized_in\":[{\"entry\":{\"asset\":\"AS-TEST\"}},{\"entry\":{\"asset\":\"AS-TEST\"}}]}}]}";
    char *path = make_temp(json);
    ASSERT(path);
    rasa_load_config(&cfg, path);
    ASSERT_EQ(rasa_check_auth(64496, "AS-TEST", &result), 0);
    ASSERT_EQ(result.authorized, 1);
    rasa_free_config(&cfg);
    clean_temp(path);
}


