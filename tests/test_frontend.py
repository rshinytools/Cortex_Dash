#!/usr/bin/env python3
# ABOUTME: Frontend testing script for Clinical Dashboard Platform
# ABOUTME: Tests frontend pages and functionality

import requests
import time
from typing import Dict, List

BASE_URL = "http://localhost:3000"

class FrontendTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = {
            "passed": [],
            "failed": [],
            "errors": []
        }
    
    def log_result(self, test_name: str, success: bool, details: str = ""):
        """Log test results"""
        if success:
            self.test_results["passed"].append(test_name)
            print(f"✅ {test_name}")
        else:
            self.test_results["failed"].append(test_name)
            print(f"❌ {test_name}: {details}")
    
    def test_page_loads(self):
        """Test if various pages load correctly"""
        print("\n=== Testing Frontend Pages ===")
        
        pages = [
            ("/", "Home/Login Page"),
            ("/api/auth/signin", "Login Page"),
            ("/dashboard", "Dashboard (should redirect)"),
            ("/studies", "Studies (should redirect)"),
            ("/admin", "Admin (should redirect)"),
            ("/settings", "Settings (should redirect)")
        ]
        
        for path, name in pages:
            try:
                response = self.session.get(f"{BASE_URL}{path}", allow_redirects=False)
                if response.status_code in [200, 307, 302]:
                    self.log_result(f"Load {name}", True)
                    if response.status_code in [307, 302]:
                        print(f"   Redirects to: {response.headers.get('location', 'unknown')}")
                else:
                    self.log_result(f"Load {name}", False, f"Status: {response.status_code}")
            except Exception as e:
                self.log_result(f"Load {name}", False, str(e))
    
    def test_static_assets(self):
        """Test if static assets are served"""
        print("\n=== Testing Static Assets ===")
        
        # Test Next.js build info
        try:
            response = self.session.get(f"{BASE_URL}/_next/static/chunks/webpack.js", allow_redirects=False)
            if response.status_code == 200:
                self.log_result("Next.js Static Assets", True)
            else:
                self.log_result("Next.js Static Assets", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Next.js Static Assets", False, str(e))
    
    def test_api_routes(self):
        """Test frontend API routes"""
        print("\n=== Testing Frontend API Routes ===")
        
        # Test auth session endpoint
        try:
            response = self.session.get(f"{BASE_URL}/api/auth/session")
            if response.status_code == 200:
                self.log_result("Auth Session API", True)
                session_data = response.json()
                print(f"   Session: {session_data}")
            else:
                self.log_result("Auth Session API", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Auth Session API", False, str(e))
    
    def generate_report(self):
        """Generate test report"""
        print("\n" + "="*50)
        print("FRONTEND TEST REPORT")
        print("="*50)
        print(f"Total Tests: {len(self.test_results['passed']) + len(self.test_results['failed'])}")
        print(f"✅ Passed: {len(self.test_results['passed'])}")
        print(f"❌ Failed: {len(self.test_results['failed'])}")
        
        if self.test_results['failed']:
            print("\nFailed Tests:")
            for test in self.test_results['failed']:
                print(f"  - {test}")
        
        success_rate = (len(self.test_results['passed']) / 
                       (len(self.test_results['passed']) + len(self.test_results['failed'])) * 100) \
                      if (self.test_results['passed'] or self.test_results['failed']) else 0
        
        print(f"\nSuccess Rate: {success_rate:.1f}%")
    
    def run_all_tests(self):
        """Run all frontend tests"""
        print("🌐 Starting Frontend Testing")
        print("="*50)
        
        self.test_page_loads()
        self.test_static_assets()
        self.test_api_routes()
        self.generate_report()


if __name__ == "__main__":
    tester = FrontendTester()
    tester.run_all_tests()