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

### 3. AS-SET Size Variations

**CRITICAL FINDING**: AS-SET sizes vary by orders of magnitude!

**Real-world sizes** (from POC queries):
| AS-SET | Provider | Prefixes | Risk |
|--------|----------|----------|------|
| **AS-HURRICANE** | Hurricane Electric | **411,327** | **CATASTROPHIC** |
| **AS-AMAZON** | Amazon | **18,547** | **MAJOR** |
| **AS-GOOGLE** | Google | **7,259** | **SIGNIFICANT** |
| AS-HETZNER | Hetzner | 4,804 | Large |
| AS-MICROSOFT | Microsoft | 1,406 | Medium |
| AS1299 | Arelion | 623 | Medium |
| AS-FACEBOOK | Meta | 541 | Medium |
| AS2914 | NTT | 589 | Medium |
| AS-NFLX | Netflix | 67 | Small |

**Key Insight**: Individual ASNs (AS15169) have few prefixes, but AS-SETs (AS-GOOGLE) contain thousands!

**Implication**: 
- Large AS-SETs (4000+ prefixes) need efficient caching
- **AS-HURRICANE at 411K prefixes is a critical protection target**
- Single malicious AS-SET inclusion could leak 400K+ prefixes

**Finding**: IRR data != reality

**Example**:
- Google (AS15169): Only 3-5 prefixes in IRR
- Reality: Google has thousands of prefixes

**Implication**: 
- IRR-based filtering is incomplete
- member-of-as-set complements (doesn't replace) RPKI
- Don't rely solely on IRR for prefix counts

### 4. Tool Integration

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

## Implementation Recommendations

### Phase 1: Tool Development (Week 1-2)

Create `bgpq4-member-verify` wrapper:

```bash
# Features needed:
# - Cache member-of-as-set queries
# - Support multiple IRR sources
# - Generate both AS-path and prefix-list
# - Configurable verification strictness
```

### Phase 2: Pilot with Large ASNs (Week 3-4)

Target ASNs for early adoption:
- Google (AS15169)
- Microsoft (AS8075)
- AWS (AS16509)
- Netflix (AS2906)

These create `member-of-as-set` listing their authorized transit providers.

### Phase 3: Transit Provider Rollout (Month 2-3)

Enable verification on customer-facing sessions:
1. NTT (AS2914)
2. Arelion (AS1299)
3. Level3 (AS3356)
4. Cogent (AS174)

### Phase 4: Automation (Month 4+)

Automated monitoring:
- Daily scans for unauthorized ASNs in AS-SETs
- Email alerts to AS-SET maintainers
- Dashboard showing verification statistics

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

## Monitoring and Alerting

### Daily Checks

```bash
#!/bin/bash
# check-as-set-hygiene.sh

# Find AS-SETs with prunable ASNs
for asset in AS-NTT-CUSTOMERS AS-ARELION-CUSTOMERS; do
    echo "Checking $asset..."
    bgpq4-member-verify -v "$asset" 2>&1 | grep "PRUNED"
done
```

### Alert Criteria

- Any AS-SET with >5% pruned ASNs
- Unauthorized tier-1 ASN in customer AS-SET
- Rapid changes in member-of-as-set objects

---

## References

- POC Code: `/poc/` directory
- bgpq4: https://github.com/bgp/bgpq4
- IRRd: https://github.com/irrdnet/irrd
- RFC Document: `draft-carbonara-irr-member-of-as-set-00.xml`
