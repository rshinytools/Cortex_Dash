#!/usr/bin/env python3
# ABOUTME: Check specific study initialization status
# ABOUTME: Debug why initialization failed

import json
import urllib.request
import urllib.parse
import sys

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
TEST_EMAIL = "admin@sagarmatha.ai"
TEST_PASSWORD = "adadad123"
STUDY_ID = "88440c07-3bf1-48b8-806c-1881257dbb45"

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

def check_initialization_status(token, study_id):
    """Check initialization status"""
    print(f"\nChecking initialization status for study {study_id}...")
    
    req = urllib.request.Request(
        f"{BASE_URL}/studies/{study_id}/initialization/status",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode())
            print("\n[SUCCESS] Initialization Status:")
            print(json.dumps(result, indent=2))
            return result
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print("[INFO] Study not found or not initialized")
        else:
            print(f"[ERROR] HTTP {e.code}: {e.reason}")
        return None
    except Exception as e:
        print(f"[ERROR] Failed to get status: {e}")
        return None

def retry_initialization(token, study_id):
    """Retry study initialization"""
    print(f"\nRetrying initialization for study {study_id}...")
    
    req = urllib.request.Request(
        f"{BASE_URL}/studies/{study_id}/initialization/retry",
        method="POST",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode())
            print("\n[SUCCESS] Initialization retry triggered:")
            print(json.dumps(result, indent=2))
            return result
    except urllib.error.HTTPError as e:
        error_body = e.read().decode() if e.code == 400 else ""
        print(f"[ERROR] HTTP {e.code}: {e.reason}")
        if error_body:
            print(f"Details: {error_body}")
        return None
    except Exception as e:
        print(f"[ERROR] Failed to retry initialization: {e}")
        return None

def main():
    print("="*60)
    print("Study Initialization Check")
    print("="*60)
    
    # Login
    token = login()
    if not token:
        print("[ERROR] Failed to login")
        sys.exit(1)
    
    print("[OK] Logged in successfully")
    
    # Check initialization status
    status = check_initialization_status(token, STUDY_ID)
    
    if status and status.get("initialization_status") == "failed":
        print("\n[INFO] Initialization has failed. Attempting retry...")
        result = retry_initialization(token, STUDY_ID)
        
        if result:
            print("\n[SUCCESS] Initialization retry triggered!")
            print(f"\nCorrect URL to monitor progress:")
            print(f"http://localhost:3000/initialization/{STUDY_ID}")
            print(f"\n(NOT http://localhost:3000/studies/{STUDY_ID}/initialization)")
    elif status:
        print(f"\n[INFO] Study initialization status: {status.get('initialization_status')}")
        print(f"Progress: {status.get('initialization_progress')}%")
        if status.get('initialization_steps', {}).get('error'):
            print(f"Error: {status['initialization_steps']['error']}")
    
    print("\n" + "="*60)
    print("Test completed")
    print("="*60)

if __name__ == "__main__":
    main()