#!/usr/bin/env python3
# ABOUTME: Test runner script for transformation tests
# ABOUTME: Runs all transformation-related tests with proper configuration

import sys
import os
import pytest
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def run_transformation_tests():
    """Run all transformation-related tests."""
    print("Running transformation tests...")
    
    # Test categories
    test_suites = [
        # API tests
        ("API Tests", "tests/api/test_study_transformation.py::TestStudyTransformationAPI"),
        
        # Service tests
        ("Service Tests", "tests/api/test_study_transformation.py::TestStudyTransformationService"),
        
        # Security tests
        ("Security Tests", "tests/api/test_study_transformation.py::TestStudyTransformationService::test_validate_script_security"),
        
        # Edge case tests
        ("Edge Cases", "tests/api/test_study_transformation.py::TestTransformationEdgeCases"),
        
        # Performance tests
        ("Performance Tests", "tests/api/test_study_transformation.py::TestTransformationPerformance"),
    ]
    
    # Run each test suite
    for suite_name, test_path in test_suites:
        print(f"\n{'='*60}")
        print(f"Running {suite_name}")
        print('='*60)
        
        result = pytest.main([
            "-v",
            test_path,
            "--tb=short",
            "--maxfail=1"
        ])
        
        if result != 0:
            print(f"\n❌ {suite_name} failed!")
            return result
        else:
            print(f"\n✅ {suite_name} passed!")
    
    print("\n" + "="*60)
    print("✅ All transformation tests passed!")
    print("="*60)
    return 0


def run_specific_test(test_name: str):
    """Run a specific test by name."""
    print(f"Running specific test: {test_name}")
    
    result = pytest.main([
        "-v",
        "-k", test_name,
        "tests/api/test_study_transformation.py",
        "--tb=short"
    ])
    
    return result


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Run specific test if provided
        exit_code = run_specific_test(sys.argv[1])
    else:
        # Run all transformation tests
        exit_code = run_transformation_tests()
    
    sys.exit(exit_code)