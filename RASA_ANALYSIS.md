# RASA Specification Analysis

**Date**: 2025-02-24  
**Source Files**: `RASA.asn1`, `draft-carbonara-rpki-as-set-auth-04.xml`  
**Purpose**: Complete data model and validation analysis for bgpq4 implementation

---

## 1. Overview of RASA Objects

RASA defines two RPKI-signed object types:

### **RASA-SET** (RPKI AS-SET Membership Object)
- Published by the AS-SET owner (Containing Autonomous System - CAS)
- **Purpose**: Defines AS-SET membership (members + nested sets)
- **OID**: `id-rpki-rasa-set` = `{ id-rpki 42 1 }`
- **Replaces**: IRR AS-SET object when authoritatively present

### **RASA-AUTH** (RPKI AS-SET Authorization Object)
- Published by the ASN or nested AS-SET owner (Member Autonomous System - MAS)
- **Purpose**: Authorizes inclusion in specific parent AS-SETs
- **OID**: `id-rpki-rasa-auth` = `{ id-rpki 42 2 }`
- **Critical**: Provides cryptographic authorization for AS-SET membership

---

## 2. Complete Data Model

### **RASA-SET: RasaSetContent**

| Field | ASN.1 Type | Optional? | Default | Description |
|-------|------------|-----------|---------|-------------|
| `version` | `[0] INTEGER` | No | 0 | Format version (this document defines v0) |
| `asSetName` | `UTF8String` | No | N/A | AS-SET name (e.g., "AS1299:AS-TWELVE99") |
| `containingAS` | `ASID` | No | N/A | ASN of the AS-SET owner |
| `members` | `SEQUENCE OF ASID` | No | N/A | List of member ASNs (sorted, unique) |
| `nestedSets` | `SEQUENCE OF UTF8String` | Yes | N/A | List of nested AS-SET names to expand |
| `irrSource` | `UTF8String` | Yes | N/A | Authoritative IRR database (RADB, RIPE, etc.) |
| `fallbackMode` | `FallbackMode` | No | `irrFallback` | IRR interaction behavior (see Section 3) |
| `flags` | `RasaFlags` | Yes | None | Behavior flags (doNotInherit, authoritative) |
| `notBefore` | `GeneralizedTime` | No | N/A | Validity start per RPKI policies |
| `notAfter` | `GeneralizedTime` | No | N/A | Validity end per RPKI policies |

**Key Fields Explained:**

**asSetName**: MUST start with "AS-" per RFC 2622. For hierarchical names (AS1299:AS-TWELVE99), the leftmost ASN component MUST match `containingAS`.

**containingAS**: The ASN that owns and signs the AS-SET. Must match the RPKI certificate subject.

**members**: Direct AS number members. MUST be sorted ascending with no duplicates. May be empty depending on `fallbackMode`.

**nestedSets**: References to other AS-SET objects by name. Recursive expansion follows same verification rules. Must check Auth for nested set before expanding.

**fallbackMode**: Controls IRR interaction behavior (see Section 3).

**irrSource**: Optional authoritative IRR database (RADB, RIPE, etc.). Prevents namespace ambiguity attacks. Required when fallbackMode is irrLock.

**flags**:
- `doNotInherit(0)`: Prevent transitive inclusion attacks
- `authoritative(1)`: RASA-SET replaces IRR data entirely

**notBefore/notAfter**: Validity period per RPKI policies.

### **RASA-AUTH: RasaAuthContent**

| Field | ASN.1 Type | Optional? | Default | Description |
|-------|------------|-----------|---------|-------------|
| `version` | `[0] INTEGER` | No | 0 | Format version |
| `authorizedEntity` | **CHOICE** | No | N/A | Either `authorizedAS` or `authorizedSet` |
| `authorizedIn` | `SEQUENCE OF AuthorizedEntry` | No | N/A | List of parent AS-SETs that may include this entity |
| `flags` | `RasaAuthFlags` | Yes | None | strictMode flag |
| `notBefore` | `GeneralizedTime` | No | N/A | Validity start |
| `notAfter` | `GeneralizedTime` | No | N/A | Validity end |

### **Author
Error message: JSON Invalid request payload: content should be a string or a Buffer
# RASA Specification Analysis

**Date**: 2025-02-24  
**Source Files**: `RASA.asn1`, `draft-carbonara-rpki-as-set-auth-04.xml`  
**Purpose**: Complete data model and validation analysis for bgpq4 implementation

---

## 1. Overview of RASA Objects

RASA defines two RPKI-signed object types:

### **RASA-SET** (RPKI AS-SET Membership Object)
- Published by the AS-SET owner (Containing Autonomous System - CAS)
- **Purpose**: Defines AS-SET membership (members + nested sets)
- **OID**: `id-rpki-rasa-set` = `{ id-rpki 42 1 }`
- **Replaces**: IRR AS-SET object when authoritatively present

### **RASA-AUTH** (RPKI AS-SET Authorization Object)
- Published by the ASN or nested AS-SET owner (Member Autonomous System - MAS)
- **Purpose**: Authorizes inclusion in specific parent AS-SETs
- **OID**: `id-rpki-rasa-auth` = `{ id-rpki 42 2 }`
- **Critical**: Provides cryptographic authorization for AS-SET membership

---

## 2. Complete Data Model

### **RASA-SET: RasaSetContent**

| Field | ASN.1 Type | Optional? | Default | Description |
|-------|------------|-----------|---------|-------------|
| `version` | `[0] INTEGER` | No | 0 | Format version (this document defines v0) |
| `asSetName` | `UTF8String` | No | N/A | AS-SET name (e.g., "AS1299:AS-TWELVE99") |
| `containingAS` | `ASID` | No | N/A | ASN of the AS-SET owner |
| `members` | `SEQUENCE OF ASID` | No | N/A | List of member ASNs (sorted, unique) |
| `nestedSets` | `SEQUENCE OF UTF8String` | Yes | N/A | List of nested AS-SET names to expand |
| `irrSource` | `UTF8String` | Yes | N/A | Authoritative IRR database (RADB, RIPE, etc.) |
| `fallbackMode` | `FallbackMode` | No | `irrFallback` | IRR interaction behavior (see Section 3) |
| `flags` | `RasaFlags` | Yes | None | Behavior flags (doNotInherit, authoritative) |
| `notBefore` | `GeneralizedTime` | No | N/A | Validity start per RPKI policies |
| `notAfter` | `GeneralizedTime` | No | N/A | Validity end per RPKI policies |

**Key Fields Explained:**

**asSetName**: MUST start with "AS-" per RFC 2622. For hierarchical names (AS1299:AS-TWELVE99), the leftmost ASN component MUST match `containingAS`.

**containingAS**: The ASN that owns and signs the AS-SET. Must match the RPKI certificate subject.

**members**: Direct AS number members. MUST be sorted ascending with no duplicates. May be empty depending on `fallbackMode`.

**nestedSets**: References to other AS-SET objects by name. Recursive expansion follows same verification rules. Must check Auth for nested set before expanding.

**fallbackMode**: Controls IRR interaction behavior (see Section 3).

**irrSource**: Optional authoritative IRR database (RADB, RIPE, etc.). Prevents namespace ambiguity attacks. Required when fallbackMode is irrLock.

**flags**:
- `doNotInherit(0)`: Prevent transitive inclusion attacks
- `authoritative(1)`: RASA-SET replaces IRR data entirely

**notBefore/notAfter**: Validity period per RPKI policies.

### **RASA-AUTH: RasaAuthContent**

| Field | ASN.1 Type | Optional? | Default | Description |
|-------|------------|-----------|---------|-------------|
| `version` | `[0] INTEGER` | No | 0 | Format version |
| `authorizedEntity` | **CHOICE** | No | N/A | Either `authorizedAS` or `authorizedSet` |
| `authorizedIn` | `SEQUENCE OF AuthorizedEntry` | No | N/A | List of parent AS-SETs that may include this entity |
| `flags` | `RasaAuthFlags` | Yes | None | strictMode flag |
| `notBefore` | `GeneralizedTime` | No | N/A | Validity start |
| `notAfter` | `GeneralizedTime` | No | N/A | Validity end |

**CHOICE: authorizedEntity**
```asn1
CHOICE {
    authorizedAS        ASID,          -- Individual ASN authorization
    authorizedSet       UTF8String     -- AS-SET name authorization
}
```

**Critical Note**: Must use explicit tags in implementation to avoid CHOICE type issues with OpenSSL. ASN.1 shows untagged, but text says "Using explicit tags to avoid CHOICE type (simpler OpenSSL integration)".

### **AuthorizedEntry Structure**

| Field | ASN.1 Type | Optional? | Default | Description |
|-------|------------|-----------|---------|-------------|
| `asSetName` | `UTF8String` | No | N/A | Parent AS-SET name |
| `propagation` | `PropagationScope` | Yes | `unrestricted(0)` | BGP import policy signal |

**Field**: `asSetName` - The AS-SET name that is authorized to include this ASN/AS-SET. An empty `authorizedIn` sequence means the entity refuses inclusion in any AS-SET.

**Field**: `propagation` - Semantics:
- `unrestricted(0)`: Default. No special BGP import policy semantics.
- `directOnly(1)`: Advisory signal to containing AS - only accept routes with this ASN from direct BGP sessions (peer lock). Does NOT affect AS-SET expansion, only provides BGP import policy hint for route servers.

### **Flag Definitions**

#### **RasaFlags (RASA-SET)**
```asn1
BIT STRING {
    doNotInherit(0),   -- Prevent transitive inclusion
    authoritative(1)   -- RASA replaces IRR data entirely
}
```

**doNotInherit(0)**: When set to TRUE, prevents transitive inclusion attacks. If AS-SET A includes AS-SET B, and B has doNotInherit set, then A gets B's reference, NOT B's members. Used by content providers to prevent their AS-SETs from being hijacked in transitive chains.

**authoritative(1)**: When set to TRUE, indicates RASA-SET completely replaces IRR AS-SET. Tools MUST ignore IRR data for this AS-SET and use only RASA members. Treats IRR object as deprecated/non-authoritative.

#### **RasaAuthFlags (RASA-AUTH)**
```asn1
BIT STRING {
    strictMode(0)  -- Reject unauthorized inclusion (vs warn)
}
```

**strictMode(0)**: When TRUE, unauthorized inclusion is a security violation (reject + log security event). When FALSE (default), unauthorized inclusion logs a warning but still excludes the ASN.

### **FallbackMode ENUMERATED**

| Value | Name | Description |
|-------|------|-------------|
| 0 | `irrFallback` | Default; merge RASA members with IRR query results |
| 1 | `irrLock` | Lock to specific IRR database only |
| 2 | `rasaOnly` | Use only RASA data, ignore IRR entirely |

---
