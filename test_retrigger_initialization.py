#!/usr/bin/env python3
# ABOUTME: Retry/retrigger study initialization
# ABOUTME: Forces a new initialization attempt

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

def check_status(token, study_id):
    """Check initialization status"""
    req = urllib.request.Request(
        f"{BASE_URL}/studies/{study_id}/initialization/status",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode())
            print("\n[INFO] Current Status:")
            print(f"  Status: {result.get('initialization_status')}")
            print(f"  Progress: {result.get('initialization_progress')}%")
            if result.get('initialization_steps'):
                print(f"  Task ID: {result['initialization_steps'].get('task_id')}")
            return result
    except Exception as e:
        print(f"[ERROR] Failed to get status: {e}")
        return None

def main():
    print("="*60)
    print("Study Initialization Retry")
    print("="*60)
    
    # Login
    token = login()
    if not token:
        print("[ERROR] Failed to login")
        sys.exit(1)
    
    print("[OK] Logged in successfully")
    
    # Check current status
    status = check_status(token, STUDY_ID)
    
    # Retry initialization
    result = retry_initialization(token, STUDY_ID)
    
    if result:
        print("\n[SUCCESS] Initialization retry triggered!")
        print("\nWait a moment and check the progress at:")
        print(f"http://localhost:3000/initialization/{STUDY_ID}")
    
    print("\n" + "="*60)
    print("Test completed")
    print("="*60)

if __name__ == "__main__":
    main()