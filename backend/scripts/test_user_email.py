# ABOUTME: Test script to verify user creation sends email
# ABOUTME: Run this in the backend container to test email integration

import asyncio
from sqlmodel import Session
from app.core.db import engine
from app.models.user import User, UserCreate
from app.crud.user import create_user
from app.services.email.email_service import email_service
from datetime import datetime
import uuid

async def test_user_creation_email():
    """Test that creating a user queues an email"""
    
    print("=" * 60)
    print("TESTING USER CREATION EMAIL")
    print("=" * 60)
    
    with Session(engine) as session:
        # Get the admin user as creator
        admin_user = session.query(User).filter_by(email="admin@sagarmatha.ai").first()
        if not admin_user:
            print("❌ Admin user not found")
            return
        
        # Create a test user
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        test_email = f"test_user_{timestamp}@example.com"
        
        print(f"\n📧 Creating user: {test_email}")
        
        user_create = UserCreate(
            email=test_email,
            password="TestPass123!",
            full_name=f"Test User {timestamp}",
            role="user",
            is_active=True,
            is_superuser=False
        )
        
        # Create the user
        new_user = create_user(session=session, user_create=user_create)
        print(f"✅ User created with ID: {new_user.id}")
        
        # Now queue the email using the new system
        print("\n📬 Queueing email notification...")
        
        email_variables = {
            "user_name": new_user.full_name or new_user.email,
            "user_email": new_user.email,
            "temp_password": "TestPass123!",  # In real scenario, use the actual password
            "user_role": new_user.role,
            "organization": "Test Organization",
            "created_by": admin_user.full_name or admin_user.email,
            "login_url": "http://localhost:3000/login"
        }
        
        try:
            queue_id = await email_service.queue_email(
                to_email=new_user.email,
                template_key="user_created",
                variables=email_variables,
                user_id=admin_user.id,
                priority=1
            )
            
            if queue_id:
                print(f"✅ Email queued successfully with ID: {queue_id}")
                print("\n💡 Email will be processed by Celery within 1 minute")
                print("   Check http://localhost:1080 to see the email")
            else:
                print("❌ Failed to queue email")
                
        except Exception as e:
            print(f"❌ Error queueing email: {str(e)}")
        
        # Test direct sending (optional)
        print("\n📨 Testing direct email send...")
        try:
            result = await email_service.send_test_email(test_email)
            if result["success"]:
                print(f"✅ Test email sent successfully!")
            else:
                print(f"❌ Failed to send test email: {result.get('error')}")
        except Exception as e:
            print(f"❌ Error sending test email: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_user_creation_email())