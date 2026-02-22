# Technical Specification Answers - member-of-as-set

## CRITICAL FINDING: member-of ALREADY EXISTS in RFC 2622

From RFC 2622 Section 5.1 (as-set class):
> "The mbrs-by-ref attribute is a list of maintainer names or the keyword ANY. If this attribute is used, the AS set also includes ASes whose aut-num objects are registered by one of these maintainers and whose **member-of attribute refers to the name of this AS set**."

**This proposal is actually:**
1. Creating a standalone object type for member-of information (instead of it being an attribute within aut-num)
2. Making verification mandatory rather than optional (mbrs-by-ref based)
3. Extending the semantics to support bidirectional verification

---

## Proposed Answers to Technical Questions

### 1. Object Lookup/Query Format

**Answer**: Use class-qualified lookup: `whois -h whois.ripe.net "member-of-as-set AS3245"`

**Rationale**: 
- RFC 2622 allows querying by object type (class name)
- This follows precedent from other RPSL queries
- Prevents collision with aut-num lookup for same ASN
- IRR tools can disambiguate by object type

**Implementation**:
```
Query: whois -h whois.ripe.net "member-of-as-set AS3245"
Returns: member-of-as-set object for AS3245

Query: whois -h whois.ripe.net "AS3245"
Returns: aut-num object for AS3245 (existing behavior)
```

**Precedent**: route objects use prefix+origin as key. Query: `whois "128.9.0.0/16AS226"`

---

### 2. Primary Key Structure

**Answer**: Primary key is the ASN itself (AS3245), with class name "member-of-as-set"

**RFC 2622 Format**:
```
Attribute          Value                      Type
member-of-as-set   <as-number>                mandatory, single-valued, class key
member-of          list of <as-set-names>     mandatory, multi-valued
mnt-by             list of <mntner-names>     mandatory, multi-valued
admin-c            <nic-handle>               mandatory, multi-valued
tech-c             <nic-handle>               mandatory, multi-valued
source             <registry-name>            mandatory, single-valued
```

**Uniqueness**: 
- Exactly ONE member-of-as-set object per ASN per IRR database
- If multiple submitted, last valid one wins (standard RPSL behavior)
- Object is identified by: (class="member-of-as-set", key="AS3245")

---

### 3. Relationship to aut-num Object

**Answer**: The member-of-as-set object CO-EXISTS with aut-num, but serves a DIFFERENT purpose

**Key Distinction**:
- **aut-num**: Defines routing policy (import/export rules)
- **member-of-as-set**: Declares AS-SET membership authorization ONLY

**Both can exist for same ASN**:
```
aut-num: AS3245                    member-of-as-set: AS3245
as-name: DIGSYS-AS                member-of: AS3245:LOCAL-PEERING
...                               mnt-by: MNTR-SOFIA-UNI
```

**Why separate object instead of aut-num attribute**:
1. **Access control**: Different maintainers may control policy vs membership
2. **Update frequency**: Membership changes more often than routing policy  
3. **Scope separation**: Aut-num is about routing, member-of-as-set is about authorization
4. **Simpler queries**: Can query membership without parsing full aut-num

**Precedent**: person vs role objects - both describe contacts, different use cases

---

### 4. Uniqueness Constraints

**Answer**: One member-of-as-set object per ASN per IRR database

**Constraints**:
```
UNIQUE(class, key) where class="member-of-as-set" and key=<as-number>
```

**Rationale**:
- Matches RFC 2622 model: one object per type per key
- Simplifies lookup and validation
- Prevents conflicting authorizations

**Update Semantics**:
- New submission with same key overwrites existing object
- Maintained by mnt-by attribute (standard RPSL authentication)
- History tracking via changed attribute

---

### 5. AS-SET Name Format Validation

**Answer**: Follow RFC 2622 Section 5 AS-SET naming rules exactly

**Rules** (from RFC 2622):
```
<as-set-name> = "as-" <object-name> | <hierarchical-as-set-name>
<hierarchical-as-set-name> = <as-number> ":" <as-set-name> {":" <as-set-name>}
<object-name> = letter *(letter | digit | "_" | "-") *(letter | digit)
```

**Specifics**:
- **Case**: Case-insensitive (RPSL standard)
- **Max length**: Follow RPSL <object-name> limits (typically 63 chars per component)
- **Character set**: ASCII letters, digits, underscore, hyphen
- **Hierarchical**: Supported via colon separator (AS2914:AS-GLOBAL)
- **Whitespace**: Space-separated list in member-of attribute

**Validation Examples**:
```
VALID:
  AS-HURRICANE
  as-hurricane (case insensitive)
  AS2914:AS-GLOBAL
  AS2914:AS-US:AS-CUSTOMERS

INVALID:
  HURRICANE (no "as-" prefix for flat names)
  as- (too short)
  as-hurricane:extra (hierarchical must start with ASN)
```

---

### 6. Operational Limits

**Answer**: Follow standard RPSL limits

**From RFC 2622**:
- **Line length**: No explicit limit, but implementations typically use 80-255 chars
- **Continuation**: Use + character for multi-line values
- **Attribute count**: No explicit limit
- **Value list length**: Practical limit ~1000 AS-SETs (performance consideration)

**Recommended Limits**:
```
Maximum AS-SETs per member-of-as-set: 1000
Maximum line length: 255 characters
Maximum object size: 64KB
```

**Rationale**: These are consistent with existing IRR implementations and prevent abuse while allowing practical use cases.

---

### 7. Implementation Requirements

**Answer**: IRR software requires object type registration

**IRRd Changes Needed**:
```python
# Add to IRRd object types configuration
OBJECT_TYPES = {
    # ... existing types ...
    'member-of-as-set': {
        'key': ['member-of-as-set'],
        'mandatory': ['member-of-as-set', 'member-of', 'mnt-by', 'admin-c', 'tech-c', 'source'],
        'optional': ['remarks', 'notify'],
        'inverse_keys': ['mnt-by', 'admin-c', 'tech-c'],
        'validators': {
            'member-of-as-set': validate_as_number,
            'member-of': validate_as_set_list,
        }
    }
}
```

**Database Schema**:
```sql
CREATE TABLE member_of_as_set (
    id SERIAL PRIMARY KEY,
    as_number INTEGER UNIQUE NOT NULL,
    member_of TEXT[] NOT NULL,  -- Array of AS-SET names
    mnt_by TEXT[] NOT NULL,
    admin_c TEXT[] NOT NULL,
    tech_c TEXT[] NOT NULL,
    source VARCHAR(255) NOT NULL,
    object_text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_member_of_as_set_as_number ON member_of_as_set(as_number);
CREATE INDEX idx_member_of_as_set_member_of ON member_of_as_set USING GIN(member_of);
```

**API Changes**:
- NRTM (Near Real Time Mirroring): Add member-of-as-set object type
- REST API: Add endpoints for CRUD operations
- Whois: Add class-qualified query support

**Migration**: No migration needed - new object type, backward compatible

---

### 8. Object Template Format

**Answer**: Standard RPSL template with class name as first attribute

**Template**:
```
member-of-as-set: [mandatory] [single] [primary/lookup key]
member-of:        [mandatory] [multiple] 
mnt-by:           [mandatory] [multiple] [inverse key]
admin-c:          [mandatory] [multiple] [inverse key]
tech-c:           [mandatory] [multiple] [inverse key]
remarks:          [optional]  [multiple]
notify:           [optional]  [multiple] [inverse key]
mnt-lower:        [optional]  [multiple] [inverse key]
changed:          [mandatory] [multiple]
source:           [mandatory] [single]
```

**Example Object**:
```
member-of-as-set: AS3245
member-of:        AS3245:LOCAL-PEERING
mnt-by:           MNTR-SOFIA-UNI
admin-c:          DK58
tech-c:           OPS4-RIPE
remarks:          Sofia University only authorizes local peering AS-SET
remarks:          NOT Hurricane Electric or other global AS-SETs
changed:          admin@sofia-uni.bg 20260222
source:           RIPE
```

**Precedent**: Matches aut-num template structure from RFC 2622

---

### 9. Authorization Semantics

**Answer**: Authorization means "this AS consents to being included in these AS-SETs"

**Semantics**:
- **Inclusion in filter**: Authorized AS-SETs include the ASN in expansion
- **NOT routing policy**: Does not imply transit or peering acceptance
- **Separate from aut-num**: Routing policy still defined in aut-num object
- **Direction**: Per-AS authorization (not per-prefix, not per-session)

**Verification Algorithm**:
```
1. Expand AS-SET S to get candidate ASNs
2. For each ASN in candidates:
   a. Query member-of-as-set object for ASN
   b. If no object exists: INCLUDE (backward compatible)
   c. If object exists:
      - Check if S is in member-of attribute
      - If YES: INCLUDE
      - If NO: PRUNE (log reason)
3. Return filtered AS list
```

**Edge Cases**:
- **Downstream ASes**: Not covered - customer must create their own member-of-as-set
- **Partial authorization**: Not supported - all or nothing per AS-SET
- **Hierarchical AS-SETs**: Check authorization at each level

---

### 10. Backward Compatibility Edge Cases

**Answer**: Graceful degradation for all edge cases

**Case 1: Old tools don't understand the object**
```
Solution: Tools ignore unknown object types (standard RPSL behavior)
Result: No change to existing functionality
```

**Case 2: member-of-as-set references non-existent AS-SET**
```
Solution: Valid during creation (AS-SET may be created later)
Verification: At expansion time, if AS-SET doesn't exist, validation passes
(because we only validate that the claimed authorization exists, not that
it's currently being used)
```

**Case 3: Circular AS-SET references**
```
Solution: Use cycle detection during expansion (existing bgpq4/IRRd behavior)
member-of-as-set does not change cycle detection logic
```

**Case 4: Orphaned member-of-as-set (AS-SET deleted)**
```
Solution: Object remains valid; AS simply authorizes inclusion in a non-existent AS-SET
No automatic deletion (maintainer must clean up)
```

**Case 5: Multiple IRR databases**
```
Solution: Each database has its own member-of-as-set objects
Verification considers source: attribute
```

---

## IANA Registration

Per RFC 2622 Section 10 (Extending RPSL):

**IANA Considerations**:
```
IANA is requested to register the member-of-as-set object type
in the RPSL Object Types registry.

Object Type: member-of-as-set
Reference: RFC XXXX (this document)
Contact: IETF GROW Working Group

IANA is requested to register the member-of-as-set attribute
in the RPSL Attributes registry.

Attribute: member-of-as-set
Object Types: member-of-as-set
Reference: RFC XXXX (this document)
```

**New Attribute Registration**:
```
Attribute: member-of (existing, but used in new context)
Object Types: member-of-as-set
Reference: RFC XXXX (this document)
Note: member-of attribute already exists in aut-num objects (RFC 2622)
```

---

## Summary

This proposal creates a **new RPSL object type** (member-of-as-set) that:
1. Separates AS-SET membership authorization from routing policy
2. Enables bidirectional verification during AS-SET expansion
3. Maintains full backward compatibility (opt-in for ASes)
4. Follows existing RPSL conventions and precedents
5. Requires minimal changes to IRR software (object type registration)

The key innovation is making authorization **mandatory** and **verifiable** rather than relying on the optional mbrs-by-ref mechanism.
