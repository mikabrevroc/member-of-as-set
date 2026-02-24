# RASA-ONLY Mode Test Cases

## 2. RASA-ONLY MODE TESTS (Continued from main spec)

### 2.1 Basic rasaOnly: Use Only RASA Members

**Test ID**: RASA-RASAONLY-001  
**Description**: Verify rasaOnly mode uses only RASA data, ignores IRR

**RASA JSON**:
```json
{
  "rasa_sets": [
    {
      "rasa_set": {
        "version": 0,
        "as_set_name": "AS-RASA-ONLY",
        "containing_as": 65500,
        "members": [65501, 65502, 65503],
        "nested_sets": [],
        "irr_source": null,
        "fallback_mode": "rasaOnly",
        "not_before": "2024-01-01T00:00:00Z",
        "not_after": "2025-01-01T00:00:00Z"
      }
    }
  ],
  "rasas": [
    {
      "rasa": {
        "version": 0,
        "authorized_as": 65501,
        "authorized_in": [
          {
            "asset": "AS-RASA-ONLY",
            "propagation": 0
          }
        ]
      }
    },
    {
      "rasa": {
        "version": 0,
        "authorized_as": 65502,
        "authorized_in": [
          {
            "asset": "AS-RASA-ONLY",
            "propagation": 0
          }
        ]
      }
    }
  ]
}
```

**IRR State**:
- RADB: AS-RASA-ONLY contains AS65501, AS65502, AS65503, AS65504, AS65505
- RIPE: AS-RASA-ONLY contains AS65503, AS65506, AS65507
- Total IRR ASNs: AS65501-AS65507

**Expected Behavior**:
- bgpq4 should NOT query any IRR databases (irr_source is null)
- Should ONLY use RASA-SET members: AS65501, AS65502, AS65503
- Should validate RASA-AUTH for AS65501 and AS65502
- AS65503 should be included even without RASA-AUTH (trusted from RASA-SET)
- Should NOT query IRR for additional ASNs
- Should NOT include AS65504-AS65507

**Expected Output**:
- Prefixes from AS65501, AS65502, AS65503
- Validation success for AS65501, AS65502
- No prefixes from AS65504-AS65507 (IRR data ignored)

---

### 2.2 rasaOnly with Empty Members

**Test ID**: RASA-RASAONLY-002  
**Description**: Verify rasaOnly handles empty members list

**RASA JSON**:
```json
{
  "rasa_sets": [
    {
      "rasa_set": {
        "version": 0,
        "as_set_name": "AS-EMPTY-RASA",
        "containing_as": 65510,
        "members": [],
        "nested_sets": [],
        "irr_source": null,
        "fallback_mode": "rasaOnly",
        "not_before": "2024-01-01T00:00:00Z",
        "not_after": "2025-01-01T00:00:00Z"
      }
    }
  ]
}
```

**IRR State**:
- RADB: AS-EMPTY-RASA contains AS65511, AS65512, AS65513
- RIPE: AS-EMPTY-RASA contains AS65514, AS65515

**Expected Behavior**:
- Should NOT query any IRR databases
- Should NOT add any ASNs (empty members list)
- Result in empty prefix-list
- Exit with success (0)

**Expected Output**:
- Empty prefix list: "no ip prefix-list <name>"
- Or if using -E flag: empty output

---

### 2.3 rasaOnly with Nested Sets

**Test ID**: RASA-RASAONLY-003  
**Description**: Verify rasaOnly handles nested AS-SET declarations

**RASA JSON**:
```json
{
  "rasa_sets": [
    {
      "rasa_set": {
        "version": 0,
        "as_set_name": "AS-PARENT-RASA",
        "containing_as": 65520,
        "members": [65521, 65522],
        "nested_sets": ["AS-CHILD-RASA"],
        "irr_source": null,
        "fallback_mode": "rasaOnly",
        "not_before": "2024-01-01T00:00:00Z",
        "not_after": "2025-01-01T00:00:00Z"
      }
    },
    {
      "rasa_set": {
        "version": 0,
        "as_set_name": "AS-CHILD-RASA",
        "containing_as": 65523,
        "members": [65523, 65524],
        "nested_sets": [],
        "irr_source": null,
        "fallback_mode": "rasaOnly",
        "not_before": "2024-01-01T00:00:00Z",
        "not_after": "2025-01-01T00:00:00Z"
      }
    }
  ],
  "rasas": [
    {
      "rasa": {
        "version": 0,
        "authorized_as": 65521,
        "authorized_in": [
          {
            "asset": "AS-PARENT-RASA",
            "propagation": 0
          }
        ]
      }
    },
    {
      "rasa": {
        "version": 0,
        "authorized_as": 65523,
        "authorized_in": [
          {
            "asset": "AS-CHILD-RASA",
            "propagation": 0
          }
        ]
      }
    }
  ]
}
```

**IRR State**:
- RADB: AS-PARENT-RASA contains AS65521, AS65522, AS65525
- RADB: AS-CHILD-RASA contains AS65523, AS65524, AS65526, AS65527

**Expected Behavior**:
- Should NOT query IRR for any AS-SET
- Should expand AS-PARENT-RASA to include:
  - Direct members: AS65521, AS65522
  - Nested set members: AS65523, AS65524 (from AS-CHILD-RASA)
- Should validate RASA-AUTH:
  - AS65521 authorized for AS-PARENT-RASA ✓
  - AS65523 authorized for AS-CHILD-RASA ✓
  - AS65522, AS65524 in RASA-SET but no RASA-AUTH (OK for rasaOnly)
- Should NOT include AS65525, AS65526, AS65527 (IRR data ignored)

**Expected Output**:
- Prefixes from AS65521, AS65522, AS65523, AS65524
- No prefixes from AS65525, AS65526, AS65527

