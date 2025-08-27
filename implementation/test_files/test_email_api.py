#!/usr/bin/env python3
"""
Test script for Email Settings API
Tests CRUD operations and email sending functionality
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
AUTH_ENDPOINT = "/login/access-token"
EMAIL_ENDPOINT = "/email"

# Test credentials
ADMIN_EMAIL = "admin@sagarmatha.ai"
ADMIN_PASSWORD = "adadad123"

# Test SMTP settings (using Mailcatcher)
TEST_SMTP_SETTINGS = {
    "smtp_host": "localhost",
    "smtp_port": 1025,  # Mailcatcher SMTP port
    "smtp_username": None,
    "smtp_password": None,
    "smtp_from_email": "noreply@sagarmatha.ai",
    "smtp_from_name": "Clinical Dashboard",
    "smtp_use_tls": False,
    "smtp_use_ssl": False,
    "smtp_timeout": 30,
    "test_recipient_email": "test@sagarmatha.ai"
}

# Test email template
TEST_TEMPLATE = {
    "template_key": "test_notification",
    "template_name": "Test Notification",
    "subject": "Test Email - {{ title }}",
    "html_template": """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; }
            .container { max-width: 600px; margin: 0 auto; padding: 20px; }
            .header { background-color: #4CAF50; color: white; padding: 20px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>{{ title }}</h2>
            </div>
            <div class="content">
                <p>Hello {{ name }},</p>
                <p>{{ message }}</p>
                <p>Sent at: {{ timestamp }}</p>
            </div>
        </div>
    </body>
    </html>
    """,
    "plain_text_template": "{{ title }}\\n\\nHello {{ name }},\\n\\n{{ message }}\\n\\nSent at: {{ timestamp }}",
    "variables": {
        "title": "Email title",
        "name": "Recipient name",
        "message": "Email message content",
        "timestamp": "Send timestamp"
    },
    "category": "notification",
    "is_active": True
}


def get_auth_token():
    """Get authentication token"""
    print("🔐 Getting authentication token...")
    
    response = requests.post(
        f"{BASE_URL.replace('/api/v1', '')}{AUTH_ENDPOINT}",
        data={
            "username": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        }
    )
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        print("✅ Authentication successful")
        return token
    else:
        print(f"❌ Authentication failed: {response.text}")
        return None


def test_create_email_settings(headers):
    """Test creating email settings"""
    print("\n📧 Testing email settings creation...")
    
    response = requests.post(
        f"{BASE_URL}{EMAIL_ENDPOINT}/settings",
        headers=headers,
        json=TEST_SMTP_SETTINGS
    )
    
    if response.status_code == 200:
        settings = response.json()
        print(f"✅ Email settings created: ID = {settings['id']}")
        return settings['id']
    else:
        print(f"❌ Failed to create settings: {response.text}")
        return None


def test_get_email_settings(headers):
    """Test getting email settings"""
    print("\n📋 Testing get email settings...")
    
    response = requests.get(
        f"{BASE_URL}{EMAIL_ENDPOINT}/settings",
        headers=headers
    )
    
    if response.status_code == 200:
        settings = response.json()
        print(f"✅ Retrieved settings: {settings['smtp_host']}:{settings['smtp_port']}")
        return True
    elif response.status_code == 404:
        print("ℹ️ No settings found (expected for first run)")
        return True
    else:
        print(f"❌ Failed to get settings: {response.text}")
        return False


def test_create_template(headers):
    """Test creating email template"""
    print("\n📝 Testing template creation...")
    
    response = requests.post(
        f"{BASE_URL}{EMAIL_ENDPOINT}/templates",
        headers=headers,
        json=TEST_TEMPLATE
    )
    
    if response.status_code == 200:
        template = response.json()
        print(f"✅ Template created: {template['template_key']}")
        return True
    elif response.status_code == 400:
        print("ℹ️ Template already exists")
        return True
    else:
        print(f"❌ Failed to create template: {response.text}")
        return False


def test_list_templates(headers):
    """Test listing templates"""
    print("\n📚 Testing list templates...")
    
    response = requests.get(
        f"{BASE_URL}{EMAIL_ENDPOINT}/templates",
        headers=headers
    )
    
    if response.status_code == 200:
        templates = response.json()
        print(f"✅ Found {len(templates)} templates")
        for template in templates:
            print(f"   - {template['template_key']}: {template['template_name']}")
        return True
    else:
        print(f"❌ Failed to list templates: {response.text}")
        return False


def test_send_email(headers):
    """Test sending an email"""
    print("\n✉️ Testing email sending...")
    
    response = requests.post(
        f"{BASE_URL}{EMAIL_ENDPOINT}/send",
        headers=headers,
        json={
            "to_email": "test@sagarmatha.ai",
            "template_key": "test_notification",
            "variables": {
                "title": "API Test Email",
                "name": "Test User",
                "message": "This is a test email sent via the API.",
                "timestamp": datetime.now().isoformat()
            },
            "priority": 1
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Email queued: Queue ID = {result.get('queue_id')}")
        return result.get('queue_id')
    else:
        print(f"❌ Failed to send email: {response.text}")
        return None


def test_email_queue(headers):
    """Test getting email queue"""
    print("\n📬 Testing email queue...")
    
    response = requests.get(
        f"{BASE_URL}{EMAIL_ENDPOINT}/queue",
        headers=headers
    )
    
    if response.status_code == 200:
        queue = response.json()
        print(f"✅ Queue has {len(queue)} items")
        for item in queue[:5]:  # Show first 5
            print(f"   - {item['recipient_email']}: {item['status']} - {item['subject']}")
        return True
    else:
        print(f"❌ Failed to get queue: {response.text}")
        return False


def test_email_history(headers):
    """Test getting email history"""
    print("\n📜 Testing email history...")
    
    response = requests.get(
        f"{BASE_URL}{EMAIL_ENDPOINT}/history",
        headers=headers,
        params={"limit": 10}
    )
    
    if response.status_code == 200:
        history = response.json()
        print(f"✅ History has {len(history)} entries")
        for entry in history[:5]:  # Show first 5
            print(f"   - {entry['recipient_email']}: {entry['status']} - {entry.get('sent_at', 'Not sent')}")
        return True
    else:
        print(f"❌ Failed to get history: {response.text}")
        return False


def test_smtp_connection(headers):
    """Test SMTP connection"""
    print("\n🔌 Testing SMTP connection...")
    
    response = requests.post(
        f"{BASE_URL}{EMAIL_ENDPOINT}/settings/test",
        headers=headers,
        json={
            "to_email": "test@sagarmatha.ai",
            "test_connection": True
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        if result['success']:
            print("✅ SMTP connection successful")
            print(f"   Connection test: {result.get('connection_test', {})}")
        else:
            print(f"⚠️ Connection failed: {result}")
        return result['success']
    else:
        print(f"❌ Failed to test connection: {response.text}")
        return False


def test_user_preferences(headers):
    """Test user email preferences"""
    print("\n👤 Testing user email preferences...")
    
    # Get current preferences
    response = requests.get(
        f"{BASE_URL}{EMAIL_ENDPOINT}/preferences/me",
        headers=headers
    )
    
    if response.status_code == 200:
        prefs = response.json()
        print("✅ Retrieved user preferences")
        print(f"   - Receive study updates: {prefs.get('receive_study_updates', True)}")
        print(f"   - Receive backup notifications: {prefs.get('receive_backup_notifications', True)}")
        
        # Update preferences
        response = requests.put(
            f"{BASE_URL}{EMAIL_ENDPOINT}/preferences/me",
            headers=headers,
            json={
                "receive_marketing": False,
                "digest_frequency": "daily"
            }
        )
        
        if response.status_code == 200:
            print("✅ Updated user preferences")
            return True
        else:
            print(f"⚠️ Failed to update preferences: {response.text}")
            return False
    else:
        print(f"❌ Failed to get preferences: {response.text}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("📧 EMAIL SETTINGS API TEST SUITE")
    print("=" * 60)
    
    # Get auth token
    token = get_auth_token()
    if not token:
        print("\n❌ Cannot proceed without authentication")
        return
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Run tests
    tests_passed = 0
    tests_total = 0
    
    # Test settings
    tests_total += 1
    if test_get_email_settings(headers):
        tests_passed += 1
    
    tests_total += 1
    if test_create_email_settings(headers):
        tests_passed += 1
    
    # Test templates
    tests_total += 1
    if test_create_template(headers):
        tests_passed += 1
    
    tests_total += 1
    if test_list_templates(headers):
        tests_passed += 1
    
    # Test SMTP connection
    tests_total += 1
    if test_smtp_connection(headers):
        tests_passed += 1
    
    # Test email sending
    tests_total += 1
    if test_send_email(headers):
        tests_passed += 1
    
    # Test queue and history
    tests_total += 1
    if test_email_queue(headers):
        tests_passed += 1
    
    tests_total += 1
    if test_email_history(headers):
        tests_passed += 1
    
    # Test user preferences
    tests_total += 1
    if test_user_preferences(headers):
        tests_passed += 1
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"Tests Passed: {tests_passed}/{tests_total}")
    
    if tests_passed == tests_total:
        print("✅ All tests passed!")
    else:
        print(f"⚠️ {tests_total - tests_passed} tests failed")
    
    # Check Mailcatcher for emails
    print("\n💡 Tip: Check Mailcatcher at http://localhost:1080 to view sent emails")


if __name__ == "__main__":
    main()