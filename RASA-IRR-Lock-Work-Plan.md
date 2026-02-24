# RASA IRR Database Lock Mode - Comprehensive Work Plan

## Executive Summary
Add comprehensive namespace and IRR database reference support to enable "IRR database lock" functionality where operators cryptographically lock which IRR database an AS-SET originates from without fully replacing IRR AS-SETs.

## Key Innovation: IRR Database Lock Mode

Current RASA draft has basic `irrSource` field but lacks comprehensive semantics for **lock without replace**. The enhancement enables:

**AS2914 Use Case:**
- AS2914 has AS2914:AS-GLOBAL in RADB with 1000+ members
- They publish RASA-SET with:
  - irrSource: "RADB"
  - fallbackMode: irrLock (new enum value)
  - members: [] (empty - don't replace, just lock)
- Tools supporting RASA will:
  - Query ONLY RADB for AS2914:AS-GLOBAL
  - Reject AS2914:AS-GLOBAL from RIPE, ARIN, etc.
  - Provide cryptographic assurance of IRR source
- AS2914 maintains single AS-SET in RADB, no dual maintenance

## Three Fallback Modes

```asn1
FallbackMode ::= ENUMERATED {
  irrFallback(0),  -- Default: Use IRR alongside RASA
  irrLock(1),      -- NEW: Lock to irrSource only
  rasaOnly(2)      -- RASA data only, ignore IRR
}
```

## Task Breakdown (10 Tasks)

### Phase 1: Analysis (Parallel)
1. **Current Draft Analysis** - Map existing fields, identify gaps
2. **IRR Database Ecosystem Research** - Survey RADB, RIPE, ARIN, etc.
3. **Implementation Requirements** - Tool integration needs (bgpq4, IRRd)

### Phase 2: Design (Sequential)
4. **ASN.1 Schema Design** - Design enhanced RasaSetContent structure
5. **Lock Mode Semantics** - Define three modes and validation algorithms
6. **Source Hierarchy & Precedence** - Document collision resolution

### Phase 3: XML Modifications (Parallel Groups)

**Group C (Parallel after design):**
7. Section 2.3 Enhancement - Add namespace protection design goal
8. New Section 3.4 - IRR Database Lock Mode documentation
9. Update Section 3.5.1 - RasaSetContent schema with new fields

**Group D (After Group C):**
10. Update Section 3.5.2 - Field definitions for new fields
11. Update Section 4.1.4 - AS-SET expansion algorithm with lock logic
12. New Section 3.9 - Namespace and database precedence rules

**Group E (Parallel after Group C):**
13. New Section 4.4 - Migration path documentation
14. New Section 5.7 - IRR Database Lock use cases (AS2914, HE, ARIN)
15. New Section 6.5 - JSON output format for tools

### Phase 4: Implementation Guidance (Parallel)
16. Update Section 7.1 - Publishing guidance with mode examples
17. Update Section 7.2 - Consuming guidance with tool implementation

### Phase 5: Validation (Sequential)
18. Specification Consistency Review - Cross-reference all sections
19. Create Test Vectors - Generate examples for each mode

## Critical Path
Task 1.1 → 2.1 → 3.3 → 3.5 → 4.2 → 5.1 (~10 days minimum)

## Key Dependencies

- **Design depends on Analysis**: ASN.1 schema needs research from Tasks 1.2-1.3
- **XML modifications depend on Design**: Can't modify schema before designing it
- **Validation depends on all modifications**: Must review complete specification

## Parallelization Opportunities

**Maximum Parallelism:**
- Phase 1 (Analysis): 3 tasks → 3 parallel agents
- Phase 3 (XML): Groups C, D, E can run 5+ agents in parallel
- Phase 4 (Implementation): 2 parallel agents
- **Total peak parallelism: 8+ simultaneous tasks**

## File Sections to Modify

| Section | Current Line | Task | Change Type |
|---------|--------------|------|-------------|
| Design Goals | 332-356 | 7 | Add namespace goal |
| RasaSetContent Schema | 599-610 | 9 | Replace with enhanced version |
| Field Definitions | 614-656 | 10 | Add new field docs |
| AS-SET Expansion | 818-865 | 11 | Rewrite algorithm |
| Publishing Guidance | 1288-1316 | 16 | Add mode examples |
| Consuming Guidance | 1317-1342 | 17 | Add tool guidance |

## New Sections to Write

Insert in draft-carbonara-rpki-as-set-auth-04.xml:
1. Section 2.x: IRR Database Lock Mode (after line 527)
2. Section 3.9: Namespace and Precedence (after line 769)
3. Section 4.4: Migration Paths (after line 1177)
4. Section 5.7: IRR Lock Use Cases (after line 1177)
5. Section 6.5: JSON Output Format (after line 1350+)

## ASN.1 Schema Changes

**Replace RasaSetContent (lines 599-610):**

```asn1
-- Fallback Mode enumeration
FallbackMode ::= ENUMERATED {
    irrFallback(0),    -- Use IRR data alongside RASA (default)
    irrLock(1),       -- Lock to irrSource only, no fallback
    rasaOnly(2)       -- RASA data only, reject IRR data
}

-- Enhanced RasaSetContent with IRR Database Lock
RasaSetContent ::= SEQUENCE {
    version           [0] INTEGER DEFAULT 0,  -- Version 0 = original
    asSetName         UTF8String,
    containingAS      ASID,
    members           SEQUENCE OF ASID,
    nestedSets        SEQUENCE OF UTF8String OPTIONAL,
    irrSource         UTF8String OPTIONAL,   -- e.g., "RADB", "RIPE"
    fallbackMode      FallbackMode DEFAULT irrFallback,
    authoritative     BOOLEAN DEFAULT FALSE, -- Replaces RasaFlags bit
    notBefore         GeneralizedTime,
    notAfter          GeneralizedTime
}
```

**Key Changes:**
- Add `FallbackMode` ENUMERATED type with 3 values
- Add `fallbackMode` field to RasaSetContent
- Replace RasaFlags `authoritative` bit with explicit BOOLEAN
- Keep backward compatibility: version=0 for original, version=1 for enhanced

## Delegation Recommendations

| Task | Category | Skills | Agent Type |
|------|----------|--------|------------|
| 1.1-1.3 | Analysis | RFCXML, RPKI, IRR | Oracle/Explore |
| 2.1-2.3 | Design | ASN.1, Security | Oracle |
| 3.1-3.9 | Specification | RFCXML, Technical Writing | Librarian |
| 4.1-4.2 | Implementation | Tool Development | Oracle |
| 5.1-5.2 | Validation | Test Design, Review | Build |

## Success Criteria

1. ✅ **Clear Semantics**: Three fallback modes unambiguously defined
2. ✅ **Backward Compatible**: Version 0 objects still validate correctly
3. ✅ **IRR Lock Working**: AS2914 can lock to RADB without replacing AS-SET
4. ✅ **Algorithm Correct**: AS-SET expansion handles all three modes
5. ✅ **Tool Ready**: JSON format specified for bgpq4/integration
6. ✅ **Reviewed**: Zero consistency errors across specification

## Estimated Duration

- **Analysis**: 2-3 days (parallel)
- **Design**: 3-4 days (sequential)
- **XML Mods**: 5-7 days (parallel groups)
- **Impl Guidance**: 2-3 days (parallel)
- **Validation**: 2-3 days (sequential)
- **TOTAL**: 14-20 days with parallelization

## Risk Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| ASN.1 breaking change | High | Low | Maintain version field, backward compatibility |
| Algorithm ambiguity | Medium | Medium | Extensive examples and test vectors |
| Complex implementation | High | Medium | Clear migration path, incremental deployment |
| Specification inconsistency | Medium | Low | Cross-reference review (Task 5.1) |

## Example: AS2914 RADB Lock

**Current State:**
- AS2914:AS-GLOBAL exists in RADB with ~1000 members
- Same name could exist in RIPE with different members (attack vector)
- Tools query all databases, merge results

**With IRR Lock:**
```asn1
RASA-SET Object:
  asSetName:     "AS2914:AS-GLOBAL"
  containingAS:  2914
  members:       []  -- Empty = don't replace, just lock source
  nestedSets:    []
  irrSource:     "RADB"
  fallbackMode:  irrLock(1)  -- NEW: Lock to RADB only
  authoritative: FALSE       -- Still using IRR data
```

**Tool Behavior:**
```
1. Query RPKI for RASA-SET
2. Find RASA-SET with irrLock mode
3. Query ONLY RADB for AS2914:AS-GLOBAL
4. Reject AS2914:AS-GLOBAL from RIPE, ARIN, etc.
5. Validate members normally
6. Operators get cryptographic source assurance
```

## Example JSON Output Format

```json
{
  "asSetName": "AS2914:AS-GLOBAL",
  "containingAS": 2914,
  "members": [64511, 64512, 64513],
  "nestedSets": [],
  "irrSource": "RADB",
  "fallbackMode": "irrLock",
  "authoritative": false,
  "validationStatus": {
    "signatureValid": true,
    "certificateChainValid": true,
    "notExpired": true,
    "totemValid": true,
    "sourceLocked": true
  },
  "queryInfo": {
    "irrDatabasesQueried": ["RADB"],
    "rrPkiRepository": "rrdp.example.com/rpki",
    "validationTime": "2026-02-24T15:30:00Z"
  }
}
```

## Next Steps

1. **Approve plan** and initiate Task 1.2 & 1.3 (parallel)
2. **Delegate** tasks to specialized agents per recommendations
3. **Review** design (Task 2.1-2.3) before implementation
4. **Implement** XML modifications in phases per dependency graph
5. **Validate** complete specification before finalization

## Deliverables

1. ✅ Updated `draft-carbonara-rpki-as-set-auth-05.xml`
2. ✅ `RASA-IRR-Lock-Implementation-Guide.md`
3. ✅ `rasa-test-vectors.json` (test cases)
4. ✅ `rasa-examples/` (configuration samples)
5. ✅ `rasa-migration-playbook.md` (deployment guide)

---

**Document Version**: 1.0  
**Date**: 2026-02-24  
**Status**: Ready for execution
**Estimated Effort**: 14-20 person-days
**Recommended Team**: 3-5 specialized agents in parallel
