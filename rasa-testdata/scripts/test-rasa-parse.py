#!/usr/bin/env python3
"""
Test RASA CMS parsing using OpenSSL command line
"""

import subprocess
import sys
import os

def test_cms_structure(cms_file):
    """Extract and display CMS content using OpenSSL"""
    print(f"Testing: {cms_file}")
    print("=" * 60)
    
    # Get CMS info
    result = subprocess.run(
        ['openssl', 'cms', '-in', cms_file, '-inform', 'DER', '-cmsout', '-print'],
        capture_output=True, text=True
    )
    
    if result.returncode != 0:
        print(f"Error parsing CMS: {result.stderr}")
        return False
    
    print("CMS Structure:")
    print(result.stdout[:2000])  # Print first 2000 chars
    print("...")
    
    return True

def verify_cms(cms_file, ca_file):
    """Verify CMS signature"""
    print(f"\nVerifying signature...")
    
    result = subprocess.run(
        ['openssl', 'cms', '-verify', '-in', cms_file, '-inform', 'DER',
         '-CAfile', ca_file, '-out', '/dev/null'],
        capture_output=True, text=True
    )
    
    if result.returncode == 0:
        print("✓ CMS signature verified successfully!")
        return True
    else:
        print(f"✗ Verification failed: {result.stderr}")
        return False

def extract_content(cms_file):
    """Extract the embedded RASA content"""
    print(f"\nExtracting RASA content...")
    
    result = subprocess.run(
        ['openssl', 'cms', '-verify', '-in', cms_file, '-inform', 'DER', '-noverify'],
        capture_output=True
    )
    
    if result.returncode == 0:
        content = result.stdout
        print(f"✓ Extracted {len(content)} bytes")
        print(f"First 64 bytes (hex): {content[:64].hex()}")
        return content
    else:
        print(f"✗ Extraction failed")
        return None

if __name__ == '__main__':
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Test each RASA object
    test_cases = [
        ('AS64496', 'ca/root.crt'),
        ('AS15169', 'ca/root.crt'),
        ('AS2914', 'ca/root.crt'),
    ]
    
    all_passed = True
    
    for asn, ca_path in test_cases:
        cms_file = os.path.join(base_dir, 'objects', f'{asn}.rasa.cms')
        ca_file = os.path.join(base_dir, ca_path)
        
        if not os.path.exists(cms_file):
            print(f"Missing: {cms_file}")
            continue
            
        print(f"\n{'='*60}")
        print(f"Testing {asn}")
        print('='*60)
        
        if not test_cms_structure(cms_file):
            all_passed = False
            continue
            
        if not verify_cms(cms_file, ca_file):
            all_passed = False
            continue
            
        content = extract_content(cms_file)
        if content:
            print(f"\n✓ {asn}: All tests passed")
        else:
            all_passed = False
    
    print(f"\n{'='*60}")
    if all_passed:
        print("All RASA CMS objects verified successfully!")
        sys.exit(0)
    else:
        print("Some tests failed!")
        sys.exit(1)
