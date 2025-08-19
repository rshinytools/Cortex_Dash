#!/usr/bin/env python3
# ABOUTME: Check StudyDataConfiguration for a specific study
# ABOUTME: Debug script to verify data is properly saved

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

def check_study_data_config(token, study_id):
    """Check StudyDataConfiguration"""
    print(f"\nChecking StudyDataConfiguration for study {study_id}...")
    
    req = urllib.request.Request(
        f"{BASE_URL}/debug/study/{study_id}/data-config",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode())
            
            print(f"\nStudy: {result.get('study_name', 'Unknown')}")
            print(f"Has DataConfig: {result.get('has_data_config', False)}")
            
            if result.get('has_data_config'):
                print(f"Datasets Count: {result.get('datasets_count', 0)}")
                
                if result.get('dataset_schemas'):
                    print("\nDatasets found:")
                    for dataset_name in result['dataset_schemas'].keys():
                        schema = result['dataset_schemas'][dataset_name]
                        print(f"  - {dataset_name}: {schema.get('row_count', 0)} rows, {schema.get('column_count', 0)} columns")
            else:
                print("\n[WARNING] No StudyDataConfiguration found!")
                print("\nInitialization steps:")
                if result.get('initialization_steps'):
                    steps = result['initialization_steps']
                    if 'pending_uploads' in steps:
                        print(f"  - Pending uploads: {len(steps['pending_uploads'])} files")
                    if 'file_processing' in steps:
                        processing = steps['file_processing']
                        if 'datasets' in processing:
                            print(f"  - Processed datasets: {len(processing['datasets'])}")
                            for ds_name in processing['datasets'].keys():
                                print(f"    * {ds_name}")
            
            return result
    except Exception as e:
        print(f"[ERROR] Failed to check data config: {e}")
        return None

def main():
    print("="*60)
    print("StudyDataConfiguration Debug Check")
    print("="*60)
    
    # Login
    token = login()
    if not token:
        print("[ERROR] Failed to login")
        sys.exit(1)
    
    print("[OK] Logged in successfully")
    
    # Check the study
    result = check_study_data_config(token, STUDY_ID)
    
    if result and not result.get('has_data_config'):
        print("\n" + "="*60)
        print("[ISSUE FOUND] StudyDataConfiguration is missing!")
        print("This is why 'No Data Available for Mapping' appears")
        print("="*60)

if __name__ == "__main__":
    main()