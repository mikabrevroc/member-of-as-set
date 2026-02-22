# member-of-as-set Implementation Guide

Based on POC experience with real IRR data and tools.

---

## Lessons Learned from POC

### 1. IRR Source Selection is Critical

**Finding**: Not all AS-SETs exist in all IRR databases.

**Example**: 
- AS-NTT exists in RIPE (4 members) but this is xTom (AS9312), not NTT
- Real NTT uses `AS2914:AS-GLOBAL` in NTTCOM database
- AS-LUMEN in RADB is owned by xTom, not the real Lumen

**Recommendation**: 
- Query multiple IRR sources: `RIPE,ARIN,APNIC,NTTCOM,RADB`
- Check `source:` attribute in whois responses
- Be aware of "squatted" AS-SET names

### 2. Hierarchical AS-SET Names

**Finding**: Tier-1s use colon-prefixed AS-SETs (RPSL hierarchical names).

**Examples**:
```
AS2914:AS-GLOBAL      (NTT Global)
AS2914:AS-US          (NTT US customers)
AS2914:AS-EUROPE      (NTT Europe customers)
```

**Implementation**:
```bash
# Query with colon-prefixed names
bgpq4 -S RIPE,NTTCOM "AS2914:AS-GLOBAL"
```

### 3. Tool Integration

**Finding**: Can implement without modifying bgpq4/IRRd.

**Approach**:
1. Expand AS-SET with bgpq4
2. For each ASN, query member-of-as-set
3. Filter results
4. Generate config

**Example wrapper**:
```bash
#!/bin/bash
ASSET="$1"
SOURCE="${2:-RIPE,ARIN,APNIC}"

# Step 1: Expand AS-SET
ASNS=$(bgpq4 -S "$SOURCE" -t "$ASSET" | grep '^AS' | sed 's/^AS//')

# Step 2: Verify each ASN
for asn in $ASNS; do
    member_sets=$(whois -h whois.ripe.net \
        "member-of-as-set AS${asn}" 2>/dev/null | \
        grep '^member-of-as-set:' | \
        awk '{print $2}')
    
    if [ -n "$member_sets" ] && \
       ! echo "$member_sets" | grep -qw "$ASSET"; then
        echo "# PRUNED: AS${asn} not authorized for $ASSET" >&2
        continue
    fi
    
    echo "AS${asn}"
done
```

---

## Juniper Configuration Examples

### AS-Path Filtering (Recommended)

```junos
# Generate with: bgpq4-member-verify -J AS-NTT-CUSTOMERS
policy-options {
    as-path AS-PATH-NTT-CUSTOMERS "^(64496|64497|64498|64499)$";
    
    policy-statement FILTER-NTT-CUSTOMERS {
        term ACCEPT-VALID {
            from as-path AS-PATH-NTT-CUSTOMERS;
            then accept;
        }
        then reject;
    }
}

# Apply to BGP group
protocols {
    bgp {
        group CUSTOMERS {
            import FILTER-NTT-CUSTOMERS;
        }
    }
}
```

### Prefix-List Filtering (Traditional)

```junos
# Generate with: bgpq4-member-verify -P AS-NTT-CUSTOMERS
policy-options {
    prefix-list PREFIX-LIST-NTT-CUSTOMERS {
        192.0.2.0/24;
        198.51.100.0/24;
        203.0.113.0/24;
    }
    
    policy-statement FILTER-NTT-PREFIXES {
        term ACCEPT-VALID {
            from {
                prefix-list PREFIX-LIST-NTT-CUSTOMERS;
            }
            then accept;
        }
        then reject;
    }
}
```

---

## Troubleshooting

### Issue: No member-of-as-set objects found

**Solution**: Backward compatibility mode. ASNs without objects are accepted.

### Issue: AS-SET not found

**Solution**: Try multiple IRR sources:
```bash
bgpq4 -S RIPE,ARIN,APNIC,NTTCOM,RADB AS-EXAMPLE
```

### Issue: Hierarchical AS-SET names (with colons)

**Solution**: Quote the name:
```bash
bgpq4 -S NTTCOM "AS2914:AS-GLOBAL"
```

---

## References

- POC Code: `/poc/` directory
- bgpq4: https://github.com/bgp/bgpq4
- IRRd: https://github.com/irrdnet/irrd
- RFC Document: `draft-carbonara-irr-member-of-as-set-00.xml`
