#!/usr/bin/env python3
# ABOUTME: Check template requirements for the study
# ABOUTME: Debug why "No widget requirements found" appears

import json
import urllib.request
import urllib.parse
import sys

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
TEST_EMAIL = "admin@sagarmatha.ai"
TEST_PASSWORD = "adadad123"
STUDY_ID = "99a75912-6474-403b-a47d-644fde30adfd"

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

def check_study_template(token, study_id):
    """Check study template"""
    print(f"\nChecking study template...")
    
    req = urllib.request.Request(
        f"{BASE_URL}/studies/{study_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            study = json.loads(response.read().decode())
            template_id = study.get('dashboard_template_id')
            print(f"  Study: {study.get('name')}")
            print(f"  Template ID: {template_id}")
            return template_id
    except Exception as e:
        print(f"[ERROR] Failed to get study: {e}")
        return None

def check_template_structure(token, template_id):
    """Check template structure"""
    print(f"\nChecking template structure...")
    
    req = urllib.request.Request(
        f"{BASE_URL}/dashboard-templates/{template_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            template = json.loads(response.read().decode())
            print(f"  Template: {template.get('name')}")
            
            structure = template.get('template_structure', {})
            dashboards = structure.get('dashboardTemplates', [])
            
            print(f"\n  Dashboards: {len(dashboards)}")
            
            total_widgets = 0
            widget_requirements = []
            
            for dashboard in dashboards:
                widgets = dashboard.get('widgets', [])
                print(f"    Dashboard '{dashboard.get('name', 'Unknown')}': {len(widgets)} widgets")
                
                for widget in widgets:
                    total_widgets += 1
                    widget_id = widget.get('id')
                    widget_title = widget.get('title', 'Unknown')
                    widget_type = widget.get('type')
                    data_config = widget.get('dataConfiguration', {})
                    
                    if data_config:
                        widget_requirements.append({
                            'widget_id': widget_id,
                            'widget_title': widget_title,
                            'widget_type': widget_type,
                            'data_config': data_config
                        })
                        
                        print(f"      - {widget_title} ({widget_type})")
                        print(f"        Data config: {json.dumps(data_config, indent=10)}")
            
            print(f"\n  Total widgets: {total_widgets}")
            print(f"  Widgets with data requirements: {len(widget_requirements)}")
            
            return widget_requirements
    except Exception as e:
        print(f"[ERROR] Failed to get template: {e}")
        return None

def check_mapping_endpoint(token, study_id):
    """Check what the mapping endpoint returns"""
    print(f"\nChecking mapping-data endpoint...")
    
    req = urllib.request.Request(
        f"{BASE_URL}/studies/wizard/{study_id}/mapping-data",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode())
            
            requirements = result.get('template_requirements', [])
            print(f"  Template requirements returned: {len(requirements)}")
            
            if requirements:
                print("\n  Requirements detail:")
                for req in requirements:
                    print(f"    - {req.get('widget_title')} ({req.get('widget_type')})")
                    print(f"      Data config: {req.get('data_config')}")
            else:
                print("\n  [PROBLEM] No template requirements returned by endpoint!")
            
            return requirements
    except Exception as e:
        print(f"[ERROR] Failed to get mapping data: {e}")
        return None

def main():
    print("="*60)
    print("Template Requirements Debug Check")
    print("="*60)
    
    # Login
    token = login()
    if not token:
        print("[ERROR] Failed to login")
        sys.exit(1)
    
    print("[OK] Logged in successfully")
    
    # Check study template
    template_id = check_study_template(token, STUDY_ID)
    if not template_id:
        print("[ERROR] No template assigned to study")
        sys.exit(1)
    
    # Check template structure
    template_requirements = check_template_structure(token, template_id)
    
    # Check mapping endpoint
    mapping_requirements = check_mapping_endpoint(token, STUDY_ID)
    
    # Compare
    print("\n" + "="*60)
    print("ANALYSIS:")
    print("="*60)
    
    if template_requirements and len(template_requirements) > 0:
        print(f"  Template HAS {len(template_requirements)} widget requirements")
    else:
        print("  Template has NO widget requirements")
    
    if mapping_requirements and len(mapping_requirements) > 0:
        print(f"  Mapping endpoint returns {len(mapping_requirements)} requirements")
    else:
        print("  Mapping endpoint returns NO requirements")
    
    if template_requirements and not mapping_requirements:
        print("\n  [ISSUE] Template has requirements but mapping endpoint doesn't return them!")
        print("  This is why 'No widget requirements found' appears")

if __name__ == "__main__":
    main()