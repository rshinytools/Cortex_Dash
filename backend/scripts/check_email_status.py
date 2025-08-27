# ABOUTME: Check email queue and history for recent emails
# ABOUTME: Verify welcome emails were sent to test users

from sqlmodel import Session, select
from app.core.db import engine
from app.models.email_settings import EmailQueue, EmailHistory, EmailStatus
from datetime import datetime, timedelta

def check_email_status():
    """Check status of recent emails"""
    
    print("=" * 60)
    print("EMAIL STATUS CHECK")
    print("=" * 60)
    
    with Session(engine) as session:
        # Check recent email queue
        print("\n📬 EMAIL QUEUE (last hour):")
        print("-" * 40)
        
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        queue_statement = select(EmailQueue).where(
            EmailQueue.created_at >= one_hour_ago
        ).order_by(EmailQueue.created_at.desc())
        
        queue_items = session.exec(queue_statement).all()
        
        if queue_items:
            for item in queue_items:
                print(f"\nID: {item.id}")
                print(f"  To: {item.recipient_email}")
                print(f"  Subject: {item.subject}")
                print(f"  Status: {item.status.value}")
                print(f"  Created: {item.created_at}")
                if item.sent_at:
                    print(f"  Sent: {item.sent_at}")
        else:
            print("No emails in queue from last hour")
        
        # Check email history
        print("\n\n📧 EMAIL HISTORY (last hour):")
        print("-" * 40)
        
        history_statement = select(EmailHistory).where(
            EmailHistory.created_at >= one_hour_ago
        ).order_by(EmailHistory.created_at.desc())
        
        history_items = session.exec(history_statement).all()
        
        if history_items:
            for item in history_items:
                print(f"\nID: {item.id}")
                print(f"  To: {item.recipient_email}")
                print(f"  Subject: {item.subject}")
                print(f"  Status: {item.status}")
                if item.sent_at:
                    print(f"  Sent: {item.sent_at}")
                    print(f"  Duration: {item.send_duration_ms}ms")
                if item.provider_response:
                    print(f"  Response: {item.provider_response}")
        else:
            print("No emails in history from last hour")
        
        # Summary
        print("\n\n📊 SUMMARY:")
        print("-" * 40)
        
        # Count queued emails
        pending_count = session.exec(
            select(EmailQueue).where(EmailQueue.status == EmailStatus.PENDING)
        ).all()
        sent_count = session.exec(
            select(EmailQueue).where(
                EmailQueue.status == EmailStatus.SENT,
                EmailQueue.created_at >= one_hour_ago
            )
        ).all()
        
        print(f"Pending emails: {len(pending_count)}")
        print(f"Sent in last hour: {len(sent_count)}")
        
        # Check for test users
        test_emails = ["amulyabista@yahoo.com", "amulyabista@gmail.com"]
        for email in test_emails:
            queue_check = session.exec(
                select(EmailQueue).where(
                    EmailQueue.recipient_email == email,
                    EmailQueue.created_at >= one_hour_ago
                )
            ).first()
            
            if queue_check:
                print(f"\n✅ {email}: Queued ({queue_check.status.value})")
                if queue_check.sent_at:
                    print(f"   Sent at: {queue_check.sent_at}")
            else:
                print(f"\n❌ {email}: Not found in queue")

if __name__ == "__main__":
    check_email_status()