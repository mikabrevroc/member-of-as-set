#!/bin/bash
# Create CMS signed RASA objects for testing with rpki-client
# Uses the test certificates created by create-test-certs.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"
CA_DIR="$BASE_DIR/ca"
OBJECTS_DIR="$BASE_DIR/objects"

echo "=== Creating CMS Signed RASA Objects ==="

# Function to sign a RASA object
sign_rasa() {
    local asn="$1"
    local input_file="$OBJECTS_DIR/${asn}.rasa"
    local output_file="$OBJECTS_DIR/${asn}.rasa.cms"
    local cert_file="$CA_DIR/${asn}.crt"
    local key_file="$CA_DIR/${asn}.key"
    
    if [ ! -f "$input_file" ]; then
        echo "ERROR: Input file not found: $input_file"
        return 1
    fi
    
    if [ ! -f "$cert_file" ]; then
        echo "ERROR: Certificate not found: $cert_file"
        return 1
    fi
    
    echo "Signing $asn..."
    
    # Create CMS signed message
    # -nodetach includes the content in the signed message
    openssl cms -sign \
        -binary \
        -in "$input_file" \
        -out "$output_file" \
        -signer "$cert_file" \
        -inkey "$key_file" \
        -outform DER \
        -nodetach \
        2>&1 || {
            echo "ERROR: Failed to sign $asn"
            return 1
        }
    
    echo "  Created: $output_file ($(stat -f%z "$output_file" 2>/dev/null || stat -c%s "$output_file" 2>/dev/null) bytes)"
}

# Sign each RASA object
sign_rasa "AS64496"
sign_rasa "AS15169"
sign_rasa "AS2914"

echo ""
echo "=== CMS Signed RASA Objects Created ==="
echo "Files in $OBJECTS_DIR:"
ls -lh "$OBJECTS_DIR/"*.rasa.cms 2>/dev/null || echo "No .rasa.cms files found"
echo ""
echo "To verify a signed object:"
echo "  openssl cms -verify -in $OBJECTS_DIR/AS64496.rasa.cms -inform DER -CAfile $CA_DIR/root.crt"
echo ""
echo "To use with rpki-client:"
echo "  rpki-client -t $CA_DIR/test.tal -c /tmp/rpki-cache $OBJECTS_DIR"
