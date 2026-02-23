#!/usr/bin/env python3
"""
RASA Validation Utilities

Shared validation logic for all RASA POC scenarios.
Implements the core RASA verification algorithms from the specification.
"""

from dataclasses import dataclass, field
from typing import Set, List, Dict, Optional, Tuple, Any
from datetime import datetime
from enum import Enum


class PropagationScope(Enum):
    """Propagation scope for AS-SET inclusion."""
    UNRESTRICTED = 0
    DIRECT_ONLY = 1


@dataclass
class RasaFlags:
    """RASA-SET flags."""
    doNotInherit: bool = False
    authoritative: bool = False


@dataclass
class RasaAuthFlags:
    """RASA-AUTH flags."""
    strictMode: bool = False


@dataclass
class AuthorizedEntry:
    """Authorized AS-SET entry with propagation constraint."""
    asSetName: str
    propagation: PropagationScope = PropagationScope.UNRESTRICTED


@dataclass
class RasaSetContent:
    """RASA-SET object content."""
    version: int = 0
    asSetName: str = ""
    containingAS: int = 0
    members: List[int] = field(default_factory=list)
    nestedSets: List[str] = field(default_factory=list)
    irrSource: Optional[str] = None
    flags: RasaFlags = field(default_factory=RasaFlags)
    notBefore: str = ""
    notAfter: str = ""


@dataclass
class RasaAuthContent:
    """RASA-AUTH object content."""
    version: int = 0
    authorizedAS: Optional[int] = None
    authorizedSet: Optional[str] = None
    authorizedIn: List[AuthorizedEntry] = field(default_factory=list)
    flags: RasaAuthFlags = field(default_factory=RasaAuthFlags)
    notBefore: str = ""
    notAfter: str = ""


@dataclass
class DelegationToken:
    """RASA delegation token."""
    delegatedTo: str  # ASN or entity identifier
    scope: List[str]  # AS-SETs covered
    notBefore: str
    notAfter: str
    issuedBy: int  # Containing AS


class RASAValidator:
    """RASA object validator implementing the specification algorithms."""
    
    def __init__(self, rasa_db: Dict[str, Any], delegation_db: Optional[Dict[str, Any]] = None):
        """
        Initialize validator with RASA database.
        
        Args:
            rasa_db: Dictionary mapping AS-SET names to RasaSetContent and
                    ASN strings (e.g., "AS12345") to RasaAuthContent
            delegation_db: Optional delegation token database
        """
        self.rasa_db = rasa_db
        self.delegation_db = delegation_db or {}
        self.log: List[Dict] = []
    
    def check_member_auth(self, asn: int, asset_name: str) -> Tuple[bool, str]:
        """
        Check if an ASN is authorized to be in an AS-SET.
        
        Implements the conflict resolution algorithm from Section 6.2.
        
        Returns:
            (is_authorized, reason)
        """
        auth_key = f"AS{asn}"
        auth_obj = self.rasa_db.get(auth_key)
        
        if not auth_obj:
            self.log.append({
                "asn": asn,
                "asset": asset_name,
                "authorized": True,
                "reason": "No RASA-AUTH (default allow)"
            })
            return True, "No RASA-AUTH (default allow)"
        
        # Check if asset is in authorizedIn list
        for entry in auth_obj.authorizedIn:
            if entry.asSetName == asset_name:
                self.log.append({
                    "asn": asn,
                    "asset": asset_name,
                    "authorized": True,
                    "reason": f"Authorized ({entry.propagation.name})"
                })
                return True, f"Authorized ({entry.propagation.name})"
        
        # Not authorized
        if auth_obj.flags.strictMode:
            self.log.append({
                "asn": asn,
                "asset": asset_name,
                "authorized": False,
                "reason": "REJECTED: strictMode=TRUE, not authorized",
                "severity": "security_event"
            })
            return False, "REJECTED: strictMode=TRUE, not authorized"
        
        self.log.append({
            "asn": asn,
            "asset": asset_name,
            "authorized": False,
            "reason": "REJECTED: not in authorizedIn",
            "severity": "warning"
        })
        return False, "REJECTED: not in authorizedIn"
    
    def check_asset_set_auth(self, nested_set: str, parent_set: str) -> Tuple[bool, str]:
        """
        Check if a nested AS-SET is authorized to be in a parent AS-SET.
        
        For nested AS-SETs, we look for RASA-AUTH with authorizedSet.
        
        Returns:
            (is_authorized, reason)
        """
        auth_key = nested_set
        auth_obj = self.rasa_db.get(auth_key)
        
        if not auth_obj:
            self.log.append({
                "nested_set": nested_set,
                "parent_set": parent_set,
                "authorized": True,
                "reason": "No RASA-AUTH (default allow)"
            })
            return True, "No RASA-AUTH (default allow)"
        
        # Check if this is a RasaAuthContent object (has authorizedIn)
        if not hasattr(auth_obj, 'authorizedIn'):
            # This is a RasaSetContent, not RasaAuthContent - default allow
            self.log.append({
                "nested_set": nested_set,
                "parent_set": parent_set,
                "authorized": True,
                "reason": "No RASA-AUTH for AS-SET (default allow)"
            })
            return True, "No RASA-AUTH for AS-SET (default allow)"
        
        # Check if parent is in authorizedIn list
        for entry in auth_obj.authorizedIn:
            if entry.asSetName == parent_set:
                self.log.append({
                    "nested_set": nested_set,
                    "parent_set": parent_set,
                    "authorized": True,
                    "reason": f"Authorized ({entry.propagation.name})"
                })
                return True, f"Authorized ({entry.propagation.name})"
        
        # Not authorized
        if auth_obj.flags.strictMode:
            self.log.append({
                "nested_set": nested_set,
                "parent_set": parent_set,
                "authorized": False,
                "reason": "REJECTED: strictMode=TRUE, not authorized",
                "severity": "security_event"
            })
            return False, "REJECTED: strictMode=TRUE, not authorized"
        
        self.log.append({
            "nested_set": nested_set,
            "parent_set": parent_set,
            "authorized": False,
            "reason": "REJECTED: not in authorizedIn",
            "severity": "warning"
        })
        return False, "REJECTED: not in authorizedIn"
    
    def validate_delegation(self, rasa_obj: Any, signer_id: str) -> Tuple[bool, str]:
        """
        Validate that a RASA object was published by an authorized entity.
        
        Implements delegation validation from Section 3.3.
        
        Returns:
            (is_valid, reason)
        """
        # Get the containing AS from the object
        if isinstance(rasa_obj, RasaSetContent):
            containing_as = rasa_obj.containingAS
        elif isinstance(rasa_obj, RasaAuthContent):
            containing_as = rasa_obj.authorizedAS
        else:
            return False, "Unknown RASA object type"
        
        # Check if signer matches containing AS
        if signer_id == f"AS{containing_as}":
            return True, "Directly published by AS-SET owner"
        
        # Check for delegation token
        token_key = f"{containing_as}:{signer_id}"
        token = self.delegation_db.get(token_key)
        
        if not token:
            return False, f"No delegation token found for {signer_id} to publish for AS{containing_as}"
        
        # Check token validity
        now = datetime.utcnow().isoformat()
        if now < token.notBefore or now > token.notAfter:
            return False, "Delegation token expired"
        
        return True, f"Valid delegation from AS{containing_as} to {signer_id}"
    
    def get_peer_lock_sets(self, asn: int) -> List[str]:
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
            if entry.propagation == PropagationScope.DIRECT_ONLY:
                peer_lock_sets.append(entry.asSetName)
        
        return peer_lock_sets
    
    def expand_with_rasa(self, asset_name: str, irr_members: List[int], 
                        irr_nested: List[str], max_depth: int = 10,
                        seen: Optional[Set[str]] = None) -> Tuple[Set[int], List[Dict]]:
        """
        Expand AS-SET with RASA authorization.
        
        Implements the AS-SET expansion algorithm from Section 5.3.
        
        Args:
            asset_name: Name of the AS-SET to expand
            irr_members: List of member ASNs from IRR
            irr_nested: List of nested AS-SETs from IRR
            max_depth: Maximum recursion depth
            seen: Set of already-seen AS-SETs (for circular detection)
            
        Returns:
            (authorized_asns, log_entries)
        """
        if seen is None:
            seen = set()
        
        # Circular reference detection
        if asset_name in seen:
            self.log.append({
                "action": "circular_reference",
                "asset": asset_name,
                "message": "Circular reference detected, skipping"
            })
            return set(), self.log
        
        if max_depth <= 0:
            self.log.append({
                "action": "max_depth",
                "asset": asset_name,
                "message": "Maximum depth reached"
            })
            return set(), self.log
        
        seen.add(asset_name)
        
        # Check for RASA-SET
        rasa_set = self.rasa_db.get(asset_name)
        if rasa_set and isinstance(rasa_set, RasaSetContent):
            if rasa_set.flags.authoritative:
                # Use only RASA data, ignore IRR
                self.log.append({
                    "action": "authoritative_rasa",
                    "asset": asset_name,
                    "message": "Using authoritative RASA-SET, ignoring IRR"
                })
                members = rasa_set.members
                nested_sets = rasa_set.nestedSets
            else:
                # Merge RASA with IRR
                self.log.append({
                    "action": "merge_rasa",
                    "asset": asset_name,
                    "message": "Merging RASA-SET with IRR data"
                })
                members = list(set(irr_members) | set(rasa_set.members))
                nested_sets = list(set(irr_nested) | set(rasa_set.nestedSets))
        else:
            # No RASA, use IRR
            self.log.append({
                "action": "irr_only",
                "asset": asset_name,
                "message": "No RASA-SET found, using IRR data"
            })
            members = irr_members
            nested_sets = irr_nested
        
        # Filter members based on RASA-AUTH
        authorized_asns = set()
        for asn in members:
            is_auth, reason = self.check_member_auth(asn, asset_name)
            if is_auth:
                authorized_asns.add(asn)
        
        # Process nested AS-SETs
        for nested_set in nested_sets:
            # Check if nested set is authorized
            is_auth, reason = self.check_asset_set_auth(nested_set, asset_name)
            
            if not is_auth:
                continue
            
            # Check doNotInherit flag
            if rasa_set and isinstance(rasa_set, RasaSetContent) and rasa_set.flags.doNotInherit:
                self.log.append({
                    "action": "do_not_inherit",
                    "nested_set": nested_set,
                    "message": "doNotInherit set, including reference only"
                })
                # Don't expand, just include the reference
                continue
            
            # Recursively expand nested set
            # In real implementation, would fetch IRR data for nested set
            # For POC, we assume nested sets have no further members
            self.log.append({
                "action": "expand_nested",
                "nested_set": nested_set,
                "parent": asset_name
            })
        
        return authorized_asns, self.log


def create_rasa_set(name: str, containing_as: int, members: List[int],
                   nested_sets: Optional[List[str]] = None,
                   flags: Optional[RasaFlags] = None,
                   irr_source: Optional[str] = None) -> RasaSetContent:
    """Helper to create RASA-SET content."""
    return RasaSetContent(
        asSetName=name,
        containingAS=containing_as,
        members=members,
        nestedSets=nested_sets or [],
        flags=flags or RasaFlags(),
        irrSource=irr_source,
        notBefore=datetime.utcnow().isoformat(),
        notAfter="2025-12-31T23:59:59Z"
    )


def create_rasa_auth(asn: Optional[int] = None, asset_set: Optional[str] = None,
                    authorized_in: Optional[List[Tuple[str, PropagationScope]]] = None,
                    strict_mode: bool = False) -> RasaAuthContent:
    """Helper to create RASA-AUTH content."""
    entries = []
    if authorized_in:
        for name, prop in authorized_in:
            entries.append(AuthorizedEntry(asSetName=name, propagation=prop))
    
    return RasaAuthContent(
        authorizedAS=asn,
        authorizedSet=asset_set,
        authorizedIn=entries,
        flags=RasaAuthFlags(strictMode=strict_mode),
        notBefore=datetime.utcnow().isoformat(),
        notAfter="2025-12-31T23:59:59Z"
    )


if __name__ == "__main__":
    # Test the validator
    print("RASA Validator Utilities")
    print("=" * 70)
    
    # Create sample RASA database
    rasa_db = {
        "AS2914:AS-GLOBAL": create_rasa_set(
            "AS2914:AS-GLOBAL", 2914, 
            [64496, 64497, 15169],
            flags=RasaFlags(authoritative=True)
        ),
        "AS15169": create_rasa_auth(
            asn=15169,
            authorized_in=[
                ("AS2914:AS-GLOBAL", PropagationScope.UNRESTRICTED),
                ("AS1299:AS-TWELVE99", PropagationScope.UNRESTRICTED)
            ],
            strict_mode=False
        )
    }
    
    validator = RASAValidator(rasa_db)
    
    # Test member authorization
    print("\nTest 1: Member authorization check")
    result, reason = validator.check_member_auth(15169, "AS2914:AS-GLOBAL")
    print(f"AS15169 in AS2914:AS-GLOBAL: {result} - {reason}")
    
    result, reason = validator.check_member_auth(15169, "AS-EVIL:CUSTOMERS")
    print(f"AS15169 in AS-EVIL:CUSTOMERS: {result} - {reason}")
    
    print("\nValidation log:")
    for entry in validator.log:
        print(f"  {entry}")
