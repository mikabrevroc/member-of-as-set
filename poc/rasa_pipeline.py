#!/usr/bin/env python3
"""
Real RASA Pipeline - Uses bgpq4 to fetch live IRR data.
Simulates AS2914 (NTT) generating as-path filters for peers.
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Set, Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class RASAAuth:
    authorizedAS: Optional[int] = None
    authorizedSet: Optional[str] = None
    authorizedIn: List[dict] = None
    strictMode: bool = False
    flags: dict = None
    
    def __post_init__(self):
        if self.authorizedIn is None:
            self.authorizedIn = []
        if self.flags is None:
            self.flags = {}


class IRRPipeline:
    """Fetches and expands AS-SETs using bgpq4."""
    
    def __init__(self, sources: str = "RIPE,NTT,RADB"):
        self.sources = sources
        self.cache_dir = Path("poc/cache")
        self.cache_dir.mkdir(exist_ok=True)
        
    def expand_asset(self, asset: str, use_cache: bool = True) -> Set[int]:
        """Expand AS-SET to member ASNs using bgpq4."""
        cache_file = self.cache_dir / f"{asset.replace(':', '_')}.json"
        
        if use_cache and cache_file.exists():
            with open(cache_file) as f:
                return set(json.load(f))
        
        try:
            result = subprocess.run(
                ["bgpq4", "-S", self.sources, "-j", asset],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                asns = set(data.get("ASNs", []))
                # Cache result
                with open(cache_file, 'w') as f:
                    json.dump(list(asns), f)
                return asns
            else:
                print(f"bgpq4 error: {result.stderr}", file=sys.stderr)
        except Exception as e:
            print(f"Error expanding {asset}: {e}", file=sys.stderr)
        
        return set()
    
    def expand_asset_recursive(self, asset: str, max_depth: int = 10,
                               seen: Set[str] = None) -> Tuple[Set[int], Set[str]]:
        """
        Recursively expand AS-SET including nested AS-SETs.
        Returns (all_asns, all_nested_sets).
        """
        if seen is None:
            seen = set()
        
        if asset in seen:
            return set(), set()
        
        if max_depth <= 0:
            return set(), set()
        
        seen.add(asset)
        
        # For now, just get ASNs - nested AS-SET expansion would require parsing WHOIS
        # In real implementation, would fetch AS-SET object and extract members:
        # - ASNs (direct members)
        # - AS-SET names (nested members)
        asns = self.expand_asset(asset)
        
        return asns, seen


class RASAFilter:
    """Applies RASA authorization to filter AS-SET members."""
    
    def __init__(self, rasa_db: Dict[str, RASAAuth]):
        self.rasa_db = rasa_db
        self.log = []
    
    def check_auth(self, asn: int, asset: str) -> Tuple[bool, str]:
        """
        Check if ASN is authorized to be in asset.
        Returns (is_authorized, reason).
        """
        auth_key = f"AS{asn}"
        auth_obj = self.rasa_db.get(auth_key)
        
        if not auth_obj:
            return True, "No RASA-AUTH (default allow)"
        
        # Check if asset is in authorizedIn list
        for entry in auth_obj.authorizedIn:
            if entry.get("asSetName") == asset:
                propagation = entry.get("propagation", "unrestricted")
                return True, f"Authorized ({propagation})"
        
        # Not authorized
        if auth_obj.strictMode:
            return False, "REJECTED: strictMode=TRUE, not authorized"
        
        return False, "REJECTED: not in authorizedIn"
    
    def filter_asset(self, asset: str, asns: Set[int]) -> Tuple[Set[int], List[dict]]:
        """
        Filter AS-SET members based on RASA authorization.
        Returns (authorized_asns, log_entries).
        """
        authorized = set()
        log = []
        
        for asn in sorted(asns):
            is_auth, reason = self.check_auth(asn, asset)
            log.append({
                "asn": asn,
                "asset": asset,
                "authorized": is_auth,
                "reason": reason
            })
            if is_auth:
                authorized.add(asn)
        
        return authorized, log
    
    def get_peer_lock_list(self, asn: int) -> List[str]:
        """
        Get list of AS-SETs where this ASN has propagation=directOnly.
        These are the AS-SETs that should only accept routes from direct sessions.
        """
        auth_key = f"AS{asn}"
        auth_obj = self.rasa_db.get(auth_key)
        
        if not auth_obj:
            return []
        
        peer_lock_sets = []
        for entry in auth_obj.authorizedIn:
            if entry.get("propagation") == "directOnly":
                peer_lock_sets.append(entry["asSetName"])
        
        return peer_lock_sets


class JunOSGenerator:
    """Generates Juniper JunOS configuration."""
    
    def __init__(self, as_number: int = 2914):
        self.as_number = as_number
    
    def generate_as_path_filter(self, asns: Set[int], policy_name: str) -> str:
        """Generate as-path-group configuration."""
        if not asns:
            return f"as-path-group {policy_name} {{\n    as-path {policy_name}-empty \"^$\";\n}}"
        
        lines = [f"as-path-group {policy_name} {{"]
        for i, asn in enumerate(sorted(asns)):
            lines.append(f'    as-path {policy_name}-{asn} ".* {asn} .*";')
        lines.append("}")
        return "\n".join(lines)
    
    def generate_peer_policy(self, peer_name: str, peer_asn: int,
                            allowed_asns: Set[int],
                            peer_lock_asns: Set[int] = None) -> str:
        """
        Generate policy-statement for a specific peer.
        
        For regular peers: accept routes with allowed ASNs in path
        For peers with peer-lock: reject routes from indirect paths
        """
        lines = [
            f"policy-statement {peer_name}-in {{",
            "    term allow-asns {",
            "        from {"
        ]
        
        # Add as-path-group match
        as_list = sorted(allowed_asns)
        if as_list:
            lines.append(f"            as-path-group {peer_name}-asns;")
        
        lines.append("        }")
        lines.append("        then accept;")
        lines.append("    }")
        lines.append("    term reject {")
        lines.append("        then reject;")
        lines.append("    }")
        lines.append("}")
        
        # Add as-path-group definition
        lines.append("")
        lines.append(self.generate_as_path_filter(allowed_asns, f"{peer_name}-asns"))
        
        return "\n".join(lines)
    
    def generate_peer_lock_policy(self, asn: int, peer_asn: int) -> str:
        """
        Generate policy for peer-lock scenario.
        For peer AS where some ASNs should only be accepted from direct sessions.
        
        Example: Hurricane Electric (AS6939) peer should reject Google routes
        if Google has set propagation=directOnly for their inclusion in AS2914:AS-GLOBAL.
        """
        lines = [
            f"policy-statement AS{peer_asn}-in-peerlock {{",
            "    term reject-indirect-peer-lock {",
            "        from {",
            f"            as-path AS{asn}-peerlock;",
            "        }",
            "        then reject;",
            "    }",
            "    term accept-others {",
            "        then accept;",
            "    }",
            "}",
            "",
            f"as-path AS{asn}-peerlock \".* {asn} .*\";"
        ]
        return "\n".join(lines)


def simulate_ntt_scenario():
    """
    Simulate AS2914 (NTT) scenario:
    - AS2914:AS-GLOBAL contains customers including AS15169 (Google)
    - AS2914 peers with Hurricane Electric (AS6939)
    - Google wants to signal peer-lock to NTT
    """
    print("=" * 70)
    print("SCENARIO: AS2914 (NTT) AS-Path Filter Generation")
    print("=" * 70)
    
    # Initialize pipeline
    irr = IRRPipeline()
    
    # Step 1: Get AS2914:AS-GLOBAL members from IRR
    print("\n1. Fetching AS2914:AS-GLOBAL from IRR...")
    asset = "AS2914:AS-GLOBAL"
    all_asns = irr.expand_asset(asset)
    print(f"   Found {len(all_asns)} ASNs: {sorted(all_asns)[:10]}...")
    
    # Step 2: Without RASA - all members are allowed
    print("\n2. WITHOUT RASA (current IRR behavior):")
    print(f"   All {len(all_asns)} ASNs would be included in filters")
    
    # Generate config without RASA
    gen = JunOSGenerator(as_number=2914)
    config_no_rasa = gen.generate_as_path_filter(all_asns, "AS2914-AS-GLOBAL")
    print("\n   Generated as-path-group (first 5 entries):")
    for line in config_no_rasa.split('\n')[:7]:
        print(f"   {line}")
    print("   ...")
    
    # Step 3: With RASA - apply authorization
    print("\n" + "=" * 70)
    print("3. WITH RASA (proposed behavior):")
    print("=" * 70)
    
    # RASA database - some ASNs publish authorization
    rasa_db = {
        "AS15169": RASAAuth(
            authorizedAS=15169,
            authorizedIn=[
                {"asSetName": "AS2914:AS-GLOBAL", "propagation": "unrestricted"},
                {"asSetName": "AS1299:AS-TWELVE99", "propagation": "unrestricted"}
            ],
            strictMode=False
        ),
        "AS64496": RASAAuth(
            authorizedAS=64496,
            authorizedIn=[
                {"asSetName": "AS2914:AS-GLOBAL", "propagation": "unrestricted"}
            ],
            strictMode=False
        ),
        # AS64497 does NOT publish RASA-AUTH (no objection)
    }
    
    # Apply RASA filtering
    rasa_filter = RASAFilter(rasa_db)
    authorized_asns, log = rasa_filter.filter_asset(asset, all_asns)
    
    print(f"\n   RASA Authorization Results:")
    for entry in log[:5]:
        status = "✓" if entry["authorized"] else "✗"
        print(f"   {status} AS{entry['asn']}: {entry['reason']}")
    if len(log) > 5:
        print(f"   ... and {len(log) - 5} more")
    
    print(f"\n   Final: {len(authorized_asns)} of {len(all_asns)} ASNs authorized")
    
    # Generate config with RASA
    config_with_rasa = gen.generate_as_path_filter(authorized_asns, "AS2914-AS-GLOBAL-RASA")
    print("\n   Generated as-path-group with RASA:")
    for line in config_with_rasa.split('\n')[:7]:
        print(f"   {line}")
    print("   ...")
    
    # Step 4: Peer scenario - Hurricane Electric
    print("\n" + "=" * 70)
    print("4. PEER SCENARIO: Hurricane Electric (AS6939)")
    print("=" * 70)
    print("\n   Regular peering - accept routes with authorized ASNs in path")
    
    peer_config = gen.generate_peer_policy("HE", 6939, authorized_asns)
    print("\n   Generated policy for HE peer:")
    for line in peer_config.split('\n')[:10]:
        print(f"   {line}")
    print("   ...")
    
    # Step 5: Peer-lock scenario
    print("\n" + "=" * 70)
    print("5. PEER-LOCK SCENARIO: Google signals directOnly")
    print("=" * 70)
    
    # Google updates RASA-AUTH with peer-lock signal
    rasa_db_peerlock = {
        "AS15169": RASAAuth(
            authorizedAS=15169,
            authorizedIn=[
                {"asSetName": "AS2914:AS-GLOBAL", "propagation": "directOnly"},  # Peer lock!
            ],
            strictMode=False
        ),
    }
    
    rasa_filter_peerlock = RASAFilter(rasa_db_peerlock)
    peer_lock_sets = rasa_filter_peerlock.get_peer_lock_list(15169)
    
    print(f"\n   AS15169 (Google) sets propagation=directOnly for AS2914:AS-GLOBAL")
    print(f"   Peer-lock applies to AS-SETs: {peer_lock_sets}")
    
    print("\n   NTT SHOULD configure:")
    print("   - ACCEPT routes with AS15169 from DIRECT BGP sessions")
    print("   - REJECT routes with AS15169 from TRANSIT/ROUTESERVERS")
    
    peerlock_config = gen.generate_peer_lock_policy(15169, 6939)
    print("\n   Generated peer-lock policy for Hurricane Electric:")
    for line in peerlock_config.split('\n'):
        print(f"   {line}")
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"""
Without RASA:    {len(all_asns)} ASNs in filter (anyone can include AS2914 customers)
With RASA:       {len(authorized_asns)} ASNs in filter (only authorized members)
Peer-Lock:       Additional BGP policy to reject indirect paths for locked ASNs

This demonstrates how RASA provides:
1. Member authorization (ASNs control inclusion)
2. Peer-lock signaling (members control route propagation)
3. Cryptographic validation (when RPKI signed)
""")


if __name__ == "__main__":
    simulate_ntt_scenario()
