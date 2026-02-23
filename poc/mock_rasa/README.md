# Mock RASA-AUTH Objects

This directory contains example/mock RASA-AUTH objects in JSON format.
These can be modified and used by the POC scripts.

## Files

| File | Description |
|------|-------------|
| `google_peerlock.json` | Google ASNs with propagation=directOnly |
| `google_asset_radbonly.json` | Google AS-SET authorization (RADB only) |
| `digitalocean_basic.json` | DigitalOcean with unrestricted propagation |
| `digitalocean_strict.json` | DigitalOcean with strictMode (no Arelion) |

## Format

```json
{
  "rasa_auth": {
    "AS12345": {
      "authorizedAS": 12345,
      "authorizedIn": [
        {
          "asSetName": "AS2914:AS-GLOBAL",
          "propagation": "unrestricted"
        }
      ],
      "strictMode": false
    }
  }
}
```

## Usage

```python
import json

with open('mock_rasa/google_peerlock.json') as f:
    rasa_db = json.load(f)['rasa_auth']
```

## Modifying

Edit any .json file to change authorization rules:
- Add/remove ASNs
- Change `propagation`: `unrestricted` | `directOnly`
- Set `strictMode`: `true` | `false`
