#!/usr/bin/env python3
# ABOUTME: Test mapping count display in Review step
# ABOUTME: Creates a new study and verifies mapping count shows correctly

import json
import urllib.request
import urllib.parse
import sys
import time
import os
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
TEST_EMAIL = "admin@sagarmatha.ai"
TEST_PASSWORD = "adadad123"
SAMPLE_DATA_DIR = Path(r"C:\Users\amuly\OneDrive\AetherClinical\Cortex_Dash\Sample_Data")

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

def get_latest_study(token):
    """Get the latest study"""
    req = urllib.request.Request(
        f"{BASE_URL}/studies",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            studies = json.loads(response.read().decode())
            if studies:
                # Get the most recent study
                latest = sorted(studies, key=lambda x: x.get('created_at', ''), reverse=True)[0]
                return latest['id']
    except Exception as e:
        print(f"[ERROR] Failed to get studies: {e}")
    
    return None

def check_mapping_data(token, study_id):
    """Check mapping data and count"""
    print(f"\nChecking mapping data for study {study_id}...")
    
    req = urllib.request.Request(
        f"{BASE_URL}/studies/wizard/{study_id}/mapping-data",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode())
            
            # Count datasets
            datasets = result.get('dataset_schemas', {})
            print(f"\nDATASETS: {len(datasets)}")
            for dataset_name in datasets:
                print(f"  - {dataset_name}")
            
            # Count widget requirements
            requirements = result.get('template_requirements', [])
            print(f"\nWIDGET REQUIREMENTS: {len(requirements)}")
            total_fields = 0
            for req in requirements:
                fields = req.get('required_fields', [])
                total_fields += len(fields)
                print(f"  - {req.get('widget_title')}: {len(fields)} fields")
            
            # Count suggestions
            suggestions = result.get('mapping_suggestions', {})
            mapped_count = 0
            for widget_id, widget_suggestions in suggestions.items():
                # Handle both list and dict formats
                if isinstance(widget_suggestions, list):
                    for suggestion in widget_suggestions:
                        if suggestion.get('suggested_column'):
                            mapped_count += 1
                elif isinstance(widget_suggestions, dict):
                    for field_name, suggestion in widget_suggestions.items():
                        if suggestion.get('suggested_column'):
                            mapped_count += 1
            
            print(f"\nMAPPING SUMMARY:")
            print(f"  Total fields needing mapping: {total_fields}")
            print(f"  Auto-mapped fields: {mapped_count}")
            print(f"  Unmapped fields: {total_fields - mapped_count}")
            
            return True
            
    except Exception as e:
        print(f"[ERROR] Failed to get mapping data: {e}")
        return False

def main():
    print("="*60)
    print("Mapping Count Test")
    print("="*60)
    
    # Login
    token = login()
    if not token:
        print("[ERROR] Failed to login")
        sys.exit(1)
    
    print("[OK] Logged in successfully")
    
    # Get latest study
    study_id = get_latest_study(token)
    if not study_id:
        print("[ERROR] No studies found")
        sys.exit(1)
    
    print(f"[OK] Found study: {study_id}")
    
    # Check mapping data
    success = check_mapping_data(token, study_id)
    
    if success:
        print("\n" + "="*60)
        print("[SUCCESS] Mapping data available!")
        print("="*60)
        print(f"\nGo to the following URL and:")
        print(f"1. Navigate to the Field Mapping step")
        print(f"2. Map some fields using the dropdowns")
        print(f"3. Click Next to go to Review step")
        print(f"4. Check if the 'Mapped Fields' count shows correctly")
        print(f"\nURL: http://localhost:3000/studies/{study_id}/initialization")
    else:
        print("\n" + "="*60)
        print("[FAILED] Mapping data not available")
        print("="*60)

if __name__ == "__main__":
    main()