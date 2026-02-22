# draft-ietf-grow-member-of-as-set-00

## Membership Verification for Autonomous System Sets (AS-SETs)

### Status of This Memo

This Internet-Draft is submitted in full conformance with the provisions of BCP 78 and BCP 79.

Internet-Drafts are working documents of the Internet Engineering Task Force (IETF). Note that other groups may also distribute working documents as Internet-Drafts. The list of current Internet-Drafts is at https://datatracker.ietf.org/drafts/current/.

Internet-Drafts are draft documents valid for a maximum of six months and may be updated, replaced, or obsoleted by other documents at any time. It is inappropriate to use Internet-Drafts as reference material or to cite them other than as work in progress.

This Internet-Draft will expire on August 22, 2026.

### Copyright Notice

Copyright (c) 2026 IETF Trust and the persons identified as the document authors. All rights reserved.

This document is subject to BCP 78 and the IETF Trust Legal Provisions Relating to IETF Documents (https://trustee.ietf.org/license-info) in effect on the date of publication of this document. Please review these documents carefully, as they describe your rights and restrictions with respect to this document. Code Components extracted from this document must include Revised BSD License text as described in Section 4.e of the Trust Legal Provisions and are provided without warranty as described in the Revised BSD License.

---

## Abstract

This document defines a new object type, member-of-as-set, for use in Internet Routing Registry (IRR) databases. The member-of-as-set object enables autonomous systems to declare membership in AS-SET objects, creating bidirectional verification of AS-SET expansions. This mechanism addresses a long-standing security gap in Border Gateway Protocol (BGP) route filtering where any autonomous system can include any other autonomous system in an AS-SET without authorization.

The member-of-as-set object provides a lightweight, backward-compatible mechanism that allows network operators to verify that an autonomous system listed in an AS-SET has authorized such inclusion. When used in conjunction with existing tools such as bgpq4, this verification enables automated pruning of unauthorized autonomous systems from AS-SET expansions, improving BGP routing security without requiring changes to router implementations or BGP protocol specifications.

---

## 1. Introduction

### 1.1 Background and Motivation

Internet Routing Registry (IRR) databases [RFC2622] have long been used by network operators to generate BGP route filters. The Routing Policy Specification Language (RPSL) defines the as-set object, which represents a set of autonomous systems. Network operators expand AS-SET objects to generate prefix lists and AS path filters for BGP peering relationships.

A fundamental limitation of current AS-SET objects is their unidirectional nature. An AS-SET owner can include any autonomous system in their set without requiring authorization from the included autonomous system. This creates a security vulnerability: a malicious or misconfigured operator can include high-value autonomous systems in their AS-SET and potentially advertise prefixes that would pass filter-based validation.

While Resource Public Key Infrastructure (RPKI) [RFC6480] provides cryptographic origin validation through Route Origin Authorizations (ROAs) [RFC6482], it does not prevent route leaks where the origin autonomous system is correct but the path is unauthorized. Similarly, Autonomous System Provider Authorization (ASPA) [RFC9595] provides AS path validation for provider-customer relationships but has seen limited deployment.

### 1.2 Goals and Scope

This document defines the member-of-as-set object to enable bidirectional verification of AS-SET membership. The primary goals are:

1. **Authorization**: Allow autonomous systems to declare which AS-SETs they authorize for inclusion.
2. **Verification**: Enable automated verification of AS-SET expansions against declared memberships.
3. **Backward Compatibility**: Ensure the mechanism does not break existing IRR infrastructure or tools.
4. **Incremental Deployment**: Allow deployment without requiring universal adoption.
5. **Complementarity**: Work alongside existing security mechanisms (RPKI, ASPA) rather than replacing them.

---

## 2. Terminology and Conventions

### 2.1 Key Words

The key words MUST, MUST NOT, REQUIRED, SHALL, SHALL NOT, SHOULD, SHOULD NOT, RECOMMENDED, NOT RECOMMENDED, MAY, and OPTIONAL in this document are to be interpreted as described in BCP 14 [RFC2119] [RFC8174] when, and only when, they appear in all capitals, as shown here.

### 2.2 Definitions

**AS-SET**: An RPSL object representing a set of autonomous system numbers (ASNs) and/or references to other AS-SETs, defined in [RFC2622].

**Member-of-AS-SET**: An RPSL object defined in this document that allows an autonomous system to declare membership in one or more AS-SETs.

**IRR**: Internet Routing Registry, a database of routing policy information used to generate BGP filters.

**RPSL**: Routing Policy Specification Language, the language used to define objects in IRR databases [RFC2622].

**AS-SET Expansion**: The process of recursively resolving an AS-SET to obtain the complete set of autonomous system numbers it represents.

**Root AS-SET**: The AS-SET object from which an expansion begins.

---

## 3. The member-of-as-set Object

### 3.1 Object Definition

The member-of-as-set object is an RPSL object that allows an autonomous system to declare membership in one or more AS-SETs. This declaration serves as authorization for inclusion in those AS-SETs.

### 3.2 Object Format

The member-of-as-set object follows standard RPSL object syntax [RFC2622]:

```
member-of-as-set:   [mandatory]  [single]     [primary/lookup key]
admin-c:            [mandatory]  [multiple]   [inverse key]
tech-c:             [mandatory]  [multiple]   [inverse key]
remarks:            [optional]   [multiple]   []
mnt-by:             [mandatory]  [multiple]   [inverse key]
created:            [generated]  [single]     []
last-modified:      [generated]  [single]     []
source:             [mandatory]  [single]     []
```

### 3.3 Attribute Definitions

#### 3.3.1 member-of-as-set Attribute

The member-of-as-set attribute specifies the AS-SET objects in which the autonomous system declares membership. The syntax is:

```
member-of-as-set: <as-set-name-1> [ <as-set-name-2> ... <as-set-name-n> ]
```

Where:
- as-set-name-i is a valid AS-SET name as defined in [RFC2622]
- Multiple AS-SETs are separated by whitespace
- The attribute MUST contain at least one AS-SET name
- AS-SET names MUST be unique within the attribute

The member-of-as-set attribute is the primary key for this object type and serves as the lookup key.

#### 3.3.2 admin-c and tech-c Attributes

These attributes reference role or person objects that provide administrative and technical contact information, respectively, as defined in [RFC2622].

#### 3.3.3 mnt-by Attribute

This attribute references the maintainer object(s) authorized to modify this object, as defined in [RFC2622]. Changes to the member-of-as-set object MUST be authenticated by one of the referenced maintainers.

#### 3.3.4 source Attribute

This attribute identifies the IRR database from which this object originates, as defined in [RFC2622].

### 3.4 Object Semantics

The member-of-as-set object creates a membership declaration from an autonomous system to one or more AS-SETs. This declaration has the following semantic properties:

1. **Authorization**: By including an AS-SET name in its member-of-as-set object, an autonomous system authorizes its inclusion in expansions of that AS-SET.
2. **Exhaustiveness**: If a member-of-as-set object exists for an autonomous system, it SHOULD contain a complete list of all AS-SETs in which the autonomous system authorizes inclusion.
3. **Independence**: The member-of-as-set object is created and maintained independently of the AS-SET objects it references.
4. **Validation**: The referenced AS-SETs need not exist at the time the member-of-as-set object is created.

---

## 4. Verification Mechanism

### 4.1 Overview

The member-of-as-set verification mechanism operates during AS-SET expansion. When a tool expands an AS-SET to generate filters, it checks each autonomous system found in the expansion against that autonomous system's member-of-as-set object, if one exists.

### 4.2 Verification Algorithm

Given an AS-SET S to be expanded, the verification algorithm is:

1. Recursively expand AS-SET S to obtain the initial set of autonomous systems A = {a1, a2, ..., an}.

2. For each autonomous system ai in A:
   a. Query the IRR for a member-of-as-set object associated with ai.
   b. If no member-of-as-set object exists for ai, include ai in the final result (backward compatibility).
   c. If a member-of-as-set object exists for ai:
      i. Check if the name of the root AS-SET S appears in ai's member-of-as-set attribute.
      ii. If yes, include ai in the final result.
      iii. If no, prune (exclude) ai from the final result.

3. Return the filtered set of autonomous systems.

### 4.3 Implementation in Filtering Tools

Tools that expand AS-SETs (such as bgpq4) SHOULD support member-of-as-set verification. The implementation SHOULD:

1. Query IRR databases for member-of-as-set objects during expansion.
2. Provide a command-line option to enable or disable verification.
3. Default to disabled verification initially to ensure backward compatibility.
4. Log or report pruned autonomous systems to facilitate troubleshooting.
5. Cache member-of-as-set objects to improve performance.

### 4.4 Root AS-SET Determination

The root AS-SET is the AS-SET from which an expansion originates. During recursive expansion:

- When expanding AS-SET A which contains a reference to AS-SET B:
  - Autonomous systems directly in A are verified against A.
  - Autonomous systems in B are verified against the original root AS-SET (A), not B.

### 4.5 Multiple Member-of-AS-SET Objects

If multiple IRR databases contain member-of-as-set objects for the same autonomous system, implementations SHOULD:

1. Query all configured IRR databases.
2. Apply the union of all declared memberships (conservative approach).
3. Optionally, report conflicts for administrative review.

---

## 5. Deployment Considerations

### 5.1 Backward Compatibility

The member-of-as-set mechanism is designed for backward compatibility:

1. **Non-participating autonomous systems**: Autonomous systems without member-of-as-set objects are included in expansions exactly as they are today.
2. **Non-supporting tools**: Tools that do not implement member-of-as-set verification continue to work without modification.
3. **IRR infrastructure**: IRR software requires no changes to support member-of-as-set objects; they are standard RPSL objects.

### 5.2 Incremental Deployment

Deployment can proceed incrementally:

1. **Phase 1 - Tool Support**: Filtering tools add member-of-as-set verification capability with default disabled.
2. **Phase 2 - Early Adopters**: Large autonomous systems create member-of-as-set objects listing their transit providers AS-SETs.
3. **Phase 3 - Provider Adoption**: Transit providers begin enabling verification for customer-facing filters.
4. **Phase 4 - Widespread Adoption**: Verification becomes standard practice, with tools defaulting to enabled.

### 5.3 Operational Recommendations

For autonomous systems creating member-of-as-set objects:

1. Include all AS-SETs for transit providers, Internet exchange route servers, and bilateral peering partners from whom you accept routes.
2. Use automation to keep member-of-as-set objects synchronized with actual routing relationships.
3. Monitor for AS-SET expansions that would prune your autonomous system.
4. Document the member-of-as-set policy in peering agreements.

For transit providers:

1. Enable member-of-as-set verification on customer-facing sessions once significant customers have deployed member-of-as-set objects.
2. Provide tools and documentation to help customers create appropriate member-of-as-set objects.
3. Consider member-of-as-set deployment status in peering decisions.

### 5.4 Relationship to Other Security Mechanisms

The member-of-as-set mechanism complements existing BGP security mechanisms:

1. **RPKI**: Member-of-as-set verification does not replace RPKI origin validation but adds AS path validation for the AS-SET expansion process.
2. **ASPA**: ASPA [RFC9595] provides more comprehensive AS path validation. Member-of-as-set is simpler to deploy but less comprehensive.
3. **Prefix Filtering**: Member-of-as-set verification can reduce reliance on prefix-based filtering by providing AS-based verification.

---

## 6. Security Considerations

### 6.1 Threat Model

The member-of-as-set mechanism addresses the following threats:

1. **Unauthorized AS-SET Inclusion**: An autonomous system operator includes another autonomous system in their AS-SET without authorization.
2. **Accidental Misconfiguration**: A legitimate operator mistakenly includes the wrong autonomous system in their AS-SET.
3. **BGP Optimizer Leaks**: Traffic engineering tools that maintain origin AS but change the path may inadvertently advertise routes through unauthorized paths.

### 6.2 Security Properties

The member-of-as-set mechanism provides:

1. **Opt-in Protection**: Autonomous systems choose whether to create member-of-as-set objects.
2. **Decentralized Authorization**: Each autonomous system independently controls its AS-SET memberships.
3. **Visibility**: Member-of-as-set objects are public, enabling monitoring and auditing.

### 6.3 Limitations and Risks

1. **Incomplete Lists**: If an autonomous system creates a member-of-as-set object but omits a legitimate AS-SET, their routes may be incorrectly filtered.
2. **Malicious Inclusion**: A determined attacker can still create false member-of-as-set objects if they compromise authentication credentials.
3. **Not Real-time**: Member-of-as-set verification occurs during filter generation, not during BGP operation.
4. **Database Proliferation**: With multiple IRR databases, inconsistent objects across databases may create confusion.

### 6.4 Best Practices

1. **Strong Authentication**: Protect maintainer credentials used to modify member-of-as-set objects.
2. **Regular Auditing**: Monitor AS-SET expansions and investigate unexpected pruned autonomous systems.
3. **Automation**: Use automated tools to generate and update member-of-as-set objects.
4. **Documentation**: Maintain clear documentation of AS-SET relationships.

---

## 7. IANA Considerations

### 7.1 RPSL Object Type Registration

IANA is requested to register the member-of-as-set object type in the RPSL Object Types registry.

Registry Name: RPSL Object Types

Registry Entry:
- Object Type: member-of-as-set
- Description: Membership declaration for AS-SET objects
- Reference: This document
- Status: Current

### 7.2 RPSL Attribute Registration

IANA is requested to register the member-of-as-set attribute in the RPSL Attributes registry.

Registry Name: RPSL Attributes

Registry Entry:
- Attribute Name: member-of-as-set
- Description: Specifies AS-SETs in which the autonomous system declares membership
- Object Types: member-of-as-set
- Reference: This document
- Status: Current

---

## 8. References

### 8.1 Normative References

[RFC2119] Bradner, S., Key words for use in RFCs to Indicate Requirement Levels, BCP 14, RFC 2119, DOI 10.17487/RFC2119, March 1997.

[RFC2622] Alaettinoglu, C., et al., Routing Policy Specification Language (RPSL), RFC 2622, DOI 10.17487/RFC2622, June 1999.

[RFC2726] Blunk, L. and J. Damas, PGP Authentication for RIPE Database Updates, RFC 2726, DOI 10.17487/RFC2726, December 1999.

[RFC8174] Leiba, B., Ambiguity of Uppercase vs Lowercase in RFC 2119 Key Words, BCP 14, RFC 8174, DOI 10.17487/RFC8174, May 2017.

### 8.2 Informative References

[RFC6480] Lepinski, M. and S. Kent, An Infrastructure to Support Secure Internet Routing, RFC 6480, DOI 10.17487/RFC6480, February 2012.

[RFC6482] Lepinski, M., Kent, S., and M. Kong, A Profile for Route Origin Authorizations (ROAs), RFC 6482, DOI 10.17487/RFC6482, February 2012.

[RFC7682] Resnick, P., Ed., Considerations for Internet Routing Registries (IRRs) and Routing Policy Configuration, RFC 7682, DOI 10.17487/RFC7682, October 2015.

[RFC8205] Haq, T., Ed., et al., BGPsec Protocol Specification, RFC 8205, DOI 10.17487/RFC8205, September 2017.

[RFC8210] Bush, R. and R. Austein, The Resource Public Key Infrastructure (RPKI) to Router Protocol, Version 1, RFC 8210, DOI 10.17487/RFC8210, September 2017.

[RFC9582] Gagliano, R., Ed., and S. Kent, A Profile for Route Origin Authorizations (ROAs), RFC 9582, DOI 10.17487/RFC9582, April 2024.

[RFC9595] Weber, K., Ed., BGP AS_PATH Verification Using Autonomous System Provider Authorization (ASPA), RFC 9595, DOI 10.17487/RFC9595, May 2024.

---

## Acknowledgments

The authors thank the members of the #networker IRC community for discussions that led to this proposal. Particular thanks to Nick Hilliard for questions regarding the authentication model and Mikael Abrahamsson for clarifying questions about deployment implications.

---

## Authors Addresses

Saku Ytti
NTT Communications Corporation
Email: saku@ytti.cy

---

## Appendix A. Example Objects and Usage

### A.1 Example member-of-as-set Object

The following example shows a member-of-as-set object for autonomous system AS65001:

```
member-of-as-set:   AS-EXAMPLE-TRANSIT AS-EXAMPLE-PEERING
admin-c:            EXAMPLE-ADMIN
tech-c:             EXAMPLE-TECH
mnt-by:             MNT-EXAMPLE
source:             EXAMPLE
```

This object declares that AS65001 authorizes inclusion in the AS-SETs AS-EXAMPLE-TRANSIT and AS-EXAMPLE-PEERING.

### A.2 Example AS-SET Expansion with Verification

Consider the following AS-SET:

```
as-set:             AS-EXAMPLE-TRANSIT
members:            AS65001, AS65002, AS65003
mnt-by:             MNT-TRANSIT
source:             EXAMPLE
```

And the following member-of-as-set objects:

```
member-of-as-set:   AS-EXAMPLE-TRANSIT
admin-c:            ADMIN-65001
tech-c:             TECH-65001
mnt-by:             MNT-65001
source:             EXAMPLE

member-of-as-set:   AS-EXAMPLE-TRANSIT AS-OTHER-SET
admin-c:            ADMIN-65002
tech-c:             TECH-65002
mnt-by:             MNT-65002
source:             EXAMPLE
```

When expanding AS-EXAMPLE-TRANSIT with member-of-as-set verification enabled:
- AS65001 is included (has member-of-as-set listing AS-EXAMPLE-TRANSIT)
- AS65002 is included (has member-of-as-set listing AS-EXAMPLE-TRANSIT)
- AS65003 is included (no member-of-as-set object exists)

### A.3 Example bgpq4 Usage

The following example shows bgpq4 usage with member-of-as-set verification:

```bash
# Generate prefix list with member-of-as-set verification
bgpq4 --verify-member-of-as-set -S RIPE AS-EXAMPLE-TRANSIT

# Generate AS path filter with member-of-as-set verification
bgpq4 --verify-member-of-as-set -A -S RIPE AS-EXAMPLE-TRANSIT

# Disable verification (default behavior)
bgpq4 --no-verify-member-of-as-set -S RIPE AS-EXAMPLE-TRANSIT
```

---

## Appendix B. Comparison with ASPA

### B.1 Overview

Autonomous System Provider Authorization (ASPA) [RFC9595] provides a mechanism for autonomous systems to register their provider-customer relationships in the RPKI. This appendix compares ASPA with the member-of-as-set mechanism.

### B.2 Technical Comparison

| Aspect | member-of-as-set | ASPA |
|--------|-----------------|------|
| Infrastructure | IRR databases | RPKI (cryptographically signed) |
| Relationship Type | AS-SET membership | Provider-customer |
| Deployment Complexity | Low (new IRR object) | High (requires RPKI deployment) |
| Security Level | Moderate (IRR authentication) | High (cryptographic) |
| Real-time Validation | No (filter generation time) | Yes (BGP operation) |
| Path Validation | AS-SET scope only | Full provider chain |
| Tool Support | bgpq4 and similar | Router implementations |

### B.3 Complementary Use

Member-of-as-set and ASPA serve different deployment scenarios:

- **Member-of-as-set**: Suitable for immediate deployment, provides AS-SET hygiene, works with existing IRR infrastructure.
- **ASPA**: Provides stronger security guarantees but requires RPKI infrastructure and router support.

Networks SHOULD deploy both mechanisms where feasible, using member-of-as-set as an immediate improvement and ASPA for long-term security architecture.
