#!/usr/bin/env python3
# ABOUTME: Test execution script with comprehensive reporting for Clinical Dashboard Platform
# ABOUTME: Runs pytest with different configurations and generates detailed reports in Reports/ folder

import os
import sys
import argparse
import subprocess
from datetime import datetime
from pathlib import Path
import json

class TestRunner:
    """Orchestrates test execution and report generation"""
    
    def __init__(self):
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.report_dir = Path(f"Reports/{self.timestamp}")
        self.report_dir.mkdir(parents=True, exist_ok=True)
        
    def run_tests(self, args):
        """Execute tests based on command line arguments"""
        
        # Build pytest command
        cmd = ["pytest"]
        
        # Add test selection
        if args.phase:
            cmd.extend(["-m", f"phase{args.phase}"])
        elif args.type:
            cmd.extend(["-m", args.type])
        elif args.pattern:
            cmd.append(args.pattern)
        
        # Add specific test file if provided
        if args.file:
            cmd.append(args.file)
            
        # Add compliance tests if requested
        if args.compliance:
            cmd.extend(["-m", "compliance"])
            
        # Add performance tests if requested
        if args.performance:
            cmd.extend(["-m", "performance"])
            
        # Override output paths to use timestamp directory
        cmd.extend([
            f"--html={self.report_dir}/test_report.html",
            f"--junit-xml={self.report_dir}/junit.xml",
            f"--cov-report=html:{self.report_dir}/coverage",
            f"--cov-report=json:{self.report_dir}/coverage.json"
        ])
        
        # Add extra pytest args
        if args.pytest_args:
            cmd.extend(args.pytest_args.split())
        
        # Show command being executed
        print(f"\n{'='*60}")
        print(f"Executing: {' '.join(cmd)}")
        print(f"Reports will be saved to: {self.report_dir}")
        print(f"{'='*60}\n")
        
        # Run tests
        result = subprocess.run(cmd, capture_output=False)
        
        # Generate summary report
        self.generate_summary_report(result.returncode)
        
        return result.returncode
    
    def generate_summary_report(self, return_code):
        """Generate a summary report of the test execution"""
        
        summary = {
            "execution_time": datetime.now().isoformat(),
            "test_result": "PASSED" if return_code == 0 else "FAILED",
            "report_directory": str(self.report_dir),
            "reports_generated": [
                "test_report.html",
                "junit.xml", 
                "coverage/index.html",
                "coverage.json"
            ]
        }
        
        # Try to load test results if available
        junit_path = self.report_dir / "junit.xml"
        if junit_path.exists():
            # Parse basic stats from JUnit XML
            import xml.etree.ElementTree as ET
            tree = ET.parse(junit_path)
            root = tree.getroot()
            
            testsuite = root.find('.//testsuite')
            if testsuite is not None:
                summary["test_stats"] = {
                    "total": int(testsuite.get('tests', 0)),
                    "passed": int(testsuite.get('tests', 0)) - int(testsuite.get('failures', 0)) - int(testsuite.get('errors', 0)),
                    "failed": int(testsuite.get('failures', 0)),
                    "errors": int(testsuite.get('errors', 0)),
                    "skipped": int(testsuite.get('skipped', 0)),
                    "time": float(testsuite.get('time', 0))
                }
        
        # Load coverage data if available
        coverage_path = self.report_dir / "coverage.json"
        if coverage_path.exists():
            with open(coverage_path) as f:
                coverage_data = json.load(f)
                summary["coverage"] = {
                    "percent_covered": coverage_data.get("totals", {}).get("percent_covered", 0),
                    "num_statements": coverage_data.get("totals", {}).get("num_statements", 0),
                    "missing_lines": coverage_data.get("totals", {}).get("missing_lines", 0)
                }
        
        # Save summary
        summary_path = self.report_dir / "summary.json"
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        # Print summary to console
        print(f"\n{'='*60}")
        print("TEST EXECUTION SUMMARY")
        print(f"{'='*60}")
        print(f"Result: {summary['test_result']}")
        print(f"Reports saved to: {self.report_dir}")
        
        if "test_stats" in summary:
            stats = summary["test_stats"]
            print(f"\nTest Statistics:")
            print(f"  Total:   {stats['total']}")
            print(f"  Passed:  {stats['passed']}")
            print(f"  Failed:  {stats['failed']}")
            print(f"  Errors:  {stats['errors']}")
            print(f"  Skipped: {stats['skipped']}")
            print(f"  Time:    {stats['time']:.2f}s")
            
        if "coverage" in summary:
            cov = summary["coverage"]
            print(f"\nCode Coverage:")
            print(f"  Coverage: {cov['percent_covered']:.1f}%")
            print(f"  Statements: {cov['num_statements']}")
            print(f"  Missing: {cov['missing_lines']}")
        
        print(f"\nView detailed reports:")
        print(f"  HTML Report: {self.report_dir}/test_report.html")
        print(f"  Coverage: {self.report_dir}/coverage/index.html")
        print(f"{'='*60}\n")


def main():
    """Main entry point for test runner"""
    
    parser = argparse.ArgumentParser(
        description="Clinical Dashboard Platform Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all tests
  python run_tests.py
  
  # Run specific phase tests
  python run_tests.py --phase 1
  python run_tests.py --phase 3
  
  # Run compliance tests only
  python run_tests.py --compliance
  
  # Run specific test type
  python run_tests.py --type unit
  python run_tests.py --type integration
  
  # Run specific test file
  python run_tests.py --file tests/test_phase1_foundation.py
  
  # Run with custom pytest arguments
  python run_tests.py --pytest-args "-v --tb=long"
  
  # Run performance tests
  python run_tests.py --performance
        """
    )
    
    parser.add_argument(
        "--phase",
        type=int,
        choices=range(1, 10),
        help="Run tests for specific implementation phase (1-9)"
    )
    
    parser.add_argument(
        "--type",
        choices=["unit", "integration", "e2e", "smoke"],
        help="Run specific type of tests"
    )
    
    parser.add_argument(
        "--compliance",
        action="store_true",
        help="Run compliance tests (21 CFR Part 11, HIPAA)"
    )
    
    parser.add_argument(
        "--performance",
        action="store_true",
        help="Run performance tests"
    )
    
    parser.add_argument(
        "--file",
        help="Run specific test file"
    )
    
    parser.add_argument(
        "--pattern",
        help="Run tests matching pattern (e.g., 'test_*rbac*')"
    )
    
    parser.add_argument(
        "--pytest-args",
        help="Additional arguments to pass to pytest"
    )
    
    args = parser.parse_args()
    
    # Create test runner
    runner = TestRunner()
    
    # Execute tests
    return_code = runner.run_tests(args)
    
    # Exit with same code as pytest
    sys.exit(return_code)


if __name__ == "__main__":
    main()