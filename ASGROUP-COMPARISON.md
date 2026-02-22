# Comparison: ASGroup vs RASA

## Background

**ASGroup** (draft-spaghetti-sidrops-rpki-asgroup-00) was proposed in November 2022 by Job Snijders (Fastly) and Fredrik Korsbäck (Amazon). It **expired in May 2023** and went nowhere.

**RASA** (draft-carbonara-rpki-as-set-auth-00) is the current proposal, building on lessons learned.

## Key Differences

### 1. Signing Model

| Aspect | ASGroup | RASA |
|--------|---------|------|
| **Signed by** | AS-SET owner (CAS) | AS-SET owner (CAS) |
| **What it proves** | "These are my members" | "These are my members" |
| **Member authorization** | Opt-out mechanism | Explicit authorization |

**ASGroup**: Members can opt-out via separate Opt-Out Listing  
**RASA**: Members implicitly authorize by being listed (no opt-out)

### 2. Object Structure

**ASGroup:**
```asn1
RpkiSignedGrouping ::= SEQUENCE {
  version          [0] INTEGER DEFAULT 0,
  asID             ASID,           -- Owner
  label            GroupingLabel,  -- Differentiator
  referenceable    BOOLEAN,        -- Can be referenced?
  members          SEQUENCE OF ASIdOrGroupingPointer
}
```

**RASA:**
```asn1
RasaContent ::= SEQUENCE {
  version          [0] INTEGER DEFAULT 0,
  asSetName        UTF8String,     -- Full AS-SET name
  containingAS     ASID,           -- Owner
  members          SEQUENCE OF ASID,
  flags            RasaFlags,      -- doNotInherit, authoritative
  notBefore        GeneralizedTime,
  notAfter         GeneralizedTime
}
```

**Key Differences:**
- ASGroup uses `label` to differentiate multiple groups per AS
- RASA uses full `asSetName` (matches IRR naming)
- ASGroup has `referenceable` boolean
- RASA has `doNotInherit` and `authoritative` flags
- RASA includes validity period

### 3. Opt-Out Mechanism

**ASGroup Opt-Out Listing:**
```asn1
RpkiSignedGroupingOptOut ::= SEQUENCE {
  version [0] INTEGER DEFAULT 0,
  asID    ASID,              -- Who's opting out
  label   GroupingLabel OPTIONAL,
  optOut  SEQUENCE OF ASIdOrGroupingPointer  -- What to opt out of
}
```

**RASA:**
- No opt-out mechanism
- Members authorize inclusion by being listed
- If member wants out, they must convince AS-SET owner to remove them

**Why:** Opt-out creates complexity. RASA simplifies to "owner decides membership."

### 4. IRR Integration

| Aspect | ASGroup | RASA |
|--------|---------|------|
| IRR compatibility | Not discussed | Core requirement |
| Fallback to IRR | No | Yes (backward compatible) |
| Tool integration | Not mentioned | bgpq4, etc. |
| Deployment path | Unclear | Phased approach |

**ASGroup** appears to be a complete replacement for IRR AS-SETs.  
**RASA** is designed to work alongside IRR during transition.

### 5. Flags Comparison

| ASGroup | RASA | Purpose |
|---------|------|---------|
| `referenceable` | `doNotInherit` | Control transitive inclusion |
| N/A | `authoritative` | Signal preference over IRR |

**ASGroup `referenceable`:**
- FALSE = This ASGroup cannot be referenced by others
- TRUE = This ASGroup can be referenced

**RASA `doNotInherit`:**
- TRUE = Can be referenced, but members not inherited
- FALSE = Normal transitive inclusion

**Difference:** ASGroup prevents reference entirely; RASA allows reference but blocks member inheritance.

## Why ASGroup Failed

### 1. Complex Opt-Out Mechanism
- Separate object type (.ool files)
- Complex validation rules
- Hard to reason about ("am I in this group?" requires checking both .grp and .ool)

### 2. Label-Based Naming
- Non-intuitive: `asID + label` forms group name
- Doesn't match existing IRR conventions
- Multiple groups per AS adds complexity

### 3. No IRR Integration Story
- Appears to be complete replacement
- No backward compatibility
- No incremental deployment path
- Tool vendors have no incentive to adopt

### 4. Validation Complexity
- Must validate both ASGroup and Opt-Out objects
- Union logic for multiple objects
- Recursive descent with opt-out filtering

### 5. Use Case Unclear
- Who publishes ASGroups?
- Who consumes them?
- Why is this better than IRR?

## What RASA Does Differently

### 1. Simplified Model
- No opt-out mechanism
- One object type (no .ool files)
- Clear semantics: owner defines membership

### 2. IRR Compatibility
- Works alongside existing IRR infrastructure
- Fallback to IRR when RASA unavailable
- Gradual adoption path

### 3. Practical Deployment
- Phase 1: High-value AS-SETs (content providers, Tier-1s)
- Phase 2: Tool integration (bgpq4, etc.)
- Phase 3: Widespread adoption

### 4. Clear Value Proposition
- Cryptographic verification of AS-SET membership
- Prevents AS-SET hijacking
- "doNotInherit" solves transitive chain attacks

### 5. Tool-Friendly
- Simple validation: check signature, check flags, return members
- No complex opt-out logic
- Can be integrated into existing IRR tools

## Recommendations

1. **Reference ASGroup** in RASA document as prior work
2. **Explain why opt-out was removed** (complexity, unclear benefit)
3. **Emphasize IRR integration** as key differentiator
4. **Keep design simple** (resist feature creep)
5. **Focus on practical deployment** (tool vendors, operators)

## Conclusion

ASGroup was a well-intentioned proposal that failed due to complexity and lack of clear deployment path. RASA learns from these mistakes by:

- Simplifying the model (no opt-out)
- Integrating with existing infrastructure (IRR)
- Providing clear incremental deployment
- Focusing on practical use cases

The key insight: **RPKI-based AS-SETs need to complement IRR, not replace it.**
