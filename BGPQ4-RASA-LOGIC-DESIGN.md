# bgpq4 RASA Integration Logic Design

## Overview

This document specifies the complete decision logic for bgpq4 RASA integration, addressing the gaps between the current implementation and the specification requirements.

## Data Structures

### Current (Broken) Approach
```c
// Single global RASA-SET config
struct rasa_set_config {
    int fallback_mode;    // One mode for all AS-SETs
    char *irr_source;     // One source for all AS-SETs
};
```

### Required Approach
```c
// Per-AS-SET RASA-SET lookup table
struct rasa_set_entry {
    char *as_set_name;           // Key: "AS2914:AS-GLOBAL"
    int fallback_mode;           // Mode for this specific AS-SET
    char *irr_source;            // Lock target (for irrLock)
    uint32_t *members;           // Direct member ASNs
    size_t num_members;
    char **nested_sets;          // Nested AS-SET names
    size_t num_nested;
    uint32_t containing_as;      // Owning ASN
};

// Hash table for O(1) lookup by AS-SET name
struct rasa_set_table {
    struct rasa_set_entry **entries;
    size_t count;
    size_t capacity;
};
```

## Decision Flow Diagram

```
Expand AS-SET "AS2914:AS-GLOBAL"
        |
        v
+-----------------------------------+
| Lookup RASA-SET by name           |
| rasa_set_table_lookup(asset)      |
+-----------------------------------+
        |
        +------------+------------+
        |                         |
   [Found]                    [Not Found]
        |                         |
        v                         v
+---------------+       +-------------------+
| Get fallback  |       | Traditional IRR   |
| mode          |       | expansion         |
+---------------+       | (existing bgpq4   |
        |               | behavior)         |
        v               +-------------------+
+-----------------------------------+
| Switch on fallback_mode:          |
+-----------------------------------+
        |
        +--------+-----------+-----------+
        |        |           |           |
   irrLock  rasaOnly   irrFallback  (default)
        |        |           |
        v        v           v
```

### irrLock Mode (Mode 1)

**Purpose**: Lock AS-SET to specific IRR database

```c
if (rasa_set->fallback_mode == RASA_FALLBACK_MODE_IRR_LOCK) {
    // Validation: irr_source MUST be specified
    if (!rasa_set->irr_source || strlen(rasa_set->irr_source) == 0) {
        sx_report(SX_ERROR, "RASA-SET %s has irrLock mode but no irr_source\n", asset);
        return 0;  // Fail expansion
    }
    
    // Validation: members should be empty (pure lock)
    if (rasa_set->num_members > 0) {
        sx_report(SX_WARN, "RASA-SET %s irrLock mode has %zu members (should be empty)\n",
                  asset, rasa_set->num_members);
        // Continue but warn
    }
    
    // Lock IRR query to specified source
    char *locked_source = rasa_set->irr_source;
    
    // Query ONLY the locked database
    bgpq_pipeline(b, NULL, NULL, "!s%s\n", locked_source);
    bgpq_pipeline(b, bgpq_expanded_macro_limit, NULL, "!i%s\n", asset);
    
    // CRITICAL: Also check if nested sets have compatible modes
    for (i = 0; i < rasa_set->num_nested; i++) {
        char *nested = rasa_set->nested_sets[i];
        struct rasa_set_entry *nested_rasa = rasa_set_table_lookup(nested);
        
        if (nested_rasa && nested_rasa->fallback_mode == RASA_FALLBACK_MODE_IRR_LOCK) {
            if (strcmp(nested_rasa->irr_source, locked_source) != 0) {
                sx_report(SX_ERROR, 
                    "RASA-SET %s locked to %s but nested %s locked to %s\n",
                    asset, locked_source, nested, nested_rasa->irr_source);
                // Conflict resolution: use parent's lock
            }
        }
    }
}
```

**Example**: AS2914:AS-GLOBAL with irrLock to RADB
- Query only RADB for AS2914:AS-GLOBAL
- If object doesn't exist in RADB: error
- If nested AS-SETs have different locks: conflict resolution needed

### rasaOnly Mode (Mode 2)

**Purpose**: Use only RASA data, ignore IRR entirely

```c
if (rasa_set->fallback_mode == RASA_FALLBACK_MODE_RASA_ONLY) {
    // Validation: members MUST be specified
    if (rasa_set->num_members == 0 && rasa_set->num_nested == 0) {
        sx_report(SX_ERROR, "RASA-SET %s has rasaOnly mode but no members\n", asset);
        return 0;  // Fail expansion - would produce empty result
    }
    
    // Add direct members
    for (i = 0; i < rasa_set->num_members; i++) {
        uint32_t member_asn = rasa_set->members[i];
        
        // RASA-AUTH validation: check if AS authorizes membership
        struct rasa_auth auth_result;
        if (rasa_check_auth(member_asn, asset, &auth_result) == 0) {
            if (!auth_result.authorized) {
                sx_report(SX_WARN, "AS%u in RASA-SET %s not authorized: %s\n",
                         member_asn, asset, auth_result.reason);
                // Policy decision: include anyway or skip?
                // Conservative: skip unauthorized ASes
                continue;
            }
        }
        
        char as_str[32];
        snprintf(as_str, sizeof(as_str), "AS%u", member_asn);
        bgpq_expander_add_as(b, as_str);
    }
    
    // Recursively expand nested sets
    for (i = 0; i < rasa_set->num_nested; i++) {
        char *nested = rasa_set->nested_sets[i];
        
        // Recurse - nested set might have different mode
        // This creates mode propagation issues!
        expand_with_rasa(b, nested, depth + 1);
    }
    
    // DO NOT query IRR
    return 0;  // Done - no IRR query
}
```

**Mode Propagation Question**: What if nested AS-SET has different mode?

```
AS2914:AS-GLOBAL (rasaOnly)
  |
  +-- AS2914:AS-CUSTOMERS (irrLock to RIPE)
```

Options:
1. **Parent Wins**: Nested set uses parent's mode (rasaOnly)
2. **Child Override**: Nested set uses its own mode (irrLock)
3. **Error**: Incompatible modes, fail expansion
4. **Documented Default**: Spec says "doNotInherit" flag controls this

### irrFallback Mode (Mode 0, Default)

**Purpose**: Merge RASA and IRR data

```c
if (rasa_set->fallback_mode == RASA_FALLBACK_MODE_IRR_FALLBACK) {
    // Step 1: Add RASA members (with RASA-AUTH validation)
    for (i = 0; i < rasa_set->num_members; i++) {
        uint32_t member_asn = rasa_set->members[i];
        
        // Optional RASA-AUTH check
        struct rasa_auth auth_result;
        if (b->rasa && rasa_check_auth(member_asn, asset, &auth_result) == 0) {
            if (auth_result.authorized) {
                char as_str[32];
                snprintf(as_str, sizeof(as_str), "AS%u", member_asn);
                bgpq_expander_add_as(b, as_str);
            }
        }
    }
    
    // Step 2: Expand nested sets from RASA
    for (i = 0; i < rasa_set->num_nested; i++) {
        char *nested = rasa_set->nested_sets[i];
        expand_with_rasa(b, nested, depth + 1);
    }
    
    // Step 3: ALSO query IRR and merge results
    // Query all configured IRR sources
    bgpq_pipeline(b, bgpq_expanded_macro_limit, NULL, "!i%s\n", asset);
    
    // Merge: IRR results add to same asnlist (automatic dedup via RB tree)
}
```

**Conflict Resolution**: Same AS in both RASA and IRR
- IRR result: AS2914
- RASA result: AS2914
- **Resolution**: RB tree deduplicates automatically (no duplicate entries)

## State Management During Expansion

### Problem: Nested AS-SETs with Different Modes

When expanding nested AS-SETs, the mode can change:

```
Expanding: AS-MEGA-CUSTOMER (irrFallback)
  |
  +-- AS2914:AS-GLOBAL (irrLock to RADB)
  |     |
  |     +-- AS1234 (from RADB only)
  |
  +-- AS-OTHER (rasaOnly)
        |
        +-- AS5678 (from RASA only)
```

**Solution**: Mode stack during recursion

```c
struct expansion_frame {
    char *asset;
    int fallback_mode;
    char *irr_source;  // Current locked source (if any)
    struct expansion_frame *parent;
};

static __thread struct expansion_frame *current_frame = NULL;

void expand_with_rasa(struct bgpq_expander *b, char *asset, int depth) {
    struct rasa_set_entry *rasa = rasa_set_table_lookup(asset);
    
    // Create new frame
    struct expansion_frame frame = {
        .asset = asset,
        .fallback_mode = rasa ? rasa->fallback_mode : RASA_FALLBACK_MODE_IRR_FALLBACK,
        .irr_source = rasa && rasa->irr_source ? strdup(rasa->irr_source) : NULL,
        .parent = current_frame
    };
    
    // Handle mode inheritance
    if (current_frame && current_frame->fallback_mode == RASA_FALLBACK_MODE_IRR_LOCK) {
        // Parent is locked - do we inherit?
        if (frame.fallback_mode != RASA_FALLBACK_MODE_RASA_ONLY) {
            // Inherit parent's lock unless explicitly rasaOnly
            frame.fallback_mode = RASA_FALLBACK_MODE_IRR_LOCK;
            frame.irr_source = strdup(current_frame->irr_source);
        }
    }
    
    current_frame = &frame;
    
    // ... do expansion based on frame.fallback_mode ...
    
    // Restore parent frame
    current_frame = frame.parent;
    if (frame.irr_source) free(frame.irr_source);
}
```

## Data Loading and Initialization

### Current Problem

bgpq4 loads RASA data from single JSON file. But rpki-client outputs multiple files/objects.

### Required Approach

```c
// Load RASA-SET data from JSON array
int rasa_set_load_json_array(struct rasa_set_table *table, json_t *root) {
    json_t *rasa_sets = json_object_get(root, "rasa_sets");
    if (!json_is_array(rasa_sets)) return -1;
    
    size_t i;
    for (i = 0; i < json_array_size(rasa_sets); i++) {
        json_t *entry = json_array_get(rasa_sets, i);
        json_t *rasa_set = json_object_get(entry, "rasa_set");
        
        struct rasa_set_entry *new_entry = calloc(1, sizeof(*new_entry));
        
        // Parse fields
        json_t *name = json_object_get(rasa_set, "as_set_name");
        new_entry->as_set_name = strdup(json_string_value(name));
        
        json_t *mode = json_object_get(rasa_set, "fallback_mode");
        if (json_is_string(mode)) {
            const char *mode_str = json_string_value(mode);
            if (strcmp(mode_str, "irrLock") == 0)
                new_entry->fallback_mode = RASA_FALLBACK_MODE_IRR_LOCK;
            else if (strcmp(mode_str, "rasaOnly") == 0)
                new_entry->fallback_mode = RASA_FALLBACK_MODE_RASA_ONLY;
            else
                new_entry->fallback_mode = RASA_FALLBACK_MODE_IRR_FALLBACK;
        }
        
        // Parse irr_source, members, nested_sets...
        
        // Insert into hash table
        rasa_set_table_insert(table, new_entry);
    }
    
    return 0;
}
```

## Test Cases Required

### irrLock Tests

```c
// Test 1: Basic irrLock
Input: {
    "as_set_name": "AS2914:AS-GLOBAL",
    "fallback_mode": "irrLock",
    "irr_source": "RADB",
    "members": [],
    "nested_sets": []
}
IRR: {
    "RADB": ["AS2914:AS-GLOBAL" contains AS1234, AS5678],
    "RIPE": ["AS2914:AS-GLOBAL" contains AS9999]
}
Expected: AS1234, AS5678 (from RADB only, not RIPE)

// Test 2: irrLock with missing source
Input: {
    "as_set_name": "AS2914:AS-GLOBAL",
    "fallback_mode": "irrLock"
    // NO irr_source!
}
Expected: Error - irrLock requires irr_source

// Test 3: Nested irrLock conflict
Parent: "AS-MEGA" (irrLock to RADB)
  Nested: "AS2914:AS-GLOBAL" (irrLock to RIPE)
Expected: Conflict warning, use parent's lock (RADB)
```

### rasaOnly Tests

```c
// Test 4: Basic rasaOnly
Input: {
    "as_set_name": "AS-TEST",
    "fallback_mode": "rasaOnly",
    "members": [1234, 5678],
    "nested_sets": []
}
IRR: ["AS-TEST" contains AS9999]
Expected: AS1234, AS5678 (from RASA, ignore IRR)

// Test 5: rasaOnly with empty members
Input: {
    "as_set_name": "AS-EMPTY",
    "fallback_mode": "rasaOnly",
    "members": []
}
Expected: Error - would produce empty result

// Test 6: rasaOnly with nested sets
Input: {
    "as_set_name": "AS-PARENT",
    "fallback_mode": "rasaOnly",
    "members": [1111],
    "nested_sets": ["AS-CHILD"]
}
Child: {
    "as_set_name": "AS-CHILD",
    "fallback_mode": "rasaOnly",
    "members": [2222]
}
Expected: AS1111, AS2222
```

### irrFallback Tests

```c
// Test 7: Merge RASA and IRR
Input: {
    "as_set_name": "AS-TEST",
    "fallback_mode": "irrFallback",
    "members": [1234],
    "nested_sets": []
}
IRR: ["AS-TEST" contains AS5678]
Expected: AS1234 (RASA), AS5678 (IRR) - both included

// Test 8: RASA-AUTH validation in irrFallback
Input: {
    "as_set_name": "AS-TEST",
    "fallback_mode": "irrFallback",
    "members": [1234]  // AS1234 in RASA-SET
}
RASA-AUTH: AS1234 does NOT authorize AS-TEST
IRR: AS5678 in AS-TEST
Expected: AS5678 only (AS1234 rejected by RASA-AUTH)
```

## Implementation Priority

1. **CRITICAL**: Fix RASA-SET lookup - use hash table by AS-SET name
2. **HIGH**: Implement mode-specific expansion logic
3. **HIGH**: Add RASA member processing for rasaOnly mode
4. **MEDIUM**: Implement mode inheritance for nested sets
5. **MEDIUM**: Add comprehensive error handling
6. **LOW**: Add debug logging for RASA decisions

## Open Questions for User

1. **Mode inheritance**: When parent is irrLock and child is rasaOnly, what happens?
2. **Conflict resolution**: Parent locked to RADB, child locked to RIPE - error or override?
3. **RASA-AUTH strictness**: In irrFallback, if RASA-AUTH rejects an AS, should it still be included from IRR?
4. **Empty AS-SETs**: If irrLock points to database without the object, empty result or error?
5. **Circular references**: How to handle "AS-A contains AS-B contains AS-A" with RASA?
