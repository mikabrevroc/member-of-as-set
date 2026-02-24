# RASA Integration Test Specification

## Overview

This document specifies comprehensive test cases for RASA (RPKI AS-SET Authorization) integration in bgpq4, covering all fallback modes and edge cases.

## Test Categories

1. **irrLock Mode Tests** - Locking to specific IRR sources
2. **rasaOnly Mode Tests** - Using only RASA data, ignoring IRR
3. **irrFallback Mode Tests** - Merging RASA and IRR with proper conflict handling
4. **Edge Cases** - Error conditions, invalid data, nested sets
5. **Real-World Scenarios** - Production AS-SET patterns from major providers

## Test Case Format

Each test case includes:
- **Test ID**: Unique identifier
- **Description**: What the test verifies
- **RASA JSON**: Input RASA configuration
- **IRR State**: Simulated IRR database state
- **Expected Behavior**: What bgpq4 should do
- **Expected Output**: Expected AS-SET expansion results

---

## 1. IRR-LOCK MODE TESTS

### 1.1 Lock to RADB Only (AS2914 Example)

**Test ID**: RASA-IRRLOCK-001  
**Description**: Verify AS2914:AS-GLOBAL locks to RADB source only

**RASA JSON**:
```json
{
  "rasa_sets": [
    {
      "rasa_set": {
        "version": 0,
        "as_set_name": "AS2914:AS-GLOBAL",
        "containing_as": 2914,
        "members": [],
        "nested_sets": [],
        "irr_source": "RADB",
        "fallback_mode": "irrLock",
        "not_before": "2024-01-01T00:00:00Z",
        "not_after": "2025-01-01T00:00:00Z"
      }
    }
  ]
}
```

**IRR State**:
- RADB: AS2914:AS-GLOBAL contains AS12345, AS67890
- RIPE: AS2914:AS-GLOBAL contains AS54321 (different AS)
- ARIN: AS2914:AS-GLOBAL contains AS98765 (different AS)

**Expected Behavior**:
- bgpq4 should ONLY query RADB for AS2914:AS-GLOBAL
- AS12345 and AS67890 should be included
- AS54321 and AS98765 should be EXCLUDED (different IRR source)
- Exit code: 0 (success)

**Expected Output** (example prefix list):
```
ip prefix-list test permit <prefixes from AS12345>
ip prefix-list test permit <prefixes from AS67890>
# NOT included: prefixes from AS54321, AS98765
```

---

### 1.2 Lock to RIPE Only

**Test ID**: RASA-IRRLOCK-002  
**Description**: Verify AS-SET locks to RIPE source only

**RASA JSON**:
```json
{
  "rasa_sets": [
    {
      "rasa_set": {
        "version": 0,
        "as_set_name": "AS-TEST-RIPE",
        "containing_as": 65000,
        "members": [65001, 65002],
        "nested_sets": [],
        "irr_source": "RIPE",
        "fallback_mode": "irrLock",
        "not_before": "2024-01-01T00:00:00Z",
        "not_after": "2025-06-01T00:00:00Z"
      }
    }
  ],
  "rasas": [
    {
      "rasa": {
        "version": 0,
        "authorized_as": 65001,
        "authorized_in": [
          {
            "asset": "AS-TEST-RIPE",
            "propagation": 0
          }
        ],
        "not_before": "2024-01-01T00:00:00Z",
        "not_after": "2025-06-01T00:00:00Z"
      }
    },
    {
      "rasa": {
        "version": 0,
        "authorized_as": 65002,
        "authorized_in": [
          {
            "asset": "AS-TEST-RIPE",
            "propagation": 0
          }
        ],
        "not_before": "2024-01-01T00:00:00Z",
        "not_after": "2025-06-01T00:00:00Z"
      }
    }
  ]
}
```

**IRR State**:
- RIPE: AS-TEST-RIPE contains AS65001, AS65002, AS65003, AS65004
- ARIN: AS-TEST-RIPE contains AS65005, AS65006 (should be ignored)
- RADB: AS-TEST-RIPE contains AS65007, AS65008 (should be ignored)

**Expected Behavior**:
- bgpq4 should ONLY query RIPE database
- Include AS65001, AS65002 (both in RASA and RIPE)
- Exclude AS65003, AS65004 (not in RASA, irrLock mode should not add them)
- Do NOT query ARIN or RADB
- RASA-AUTH should validate AS65001 and AS65002

**Expected Output**:
- Authorization for AS65001 and AS65002 passes
- No prefixes from AS65003, AS65004, AS65005, AS65006, AS65007, AS65008

---

### 1.3 AS-SET Exists in Multiple Databases

**Test ID**: RASA-IRRLOCK-003  
**Description**: Verify irrLock handles AS-SET in multiple databases correctly

**RASA JSON**:
```json
{
  "rasa_sets": [
    {
      "rasa_set": {
        "version": 0,
        "as_set_name": "AS-MULTI-DB",
        "containing_as": 65010,
        "members": [65011],
        "nested_sets": [],
        "irr_source": "ARIN",
        "fallback_mode": "irrLock",
        "not_before": "2024-01-01T00:00:00Z",
        "not_after": "2025-01-01T00:00:00Z"
      }
    }
  ],
  "rasas": [
    {
      "rasa": {
        "version": 0,
        "authorized_as": 65011,
        "authorized_in": [
          {
            "asset": "AS-MULTI-DB",
            "propagation": 0
          }
        ],
        "not_before": "2024-01-01T00:00:00Z",
        "not_after": "2025-01-01T00:00:00Z"
      }
    }
  ]
}
```

**IRR State**:
- ARIN: AS-MULTI-DB contains AS65011, AS65012
- RIPE: AS-MULTI-DB contains AS65011, AS65013, AS65014
- RADB: AS-MULTI-DB contains AS65011, AS65015, AS65016, AS65017
- APNIC: AS-MULTI-DB contains AS65011, AS65018

**Expected Behavior**:
- bgpq4 should query ONLY ARIN database (as specified in irr_source)
- Include AS65011 (in both RASA and ARIN)
- Exclude AS65012 (not in RASA, irrLock mode)
- Do NOT query RIPE, RADB, or APNIC
- Do NOT include AS65013-AS65018 from other databases

**Expected Output**:
- Only prefixes from AS65011
- Successfully validates authorization for AS65011

---

### 1.4 Error Case: No irrSource Specified

**Test ID**: RASA-IRRLOCK-004  
**Description**: Verify irrLock fails when irr_source is null/empty

**RASA JSON**:
```json
{
  "rasa_sets": [
    {
      "rasa_set": {
        "version": 0,
        "as_set_name": "AS-NO-SOURCE",
        "containing_as": 65020,
        "members": [65021, 65022],
        "nested_sets": [],
        "irr_source": null,
        "fallback_mode": "irrLock",
        "not_before": "2024-01-01T00:00:00Z",
        "not_after": "2025-01-01T00:00:00Z"
      }
    }
  ],
  "rasas": [
    {
      "rasa": {
        "version": 0,
        "authorized_as": 65021,
        "authorized_in": [
          {
            "asset": "AS-NO-SOURCE",
            "propagation": 0
          }
        ],
        "not_before": "2024-01-01T00:00:00Z",
        "not_after": "2025-01-01T00:00:00Z"
      }
    }
  ]
}
```

**IRR State**:
- RIPE: AS-NO-SOURCE contains AS65021, AS65022, AS65023
- ARIN: AS-NO-SOURCE contains AS65021, AS65024
- Default IRR sources: RIPE,RADB,ARIN,APNIC

**Expected Behavior**:
- bgpq4 should detect invalid irrLock configuration (null irr_source)
- Should log error: "irrLock mode requires irr_source to be specified"
- Should fall back to default behavior (all IRR sources or error out)
- Exit with non-zero status code

**Expected Output**:
- Error message to stderr explaining irrLock requires irr_source
- No prefix list output (or controlled fallback behavior)

---

### 1.5 Empty AS-SET in irrLock Mode

**Test ID**: RASA-IRRLOCK-005  
**Description**: Verify irrLock handles empty AS-SET correctly

**RASA JSON**:
```json
{
  "rasa_sets": [
    {
      "rasa_set": {
        "version": 0,
        "as_set_name": "AS-EMPTY-IRRLOCK",
        "containing_as": 65030,
        "members": [],
        "nested_sets": [],
        "irr_source": "RADB",
        "fallback_mode": "irrLock",
        "not_before": "2024-01-01T00:00:00Z",
        "not_after": "2025-01-01T00:00:00Z"
      }
    }
  ]
}
```

**IRR State**:
- RADB: AS-EMPTY-IRRLOCK contains AS65031, AS65032
- No RASA-AUTH for any AS

**Expected Behavior**:
- irrLock mode should NOT add AS65031, AS65032 even though they're in RADB
- Empty members list means don't trust IRR data
- Result in empty prefix-list
- Exit with success (0), indicating correctly locked behavior

**Expected Output**:
- Empty prefix list or "no ip prefix-list <name>"
- Warning in log: "irrLock mode with empty members list - no ASNs will be added"

