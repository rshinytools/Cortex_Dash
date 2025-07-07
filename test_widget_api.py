#!/usr/bin/env python3
# ABOUTME: Test script for widget API endpoints
# ABOUTME: Verifies that widget, dashboard, and menu endpoints are working

import requests
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8000"
API_V1 = f"{BASE_URL}/api/v1"

def get_auth_token(username: str = "admin@sagarmatha.ai", password: str = "adadad123") -> str:
    """Get authentication token"""
    response = requests.post(
        f"{API_V1}/login/access-token",
        data={"username": username, "password": password}
    )
    if not response.ok:
        print(f"Login error: {response.status_code} - {response.text}")
    response.raise_for_status()
    return response.json()["access_token"]

def test_widget_endpoints(token: str):
    """Test widget management endpoints"""
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n=== Testing Widget Endpoints ===")
    
    # List widgets
    print("\n1. List widgets:")
    response = requests.get(f"{API_V1}/admin/widgets", headers=headers)
    print(f"Status: {response.status_code}")
    if response.ok:
        data = response.json()
        if isinstance(data, list):
            print(f"Total widgets: {len(data)}")
            print(f"First widget: {data[0] if data else 'None'}")
        else:
            print(f"Total widgets: {data.get('count', 0)}")
            print(f"First widget: {data.get('data', [])[0] if data.get('data') else 'None'}")
    else:
        print(f"Error: {response.text}")
    
    # Create a widget
    print("\n2. Create a widget:")
    widget_data = {
        "code": "test_metric_card",
        "name": "Test Metric Card",
        "description": "A test metric card widget",
        "category": "metrics",
        "config_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "dataset": {"type": "string"}
            }
        },
        "default_config": {
            "title": "Default Title"
        }
    }
    response = requests.post(f"{API_V1}/admin/widgets", headers=headers, json=widget_data)
    print(f"Status: {response.status_code}")
    if response.ok:
        created_widget = response.json()
        print(f"Created widget ID: {created_widget.get('id')}")
        return created_widget.get('id')
    else:
        print(f"Error: {response.text}")
        return None

def test_dashboard_endpoints(token: str):
    """Test dashboard management endpoints"""
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n=== Testing Dashboard Endpoints ===")
    
    # List dashboards
    print("\n1. List dashboards:")
    response = requests.get(f"{API_V1}/admin/dashboards", headers=headers)
    print(f"Status: {response.status_code}")
    if response.ok:
        data = response.json()
        if isinstance(data, list):
            print(f"Total dashboards: {len(data)}")
        else:
            print(f"Total dashboards: {data.get('count', 0)}")
    else:
        print(f"Error: {response.text}")

def test_menu_endpoints(token: str):
    """Test menu management endpoints"""
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n=== Testing Menu Endpoints ===")
    
    # List menus
    print("\n1. List menus:")
    response = requests.get(f"{API_V1}/admin/menus", headers=headers)
    print(f"Status: {response.status_code}")
    if response.ok:
        data = response.json()
        if isinstance(data, list):
            print(f"Total menus: {len(data)}")
        else:
            print(f"Total menus: {data.get('count', 0)}")
    else:
        print(f"Error: {response.text}")

def main():
    """Run all tests"""
    print("Testing Widget Management API Endpoints")
    print("=====================================")
    
    try:
        # Get auth token
        print("Getting authentication token...")
        token = get_auth_token()
        print("✓ Authentication successful")
        
        # Test endpoints
        test_widget_endpoints(token)
        test_dashboard_endpoints(token)
        test_menu_endpoints(token)
        
        print("\n✓ All tests completed!")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")

if __name__ == "__main__":
    main()