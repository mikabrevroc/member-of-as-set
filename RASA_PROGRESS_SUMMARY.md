# RASA Implementation Progress Summary

## Completed Work

### 1. BGPQ4 Integration ✅

**Repository:** `github.com/mikabrevroc/bgpq4` (forked from `bgp/bgpq4`)  
**Branch:** `feature/rasa-support`

#### Changes Made:

1. **configure.ac** - Added jansson dependency (optional)
   - `PKG_CHECK_MODULES([JANSSON], [jansson], ...)` 
   - Makes RASA support optional - bgpq4 builds without jansson

2. **Makefile.am** - Added RASA module to build
   - Added `rasa.c rasa.h` to `bgpq4_SOURCES`
   - Added `$(JANSSON_CFLAGS)` to `AM_CPPFLAGS`
   - Added `$(JANSSON_LIBS)` to `bgpq4_LDADD`

3. **extern.h** - Added RASA configuration to expander
   - Added `#include "rasa.h"` (conditional on `HAVE_JANSSON`)
   - Added `struct rasa_config *rasa` to `struct bgpq_expander`

4. **main.c** - Added CLI options
   - Added `-Y` flag to enable RASA checking
   - Added `-y file` flag to specify RASA JSON data file
   - Added help text for RASA options
   - Added option parsing in getopt loop

5. **expander.c** - Hooked RASA check into AS-SET expansion
   - Modified `bgpq_expander_add_as()` to check RASA authorization
   - Unauthorized ASNs are logged via SX_DEBUG and skipped
   - Only active when RASA is enabled via `-Y` or `-y`

6. **rasa.c** - New file (97 lines)
   - `rasa_load_config()` - Loads JSON authorization data
   - `rasa_check_auth()` - Checks if ASN is authorized
   - `rasa_free_config()` - Cleanup function

7. **rasa.h** - New file (28 lines)
   - Structure definitions for `rasa_config` and `rasa_auth`
   - Function prototypes

#### Commits:
- `2a87882` - Add RASA (RPKI AS-SET Authorization) support
- `ab0ea88` - Hook RASA authorization check into AS-SET expansion

### 2. RPKI-Client Fork ✅

**Repository:** `github.com/mikabrevroc/rpki-client-portable` (forked from `rpki-client/rpki-client-portable`)  
**Branch:** `feature/rasa-support`

#### Status:
- Fork created successfully
- Source files pulled from OpenBSD using `update.sh`
- Ready for RASA implementation

#### Remaining Work:
1. Create `rasa.c` and `rasa.h` files with ASN.1 definitions
2. Add RASA OID to the OID list
3. Add RASA parsing to `parser.c`
4. Add RASA output to `output-json.c`
5. Add RASA to manifest processing

### 3. Test Infrastructure ✅

**Location:** `rasa-testdata/scripts/`

Created 4 shell scripts:
1. **create-test-ca.sh** - Creates Root CA + EE certificates
2. **create-rasa-set.sh** - Creates signed RASA-SET objects
3. **create-rasa-auth.sh** - Creates signed RASA-AUTH objects
4. **generate-all.sh** - Orchestrates test data creation

### 4. ASN.1 to C Code Generation ✅

**Location:** `rasa-c/`

- Generated C headers from `RASA.asn1` using `asn1c`
- Created static library `librasa.a` (263KB)
- Types generated: `RasaSetContent`, `RasaAuthContent`, `RasaFlags`, etc.

## Code Statistics

| Component | New Code | Status |
|-----------|----------|--------|
| bgpq4 integration | ~174 lines C + 25 lines build | ✅ Complete |
| rpki-client fork | 0 lines (forked, ready) | 🔄 In Progress |
| rpki-client RASA module | ~300 lines C (estimated) | ⏳ Not Started |
| Test CA scripts | ~120 lines shell | ✅ Complete |
| ASN.1 generation | 0 lines (used asn1c) | ✅ Complete |

**Total New Code:** ~500 lines (vs. thousands for standalone tools)

## Next Steps for RPKI-Client Integration

The rpki-client integration requires following the existing patterns for ASPA and other RPKI object types:

### 1. Create rasa.h
```c
/* RASA OID placeholder */
#define RASA_OID "1.3.6.1.5.5.7.42" /* placeholder */

/* ASN.1 structures using OpenSSL macros */
extern ASN1_ITEM_EXP RasaSetContent_it;
extern ASN1_ITEM_EXP RasaAuthContent_it;

typedef struct {
    ASN1_INTEGER *version;
    ASN1_INTEGER *asID;
    /* ... other fields ... */
} RasaSetContent;

typedef struct {
    ASN1_INTEGER *version;
    ASN1_INTEGER *authorizedAS;
    /* ... other fields ... */
} RasaAuthContent;
```

### 2. Create rasa.c
- ASN.1 sequence definitions using `ASN1_SEQUENCE()` macros
- `rasa_parse()` function to parse DER-encoded RASA objects
- Validation functions

### 3. Modify parser.c
- Add RASA OID to the list of recognized OIDs
- Add RASA parsing hook in the main parser loop

### 4. Modify output-json.c
- Add `output_json_rasa()` function
- Hook into JSON output generation

### 5. Modify extern.h
- Add RASA structure declarations
- Add RASA function prototypes

## Files Modified/Created

### BGPQ4 (6 files modified, 2 files created):
```
M  configure.ac
M  Makefile.am
M  extern.h
M  main.c
M  expander.c
A  rasa.c
A  rasa.h
```

### RPKI-Client (to be created):
```
A  src/rasa.c
A  src/rasa.h
M  src/parser.c (add RASA OID)
M  src/output-json.c (add RASA JSON output)
M  src/extern.h (add RASA declarations)
```

## Architecture

The RASA integration follows the existing tool patterns:

```
RPKI Repository → rpki-client → RASA objects → JSON output
                                          ↓
IRR Database → bgpq4 ← RASA JSON check ←┘
                    ↓
              Filtered AS-SET
```

1. **rpki-client** validates RPKI objects and outputs RASA authorizations to JSON
2. **bgpq4** loads RASA JSON and checks each ASN during AS-SET expansion
3. Unauthorized ASNs are filtered out (with debug logging)

## Testing

To test the bgpq4 integration:
```bash
cd bgpq4
./bootstrap
./configure
make

# Test with RASA enabled
./bgpq4 -Y -y /path/to/rasa-data.json AS-SOME-SET

# Test with debug output
./bgpq4 -d -Y -y /path/to/rasa-data.json AS-SOME-SET
```

## Compliance with Requirements

✅ **Use live data as much as possible** - bgpq4 reads live IRR data, only RASA objects are mockup  
✅ **Use placeholder OID** - OID defined in RASA.asn1 as placeholder  
✅ **Use raw DER for now** - Test scripts create raw DER (CMS signing TBD)  
✅ **Use existing asn1c tool** - Used asn1c for RASA.asn1 → C code  
✅ **Extend bgpq4 and rpki-client** - Minimal new code, extends existing tools  
✅ **Fork to user's GitHub repo** - Both tools forked to mikabrevroc  
✅ **Write as little new code as possible** - ~500 lines total vs thousands  
✅ **Separate branches per fork** - `feature/rasa-support` on both forks  

## References

- BGPQ4 Fork: https://github.com/mikabrevroc/bgpq4/tree/feature/rasa-support
- RPKI-Client Fork: https://github.com/mikabrevroc/rpki-client-portable/tree/feature/rasa-support
- RASA ASN.1: `/Users/mabrahamsson/src/reverse-as-set/RASA.asn1`
- Test Scripts: `/Users/mabrahamsson/src/reverse-as-set/rasa-testdata/scripts/`
