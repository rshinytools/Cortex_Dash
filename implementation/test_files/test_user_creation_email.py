#!/usr/bin/env python3
# ABOUTME: Test script to verify email is sent when creating a new user
# ABOUTME: Creates a test user and checks if email is queued and sent

import requests
import time
import json
from datetime import datetime

# API configuration
BASE_URL = "http://localhost:8000/api/v1"
ADMIN_EMAIL = "admin@sagarmatha.ai"
ADMIN_PASSWORD = "adadad123"

def get_auth_token():
    """Get authentication token"""
    response = requests.post(
        f"{BASE_URL}/auth/login",
        data={
            "username": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        }
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"Failed to login: {response.text}")
        return None

def create_test_user(token):
    """Create a new test user"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    test_email = f"test_user_{timestamp}@example.com"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    user_data = {
        "email": test_email,
        "password": "TestPass123!",
        "full_name": f"Test User {timestamp}",
        "role": "user",
        "is_active": True,
        "is_superuser": False
    }
    
    print(f"\n📧 Creating user with email: {test_email}")
    response = requests.post(
        f"{BASE_URL}/users/",
        headers=headers,
        json=user_data
    )
    
    if response.status_code == 200:
        user = response.json()
        print(f"✅ User created successfully!")
        print(f"   ID: {user['id']}")
        print(f"   Email: {user['email']}")
        return user
    else:
        print(f"❌ Failed to create user: {response.text}")
        return None

def check_email_queue(token):
    """Check if email is in the queue"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print("\n📬 Checking email queue...")
    response = requests.get(
        f"{BASE_URL}/email/queue",
        headers=headers
    )
    
    if response.status_code == 200:
        queue = response.json()
        if queue and len(queue) > 0:
            print(f"✅ Found {len(queue)} email(s) in queue")
            for email in queue[:3]:  # Show first 3
                print(f"   - To: {email.get('recipient_email')}")
                print(f"     Status: {email.get('status')}")
                print(f"     Subject: {email.get('subject')}")
            return True
        else:
            print("📭 Queue is empty")
            return False
    else:
        print(f"❌ Failed to check queue: {response.text}")
        return False

def check_email_history(token):
    """Check email history for sent emails"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print("\n📜 Checking email history...")
    response = requests.get(
        f"{BASE_URL}/email/history?limit=5",
        headers=headers
    )
    
    if response.status_code == 200:
        history = response.json()
        if history and len(history) > 0:
            print(f"✅ Found {len(history)} email(s) in history")
            for email in history[:3]:  # Show first 3
                print(f"   - To: {email.get('recipient_email')}")
                print(f"     Status: {email.get('status')}")
                print(f"     Sent: {email.get('sent_at')}")
            return True
        else:
            print("📭 No email history found")
            return False
    else:
        print(f"❌ Failed to check history: {response.text}")
        return False

def main():
    print("=" * 60)
    print("USER CREATION EMAIL TEST")
    print("=" * 60)
    
    # Get auth token
    print("\n🔐 Logging in as admin...")
    token = get_auth_token()
    if not token:
        print("❌ Failed to authenticate")
        return
    
    print("✅ Logged in successfully")
    
    # Create test user
    user = create_test_user(token)
    if not user:
        return
    
    # Check email queue immediately
    time.sleep(2)  # Give it a moment to queue
    check_email_queue(token)
    
    # Wait for Celery to process (runs every minute)
    print("\n⏳ Waiting 65 seconds for Celery to process queue...")
    print("   (Email queue is processed every minute)")
    time.sleep(65)
    
    # Check queue again (should be empty or processed)
    print("\n📬 Checking queue after processing...")
    check_email_queue(token)
    
    # Check email history
    check_email_history(token)
    
    print("\n" + "=" * 60)
    print("💡 Check Mailcatcher at http://localhost:1080")
    print("   to see if the email was received!")
    print("=" * 60)

if __name__ == "__main__":
    main()