# Architectural Limitations of member-of-as-set

## The Core Problem: Chain of Trust

The member-of-as-set proposal has a fundamental architectural limitation:
**For authorization to be effective, EVERY AS-SET in the expansion chain must protect itself.**

### Attack Scenario

```
Google (AS15169) wants to be in Arelion's (AS1299) customer AS-SET only.

1. Google creates:
   member-of-as-set: AS15169
   member-of:        AS1299:AS-TWELVE99

2. Malicious ISP creates:
   AS-MALICIOUS-CUSTOMER
   members: AS1299:AS-TWELVE99  ← includes Arelion's AS-SET

3. If Arelion does NOT create member-of-as-set for AS1299:AS-TWELVE99,
   then AS-MALICIOUS-CUSTOMER expansion includes Arelion's AS-SET,
   which includes Google.

4. Result: Google is now in malicious AS-SET, despite only
   authorizing Arelion's AS-SET.
```

### Why This Happens

AS-SET expansion is **transitive**:
- AS-SET A contains AS-SET B
- AS-SET B contains ASN X
- Therefore AS-SET A contains ASN X

The member-of-as-set proposal only protects the **leaf nodes** (ASNs).
It does not protect **intermediate AS-SETs** unless they also create
member-of-as-set objects.

## The Bootstrap Problem

For Google's authorization to be meaningful:
1. ✓ Google must create member-of-as-set (under Google's control)
2. ✓ Google must list authorized AS-SETs (under Google's control)
3. ✗ **Arelion must also protect AS1299:AS-TWELVE99** (NOT under Google's control)
4. ✗ **Every AS-SET in the chain must protect itself** (NOT under Google's control)

**If any link in the chain doesn't use member-of-as-set, the whole chain is vulnerable.**

## Deployment Reality

### Scenario 1: Universal Adoption (Unrealistic)
- Every AS-SET in the world creates member-of-as-set objects
- Full protection achieved
- **Problem:** Never happens in practice

### Scenario 2: Tier-1 First (Partial)
- Only Tier-1 providers protect their AS-SETs
- Content providers can safely authorize Tier-1 AS-SETs
- **Problem:** Tier-2/3 providers remain vulnerable

### Scenario 3: Leaf-Node Only (Current Draft)
- Only ASNs create member-of-as-set objects
- **Problem:** Intermediate AS-SETs can be hijacked, bypassing protection

## Potential Solutions

### Solution 1: Protected-Set Flag

Add a `protected-set` attribute to AS-SET objects:

```
as-set: AS1299:AS-TWELVE99
members: AS1, AS2, AS3
protected-set: yes
mnt-by: MAINT-ARELION
```

IRR software **MUST NOT** expand AS-SETs without `protected-set: yes`
when member-of-as-set verification is enabled.

**Pros:**
- Clear opt-in for AS-SET protection
- Fail-closed (unprotected AS-SETs can't be used in verified expansions)

**Cons:**
- Requires AS-SET owners to update their objects
- Breaking change to AS-SET behavior

### Solution 2: Stop-on-Missing-Protect

Verification algorithm change:
- When expanding an AS-SET, check if it has member-of-as-set
- If NO member-of-as-set exists, **STOP expansion** and return error
- Do NOT silently include unprotected AS-SETs

**Pros:**
- No changes to AS-SET objects needed
- Fail-closed behavior

**Cons:**
- Many legitimate AS-SETs will cause failures
- Requires widespread adoption before useful

### Solution 3: Hierarchical Authorization

Allow member-of-as-set to reference **both** ASNs and AS-SETs in member-of:

```
member-of-as-set: AS15169
member-of:        AS1299:AS-TWELVE99
member-of:        AS-HURRICANE
```

When expanding AS-HURRICANE which contains AS1299:AS-TWELVE99,
verification checks if AS1299:AS-TWELVE99 is in Google's authorized list.

**Pros:**
- Works with existing AS-SET structure
- No changes to AS-SET objects

**Cons:**
- Requires content providers to list ALL intermediate AS-SETs
- Maintenance burden (AS-SETs change over time)

### Solution 4: Signed Assertions (RPKI Integration)

Use RPKI to sign member-of-as-set assertions:
- AS15169 creates ROA-like object signed by Google's RPKI key
- Object states: "AS15169 authorizes inclusion in AS1299:AS-TWELVE99"
- Verification uses RPKI validation instead of IRR queries

**Pros:**
- Cryptographic security
- No IRR dependency
- Works with existing RPKI infrastructure

**Cons:**
- Major scope change (now it's an RPKI proposal)
- Requires RPKI deployment
- More complex

### Solution 5: Do-Not-Inherit Flag

Add a `do-not-inherit` or `opaque` flag to AS-SET objects:

```
as-set: AS1299:AS-TWELVE99
members: AS1, AS2, AS3
do-not-inherit: yes
mnt-by: MAINT-ARELION
```

When `do-not-inherit: yes` is set:
- The AS-SET can be included in other AS-SETs
- But its members are NOT transitively inherited
- Expansion stops at the AS-SET boundary

**Example:**
```
AS-MALICIOUS members: AS1299:AS-TWELVE99
AS1299:AS-TWELVE99 do-not-inherit: yes, members: AS1, AS2, Google

Result: AS-MALICIOUS expansion = {AS1299:AS-TWELVE99}
        NOT {AS1, AS2, Google}
```

**Pros:**
- AS-SET owner controls inheritance behavior
- Protects downstream ASNs without requiring their participation
- Simple to understand and implement
- Backward compatible (default is inherit)

**Cons:**
- Requires AS-SET owners to update their objects
- Changes traditional AS-SET semantics
- May break existing uses that depend on inheritance
- Tools must be updated to respect the flag

**Use Case:**
Tier-1 providers can protect their customer AS-SETs:
```
as-set: AS1299:AS-TWELVE99
do-not-inherit: yes
remarks: Customer AS-SET - members not inheritable
mnt-by: MAINT-ARELION
```

This prevents malicious AS-SETs from "stealing" customers by
including AS1299:AS-TWELVE99.

## Recommendation

The current draft should **acknowledge this limitation** and **document**
that member-of-as-set only provides protection when:

1. **Both parties participate** - the ASN AND the AS-SET owner
2. **Chain is fully protected** - every intermediate AS-SET is protected
3. **Adoption is widespread** - unprotected AS-SETs cause failures

### Incremental Deployment Strategy

**Phase 1: Education**
- Document the limitation clearly
- Target Tier-1 providers first
- Content providers can start creating objects

**Phase 2: Tier-1 Protection**
- Major transit providers protect their AS-SETs
- Content providers see benefit for Tier-1 relationships

**Phase 3: Tooling**
- IRR software supports "stop-on-missing-protect" mode
- Network operators can enable strict verification

**Phase 4: Universal Adoption**
- Industry standard to protect AS-SETs
- Full protection achieved

## Document Update Needed

The RFC draft needs:
1. **Security Considerations** section documenting this limitation
2. **Deployment Considerations** section with phased approach
3. **Examples** showing both protected and unprotected scenarios
4. **IANA considerations** for protected-set flag (if adopted)

## Conclusion

member-of-as-set is **not a silver bullet**. It requires **coordinated
adoption** to be effective. The proposal should be framed as an **opt-in
mechanism for mutual protection** rather than a **unilateral security
control**.

Without widespread adoption, the protection is partial at best.
