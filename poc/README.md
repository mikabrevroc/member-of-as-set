# RASA Proof of Concept

Minimal implementation using existing tools (bgpq4) to demonstrate RPKI AS-SET Authorization (RASA) concepts.

## What It Does

1. **Expands AS-SETs** using bgpq4 to get member ASNs
2. **Applies RASA authorization** to filter members based on cryptographic authorization
3. **Generates JunOS config** for authorized ASNs only

## Requirements

- `bgpq4` (install via `brew install bgpq4` or build from source)
- Python 3.8+
- No additional Python packages needed (uses stdlib only)

## Usage

```bash
python3 rasa_poc.py
```

This runs Example 1 from the draft: Member Authorizes Inclusion

## Examples from Draft

### Example 1: Member Authorizes Inclusion
- AS2914:AS-GLOBAL claims AS15169 as member
- AS15169 publishes RASA-AUTH authorizing AS2914:AS-GLOBAL
- Result: AS15169 included

### Example 2: Member Denies Inclusion  
- AS2914:AS-GLOBAL claims AS15169 as member
- AS15169 publishes RASA-AUTH with strictMode=TRUE, doesn't authorize AS2914:AS-GLOBAL
- Result: AS15169 excluded, security event logged

### Example 3: No RASA-AUTH
- AS2914:AS-GLOBAL claims AS398465 as member
- AS398465 publishes no RASA-AUTH
- Result: AS398465 included (no objection)

### Example 4: AS-SET Authorization
- AS2914:AS-GLOBAL has nested AS-SET AS1299:AS-TWELVE99
- AS1299 publishes RASA-AUTH (authorizedSet) authorizing inclusion
- Result: Nested AS-SET included

### Example 5: AS-SET Authorization Denied
- AS2914:AS-GLOBAL has nested AS-SET AS1299:AS-TWELVE99  
- AS1299 publishes RASA-AUTH but doesn't authorize AS2914:AS-GLOBAL
- strictMode=TRUE
- Result: Nested AS-SET excluded

### Example 6: Peer Lock Signal
- AS15169 authorizes AS2914:AS-GLOBAL with propagation=directOnly
- AS-SET expansion includes AS15169 normally
- BUT: BGP import policy signal tells NTT to only accept AS15169 routes from direct sessions
- This is advisory, not part of AS-SET expansion

## RASA Data Format

JSON format matching the draft's ASN.1 structure:

```json
{
  "rasa_auth": {
    "AS15169": {
      "authorizedEntity": {"authorizedAS": 15169},
      "authorizedIn": [
        {"asSetName": "AS2914:AS-GLOBAL", "propagation": "unrestricted"}
      ],
      "strictMode": false
    }
  }
}
```

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   IRR DB    │────▶│   bgpq4     │────▶│  Raw ASNs   │
│(NTT, RIPE)  │     │ (existing)  │     │             │
└─────────────┘     └─────────────┘     └──────┬──────┘
                                                │
                                                ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   RASA-AUTH │────▶│  RASA Logic │────▶│  Authorized │
│  (mock JSON)│     │  (new code) │     │    ASNs     │
└─────────────┘     └─────────────┘     └──────┬──────┘
                                                │
                                                ▼
                                       ┌─────────────┐
                                       │  JunOS Config│
                                       │  (output)    │
                                       └─────────────┘
```

## Production Implementation

In production, RASA-AUTH objects would:
1. Be fetched from RPKI repositories (not mock JSON)
2. Be validated using RPKI CMS signatures (RFC 6488)
3. Include AS-SET nesting authorization (authorizedSet)
4. Include propagation scope for peer locking (directOnly)

This POC demonstrates the authorization logic using mock data.
