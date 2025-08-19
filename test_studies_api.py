#!/usr/bin/env python3
# ABOUTME: Test studies API endpoint
# ABOUTME: Check if backend is returning studies

import json
import urllib.request
import urllib.parse
import sys

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
TEST_EMAIL = "admin@sagarmatha.ai"
TEST_PASSWORD = "adadad123"

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

def get_studies(token):
    """Get all studies"""
    print("\nFetching studies from API...")
    
    req = urllib.request.Request(
        f"{BASE_URL}/studies",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            studies = json.loads(response.read().decode())
            print(f"\n[SUCCESS] Found {len(studies)} studies")
            for study in studies:
                print(f"  - {study.get('name')} (ID: {study.get('id')}, Status: {study.get('status')})")
            return studies
    except urllib.error.HTTPError as e:
        error_body = e.read().decode() if e.code in [400, 500] else ""
        print(f"[ERROR] HTTP {e.code}: {e.reason}")
        if error_body:
            print(f"Details: {error_body}")
        return None
    except Exception as e:
        print(f"[ERROR] Failed to get studies: {e}")
        return None

def main():
    print("="*60)
    print("Studies API Test")
    print("="*60)
    
    # Login
    token = login()
    if not token:
        print("[ERROR] Failed to login")
        sys.exit(1)
    
    print("[OK] Logged in successfully")
    
    # Get studies
    studies = get_studies(token)
    
    if studies is not None:
        print(f"\n[INFO] Backend API is working and returning {len(studies)} studies")
    else:
        print("\n[ERROR] Backend API failed to return studies")
    
    print("\n" + "="*60)
    print("Test completed")
    print("="*60)

if __name__ == "__main__":
    main()