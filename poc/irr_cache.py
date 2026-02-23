#!/usr/bin/env python3
"""IRR Cache - Cache WHOIS queries locally to avoid repeated lookups."""

import json
import hashlib
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any


# Use absolute path based on this file's location
CACHE_DIR = Path(__file__).parent / "cache" / "irr"
CACHE_TTL_HOURS = 24


def get_cache_key(asset_name: str, server: str) -> str:
    """Generate cache key for asset query."""
    key = f"{server}:{asset_name}"
    return hashlib.md5(key.encode()).hexdigest()


def get_cache_path(asset_name: str, server: str) -> Path:
    """Get cache file path for asset."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_key = get_cache_key(asset_name, server)
    return CACHE_DIR / f"{cache_key}.json"


def get_cached(asset_name: str, server: str = "whois.radb.net") -> Optional[Dict[str, Any]]:
    """Get cached WHOIS result if valid."""
    cache_path = get_cache_path(asset_name, server)
    
    if not cache_path.exists():
        return None
    
    try:
        with open(cache_path, 'r') as f:
            cached = json.load(f)
        
        # Check TTL
        cached_time = datetime.fromisoformat(cached['timestamp'])
        if datetime.now() - cached_time > timedelta(hours=CACHE_TTL_HOURS):
            return None
        
        return cached['data']
    except (json.JSONDecodeError, KeyError, ValueError):
        return None


def set_cached(asset_name: str, server: str, data: Dict[str, Any]) -> None:
    """Cache WHOIS result."""
    cache_path = get_cache_path(asset_name, server)
    
    cached = {
        'timestamp': datetime.now().isoformat(),
        'asset': asset_name,
        'server': server,
        'data': data
    }
    
    with open(cache_path, 'w') as f:
        json.dump(cached, f, indent=2)


def clear_cache() -> int:
    """Clear all cached entries. Returns count of removed files."""
    if not CACHE_DIR.exists():
        return 0
    
    count = 0
    for f in CACHE_DIR.glob("*.json"):
        f.unlink()
        count += 1
    
    return count


def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics."""
    if not CACHE_DIR.exists():
        return {'count': 0, 'size_bytes': 0}
    
    files = list(CACHE_DIR.glob("*.json"))
    total_size = sum(f.stat().st_size for f in files)
    
    # Format size nicely
    if total_size < 1024:
        size_str = f"{total_size} B"
    elif total_size < 1024 * 1024:
        size_str = f"{total_size / 1024:.1f} KB"
    else:
        size_str = f"{total_size / 1024 / 1024:.2f} MB"
    
    return {
        'count': len(files),
        'size_bytes': total_size,
        'size_str': size_str,
        'cache_dir': str(CACHE_DIR)
    }


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "clear":
        count = clear_cache()
        print(f"Cleared {count} cached entries")
    else:
        stats = get_cache_stats()
        print(f"IRR Cache Statistics:")
        print(f"  Entries: {stats['count']}")
        print(f"  Size: {stats['size_str']}")
        print(f"  Location: {stats['cache_dir']}")
