# Edge Cases and Error Handling

## 4. EDGE CASE TESTS

### 4.1 AS-SET Without RASA Object

**Test ID**: RASA-EDGE-001  
**Description**: Verify behavior when AS-SET has no corresponding RASA object

**RASA JSON**:
```json
{
  "rasa_sets": [
    {
      "rasa_set": {
        "version": 0,
        "as_set_name": "AS-EXISTS-RASA",
        "containing_as": 65100,
        "members": [65101],
        "nested_sets": [],
        "irr_source": "RADB",
        "fallback_mode": "irrFallback",
        "not_before": "2024-01-01T00:00:00Z",
        "not_after": "2025-01-01T00:00:00Z"
      }
    }
  ]
}
```

**IRR State** (AS-EXISTS-RASA):
- RADB: contains AS65101, AS65102

**IRR State** (AS-NO-RASA):
- RADB: AS-NO-RASA contains AS65110, AS65111, AS65112

**Test Cases**:
1. **Query AS-EXISTS-RASA** (has RASA object)
   - Should use RASA processing
   - Include AS65101 (from RASA)

2. **Query AS-NO-RASA** (no RASA object)
   - Should log warning: "No RASA object found for AS-NO-RASA, falling back to traditional IRR"
   - Expand normally using IRR data
   - Include AS65110, AS65111, AS65112

---

### 4.2 RASA Object with Invalid Data

**Test ID**: RASA-EDGE-002  
**Description**: Verify proper error handling for invalid RASA JSON

**Invalid RASA JSON Examples**:

**Case 2a: Malformed JSON (syntax error)**
```json
{
  "rasa_sets": [
    {
      "rasa_set": {
        "version": 0,
        "as_set_name": "AS-MALFORMED",
        "containing_as": 65120,
        "members": [65121, 65122  // Missing closing bracket
      }
    }
  ]
}
```

**Expected Behavior**:
- JSON parsing should fail
- Log error: "Failed to parse RASA JSON: syntax error at line X"
- Continue without RASA protection (traditional IRR expansion)
- Exit code: 0 (but with warning)

**Case 2b: Missing required fields**
```json
{
  "rasa_sets": [
    {
      "rasa_set": {
        "version": 0,
        "as_set_name": "AS-MISSING-FIELDS",
        // Missing containing_as
        "members": [65131],
        "nested_sets": [],
        "irr_source": "RADB",
        "fallback_mode": "irrFallback"
      }
    }
  ]
}
```

**Expected Behavior**:
- RASA validation should fail (missing containing_as)
- Log error: "Invalid RASA object: missing required field 'containing_as'"
- Fall back to traditional IRR expansion
- Exit code: 0 (with warning)

**Case 2c: Invalid fallback_mode value**
```json
{
  "rasa_sets": [
    {
      "rasa_set": {
        "version": 0,
        "as_set_name": "AS-INVALID-MODE",
        "containing_as": 65140,
        "members": [65141],
        "nested_sets": [],
        "irr_source": "RADB",
        "fallback_mode": "invalidMode"
      }
    }
  ]
}
```

**Expected Behavior**:
- RASA validation should fail (invalid fallback_mode)
- Log error: "Invalid fallback_mode 'invalidMode', must be one of: irrLock, rasaOnly, irrFallback"
- Use default behavior (likely irrFallback) or fail

---

### 4.3 Circular Dependencies in Nested Sets

**Test ID**: RASA-EDGE-003  
**Description**: Verify handling of circular dependencies

**RASA JSON**:
```json
{
  "rasa_sets": [
    {
      "rasa_set": {
        "version": 0,
        "as_set_name": "AS-CIRCULAR-A",
        "containing_as": 65150,
        "members": [65151],
        "nested_sets": ["AS-CIRCULAR-B"],
        "irr_source": "RADB",
        "fallback_mode": "irrFallback",
        "not_before": "2024-01-01T00:00:00Z",
        "not_after": "2025-01-01T00:00:00Z"
      }
    },
    {
      "rasa_set": {
        "version": 0,
        "as_set_name": "AS-CIRCULAR-B",
        "containing_as": 65152,
        "members": [65153],
        "nested_sets": ["AS-CIRCULAR-A"],
        "irr_source": "RADB",
        "fallback_mode": "irrFallback",
        "not_before": "2024-01-01T00:00:00Z",
        "not_after": "2025-01-01T00:00:00Z"
      }
    }
  ]
}
```

**Expected Behavior**:
- Detection of circular dependency
- Log: "Circular dependency detected: AS-CIRCULAR-A → AS-CIRCULAR-B → AS-CIRCULAR-A"
- Break the loop (e.g., include AS65151, AS65153, but stop at cycle)
- Continue processing with partial results
- Exit code: 0 (with warning)

---

### 4.4 Expired RASA Object

**Test ID**: RASA-EDGE-004  
**Description**: Verify handling of expired RASA objects

**RASA JSON**:
```json
{
  "rasa_sets": [
    {
      "rasa_set": {
        "version": 0,
        "as_set_name": "AS-EXPIRED",
        "containing_as": 65160,
        "members": [65161],
        "nested_sets": [],
        "irr_source": "RADB",
        "fallback_mode": "irrFallback",
        "not_before": "2023-01-01T00:00:00Z",
        "not_after": "2023-12-31T23:59:59Z"
      }
    }
  ]
}
```

**Current Date**: 2024-06-01 (after expiry)

**Expected Behavior**:
- Check RASA validity (not_before < current < not_after)
- Current date is after "not_after"
- Log error: "RASA object for AS-EXPIRED has expired (expiry: 2023-12-31T23:59:59Z)"
- Options:
  a) Fail completely (exit code > 0)
  b) Fall back to traditional IRR expansion with warning
- Recommended: Option (b) - maintain backward compatibility

---

### 4.5 Large AS-SET with Many Members

**Test ID**: RASA-EDGE-005  
**Description**: Verify performance with large AS-SET (100+ members)

**RASA JSON**:
```json
{
  "rasa_sets": [
    {
      "rasa_set": {
        "version": 0,
        "as_set_name": "AS-LARGE-SET",
        "containing_as": 65170,
        "members": [AS65171, AS65172, ..., AS65270],
        "nested_sets": [],
        "irr_source": "RADB",
        "fallback_mode": "irrFallback",
        "not_before": "2024-01-01T00:00:00Z",
        "not_after": "2025-01-01T00:00:00Z"
      }
    }
  ]
}
```

**IRR State**:
- RADB: AS-LARGE-SET contains 100+ ASNs, including AS65171-AS65270

**Expected Behavior**:
- Complete processing in reasonable time (< 30 seconds)
- Include all 100 RASA-SET members
- Validate RASA-AUTH efficiently
- Memory usage should not exceed practical limits

**Performance Requirements**:
- Time: < 30 seconds for 100 ASNs
- Memory: < 512MB
- RASA-AUTH lookups: O(1) or O(log n) per ASN

---

### 4.6 Multiple RASA Objects for Same AS-SET

**Test ID**: RASA-EDGE-006  
**Description**: Verify handling of duplicate RASA objects for same AS-SET

**RASA JSON**:
```json
{
  "rasa_sets": [
    {
      "rasa_set": {
        "version": 0,
        "as_set_name": "AS-DUPLICATE",
        "containing_as": 65180,
        "members": [65181, 65182],
        "nested_sets": [],
        "irr_source": "RADB",
        "fallback_mode": "irrFallback",
        "not_before": "2024-01-01T00:00:00Z",
        "not_after": "2025-01-01T00:00:00Z"
      }
    },
    {
      "rasa_set": {
        "version": 0,
        "as_set_name": "AS-DUPLICATE",
        "containing_as": 65180,
        "members": [65183, 65184],
        "nested_sets": [],
        "irr_source": "RADB",
        "fallback_mode": "irrFallback",
        "not_before": "2024-01-01T00:00:00Z",
        "not_after": "2025-01-01T00:00:00Z"
      }
    }
  ]
}
```

**Expected Behavior**:
- Detect duplicate AS-SET name
- Options:
  a) Use first occurrence, ignore subsequent
  b) Merge members from all occurrences
  c) Log error and fail
- **Recommended**: Option (b) - merge members
- Should also check for conflicts in other fields (fallback_mode, irr_source)

**Expected Output (if merging)**:
- Merged members: AS65181, AS65182, AS65183, AS65184
- Log: "Multiple RASA objects found for AS-DUPLICATE, merging 2 entries"

