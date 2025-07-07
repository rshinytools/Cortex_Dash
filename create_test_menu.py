#!/usr/bin/env python3
"""
Test script to create a menu template with three items:
- Overview
- Adverse Events
- Lab Data
"""
import requests
import json
import uuid
from datetime import datetime

# Login
print("Logging in...")
login_response = requests.post(
    'http://localhost:8000/api/v1/login/access-token',
    data={'username': 'admin@sagarmatha.ai', 'password': 'adadad123'}
)
token = login_response.json()['access_token']
headers = {'Authorization': f'Bearer {token}'}

# Create a menu template with three items
menu_template = {
    "code": f"clinical_trial_menu_{uuid.uuid4().hex[:8]}",
    "name": "Clinical Trial Menu",
    "description": "Standard menu template with Overview, Adverse Events, and Lab Data",
    "category": "custom",
    "template_structure": {
        "menu_structure": [
            {
                "id": "overview",
                "type": "dashboard",
                "label": "Overview",
                "icon": "home",
                "dashboard_code": "overview_dashboard",
                "order": 1,
                "permissions": None,
                "visible_conditions": None
            },
            {
                "id": "adverse_events",
                "type": "dashboard",
                "label": "Adverse Events",
                "icon": "alert-triangle",
                "dashboard_code": "adverse_events_dashboard",
                "order": 2,
                "permissions": ["view_safety_data"],
                "visible_conditions": None
            },
            {
                "id": "lab_data",
                "type": "dashboard",
                "label": "Lab Data",
                "icon": "activity",
                "dashboard_code": "lab_results_dashboard",
                "order": 3,
                "permissions": ["view_lab_data"],
                "visible_conditions": None
            }
        ],
        "dashboards": []  # Menu templates don't have dashboard definitions
    },
    "is_active": True
}

print("\nCreating menu template...")
print(f"Name: {menu_template['name']}")
print(f"Code: {menu_template['code']}")
print("Menu Items:")
for item in menu_template['template_structure']['menu_structure']:
    print(f"  - {item['label']} (icon: {item['icon']}, dashboard: {item['dashboard_code']})")

# Create the template
response = requests.post(
    'http://localhost:8000/api/v1/dashboard-templates/',
    json=menu_template,
    headers=headers
)

print(f"\nAPI Response Status: {response.status_code}")
if response.status_code == 200:
    created = response.json()
    print(f"✅ Successfully created menu template!")
    print(f"   ID: {created['id']}")
    print(f"   Name: {created['name']}")
    print(f"   Created at: {created['created_at']}")
    
    # Verify by listing custom templates
    print("\nVerifying by listing all custom category templates...")
    list_response = requests.get(
        'http://localhost:8000/api/v1/dashboard-templates/?category=custom',
        headers=headers
    )
    
    if list_response.status_code == 200:
        templates = list_response.json()
        print(f"Found {templates['count']} custom templates:")
        for template in templates['data']:
            print(f"  - {template['name']} (ID: {template['id']})")
            if template['id'] == created['id']:
                print("    ✅ Our newly created template is in the list!")
                
    # Fetch the specific template to verify menu structure
    print(f"\nFetching the created template to verify menu structure...")
    get_response = requests.get(
        f"http://localhost:8000/api/v1/dashboard-templates/{created['id']}",
        headers=headers
    )
    
    if get_response.status_code == 200:
        template_data = get_response.json()
        menu_items = template_data.get('template_structure', {}).get('menu_structure', [])
        print(f"Menu structure contains {len(menu_items)} items:")
        for item in menu_items:
            print(f"  - {item['label']} (type: {item['type']}, icon: {item['icon']})")
else:
    print(f"❌ Failed to create menu template")
    print(f"   Error: {response.text}")

print("\n✅ Test completed!")