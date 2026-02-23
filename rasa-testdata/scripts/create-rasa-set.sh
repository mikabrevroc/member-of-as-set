#!/bin/bash
# Create signed RASA-SET object
# Example: ./create-rasa-set.sh AS2914:AS-GLOBAL 2914 "64496 64497"

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"

if [ $# -lt 3 ]; then
    echo "Usage: $0 <as-set-name> <containing-as> <member-asns>"
    echo "Example: $0 AS2914:AS-GLOBAL 2914 \"64496 64497\""
    exit 1
fi

AS_SET_NAME="$1"
CONTAINING_AS="$2"
MEMBERS="$3"
OUTPUT="${4:-$BASE_DIR/objects/${AS_SET_NAME//:/_}.rasa-set.cms}"

# Convert space-separated members to array for ASN.1 encoding
MEMBER_ARRAY=""
for asn in $MEMBERS; do
    MEMBER_ARRAY="${MEMBER_ARRAY}${asn},"
done
MEMBER_ARRAY="${MEMBER_ARRAY%,}"

echo "Creating RASA-SET: $AS_SET_NAME"
echo "  Containing AS: $CONTAINING_AS"
echo "  Members: $MEMBERS"

# Create DER content (simplified - use asn1c generated code in real version)
# For now, create a placeholder that represents the structure
CONTENT_FILE=$(mktemp)
echo "RASA-SET|$AS_SET_NAME|$CONTAINING_AS|$MEMBER_ARRAY" > "$CONTENT_FILE"

# Sign with AS-SET owner's certificate
openssl cms -sign \
    -in "$CONTENT_FILE" \
    -out "$OUTPUT" \
    -signer "$BASE_DIR/ca/AS2914.crt" \
    -inkey "$BASE_DIR/ca/AS2914.key" \
    -outform DER \
    -nodetach

rm "$CONTENT_FILE"

echo "Created: $OUTPUT"
