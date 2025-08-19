#!/usr/bin/env python3
# ABOUTME: Test complete mapping flow with widget requirements
# ABOUTME: Verifies both datasets and widget requirements are available

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

def test_complete_mapping(token, study_id):
    """Test complete mapping data"""
    print(f"\nTesting complete mapping data for study {study_id}...")
    
    req = urllib.request.Request(
        f"{BASE_URL}/studies/wizard/{study_id}/mapping-data",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode())
            
            print("\n[SUCCESS] Complete Mapping Data Retrieved!")
            print("="*60)
            
            # Check datasets
            datasets = result.get('dataset_schemas', {})
            print(f"\n1. DATASETS AVAILABLE: {len(datasets)}")
            for dataset_name, schema in datasets.items():
                columns = schema.get('columns', {})
                print(f"   - {dataset_name}: {schema.get('row_count', 0)} rows, {len(columns)} columns")
            
            # Check widget requirements
            requirements = result.get('template_requirements', [])
            print(f"\n2. WIDGET REQUIREMENTS: {len(requirements)} widgets need data")
            for req in requirements:
                widget_title = req.get('widget_title')
                widget_type = req.get('widget_type')
                required_fields = req.get('required_fields', [])
                print(f"   - {widget_title} ({widget_type})")
                print(f"     Required fields: {', '.join(required_fields)}")
            
            # Check mapping suggestions
            suggestions = result.get('mapping_suggestions', {})
            print(f"\n3. AUTO-MAPPING SUGGESTIONS: {len(suggestions)} widgets have suggestions")
            
            # Summary
            print("\n" + "="*60)
            print("SUMMARY:")
            print(f"  [OK] {len(datasets)} datasets with {result.get('total_columns', 0)} total columns")
            print(f"  [OK] {len(requirements)} widgets requiring data mapping")
            print(f"  [OK] {len(suggestions)} auto-mapping suggestions generated")
            
            # Validation
            if len(datasets) > 0 and len(requirements) > 0:
                print("\n[SUCCESS] Both datasets and widget requirements are available!")
                print("The field mapping should now work correctly in the UI.")
                return True
            else:
                if len(datasets) == 0:
                    print("\n[ERROR] No datasets found")
                if len(requirements) == 0:
                    print("\n[ERROR] No widget requirements found")
                return False
                
    except Exception as e:
        print(f"[ERROR] Failed to get mapping data: {e}")
        return False

def main():
    print("="*60)
    print("Complete Mapping Flow Test")
    print("="*60)
    
    # Login
    token = login()
    if not token:
        print("[ERROR] Failed to login")
        sys.exit(1)
    
    print("[OK] Logged in successfully")
    
    # Test complete mapping
    success = test_complete_mapping(token, STUDY_ID)
    
    if success:
        print("\n" + "="*60)
        print("[SUCCESS] Complete mapping flow is working!")
        print("="*60)
        print(f"\nYou can now complete the field mapping at:")
        print(f"http://localhost:3000/studies/{STUDY_ID}/initialization")
    else:
        print("\n" + "="*60)
        print("[FAILED] Mapping flow still has issues")
        print("="*60)
        sys.exit(1)

if __name__ == "__main__":
    main()