
void test_bidirectional_only_auth(void) {
    struct rasa_config auth_cfg = {0};
    struct rasa_set_config set_cfg = {0};
    struct rasa_auth auth_result = {0};
    struct rasa_set_membership set_result = {0};
    
    rasa_verify_bidirectional("AS-TEST", 64496, &auth_result, &set_result);
}
