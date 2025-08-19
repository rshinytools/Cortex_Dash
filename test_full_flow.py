#!/usr/bin/env python3
# ABOUTME: Complete test of study initialization and dashboard flow
# ABOUTME: Tests API endpoints, WebSocket, and dashboard template loading

import json
import urllib.request
import urllib.parse
import time
import sys

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
            return result["access_token"]
    except Exception as e:
        print(f"[ERROR] Login failed: {e}")
        return None

def test_study_api(token, study_id):
    """Test study API endpoint"""
    print("\n[1] Testing Study API")
    print("=" * 50)
    
    req = urllib.request.Request(
        f"{BASE_URL}/studies/{study_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            study = json.loads(response.read().decode())
            print(f"[OK] Study found: {study.get('name')}")
            print(f"  - Status: {study.get('status')}")
            print(f"  - Initialization: {study.get('initialization_status')}")
            print(f"  - Template ID: {study.get('dashboard_template_id')}")
            return study
    except urllib.error.HTTPError as e:
        print(f"[FAIL] Failed to get study: HTTP {e.code}")
        return None

def test_template_api(token, template_id):
    """Test template API endpoint"""
    print("\n[2] Testing Template API")
    print("=" * 50)
    
    if not template_id:
        print("[FAIL] No template ID provided")
        return None
    
    req = urllib.request.Request(
        f"{BASE_URL}/dashboard-templates/{template_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            template = json.loads(response.read().decode())
            print(f"[OK] Template found: {template.get('name')}")
            
            if template.get('template_structure'):
                structure = template['template_structure']
                print(f"  - Menu items: {len(structure.get('menu_structure', {}).get('items', []))}")
                print(f"  - Dashboard templates: {len(structure.get('dashboardTemplates', []))}")
                
                # Check widgets
                widget_count = 0
                for dt in structure.get('dashboardTemplates', []):
                    widget_count += len(dt.get('widgets', []))
                print(f"  - Total widgets: {widget_count}")
                
            return template
    except urllib.error.HTTPError as e:
        print(f"[FAIL] Failed to get template: HTTP {e.code}")
        return None

def test_initialization_status(token, study_id):
    """Test initialization status endpoint"""
    print("\n[3] Testing Initialization Status")
    print("=" * 50)
    
    req = urllib.request.Request(
        f"{BASE_URL}/studies/{study_id}/initialization/status",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            status = json.loads(response.read().decode())
            print(f"[OK] Initialization status: {status.get('initialization_status')}")
            print(f"  - Progress: {status.get('initialization_progress')}%")
            
            if status.get('initialization_steps'):
                steps = status['initialization_steps']
                if 'error' in steps:
                    print(f"  - Error: {steps['error']}")
                if 'pending_uploads' in steps:
                    print(f"  - Pending uploads: {len(steps['pending_uploads'])}")
                    
            return status
    except urllib.error.HTTPError as e:
        print(f"[FAIL] Failed to get initialization status: HTTP {e.code}")
        return None

def test_websocket(token, study_id):
    """Test WebSocket connection"""
    print("\n[4] Testing WebSocket Connection")
    print("=" * 50)
    
    try:
        import asyncio
        import websockets
        
        async def test_ws():
            url = f"ws://localhost:8000/api/v1/ws/studies/{study_id}/initialization?token={token}"
            try:
                async with websockets.connect(url) as websocket:
                    print("[OK] WebSocket connected successfully")
                    
                    # Wait for initial message
                    message = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                    data = json.loads(message)
                    
                    if data.get('type') == 'current_status':
                        print(f"  - Received status: {data.get('initialization_status')}")
                        print(f"  - Progress: {data.get('initialization_progress')}%")
                    
                    return True
                    
            except Exception as e:
                print(f"[FAIL] WebSocket connection failed: {e}")
                return False
        
        return asyncio.run(test_ws())
        
    except ImportError:
        print("[WARN] WebSocket test skipped (websockets module not installed)")
        return None

def check_data_files(study_id):
    """Check if data files exist"""
    print("\n[5] Checking Data Files")
    print("=" * 50)
    
    import os
    from pathlib import Path
    
    # Check for uploaded files
    data_dir = Path(f"C:/Users/amuly/OneDrive/AetherClinical/Cortex_Dash/data/studies")
    
    if data_dir.exists():
        study_dirs = list(data_dir.glob(f"*/{study_id}"))
        if study_dirs:
            print(f"[OK] Study data directory found")
            for study_dir in study_dirs:
                source_data = study_dir / "source_data"
                if source_data.exists():
                    data_folders = list(source_data.iterdir())
                    print(f"  - Source data folders: {len(data_folders)}")
                    
                    for folder in data_folders[:2]:  # Show first 2
                        files = list(folder.glob("*.sas7bdat"))
                        parquet_files = list(folder.glob("*.parquet"))
                        print(f"    - {folder.name}: {len(files)} SAS files, {len(parquet_files)} Parquet files")
        else:
            print("[FAIL] No study data directory found")
    else:
        print("[FAIL] Data directory does not exist")

def main():
    print("="*60)
    print("CLINICAL DASHBOARD - COMPLETE SYSTEM TEST")
    print("="*60)
    
    # Login
    print("\n[0] Authentication")
    print("=" * 50)
    token = login()
    if not token:
        print("[FAIL] Authentication failed")
        sys.exit(1)
    print("[OK] Authentication successful")
    
    # Test study API
    study = test_study_api(token, STUDY_ID)
    if not study:
        sys.exit(1)
    
    # Test template API
    template_id = study.get('dashboard_template_id')
    template = test_template_api(token, template_id)
    
    # Test initialization status
    init_status = test_initialization_status(token, STUDY_ID)
    
    # Test WebSocket
    test_websocket(token, STUDY_ID)
    
    # Check data files
    check_data_files(STUDY_ID)
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    all_good = True
    
    if study and study.get('status') == 'SETUP':
        print("[OK] Study is in SETUP status")
    else:
        print("[FAIL] Study is not in SETUP status")
        all_good = False
    
    if study and study.get('initialization_status') == 'completed':
        print("[OK] Study initialization is completed")
    else:
        print("[FAIL] Study initialization is not completed")
        all_good = False
    
    if template:
        print("[OK] Dashboard template is accessible")
    else:
        print("[FAIL] Dashboard template is not accessible")
        all_good = False
    
    if all_good:
        print("\n[SUCCESS] All tests passed! The dashboard should be working.")
        print(f"\nYou can access the dashboard at:")
        print(f"http://localhost:3000/studies/{STUDY_ID}/dashboard")
    else:
        print("\n[WARN] Some tests failed. Please check the errors above.")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    main()