# RASA Specification Changes Summary

**Date**: 2026-02-24  
**Status**: ASN.1 and XML Updated

---

## Changes Made

### 1. RASA.asn1 - Updated

**Location**: `/Users/mabrahamsson/src/reverse-as-set/RASA.asn1`

#### New Types Added:

**FallbackMode ENUMERATED** (Lines 31-35):
```asn1
FallbackMode ::= ENUMERATED {
    irrFallback(0),    -- Merge RASA members with IRR query (default)
    irrLock(1),        -- Lock to specific IRR database only
    rasaOnly(2)        -- Use only RASA data, ignore IRR
}
```

**PropagationScope ENUMERATED** (Lines 38-41):
```asn1
PropagationScope ::= ENUMERATED {
    unrestricted(0),    -- Can be nested anywhere (default)
    directOnly(1)       -- Only direct inclusion, no nesting/transit
}
```

**AuthorizedEntry SEQUENCE** (Lines 45-49):
```asn1
AuthorizedEntry ::= SEQUENCE {
    asSetName        UTF8String,
    propagation      PropagationScope OPTIONAL
    -- If propagation is absent, defaults to unrestricted
}
```

#### Modified Types:

**RasaSetContent** (Lines 52-63):
- Added `fallbackMode` field with DEFAULT irrFallback

**RasaAuthContent** (Lines 68-76):
- Changed `authorizedIn` from `SEQUENCE OF UTF8String` to `SEQUENCE OF AuthorizedEntry`

---

### 2. draft-carbonara-rpki-as-set-auth-04.xml - Updated

**Location**: `/Users/mabrahamsson/src/reverse-as-set/draft-carbonara-rpki-as-set-auth-04.xml`

#### Changes:

1. **Added FallbackMode to ASN.1 schema** (around line 585):
   - Added FallbackMode ENUMERATED definition
   - Added to RasaSetContent structure

2. **Updated RASA-SET field definitions** (around line 655):
   - Added `fallbackMode` field documentation
   - Updated `irrSource` documentation to note it's required for irrLock

3. **Added new section: fallbackMode Behavior** (after line 798):
   - Section anchor: `fallback-mode`
   - Subsections:
     - `fallback-irrFallback`: Default merge behavior
     - `fallback-irrLock`: IRR database lock mode
     - `fallback-rasaOnly`: RASA-only mode
     - `fallback-validation`: Validation rules

---

## Feature Coverage

### ✅ Now Fully Specified

| Feature | ASN.1 | XML Spec | Description |
|---------|-------|----------|-------------|
| **fallbackMode** | ✅ | ✅ | Three modes: irrFallback, irrLock, rasaOnly |
| **AuthorizedEntry** | ✅ | ✅ | Structure with asSetName + propagation |
| **PropagationScope** | ✅ | ✅ | unrestricted(0) or directOnly(1) |
| **IRR Database Lock** | ✅ | ✅ | irrLock mode with irrSource |

---

## Key Use Case: IRR Database Lock

**AS2914 Example**:
```asn1
RasaSetContent {
  asSetName: "AS2914:AS-GLOBAL",
  containingAS: 2914,
  members: [],              -- Empty for lock mode
  nestedSets: [],
  irrSource: "RADB",        -- Lock to RADB
  fallbackMode: irrLock     -- Lock mode
}
```

**Behavior**:
- Tools query ONLY RADB for this AS-SET
- Reject same AS-SET from RIPE/ARIN
- No duplicate AS-SET maintenance required

---

## Next Steps

### Implementation Required:

1. **rpki-client** (Phase 1):
   - Update `rasa.c` to parse new ASN.1 structure
   - Extract propagation from AuthorizedEntry
   - Parse fallbackMode field
   - Update JSON output format

2. **bgpq4** (Phase 2):
   - Update JSON parsing for new fields
   - Implement fallbackMode logic
   - Add IRR source filtering
   - Integrate with expander.c

3. **Testing** (Phase 3):
   - Create test RPKI objects
   - Verify end-to-end flow
   - Test all three fallback modes

---

## Files Modified

1. `/Users/mabrahamsson/src/reverse-as-set/RASA.asn1` - Complete ASN.1 schema
2. `/Users/mabrahamsson/src/reverse-as-set/draft-carbonara-rpki-as-set-auth-04.xml` - RFC XML specification
3. `/Users/mabrahamsson/src/reverse-as-set/RASA-DATA-FLOW.md` - Data flow documentation (new)
4. `/Users/mabrahamsson/src/reverse-as-set/CHANGES-SUMMARY.md` - This file (new)

---

## Document History

- 2026-02-24: Updated ASN.1 with FallbackMode, AuthorizedEntry, PropagationScope
- 2026-02-24: Updated RFC XML with fallbackMode section and field definitions
