# ABOUTME: Simple API testing script for Clinical Dashboard Platform
# ABOUTME: Provides examples of how to test various API endpoints

import requests
import json
from typing import Dict, Any
import time

class APITester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api/v1"
        self.token = None
        self.headers = {}
        
    def login(self, username: str, password: str) -> bool:
        """Login and store the access token"""
        try:
            response = requests.post(
                f"{self.api_url}/login/access-token",
                data={"username": username, "password": password}
            )
            if response.status_code == 200:
                self.token = response.json()["access_token"]
                self.headers = {"Authorization": f"Bearer {self.token}"}
                print(f"✅ Login successful for {username}")
                return True
            else:
                print(f"❌ Login failed: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Login error: {e}")
            return False
    
    def test_endpoint(self, method: str, endpoint: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Test an API endpoint"""
        url = f"{self.api_url}{endpoint}"
        
        try:
            if method == "GET":
                response = requests.get(url, headers=self.headers)
            elif method == "POST":
                response = requests.post(url, headers=self.headers, json=data)
            elif method == "PATCH":
                response = requests.patch(url, headers=self.headers, json=data)
            elif method == "DELETE":
                response = requests.delete(url, headers=self.headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            return {
                "status_code": response.status_code,
                "success": response.status_code < 400,
                "data": response.json() if response.text else None
            }
        except Exception as e:
            return {
                "status_code": 0,
                "success": False,
                "error": str(e)
            }
    
    def print_result(self, test_name: str, result: Dict[str, Any]):
        """Print test result in a nice format"""
        if result["success"]:
            print(f"✅ {test_name}: SUCCESS (Status: {result['status_code']})")
            if result.get("data"):
                print(f"   Response: {json.dumps(result['data'], indent=2)[:200]}...")
        else:
            print(f"❌ {test_name}: FAILED (Status: {result['status_code']})")
            if result.get("error"):
                print(f"   Error: {result['error']}")
            elif result.get("data"):
                print(f"   Response: {json.dumps(result['data'], indent=2)[:200]}...")


def main():
    # Initialize tester
    tester = APITester()
    
    print("🧪 Clinical Dashboard API Testing\n")
    
    # Test 1: Health Check (no auth required)
    print("1️⃣ Testing Health Check...")
    result = tester.test_endpoint("GET", "/../health")
    tester.print_result("Health Check", result)
    print()
    
    # Test 2: Login
    print("2️⃣ Testing Authentication...")
    if not tester.login("admin@sagarmatha.ai", "adadad123"):
        print("Cannot continue without authentication")
        return
    print()
    
    # Test 3: Get Current User
    print("3️⃣ Testing Get Current User...")
    result = tester.test_endpoint("GET", "/users/me")
    tester.print_result("Get Current User", result)
    print()
    
    # Test 4: List Organizations
    print("4️⃣ Testing List Organizations...")
    result = tester.test_endpoint("GET", "/organizations")
    tester.print_result("List Organizations", result)
    print()
    
    # Test 5: Create Organization (System Admin only)
    print("5️⃣ Testing Create Organization...")
    org_data = {
        "name": "Test Pharmaceutical Inc",
        "slug": "test-pharma",
        "license_type": "trial",
        "max_users": 10,
        "max_studies": 5,
        "active": True
    }
    result = tester.test_endpoint("POST", "/organizations", org_data)
    tester.print_result("Create Organization", result)
    
    if result["success"]:
        org_id = result["data"]["id"]
        print(f"   Created Organization ID: {org_id}")
        
        # Test 6: Create User
        print("\n6️⃣ Testing Create User...")
        user_data = {
            "email": "test.user@testpharma.com",
            "password": "SecurePass123!",
            "full_name": "Test User",
            "role": "study_manager",
            "org_id": org_id,
            "is_active": True
        }
        result = tester.test_endpoint("POST", "/v1/users", user_data)
        tester.print_result("Create User", result)
        
        # Test 7: Create Study
        print("\n7️⃣ Testing Create Study...")
        study_data = {
            "org_id": org_id,
            "name": "Test Clinical Trial",
            "protocol_number": "TEST-2024-001",
            "description": "A test clinical trial for API testing",
            "status": "setup"
        }
        result = tester.test_endpoint("POST", "/studies", study_data)
        tester.print_result("Create Study", result)
        
        if result["success"]:
            study_id = result["data"]["id"]
            print(f"   Created Study ID: {study_id}")
            
            # Test 8: Get Study Details
            print("\n8️⃣ Testing Get Study Details...")
            result = tester.test_endpoint("GET", f"/studies/{study_id}")
            tester.print_result("Get Study Details", result)
    
    # Test 9: List Studies
    print("\n9️⃣ Testing List Studies...")
    result = tester.test_endpoint("GET", "/studies")
    tester.print_result("List Studies", result)
    
    # Test 10: Test Permission (Try as non-admin)
    print("\n🔟 Testing RBAC - Creating user as study_manager (should fail)...")
    if tester.login("test.user@testpharma.com", "SecurePass123!"):
        result = tester.test_endpoint("POST", "/v1/users", {
            "email": "unauthorized@test.com",
            "password": "test",
            "role": "viewer",
            "org_id": org_id
        })
        tester.print_result("RBAC Test - Unauthorized User Creation", result)
    
    print("\n✅ API Testing Complete!")
    print("\n📝 Summary:")
    print("- Server URL: http://localhost:8000")
    print("- API Docs: http://localhost:8000/docs")
    print("- All basic endpoints tested")
    print("\n💡 Next Steps:")
    print("1. Test data pipeline endpoints")
    print("2. Test async task execution")
    print("3. Test file uploads")
    print("4. Test report generation")


if __name__ == "__main__":
    main()