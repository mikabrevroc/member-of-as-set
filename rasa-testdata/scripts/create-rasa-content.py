#!/usr/bin/env python3
"""
Create RASA (RPKI AS-SET Authorization) raw DER content files
These are the eContent that would be inside a CMS signed object
"""

import sys
import os
from datetime import datetime, timezone
from asn1crypto import core

class RasaAuthContent(core.Sequence):
    _fields = [
        ('version', core.Integer, {'tag_type': 'explicit', 'tag': 0, 'optional': True}),
        ('authorized_as', core.Integer, {'tag_type': 'explicit', 'tag': 1, 'optional': True}),
        ('authorized_set', core.UTF8String, {'tag_type': 'explicit', 'tag': 2, 'optional': True}),
        ('authorized_in', core.SequenceOf, {'spec': core.UTF8String}),
        ('flags', core.BitString, {'tag_type': 'explicit', 'tag': 3, 'optional': True}),
        ('not_before', core.GeneralizedTime),
        ('not_after', core.GeneralizedTime),
    ]

def create_rasa_content(asn=None, asset=None, authorized_in=None):
    content = RasaAuthContent()
    content['version'] = 0
    
    if asn is not None:
        content['authorized_as'] = asn
    elif asset is not None:
        content['authorized_set'] = asset
    else:
        raise ValueError("Must specify either asn or asset")
    
    if authorized_in is None:
        authorized_in = []
    auth_in_seq = core.SequenceOf(spec=core.UTF8String)
    for a in authorized_in:
        auth_in_seq.append(a)
    content['authorized_in'] = auth_in_seq
    
    now = datetime.now(timezone.utc)
    later = now.replace(year=now.year + 1)
    
    content['not_before'] = now.strftime('%Y%m%d%H%M%SZ')
    content['not_after'] = later.strftime('%Y%m%d%H%M%SZ')
    
    return content

def main():
    if len(sys.argv) < 3:
        print("Usage: create-rasa-content.py <asn|asset> <authorized-in-asset> <output>")
        print("Example: create-rasa-content.py 64496 AS-EXAMPLE objects/AS64496.rasa")
        sys.exit(1)
    
    entity = sys.argv[1]
    authorized_in = sys.argv[2].split(',')
    output_path = sys.argv[3]
    
    try:
        asn = int(entity)
        asset = None
    except ValueError:
        asn = None
        asset = entity
    
    content = create_rasa_content(asn=asn, asset=asset, authorized_in=authorized_in)
    
    with open(output_path, 'wb') as f:
        f.write(content.dump())
    
    print(f"Created RASA content: {output_path}")
    print(f"  Entity: {'AS' + str(asn) if asn else asset}")
    print(f"  Authorized in: {authorized_in}")

if __name__ == '__main__':
    main()
