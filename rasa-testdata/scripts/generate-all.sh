#!/bin/bash
# Generate complete test data set

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== RASA Test Data Generation ==="

$SCRIPT_DIR/create-test-ca.sh

$SCRIPT_DIR/create-rasa-set.sh AS2914:AS-GLOBAL 2914 "64496 64497 15169"

$SCRIPT_DIR/create-rasa-auth.sh 64496 AS2914:AS-GLOBAL

echo ""
echo "=== Test Data Created ==="
ls -la "$(dirname "$SCRIPT_DIR")/objects/"
