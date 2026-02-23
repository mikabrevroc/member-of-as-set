#!/usr/bin/env python3
"""Common IRR fetcher with caching support."""

import subprocess
import re
from typing import Set, List, Optional, Tuple
from dataclasses import dataclass, asdict
from irr_cache import get_cached, set_cached


@dataclass
class ASSET:
    name: str
    members: List[str]
    source: str


def fetch_asset(asset_name: str, server: str = "whois.radb.net") -> Optional[ASSET]:
    """Fetch AS-SET from IRR with caching."""
    # Check cache first
    cached = get_cached(asset_name, server)
    if cached:
        return ASSET(**cached)
    
    try:
        result = subprocess.run(
            ["whois", "-h", server, asset_name],
            capture_output=True, text=True, timeout=10
        )
        
        if result.returncode != 0:
            return None
        
        lines = result.stdout.split('\n')
        members = []
        source = "UNKNOWN"
        
        in_members = False
        for raw_line in lines:
            line = raw_line.strip()
            
            if line.startswith('source:'):
                source = line.split(':', 1)[1].strip()
            
            if line.startswith('members:'):
                in_members = True
                member_str = line.split(':', 1)[1].strip()
                members.extend(parse_members(member_str))
            elif in_members:
                if not line:
                    in_members = False
                elif raw_line and raw_line[0].isupper() and not raw_line.startswith(' '):
                    in_members = False
                else:
                    members.extend(parse_members(line))
        
        asset = ASSET(name=asset_name, members=members, source=source)
        # Save to cache
        set_cached(asset_name, server, asdict(asset))
        return asset
        
    except Exception as e:
        print(f"Error fetching {asset_name}: {e}")
        return None


def parse_members(member_str: str) -> List[str]:
    """Parse member list from WHOIS format."""
    members = []
    for part in member_str.split(','):
        member = part.strip()
        if member:
            members.append(member)
    return members


def is_asn(member: str) -> bool:
    """Check if member is an ASN (AS12345) not an AS-SET."""
    return bool(re.match(r'^AS\d+$', member))


def expand_asset(asset_name: str, max_depth: int = 5, 
                seen: Set[str] = None) -> Tuple[Set[int], Set[str], List[dict]]:
    """
    Recursively expand AS-SET to get all ASNs.
    Returns (asns, nested_sets, log).
    """
    if seen is None:
        seen = set()
    
    if asset_name in seen:
        return set(), set(), [{"asset": asset_name, "action": "circular_skip"}]
    
    if max_depth <= 0:
        return set(), set(), [{"asset": asset_name, "action": "max_depth"}]
    
    seen.add(asset_name)
    
    asset = fetch_asset(asset_name)
    if not asset:
        return set(), set(), [{"asset": asset_name, "action": "not_found"}]
    
    asns = set()
    nested_sets = set()
    log = [{"asset": asset_name, "source": asset.source, "action": "expanded"}]
    
    for member in asset.members:
        if is_asn(member):
            asns.add(int(member[2:]))
        elif member.startswith('AS'):
            nested_sets.add(member)
            # Recursively expand
            sub_asns, sub_sets, sub_log = expand_asset(member, max_depth - 1, seen)
            asns.update(sub_asns)
            nested_sets.update(sub_sets)
            log.extend(sub_log)
    
    return asns, nested_sets, log
