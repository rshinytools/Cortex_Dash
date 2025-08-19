#!/usr/bin/env python3
# ABOUTME: Test file upload for a specific study ID
# ABOUTME: Uploads SAS files from Sample_Data folder to the study

import json
import os
import sys
from pathlib import Path
import urllib.request
import urllib.parse
import io
import uuid

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
TEST_EMAIL = "admin@sagarmatha.ai"
TEST_PASSWORD = "adadad123"

# The study ID from our previous test
STUDY_ID = "f1001104-8dde-4ff7-b008-5710e367ea44"

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
        print(f"  - {f.name} ({f.stat().st_size / 1024:.2f} KB)")
    
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
            print(f"     Upload location: data/studies/{study_id}/...")
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
            
            # Show any errors or warnings
            if result.get('processing_errors'):
                print("\n[ERRORS]:")
                for error in result['processing_errors']:
                    print(f"  - {error}")
            
            if result.get('processing_warnings'):
                print("\n[WARNINGS]:")
                for warning in result['processing_warnings']:
                    print(f"  - {warning}")
                    
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
                    print(f"\n  [DATASET] {dataset_name}")
                    print(f"    - Rows: {row_count:,}")
                    print(f"    - Columns: {len(columns)}")
                    
                    # Show first few columns
                    if columns:
                        print(f"    - Sample columns:")
                        for i, col_name in enumerate(list(columns.keys())[:5]):
                            col_info = columns[col_name]
                            dtype = col_info.get("dtype", "unknown")
                            print(f"      * {col_name} ({dtype})")
                        if len(columns) > 5:
                            print(f"      * ... and {len(columns) - 5} more columns")
                
                # Check template requirements
                requirements = result.get("template_requirements", [])
                if requirements:
                    print(f"\n[TEMPLATE] Has {len(requirements)} widget data requirements")
                
                # Check mapping suggestions
                suggestions = result.get("mapping_suggestions", {})
                if suggestions:
                    print(f"[MAPPING] Auto-mapping suggestions available")
                    
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
    print("File Upload Test for Study: " + STUDY_ID)
    print("="*60)
    
    # Step 1: Login
    token = login()
    if not token:
        sys.exit(1)
    
    # Step 2: Upload files
    if not upload_files(token, STUDY_ID):
        sys.exit(1)
    
    # Step 3: Complete upload and extract metadata
    if not complete_upload(token, STUDY_ID):
        sys.exit(1)
    
    # Step 4: Verify metadata
    if not get_mapping_data(token, STUDY_ID):
        sys.exit(1)
    
    print("\n" + "="*60)
    print("[SUCCESS] ALL TESTS PASSED!")
    print("="*60)
    print(f"\nNext steps:")
    print(f"1. Go to: http://localhost:3000/studies/{STUDY_ID}/initialization")
    print(f"2. Navigate to 'Review & Activate' step")
    print(f"3. Complete manual field mapping")
    print(f"4. Activate the study")

if __name__ == "__main__":
    main()