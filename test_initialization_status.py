#!/usr/bin/env python3
# ABOUTME: Test study initialization status and trigger if needed
# ABOUTME: Checks why initialization is not progressing

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

def trigger_initialization(token, study_id):
    """Trigger study initialization"""
    print(f"\nTriggering initialization for study {study_id}...")
    
    # First get the study to find template ID
    req = urllib.request.Request(
        f"{BASE_URL}/studies/{study_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            study = json.loads(response.read().decode())
            template_id = study.get("dashboard_template_id")
            
            if not template_id:
                print("[ERROR] Study has no template selected")
                return None
                
            print(f"[INFO] Using template: {template_id}")
            
            # Now trigger initialization
            data = json.dumps({
                "template_id": template_id,
                "skip_data_upload": False
            }).encode()
            
            req = urllib.request.Request(
                f"{BASE_URL}/studies/{study_id}/initialize-with-progress",
                data=data,
                method="POST",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
            )
            
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode())
                print("\n[SUCCESS] Initialization triggered:")
                print(json.dumps(result, indent=2))
                return result
                
    except urllib.error.HTTPError as e:
        if e.code == 400:
            error_body = e.read().decode()
            print(f"[ERROR] Bad request: {error_body}")
        else:
            print(f"[ERROR] HTTP {e.code}: {e.reason}")
        return None
    except Exception as e:
        print(f"[ERROR] Failed to trigger initialization: {e}")
        return None

def main():
    print("="*60)
    print("Study Initialization Status Test")
    print("="*60)
    
    # Login
    token = login()
    if not token:
        print("[ERROR] Failed to login")
        sys.exit(1)
    
    print("[OK] Logged in successfully")
    
    # Check initialization status
    status = check_initialization_status(token, STUDY_ID)
    
    if status and status.get("initialization_status") == "not_started":
        print("\n[INFO] Study not initialized, triggering initialization...")
        result = trigger_initialization(token, STUDY_ID)
        
        if result:
            print("\n[SUCCESS] Initialization triggered successfully!")
            print(f"Task ID: {result.get('task_id')}")
            print(f"Status: {result.get('status')}")
    elif status:
        print(f"\n[INFO] Study initialization status: {status.get('initialization_status')}")
        print(f"Progress: {status.get('initialization_progress')}%")
    
    print("\n" + "="*60)
    print("Test completed")
    print("="*60)

if __name__ == "__main__":
    main()