# Technical Specification Questions - member-of-as-set

## Critical Unanswered Questions for IRR Implementation

### 1. Object Lookup/Query Format
**Question**: How is this object queried via whois/IRR tools?

**Specific concerns**:
- `whois -h whois.ripe.net "member-of-as-set AS3245"` ?
- `whois -h whois.ripe.net "AS3245"` (conflicts with aut-num lookup)
- Need unique primary key that doesn't collide with existing objects
- How to distinguish member-of-as-set from aut-num in query results?

**Research needed**:
- How do other RPSL objects handle lookup (route, route6, as-block)?
- What is the standard primary key format for RPSL objects?
- How do IRR tools handle object type disambiguation?

---

### 2. Primary Key Structure
**Question**: What is the exact primary key format?

**Specific concerns**:
- Is the key the ASN itself (AS3245) or qualified (member-of-as-set:AS3245)?
- How to prevent collision with aut-num object for same ASN?
- Can multiple member-of-as-set objects exist for the same ASN?

**Research needed**:
- RFC 2622 primary key definitions for all RPSL objects
- Examples from RIPE/RADB database schemas
- How IRRd handles object uniqueness per type

---

### 3. Relationship to aut-num Object
**Question**: How does this interact with existing aut-num objects?

**Specific concerns**:
- Can an ASN have both aut-num AND member-of-as-set objects?
- Which object "owns" the ASN identity?
- If both exist, which takes precedence for authorization?
- Should member-of-as-set be an attribute within aut-num instead?

**Research needed**:
- RFC 2622 object relationships
- Precedent: aut-num vs as-block objects
- IRR operator preferences (one object vs many)

---

### 4. Uniqueness Constraints
**Question**: How many member-of-as-set objects per ASN?

**Specific concerns**:
- Exactly one per ASN per IRR database?
- Multiple objects allowed with different maintainers (transfer scenarios)?
- If multiple exist, how to merge/resolve conflicts?

**Research needed**:
- RPSL uniqueness model for other objects
- Database-level constraints in IRR implementations
- Multi-object scenarios in existing IRRs

---

### 5. AS-SET Name Format Validation
**Question**: What are the validation rules for AS-SET names?

**Specific concerns**:
- Hierarchical names: `AS2914:AS-GLOBAL` - colon handling?
- Case sensitivity: `AS-HURRICANE` vs `as-hurricane`
- Maximum length limits?
- Character set: ASCII only? Unicode?
- Whitespace handling in lists: `AS-SET1 AS-SET2` vs `AS-SET1,AS-SET2`

**Research needed**:
- RFC 2622 AS-SET name syntax specification
- Existing IRR implementations validation rules
- RPSL parser implementations (IRRd, RIPE whois)

---

### 6. Operational Limits
**Question**: What are the practical limits?

**Specific concerns**:
- Maximum number of AS-SETs per member-of-as-set object?
- Line length limits (RPSL format constraints)?
- Total object size limits?
- Database storage implications?

**Research needed**:
- RPSL line length limits (RFC 2622)
- IRR database size constraints
- Performance impact of large attribute lists

---

### 7. Implementation Requirements
**Question**: What changes are required to IRR software?

**Specific concerns**:
- IRRd version/config requirements
- Database schema changes needed
- Whois query parser modifications
- API changes (REST, NRTM)?
- Migration procedures for operators

**Research needed**:
- IRRd object type registration
- IRRd schema extension mechanism
- RIPE whois object type addition process
- NTTCOM/ARIN implementation specifics

---

### 8. Object Template Format
**Question**: What is the exact RPSL template?

**Specific concerns**:
- All mandatory vs optional attributes
- Attribute ordering requirements
- Inverse key definitions for whois queries
- Default values for optional attributes

**Research needed**:
- RFC 2622 object template format
- Existing object templates (as-set, aut-num, route)
- IRRd template registration format

---

### 9. Authorization Semantics
**Question**: What does authorization actually mean?

**Specific concerns**:
- Authorization for transit? peering? both?
- Does inclusion imply full routing policy acceptance?
- How to handle partial authorization (certain prefixes only)?
- What about downstream ASNs (customer's customers)?

**Research needed**:
- RPSL authorization model
- IRR-based filtering semantics
- Transit vs peering policy distinctions

---

### 10. Backward Compatibility Edge Cases
**Question**: How to handle edge cases?

**Specific concerns**:
- Old tools that don't understand the object type
- What happens if member-of-as-set references non-existent AS-SET?
- Circular references (AS-SET A includes AS-SET B which includes AS-SET A)?
- Orphaned member-of-as-set objects (AS-SET deleted)

**Research needed**:
- RPSL error handling conventions
- IRR validation practices
- Tool compatibility testing approaches

---

## Research Sources to Investigate

1. **RFC 2622** - Routing Policy Specification Language (RPSL)
2. **RFC 4012** - RPSL cryptographic signatures (if applicable)
3. **IRRd source code** - Object type implementation
4. **RIPE whois documentation** - Object type specifications
5. **RADB documentation** - AS-SET handling specifics
6. **NTTCOM whois implementation** - Hierarchical AS-SET support
7. **bgpq4 source code** - AS-SET expansion logic
8. **IRR operator mailing lists** - Real-world constraints

---

## Proposed Investigation Plan

1. Read RFC 2622 object specification section thoroughly
2. Examine IRRd source for object type patterns
3. Query actual IRRs for object templates
4. Review existing RPSL object RFCs for format precedent
5. Document findings with specific examples
6. Propose specification text for each question
