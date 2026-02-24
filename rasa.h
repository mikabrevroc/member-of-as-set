#ifndef RASA_H
#define RASA_H

#include <stdbool.h>
#include <stdint.h>

/* Forward declarations */
struct rasa_config;
struct rasa_auth;
struct rasa_set_config;
struct rasa_set_membership;

/* RASA-AUTH: Configuration and authorization */
struct rasa_config {
    int enabled;
    /* Add more fields as needed */
};

struct rasa_auth {
    int authorized;
    char reason[256];
};

/* Core RASA-AUTH functions */
int rasa_load_config(struct rasa_config *cfg, const char *filename);
void rasa_free_config(struct rasa_config *cfg);
int rasa_check_auth(uint32_t asn, const char *asset, struct rasa_auth *result);

/* RASA-SET: Set configuration and membership */
struct rasa_set_config {
    int enabled;
    /* Add more fields as needed */
};

struct rasa_set_membership {
    int is_member;
    char reason[256];
};

/* Core RASA-SET functions */
int rasa_set_load_config(struct rasa_set_config *cfg, const char *filename);
void rasa_set_free_config(struct rasa_set_config *cfg);
int rasa_check_set_membership(const char *as_set_name, uint32_t asn, struct rasa_set_membership *result);

/* Bidirectional verification */
int rasa_verify_bidirectional(const char *as_set_name, uint32_t asn, struct rasa_auth *auth_result, struct rasa_set_membership *set_result);

#endif /* RASA_H */
#define RASA_H

#include <stdint.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

/* RASA-AUTH Configuration Structure */
struct rasa_config {
    int enabled;
    /* Add additional fields as needed for internal state */
};

/* RASA-AUTH Result Structure */
struct rasa_auth {
    int authorized;
    char *reason;
    /* Add additional fields for detailed authorization info */
};

/* RASA-SET Configuration Structure */
struct rasa_set_config {
    int enabled;
    /* Add additional fields for internal state */
};

/* RASA-SET Membership Result Structure */
struct rasa_set_membership {
    int is_member;
    char *reason;
    /* Add additional fields for membership info */
};

/* Function Prototypes */
int rasa_load_config(struct rasa_config *cfg, const char *filename);
void rasa_free_config(struct rasa_config *cfg);
int rasa_check_auth(uint32_t asn, const char *asset, struct rasa_auth *result);

int rasa_set_load_config(struct rasa_set_config *cfg, const char *filename);
void rasa_set_free_config(struct rasa_set_config *cfg);
int rasa_check_set_membership(const char *as_set_name, uint32_t asn, struct rasa_set_membership *result);
int rasa_verify_bidirectional(const char *as_set_name, uint32_t asn, struct rasa_auth *auth_result, struct rasa_set_membership *set_result);

#endif /* RASA_H */