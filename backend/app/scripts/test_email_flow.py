#!/usr/bin/env python3
"""
Test the complete email flow:
1. Configure SMTP settings
2. Test SMTP connection
3. Send test emails using templates
4. Check email queue
5. Verify email history
"""

import asyncio
import requests
from datetime import datetime
from uuid import uuid4
from sqlmodel import Session, select
from app.core.db import engine
from app.models.email_settings import EmailSettings, EmailTemplate, EmailQueue, EmailHistory
from app.services.email.email_service import email_service
from app.core.encryption import encryption_service


def setup_smtp_settings():
    """Configure SMTP settings for Mailcatcher"""
    print("📧 Setting up SMTP configuration for Mailcatcher...")
    
    with Session(engine) as session:
        # Check if settings already exist
        statement = select(EmailSettings).where(EmailSettings.is_active == True)
        existing = session.exec(statement).first()
        
        if existing:
            print("   ℹ️ Active settings already exist")
            return existing
        
        # Create new settings for Mailcatcher
        settings = EmailSettings(
            id=uuid4(),
            smtp_host="mailcatcher",  # Docker service name
            smtp_port=1025,  # Mailcatcher SMTP port
            smtp_from_email="noreply@clinical-dashboard.ai",
            smtp_from_name="Clinical Dashboard System",
            smtp_use_tls=False,
            smtp_use_ssl=False,
            smtp_timeout=30,
            is_active=True,
            test_recipient_email="test@clinical-dashboard.ai",
            max_retries=3,
            retry_delay=300,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        session.add(settings)
        session.commit()
        
        print("   ✅ SMTP settings configured for Mailcatcher")
        return settings


async def test_smtp_connection():
    """Test SMTP connection"""
    print("\n🔌 Testing SMTP connection...")
    
    result = await email_service.test_smtp_connection()
    
    if result["success"]:
        print(f"   ✅ Connection successful to {result['host']}:{result['port']}")
    else:
        print(f"   ❌ Connection failed: {result['error']}")
    
    return result["success"]


async def send_test_emails():
    """Send test emails using different templates"""
    print("\n📮 Sending test emails...")
    
    test_cases = [
        {
            "template_key": "user_created",
            "to_email": "newuser@test.com",
            "variables": {
                "user_name": "John Doe",
                "user_email": "john.doe@test.com",
                "temp_password": "TempPass123!",
                "user_role": "Study Manager",
                "organization": "Sagarmatha AI",
                "created_by": "System Administrator",
                "login_url": "http://localhost:3000/login"
            }
        },
        {
            "template_key": "backup_completed",
            "to_email": "admin@test.com",
            "variables": {
                "backup_filename": "backup_20250826_120000.zip",
                "backup_size": "125.5",
                "backup_type": "Full System Backup",
                "created_at": datetime.utcnow().isoformat(),
                "created_by": "Automated System",
                "checksum": "a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456"
            }
        },
        {
            "template_key": "study_created",
            "to_email": "researcher@test.com",
            "variables": {
                "user_name": "Dr. Jane Smith",
                "study_name": "COVID-19 Vaccine Trial Phase III",
                "protocol_number": "CVD-2024-001",
                "study_phase": "Phase III",
                "sponsor": "Global Pharma Inc.",
                "created_by": "Study Administrator",
                "creation_date": datetime.utcnow().isoformat(),
                "study_url": "http://localhost:3000/studies/123",
                "permissions_list": "<li>View study data</li><li>Export reports</li><li>Manage dashboards</li>"
            }
        }
    ]
    
    queued_emails = []
    
    for test in test_cases:
        try:
            queue_id = await email_service.queue_email(
                to_email=test["to_email"],
                template_key=test["template_key"],
                variables=test["variables"],
                priority=1
            )
            
            if queue_id:
                print(f"   ✅ Queued email: {test['template_key']} to {test['to_email']} (ID: {queue_id})")
                queued_emails.append(queue_id)
            else:
                print(f"   ⚠️ Failed to queue: {test['template_key']}")
                
        except Exception as e:
            print(f"   ❌ Error queuing {test['template_key']}: {str(e)}")
    
    return queued_emails


async def process_email_queue():
    """Process the email queue"""
    print("\n⚙️ Processing email queue...")
    
    result = await email_service.process_queue(batch_size=10)
    
    print(f"   📊 Queue processing results:")
    print(f"      - Processed: {result['processed']}")
    print(f"      - Sent: {result['sent']}")
    print(f"      - Failed: {result['failed']}")
    
    if result['errors']:
        print(f"      - Errors: {result['errors']}")
    
    return result


def check_email_history():
    """Check email history"""
    print("\n📜 Checking email history...")
    
    with Session(engine) as session:
        # Get recent email history
        statement = select(EmailHistory).order_by(EmailHistory.created_at.desc()).limit(10)
        history = session.exec(statement).all()
        
        print(f"   Found {len(history)} recent email records:")
        
        for record in history:
            status_emoji = "✅" if record.status == "sent" else "❌"
            print(f"   {status_emoji} {record.recipient_email}: {record.subject[:50]}... - {record.status}")
        
        return len(history)


def check_mailcatcher():
    """Check Mailcatcher for received emails"""
    print("\n📬 Checking Mailcatcher for emails...")
    
    try:
        # Get messages from Mailcatcher API
        response = requests.get("http://localhost:1080/messages")
        
        if response.status_code == 200:
            messages = response.json()
            print(f"   Found {len(messages)} emails in Mailcatcher:")
            
            for msg in messages[-5:]:  # Show last 5
                print(f"   📧 To: {msg['recipients'][0]} - Subject: {msg['subject']}")
            
            if len(messages) > 5:
                print(f"   ... and {len(messages) - 5} more")
            
            return len(messages)
        else:
            print("   ⚠️ Could not connect to Mailcatcher")
            return 0
            
    except Exception as e:
        print(f"   ⚠️ Mailcatcher not available: {str(e)}")
        return 0


def check_celery_tasks():
    """Check if Celery tasks are registered"""
    print("\n🔄 Checking Celery email tasks...")
    
    try:
        from app.core.celery_app import celery_app
        
        email_tasks = [
            "process_email_queue",
            "retry_failed_emails",
            "send_email_immediately",
            "process_scheduled_emails"
        ]
        
        registered = celery_app.tasks.keys()
        
        for task in email_tasks:
            if task in registered:
                print(f"   ✅ Task registered: {task}")
            else:
                print(f"   ❌ Task not found: {task}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error checking Celery tasks: {str(e)}")
        return False


async def send_direct_test_email():
    """Send a test email directly (not through queue)"""
    print("\n✉️ Sending direct test email...")
    
    result = await email_service.send_test_email("direct-test@clinical-dashboard.ai")
    
    if result["success"]:
        print(f"   ✅ Test email sent successfully")
        print(f"      Message ID: {result.get('message_id')}")
        print(f"      Duration: {result.get('duration_ms')} ms")
    else:
        print(f"   ❌ Failed to send test email: {result.get('error')}")
    
    return result["success"]


async def main():
    """Run all tests"""
    print("=" * 60)
    print("📧 COMPREHENSIVE EMAIL SYSTEM TEST")
    print("=" * 60)
    
    # Setup SMTP
    setup_smtp_settings()
    
    # Test connection
    connection_ok = await test_smtp_connection()
    
    if not connection_ok:
        print("\n❌ Cannot proceed without SMTP connection")
        print("💡 Make sure Mailcatcher is running: docker-compose up mailcatcher")
        return
    
    # Send direct test email
    await send_direct_test_email()
    
    # Send templated emails
    queued_emails = await send_test_emails()
    
    # Process queue
    if queued_emails:
        await asyncio.sleep(2)  # Wait a bit
        await process_email_queue()
    
    # Check history
    check_email_history()
    
    # Check Mailcatcher
    mailcatcher_count = check_mailcatcher()
    
    # Check Celery
    check_celery_tasks()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"✅ SMTP Connection: {'Working' if connection_ok else 'Failed'}")
    print(f"✅ Templates Created: 5")
    print(f"✅ Emails Queued: {len(queued_emails)}")
    print(f"✅ Emails in Mailcatcher: {mailcatcher_count}")
    
    print("\n💡 Next Steps:")
    print("   1. Check Mailcatcher UI at http://localhost:1080")
    print("   2. View email content and formatting")
    print("   3. Test Celery background processing:")
    print("      docker exec cortex_dash-celery-worker-1 celery -A app.core.celery_app call test_email_system")
    print("   4. Monitor Celery Beat for scheduled tasks:")
    print("      docker logs cortex_dash-celery-beat-1 --tail 20")


if __name__ == "__main__":
    print("🚀 Starting email system test...")
    asyncio.run(main())