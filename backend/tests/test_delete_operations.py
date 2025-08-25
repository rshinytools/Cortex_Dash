#!/usr/bin/env python3
# ABOUTME: Test script to verify delete operations work correctly
# ABOUTME: Tests both soft and hard delete for studies and organizations

import asyncio
import requests
from datetime import datetime
import json

# API base URL
BASE_URL = "http://localhost:8001/api/v1"

# Test credentials
ADMIN_EMAIL = "admin@sagarmatha.ai"
ADMIN_PASSWORD = "changethis123"

def get_auth_headers(token):
    """Get authorization headers"""
    return {"Authorization": f"Bearer {token}"}

def login():
    """Login and get access token"""
    response = requests.post(
        f"{BASE_URL}/login/access-token",
        data={
            "username": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        }
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"Login failed: {response.status_code} - {response.text}")
        return None

def test_study_delete(token):
    """Test study delete operations"""
    headers = get_auth_headers(token)
    
    print("\n=== Testing Study Delete Operations ===")
    
    # First, create a test organization
    org_data = {
        "name": f"Test Org for Delete {datetime.now().isoformat()}",
        "slug": f"test-org-delete-{datetime.now().timestamp()}"
    }
    org_response = requests.post(f"{BASE_URL}/organizations", json=org_data, headers=headers)
    if org_response.status_code != 200:
        print(f"Failed to create organization: {org_response.text}")
        return
    
    org_id = org_response.json()["id"]
    print(f"Created test organization: {org_id}")
    
    # Create a test study
    study_data = {
        "name": f"Test Study for Delete {datetime.now().isoformat()}",
        "code": f"TEST-DEL-{int(datetime.now().timestamp())}",
        "protocol_number": f"PROTO-DEL-{int(datetime.now().timestamp())}",
        "org_id": org_id
    }
    
    study_response = requests.post(f"{BASE_URL}/studies", json=study_data, headers=headers)
    if study_response.status_code != 200:
        print(f"Failed to create study: {study_response.text}")
        return
    
    study_id = study_response.json()["id"]
    print(f"Created test study: {study_id}")
    
    # Test 1: Soft delete (archive)
    print("\n1. Testing soft delete (archive)...")
    delete_response = requests.delete(f"{BASE_URL}/studies/{study_id}", headers=headers)
    print(f"Soft delete response: {delete_response.status_code} - {delete_response.json()}")
    
    # Verify study is archived
    get_response = requests.get(f"{BASE_URL}/studies/{study_id}", headers=headers)
    if get_response.status_code == 200:
        study = get_response.json()
        print(f"Study status after soft delete: {study.get('status')}, is_active: {study.get('is_active')}")
    
    # Test 2: Hard delete
    print("\n2. Testing hard delete...")
    delete_response = requests.delete(
        f"{BASE_URL}/studies/{study_id}",
        params={"hard_delete": True},
        headers=headers
    )
    print(f"Hard delete response: {delete_response.status_code} - {delete_response.json()}")
    
    # Verify study is gone
    get_response = requests.get(f"{BASE_URL}/studies/{study_id}", headers=headers)
    print(f"Get study after hard delete: {get_response.status_code}")
    
    # Clean up - delete the test organization
    requests.delete(f"{BASE_URL}/organizations/{org_id}", params={"hard_delete": True}, headers=headers)

def test_organization_delete(token):
    """Test organization delete operations"""
    headers = get_auth_headers(token)
    
    print("\n=== Testing Organization Delete Operations ===")
    
    # Test 1: Create org with no dependencies
    org_data = {
        "name": f"Test Org No Deps {datetime.now().isoformat()}",
        "slug": f"test-org-no-deps-{datetime.now().timestamp()}"
    }
    org_response = requests.post(f"{BASE_URL}/organizations", json=org_data, headers=headers)
    if org_response.status_code != 200:
        print(f"Failed to create organization: {org_response.text}")
        return
    
    org_id = org_response.json()["id"]
    print(f"Created test organization: {org_id}")
    
    # Soft delete
    print("\n1. Testing soft delete (deactivate)...")
    delete_response = requests.delete(f"{BASE_URL}/organizations/{org_id}", headers=headers)
    print(f"Soft delete response: {delete_response.status_code} - {delete_response.json()}")
    
    # Hard delete
    print("\n2. Testing hard delete...")
    delete_response = requests.delete(
        f"{BASE_URL}/organizations/{org_id}",
        params={"hard_delete": True},
        headers=headers
    )
    print(f"Hard delete response: {delete_response.status_code} - {delete_response.json()}")
    
    # Test 2: Create org with studies
    print("\n3. Testing delete with dependencies...")
    org_data = {
        "name": f"Test Org With Studies {datetime.now().isoformat()}",
        "slug": f"test-org-with-studies-{datetime.now().timestamp()}"
    }
    org_response = requests.post(f"{BASE_URL}/organizations", json=org_data, headers=headers)
    org_id = org_response.json()["id"]
    
    # Create a study in this org
    study_data = {
        "name": f"Test Study in Org {datetime.now().isoformat()}",
        "code": f"TEST-ORG-{int(datetime.now().timestamp())}",
        "protocol_number": f"PROTO-ORG-{int(datetime.now().timestamp())}",
        "org_id": org_id
    }
    study_response = requests.post(f"{BASE_URL}/studies", json=study_data, headers=headers)
    study_id = study_response.json()["id"]
    print(f"Created study {study_id} in org {org_id}")
    
    # Try to delete without force
    print("\n4. Trying to delete org with studies (should fail)...")
    delete_response = requests.delete(
        f"{BASE_URL}/organizations/{org_id}",
        params={"hard_delete": True},
        headers=headers
    )
    print(f"Delete without force: {delete_response.status_code} - {delete_response.json()}")
    
    # Delete with force
    print("\n5. Deleting org with force=true (cascade delete)...")
    delete_response = requests.delete(
        f"{BASE_URL}/organizations/{org_id}",
        params={"hard_delete": True, "force": True},
        headers=headers
    )
    print(f"Delete with force: {delete_response.status_code} - {delete_response.json()}")
    
    # Verify study is also deleted
    get_response = requests.get(f"{BASE_URL}/studies/{study_id}", headers=headers)
    print(f"Get study after org cascade delete: {get_response.status_code}")

def main():
    """Run all tests"""
    print("Starting delete operation tests...")
    
    # Login
    token = login()
    if not token:
        print("Failed to login, exiting")
        return
    
    print(f"Successfully logged in")
    
    # Run tests
    test_study_delete(token)
    test_organization_delete(token)
    
    print("\n=== Tests completed ===")

if __name__ == "__main__":
    main()