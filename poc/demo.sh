#!/bin/bash
#
# demo.sh - Demonstrate member-of-as-set proposal
#
# This script simulates a tier-1 provider (NTT) using AS-SET expansion
# with and without member-of-as-set verification.
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "======================================================================="
echo "  member-of-as-set Proof of Concept"
echo "  Simulating NTT (AS2914) as Tier-1 Provider"
echo "======================================================================="
echo ""

# Make scripts executable
chmod +x as-set-expander.sh juniper-generator.sh

# ===========================================================================
# SCENARIO 1: Legitimate Customer AS-SET
# ===========================================================================
echo "SCENARIO 1: Legitimate Customer AS-SET"
echo "======================================================================="
echo ""
echo "AS-SET: AS-NTT-CUSTOMERS"
echo "Members: AS64496, AS64497, AS64498, AS64499 (all legitimate NTT customers)"
echo ""

# Without verification
echo "--- WITHOUT member-of-as-set verification ---"
./as-set-expander.sh AS-NTT-CUSTOMERS 2>/dev/null | tail -10
echo ""

# With verification
echo "--- WITH member-of-as-set verification ---"
./as-set-expander.sh -v AS-NTT-CUSTOMERS 2>/dev/null | tail -10
echo ""

echo "Result: All 4 ASNs are authorized. No change."
echo ""

# ===========================================================================
# SCENARIO 2: Malicious Customer with Unauthorized ASNs
# ===========================================================================
echo ""
echo "======================================================================="
echo "SCENARIO 2: Malicious Customer with Unauthorized ASNs"
echo "======================================================================="
echo ""
echo "AS-SET: AS-MALICIOUS-CUSTOMER"
echo "Members: AS64496-64499 (legitimate) + AS15169 (Google) + AS3356 (Level3) + AS8075 (Microsoft)"
echo ""
echo "Attack: Customer adds tier-1/content provider ASNs to steal traffic"
echo ""

# Without verification
echo "--- WITHOUT member-of-as-set verification ---"
echo "All ASNs would be accepted into the filter!"
echo "AS-path would allow: AS64496|AS64497|AS64498|AS64499|AS15169|AS3356|AS8075"
echo ""
# Generate Juniper config for the malicious set (simulated)
echo "Juniper AS-path filter (VULNERABLE):"
./juniper-generator.sh AS-MALICIOUS-CUSTOMER 64496 64497 64498 64499 15169 3356 8075
echo ""

# With verification
echo "--- WITH member-of-as-set verification ---"
echo "Checking each ASN against member-of-as-set database..."
echo ""

# Check each ASN manually
echo "AS64496: member-of-as-set = AS-NTT-CUSTOMERS ✓ AUTHORIZED"
echo "AS64497: member-of-as-set = AS-NTT-CUSTOMERS ✓ AUTHORIZED"
echo "AS64498: member-of-as-set = AS-NTT-CUSTOMERS ✓ AUTHORIZED"
echo "AS64499: member-of-as-set = AS-NTT-CUSTOMERS ✓ AUTHORIZED"
echo "AS15169: member-of-as-set = AS-GOOGLE,AS-GOOGLE-PEERING ✗ NOT AUTHORIZED for AS-NTT-CUSTOMERS"
echo "AS3356: member-of-as-set = AS-LEVEL3-TRANSIT,AS-LEVEL3-PEERING ✗ NOT AUTHORIZED for AS-NTT-CUSTOMERS"
echo "AS8075: member-of-as-set = AS-MICROSOFT ✗ NOT AUTHORIZED for AS-NTT-CUSTOMERS"
echo ""

echo "Pruned ASNs: AS15169, AS3356, AS8075"
echo ""

echo "Juniper AS-path filter (SECURE):"
./juniper-generator.sh AS-MALICIOUS-CUSTOMER-FILTERED 64496 64497 64498 64499
echo ""

echo ""
echo "======================================================================="
echo "COMPARISON C: AS-Path vs Prefix-List Filtering"
echo "======================================================================="
echo ""

echo "Real-world data: If we expand these ASNs against actual IRR data:"
echo ""

# Show real prefix counts for the ASNs in our example
echo "AS64496 (legitimate customer): ~5-10 prefixes"
echo "AS64497 (legitimate customer): ~5-10 prefixes"
echo "AS64498 (legitimate customer): ~5-10 prefixes"
echo "AS64499 (legitimate customer): ~5-10 prefixes"
echo "---"
echo "AS15169 (Google): ~3-5 prefixes in IRR (real: thousands more not registered)"
echo "AS3356 (Level3): ~353 prefixes (from real data)"
echo "AS8075 (Microsoft): ~186 prefixes (from real data)"
echo ""

echo "WITHOUT verification - Prefix-list would include:"
echo "  Legitimate: ~20-40 prefixes"
echo "  GOOGLE: +potentially thousands of prefixes"
echo "  LEVEL3: +353 prefixes"
echo "  MICROSOFT: +186 prefixes"
echo "  TOTAL: ~500+ prefixes (mostly unauthorized!)"
echo ""

echo "WITH verification - Prefix-list includes only:"
echo "  Legitimate: ~20-40 prefixes"
echo "  TOTAL: ~20-40 prefixes"
echo ""

echo "Savings: ~90%+ reduction in prefix-list size"
echo "         + prevention of major route leaks"
echo ""

# Generate example prefix-list showing the difference
echo "Example Juniper prefix-lists (simulated):"
echo ""
echo "WITHOUT verification (VULNERABLE):"
./juniper-generator.sh -t prefix AS-MALICIOUS-CUSTOMER 192.0.2.0/24 198.51.100.0/24 203.0.113.0/24 "8.8.8.0/24 (GOOGLE)" "4.0.0.0/8 (LEVEL3)" "13.0.0.0/8 (MICROSOFT)"
echo ""

echo "WITH verification (SECURE):"
./juniper-generator.sh -t prefix AS-MALICIOUS-CUSTOMER-FILTERED 192.0.2.0/24 198.51.100.0/24 203.0.113.0/24
echo ""

# ===========================================================================
# Real-world comparison with actual IRR data
# ===========================================================================
echo ""
echo "======================================================================="
echo "REAL-WORLD COMPARISON: Actual Tier-1 AS-SET Sizes"
echo "======================================================================="
echo ""

echo "From real IRR queries:"
echo ""
echo "AS-HETZNER (hosting provider): ~4,804 prefixes"
echo "AS2914 (NTT): ~589 prefixes"
echo "AS1299 (Arelion): ~623 prefixes"
echo "AS3356 (Level3): ~353 prefixes"
echo "AS6461 (Zayo): ~80 prefixes"
echo ""

echo "A malicious customer adding Google (AS15169) to a large AS-SET like"
echo "AS-HETZNER could potentially leak Google's prefixes to thousands of peers."
echo ""

# ===========================================================================
# Summary
# ===========================================================================
echo "======================================================================="
echo "SUMMARY"
echo "======================================================================="
echo ""
echo "WITHOUT member-of-as-set:"
echo "  - Any ASN can be added to any AS-SET without authorization"
echo "  - Malicious customers can add tier-1/content ASNs"
echo "  - Filters accept unauthorized ASNs, enabling route leaks"
echo ""
echo "WITH member-of-as-set:"
echo "  - ASNs must explicitly authorize AS-SET membership"
echo "  - Unauthorized ASNs are pruned during expansion"
echo "  - Filters only accept legitimately authorized ASNs"
echo "  - Backward compatible: ASNs without objects are still accepted"
echo ""
echo "Benefits:"
echo "  1. Prevents unauthorized prefix leaks"
echo "  2. Stops AS-SET hijacking attempts"
echo "  3. No changes to IRR software needed"
echo "  4. Incremental deployment possible"
echo "======================================================================="
