#!/usr/bin/env python3
"""
Create RASA (RPKI AS-SET Authorization) DER encoded files
Uses asn1crypto to create proper ASN.1 structures
"""

import sys
import os
from datetime import datetime, timezone
from asn1crypto import cms, x509, core

# RASA OID (placeholder)
RASA_OID = '1.3.6.1.4.1.99999.1.1'

class RasaAuthContent(core.Sequence):
    """RasaAuthContent ::= SEQUENCE {
      version          [0] INTEGER DEFAULT 0,
      authorizedAS     [1] ASID OPTIONAL,
      authorizedSet    [2] UTF8String OPTIONAL,
      authorizedIn         SEQUENCE OF UTF8String,
      flags                RasaAuthFlags OPTIONAL,
      notBefore            GeneralizedTime,
      notAfter             GeneralizedTime
    }"""
    
    _fields = [
        ('version', core.Integer, {'tag_type': 'explicit', 'tag': 0, 'optional': True}),
        ('authorized_as', core.Integer, {'tag_type': 'explicit', 'tag': 1, 'optional': True}),
        ('authorized_set', core.UTF8String, {'tag_type': 'explicit', 'tag': 2, 'optional': True}),
        ('authorized_in', core.SequenceOf, {'spec': core.UTF8String}),
        ('flags', core.BitString, {'tag_type': 'explicit', 'tag': 3, 'optional': True}),
        ('not_before', core.GeneralizedTime),
        ('not_after', core.GeneralizedTime),
    ]

def create_rasa_auth_content(asn=None, asset=None, authorized_in=None, 
                             not_before=None, not_after=None):
    """Create RASA Auth Content structure"""
    
    content = RasaAuthContent()
    
    # Version (optional, default 0)
    content['version'] = 0
    
    # Authorized entity - either ASID or AS-SET name
    if asn is not None:
        content['authorized_as'] = asn
    elif asset is not None:
        content['authorized_set'] = asset
    else:
        raise ValueError("Must specify either asn or asset")
    
    # Authorized in - list of AS-SET names
    if authorized_in is None:
        authorized_in = []
    auth_in_seq = core.SequenceOf(spec=core.UTF8String)
    for a in authorized_in:
        auth_in_seq.append(a)
    content['authorized_in'] = auth_in_seq
    
    # Flags (optional)
    # content['flags'] = core.BitString('00')  # No flags
    
    # Validity times
    if not_before is None:
        not_before = datetime.now(timezone.utc)
    if not_after is None:
        not_after = datetime.now(timezone.utc)
        not_after = not_after.replace(year=not_after.year + 1)
    
    content['not_before'] = not_before.strftime('%Y%m%d%H%M%SZ')
    content['not_after'] = not_after.strftime('%Y%m%d%H%M%SZ')
    
    return content

def create_signed_rasa(content, signer_cert_path, signer_key_path, output_path):
    """Create CMS signed RASA object"""
    
    # Load certificate and key
    with open(signer_cert_path, 'rb') as f:
        cert_bytes = f.read()
    
    with open(signer_key_path, 'rb') as f:
        key_bytes = f.read()
    
    # Parse certificate
    cert = x509.Certificate.load(cert_bytes)
    
    # Encode content
    content_bytes = content.dump()
    
    # Create CMS signed data
    signed_data = cms.SignedData({
        'version': 'v1',
        'digest_algorithms': [cms.DigestAlgorithm({'algorithm': 'sha256'})],
        'encap_content_info': cms.EncapsulatedContentInfo({
            'content_type': RASA_OID,
            'content': content_bytes,
        }),
        'certificates': [cert],
        'signer_infos': [],  # We'll sign externally with OpenSSL
    })
    
    # Write content to temp file for OpenSSL signing
    import tempfile
    import subprocess
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.der') as f:
        content_file = f.name
        f.write(content_bytes)
    
    try:
        # Use OpenSSL to create CMS signed object
        subprocess.run([
            'openssl', 'cms', '-sign',
            '-in', content_file,
            '-out', output_path,
            '-signer', signer_cert_path,
            '-inkey', signer_key_path,
            '-outform', 'DER',
            '-nodetach',
        ], check=True)
        
        print(f"Created signed RASA: {output_path}")
        
    finally:
        os.unlink(content_file)

def main():
    if len(sys.argv) < 5:
        print("Usage: create-rasa-der.py <asn|asset> <authorized-in-asset> <cert> <key> <output>")
        print("Example: create-rasa-der.py 64496 AS-EXAMPLE ca/AS64496.crt ca/AS64496.key AS64496.rasa")
        sys.exit(1)
    
    entity = sys.argv[1]
    authorized_in = sys.argv[2].split(',')
    cert_path = sys.argv[3]
    key_path = sys.argv[4]
    output_path = sys.argv[5]
    
    # Determine if entity is ASN or AS-SET
    try:
        asn = int(entity)
        asset = None
    except ValueError:
        asn = None
        asset = entity
    
    # Create RASA content
    content = create_rasa_auth_content(
        asn=asn,
        asset=asset,
        authorized_in=authorized_in,
    )
    
    # Create signed RASA
    create_signed_rasa(content, cert_path, key_path, output_path)

if __name__ == '__main__':
    main()
