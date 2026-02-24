# IRR-FALLBACK Mode Test Cases

## 3. IRR-FALLBACK MODE TESTS (Continued from main spec)

### 3.1 Merge RASA and IRR Data

**Test ID**: RASA-IRRFALLBACK-001  
**Description**: irrFallback merges RASA-SET and IRR data (but prefers RASA)

**RASA JSON**:
```json
{
  "rasa_sets": [
    {
      "rasa_set": {
        "version": 0,
        "as_set_name": "AS-MERGE-TEST",
        "containing_as": 64496,
        "members": [65001, 65002],
        "nested_sets": [],
        "irr_source": "RADB",
        "fallback_mode": "irrFallback",
        "not_before": "2024-01-01T00:00:00Z",
        "not_after": "2025-01-01T00:00:00Z"
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
            "asset": "AS-MERGE-TEST",
            "propagation": 0
          }
        ]
      }
    },
    {
      "rasa": {
        "version": 0,
        "authorized_as": 65002,
        "authorized_in": [
          {
            "asset": "AS-MERGE-TEST",
            "propagation": 0
          }
        ]
      }
    }
  ]
}
```

**IRR State**:
- RADB: AS-MERGE-TEST contains AS65001, AS65002, AS65003, AS65004, AS65005
- RIPE: AS-MERGE-TEST contains AS65001, AS65002, AS65006
- ARIN: AS-MERGE-TEST contains AS65001, AS65002, AS65007

**Expected Behavior**:
- Query RADB (irr_source: RADB)
- Include AS65001, AS65002 from RASA-SET (primary source)
- Include AS65003, AS65004, AS65005 from IRR (fallback/additional)
- Validate RASA-AUTH for AS65001 and AS65002 (should pass)
- For AS65003-AS65005: require RASA-AUTH before inclusion
- Since no RASA-AUTH for AS65003-AS65005, they should NOT be included
- Do NOT query RIPE or ARIN

**Expected Output**:
- Prefixes from AS65001, AS65002 (validated via RASA)
- Warning: "AS65003, AS65004, AS65005 found in IRR but lacking RASA-AUTH - skipped"
- No prefixes from AS65006, AS65007

---

### 3.2 Conflict Handling (Same AS in Both)

**Test ID**: RASA-IRRFALLBACK-002  
**Description**: Verify conflicts resolved when AS appears in both RASA and IRR

**RASA JSON**:
```json
{
  "rasa_sets": [
    {
      "rasa_set": {
        "version": 0,
        "as_set_name": "AS-CONFLICT-TEST",
        "containing_as": 64496,
        "members": [65010],
        "nested_sets": [],
        "irr_source": "RADB",
        "fallback_mode": "irrFallback",
        "not_before": "2024-01-01T00:00:00Z",
        "not_after": "2025-01-01T00:00:00Z"
      }
    }
  ],
  "rasas": [
    {
      "rasa": {
        "version": 0,
        "authorized_as": 65010,
        "authorized_in": [
          {
            "asset": "AS-CONFLICT-TEST",
            "propagation": 0
          }
        ]
      }
    }
  ]
}
```

**IRR State**:
- RADB: AS-CONFLICT-TEST contains AS65010, AS65011, AS65012

**Expected Behavior**:
- RASA-SET declares AS65010 as member
- IRR also shows AS65010 as member
- RASA-AUTH confirms AS65010 is authorized for this AS-SET
- AS65010 should be included once (no duplicates)
- AS65011, AS65012 should be evaluated for RASA-AUTH inclusion

**Expected Output**:
- Prefixes from AS65010 (single occurrence, verified)
- For AS65011, AS65012: check RASA-AUTH before inclusion
- If no RASA-AUTH entries for AS65011, AS65012: exclude them with warnings

---

### 3.3 RASA-AUTH Validation During Expansion

**Test ID**: RASA-IRRFALLBACK-003  
**Description**: irrFallback validates RASA-AUTH for all ASNs before inclusion

**RASA JSON**:
```json
{
  "rasa_sets": [
    {
      "rasa_set": {
        "version": 0,
        "as_set_name": "AS-AUTH-VALIDATION",
        "containing_as": 64496,
        "members": [65021, 65022, 65023],
        "nested_sets": [],
        "irr_source": "RADB",
        "fallback_mode": "irrFallback",
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
            "asset": "AS-AUTH-VALIDATION",
            "propagation": 0
          }
        ]
      }
    },
    {
      "rasa": {
        "version": 0,
        "authorized_as": 65022,
        "authorized_in": [
          {
            "asset": "AS-AUTH-VALIDATION",
            "propagation": 0
          }
        ]
      }
    },
    {
      "rasa": {
        "version": 0,
        "authorized_as": 65023,
        "authorized_in": [
          {
            "asset": "AS-AUTH-VALIDATION",
            "propagation": 0
          }
        ]
      }
    }
  ]
}
```

**IRR State**:
- RADB: AS-AUTH-VALIDATION contains AS65021, AS65022, AS65023, AS65024, AS65025
- Each ASN has valid route-objects in RADB

**Expected Behavior**:
- Query RADB database
- For each ASN found:
  1. Check RASA-AUTH validation
  2. If authorized: include prefixes
  3. If NOT authorized: skip with warning
- AS65021, AS65022, AS65023: authorized via RASA → include
- AS65024, AS65025: no RASA-AUTH → skip with warning

**Expected Output**:
- Prefixes from AS65021, AS65022, AS65023
- Warning: "Skipping AS65024 (not authorized by RASA-AUTH)"
- Warning: "Skipping AS65025 (not authorized by RASA-AUTH)"

---

### 3.4 Nested Sets with irrFallback

**Test ID**: RASA-IRRFALLBACK-004  
**Description**: irrFallback validates nested AS-SET structures

**RASA JSON**:
```json
{
  "rasa_sets": [
    {
      "rasa_set": {
        "version": 0,
        "as_set_name": "AS-PARENT-FALLBACK",
        "containing_as": 64496,
        "members": [65031, 65032],
        "nested_sets": ["AS-CHILD-FALLBACK"],
        "irr_source": "RADB",
        "fallback_mode": "irrFallback",
        "not_before": "2024-01-01T00:00:00Z",
        "not_after": "2025-01-01T00:00:00Z"
      }
    },
    {
      "rasa_set": {
        "version": 0,
        "as_set_name": "AS-CHILD-FALLBACK",
        "containing_as": 65033,
        "members": [65033, 65034],
        "nested_sets": [],
        "irr_source": "RADB",
        "fallback_mode": "irrFallback",
        "not_before": "2024-01-01T00:00:00Z",
        "not_after": "2025-01-01T00:00:00Z"
      }
    }
  ],
  "rasas": [
    {
      "rasa": {
        "version": 0,
        "authorized_as": 65031,
        "authorized_in": [
          {
            "asset": "AS-PARENT-FALLBACK",
            "propagation": 0
          }
        ]
      }
    },
    {
      "rasa": {
        "version": 0,
        "authorized_as": 65033,
        "authorized_in": [
          {
            "asset": "AS-CHILD-FALLBACK",
            "propagation": 0
          }
        ]
      }
    }
  ]
}
```

**IRR State**:
- RADB: AS-PARENT-FALLBACK contains AS65031, AS65032, AS65035
- RADB: AS-CHILD-FALLBACK contains AS65033, AS65034, AS65036, AS65037

**Expected Behavior**:
- Query RADB for AS-PARENT-FALLBACK
- Include declared members: AS65031, AS65032
- Expand nested set: Query RADB for AS-CHILD-FALLBACK
- Include nested set members: AS65033, AS65034
- Validate RASA-AUTH for AS65031, AS65033
- IRR fallback additions: AS65035, AS65036, AS65037
- For IRR additions (AS65035-AS65037): validate RASA-AUTH before inclusion

**Expected Output**:
- Prefixes from AS65031, AS65032, AS65033, AS65034
- AS65035: skipped (no RASA-AUTH)
- AS65036, AS65037: skipped (no RASA-AUTH)
- Log: "Skipping AS65035-AS65037 (IRR data lacks RASA-AUTH)"

