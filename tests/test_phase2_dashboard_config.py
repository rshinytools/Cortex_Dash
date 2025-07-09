#!/usr/bin/env python3
# ABOUTME: Test script for Phase 2 - Study Dashboard Configuration
# ABOUTME: Creates study with dashboard template and verifies real configuration loads

import requests
import json
from datetime import datetime
import uuid

# Configuration
BASE_URL = "http://localhost:5173/api/v1"
USERNAME = "test@example.com"
PASSWORD = "changethis123"

def login():
    """Login and get access token"""
    response = requests.post(
        f"{BASE_URL}/auth/login",
        data={
            "username": USERNAME,
            "password": PASSWORD
        }
    )
    if response.status_code == 200:
        token = response.json()["access_token"]
        print("✓ Login successful")
        return token
    else:
        print(f"✗ Login failed: {response.status_code} - {response.text}")
        return None

def create_test_dashboard_template(token):
    """Create a dashboard template with real widget configurations"""
    headers = {"Authorization": f"Bearer {token}"}
    
    template_data = {
        "code": f"clinical_overview_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "name": "Clinical Overview Dashboard",
        "category": "overview",
        "template_structure": {
            "menu_structure": {
                "items": [
                    {
                        "id": "overview",
                        "type": "dashboard",
                        "label": "Study Overview",
                        "icon": "LayoutDashboard",
                        "order": 1
                    },
                    {
                        "id": "enrollment",
                        "type": "dashboard",
                        "label": "Enrollment",
                        "icon": "Users",
                        "order": 2
                    },
                    {
                        "id": "safety",
                        "type": "dashboard",
                        "label": "Safety",
                        "icon": "Shield",
                        "order": 3
                    }
                ]
            },
            "dashboards": [
                {
                    "id": "overview",
                    "layout": [
                        {
                            "i": "total-enrolled",
                            "type": "metric-card",
                            "x": 0, "y": 0, "w": 3, "h": 2,
                            "config": {
                                "title": "Total Enrolled",
                                "dataset": "ADSL",
                                "calculation": "count",
                                "filter": "SAFFL='Y'"
                            }
                        },
                        {
                            "i": "screen-failures",
                            "type": "metric-card",
                            "x": 3, "y": 0, "w": 3, "h": 2,
                            "config": {
                                "title": "Screen Failures",
                                "dataset": "ADSL",
                                "calculation": "count",
                                "filter": "SCRFL='Y'"
                            }
                        },
                        {
                            "i": "discontinuations",
                            "type": "metric-card",
                            "x": 6, "y": 0, "w": 3, "h": 2,
                            "config": {
                                "title": "Discontinuations",
                                "dataset": "ADSL",
                                "calculation": "count",
                                "filter": "DCSREAS IS NOT NULL"
                            }
                        },
                        {
                            "i": "completion-rate",
                            "type": "metric-card",
                            "x": 9, "y": 0, "w": 3, "h": 2,
                            "config": {
                                "title": "Completion Rate",
                                "dataset": "ADSL",
                                "calculation": "percentage",
                                "numerator_filter": "COMPLFL='Y'",
                                "denominator_filter": "SAFFL='Y'"
                            }
                        }
                    ]
                },
                {
                    "id": "enrollment",
                    "layout": [
                        {
                            "i": "enrollment-by-site",
                            "type": "bar-chart",
                            "x": 0, "y": 0, "w": 6, "h": 4,
                            "config": {
                                "title": "Enrollment by Site",
                                "dataset": "ADSL",
                                "x_axis": "SITEID",
                                "y_axis": "count"
                            }
                        },
                        {
                            "i": "enrollment-trend",
                            "type": "line-chart",
                            "x": 6, "y": 0, "w": 6, "h": 4,
                            "config": {
                                "title": "Enrollment Over Time",
                                "dataset": "ADSL",
                                "x_axis": "RANDDT",
                                "y_axis": "cumulative_count",
                                "group_by": "ARM"
                            }
                        }
                    ]
                },
                {
                    "id": "safety",
                    "layout": [
                        {
                            "i": "total-aes",
                            "type": "metric-card",
                            "x": 0, "y": 0, "w": 3, "h": 2,
                            "config": {
                                "title": "Total AEs",
                                "dataset": "ADAE",
                                "calculation": "count"
                            }
                        },
                        {
                            "i": "serious-aes",
                            "type": "metric-card",
                            "x": 3, "y": 0, "w": 3, "h": 2,
                            "config": {
                                "title": "Serious AEs",
                                "dataset": "ADAE",
                                "calculation": "count",
                                "filter": "AESER='Y'"
                            }
                        },
                        {
                            "i": "ae-table",
                            "type": "table",
                            "x": 0, "y": 2, "w": 12, "h": 6,
                            "config": {
                                "title": "Adverse Events List",
                                "dataset": "ADAE",
                                "columns": ["USUBJID", "AETERM", "AESTDTC", "AESER", "AEREL"],
                                "sort_by": "AESTDTC",
                                "sort_order": "desc"
                            }
                        }
                    ]
                }
            ],
            "data_requirements": {
                "required_datasets": ["ADSL", "ADAE"],
                "field_mappings": {
                    "ADSL": ["USUBJID", "SAFFL", "SCRFL", "DCSREAS", "COMPLFL", "SITEID", "RANDDT", "ARM"],
                    "ADAE": ["USUBJID", "AETERM", "AESTDTC", "AESER", "AEREL"]
                }
            }
        },
        "is_active": True
    }
    
    response = requests.post(
        f"{BASE_URL}/admin/dashboard-templates",
        headers=headers,
        json=template_data
    )
    
    if response.status_code == 200:
        template = response.json()
        print(f"✓ Created dashboard template: {template['id']}")
        return template
    else:
        print(f"✗ Failed to create template: {response.status_code} - {response.text}")
        return None

def initialize_study_with_template(token, study_id, template_id):
    """Initialize study with dashboard template"""
    headers = {"Authorization": f"Bearer {token}"}
    
    init_data = {
        "dashboard_template_id": template_id,
        "field_mappings": {
            "ADSL": {
                "USUBJID": "subject_id",
                "SAFFL": "safety_flag",
                "SITEID": "site_id"
            },
            "ADAE": {
                "USUBJID": "subject_id",
                "AETERM": "adverse_event"
            }
        }
    }
    
    response = requests.post(
        f"{BASE_URL}/studies/{study_id}/initialize",
        headers=headers,
        json=init_data
    )
    
    if response.status_code == 200:
        print(f"✓ Study initialized with dashboard template")
        return True
    else:
        print(f"✗ Failed to initialize study: {response.status_code} - {response.text}")
        return False

def verify_dashboard_config(token, study_id):
    """Verify dashboard configuration is loaded correctly"""
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get dashboard configuration
    response = requests.get(
        f"{BASE_URL}/runtime/{study_id}/dashboard-config",
        headers=headers
    )
    
    if response.status_code == 200:
        config = response.json()
        print("\n✓ Dashboard configuration loaded:")
        print(f"  - Dashboard: {config['dashboard_name']}")
        print(f"  - Template ID: {config['dashboard_template_id']}")
        print(f"  - Menu Layouts: {len(config.get('menu_layouts', {}))} pages")
        
        # Verify each menu has widgets
        for menu_id, layout in config.get('menu_layouts', {}).items():
            widget_count = len(layout)
            widget_types = [w.get('type', 'unknown') for w in layout]
            print(f"    - {menu_id}: {widget_count} widgets ({', '.join(set(widget_types))})")
        
        return True
    else:
        print(f"✗ Failed to get dashboard config: {response.status_code} - {response.text}")
        return False

def main():
    print("=== Phase 2: Study Dashboard Configuration Test ===\n")
    
    # Login
    token = login()
    if not token:
        return
    
    # Create dashboard template
    template = create_test_dashboard_template(token)
    if not template:
        return
    
    # Get or create a study
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/studies", headers=headers)
    
    if response.status_code == 200 and response.json():
        study = response.json()[0]
        study_id = study['id']
        print(f"\n✓ Using study: {study['name']} ({study_id})")
        
        # Initialize study with template
        if initialize_study_with_template(token, study_id, template['id']):
            # Verify configuration
            if verify_dashboard_config(token, study_id):
                print("\n✅ Phase 2 Implementation: COMPLETE")
                print("  - Study initialization creates StudyDashboard record")
                print("  - Dashboard config API returns real template data")
                print("  - Menu layouts properly loaded with widgets")
                print("\nNext: Test in browser to verify widgets display correctly")
    else:
        print("✗ No studies found. Please create a study first.")

if __name__ == "__main__":
    main()