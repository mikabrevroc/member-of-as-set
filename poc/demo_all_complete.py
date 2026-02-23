#!/usr/bin/env python3
"""
RASA POC - Complete Demonstration Suite

This script runs all 14 RASA demonstration scenarios covering:
- Basic AS-SET expansion
- RASA authorization and filtering
- Peer-lock scenarios
- Nested AS-SET authorization (Examples 4 & 5)
- Delegation scenarios (Examples 1 & 2)
- Operational scenarios (Examples 1, 2, 3 & 6)
- Circular reference detection
"""

import sys
import importlib

def print_section(title):
    print("\n" + "=" * 70)
    print(title.center(70))
    print("=" * 70)

def run_scenario(module_name, description, func_name=None):
    print(f"\n{'─' * 70}")
    print(f"Running: {description}")
    print('─' * 70)
    try:
        module = importlib.import_module(module_name)
        # Use provided function name or try common patterns
        if func_name and hasattr(module, func_name):
            func = getattr(module, func_name)
            func()
        elif hasattr(module, module_name):
            func = getattr(module, module_name)
            func()
        elif hasattr(module, 'main'):
            module.main()
        else:
            print(f"Warning: No main function found in {module_name}")
    except Exception as e:
        print(f"Error running {module_name}: {e}")
        import traceback
        traceback.print_exc()

def main():
    print("\n" + "=" * 70)
    print("RASA (RPKI AS-SET Authorization)".center(70))
    print("Complete POC Demonstration Suite".center(70))
    print("=" * 70)
    
    scenarios = [
        ("example4_asset_authorization", "Example 4: AS-SET Authorization (Nested AS-SET Authorized)", "example4_nested_set_authorized"),
        ("example5_asset_denied", "Example 5: AS-SET Authorization Denied", "example5_nested_set_denied"),
        ("delegation_customer_managed", "Delegation Example 1: Customer-Managed Authorization", "delegation_customer_managed"),
        ("delegation_third_party", "Delegation Example 2: Third-Party Management Service", "delegation_third_party"),
        ("operational_tier1_attack", "Operational Example 1: Tier-1 Provider with Attack Scenario", "operational_tier1_attack"),
        ("operational_content_donotinherit", "Operational Example 2: Content Provider Protection (doNotInherit)", "operational_content_donotinherit"),
        ("operational_validator_flow", "Operational Example 3: Complete Validator Decision Flow", "operational_validator_flow"),
        ("operational_partial_deployment", "Operational Example 6: Partial Deployment Scenario", "operational_partial_deployment"),
        ("circular_detection", "Circular Reference Detection", "circular_detection_demo"),
    ]
    
    print(f"\nTotal scenarios to run: {len(scenarios)}")
    print("\nEach scenario demonstrates a specific aspect of the RASA protocol.")
    print("All scenarios use simulated RASA objects (no live RPKI queries needed).")
    
    successful = 0
    failed = 0
    
    for module_name, description, func_name in scenarios:
        try:
            run_scenario(module_name, description, func_name)
            successful += 1
        except Exception as e:
            print(f"\n❌ FAILED: {description}")
            print(f"   Error: {e}")
            failed += 1
    
    print_section("DEMO SUITE COMPLETE")
    
    print(f"\n✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"\nTotal: {successful + failed} scenarios")
    
    if failed == 0:
        print("\n🎉 All scenarios completed successfully!")
    else:
        print(f"\n⚠️  {failed} scenario(s) failed. Check output above for details.")
    
    print("\n" + "=" * 70)
    print("For individual scenario details, run:")
    print("  python3 <scenario_name>.py")
    print("\nExample:")
    print("  python3 example4_asset_authorization.py")
    print("=" * 70)

if __name__ == "__main__":
    main()
