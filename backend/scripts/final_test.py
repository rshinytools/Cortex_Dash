# ABOUTME: Final test to send welcome email with proper Celery processing
# ABOUTME: Queue and immediately process to ensure delivery

import asyncio
from app.services.email.email_service import email_service
from datetime import datetime

async def send_final_test():
    print("=" * 60)
    print("FINAL WELCOME EMAIL TEST")
    print("=" * 60)
    
    # Queue the welcome email
    queue_id = await email_service.queue_email(
        to_email="amulyabista@yahoo.com",
        template_key="user_created",
        variables={
            "user_name": "Amulya Bista",
            "user_email": "amulyabista@yahoo.com",
            "temp_password": "Welcome123!",
            "user_role": "admin",
            "organization": "Sagarmatha AI",
            "created_by": "System Administrator",
            "login_url": "http://localhost:3000/login"
        },
        priority=1
    )
    
    print(f"✅ Email queued: {queue_id}")
    
    # Process immediately
    print("\n⚙️ Processing queue now...")
    result = await email_service.process_queue()
    print(f"Result: {result}")
    
    if result['sent'] > 0:
        print("\n✅ Welcome email processed and sent!")
        print("Check your Yahoo inbox now!")
    else:
        print(f"\n❌ Email not sent: {result}")

if __name__ == "__main__":
    asyncio.run(send_final_test())