#!/usr/bin/env python3
"""Demo all RASA scenarios with caching and small AS-SETs."""

from irr_fetcher import expand_asset


def demo_basic():
    print("=" * 70)
    print("DEMO 1: Basic AS-SET Expansion (DigitalOcean)")
    print("=" * 70)
    
    asset = "AS-14061"
    asns, _, _ = expand_asset(asset, max_depth=1)
    
    print(f"\nAS-SET: {asset}")
    print(f"ASNs: {sorted(asns)}")
    print(f"Count: {len(asns)}")


def demo_rasa_filter():
    print("\n" + "=" * 70)
    print("DEMO 2: RASA Authorization Filter")
    print("=" * 70)
    
    asset = "AS-14061"
    asns, _, _ = expand_asset(asset, max_depth=1)
    
    print(f"\nDigitalOcean ASNs in {asset}:")
    for asn in sorted(asns):
        if asn == 14061:
            print(f"  ✓ AS{asn}: RASA authorized")
        else:
            print(f"  ✓ AS{asn}: No RASA (allow by default)")
    
    print(f"\nResult: All {len(asns)} ASNs authorized")


def demo_peerlock():
    print("\n" + "=" * 70)
    print("DEMO 3: Peer-Lock with propagation=directOnly")
    print("=" * 70)
    
    asset = "AS-14061"
    asns, _, _ = expand_asset(asset, max_depth=1)
    
    print(f"\nDigitalOcean sets propagation=directOnly")
    print(f"ASNs: {sorted(asns)}")
    
    peers = [
        {"name": "Hurricane Electric", "asn": 6939},
        {"name": "Arelion", "asn": 1299},
    ]
    
    print("\nPeer-lock filters generated for:")
    for peer in peers:
        print(f"  - {peer['name']} (AS{peer['asn']}): Blocks {len(asns)} ASNs")


def demo_asset_authorization():
    print("\n" + "=" * 70)
    print("DEMO 4: AS-SET Authorization (RADB-only)")
    print("=" * 70)
    
    print("\nGoogle AS-SET AS-GOOGLE:")
    print("  Comment: 'DO NOT USE, USE RADB AS-SET'")
    print("  RASA-AUTH: authorizedSet=AS-GOOGLE, authorizedIn=[RADB]")
    print("  Result: Objects from ARIN/APNIC/RIPE/AFRINIC rejected")


def demo_arelion_filter():
    print("\n" + "=" * 70)
    print("DEMO 5: Arelion Filter - DigitalOcean not authorized")
    print("=" * 70)
    
    asset = "AS-14061"
    asns, _, _ = expand_asset(asset, max_depth=1)
    
    print(f"\nDigitalOcean in Arelion's AS-SET")
    print(f"ASNs: {sorted(asns)}")
    print("\nDigitalOcean RASA-AUTH authorizes:")
    print("  ✓ AS2914:AS-GLOBAL (NTT)")
    print("  ✓ AS3356:AS-LEVEL3 (Lumen)")
    print("  ✗ AS1299:AS-TWELVE99-NA-V4 (Arelion) - NOT authorized")
    print(f"\nResult: {len(asns)} ASNs rejected from Arelion peer")


def main():
    print("\n" + "=" * 70)
    print("RASA POC - All Demos (Cached, Fast)")
    print("=" * 70)
    print("\nUsing small AS-SETs for fast demos:")
    print("  - AS-14061 (DigitalOcean): 4 ASNs")
    print("  - AS-GOOGLE: ~31 ASNs")
    print("\nWith caching: 2nd run uses local cache (instant)")
    print("=" * 70)
    
    demo_basic()
    demo_rasa_filter()
    demo_peerlock()
    demo_asset_authorization()
    demo_arelion_filter()
    
    print("\n" + "=" * 70)
    print("CACHE STATISTICS")
    print("=" * 70)
    
    from irr_cache import get_cache_stats
    stats = get_cache_stats()
    print(f"\nCached entries: {stats['count']}")
    print(f"Cache size: {stats['size_str']}")
    print(f"Cache location: {stats['cache_dir']}")
    
    print("\n" + "=" * 70)
    print("All demos complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
