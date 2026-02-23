#!/bin/bash
# Create test CA for RASA development
# Uses openssl CLI - no custom crypto code

set -e

BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CA_DIR="$BASE_DIR/ca"

mkdir -p "$CA_DIR"

echo "=== Creating Test RPKI CA ==="

# Root CA
echo "1. Creating Root CA..."
openssl req -x509 -new -newkey rsa:2048 -nodes \
    -keyout "$CA_DIR/root.key" \
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

# EE certificate for AS-SET owner (AS2914)
echo "2. Creating EE cert for AS-SET owner (AS2914)..."
openssl req -new -newkey rsa:2048 -nodes \
    -keyout "$CA_DIR/AS2914.key" \
    -out "$CA_DIR/AS2914.csr" \
    -subj "/C=US/O=NTT/CN=AS2914"

openssl x509 -req \
    -in "$CA_DIR/AS2914.csr" \
    -CA "$CA_DIR/root.crt" \
    -CAkey "$CA_DIR/root.key" \
    -CAcreateserial \
    -out "$CA_DIR/AS2914.crt" \
    -days 365 \
    -extfile <(cat <<EOF
basicConstraints = CA:FALSE
keyUsage = critical, digitalSignature
subjectAltName = @alt_names
[alt_names]
ASNUM.1 = 2914
EOF
)

# EE certificate for ASN owner (AS64496)
echo "3. Creating EE cert for ASN owner (AS64496)..."
openssl req -new -newkey rsa:2048 -nodes \
    -keyout "$CA_DIR/AS64496.key" \
    -out "$CA_DIR/AS64496.csr" \
    -subj "/C=US/O=DigitalOcean/CN=AS64496"

openssl x509 -req \
    -in "$CA_DIR/AS64496.csr" \
    -CA "$CA_DIR/root.crt" \
    -CAkey "$CA_DIR/root.key" \
    -CAcreateserial \
    -out "$CA_DIR/AS64496.crt" \
    -days 365 \
    -extfile <(cat <<EOF
basicConstraints = CA:FALSE
keyUsage = critical, digitalSignature
subjectAltName = @alt_names
[alt_names]
ASNUM.1 = 64496
EOF
)

echo "=== Test CA Created ==="
echo "Root CA: $CA_DIR/root.crt"
echo "AS2914:  $CA_DIR/AS2914.crt"
echo "AS64496: $CA_DIR/AS64496.crt"
