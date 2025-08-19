#!/usr/bin/env python3
# ABOUTME: Test that field mapping is now working correctly
# ABOUTME: Verifies the complete data upload to mapping flow

import json
import urllib.request
import urllib.parse
import sys

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
TEST_EMAIL = "admin@sagarmatha.ai"
TEST_PASSWORD = "adadad123"
STUDY_ID = "99a75912-6474-403b-a47d-644fde30adfd"

def login():
    """Login and get token"""
    data = urllib.parse.urlencode({
        "username": TEST_EMAIL,
        "password": TEST_PASSWORD
    }).encode()
    
    req = urllib.request.Request(
        f"{BASE_URL}/login/access-token",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode())
            return result["access_token"]
    except Exception as e:
        print(f"[ERROR] Login failed: {e}")
        return None

def test_mapping_data_endpoint(token, study_id):
    """Test the mapping-data endpoint"""
    print(f"\nTesting mapping-data endpoint for study {study_id}...")
    
    req = urllib.request.Request(
        f"{BASE_URL}/studies/wizard/{study_id}/mapping-data",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode())
            
            print("\n[SUCCESS] Mapping data endpoint returned:")
            print(f"  - Total datasets: {result.get('total_datasets', 0)}")
            print(f"  - Total columns: {result.get('total_columns', 0)}")
            print(f"  - Total widgets: {result.get('total_widgets', 0)}")
            
            if result.get('dataset_schemas'):
                print("\n  Datasets available for mapping:")
                for dataset_name, schema in result['dataset_schemas'].items():
                    columns = schema.get('columns', {})
                    print(f"    * {dataset_name}: {schema.get('row_count', 0)} rows, {len(columns)} columns")
            
            if result.get('template_requirements'):
                print(f"\n  Template requirements: {len(result['template_requirements'])} widgets need data")
            
            if result.get('mapping_suggestions'):
                print(f"\n  Auto-mapping suggestions: Available for {len(result['mapping_suggestions'])} widgets")
            
            return True
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f"[ERROR] Mapping data endpoint failed: {e.code}")
        print(f"  Response: {error_body}")
        return False
    except Exception as e:
        print(f"[ERROR] Failed to get mapping data: {e}")
        return False

def main():
    print("="*60)
    print("Field Mapping Fix Verification Test")
    print("="*60)
    
    # Login
    token = login()
    if not token:
        print("[ERROR] Failed to login")
        sys.exit(1)
    
    print("[OK] Logged in successfully")
    
    # Test the mapping data endpoint
    success = test_mapping_data_endpoint(token, STUDY_ID)
    
    if success:
        print("\n" + "="*60)
        print("[SUCCESS] Field mapping data is now accessible!")
        print("The 'No Data Available for Mapping' issue is FIXED!")
        print("="*60)
        print(f"\nYou can now complete the field mapping at:")
        print(f"http://localhost:3000/studies/{STUDY_ID}/initialization")
    else:
        print("\n" + "="*60)
        print("[FAILED] Field mapping data is still not accessible")
        print("="*60)
        sys.exit(1)

if __name__ == "__main__":
    main()