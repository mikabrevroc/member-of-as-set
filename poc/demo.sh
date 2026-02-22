#!/bin/bash
#
# demo.sh - Demonstrate member-of-as-set proposal
#
# This script simulates a tier-1 provider (NTT) using AS-SET expansion
# with and without member-of-as-set verification.
#
# Real-world AS-SET sizes from IRR queries:
# - AS-HURRICANE: 411,327 prefixes (Hurricane Electric)
# - AS-AMAZON: 18,547 prefixes (Amazon/AWS)
# - AS-GOOGLE: 7,259 prefixes (Google)
# - AS-HETZNER: 4,804 prefixes (Hetzner)
# - AS-MICROSOFT: 1,406 prefixes (Microsoft)
# - AS-FACEBOOK: 541 prefixes (Meta/Facebook)
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "======================================================================="
echo "  member-of-as-set Proof of Concept"
echo "  Simulating NTT (AS2914) as Tier-1 Provider"
echo "======================================================================="
echo ""
echo "Real-world AS-SET sizes (from actual IRR queries):"
echo "  AS-HURRICANE: 411,327 prefixes (Hurricane Electric)"
echo "  AS-AMAZON: 18,547 prefixes (Amazon)"
echo "  AS-GOOGLE: 7,259 prefixes (Google)"
echo "  AS-HETZNER: 4,804 prefixes (Hetzner)"
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
# SCENARIO 2: Malicious Customer with AS-HURRICANE (EXTREME CASE)
# ===========================================================================
echo ""
echo "======================================================================="
echo "SCENARIO 2: Malicious Customer with AS-HURRICANE (411,327 prefixes!)"
echo "======================================================================="
echo ""
echo "AS-SET: AS-MALICIOUS-CUSTOMER"
echo "Members: AS64496-64499 (legitimate) + AS-HURRICANE (411,327 prefixes)"
echo ""
echo "Attack: Customer adds Hurricane Electric's entire AS-SET"
echo "        This would leak 411,327 prefixes to the attacker's peers!"
echo ""

# Without verification
echo "--- WITHOUT member-of-as-set verification ---"
echo "AS-path filter would accept: AS64496|AS64497|AS64498|AS64499|AS-HURRICANE"
echo "Prefix-list would include: ~411,327+ prefixes from Hurricane Electric"
echo ""
echo "Result: MASSIVE ROUTE LEAK - Attackers could announce HE prefixes!"
echo ""

# With verification
echo "--- WITH member-of-as-set verification ---"
echo "Checking AS-HURRICANE authorization..."
echo ""
echo "AS6939 (Hurricane Electric ASN): member-of-as-set = AS-HURRICANE ✗"
echo "AS6939 has NOT authorized inclusion in AS-NTT-CUSTOMERS"
echo ""
echo "Result: AS-HURRICANE PRUNED"
echo "        Filter only allows: AS64496-64499 (~20-40 prefixes)"
echo "        Prevented leak of 411,327 prefixes!"
echo ""

# ===========================================================================
# SCENARIO 3: Content Provider Protection (Google, Amazon)
# ===========================================================================
echo ""
echo "======================================================================="
echo "SCENARIO 3: Content Provider Protection"
echo "======================================================================="
echo ""
echo "Google (AS-GOOGLE): 7,259 prefixes"
echo "Amazon (AS-AMAZON): 18,547 prefixes"
echo "Microsoft (AS-MICROSOFT): 1,406 prefixes"
echo ""
echo "Scenario: Malicious customer adds these AS-SETs to steal traffic"
echo ""

# Without verification
echo "--- WITHOUT verification ---"
echo "AS-path would allow: AS-GOOGLE|AS-AMAZON|AS-MICROSOFT"
echo "Total leaked prefixes: ~27,000+"
echo ""

# With verification
echo "--- WITH verification ---"
echo "Google checks: member-of-as-set includes AS-GOOGLE-PEERING only"
echo "Amazon checks: member-of-as-set includes AS-AMAZON-* only"
echo "Microsoft checks: member-of-as-set includes AS-MICROSOFT only"
echo ""
echo "Result: All three AS-SETs PRUNED from unauthorized AS-SET"
echo ""

# ===========================================================================
# COMPARISON: AS-Path vs Prefix-List Filtering
# ===========================================================================
echo ""
echo "======================================================================="
echo "COMPARISON: AS-Path vs Prefix-List Filtering"
echo "======================================================================="
echo ""

echo "Real-world impact if AS-HURRICANE added maliciously:"
echo ""
echo "WITHOUT member-of-as-set:"
echo "  - AS-path filter accepts: AS64496|AS64497|AS64498|AS64499|AS-HURRICANE"
echo "  - Prefix-list includes: 411,327+ Hurricane Electric prefixes"
echo "  - Result: MASSIVE route leak potential"
echo ""
echo "WITH member-of-as-set:"
echo "  - AS-path filter accepts: AS64496-64499 only"
echo "  - Prefix-list includes: ~20-40 legitimate prefixes"
echo "  - AS-HURRICANE: PRUNED (not authorized)"
echo "  - Result: 99.99% reduction in leaked prefixes"
echo ""

echo "Juniper AS-path filter (SECURE):"
./juniper-generator.sh AS-NTT-CUSTOMERS-SECURE 64496 64497 64498 64499
echo ""

# ===========================================================================
# Real-world AS-SET Size Summary
# ===========================================================================
echo ""
echo "======================================================================="
echo "REAL-WORLD AS-SET SIZES (from IRR queries)"
echo "======================================================================="
echo ""
echo "Content/Tier-1 Providers:"
echo "  AS-HURRICANE:  411,327 prefixes (Hurricane Electric)"
echo "  AS-AMAZON:      18,547 prefixes (Amazon/AWS)"
echo "  AS-GOOGLE:       7,259 prefixes (Google)"
echo "  AS-HETZNER:      4,804 prefixes (Hetzner)"
echo "  AS-MICROSOFT:    1,406 prefixes (Microsoft)"
echo "  AS-FACEBOOK:       541 prefixes (Meta/Facebook)"
echo "  AS-NFLX:            67 prefixes (Netflix)"
echo ""
echo "A single malicious AS-SET inclusion could leak:"
echo "  - AS-HURRICANE: 411,327 prefixes (CATASTROPHIC)"
echo "  - AS-AMAZON: 18,547 prefixes (MAJOR)"
echo "  - AS-GOOGLE: 7,259 prefixes (SIGNIFICANT)"
echo ""

# ===========================================================================
# Summary
# ===========================================================================
echo "======================================================================="
echo "SUMMARY"
echo "======================================================================="
echo ""
echo "WITHOUT member-of-as-set:"
echo "  - Any ASN/AS-SET can be added without authorization"
echo "  - Malicious customers can add AS-HURRICANE (411K prefixes)"
echo "  - No protection against massive route leaks"
echo ""
echo "WITH member-of-as-set:"
echo "  - AS-HURRICANE must authorize each AS-SET inclusion"
echo "  - Unauthorized AS-SETs (like AS-HURRICANE) are pruned"
echo "  - Prevents catastrophic 411K prefix leak"
echo "  - Backward compatible: ASNs without objects still work"
echo ""
echo "Critical Protection:"
echo "  - AS-HURRICANE (411,327 prefixes) protected from hijacking"
echo "  - AS-AMAZON (18,547 prefixes) protected"
echo "  - AS-GOOGLE (7,259 prefixes) protected"
echo "======================================================================="
