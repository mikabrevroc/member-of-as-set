#!/usr/bin/env python3
"""
Circular Reference Detection

Demonstrates the circular reference detection algorithm from Section 9.
Shows how validators prevent infinite loops during AS-SET expansion.
"""

from rasa_validator import (
    RASAValidator, create_rasa_set, create_rasa_auth,
    RasaFlags, PropagationScope
)
from typing import Set, Tuple


def detect_circular_reference(asset_name: str, rasa_db: dict, 
                              seen: Set[str] = None, depth: int = 0,
                              max_depth: int = 10) -> Tuple[bool, list[dict]]:
    """
    Detect circular references in AS-SET expansion.
    
    Implements the algorithm from Section 9.1.
    
    Returns:
        (has_circular_ref, log)
    """
    if seen is None:
        seen = set()
    
    log = []
    indent = "  " * depth
    
    print(f"{indent}Expanding: {asset_name}")
    print(f"{indent}Seen set: {seen if seen else 'empty'}")
    
    # Check for circular reference
    if asset_name in seen:
        log.append({
            "action": "circular_detected",
            "asset": asset_name,
            "seen": list(seen),
            "message": f"Circular reference detected: {asset_name} already in {seen}"
        })
        print(f"{indent}⚠ CIRCULAR REFERENCE DETECTED!")
        print(f"{indent}   {asset_name} is already in seen set")
        print(f"{indent}   Stopping expansion of this branch")
        return True, log
    
    # Check max depth
    if depth >= max_depth:
        log.append({
            "action": "max_depth",
            "asset": asset_name,
            "depth": depth,
            "message": "Maximum depth reached"
        })
        print(f"{indent}⚠ Maximum depth ({max_depth}) reached")
        return False, log
    
    # Add to seen
    seen.add(asset_name)
    print(f"{indent}✓ Added {asset_name} to seen set")
    
    # Get RASA-SET
    rasa_set = rasa_db.get(asset_name)
    if not rasa_set:
        log.append({
            "action": "not_found",
            "asset": asset_name
        })
        print(f"{indent}✗ No RASA-SET found for {asset_name}")
        seen.remove(asset_name)
        return False, log
    
    # Process members
    if rasa_set.members:
        print(f"{indent}Members: {rasa_set.members}")
    
    # Process nested sets
    has_circular = False
    for nested in rasa_set.nestedSets:
        print(f"{indent}→ Processing nested: {nested}")
        circular, nested_log = detect_circular_reference(
            nested, rasa_db, seen.copy(), depth + 1, max_depth
        )
        log.extend(nested_log)
        if circular:
            has_circular = True
    
    # Remove from seen when backtracking (allows valid reuse)
    if asset_name in seen:
        seen.remove(asset_name)
        print(f"{indent}← Backtracking: removed {asset_name} from seen")
    
    return has_circular, log


def circular_detection_demo():
    """Demonstrate circular reference detection."""
    
    print("=" * 70)
    print("CIRCULAR REFERENCE DETECTION")
    print("=" * 70)
    print("\nScenario from draft Section 9")
    print("Demonstrates detection algorithm with example")
    print("-" * 70)
    
    # Create circular reference scenario
    print("\n📋 SETUP: Creating AS-SETs with circular reference")
    print("-" * 70)
    
    # AS2914:AS-GLOBAL contains AS64496:AS-SET
    rasa_set_2914 = create_rasa_set(
        name="AS2914:AS-GLOBAL",
        containing_as=2914,
        members=[64496],
        nested_sets=["AS64496:AS-SET"],
        flags=RasaFlags()
    )
    
    # AS64496:AS-SET contains AS398465 and... AS2914:AS-GLOBAL (circular!)
    rasa_set_64496 = create_rasa_set(
        name="AS64496:AS-SET",
        containing_as=64496,
        members=[398465],
        nested_sets=["AS2914:AS-GLOBAL"],  # Circular reference!
        flags=RasaFlags()
    )
    
    rasa_db = {
        "AS2914:AS-GLOBAL": rasa_set_2914,
        "AS64496:AS-SET": rasa_set_64496
    }
    
    print("\nAS-SET Definitions:")
    print("\n  AS2914:AS-GLOBAL:")
    print(f"    members: {rasa_set_2914.members}")
    print(f"    nestedSets: {rasa_set_2914.nestedSets}")
    
    print("\n  AS64496:AS-SET:")
    print(f"    members: {rasa_set_64496.members}")
    print(f"    nestedSets: {rasa_set_64496.nestedSets}")
    print(f"    ⚠ Note: Contains reference back to AS2914:AS-GLOBAL!")
    
    print("\n  Circular chain: AS2914 → AS64496 → AS2914 → ... (infinite loop)")
    
    # Demonstrate the detection
    print("\n" + "=" * 70)
    print("EXPANSION TRACE (with circular detection)")
    print("=" * 70)
    
    has_circular, log = detect_circular_reference("AS2914:AS-GLOBAL", rasa_db)
    
    # Show final result
    print("\n" + "=" * 70)
    print("RESULT")
    print("=" * 70)
    
    if has_circular:
        print("\n✓ Circular reference DETECTED and HANDLED")
        print("\nFinal AS-SET members:")
        print("  ✓ AS64496 (from AS2914:AS-GLOBAL direct members)")
        print("  ✓ AS398465 (from AS64496:AS-SET before circular detected)")
        print("  ✗ AS2914:AS-GLOBAL circular reference - EXPANSION STOPPED")
    
    print("\nAlgorithm prevented infinite loop!")
    
    # Show log
    print("\n" + "=" * 70)
    print("DETECTION LOG")
    print("=" * 70)
    
    for entry in log:
        action = entry.get("action")
        if action == "circular_detected":
            print(f"\n🚨 {action.upper()}")
            print(f"   Asset: {entry['asset']}")
            print(f"   Seen: {entry['seen']}")
            print(f"   Message: {entry['message']}")
        else:
            print(f"\n  {action}: {entry.get('asset', '')}")
    
    # Algorithm explanation
    print("\n" + "=" * 70)
    print("ALGORITHM (from Section 9.1)")
    print("=" * 70)
    
    print("\nDetection Algorithm:")
    print("""
  1. Initialize empty set 'seen'
  
  2. Before expanding any AS-SET:
     - Check if its name is already in 'seen'
     - If YES: Circular reference detected!
       → Stop expanding this branch
       → Log warning
       → Do not include any members
     - If NO: Add AS-SET name to 'seen'
  
  3. Continue expansion normally
  
  4. When backtracking from nested AS-SET:
     - Remove its name from 'seen'
     - This allows valid reuse in different branches
  
  5. Maintain 'seen' per expansion chain, not globally
    """)
    
    # Comparison: What happens without detection
    print("\n" + "=" * 70)
    print("COMPARISON: Without Circular Detection")
    print("=" * 70)
    
    print("\n❌ Without circular detection:")
    print("  AS2914:AS-GLOBAL")
    print("    → AS64496:AS-SET")
    print("      → AS2914:AS-GLOBAL")
    print("        → AS64496:AS-SET")
    print("          → AS2914:AS-GLOBAL")
    print("            → ... (infinite loop)")
    print("\n  Result: Validator hangs, crashes, or exhausts resources")
    
    print("\n✅ With circular detection:")
    print("  AS2914:AS-GLOBAL")
    print("    ✓ AS64496 (direct member)")
    print("    → AS64496:AS-SET")
    print("      ✓ AS398465 (member)")
    print("      → AS2914:AS-GLOBAL ⚠ CIRCULAR - STOP")
    print("\n  Result: Graceful handling, valid members included")
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    print("\n✅ Circular Detection Benefits:")
    print("  • Prevents infinite loops during AS-SET expansion")
    print("  • Protects against DoS via crafted AS-SET objects")
    print("  • Allows valid reuse of AS-SETs in different branches")
    print("  • Logs warnings for investigation")
    
    print("\n⚠️ Important Notes:")
    print("  • Circular references may indicate misconfiguration")
    print("  • Validators should log security events for circular refs")
    print("  • AS-SET owners should audit their nested sets")
    print("  • Multiple paths to same AS-SET is OK (valid reuse)")
    print("  • True circular (A→B→A) is NOT OK")
    
    return True


if __name__ == "__main__":
    circular_detection_demo()
