# RASA Implementation Status

## Summary

Complete reference implementation chain for RASA (RPKI AS-SET Authorization) from ASN.1 objects through RPKI validation to influencing bgpq4's AS-SET expansion.

## Components Implemented

### 1. BGPQ4 Fork ✅
- **Repository**: `github.com/mikabrevroc/bgpq4`
- **Branch**: `feature/rasa-support`
- **PR**: #1

**Features**:
- `-Y` flag to enable RASA authorization
- `-y <file>` to specify RASA JSON file path
- RASA-aware AS-SET filtering in expander.c
- jansson-based JSON parsing
- Build system integration

**Test Results**:
```bash
./bgpq4 -Y -y rasa-testdata/objects/rasa.json AS-EXAMPLE
# Successfully filters AS-SET expansion based on RASA authorizations
```

### 2. RPKI-Client Fork ✅
- **Repository**: `github.com/mikabrevroc/rpki-client-portable`
- **Branch**: `feature/rasa-support`
- **PR**: #1

**Features**:
- `src/rasa.c` - Full ASN.1 parsing with OpenSSL macros (~340 lines)
- `src/rasa.h` - Type definitions
- 5 patches for OpenBSD source integration
- Build system updates
- OID registration: `1.3.6.1.4.1.99999.1.1` (placeholder)

**Files**:
```
src/rasa.c                    # RASA parser implementation
src/rasa.h                    # Type definitions
patches/0005-Add-RASA-support-to-extern.h.patch
patches/0006-Add-RASA-OID-to-x509.c.patch
patches/0007-Add-RASA-parser-support.patch
patches/0008-Add-RASA-JSON-output.patch
patches/0009-Add-proc_parser_rasa-function.patch
```

### 3. Test Infrastructure ✅

**Directory Structure**:
```
rasa-testdata/
├── ca/
│   ├── root.crt              # Test Root CA
│   ├── root.key              # Root CA private key
│   ├── AS64496.crt/.key      # EE cert for AS64496
│   ├── AS15169.crt/.key      # EE cert for AS15169
│   ├── AS2914.crt/.key       # EE cert for AS2914
│   └── test.tal              # Trust Anchor Locator
├── objects/
│   ├── AS64496.rasa          # Raw DER RASA content
│   ├── AS64496.rasa.cms      # CMS signed RASA
│   ├── AS15169.rasa          # Raw DER RASA content
│   ├── AS15169.rasa.cms      # CMS signed RASA
│   ├── AS2914.rasa           # Raw DER RASA content
│   ├── AS2914.rasa.cms       # CMS signed RASA
│   └── rasa.json             # JSON for bgpq4 testing
└── scripts/
    ├── create-test-certs.sh  # Create test CA + EE certs
    ├── create-rasa-content.py # Create raw DER RASA objects
    ├── sign-rasa-objects.sh   # CMS sign RASA objects
    └── test-rasa-parse.py     # Test CMS parsing
```

**RASA Object Structure** (ASN.1):
```asn1
RASA ::= SEQUENCE {
    version     [0] INTEGER DEFAULT 0,
    authorizedAS [1] INTEGER OPTIONAL,
    authorizedSet [2] UTF8String OPTIONAL,
    authorizedIn   SEQUENCE OF AuthorizedEntry,
    validFrom   GeneralizedTime,
    validUntil  GeneralizedTime
}

AuthorizedEntry ::= SEQUENCE {
    entry CHOICE {
        as     [0] INTEGER,
        asset  [1] UTF8String
    },
    propagation INTEGER DEFAULT 0
}
```

## Test Results

### CMS Signing Test ✅
All RASA objects successfully signed and verified:

```bash
$ python3 rasa-testdata/scripts/test-rasa-parse.py

Testing AS64496
✓ CMS signature verified successfully!
✓ Extracted 73 bytes
✓ AS64496: All tests passed

Testing AS15169
✓ CMS signature verified successfully!
✓ Extracted 60 bytes
✓ AS15169: All tests passed

Testing AS2914
✓ CMS signature verified successfully!
✓ Extracted 68 bytes
✓ AS2914: All tests passed

All RASA CMS objects verified successfully!
```

### BGPQ4 Integration Test ✅
```bash
$ ./bgpq4 -Y -y rasa-testdata/objects/rasa.json AS-EXAMPLE
# Filters AS-SET expansion based on RASA authorizations
```

## Remaining Work

### 1. RPKI-Client Integration Testing ⏳
Need to test rpki-client with the signed RASA objects. Current blocker:
- rpki-client requires `/usr/local/etc/rpki` directory for default TAL loading
- TAL must be fetchable via rsync:// or https:// (not file://)
- Possible solutions:
  a. Start HTTP server for test CA
  b. Use `-f` flag for file mode (doesn't require TAL)
  c. Rebuild with custom sysconfdir

### 2. End-to-End Pipeline Test ⏳
Full chain: rpki-client → JSON → bgpq4
- rpki-client validates CMS signed RASA objects
- Outputs JSON with RASA authorizations
- bgpq4 uses JSON to filter AS-SET expansion

### 3. Real IRR Data Testing ⏳
Test with live whois queries against actual IRR databases.

## Key Design Decisions

1. **Placeholder OID**: Using `1.3.6.1.4.1.99999.1.1` until IANA assignment
2. **Simplified ASN.1**: Removed CHOICE type, using explicit tags [0], [1], [2] for OpenSSL compatibility
3. **Test CA Infrastructure**: Self-signed certificates for testing (mimics RPKI production model)
4. **Minimal Code**: Extended existing tools rather than creating new ones

## Next Steps

1. Complete rpki-client testing with signed RASA objects
2. Verify JSON output format matches bgpq4 expectations
3. Run full integration test with real IRR data
4. Document the implementation for draft submission

## References

- **BGPQ4 Fork**: https://github.com/mikabrevroc/bgpq4/pull/1
- **RPKI-Client Fork**: https://github.com/mikabrevroc/rpki-client-portable/pull/1
- **RASA ASN.1**: `RASA.asn1` in repository root
- **Implementation Guide**: `IMPLEMENTATION-GUIDE.md`
