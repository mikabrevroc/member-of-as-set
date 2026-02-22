#!/bin/bash
#
# demo.sh - Demonstrate member-of-as-set proposal
#
# This script simulates a tier-1 provider (NTT) using AS-SET expansion
# with and without member-of-as-set verification.

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
# SCENARIO 2: Malicious Customer with Tier-1 AS-SET
# ===========================================================================
echo ""
echo "======================================================================="
echo "SCENARIO 2: Malicious Customer with AS2914:AS-GLOBAL (NTT's customer AS-SET)"
echo "======================================================================="
echo ""
echo "AS-SET: AS-MALICIOUS-CUSTOMER"
echo "Members: AS64496-64499 (legitimate) + AS2914:AS-GLOBAL (NTT's global AS-SET)"
echo ""
echo "Attack: Customer adds NTT's global AS-SET"
echo "        This would leak all NTT customer routes to the attacker's peers!"
echo ""

# Without verification
echo "--- WITHOUT member-of-as-set verification ---"
echo "AS-path filter would accept: AS64496|AS64497|AS64498|AS64499|AS2914:AS-GLOBAL"
echo "Prefix-list would include: All NTT customer prefixes"
echo ""
echo "Result: MASSIVE ROUTE LEAK - Attackers could announce NTT customer prefixes!"
echo ""

# With verification
echo "--- WITH member-of-as-set verification ---"
echo "Checking AS2914:AS-GLOBAL authorization..."
echo ""
echo "AS2914 (NTT): member-of-as-set = AS2914:AS-GLOBAL ✓"
echo "AS2914 has authorized inclusion in AS2914:AS-GLOBAL only"
echo ""
echo "Result: AS2914:AS-GLOBAL PRUNED from AS-MALICIOUS-CUSTOMER"
echo "        Filter only allows: AS64496-64499 (legitimate customers)"
echo "        Prevented leak of NTT customer routes!"
echo ""

# ===========================================================================
# SCENARIO 3: Content Provider Protection (Google, Amazon, Microsoft)
# ===========================================================================
echo ""
echo "======================================================================="
echo "SCENARIO 3: Content Provider Protection"
echo "======================================================================="
echo ""
echo "Scenario: Malicious customer adds Google, Amazon, Microsoft AS-SETs"
echo ""

# Without verification
echo "--- WITHOUT verification ---"
echo "AS-path would allow: AS-GOOGLE|AS-AMAZON|AS-MICROSOFT"
echo "Result: Content provider traffic could be intercepted"
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
# SCENARIO 4: AS3245 - Real-World Example of Unauthorized Inclusion
# ===========================================================================
echo ""
echo "======================================================================="
echo "SCENARIO 4: AS3245 (Sofia University) - Real-World Opt-Out Example"
echo "======================================================================="
echo ""
echo "Real Example from AS-HURRICANE (RADB):"
echo "  AS3245 (Sofia University, Bulgaria) is currently a member of AS-HURRICANE"
echo "  This means their routes could be announced via Hurricane Electric"
echo ""
echo "BEFORE member-of-as-set:"
echo "  - AS3245 appears in AS-HURRICANE expansion"
echo "  - Their routes can leak globally via HE"
echo "  - No way to prevent unauthorized inclusion"
echo ""
echo "AFTER member-of-as-set (AS3245 creates object):"
echo "  member-of-as-set: AS3245:LOCAL-PEERING"
echo "  (NOT AS-HURRICANE - they only authorize local peering)"
echo ""
echo "  - AS3245 PRUNED from AS-HURRICANE expansion"
echo "  - Their routes no longer leak via HE"
echo "  - AS3245 maintains control of their routing policy"
echo ""
echo "Result: AS3245 successfully opts out of AS-HURRICANE"
echo "        This is exactly what member-of-as-set enables!"

# ===========================================================================
# COMPARISON: AS-Path vs Prefix-List Filtering
# ===========================================================================
echo ""
echo "======================================================================="
echo "COMPARISON: AS-Path vs Prefix-List Filtering"
echo "======================================================================="
echo ""

echo "WITHOUT member-of-as-set:"
echo "  - Any AS-SET/ASN can be added without authorization"
echo "  - Malicious customers can add tier-1 AS-SETs"
echo "  - No protection against route leaks"
echo ""
echo "WITH member-of-as-set:"
echo "  - Tier-1 AS-SETs must authorize each inclusion"
echo "  - Unauthorized AS-SETs are pruned during expansion"
echo "  - Backward compatible: ASNs without objects still work"
echo ""

echo "Juniper AS-path filter (SECURE):"
./juniper-generator.sh AS-NTT-CUSTOMERS-SECURE 64496 64497 64498 64499
echo ""

# ===========================================================================
# Summary
# ===========================================================================
echo ""
echo "======================================================================="
echo "SUMMARY"
echo "======================================================================="
echo ""
echo "WITHOUT member-of-as-set:"
echo "  - Any ASN/AS-SET can be added without authorization"
echo "  - Malicious customers can add tier-1 AS-SETs (AS2914:AS-GLOBAL, etc.)"
echo "  - No protection against massive route leaks"
echo ""
echo "WITH member-of-as-set:"
echo "  - Tier-1 AS-SETs must authorize each AS-SET inclusion"
echo "  - Unauthorized AS-SETs (like AS2914:AS-GLOBAL) are pruned"
echo "  - Prevents catastrophic route leaks"
echo "  - Backward compatible: ASNs without objects still work"
echo ""
echo "Critical Protection:"
echo "  - AS2914:AS-GLOBAL (NTT customers) protected from hijacking"
echo "  - AS-HURRICANE (Hurricane Electric) protected"
echo "  - AS-AMAZON (Amazon/AWS) protected"
echo "  - AS-GOOGLE (Google) protected"
echo "======================================================================="
