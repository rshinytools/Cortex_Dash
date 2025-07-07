#!/usr/bin/env python3
# ABOUTME: Comprehensive test script for Clinical Dashboard Platform
# ABOUTME: Tests all API endpoints and features systematically

import requests
import json
import time
import uuid
from datetime import datetime
from typing import Dict, Any, List

BASE_URL = "http://localhost:8000"
ADMIN_EMAIL = "admin@sagarmatha.ai"
ADMIN_PASSWORD = "adadad123"

class ClinicalDashboardTester:
    def __init__(self):
        self.token = None
        self.org_id = None
        self.study_id = None
        self.data_source_id = None
        self.dashboard_template_id = None
        self.widget_id = None
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
    
    def log_error(self, test_name: str, error: str):
        """Log test errors"""
        self.test_results["errors"].append(f"{test_name}: {error}")
        print(f"🔥 ERROR in {test_name}: {error}")
    
    def test_authentication(self):
        """Test authentication endpoints"""
        print("\n=== Testing Authentication ===")
        
        # Test login
        try:
            response = requests.post(
                f"{BASE_URL}/api/v1/login/access-token",
                data={
                    "username": ADMIN_EMAIL,
                    "password": ADMIN_PASSWORD
                }
            )
            if response.status_code == 200:
                self.token = response.json()["access_token"]
                self.log_result("Login", True)
            else:
                self.log_result("Login", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_error("Login", str(e))
        
        # Test get current user
        if self.token:
            try:
                response = requests.get(
                    f"{BASE_URL}/api/v1/users/me",
                    headers={"Authorization": f"Bearer {self.token}"}
                )
                if response.status_code == 200:
                    user_data = response.json()
                    self.log_result("Get Current User", True)
                    print(f"   User: {user_data['email']}, Role: {user_data['role']}")
                else:
                    self.log_result("Get Current User", False, f"Status: {response.status_code}")
            except Exception as e:
                self.log_error("Get Current User", str(e))
    
    def test_organization_management(self):
        """Test organization CRUD operations"""
        print("\n=== Testing Organization Management ===")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # Create organization
        try:
            org_data = {
                "name": f"Test Organization {int(time.time())}",
                "slug": f"test-org-{int(time.time())}",
                "active": True
            }
            response = requests.post(
                f"{BASE_URL}/api/v1/organizations/",
                json=org_data,
                headers=headers
            )
            if response.status_code == 200:
                org = response.json()
                self.org_id = org["id"]
                self.log_result("Create Organization", True)
                print(f"   Created: {org['name']} (ID: {self.org_id})")
            else:
                self.log_result("Create Organization", False, f"Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.log_error("Create Organization", str(e))
        
        # List organizations
        try:
            response = requests.get(
                f"{BASE_URL}/api/v1/organizations/",
                headers=headers
            )
            if response.status_code == 200:
                orgs = response.json()
                self.log_result("List Organizations", True)
                # Handle both list and paginated response formats
                if isinstance(orgs, list):
                    print(f"   Found {len(orgs)} organizations")
                elif isinstance(orgs, dict) and 'count' in orgs:
                    print(f"   Found {orgs['count']} organizations")
                else:
                    print(f"   Response: {orgs}")
            else:
                self.log_result("List Organizations", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_error("List Organizations", str(e))
        
        # Get organization by ID
        if self.org_id:
            try:
                response = requests.get(
                    f"{BASE_URL}/api/v1/organizations/{self.org_id}",
                    headers=headers
                )
                if response.status_code == 200:
                    self.log_result("Get Organization by ID", True)
                else:
                    self.log_result("Get Organization by ID", False, f"Status: {response.status_code}")
            except Exception as e:
                self.log_error("Get Organization by ID", str(e))
    
    def test_study_management(self):
        """Test study CRUD operations"""
        print("\n=== Testing Study Management ===")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # Create study
        if self.org_id:
            try:
                timestamp = int(time.time())
                study_data = {
                    "name": f"test_study_{timestamp}",
                    "code": f"TST{timestamp % 1000}",
                    "protocol_number": f"TEST-{timestamp}",
                    "description": "Test study for comprehensive testing",
                    "org_id": self.org_id,
                    "therapeutic_area": "Oncology",
                    "phase": "phase_3",
                    "sponsor": "Test Sponsor",
                    "indication": "Test Indication",
                    "study_type": "Interventional"
                }
                response = requests.post(
                    f"{BASE_URL}/api/v1/studies/",
                    json=study_data,
                    headers=headers
                )
                if response.status_code == 200:
                    study = response.json()
                    self.study_id = study["id"]
                    self.log_result("Create Study", True)
                    print(f"   Created: {study['name']} (ID: {self.study_id})")
                else:
                    self.log_result("Create Study", False, f"Status: {response.status_code}, Response: {response.text}")
            except Exception as e:
                self.log_error("Create Study", str(e))
        
        # List studies
        try:
            response = requests.get(
                f"{BASE_URL}/api/v1/studies/",
                headers=headers
            )
            if response.status_code == 200:
                studies = response.json()
                self.log_result("List Studies", True)
                # Handle both list and paginated response formats
                if isinstance(studies, list):
                    print(f"   Found {len(studies)} studies")
                elif isinstance(studies, dict) and 'count' in studies:
                    print(f"   Found {studies['count']} studies")
                else:
                    print(f"   Response: {studies}")
            else:
                self.log_result("List Studies", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_error("List Studies", str(e))
        
        # Initialize study (required for dashboard features)
        if self.study_id:
            try:
                response = requests.post(
                    f"{BASE_URL}/api/v1/studies/{self.study_id}/initialize",
                    json={},  # Send empty body with default values
                    headers=headers
                )
                if response.status_code == 200:
                    self.log_result("Initialize Study", True)
                else:
                    self.log_result("Initialize Study", False, f"Status: {response.status_code}")
            except Exception as e:
                self.log_error("Initialize Study", str(e))
    
    def test_data_sources(self):
        """Test data source management"""
        print("\n=== Testing Data Sources ===")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # Create data source
        if self.study_id:
            try:
                data_source = {
                    "name": "Test Data Source",
                    "type": "zip_upload",
                    "description": "Test data source for uploads",
                    "study_id": self.study_id,
                    "config": {
                        "allowed_file_types": [".sas7bdat", ".csv", ".xpt"],
                        "max_file_size_mb": 100
                    }
                }
                response = requests.post(
                    f"{BASE_URL}/api/v1/studies/{self.study_id}/data-sources",
                    json=data_source,
                    headers=headers
                )
                if response.status_code == 200:
                    ds = response.json()
                    self.data_source_id = ds["id"]
                    self.log_result("Create Data Source", True)
                    print(f"   Created: {ds['name']} (Type: {ds['type']})")
                else:
                    self.log_result("Create Data Source", False, f"Status: {response.status_code}, Response: {response.text}")
            except Exception as e:
                self.log_error("Create Data Source", str(e))
        
        # List data sources
        if self.study_id:
            try:
                response = requests.get(
                    f"{BASE_URL}/api/v1/studies/{self.study_id}/data-sources",
                    headers=headers
                )
                if response.status_code == 200:
                    sources = response.json()
                    self.log_result("List Data Sources", True)
                    # Handle both list and paginated response formats
                    if isinstance(sources, list):
                        print(f"   Found {len(sources)} data sources")
                    elif isinstance(sources, dict) and 'count' in sources:
                        print(f"   Found {sources['count']} data sources")
                    else:
                        print(f"   Response: {sources}")
                else:
                    self.log_result("List Data Sources", False, f"Status: {response.status_code}")
            except Exception as e:
                self.log_error("List Data Sources", str(e))
    
    def test_dashboard_templates(self):
        """Test dashboard template functionality"""
        print("\n=== Testing Dashboard Templates ===")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # List dashboard templates
        try:
            response = requests.get(
                f"{BASE_URL}/api/v1/dashboard-templates/",
                headers=headers
            )
            if response.status_code == 200:
                templates = response.json()
                self.log_result("List Dashboard Templates", True)
                print(f"   Found {templates['count']} templates")
                if templates['count'] > 0:
                    self.dashboard_template_id = templates['data'][0]['id']
            else:
                self.log_result("List Dashboard Templates", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_error("List Dashboard Templates", str(e))
        
        # Create custom dashboard template
        try:
            template_data = {
                "code": f"test_template_{int(time.time())}",
                "name": "Test Dashboard Template",
                "description": "Template for testing",
                "category": "custom",
                "template_structure": {
                    "menu": {
                        "items": [{
                            "id": "overview",
                            "label": "Overview",
                            "icon": "dashboard",
                            "path": "/overview"
                        }]
                    },
                    "dashboards": {
                        "overview": {
                            "title": "Test Overview",
                            "layout": {"cols": 12, "rows": 8},
                            "widgets": []
                        }
                    }
                }
            }
            response = requests.post(
                f"{BASE_URL}/api/v1/dashboard-templates/",
                json=template_data,
                headers=headers
            )
            if response.status_code == 200:
                template = response.json()
                self.dashboard_template_id = template["id"]
                self.log_result("Create Dashboard Template", True)
                print(f"   Created: {template['name']}")
            else:
                self.log_result("Create Dashboard Template", False, f"Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.log_error("Create Dashboard Template", str(e))
    
    def test_widget_definitions(self):
        """Test widget definition endpoints"""
        print("\n=== Testing Widget Definitions ===")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # List widget definitions
        try:
            response = requests.get(
                f"{BASE_URL}/api/v1/admin/widgets/",
                headers=headers
            )
            if response.status_code == 200:
                widgets = response.json()
                self.log_result("List Widget Definitions", True)
                print(f"   Found {widgets['count']} widget definitions")
                if widgets['count'] > 0:
                    self.widget_id = widgets['data'][0]['id']
            else:
                self.log_result("List Widget Definitions", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_error("List Widget Definitions", str(e))
    
    def test_study_dashboards(self):
        """Test study dashboard functionality"""
        print("\n=== Testing Study Dashboards ===")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # Note: Dashboards are created through study initialization with templates, not directly
        
        # List study dashboards
        if self.study_id:
            try:
                response = requests.get(
                    f"{BASE_URL}/api/v1/studies/{self.study_id}/dashboards",
                    headers=headers
                )
                if response.status_code == 200:
                    dashboards = response.json()
                    self.log_result("List Study Dashboards", True)
                    print(f"   Found {len(dashboards)} dashboards")
                else:
                    self.log_result("List Study Dashboards", False, f"Status: {response.status_code}")
            except Exception as e:
                self.log_error("List Study Dashboards", str(e))
    
    def test_api_health(self):
        """Test various API health and utility endpoints"""
        print("\n=== Testing API Health & Utilities ===")
        
        # Test health check
        try:
            response = requests.get(f"{BASE_URL}/api/v1/utils/health-check/")
            if response.status_code == 200:
                self.log_result("Health Check", True)
            else:
                self.log_result("Health Check", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_error("Health Check", str(e))
        
        # Test API documentation
        try:
            response = requests.get(f"{BASE_URL}/docs")
            if response.status_code == 200:
                self.log_result("API Documentation", True)
            else:
                self.log_result("API Documentation", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_error("API Documentation", str(e))
    
    def test_cleanup(self):
        """Clean up test data"""
        print("\n=== Cleaning Up Test Data ===")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # Delete study (this should cascade delete data sources)
        if self.study_id:
            try:
                # Use hard delete to remove all related data
                response = requests.delete(
                    f"{BASE_URL}/api/v1/studies/{self.study_id}?hard_delete=true",
                    headers=headers
                )
                if response.status_code in [200, 204]:
                    self.log_result("Delete Study", True)
                else:
                    self.log_result("Delete Study", False, f"Status: {response.status_code}, Response: {response.text}")
            except Exception as e:
                self.log_error("Delete Study", str(e))
        
        # Delete organization
        if self.org_id:
            try:
                response = requests.delete(
                    f"{BASE_URL}/api/v1/organizations/{self.org_id}",
                    headers=headers
                )
                if response.status_code in [200, 204]:
                    self.log_result("Delete Organization", True)
                else:
                    self.log_result("Delete Organization", False, f"Status: {response.status_code}")
            except Exception as e:
                self.log_error("Delete Organization", str(e))
    
    def generate_report(self):
        """Generate test report"""
        print("\n" + "="*50)
        print("COMPREHENSIVE TEST REPORT")
        print("="*50)
        print(f"Total Tests: {len(self.test_results['passed']) + len(self.test_results['failed'])}")
        print(f"✅ Passed: {len(self.test_results['passed'])}")
        print(f"❌ Failed: {len(self.test_results['failed'])}")
        print(f"🔥 Errors: {len(self.test_results['errors'])}")
        
        if self.test_results['failed']:
            print("\nFailed Tests:")
            for test in self.test_results['failed']:
                print(f"  - {test}")
        
        if self.test_results['errors']:
            print("\nErrors:")
            for error in self.test_results['errors']:
                print(f"  - {error}")
        
        success_rate = (len(self.test_results['passed']) / 
                       (len(self.test_results['passed']) + len(self.test_results['failed'])) * 100) \
                      if (self.test_results['passed'] or self.test_results['failed']) else 0
        
        print(f"\nSuccess Rate: {success_rate:.1f}%")
        
        # Save detailed report
        with open("test_report.json", "w") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "results": self.test_results,
                "summary": {
                    "total": len(self.test_results['passed']) + len(self.test_results['failed']),
                    "passed": len(self.test_results['passed']),
                    "failed": len(self.test_results['failed']),
                    "errors": len(self.test_results['errors']),
                    "success_rate": success_rate
                }
            }, f, indent=2)
        print("\nDetailed report saved to: test_report.json")
    
    def run_all_tests(self):
        """Run all tests in sequence"""
        print("🚀 Starting Comprehensive System Testing")
        print("="*50)
        
        self.test_api_health()
        self.test_authentication()
        self.test_organization_management()
        self.test_study_management()
        self.test_data_sources()
        self.test_dashboard_templates()
        self.test_widget_definitions()
        self.test_study_dashboards()
        self.test_cleanup()
        self.generate_report()


if __name__ == "__main__":
    tester = ClinicalDashboardTester()
    tester.run_all_tests()