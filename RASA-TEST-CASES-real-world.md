# Real-World Scenario Test Cases

## 5. REAL-WORLD SCENARIOS

### 5.1 AS-HURRICANE Protection (Large Tier-1 AS-SET)

**Background**: AS-HURRICANE is one of the largest AS-SETs in IRR, containing thousands of members. It's a common target for route leaks.

**Test ID**: RASA-REAL-001  
**Description**: Protect AS-HURRICANE using RASA-AUTH

**RASA JSON**:
```json
{
  "rasa_sets": [
    {
      "rasa_set": {
        "version": 0,
        "as_set_name": "AS-HURRICANE",
        "containing_as": 6939,
        "members": [AS15169, AS15169, AS16591, AS6939, AS36236],
        "nested_sets": [],
        "irr_source": "RADB",
        "fallback_mode": "irrFallback",
        "not_before": "2024-01-01T00:00:00Z",
        "not_after": "2025-01-01T00:00:00Z"
      }
    }
  ],
  "rasas": [
    {
      "rasa": {
        "version": 0,
        "authorized_as": 15169,
        "authorized_in": [
          {
            "asset": "AS-HURRICANE",
            "propagation": 0
          }
        ]
      }
    },
    {
      "rasa": {
        "version": 0,
        "authorized_as": 16591,
        "authorized_in": [
          {
            "asset": "AS-HURRICANE",
            "propagation": 0
          }
        ]
      }
    },
    {
      "rasa": {
        "version": 0,
        "authorized_as": 6939,
        "authorized_in": [
          {
            "asset": "AS-HURRICANE",
            "propagation": 0
          }
        ]
      }
    },
    {
      "rasa": {
        "version": 0,
        "authorized_as": 36236,
        "authorized_in": [
          {
            "asset": "AS-HURRICANE",
            "propagation": 0
          }
        ]
      }
    }
  ]
}
```

**IRR State (Actual)**:
- RADB: AS-HURRICANE contains ~2000+ ASNs including:
  - 15169, 16591, 6939, 36236 (legitimate, should be authorized)
  - Many others that may NOT be authorized

**Expected Behavior**:
- Load RADB for IRR-Fallback
- Use RASA-SET members (AS15169, AS16591, AS6939, AS36236) as basis
- Query IRR for AS-HURRICANE (irrFallback)
- For each ASN found in IRR:
  - Check if it has RASA-AUTH
  - Only include if authorized via RASA
- Result: Protection against unauthorized AS-HURRICANE members

**Scenario**: Malicious actor adds AS-AMAZON to their AS-SET
- IRR shows AS-AMAZON in AS-HURRICANE
- RASA-AUTH for AS-AMAZON does NOT authorize AS-HURRICANE
- AS-AMAZON should be EXCLUDED

**Expected Output**:
- Only authorized Hurricane Electric customers
- Excludes any ASNs not in RASA-SET members list (or without RASA-AUTH)

**Impact**: Prevents massive route leak scenario

---

### 5.2 Content Provider AS-SETs (Google)

**Test ID**: RASA-REAL-002  
**Description**: Google AS-SET protection with nested authorization

**RASA JSON**:
```json
{
  "rasa_sets": [
    {
      "rasa_set": {
        "version": 0,
        "as_set_name": "AS-GOOGLE",
        "containing_as": 15169,
        "members": [15169, 36040, 36384, 36385, 395973, 41264],
        "nested_sets": ["AS-GOOGLE-APAC", "AS-GOOGLE-EU"],
        "irr_source": "RADB",
        "fallback_mode": "irrFallback",
        "not_before": "2024-01-01T00:00:00Z",
        "not_after": "2025-01-01T00:00:00Z"
      }
    },
    {
      "rasa_set": {
        "version": 0,
        "as_set_name": "AS-GOOGLE-APAC",
        "containing_as": 15169,
        "members": [139070, 139190, 140904],
        "nested_sets": [],
        "irr_source": "RADB",
        "fallback_mode": "irrFallback",
        "not_before": "2024-01-01T00:00:00Z",
        "not_after": "2025-01-01T00:00:00Z"
      }
    }
  ],
  "rasas": [
    {
      "rasa": {
        "version": 0,
        "authorized_as": 15169,
        "authorized_in": [
          {
            "asset": "AS-GOOGLE",
            "propagation": 0
          }
        ]
      }
    },
    {
      "rasa": {
        "version": 0,
        "authorized_as": 36040,
        "authorized_in": [
          {
            "asset": "AS-GOOGLE",
            "propagation": 0
          }
        ]
      }
    },
    {
      "rasa": {
        "version": 0,
        "authorized_as": 139070,
        "authorized_in": [
          {
            "asset": "AS-GOOGLE-APAC",
            "propagation": 0
          }
        ]
      }
    }
  ]
}
```

**Expected Behavior**:
- Google publishes RASA objects for their AS-SET hierarchy
- AS-GOOGLE contains main ASNs and nested regional sets
- Each nested set has its own RASA authorization
- IRR data can be combined with RASA validation

**Attack Scenario**:
- Someone tries to add Arelion (AS1299) to AS-GOOGLE
- IRR might show AS1299 in AS-GOOGLE (if someone registered it)
- RASA-AUTH for AS1299 only authorizes AS1299:AS-TWELVE99
- AS1299 lacks RASA authorization for AS-GOOGLE
- **Result**: AS1299 excluded from expansion

**Expected Output**:
- Only Google-authorized ASNs included
- Validation through nested AS-SET structure

---

### 5.3 Tier-1 Provider: NTT

**Test ID**: RASA-REAL-003  
**Description**: NTT customer AS-SET with irrLock to RADB

**RASA JSON**:
```json
{
  "rasa_sets": [
    {
      "rasa_set": {
        "version": 0,
        "as_set_name": "AS2914:AS-GLOBAL",
        "containing_as": 2914,
        "members": [],
        "nested_sets": ["AS2914:AS-CUSTOMERS"],
        "irr_source": "RADB",
        "fallback_mode": "irrLock",
        "not_before": "2024-01-01T00:00:00Z",
        "not_after": "2025-01-01T00:00:00Z"
      }
    },
    {
      "rasa_set": {
        "version": 0,
        "as_set_name": "AS2914:AS-CUSTOMERS",
        "containing_as": 2914,
        "members": [],
        "nested_sets": [],
        "irr_source": "RADB",
        "fallback_mode": "irrLock",
        "not_before": "2024-01-01T00:00:00Z",
        "not_after": "2025-01-01T00:00:00Z"
      }
    }
  ]
}
```

**IRR State**:
- RADB: AS2914:AS-GLOBAL contains actual NTT customer ASNs
- RIPE: Someone adds fake ASNs to stolen AS-SET "AS2914:AS-GLOBAL"
- ARIN: Someone adds fake ASNs to stolen AS-SET "AS2914:AS-GLOBAL"

**Expected Behavior (irrLock mode)**:
- Query ONLY RADB (as specified in irr_source)
- Trust IR data from RADB only
- Ignore AS2914:AS-GLOBAL definitions in RIPE, ARIN, APNIC
- If fake ASNs added to RIPE AS2914:AS-GLOBAL: ignored
- If fake ASNs added to ARIN AS2914:AS-GLOBAL: ignored

**Use Case**:
- Customer configures: bgpq4 -Jl customer NTT AS2914:AS-GLOBAL
- Malicious actor adds random ASNs to RIPE AS2914:AS-GLOBAL
- Customer still gets only RADB definitions (protected)

---

### 5.4 Arelion (Former Telia Carrier) Hierarchical AS-SET

**Test ID**: RASA-REAL-004  
**Description**: Complex hierarchical AS-SET structure

**RASA JSON**:
```json
{
  "rasa_sets": [
    {
      "rasa_set": {
        "version": 0,
        "as_set_name": "AS1299:AS-TWELVE99",
        "containing_as": 1299,
        "members": [AS8893, AS3301],
        "nested_sets": ["AS1299:AS-TWELVE99-CUSTOMERS"],
        "irr_source": "RIPE",
        "fallback_mode": "irrFallback",
        "not_before": "2024-01-01T00:00:00Z",
        "not_after": "2025-01-01T00:00:00Z"
      }
    },
    {
      "rasa_set": {
        "version": 0,
        "as_set_name": "AS1299:AS-TWELVE99-CUSTOMERS",
        "containing_as": 1299,
        "members": [AS42708, AS42862],
        "nested_sets": [],
        "irr_source": "RIPE",
        "fallback_mode": "irrFallback",
        "not_before": "2024-01-01T00:00:00Z",
        "not_after": "2025-01-01T00:00:00Z"
      }
    }
  ],
  "rasas": [
    {
      "rasa": {
        "version": 0,
        "authorized_as": 8893,
        "authorized_in": [
          {
            "asset": "AS1299:AS-TWELVE99",
            "propagation": 0
          }
        ]
      }
    },
    {
      "rasa": {
        "version": 0,
        "authorized_as": 42708,
        "authorized_in": [
          {
            "asset": "AS1299:AS-TWELVE99-CUSTOMERS",
            "propagation": 0
          }
        ]
      }
    }
  ]
}
```

**Expected Behavior**:
- Hierarchical AS-SET structure: AS-TWELVE99 → AS-TWELVE99-CUSTOMERS
- Each level can have direct members and nested sets
- RASA-AUTH valid at each level
- IRR fallack adds additional ASNs but requires authorization

**Use Case**:
- Large carrier with:
  - Direct peering ASNs (AS8893, AS3301)
  - Customer ASNs (AS42708, AS42862)
- Distinct authorization for different tiers

---

### 5.5 AWS (Amazon) Content Provider

**Test ID**: RASA-REAL-005  
**Description**: AWS customer peering with rasaOnly mode

**RASA JSON**:
```json
{
  "rasa_sets": [
    {
      "rasa_set": {
        "version": 0,
        "as_set_name": "AS-AMAZON",
        "containing_as": 16509,
        "members": [AS7224, AS16509, AS14618],
        "nested_sets": ["AS-AMAZON-APN"],
        "irr_source": null,
        "fallback_mode": "rasaOnly",
        "not_before": "2024-01-01T00:00:00Z",
        "not_after": "2025-01-01T00:00:00Z"
      }
    }
  ],
  "rasas": [
    {
      "rasa": {
        "version": 0,
        "authorized_as": 7224,
        "authorized_in": [
          {
            "asset": "AS-AMAZON",
            "propagation": 0
          }
        ]
      }
    },
    {
      "rasa": {
        "version": 0,
        "authorized_as": 16509,
        "authorized_in": [
          {
            "asset": "AS-AMAZON",
            "propagation": 0
          }
        ]
      }
    },
    {
      "rasa": {
        "version": 0,
        "authorized_as": 14618,
        "authorized_in": [
          {
            "asset": "AS-AMAZON",
            "propagation": 0
          }
        ]
      }
    }
  ]
}
```

**Expected Behavior**:
- rasaOnly mode: don't query IRR at all
- Use only RASA-SET members
- Only AWS-authorized ASNs included
- No IRR queries required
- Fast and secure

**Use Case**:
- AWS customer wants to peer with AWS
- Gets RASA file from AWS with authorized ASNs
- Uses rasaOnly for maximum security
- No risk of IRR poisoning

**Expected Output**:
- Only prefixes from AWS-authorized ASNs
- No unauthenticated ASNs possible

---

### 5.6 Mixed Provider Transit Customer

**Test ID**: RASA-REAL-006  
**Description**: Customer using multiple Tier-1 providers

**RASA JSON**:
```json
{
  "rasa_sets": [
    {
      "rasa_set": {
        "version": 0,
        "as_set_name": "AS-CUSTOMER-MULTI-HOMED",
        "containing_as": 65000,
        "members": [AS65000],
        "nested_sets": ["AS2914:AS-GLOBAL", "AS1299:AS-TWELVE99"],
        "irr_source": "RADB",
        "fallback_mode": "irrFallback",
        "not_before": "2024-01-01T00:00:00Z",
        "not_after": "2025-01-01T00:00:00Z"
      }
    },
    {
      "rasa_set": {
        "version": 0,
        "as_set_name": "AS2914:AS-GLOBAL",
        "containing_as": 2914,
        "members": [],
        "nested_sets": [],
        "irr_source": "RADB",
        "fallback_mode": "irrLock",
        "not_before": "2024-01-01T00:00:00Z",
        "not_after": "2025-01-01T00:00:00Z"
      }
    },
    {
      "rasa_set": {
        "version": 0,
        "as_set_name": "AS1299:AS-TWELVE99",
        "containing_as": 1299,
        "members": [],
        "nested_sets": [],
        "irr_source": "RIPE",
        "fallback_mode": "irrLock",
        "not_before": "2024-01-01T00:00:00Z",
        "not_after": "2025-01-01T00:00:00Z"
      }
    }
  ],
  "rasas": [
    {
      "rasa": {
        "version": 0,
        "authorized_as": 65000,
        "authorized_in": [
          {
            "asset": "AS-CUSTOMER-MULTI-HOMED",
            "propagation": 0
          }
        ]
      }
    }
  ]
}
```

**Expected Behavior**:
- Customer multi-homed to NTT (AS2914) and Arelion (AS1299)
- AS-CUSTOMER-MULTI-HOMED contains NTT's global AS-SET and Arelion's AS-SET
- Different IRR sources for each provider:
  - NTT: RADB (irrLock)
  - Arelion: RIPE (irrLock)
- RASA-AUTH validates AS65000 is authorized

**Expected Output**:
- Union of NTT and Arelion customer AS-SETs
- Each queried from correct IRR source
- Protected by irrLock mode

