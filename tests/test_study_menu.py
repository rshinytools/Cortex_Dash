#!/usr/bin/env python3
# ABOUTME: Test script to verify study menu endpoint functionality
# ABOUTME: Creates a test dashboard template with menu structure and retrieves it

import requests
import json
from datetime import datetime

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

def create_dashboard_template_with_menu(token):
    """Create a dashboard template with embedded menu structure"""
    headers = {"Authorization": f"Bearer {token}"}
    
    template_data = {
        "code": f"test_menu_dashboard_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "name": "Test Dashboard with Menu",
        "category": "custom",
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
                        "id": "safety-group",
                        "type": "group",
                        "label": "Safety Monitoring",
                        "order": 2,
                        "children": [
                            {
                                "id": "adverse-events",
                                "type": "dashboard",
                                "label": "Adverse Events",
                                "icon": "Shield",
                                "order": 1
                            },
                            {
                                "id": "lab-data",
                                "type": "dashboard",
                                "label": "Lab Data",
                                "icon": "FlaskConical",
                                "order": 2
                            }
                        ]
                    },
                    {
                        "id": "efficacy",
                        "type": "dashboard",
                        "label": "Efficacy Analysis",
                        "icon": "BarChart3",
                        "order": 3
                    }
                ]
            },
            "dashboards": []
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
        return template['id']
    else:
        print(f"✗ Failed to create template: {response.status_code} - {response.text}")
        return None

def get_study_menu(token, study_id):
    """Get menu structure for a study"""
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(
        f"{BASE_URL}/runtime/{study_id}/menus",
        headers=headers
    )
    
    if response.status_code == 200:
        menu = response.json()
        print("✓ Retrieved study menu:")
        print(json.dumps(menu, indent=2))
        return menu
    else:
        print(f"✗ Failed to get menu: {response.status_code} - {response.text}")
        return None

def main():
    # Login
    token = login()
    if not token:
        return
    
    # Create dashboard template with menu
    template_id = create_dashboard_template_with_menu(token)
    if not template_id:
        return
    
    # Get first study (you may need to adjust this)
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/studies", headers=headers)
    if response.status_code == 200 and response.json():
        study = response.json()[0]
        study_id = study['id']
        print(f"\n✓ Using study: {study['name']} ({study_id})")
        
        # Get menu for the study
        menu = get_study_menu(token, study_id)
    else:
        print("✗ No studies found")

if __name__ == "__main__":
    main()