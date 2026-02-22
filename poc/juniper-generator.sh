#!/bin/bash
#
# juniper-generator.sh - Generate Juniper configuration
# Supports both AS-path filters and prefix-lists
#
# Usage: ./juniper-generator.sh [-t type] <AS-SET-NAME> [items...]
#   -t as-path    Generate AS-path filter (default)
#   -t prefix     Generate prefix-list
#
# Example:
#   ./juniper-generator.sh AS-NTT-CUSTOMERS AS64496 AS64497
#   ./juniper-generator.sh AS-MALICIOUS-CUSTOMER AS64496 AS15169

generate_as_path() {
    local name="$1"
    shift
    local asns=("$@")
    
    if [ ${#asns[@]} -eq 0 ]; then
        echo "Error: No ASNs provided" >&2
        return 1
    fi
    
    # Build AS-path regex
    local as_path_regex="^("
    local first=true
    
    for asn in "${asns[@]}"; do
        if [ "$first" = true ]; then
            first=false
        else
            as_path_regex="${as_path_regex}|"
        fi
        as_path_regex="${as_path_regex}${asn}"
    done
    
    as_path_regex="${as_path_regex})$"
    
    # Generate Juniper config snippet
    echo "policy-options {"
    echo "    as-path AS-PATH-${name} \"${as_path_regex}\";"
    echo "}"
}

generate_prefix_list() {
    local name="$1"
    shift
    local prefixes=("$@")
    
    if [ ${#prefixes[@]} -eq 0 ]; then
        echo "Error: No prefixes provided" >&2
        return 1
    fi
    
    # Generate Juniper prefix-list
    echo "policy-options {"
    echo "    prefix-list PREFIX-LIST-${name} {"
    for prefix in "${prefixes[@]}"; do
        echo "        ${prefix};"
    done
    echo "    }"
    echo "}"
}

# Main
TYPE="as-path"
while getopts "t:" opt; do
    case $opt in
        t) TYPE="$OPTARG" ;;
        *) echo "Usage: $0 [-t as-path|prefix] <name> <item> [item2] ..." >&2; exit 1 ;;
    esac
done
shift $((OPTIND-1))

if [ $# -lt 2 ]; then
    echo "Usage: $0 [-t as-path|prefix] <name> <item> [item2] ..." >&2
    echo "Examples:" >&2
    echo "  $0 AS-NTT 64496 64497 64498                    # AS-path" >&2
    echo "  $0 -t prefix AS-NTT 192.0.2.0/24 198.51.100.0/24 # Prefix-list" >&2
    exit 1
fi

NAME="$1"
shift

case "$TYPE" in
    as-path) generate_as_path "$NAME" "$@" ;;
    prefix) generate_prefix_list "$NAME" "$@" ;;
    *) echo "Error: Unknown type '$TYPE'. Use 'as-path' or 'prefix'." >&2; exit 1 ;;
esac
