#!/bin/bash
# Create signed RASA-AUTH object
# Example: ./create-rasa-auth.sh 64496 AS2914:AS-GLOBAL

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"

if [ $# -lt 2 ]; then
    echo "Usage: $0 <asn> <authorized-in-asset>"
    echo "Example: $0 64496 AS2914:AS-GLOBAL"
    exit 1
fi

ASN="$1"
ASSET="$2"
OUTPUT="${3:-$BASE_DIR/objects/AS${ASN}.rasa-auth.cms}"

echo "Creating RASA-AUTH: AS$ASN"
echo "  Authorized in: $ASSET"

CONTENT_FILE=$(mktemp)
echo "RASA-AUTH|$ASN|$ASSET" > "$CONTENT_FILE"

openssl cms -sign \
    -in "$CONTENT_FILE" \
    -out "$OUTPUT" \
    -signer "$BASE_DIR/ca/AS${ASN}.crt" \
    -inkey "$BASE_DIR/ca/AS${ASN}.key" \
    -outform DER \
    -nodetach

rm "$CONTENT_FILE"

echo "Created: $OUTPUT"
