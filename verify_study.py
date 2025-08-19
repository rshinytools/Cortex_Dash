#!/usr/bin/env python3
# ABOUTME: Check study initialization status with fresh token
# ABOUTME: Debug WebSocket and initialization issues

import json
import urllib.request
import urllib.parse
import sys
import time
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
TEST_EMAIL = "admin@sagarmatha.ai"
TEST_PASSWORD = "adadad123"
STUDY_ID = "521b4b98-87ec-4643-9103-eae78e2dad79"

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
            token = result["access_token"]
            
            # Decode token to check expiration
            import base64
            parts = token.split('.')
            if len(parts) >= 2:
                # Add padding if needed
                payload = parts[1]
                payload += '=' * (4 - len(payload) % 4)
                decoded = base64.b64decode(payload)
                token_data = json.loads(decoded)
                exp_time = datetime.fromtimestamp(token_data.get('exp', 0))
                print(f"[INFO] Token expires at: {exp_time}")
                print(f"[INFO] Current time: {datetime.now()}")
                if exp_time > datetime.now():
                    print(f"[OK] Token is valid for {(exp_time - datetime.now()).total_seconds() / 3600:.1f} hours")
                else:
                    print(f"[WARNING] Token is expired!")
            
            return token
    except Exception as e:
        print(f"[ERROR] Login failed: {e}")
        return None

def check_study(token, study_id):
    """Check study details and status"""
    print(f"\nChecking study {study_id}...")
    
    req = urllib.request.Request(
        f"{BASE_URL}/studies/{study_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            study = json.loads(response.read().decode())
            print(f"[SUCCESS] Study found: {study.get('name')}")
            print(f"  - Status: {study.get('status')}")
            print(f"  - Init Status: {study.get('initialization_status')}")
            print(f"  - Init Progress: {study.get('initialization_progress')}%")
            return study
    except urllib.error.HTTPError as e:
        print(f"[ERROR] HTTP {e.code}: {e.reason}")
        return None

def check_initialization_status(token, study_id):
    """Check detailed initialization status"""
    print(f"\nChecking initialization status...")
    
    req = urllib.request.Request(
        f"{BASE_URL}/studies/{study_id}/initialization/status",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode())
            print("\n[INFO] Initialization Details:")
            print(f"  Status: {result.get('initialization_status')}")
            print(f"  Progress: {result.get('initialization_progress')}%")
            
            if result.get('initialization_steps'):
                steps = result['initialization_steps']
                if 'error' in steps:
                    print(f"  Error: {steps['error']}")
                if 'failed_at' in steps:
                    print(f"  Failed at: {steps['failed_at']}")
            
            return result
    except Exception as e:
        print(f"[ERROR] Failed to get initialization status: {e}")
        return None

def retry_initialization(token, study_id):
    """Retry initialization if failed"""
    print(f"\nRetrying initialization...")
    
    req = urllib.request.Request(
        f"{BASE_URL}/studies/{study_id}/initialization/retry",
        method="POST",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode())
            print("[SUCCESS] Initialization retry triggered:")
            print(f"  Task ID: {result.get('task_id')}")
            return result
    except urllib.error.HTTPError as e:
        error_body = e.read().decode() if e.code == 400 else ""
        print(f"[ERROR] Cannot retry: {error_body if error_body else e.reason}")
        return None

def main():
    print("="*60)
    print("Study Data and Initialization Check")
    print("="*60)
    
    # Login with fresh token
    token = login()
    if not token:
        print("[ERROR] Failed to login")
        sys.exit(1)
    
    print(f"\n[OK] Fresh token obtained")
    
    # Check study
    study = check_study(token, STUDY_ID)
    if not study:
        print(f"\n[ERROR] Study {STUDY_ID} not found")
        sys.exit(1)
    
    # Check initialization status
    init_status = check_initialization_status(token, STUDY_ID)
    
    # If failed, try to retry
    if init_status and init_status.get('initialization_status') == 'failed':
        print("\n[INFO] Initialization failed, attempting retry...")
        retry_result = retry_initialization(token, STUDY_ID)
        if retry_result:
            print(f"\n[SUCCESS] Use this fresh token in the frontend:")
            print(f"Token: {token}")
            print(f"\nMonitor at: http://localhost:3000/initialization/{STUDY_ID}")
    
    print("\n" + "="*60)
    print("Test completed")
    print("="*60)

if __name__ == "__main__":
    main()