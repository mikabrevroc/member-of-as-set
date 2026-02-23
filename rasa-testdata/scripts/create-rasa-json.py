#!/usr/bin/env python3
"""
Create RASA JSON output for testing bgpq4
This simulates what rpki-client would output
"""

import json
import sys
from datetime import datetime, timezone

def create_rasa_json(output_path):
    """Create sample RASA JSON output"""
    
    rasa_data = {
        "metadata": {
            "buildtime": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "rasas": 3,
            "vrasas": 3,
            "uniquevrasas": 3
        },
        "rasas": [
            {
                "rasa": {
                    "authorized_as": 64496,
                    "authorized_in": [
                        {"entry": {"asset": "AS-EXAMPLE", "propagation": 0}},
                        {"entry": {"asset": "AS-GLOBAL", "propagation": 0}}
                    ],
                    "expires": int((datetime.now(timezone.utc).replace(year=datetime.now(timezone.utc).year + 1)).timestamp()),
                    "ta": "TEST"
                }
            },
            {
                "rasa": {
                    "authorized_as": 15169,
                    "authorized_in": [
                        {"entry": {"asset": "AS-GOOGLE", "propagation": 0}}
                    ],
                    "expires": int((datetime.now(timezone.utc).replace(year=datetime.now(timezone.utc).year + 1)).timestamp()),
                    "ta": "TEST"
                }
            },
            {
                "rasa": {
                    "authorized_as": 2914,
                    "authorized_in": [
                        {"entry": {"asset": "AS-NTT", "propagation": 0}},
                        {"entry": {"asset": "AS-GLOBAL", "propagation": 0}}
                    ],
                    "expires": int((datetime.now(timezone.utc).replace(year=datetime.now(timezone.utc).year + 1)).timestamp()),
                    "ta": "TEST"
                }
            }
        ]
    }
    
    with open(output_path, 'w') as f:
        json.dump(rasa_data, f, indent=2)
    
    print(f"Created RASA JSON: {output_path}")
    print(f"  Contains {len(rasa_data['rasas'])} RASA entries")

if __name__ == '__main__':
    output = sys.argv[1] if len(sys.argv) > 1 else 'rasa.json'
    create_rasa_json(output)
