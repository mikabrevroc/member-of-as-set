# RASA Data Flow and Logic Documentation

## Overview
This document explains how data flows through the RASA system from RPKI objects to AS-SET filtering decisions.

---

## Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         RPKI OBJECT CREATION                                 │
│  Operator creates RASA-SET or RASA-AUTH, signs with RPKI certificate        │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         RPKI REPOSITORY PUBLICATION                          │
│  Objects published to RPKI repository (rsync/RRDP)                          │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                     rpki-client VALIDATION                             │  │
│  │  1. Download RASA objects from RPKI repositories                       │  │
│  │  2. Validate CMS signatures (RFC 6488)                                 │  │
│  │  3. Validate certificate chains                                        │  │
│  │  4. Parse ASN.1 content (RasaSetContent / RasaAuthContent)            │  │
│  │  5. Verify: signing cert ASID matches containingAS/authorizedAS       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                      │                                       │
│                                      ▼                                       │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                     rpki-client JSON OUTPUT                            │  │
│  │  Produces JSON file with validated RASA data:                          │  │
│  │  - rasas[]: Array of RASA-AUTH objects                                 │  │
│  │  - rasa_sets[]: Array of RASA-SET objects                              │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                     bgpq4 RASA LIBRARY                                 │  │
│  │  1. Load JSON file via rasa_load_config() / rasa_set_load_config()    │  │
│  │  2. Parse and validate JSON structure                                  │  │
│  │  3. Build in-memory lookup structures                                  │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                      │                                       │
│                                      ▼                                       │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                     bgpq4 AS-SET EXPANSION                             │  │
│  │  expander.c calls RASA functions during IRR queries:                   │  │
│  │                                                                        │  │
│  │  For each AS-SET to expand:                                            │  │
│  │    1. Lookup RASA-SET by name                                          │  │
│  │    2. IF found:                                                        │  │
│  │         - Apply fallbackMode logic (irrLock/irrFallback/rasaOnly)     │  │
│  │         - Expand nestedSets recursively                                │  │
│  │         - Query IRR if needed (respecting irrSource lock)             │  │
│  │    3. IF NOT found:                                                    │  │
│  │         - Query IRR normally (legacy behavior)                         │  │
│  │                                                                        │  │
│  │  For each member ASN:                                                  │  │
│  │    1. Check RASA-AUTH authorization (bidirectional verification)      │  │
│  │    2. Filter unauthorized ASNs                                         │  │
│  │    3. Query route objects for authorized ASNs                          │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ROUTER CONFIGURATION OUTPUT                          │
│  Generate prefix-lists, as-path filters based on verified AS-SET members    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## ASN.1 Data Structures

### RASA-SET (RasaSetContent)
```asn1
RasaSetContent ::= SEQUENCE {
  version          [0] INTEGER DEFAULT 0,           -- Format version
  asSetName            UTF8String,                  -- AS-SET name (e.g., "AS2914:AS-GLOBAL")
  containingAS         ASID,                        -- Owning ASN
  members              SEQUENCE OF ASID,            -- Direct member ASNs
  nestedSets           SEQUENCE OF UTF8String OPTIONAL,  -- Nested AS-SET names
  irrSource            UTF8String OPTIONAL,         -- Authoritative IRR database
  fallbackMode         FallbackMode DEFAULT irrFallback,  -- IRR handling mode
  flags                RasaFlags OPTIONAL,          -- doNotInherit, authoritative
  notBefore            GeneralizedTime,             -- Validity start
  notAfter             GeneralizedTime              -- Validity end
}
```

### RASA-AUTH (RasaAuthContent)
```asn1
RasaAuthContent ::= SEQUENCE {
  version          [0] INTEGER DEFAULT 0,           -- Format version
  authorizedAS     [1] ASID OPTIONAL,               -- ASN authorizing inclusion
  authorizedSet    [2] UTF8String OPTIONAL,         -- OR AS-SET authorizing inclusion
  authorizedIn         SEQUENCE OF AuthorizedEntry, -- AS-SETs authorized for
  flags                RasaAuthFlags OPTIONAL,      -- strictMode
  notBefore            GeneralizedTime,             -- Validity start
  notAfter             GeneralizedTime              -- Validity end
}
```

### Supporting Types
```asn1
-- Fallback mode for RASA-SET
FallbackMode ::= ENUMERATED {
    irrFallback(0),    -- Merge RASA members with IRR query (default)
    irrLock(1),        -- Lock to specific IRR database only
    rasaOnly(2)        -- Use only RASA data, ignore IRR
}

-- Entry in authorizedIn with propagation scope
AuthorizedEntry ::= SEQUENCE {
    asSetName        UTF8String,                  -- AS-SET name
    propagation      PropagationScope OPTIONAL    -- Scope constraint
}

-- Propagation scope (for peer locking)
PropagationScope ::= ENUMERATED {
    unrestricted(0),   -- Can be nested anywhere (default)
    directOnly(1)      -- Only direct inclusion (peer lock signal)
}

-- RASA-SET flags
RasaFlags ::= BIT STRING {
    doNotInherit(0),   -- Prevent transitive inclusion
    authoritative(1)   -- RASA-SET replaces IRR data
}

-- RASA-AUTH flags
RasaAuthFlags ::= BIT STRING {
    strictMode(0)      -- Reject if not in authorizedIn
}
```

---

## fallbackMode Logic

### Mode 1: irrFallback(0) - DEFAULT
**Purpose**: Supplement IRR data with RASA, gradual migration

**Logic**:
```python
def expand_irr_fallback(asset_name, rasa_set):
    # Get RASA members (if any)
    rasa_members = rasa_set.members if rasa_set else []
    
    # Get nested set members (recursively expanded)
    nested_members = []
    for nested in rasa_set.nested_sets:
        nested_members += expand_asset(nested)
    
    # Query IRR
    irr_members = query_irr(asset_name)
    
    # Merge all sources (deduplicate)
    return unique(rasa_members + nested_members + irr_members)
```

**Use Case**: AS64496 has some customers in RASA, others still only in IRR

---

### Mode 2: irrLock(1) - IRR DATABASE LOCK
**Purpose**: Cryptographically lock which IRR database is authoritative

**Validation Rules**:
- MUST have empty `members` sequence
- MUST have `irrSource` field present
- MUST NOT have nestedSets (or must be empty)

**Logic**:
```python
def expand_irr_lock(asset_name, rasa_set):
    assert rasa_set.fallback_mode == IRR_LOCK
    assert rasa_set.members is None or len(rasa_set.members) == 0
    assert rasa_set.irr_source is not None
    
    # Query ONLY the locked IRR database
    return query_irr(asset_name, source=rasa_set.irr_source)
```

**Use Case**: AS2914 wants to ensure AS2914:AS-GLOBAL only comes from RADB, reject RIPE/ARIN versions

**Example**:
```asn1
RasaSetContent {
  asSetName: "AS2914:AS-GLOBAL",
  containingAS: 2914,
  members: [],              -- EMPTY!
  irrSource: "RADB",
  fallbackMode: irrLock     -- Lock mode
}
```

---

### Mode 3: rasaOnly(2) - RASA REPLACEMENT
**Purpose**: Replace IRR entirely with RASA

**Validation Rules**:
- MUST have non-empty `members` sequence
- No IRR query performed

**Logic**:
```python
def expand_rasa_only(asset_name, rasa_set):
    assert rasa_set.fallback_mode == RASA_ONLY
    assert rasa_set.members is not None and len(rasa_set.members) > 0
    
    # Get direct members
    members = list(rasa_set.members)
    
    # Recursively expand nested sets
    for nested in rasa_set.nested_sets:
        members += expand_asset(nested)
    
    # NO IRR QUERY
    return unique(members)
```

**Use Case**: New network with no IRR legacy, pure RASA deployment

---

## Bidirectional Verification

### Concept
For complete security, both sides must agree:
1. **RASA-SET**: AS-SET owner declares "AS64496 is in my set"
2. **RASA-AUTH**: AS64496 declares "I authorize being in this AS-SET"

### Verification Logic
```python
def verify_bidirectional(asset_name, asn):
    # Check RASA-SET side
    set_result = rasa_check_set_membership(asset_name, asn)
    # Returns: is_member (bool), reason (string)
    
    # Check RASA-AUTH side
    auth_result = rasa_check_auth(asn, asset_name)
    # Returns: authorized (bool), reason (string)
    
    # Both must be true for authorization
    if set_result.is_member and auth_result.authorized:
        return True, "Bidirectionally verified"
    elif not set_result.is_member:
        return False, f"AS-SET does not declare membership: {set_result.reason}"
    else:
        return False, f"AS does not authorize inclusion: {auth_result.reason}"
```

### Strict Mode
If RASA-AUTH has `strictMode` flag set:
```python
if strictMode and not authorized:
    # Hard reject (not just warning)
    raise AuthorizationError("Strict mode: unauthorized AS-SET inclusion rejected")
```

---

## Nested Set Expansion

### Recursive Algorithm
```python
def expand_rasa_set(asset_name, visited=None):
    if visited is None:
        visited = set()
    
    # Prevent infinite loops
    if asset_name in visited:
        return []  # Circular reference detected
    visited.add(asset_name)
    
    # Lookup RASA-SET
    rasa_set = lookup_rasa_set(asset_name)
    if not rasa_set:
        # Fall back to IRR
        return query_irr(asset_name)
    
    members = []
    
    # Add direct members
    members.extend(rasa_set.members)
    
    # Recursively expand nested sets
    for nested in rasa_set.nested_sets:
        members.extend(expand_rasa_set(nested, visited))
    
    return unique(members)
```

### doNotInherit Flag
If a RASA-SET has `doNotInherit` flag:
```python
if rasa_set.flags.doNotInherit:
    # Do NOT include this set's members when it's nested
    # Only include when directly referenced
    return []
```

---

## JSON Format (rpki-client → bgpq4)

### RASA-AUTH JSON
```json
{
  "rasas": [
    {
      "rasa": {
        "version": 0,
        "authorized_as": 64496,
        "authorized_set": null,
        "authorized_in": [
          {
            "asset": "AS-TEST",
            "propagation": 0
          }
        ],
        "flags": [],
        "not_before": "2024-01-01T00:00:00Z",
        "not_after": "2025-01-01T00:00:00Z"
      }
    }
  ]
}
```

### RASA-SET JSON
```json
{
  "rasa_sets": [
    {
      "rasa_set": {
        "version": 0,
        "as_set_name": "AS2914:AS-GLOBAL",
        "containing_as": 2914,
        "members": [64496, 65001],
        "nested_sets": ["AS-CHILD"],
        "irr_source": "RADB",
        "fallback_mode": "irrLock",
        "flags": [],
        "not_before": "2024-01-01T00:00:00Z",
        "not_after": "2025-01-01T00:00:00Z"
      }
    }
  ]
}
```

---

## Complete Example: AS2914 IRR Lock

### Step 1: Create RASA-SET
```asn1
-- AS2914 publishes this to RPKI
RasaSetContent {
  version: 0,
  asSetName: "AS2914:AS-GLOBAL",
  containingAS: 2914,
  members: [],              -- Empty for lock-only mode
  nestedSets: [],
  irrSource: "RADB",        -- Lock to RADB only
  fallbackMode: irrLock(1),
  flags: {},
  notBefore: 2024-01-01T00:00:00Z,
  notAfter: 2025-01-01T00:00:00Z
}
```

### Step 2: rpki-client Validation
```bash
rpki-client processes the CMS-signed object:
1. Validates signature with AS2914's RPKI certificate
2. Parses ASN.1 content
3. Extracts all fields including fallbackMode=irrLock
4. Outputs to JSON
```

### Step 3: JSON Output
```json
{
  "rasa_sets": [
    {
      "rasa_set": {
        "as_set_name": "AS2914:AS-GLOBAL",
        "containing_as": 2914,
        "members": [],
        "irr_source": "RADB",
        "fallback_mode": "irrLock"
      }
    }
  ]
}
```

### Step 4: bgpq4 Processing
```bash
bgpq4 -Y -y rasa-output.json -Jl filter AS2914:AS-GLOBAL
```

**Internal Logic**:
```python
rasa_set = lookup_rasa_set("AS2914:AS-GLOBAL")
if rasa_set and rasa_set.fallback_mode == "irrLock":
    # Query ONLY RADB
    members = query_irr("AS2914:AS-GLOBAL", source="RADB")
else:
    # Query all IRR databases
    members = query_irr("AS2914:AS-GLOBAL")
```

### Step 5: Result
- If AS2914:AS-GLOBAL in RADB: Members returned ✓
- If AS2914:AS-GLOBAL in RIPE: Rejected ✗
- Cryptographic assurance of data source ✓

---

## Error Handling

### ASN.1 Parsing Errors
| Error | Cause | Action |
|-------|-------|--------|
| Invalid version | Unknown version number | Reject object |
| Missing required field | Schema violation | Reject object |
| Invalid ASID | Out of range (0-4294967295) | Reject object |
| Both authorizedAS and authorizedSet | Schema violation | Reject object |
| Invalid fallbackMode | Unknown enum value | Reject object |
| irrLock with non-empty members | Validation rule violation | Reject object |

### JSON Parsing Errors
| Error | Cause | Action |
|-------|-------|--------|
| Invalid JSON format | Syntax error | Log error, skip file |
| Missing required field | Schema mismatch | Log warning, use defaults |
| Unknown fallback_mode | Forward compatibility | Default to irrFallback |

### Runtime Errors
| Error | Cause | Action |
|-------|-------|--------|
| RASA-SET not found | No published object | Fall back to IRR query |
| IRR database unreachable | Network error | Log error, use cached data |
| Expired RASA object | notAfter passed | Reject object |
| Signature invalid | Certificate issue | Reject object |

---

## Security Considerations

### Threat Model
1. **IRR Database Compromise**: Attacker modifies AS-SET in IRR
   - **Mitigation**: RASA signature validates authoritative source
   
2. **RPKI Key Compromise**: Attacker publishes fake RASA objects
   - **Mitigation**: RPKI revocation, monitoring
   
3. **Namespace Collision**: Same AS-SET name on multiple databases
   - **Mitigation**: irrSource lock prevents ambiguity
   
4. **Circular References**: Nested sets reference each other
   - **Mitigation**: Visited set tracking in expansion

### Trust Boundaries
- RPKI validation ensures object authenticity
- RASA logic ensures authorization correctness
- IRR queries only when explicitly allowed

---

## Document History

- 2026-02-24: Initial data flow documentation
