# Reverse AS-SET Proposal - IRC Discussion Summary

**Source:** #networker IRC channel log (networker-260222.log)  
**Date:** February 2026 (based on timestamps from log)  
**Proposer:** ytti (Saku Ytti)  
**Key Participants:** SwedeMike (Mikael Abrahamsson), nick-2128, Axu, teun, others

---

## Table of Contents

1. [Technical Background](#technical-background)
2. [The Problem Statement](#the-problem-statement)
3. [The Reverse AS-SET Proposal](#the-reverse-as-set-proposal)
4. [Key Discussion Points](#key-discussion-points)
5. [Technical Implementation Details](#technical-implementation-details)
6. [Questions and Concerns Raised](#questions-and-concerns-raised)
7. [Related Context: Bidirectional AS-SET](#related-context-bidirectional-as-set)
8. [Conclusion and Next Steps](#conclusion-and-next-steps)

---

## Technical Background

### Current Internet Routing Security Landscape

The discussions reference several existing routing security mechanisms:

1. **RPKI (Resource Public Key Infrastructure)** - Cryptographic validation of route originations via ROAs (Route Origin Authorizations)
2. **AS-SETs** - Sets of Autonomous System numbers maintained in IRR (Internet Routing Registry) databases like RIPE, ARIN, APNIC
3. **Prefix Filtering** - Traditional method of creating prefix-lists from AS-SET expansions to control what routes are accepted
4. **AS-PATH Filtering** - Filtering based on the AS path in BGP updates

### How AS-SETs Currently Work

Currently, an AS-SET is a unidirectional declaration:
- An AS-SET owner (e.g., a transit provider) declares which ASNs are permitted to be in their set
- These ASNs have no mechanism to declare "I should be in this AS-SET"
- Tools like `bgpq3` and `bgpq4` expand AS-SETs to generate prefix filters or AS-path filters
- There is no validation that an ASN in an AS-SET actually wants to be there

### The Problem with Current AS-SETs

From the IRC discussions, the key issue is:
- Anyone can add any ASN to their AS-SET without authorization
- If Google buys transit from a provider, that provider adds Google's ASNs to their AS-SET
- But there's no way for Google to verify or control which AS-SETs claim to contain them
- This allows potential hijacking: a malicious actor could add Google's ASNs to their AS-SET and advertise Google prefixes (with correct origin AS if the origin stays correct)

---

## The Problem Statement

### Quote from ytti (line 8511-8515):

> "hilariously, but if we had made AS-SET bidir, that is, for AS1 to include AS2 in their as-set, your AS2 would have to have some other object which includes AS1"
> 
> "we would have had, to this day, better mechanism for routing security than RPKI"
> 
> "since you can still happily leak google prefixes, as long as the origin stays correct"

### Quote from ytti (line 9706-9715) - The Core Proposal:

> "who will write proposal for reverse as-set object for IRR, like member-of-as-set: object"
> 
> "e.g. if google buys transit from me, google ads my as-set that i have in peeringdb to their member-of-as-set"
> 
> "now when BGPQ4 recurses my peeringdb as-set, it will check existence fo member-of-as-set and if that doesn't have the root as-set it is recursing, it'll prune the ASN"
> 
> "basically 0 cost bidir verification of as-set expensaion, that people get automatically once they upgrade bgpq4, without even knowing they have it"

---

## The Reverse AS-SET Proposal

### Core Concept

The proposal introduces a new IRR object called `member-of-as-set` (or similar) that creates bidirectional verification:

1. **Current state (unidirectional):**
   - AS-SET owner says: "These ASNs are in my set"
   - The ASNs have no say in the matter

2. **Proposed state (bidirectional):**
   - AS-SET owner says: "These ASNs are in my set"
   - Each ASN can declare: "I am a member of these AS-SETs"
   - When expanding an AS-SET, the tool checks if the claimed ASN has declared membership
   - If not declared, the ASN is pruned from the expansion

### Example Workflow

**Scenario:** Google (AS15169) buys transit from NTT (AS2914)

**Current Process:**
1. NTT adds AS15169 to their AS-SET: `AS-NTT-CUSTOMERS`
2. Anyone can expand `AS-NTT-CUSTOMERS` and get Google's prefixes
3. No verification that Google actually buys transit from NTT

**Proposed Process:**
1. NTT has AS-SET: `AS-NTT-CUSTOMERS` containing AS15169
2. Google creates `member-of-as-set: AS-NTT-CUSTOMERS` in their IRR object
3. When bgpq4 expands `AS-NTT-CUSTOMERS`:
   - Sees AS15169 in the set
   - Checks if AS15169 has declared `member-of-as-set: AS-NTT-CUSTOMERS`
   - If yes: include AS15169
   - If no: prune (drop) AS15169

### Benefits

From ytti's explanation (lines 9709-9716):

> "so now when some other customer i have, leaks google prefixes to me one of two things happen"
> 
> "a) it is dropped by RPKI, because origin is wrong"
> 
> "b) it is droped by AS-PATH filter, because their as-set cannot contain google, even if they add it"
> 
> "i have no prefix filtering at all, just as-path filter from expanding as-set"
> 
> "i think this would be very nice stop-gap solution, while we wait for something superior to come along"
> 
> "since we will get it deployed, without asking anyone to deploy it"

---

## Key Discussion Points

### 1. Authentication Model (nick-2128's Question)

**nick-2128 asks (line 9721-9723):**
> "ytti: how does the authentication work for this?"

**ytti's response (lines 9737-9745):**
> "nick-2128, not sure i understand"
> 
> "nick-2128, like my as-set, is of course my auth"
> 
> "nick-2128, but google's member-of-as-set is of course their auth"
> 
> "nick-2128, so if google buys transit from me, they figure out what is my as-set, and add that name to their member-of-as-set"
> 
> "nick-2128, these are basically ships in the night, neither one cares at all of the other one exists"
> 
> "google can claim to be member of any as-set it wants, without talking to anyone"
> 
> "my as-set can claim to have any asn in it, without talking to anyone"
> 
> "so all the 'security' happens at as-path/prefix-list gneration time (or out-of-band, people looking at peeringdb as-set, and complaining about prunable ASNs in as-sets)"

**Key insight:** The authentication is decentralized. Each party maintains their own objects, and the verification happens at filter generation time, not at object creation time.

### 2. Exhaustive List vs. Optional (SwedeMike's Question)

**SwedeMike asks (line 9746-9747):**
> "does the existance of this imply 'exhaustive list'? As in 'filter everything else'? Or perhaps that should be some kind of additional information?"

**Later, SwedeMike clarifies (line 9763):**
> "ytti: I mean, if I create this member-of-as-set and put 5 different AS-sets in there, and then some 6th shows up with my ASN in there, does that mean I've given a strong signal to ignore that?"

**ytti's response (lines 9763-9776):**
> "SwedeMike, if you list AS-SET[12345] there, and someone is recursing starting from AS-SET6, then your ASN cannot be in that list"
> 
> "and by default ep bgpq4 would prune it (with some --no-reverse-check switch to disable the behaviour)"
> 
> "SwedeMike, ok, so it is prescriptive and if I create this, I'd better maintain it and keep all of them in there?"
> 
> "yes"
> 
> "you need to know who are going to advertise you"
> 
> "or you create gap"
> 
> "ok, so then that's a 'exhaustive list' then. Just by creating this object, I'm attesting it contains everything and if it's not in there, drop it"
> 
> "yes"
> 
> "now i understand your original question"
> 
> "the moment you have 1 entry, it has to be complete list"

**Critical point:** Creating a `member-of-as-set` object is a prescriptive signal. Once you create it, you're declaring "these are ALL the AS-SETs I'm authorized to be in" - anything else should be pruned.

### 3. Different User Types

**ytti outlines different adoption patterns (lines 9756-9764):**

> "so i don't expect all or maybe not even most to add member-of-as-set object in their ASN"
> 
> "because most are not really that worried about being hijacked anyhow"
> 
> "but i would expect large shops to adopt it quickly"
> 
> "and that they would require in transit agreement, that their transit providers use pruning when genreating filters"
> 
> "so there probably will be few types of users"
> 
> "a) big shops, who know precisely what as-sets they are supposed to be member of"
> 
> "b) smaller shops, who care about this, but cannot know precisely what as-sets they are supposed to be member of, so they pre-authorize exhaustive list of tier1, tier2 players, because they don't know which upstream they'll upstream will purchaase and when, but they can easily list all 'usual suspects'"
> 
> "c) smaller shops who don't care, and never populate member-of-as-set"

### 4. Deployment Strategy

**ytti explains the deployment advantage (lines 9786-9790):**

> "to me it feels slike this would add lot of prefix hygiene with almost no cost at all, because no NOS needs to be changed, and large portino of people don't need to even change internal system. One day they upgrade bgpq4, and they gain this feature, without knowing it exists"

**Key deployment features:**
- No network operating system changes required
- No configuration changes needed for most users
- Just upgrade bgpq4 (or similar tools)
- Opt-in at the ASN level by creating the `member-of-as-set` object

---

## Technical Implementation Details

### BGPQ4 Integration

**ytti describes the implementation (lines 9708-9710):**

> "now when BGPQ4 recurses my peeringdb as-set, it will check existence fo member-of-as-set and if that doesn't have the root as-set it is recursing, it'll prune the ASN"
> 
> "basically 0 cost bidir verification of as-set expensaion, that people get automatically once they upgrade bgpq4, without even knowing they have it"
> 
> "(ofc BGPQ4 would have command line switch to disable reverse check, because not all applications of as-set have anything to do with BGP peering security)"

### Filter Generation

**Current approach (prefix-list):**
```
# Expand AS-SET to prefixes
bgpq3 -S RIPE AS-EXAMPLE > prefix-list.txt
# Apply prefix-list to BGP session
```

**Proposed approach (AS-path filter):**
```
# Expand AS-SET with reverse check
bgpq4 --reverse-check -S RIPE AS-EXAMPLE > as-path-filter.txt
# Result: AS-PATH filter like "^([1 2 3 4 5]*)$"
```

### Impact on Route Server Filtering

**SwedeMike asks about IX route servers (line 9782):**
> "how does this work on IXes with RS btw, never thought of that."

**ytti responds (lines 9783-9785):**
> "i reckon people don't prefix filter in RS, IDK, but RS likely prefix filters people peering with it?"

**SwedeMike follows up:**
> "theoretically one could invent something new there as well, and map next-hopsto ASNs and thus to AS sets, and the IX operator could maintain an ASN-to-nexthop list."

This suggests potential extensions for route server environments, though the primary focus is on transit/peering relationships.

---

## Questions and Concerns Raised

### 1. Maintenance Burden

SwedeMike raised the concern that creating a `member-of-as-set` object implies a commitment to maintain an exhaustive list. If you have multiple upstreams and miss one, your routes could be pruned.

**ytti's response:** This is a feature, not a bug. Large networks should know their upstreams. Smaller networks can either:
- Not use the feature (status quo)
- Pre-authorize a list of "usual suspect" tier-1/tier-2 providers

### 2. Gap Handling

**SwedeMike (line 9811):**
> "don't you still need prefix filter for non-ROA prefixes?"

**ytti's response (lines 9812-9818):**
> "no, those are like 20% and i'd just synthethise them from route objects"
> 
> "but even if i don't synthethise them, and just allow unknown and valid both"
> 
> "it's fine"
> 
> "because if by now you don't have signed prefix, that's on you"
> 
> "and you're welcome to close the gap at any time"

This indicates the proposal is designed to work alongside RPKI, not replace it entirely.

### 3. Opposition Concerns

**ytti anticipates opposition (lines 9822-9824):**

> "i reckon my main fear is, not if this works, but that it's good enough"
> 
> "in that proper solutions become harder to market"
> 
> "and i think that might be the biggest opposition argument as well"

This is a political/strategic concern: if this "good enough" stop-gap solution is widely deployed, it might delay adoption of "proper" solutions like ASPA.

---

## Related Context: Bidirectional AS-SET

Earlier in the IRC log (lines 8511-8515), ytti mentions the concept of bidirectional AS-SET in the context of routing security:

> "hilariously, but if we had made AS-SET bidir, that is, for AS1 to include AS2 in their as-set, your AS2 would have to have some other object which includes AS1"
> 
> "we would have had, to this day, better mechanism for routing security than RPKI"
> 
> "since you can still happily leak google prefixes, as long as the origin stays correct"
> 
> "but that wouldn't be possible, if we had bidir as-set"
> 
> "sure we can conecive that with ASPA in place, we have superior solution"

This shows the thinking that led to the reverse AS-SET proposal - it's essentially a practical way to implement bidirectional verification without changing the fundamental IRR infrastructure.

---

## Conclusion and Next Steps

### Summary of the Proposal

The "reverse AS-SET" or "member-of-as-set" proposal is a lightweight, backward-compatible enhancement to IRR-based route filtering that:

1. **Adds bidirectional verification** to AS-SET expansions
2. **Requires no protocol changes** - uses existing IRR infrastructure
3. **Is opt-in** - ASNs choose whether to create the `member-of-as-set` object
4. **Integrates with existing tools** - bgpq4 can add support with a command-line flag
5. **Provides immediate value** - even partial adoption provides security benefits
6. **Complements RPKI** - works alongside existing origin validation

### Immediate Benefits

**From ytti (line 9787-9804):**

> "like in NTT case particularly, 99% of our customer ports couldn't anymore advertise google to us"
> 
> "_while_ dropping prefix-lists"
> 
> "and having only RPKI + AS_PATH"
> 
> "(not 'proper' AS_PATH but 'these ASN, in any permutation')"
> 
> "as given by AS-SET recursion"
> 
> "i'm busy trying to get rid of prefix-list filteirng at NTT, and i think i might succeed"
> 
> "but i'm kinda worried of accidental leaks from BGP optimizers, which might keep origin ASN in place"
> 
> "this would pass RPKI check, ofc"
> 
> "and if will pass prefix-list check, if google is in AS-SET"
> 
> "so this would actually stop also malicious actors from _majority_ of ports"

### Next Steps Needed

Based on the IRC discussions, the following would be needed to move this forward:

1. **Formal proposal document** to IRR communities (RIPE, ARIN, APNIC, etc.)
2. **Reference implementation** in bgpq4 or similar tool
3. **PeeringDB integration** - the discussions mention PeeringDB as a source for AS-SET data
4. **Adoption by large networks** - ytti mentions large shops would be early adopters
5. **Community feedback** - especially from transit providers and IX operators

### Final Quote

**ytti (lines 9825-9827):**

> "but i just don't see anything, even ASPA, being widely deployed in next 10y"
> 
> "and this could potentially be widely deployed in weeks, not months or years"
> 
> "the momoent anyone ads member-of-as-set object, the momoent people can trawl through peeringDB as-set, and automatically contact offenders"

---

## Appendix: Related IRC Quotes

### On RPKI Limitations
> "since you can still happily leak google prefixes, as long as the origin stays correct" - ytti

### On Deployment Speed
> "since we will get it deployed, without asking anyone to deploy it" - ytti

### On Automatic Monitoring
> "undoubtful, if we get this done, someone will regularly walk peeringdb AS-SET, and automatically email people who have prunable ASN in their set" - ytti

### On Authentication Model
> "so all the 'security' happens at as-path/prefix-list gneration time (or out-of-band, people looking at peeringdb as-set, and complaining about prunable ASNs in as-sets)" - ytti

### On Backward Compatibility
> "(ofc BGPQ4 would have command line switch to disable reverse check, because not all applications of as-set have anything to do with BGP peering security)" - ytti

---

*Document compiled from IRC log analysis. All quotes are verbatim from the #networker IRC channel discussion.*
