#!/usr/bin/env python3
# ABOUTME: Check study configuration and uploaded files
# ABOUTME: Debug what data is stored in the study

import json
import urllib.request
import urllib.parse
import sys

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
TEST_EMAIL = "admin@sagarmatha.ai"
TEST_PASSWORD = "adadad123"
STUDY_ID = "7ff94cca-4c95-450a-bdd9-5cc30584013b"

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

def check_study(token, study_id):
    """Check study details"""
    print(f"\nChecking study {study_id}...")
    
    req = urllib.request.Request(
        f"{BASE_URL}/studies/{study_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            study = json.loads(response.read().decode())
            
            print("\n[INFO] Study Details:")
            print(f"  Name: {study.get('name')}")
            print(f"  Status: {study.get('status')}")
            print(f"  Initialization Status: {study.get('initialization_status')}")
            print(f"  Template ID: {study.get('dashboard_template_id')}")
            
            config = study.get('config', {})
            print(f"\n[INFO] Config Keys: {list(config.keys())}")
            
            if 'uploaded_files' in config:
                files = config['uploaded_files']
                print(f"\n[INFO] Uploaded Files: {len(files)} files")
                for f in files[:3]:  # Show first 3
                    print(f"  - {f}")
            else:
                print("\n[WARNING] No uploaded_files in config")
                
            if 'pending_uploads' in config:
                pending = config['pending_uploads']
                print(f"\n[INFO] Pending Uploads: {len(pending)} files")
                
            # Check the data directory
            print(f"\n[INFO] Folder Path: {study.get('folder_path')}")
            
            return study
    except Exception as e:
        print(f"[ERROR] Failed to get study: {e}")
        return None

def check_uploads(token, study_id):
    """Check uploaded files via API"""
    print(f"\nChecking uploads for study {study_id}...")
    
    req = urllib.request.Request(
        f"{BASE_URL}/studies/{study_id}/data-uploads",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            uploads = json.loads(response.read().decode())
            print(f"\n[INFO] Found {len(uploads)} uploads")
            for upload in uploads[:5]:  # Show first 5
                print(f"  - {upload.get('filename')} ({upload.get('status')})")
            return uploads
    except Exception as e:
        print(f"[ERROR] Failed to get uploads: {e}")
        return None

def main():
    print("="*60)
    print("Study Configuration Check")
    print("="*60)
    
    # Login
    token = login()
    if not token:
        print("[ERROR] Failed to login")
        sys.exit(1)
    
    print("[OK] Logged in successfully")
    
    # Check study
    study = check_study(token, STUDY_ID)
    
    # Check uploads
    uploads = check_uploads(token, STUDY_ID)
    
    print("\n" + "="*60)
    print("Check completed")
    print("="*60)

if __name__ == "__main__":
    main()