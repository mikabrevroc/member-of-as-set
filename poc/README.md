# RASA Proof of Concept

Demonstrates RPKI AS-SET Authorization (RASA) concepts using real IRR data.

## Features

- **IRR Caching**: WHOIS results cached locally for 24 hours (instant 2nd runs)
- **Small AS-SETs**: Fast demos using AS-14061 (DigitalOcean, 4 ASNs)
- **Real Data**: Fetches actual IRR data from RADB/RIPE/APNIC/etc.
- **JunOS Output**: Generates actual router configurations

## Quick Start

```bash
# Run all demos (cached, fast)
python3 demo_all.py

# Individual demos
python3 rasa_poc_cached.py          # Basic expansion
python3 google_peerlock.py          # Peer-lock scenario
python3 google_asset_auth.py        # AS-SET authorization
python3 arelion_rasa_filter.py      # Rejection scenario

# View cache stats
python3 irr_cache.py

# Clear cache
python3 irr_cache.py clear
```

## Removed

The following toy/mock implementations were removed:
- `demo.sh` - Bash demo with simulated data
- `as-set-expander.sh` - Bash AS-SET expander
- `juniper-generator.sh` - Bash config generator
- `simulated-irr/` - Mock IRR database
- `rasa_poc.py` - Mock-based Python POC

All replaced with real WHOIS-based implementations.

## Files

| File | Description |
|------|-------------|
| `demo_all.py` | All demos in one script |
| `rasa_poc_cached.py` | Basic RASA with caching |
| `google_peerlock.py` | Google peer-lock to HE/Arelion |
| `google_asset_auth.py` | Enforce RADB-only for AS-GOOGLE |
| `arelion_rasa_filter.py` | DigitalOcean rejected from Arelion |
| `juniper_config_diff.py` | Generate config comparisons |
| `irr_cache.py` | WHOIS caching module |
| `small_as_sets.json` | List of small AS-SETs for testing |

### Mock RASA Objects

| File | Description |
|------|-------------|
| `mock_rasa/google_peerlock.json` | Google ASNs with propagation=directOnly |
| `mock_rasa/google_asset_radbonly.json` | Google AS-SET RADB-only enforcement |
| `mock_rasa/digitalocean_basic.json` | DigitalOcean unrestricted |
| `mock_rasa/digitalocean_strict.json` | DigitalOcean strictMode (no Arelion) |
| `mock_rasa/README.md` | Documentation for mock objects |

## AS-SETs Used

**Small (Fast):**
- AS-14061 (DigitalOcean) - 4 ASNs
- AS-NETFLIX - 5-10 ASNs

**Medium:**
- AS-GOOGLE - 31 ASNs
- AS-AMAZON - 20-30 ASNs
- AS-FACEBOOK - 15-20 ASNs

**Large (Slow without cache):**
- AS2914:AS-US - 200-300 ASNs

## Generated Configs

- `juniper_without_rasa.conf` - Baseline config
- `juniper_with_rasa.conf` - With RASA peer-lock
- `arelion_without_rasa.conf` - Accept all
- `arelion_with_rasa.conf` - Rejected (empty)

## Scenarios Demonstrated

### 1. Basic AS-SET Expansion
Expand AS-14061 and show member ASNs

### 2. RASA Authorization
AS14061 publishes RASA-AUTH, others don't → All authorized

### 3. Peer-Lock (propagation=directOnly)
DigitalOcean sets directOnly → Blocked from HE/Arelion peers

### 4. AS-SET Authorization (RADB-only)
Google's "DO NOT USE" comment cryptographically enforced

### 5. Rejection (strictMode)
DigitalOcean authorizes NTT/Lumen but NOT Arelion → Rejected from Arelion
