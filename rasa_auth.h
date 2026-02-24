#ifndef RASA_AUTH_H
#define RASA_AUTH_H

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

/* RASA-AUTH Object: Contains authorization statements from AS/AS-SET owners
 * granting permission for inclusion in specified parent AS-SETs.
 *
 * This object is published by the ASN or AS-SET owner to control inclusion
 * authorization. It is used to validate that a member ASN authorizes its
 * inclusion in a given AS-SET.
 *
 * The RASA-AUTH object is encoded using CMS (RFC5652) with eContentType:
 * id-rpki-rasa-auth OBJECT IDENTIFIER ::= { id-rpki 42 2 }
 */

/**
 * @brief RASA-AUTH object version
 * 
 * Version 0 is defined in the specification.
 * Future versions may extend the format.
 */
#define RASA_AUTH_VERSION 0

/**
 * @brief Propagation scope for peer locking
 * 
 * Used in RASA-AUTH to signal BGP import policy preferences.
 * - unrestricted (default): no special semantics
 * - directOnly: advise containing AS to only accept routes with this ASN
 *   from direct BGP sessions (peer lock signal)
 */
typedef enum {
    PROPAGATION_UNRESTRICTED = 0,
    PROPAGATION_DIRECT_ONLY  = 1
} PropagationScope;

/**
 * @brief RASA-AUTH flags
 * 
 * Optional flags controlling authorization behavior.
 * - strictMode: If set, AS-SETs NOT in this list MUST NOT include
 *   this ASN (reject rather than warn).
 */
typedef enum {
    RASA_AUTH_FLAG_STRICT_MODE = 1 << 0
} RasaAuthFlags;

/**
 * @brief Authorized entry in RASA-AUTH object
 * 
 * Each entry contains the AS-SET name and optional propagation constraint.
 * If propagation is absent, defaults to unrestricted.
 */
typedef struct {
    char* asSetName;         /**< AS-SET name (e.g., "AS1299:AS-TWELVE99") */
    PropagationScope propagation; /**< Propagation scope (default: unrestricted) */
} AuthorizedEntry;

/**
 * @brief RASA-AUTH content structure
 * 
 * The RASA-AUTH content has the following ASN.1 structure:
 * 
 * RasaAuthContent ::= SEQUENCE {
 *   version          [0] INTEGER DEFAULT 0,
 *   authorizedEntity CHOICE {
 *      authorizedAS        ASID,
 *      authorizedSet       UTF8String
 *   },
 *   authorizedIn         SEQUENCE OF AuthorizedEntry,
 *   flags                RasaAuthFlags OPTIONAL,
 *   notBefore            GeneralizedTime,
 *   notAfter             GeneralizedTime
 * }
 */
typedef struct {
    uint32_t version;                     /**< RASA-AUTH version (0) */
    bool isAuthorizedAs;                  /**< True if authorized by ASN, false if by AS-SET */
    union {
        uint32_t authorizedAS;           /**< ASN that is authorizing inclusion */
        char* authorizedSet;             /**< AS-SET name that is authorizing inclusion */
    };                                   /**< Authorized entity */
    AuthorizedEntry* authorizedIn;        /**< Array of authorized AS-SETs */
    size_t authorizedInCount;             /**< Number of authorized AS-SETs */
    RasaAuthFlags flags;                  /**< Optional flags (strictMode) */
    char* notBefore;                      /**< Validity period start (GeneralizedTime) */
    char* notAfter;                       /**< Validity period end (GeneralizedTime) */
} RasaAuthContent;

/* Function declarations */

/**
 * @brief Initialize a RASA-AUTH content structure
 * 
 * @param content Pointer to RasaAuthContent structure to initialize
 * @param version RASA-AUTH version
 * @param authorizedAS ASN authorizing inclusion (0 = not used)
 * @param authorizedSet AS-SET name authorizing inclusion (NULL = not used)
 * @param notBefore Validity start time
 * @param notAfter Validity end time
 * @return 0 on success, -1 on error
 */
int rasa_auth_init(RasaAuthContent* content, uint32_t version,
                   uint32_t authorizedAS, const char* authorizedSet,
                   const char* notBefore, const char* notAfter);

/**
 * @brief Free memory allocated by RasaAuthContent
 * 
 * @param content Pointer to RasaAuthContent structure to free
 */
void rasa_auth_free(RasaAuthContent* content);

/**
 * @brief Add an authorized AS-SET to the RASA-AUTH object
 * 
 * @param content Pointer to RasaAuthContent structure
 * @param asSetName AS-SET name to authorize
 * @param propagation Propagation scope (default: unrestricted)
 * @return 0 on success, -1 on error
 */
int rasa_auth_add_authorized_set(RasaAuthContent* content, const char* asSetName,
                                 PropagationScope propagation);

/**
 * @brief Check if an AS-SET is authorized in the RASA-AUTH object
 * 
 * @param content Pointer to RasaAuthContent structure
 * @param asSetName AS-SET name to check
 * @param strictMode If true, require exact match; if false, allow warnings
 * @return true if authorized, false otherwise
 */
bool rasa_auth_is_authorized(const RasaAuthContent* content, const char* asSetName,
                             bool strictMode);

/**
 * @brief Set strictMode flag in RASA-AUTH object
 * 
 * @param content Pointer to RasaAuthContent structure
 * @param strictMode True to enable strictMode, false to disable
 */
void rasa_auth_set_strict_mode(RasaAuthContent* content, bool strictMode);

/**
 * @brief Get the authorized entity (ASN or AS-SET name)
 * 
 * @param content Pointer to RasaAuthContent structure
 * @return Pointer to authorized entity string (ASN or AS-SET name)
 */
const char* rasa_auth_get_authorized_entity(const RasaAuthContent* content);

/**
 * @brief Validate RASA-AUTH content for conformance to specification
 * 
 * @param content Pointer to RasaAuthContent structure
 * @return true if valid, false otherwise
 */
bool rasa_auth_validate(const RasaAuthContent* content);

#endif /* RASA_AUTH_H */