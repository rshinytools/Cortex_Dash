#!/usr/bin/env python3
# ABOUTME: Simple file upload test using only standard library
# ABOUTME: Tests file upload and metadata extraction for study initialization

import json
import os
import sys
from pathlib import Path
import urllib.request
import urllib.parse
import mimetypes
import io
import uuid

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
TEST_EMAIL = "admin@sagarmatha.ai"
TEST_PASSWORD = "adadad123"

def login():
    """Login and get token"""
    print("Logging in...")
    
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
            print(f"[OK] Logged in as {TEST_EMAIL}")
            return result["access_token"]
    except Exception as e:
        print(f"[ERROR] Login failed: {e}")
        return None

def get_recent_study(token):
    """Get the most recent study in initialization"""
    print("\nGetting recent studies...")
    
    req = urllib.request.Request(
        f"{BASE_URL}/studies/",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            studies = json.loads(response.read().decode())
            # Find studies that are draft or in initialization
            init_studies = [s for s in studies if s.get("status") in ["draft", "planning", "active"] 
                           and s.get("initialization_status") in ["pending", "not_started", None]]
            if init_studies:
                # Get the most recent one
                study = sorted(init_studies, key=lambda x: x.get("created_at", ""), reverse=True)[0]
                print(f"[OK] Found study: {study['name']} (ID: {study['id']})")
                return study["id"]
            else:
                print("[ERROR] No studies in initialization found")
                return None
    except Exception as e:
        print(f"[ERROR] Failed to get studies: {e}")
        return None

def create_multipart_formdata(files):
    """Create multipart/form-data manually"""
    boundary = f"----WebKitFormBoundary{uuid.uuid4().hex[:16]}"
    body = io.BytesIO()
    
    for filepath in files:
        filename = os.path.basename(filepath)
        
        # Add file field
        body.write(f'------{boundary}\r\n'.encode())
        body.write(f'Content-Disposition: form-data; name="files"; filename="{filename}"\r\n'.encode())
        body.write(b'Content-Type: application/octet-stream\r\n\r\n')
        
        with open(filepath, 'rb') as f:
            body.write(f.read())
        body.write(b'\r\n')
    
    # End boundary
    body.write(f'------{boundary}--\r\n'.encode())
    
    return body.getvalue(), f"multipart/form-data; boundary=----{boundary}"

def upload_files(token, study_id):
    """Upload test SAS files"""
    print(f"\nUploading files for study {study_id}...")
    
    # Find SAS files in Sample_Data folder
    data_path = Path("C:/Users/amuly/OneDrive/AetherClinical/Cortex_Dash/Sample_Data")
    sas_files = list(data_path.glob("*.sas7bdat"))[:5]  # Upload first 5 files for testing
    
    if not sas_files:
        print(f"[ERROR] No SAS files found in {data_path}")
        return False
    
    print(f"Found {len(sas_files)} SAS files to upload:")
    for f in sas_files:
        print(f"  - {f.name} ({f.stat().st_size / 1024 / 1024:.2f} MB)")
    
    # Create multipart form data
    body, content_type = create_multipart_formdata([str(f) for f in sas_files])
    
    req = urllib.request.Request(
        f"{BASE_URL}/studies/wizard/{study_id}/upload",
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": content_type
        }
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode())
            print(f"[OK] Successfully uploaded {result.get('total_files', 0)} files")
            return True
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f"[ERROR] Upload failed: {e.code} - {error_body}")
        return False
    except Exception as e:
        print(f"[ERROR] Upload failed: {e}")
        return False

def complete_upload(token, study_id):
    """Complete upload and trigger metadata extraction"""
    print(f"\nCompleting upload and extracting metadata...")
    
    req = urllib.request.Request(
        f"{BASE_URL}/studies/wizard/{study_id}/complete-upload",
        data=b"{}",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode())
            print(f"[OK] Upload completed")
            print(f"  - Files processed: {result.get('uploaded_files_count', 0)}")
            print(f"  - Datasets found: {result.get('datasets_found', 0)}")
            print(f"  - Converted files: {result.get('converted_files_count', 0)}")
            return True
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f"[ERROR] Complete upload failed: {e.code} - {error_body}")
        return False
    except Exception as e:
        print(f"[ERROR] Complete upload failed: {e}")
        return False

def get_mapping_data(token, study_id):
    """Get mapping data to verify metadata extraction"""
    print(f"\nVerifying metadata extraction...")
    
    req = urllib.request.Request(
        f"{BASE_URL}/studies/wizard/{study_id}/mapping-data",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode())
            schemas = result.get("dataset_schemas", {})
            
            if schemas:
                print(f"[OK] Metadata extracted for {len(schemas)} datasets:")
                for dataset_name, schema in schemas.items():
                    columns = schema.get("columns", {})
                    row_count = schema.get("row_count", 0)
                    print(f"  [DATA] {dataset_name}: {row_count:,} rows, {len(columns)} columns")
                return True
            else:
                print("[ERROR] No metadata extracted")
                return False
    except Exception as e:
        print(f"[ERROR] Failed to get mapping data: {e}")
        return False

def main():
    """Run the file upload test"""
    print("="*60)
    print("File Upload and Metadata Extraction Test")
    print("="*60)
    
    # Step 1: Login
    token = login()
    if not token:
        sys.exit(1)
    
    # Step 2: Get recent study
    study_id = get_recent_study(token)
    if not study_id:
        print("\nPlease create a study first using test_study_init.bat")
        sys.exit(1)
    
    # Step 3: Upload files
    if not upload_files(token, study_id):
        sys.exit(1)
    
    # Step 4: Complete upload and extract metadata
    if not complete_upload(token, study_id):
        sys.exit(1)
    
    # Step 5: Verify metadata
    if not get_mapping_data(token, study_id):
        sys.exit(1)
    
    print("\n" + "="*60)
    print("[SUCCESS] ALL TESTS PASSED!")
    print("="*60)
    print(f"\nNext steps:")
    print(f"1. Go to: http://localhost:3000/studies/{study_id}/initialization")
    print(f"2. Navigate to 'Review & Activate' step")
    print(f"3. Complete manual field mapping")
    print(f"4. Activate the study")

if __name__ == "__main__":
    main()