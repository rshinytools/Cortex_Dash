#!/usr/bin/env python
"""
Run Phase 1 tests to verify implementation
"""

import sys
import subprocess
import json
from datetime import datetime

def run_tests():
    """Run Phase 1 test suite"""
    
    print("\n" + "="*60)
    print("PHASE 1 WIDGET ARCHITECTURE - TEST SUITE")
    print("="*60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60 + "\n")
    
    test_modules = [
        {
            "name": "Database Schema Tests",
            "command": ["pytest", "tests/test_phase1_widget_architecture.py::TestPhase1DatabaseSchema", "-v"],
            "critical": True
        },
        {
            "name": "Widget Contract Tests",
            "command": ["pytest", "tests/test_phase1_widget_architecture.py::TestPhase1WidgetContracts", "-v"],
            "critical": True
        },
        {
            "name": "API Endpoint Tests",
            "command": ["pytest", "tests/test_phase1_widget_architecture.py::TestPhase1APIs", "-v"],
            "critical": False
        },
        {
            "name": "Integration Tests",
            "command": ["pytest", "tests/test_phase1_widget_architecture.py::TestPhase1Integration", "-v"],
            "critical": False
        }
    ]
    
    results = []
    all_passed = True
    
    for test in test_modules:
        print(f"\n{'='*60}")
        print(f"Running: {test['name']}")
        print('='*60)
        
        try:
            result = subprocess.run(
                test['command'],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            success = result.returncode == 0
            
            if success:
                print(f"✅ {test['name']} PASSED")
            else:
                print(f"❌ {test['name']} FAILED")
                if test['critical']:
                    all_passed = False
                    print("⚠️  Critical test failed!")
                
            results.append({
                "name": test['name'],
                "passed": success,
                "critical": test['critical'],
                "output": result.stdout,
                "errors": result.stderr
            })
            
        except subprocess.TimeoutExpired:
            print(f"⏱️ {test['name']} TIMEOUT")
            results.append({
                "name": test['name'],
                "passed": False,
                "critical": test['critical'],
                "output": "",
                "errors": "Test timed out after 60 seconds"
            })
            if test['critical']:
                all_passed = False
        
        except Exception as e:
            print(f"💥 {test['name']} ERROR: {e}")
            results.append({
                "name": test['name'],
                "passed": False,
                "critical": test['critical'],
                "output": "",
                "errors": str(e)
            })
            if test['critical']:
                all_passed = False
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for r in results if r['passed'])
    failed = len(results) - passed
    
    print(f"Total Tests: {len(results)}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"Success Rate: {(passed/len(results)*100):.1f}%")
    
    if all_passed:
        print("\n🎉 ALL CRITICAL TESTS PASSED!")
    else:
        print("\n⚠️  SOME CRITICAL TESTS FAILED")
    
    # Save results
    results_file = f"tests/phase1_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total": len(results),
                "passed": passed,
                "failed": failed,
                "all_critical_passed": all_passed
            },
            "results": results
        }, f, indent=2)
    
    print(f"\nDetailed results saved to: {results_file}")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(run_tests())