#!/bin/bash
#
# as-set-expander.sh - Expand AS-SET with member-of-as-set verification
#
# Usage: ./as-set-expander.sh [-v] <AS-SET-NAME>
#   -v  Enable member-of-as-set verification (prune unauthorized ASNs)
#
# Example:
#   ./as-set-expander.sh AS-NTT-CUSTOMERS          # Without verification
#   ./as-set-expander.sh -v AS-NTT-CUSTOMERS       # With verification

set -e

# Configuration
MEMBER_DB="${MEMBER_DB:-simulated-irr/member-of-as-set.db}"
IRR_SOURCES="${IRR_SOURCES:-RIPE,ARIN,APNIC,RADB}"

# Parse arguments
VERIFY=false
while getopts "v" opt; do
    case $opt in
        v) VERIFY=true ;;
        *) echo "Usage: $0 [-v] <AS-SET-NAME>" >&2; exit 1 ;;
    esac
done
shift $((OPTIND-1))

ASSET="${1:-AS-NTT-CUSTOMERS}"

if [ -z "$ASSET" ]; then
    echo "Error: No AS-SET specified" >&2
    echo "Usage: $0 [-v] <AS-SET-NAME>" >&2
    exit 1
fi

echo "=========================================="
echo "AS-SET Expansion: $ASSET"
echo "Verification: $VERIFY"
echo "=========================================="
echo ""

# Function to check if ASN is authorized for this AS-SET
check_authorization() {
    local asn="$1"
    local asset="$2"
    
    # If verification is disabled, always authorize
    if [ "$VERIFY" != "true" ]; then
        return 0
    fi
    
    # Check if ASN exists in member-of-as-set database
    local entry
    entry=$(grep "^${asn}|" "$MEMBER_DB" 2>/dev/null || true)
    
    if [ -z "$entry" ]; then
        # No member-of-as-set object exists - backward compatibility
        return 0
    fi
    
    # Extract the AS-SETs this ASN authorizes
    local authorized_sets
    authorized_sets=$(echo "$entry" | cut -d'|' -f2)
    
    # Check if our AS-SET is in the authorized list
    if echo "$authorized_sets" | grep -qw "$asset"; then
        return 0  # Authorized
    else
        return 1  # Not authorized - should be pruned
    fi
}

# Get ASNs from bgpq4 (using -t for asplain output)
echo "Querying IRR for $ASSET..."
ASNS=$(bgpq4 -S "$IRR_SOURCES" -t "$ASSET" 2>/dev/null | grep -E '^AS[0-9]+$' | sed 's/^AS//' || true)

if [ -z "$ASNS" ]; then
    echo "Warning: No ASNs found for $ASSET" >&2
    exit 0
fi

TOTAL=$(echo "$ASNS" | wc -l)
echo "Found $TOTAL ASNs in $ASSET"
echo ""

# Process each ASN
AUTHORIZED=0
PRUNED=0
declare -a PRUNED_LIST
declare -a AUTHORIZED_ASNS

for asn in $ASNS; do
    if check_authorization "$asn" "$ASSET"; then
        AUTHORIZED_ASNS+=("$asn")
        ((AUTHORIZED++))
    else
        PRUNED_LIST+=("$asn")
        ((PRUNED++))
        if [ "$VERIFY" = "true" ]; then
            echo "  [PRUNED] AS$asn - not authorized for $ASSET"
        fi
    fi
done

echo ""
echo "=========================================="
echo "RESULTS:"
echo "=========================================="
echo "Total ASNs in $ASSET: $TOTAL"
echo "Authorized: $AUTHORIZED"
echo "Pruned: $PRUNED"
echo ""

if [ "$VERIFY" = "true" ] && [ $PRUNED -gt 0 ]; then
    echo "Pruned ASNs:"
    for asn in "${PRUNED_LIST[@]}"; do
        # Show what AS-SETs they actually authorize
        entry=$(grep "^${asn}|" "$MEMBER_DB" 2>/dev/null || true)
        if [ -n "$entry" ]; then
            authorized_sets=$(echo "$entry" | cut -d'|' -f2)
            echo "  AS$asn (authorizes: $authorized_sets)"
        fi
    done
    echo ""
fi

# Output authorized ASNs
if [ ${#AUTHORIZED_ASNS[@]} -gt 0 ]; then
    echo "Authorized ASNs:"
    printf '  AS%s\n' "${AUTHORIZED_ASNS[@]}"
fi
