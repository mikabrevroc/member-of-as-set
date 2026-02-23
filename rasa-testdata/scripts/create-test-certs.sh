#!/bin/bash
# Create self-signed test certificates for RASA testing
# These can be used with rpki-client by adding the test CA to TALs

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"
CA_DIR="$BASE_DIR/ca"

mkdir -p "$CA_DIR"

echo "=== Creating Test CA for RASA ==="

# Create root CA key and self-signed certificate
echo "1. Creating Root CA..."
openssl genrsa -out "$CA_DIR/root.key" 2048 2>/dev/null
openssl req -x509 -new -key "$CA_DIR/root.key" \
    -out "$CA_DIR/root.crt" \
    -days 3650 \
    -subj "/C=US/O=Test RPKI/CN=Test Root CA" \
    -config <(cat <<EOF
[req]
distinguished_name = req_distinguished_name
x509_extensions = v3_ca
[req_distinguished_name]
[v3_ca]
basicConstraints = critical, CA:TRUE
keyUsage = critical, keyCertSign, cRLSign
EOF
)

# Extract public key for TAL
echo "2. Creating TAL file..."
openssl x509 -in "$CA_DIR/root.crt" -pubkey -noout > "$CA_DIR/root.pub"

# Create EE certificate for AS64496
echo "3. Creating EE cert for AS64496..."
openssl genrsa -out "$CA_DIR/AS64496.key" 2048 2>/dev/null
openssl req -new -key "$CA_DIR/AS64496.key" \
    -out "$CA_DIR/AS64496.csr" \
    -subj "/C=US/O=Test/CN=AS64496"

openssl x509 -req -in "$CA_DIR/AS64496.csr" \
    -CA "$CA_DIR/root.crt" -CAkey "$CA_DIR/root.key" \
    -CAcreateserial -out "$CA_DIR/AS64496.crt" \
    -days 365 \
    -extfile <(cat <<EOF
basicConstraints = CA:FALSE
keyUsage = critical, digitalSignature
subjectAltName = @alt_names
[alt_names]
otherName.1 = 1.3.6.1.5.5.7.8.10;UTF8:AS64496
EOF
)

# Create EE certificate for AS15169
echo "4. Creating EE cert for AS15169..."
openssl genrsa -out "$CA_DIR/AS15169.key" 2048 2>/dev/null
openssl req -new -key "$CA_DIR/AS15169.key" \
    -out "$CA_DIR/AS15169.csr" \
    -subj "/C=US/O=Test/CN=AS15169"

openssl x509 -req -in "$CA_DIR/AS15169.csr" \
    -CA "$CA_DIR/root.crt" -CAkey "$CA_DIR/root.key" \
    -CAcreateserial -out "$CA_DIR/AS15169.crt" \
    -days 365 \
    -extfile <(cat <<EOF
basicConstraints = CA:FALSE
subjectAltName = @alt_names
[alt_names]
otherName.1 = 1.3.6.1.5.5.7.8.10;UTF8:AS15169
EOF
)

# Create EE certificate for AS2914
echo "5. Creating EE cert for AS2914..."
openssl genrsa -out "$CA_DIR/AS2914.key" 2048 2>/dev/null
openssl req -new -key "$CA_DIR/AS2914.key" \
    -out "$CA_DIR/AS2914.csr" \
    -subj "/C=US/O=Test/CN=AS2914"

openssl x509 -req -in "$CA_DIR/AS2914.csr" \
    -CA "$CA_DIR/root.crt" -CAkey "$CA_DIR/root.key" \
    -CAcreateserial -out "$CA_DIR/AS2914.crt" \
    -days 365 \
    -extfile <(cat <<EOF
basicConstraints = CA:FALSE
subjectAltName = @alt_names
[alt_names]
otherName.1 = 1.3.6.1.5.5.7.8.10;UTF8:AS2914
EOF
)

# Create TAL file for rpki-client
echo "6. Creating TAL file for rpki-client..."
cat > "$CA_DIR/test.tal" <<EOF
https://localhost/test-ca/root.crt

$(openssl x509 -in "$CA_DIR/root.crt" -pubkey -noout | grep -v "^-----" | tr -d '\n')
EOF

echo ""
echo "=== Test CA Created ==="
echo "Root CA: $CA_DIR/root.crt"
echo "TAL:     $CA_DIR/test.tal"
echo ""
echo "EE Certificates:"
echo "  AS64496: $CA_DIR/AS64496.crt"
echo "  AS15169: $CA_DIR/AS15169.crt"
echo "  AS2914:  $CA_DIR/AS2914.crt"
echo ""
echo "To use with rpki-client:"
echo "  rpki-client -t $CA_DIR/test.tal -c /tmp/rpki-cache ..."
