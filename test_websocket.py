#!/usr/bin/env python3
# ABOUTME: Test WebSocket connection and authentication
# ABOUTME: Debug why WebSocket is getting 403 Forbidden

import asyncio
import websockets
import json
import urllib.request
import urllib.parse
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
WS_BASE_URL = "ws://localhost:8000"
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
    """Get list of studies to find a valid one"""
    req = urllib.request.Request(
        f"{BASE_URL}/studies",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            studies = json.loads(response.read().decode())
            if studies:
                return studies[0]["id"]  # Return first study ID
            return None
    except Exception as e:
        print(f"[ERROR] Failed to get studies: {e}")
        return None

async def test_websocket(token, study_id):
    """Test WebSocket connection"""
    # Try different URL patterns
    urls_to_try = [
        f"{WS_BASE_URL}/ws/studies/{study_id}/initialization?token={token}",
        f"{WS_BASE_URL}/api/v1/ws/studies/{study_id}/initialization?token={token}",
    ]
    
    for url in urls_to_try:
        print(f"\n[TEST] Trying: {url[:80]}...")
        try:
            async with websockets.connect(url) as websocket:
                print("[SUCCESS] Connected!")
                
                # Wait for initial message
                message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                print(f"[RECEIVED] {message}")
                
                # Send a ping
                await websocket.send(json.dumps({"type": "ping"}))
                
                # Wait for pong
                pong = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                print(f"[RECEIVED] {pong}")
                
                return True
                
        except websockets.exceptions.InvalidStatusCode as e:
            print(f"[ERROR] HTTP {e.status_code}")
            if hasattr(e, 'headers'):
                print(f"Headers: {dict(e.headers)}")
        except asyncio.TimeoutError:
            print("[ERROR] Timeout waiting for response")
        except Exception as e:
            print(f"[ERROR] {type(e).__name__}: {e}")
    
    return False

async def main():
    print("="*60)
    print("WebSocket Connection Test")
    print("="*60)
    
    # Get fresh token
    print("\n[1] Getting fresh token...")
    token = login()
    if not token:
        print("[FAIL] Could not get token")
        return
    
    print(f"[OK] Got token: {token[:20]}...")
    
    # Get a valid study ID
    print("\n[2] Getting study ID...")
    study_id = get_studies(token)
    if not study_id:
        print("[FAIL] No studies found")
        return
    
    print(f"[OK] Using study: {study_id}")
    
    # Test WebSocket
    print("\n[3] Testing WebSocket connection...")
    success = await test_websocket(token, study_id)
    
    if success:
        print("\n[SUCCESS] WebSocket is working!")
    else:
        print("\n[FAIL] Could not connect to WebSocket")

if __name__ == "__main__":
    asyncio.run(main())
