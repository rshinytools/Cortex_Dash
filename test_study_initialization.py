#!/usr/bin/env python3
# ABOUTME: Automated test script for study initialization wizard flow
# ABOUTME: Tests study creation, template selection, file upload, and metadata extraction

import requests
import json
import time
import sys
from pathlib import Path
from datetime import datetime
import random

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
FRONTEND_URL = "http://localhost:3000"
TEST_EMAIL = "admin@sagarmatha.ai"
TEST_PASSWORD = "adadad123"

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_step(message):
    print(f"\n{BLUE}→ {message}{RESET}")

def print_success(message):
    print(f"{GREEN}✓ {message}{RESET}")

def print_error(message):
    print(f"{RED}✗ {message}{RESET}")

def print_info(message):
    print(f"{YELLOW}ℹ {message}{RESET}")

class StudyInitializationTest:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.study_id = None
        self.org_id = None
        
    def login(self):
        """Login and get authentication token"""
        print_step("Logging in...")
        
        # Login using form data
        login_data = {
            "username": TEST_EMAIL,
            "password": TEST_PASSWORD
        }
        
        response = self.session.post(
            f"{BASE_URL}/login/access-token",
            data=login_data  # Use form data, not JSON
        )
        
        if response.status_code == 200:
            data = response.json()
            self.token = data["access_token"]
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
            print_success(f"Logged in successfully as {TEST_EMAIL}")
            
            # Get user info to get org_id
            user_response = self.session.get(f"{BASE_URL}/users/me")
            if user_response.status_code == 200:
                user_data = user_response.json()
                self.org_id = user_data.get("org_id")
                print_info(f"Organization ID: {self.org_id}")
            return True
        else:
            print_error(f"Login failed: {response.status_code} - {response.text}")
            return False
    
    def create_study(self):
        """Create a new study through the wizard"""
        print_step("Creating new study...")
        
        # Generate unique study name
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        study_name = f"TestStudy_{timestamp}"
        protocol_number = f"TEST_{timestamp}"
        
        study_data = {
            "name": study_name,
            "protocol_number": protocol_number,
            "description": "Automated test study",
            "phase": "phase_3",
            "therapeutic_area": "Oncology",
            "indication": "Non-Small Cell Lung Cancer (NSCLC)"
        }
        
        response = self.session.post(
            f"{BASE_URL}/studies/wizard/start",
            json=study_data
        )
        
        if response.status_code == 200:
            data = response.json()
            self.study_id = data["study_id"]
            print_success(f"Study created successfully")
            print_info(f"Study ID: {self.study_id}")
            print_info(f"Study Name: {study_name}")
            print_info(f"Protocol: {protocol_number}")
            return True
        else:
            print_error(f"Failed to create study: {response.status_code} - {response.text}")
            return False
    
    def select_template(self):
        """Select the first available dashboard template"""
        print_step("Selecting dashboard template...")
        
        # Get available templates
        response = self.session.get(
            f"{BASE_URL}/studies/wizard/{self.study_id}/templates"
        )
        
        if response.status_code != 200:
            print_error(f"Failed to get templates: {response.status_code}")
            return False
        
        templates = response.json()
        if not templates or len(templates) == 0:
            print_error("No templates available")
            return False
        
        # Select the first template
        template = templates[0]
        template_id = template["id"]
        template_name = template["name"]
        
        print_info(f"Found template: {template_name}")
        print_info(f"Widgets: {template.get('widget_count', 0)}, Dashboards: {template.get('dashboard_count', 0)}")
        
        # Select the template
        response = self.session.post(
            f"{BASE_URL}/studies/wizard/{self.study_id}/select-template",
            json={"template_id": template_id}
        )
        
        if response.status_code == 200:
            print_success(f"Template '{template_name}' selected successfully")
            
            # Update wizard state
            self.session.patch(
                f"{BASE_URL}/studies/wizard/{self.study_id}/state",
                json={
                    "current_step": 3,
                    "completed_steps": ["basic_info", "template_selection"]
                }
            )
            return True
        else:
            print_error(f"Failed to select template: {response.status_code}")
            return False
    
    def upload_files(self):
        """Upload test SAS files"""
        print_step("Uploading clinical data files...")
        
        # Find SAS files in the data directory
        data_path = Path("C:/Users/amuly/OneDrive/AetherClinical/dummy_data")
        sas_files = list(data_path.glob("*.sas7bdat"))
        
        if not sas_files:
            print_error(f"No SAS files found in {data_path}")
            return False
        
        print_info(f"Found {len(sas_files)} SAS files to upload")
        
        # Prepare multipart form data
        files = []
        for sas_file in sas_files[:7]:  # Upload up to 7 files
            print_info(f"  • {sas_file.name} ({sas_file.stat().st_size / 1024 / 1024:.2f} MB)")
            files.append(('files', (sas_file.name, open(sas_file, 'rb'), 'application/octet-stream')))
        
        # Upload files
        response = self.session.post(
            f"{BASE_URL}/studies/wizard/{self.study_id}/upload",
            files=files
        )
        
        # Close file handles
        for _, file_tuple in files:
            file_tuple[1].close()
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Successfully uploaded {data['total_files']} files")
            return True
        else:
            print_error(f"Failed to upload files: {response.status_code} - {response.text}")
            return False
    
    def complete_upload_and_extract_metadata(self):
        """Complete upload step and trigger metadata extraction"""
        print_step("Processing files and extracting metadata...")
        
        # Complete the upload step (triggers file processing)
        response = self.session.post(
            f"{BASE_URL}/studies/wizard/{self.study_id}/complete-upload"
        )
        
        if response.status_code != 200:
            print_error(f"Failed to complete upload: {response.status_code} - {response.text}")
            return False
        
        data = response.json()
        print_success(f"Upload completed successfully")
        print_info(f"Files processed: {data.get('uploaded_files_count', 0)}")
        print_info(f"Datasets found: {data.get('datasets_found', 0)}")
        print_info(f"Converted files: {data.get('converted_files_count', 0)}")
        
        if data.get('processing_errors'):
            print_error("Processing errors:")
            for error in data['processing_errors']:
                print_error(f"  • {error}")
        
        if data.get('processing_warnings'):
            print_info("Processing warnings:")
            for warning in data['processing_warnings']:
                print_info(f"  • {warning}")
        
        return data.get('datasets_found', 0) > 0
    
    def verify_metadata(self):
        """Verify that metadata has been extracted"""
        print_step("Verifying metadata extraction...")
        
        # Get mapping data (which includes extracted schemas)
        response = self.session.get(
            f"{BASE_URL}/studies/wizard/{self.study_id}/mapping-data"
        )
        
        if response.status_code != 200:
            print_error(f"Failed to get mapping data: {response.status_code}")
            return False
        
        data = response.json()
        
        # Check dataset schemas
        schemas = data.get("dataset_schemas", {})
        if not schemas:
            print_error("No dataset schemas found")
            return False
        
        print_success(f"Metadata extracted successfully for {len(schemas)} datasets:")
        
        for dataset_name, schema in schemas.items():
            columns = schema.get("columns", {})
            row_count = schema.get("row_count", 0)
            print_info(f"\n  📊 Dataset: {dataset_name}")
            print_info(f"     Rows: {row_count:,}")
            print_info(f"     Columns: {len(columns)}")
            
            # Show first 5 columns as sample
            if columns:
                print_info("     Sample columns:")
                for i, (col_name, col_info) in enumerate(list(columns.items())[:5]):
                    dtype = col_info.get("dtype", "unknown")
                    print_info(f"       • {col_name} ({dtype})")
                if len(columns) > 5:
                    print_info(f"       ... and {len(columns) - 5} more columns")
        
        # Check template requirements
        requirements = data.get("template_requirements", [])
        if requirements:
            print_info(f"\n  📋 Template has {len(requirements)} widget data requirements")
        
        # Check mapping suggestions
        suggestions = data.get("mapping_suggestions", {})
        if suggestions:
            print_info(f"  🔗 Auto-mapping suggestions generated for widgets")
        
        return True
    
    def cleanup(self):
        """Optional: Delete the test study"""
        print_step("Cleanup...")
        
        if self.study_id:
            # Archive the study (soft delete)
            response = self.session.delete(
                f"{BASE_URL}/studies/{self.study_id}"
            )
            
            if response.status_code in [200, 204]:
                print_success("Test study archived")
            else:
                print_info("Could not archive test study (may need manual cleanup)")
    
    def run_test(self):
        """Run the complete test flow"""
        print(f"\n{BLUE}{'='*60}{RESET}")
        print(f"{BLUE}Study Initialization Automated Test{RESET}")
        print(f"{BLUE}{'='*60}{RESET}")
        
        try:
            # Step 1: Login
            if not self.login():
                return False
            
            # Step 2: Create study
            if not self.create_study():
                return False
            
            # Step 3: Select template
            if not self.select_template():
                return False
            
            # Step 4: Upload files
            if not self.upload_files():
                return False
            
            # Step 5: Complete upload and extract metadata
            if not self.complete_upload_and_extract_metadata():
                return False
            
            # Step 6: Verify metadata
            if not self.verify_metadata():
                return False
            
            print(f"\n{GREEN}{'='*60}{RESET}")
            print(f"{GREEN}✅ ALL TESTS PASSED SUCCESSFULLY!{RESET}")
            print(f"{GREEN}{'='*60}{RESET}")
            
            print(f"\n{YELLOW}Next Steps:{RESET}")
            print(f"1. Go to: {FRONTEND_URL}/studies/{self.study_id}/initialization")
            print(f"2. Navigate to the 'Review & Activate' step")
            print(f"3. Complete the manual field mapping")
            print(f"4. Activate the study")
            
            return True
            
        except Exception as e:
            print_error(f"Test failed with exception: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
        
        finally:
            # Optional cleanup
            # self.cleanup()
            pass

def main():
    """Main entry point"""
    test = StudyInitializationTest()
    success = test.run_test()
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()