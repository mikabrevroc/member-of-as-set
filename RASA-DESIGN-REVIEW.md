# RASA -01 Design Review

**Date:** 2026-02-23  
**Document:** draft-carbonara-rpki-as-set-auth-01  
**Reviewer:** Based on ASGroup analysis and RIPE-731 principles

---

## Executive Summary

RASA -01 represents a significant architectural improvement over the -00 draft and addresses key lessons from ASGroup (draft-spaghetti-sidrops-rpki-asgroup-00). The two-object approach (RASA-SET + RASA-AUTH) is well-justified and aligns with the principle of separation of concerns.

**Overall Assessment:** **STRONG** - Ready for community review with minor clarifications.

---

## 1. Comparison with ASGroup (Prior Work)

### 1.1 What RASA -01 Does Right (vs. ASGroup)

| Aspect | ASGroup (Failed) | RASA -01 (Current) | Assessment |
|--------|------------------|-------------------|------------|
| **Opt-out mechanism** | Complex Opt-Out Listing (.ool files) | No opt-out - owner decides membership | ✅ Simplified |
| **Object types** | Two types (ASGroup + Opt-Out) | Two types (RASA-SET + RASA-AUTH) | ✅ Better separation |
| **Naming** | `asID + label` (non-intuitive) | Full `asSetName` (matches IRR) | ✅ Familiar |
| **IRR integration** | Not discussed - appears to replace | Core requirement - backward compatible | ✅ Critical win |
| **Validation** | Complex union logic | Simple lookup + optional RASA-AUTH check | ✅ Implementable |
| **Deployment story** | Unclear | Phased approach (3 phases) | ✅ Realistic |

### 1.2 Key Improvements Over ASGroup

1. **No Opt-Out Complexity**
   - ASGroup required checking both .grp and .ool files
   - RASA: Owner publishes members, that's it
   - If member wants out → must negotiate with owner (social, not technical)

2. **Clear Value Proposition**
   - ASGroup: "Group ASes cryptographically" (vague)
   - RASA: "Prevent AS-SET hijacking + enable member authorization" (specific)

3. **Tool Integration**
   - ASGroup: No mention of existing tools
   - RASA: Explicitly designed for bgpq4, IRRd integration

4. **Migration Path**
   - ASGroup: Big-bang replacement
   - RASA: Gradual 5-10 year transition

### 1.3 What ASGroup Had That RASA Doesn't (And That's OK)

- **Multiple groups per AS**: ASGroup's `label` allowed AS1234 to have multiple groups
  - *RASA position*: One AS-SET per owner is sufficient (matches IRR reality)
  - *Assessment*: ✅ Acceptable simplification

- **Opt-out flexibility**: Members could selectively opt-out of specific groups
  - *RASA position*: Not needed - if you're listed, you're authorized
  - *Assessment*: ✅ Complexity not justified by use cases

---

## 2. RIPE-731 Analysis and RASA Equivalence

### 2.1 RIPE-731 Approach (Route Object Validation)

**Core concept:** Use ROAs to validate/clean IRR route objects

```
IRR route object claims: 192.0.2.0/24 origin AS64496
ROA proves: AS64496 can announce 192.0.2.0/24
Result: Valid route object
```

**Key insight:** RPKI provides ground truth for validation, not replacement

### 2.2 RASA Equivalence

**Core concept:** Use RASA to validate/clean IRR AS-SET objects

```
IRR AS-SET claims: AS64496 is member of AS1299:AS-TWELVE99
RASA-SET proves: AS1299 owns AS1299:AS-TWELVE99 with members [64496, ...]
RASA-AUTH proves: AS64496 authorizes inclusion in AS1299:AS-TWELVE99
Result: Valid AS-SET membership
```

### 2.3 RIPE-731 Lessons Applied to RASA

| RIPE-731 Principle | RASA Application | Status |
|-------------------|------------------|--------|
| RPKI validates, doesn't replace | RASA validates AS-SETs, IRR still used | ✅ Applied |
| Gradual adoption | 3-phase deployment plan | ✅ Applied |
| Tool integration | bgpq4, IRRd support mentioned | ✅ Applied |
| Operator control | authoritative flag for policy | ✅ Applied |

### 2.4 Critical Difference: Bidirectional Validation

**RIPE-731 (Route objects):**
- Single direction: ROA confirms route object
- Route object owner = prefix owner (same entity)

**RASA (AS-SETs):**
- Bidirectional: 
  1. RASA-SET confirms AS-SET membership (AS-SET owner)
  2. RASA-AUTH confirms inclusion authorization (member ASN)
- Two different entities (AS-SET owner vs. member)

**Assessment:** ✅ RASA correctly identifies need for bidirectional authorization

---

## 3. Architectural Strengths

### 3.1 Two-Object Separation (RASA-SET + RASA-AUTH)

**Rationale:**
- Cryptographic separation of concerns
- Independent deployment schedules
- Prevents AS-SET owner from forging member authorization

**Comparison to alternatives:**

| Approach | Pros | Cons | RASA Choice |
|----------|------|------|-------------|
| **Separate objects** (RASA) | Clean separation, independent deploy | Two OIDs, more complex lookup | ✅ Selected |
| **Unified object** | Single OID, simpler | Blurred boundaries, forgery risk | ❌ Rejected |
| **ASGroup opt-out** | Member control | Complex validation, two files | ❌ Rejected |

### 3.2 nestedSets Field

**Purpose:** Enable recursive AS-SET expansion in pure RPKI

**Use case:**
```
AS1299:AS-TWELVE99 contains:
  - members: [AS64496, AS64497]
  - nestedSets: ["AS1299:AS-PEERS"]
```

**Assessment:** ✅ Essential for feature parity with IRR AS-SETs

### 3.3 authorizedIn Field (RASA-AUTH)

**Purpose:** Member ASN authorizes specific AS-SETs to include them

**Use case:**
```
AS64496 publishes RASA-AUTH:
  - authorizedIn: ["AS1299:AS-TWELVE99", "AS6939:AS-HURRICANE"]
  - strictMode: TRUE
→ Only these AS-SETs can include AS64496
```

**Assessment:** ✅ Critical for member protection

### 3.4 irrSource Field

**Purpose:** Lock AS-SET to specific IRR database (namespace protection)

**Assessment:** ✅ Solves real problem of AS-SET name collisions across databases

---

## 4. Areas for Improvement

### 4.1 Conflict Resolution Between RASA-SET and RASA-AUTH

**Current state:** Section mentions "log a warning or exclude based on policy"

**Gap:** No specific guidance on which should win

**Recommendation:**
```
When RASA-SET claims member X, but RASA-AUTH from X doesn't authorize:
- strictMode=FALSE: Include member, log warning
- strictMode=TRUE: Exclude member, log error
```

**Rationale:** RASA-AUTH (member's intent) should override RASA-SET (owner's claim)

### 4.2 RASA-AUTH strictMode Semantics

**Current:** "reject rather than warn"

**Gap:** Unclear what "reject" means operationally

**Recommendation:** Clarify:
- `strictMode=TRUE`: AS-SET expansion MUST fail if member not authorized
- `strictMode=FALSE`: Include member, log warning for audit

### 4.3 Nested AS-SET Validation

**Current:** nestedSets resolved recursively

**Gap:** No mention of circular dependency detection

**Recommendation:** Add:
```
Validators MUST detect circular nestedSets references:
- Track visited AS-SETs during expansion
- Abort with error if circular reference detected
- Suggest maximum recursion depth (e.g., 10)
```

### 4.4 IRR Fallback During Transition

**Current:** "use ONLY RASA member list" when authoritative=TRUE

**Gap:** What about nested AS-SETs with mixed coverage?

**Recommendation:** Document behavior:
```
Expanding AS-SET with nestedSets:
1. If nested AS-SET has RASA-SET → use RASA-SET
2. If nested AS-SET has no RASA-SET → use IRR
3. Result: Mixed RASA/IRR expansion is valid during transition
```

### 4.5 Member Authorization Ambiguity

**Current:** RASA-AUTH has `authorizedIn` list

**Gap:** What if member publishes multiple RASA-AUTH objects?

**Recommendation:** Add:
```
If multiple RASA-AUTH objects exist for same ASN:
- Validators SHOULD merge authorizedIn lists
- If conflicts (one says yes, other says no), most restrictive wins
```

---

## 5. Documentation Gaps

### 5.1 Missing: Detailed Validator Algorithm

Current algorithm is high-level. Needs pseudocode for:
- Recursive expansion with nestedSets
- RASA-AUTH validation at each level
- Circular reference detection
- Mixed RASA/IRR handling

### 5.2 Missing: Error Handling Specification

What should validators do when:
- RASA-SET signature invalid?
- RASA-AUTH expired but RASA-SET valid?
- Partial RASA coverage in nestedSets?

### 5.3 Missing: Operational Examples

Need concrete examples showing:
1. Happy path: RASA-SET + RASA-AUTH both present
2. Conflict: RASA-SET claims member, RASA-AUTH denies
3. Mixed: Some nested AS-SETs have RASA, others don't
4. Transition: Gradual migration from IRR to RASA

---

## 6. Comparison Summary

| Criterion | ASGroup | RASA -01 | Assessment |
|-----------|---------|----------|------------|
| **Simplicity** | ⭐⭐ Complex | ⭐⭐⭐⭐ Simple | RASA wins |
| **IRR Integration** | ⭐ None | ⭐⭐⭐⭐⭐ Core | RASA wins |
| **Member Protection** | ⭐⭐⭐ Opt-out | ⭐⭐⭐⭐⭐ Explicit auth | RASA wins |
| **Implementation** | ⭐⭐ Hard | ⭐⭐⭐⭐ Doable | RASA wins |
| **Deployment Path** | ⭐ Unclear | ⭐⭐⭐⭐⭐ Clear | RASA wins |
| **Prior Art** | ⭐⭐ ASGroup | ⭐⭐⭐⭐ Learns from ASGroup | RASA wins |

---

## 7. Recommendations

### 7.1 High Priority (Before Publication)

1. **Add conflict resolution section**
   - Document strictMode behavior
   - Clarify RASA-AUTH override

2. **Add circular reference detection**
   - Validator MUST detect cycles
   - Maximum recursion depth

3. **Expand operational examples**
   - Show RASA-SET + RASA-AUTH interaction
   - Document mixed RASA/IRR scenarios

### 7.2 Medium Priority (Future Revision)

4. **Add validator pseudocode**
   - Detailed expansion algorithm
   - Error handling flowchart

5. **Reference ASGroup explicitly**
   - Acknowledge prior work
   - Explain design differences

6. **Add ASPA synthesis details**
   - Algorithm for deriving AS-SETs from ASPA
   - Comparison with RASA approach

### 7.3 Low Priority (Nice to Have)

7. **Consider metadata fields**
   - `descr` for human-readable description
   - `contact` for operational issues

8. **Add deployment statistics**
   - Target adoption metrics
   - Success criteria

---

## 8. Conclusion

**RASA -01 is a well-designed proposal that successfully learns from ASGroup's failures.**

**Key strengths:**
1. ✅ Two-object approach provides clean separation
2. ✅ IRR integration enables incremental deployment
3. ✅ Nested AS-SET support (nestedSets field)
4. ✅ Member authorization (RASA-AUTH)
5. ✅ Namespace protection (irrSource field)

**Key gaps:**
1. ⚠️ Conflict resolution needs clarification
2. ⚠️ Circular reference detection missing
3. ⚠️ Detailed validator algorithm needed

**Overall verdict:** RASA -01 is ready for IETF community review. The architecture is sound, the design is implementable, and the deployment path is realistic. Addressing the gaps identified would strengthen the document but are not blockers for initial publication.

**Comparison to ASGroup:** RASA has learned the right lessons and avoids the pitfalls that caused ASGroup to fail. The focus on IRR compatibility and incremental deployment is the critical differentiator.

---

## Appendix: Design Philosophy Comparison

| Philosophy | ASGroup | RASA -01 |
|------------|---------|----------|
| **Complexity** | High (opt-out mechanism) | Low (explicit auth) |
| **Integration** | Replace IRR | Complement IRR |
| **Deployment** | Big-bang | Gradual (5-10 years) |
| **Validation** | Multi-object union | Simple lookup |
| **Member control** | Opt-out (reactive) | Authorization (proactive) |

**The shift from reactive (opt-out) to proactive (authorization) is the fundamental architectural improvement.**
