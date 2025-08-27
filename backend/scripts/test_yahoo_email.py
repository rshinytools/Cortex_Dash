# ABOUTME: Test script to send email directly to Yahoo address
# ABOUTME: Diagnose why emails aren't reaching Yahoo inbox

import asyncio
from app.services.email.email_service import email_service
from sqlmodel import Session
from app.core.db import engine
from app.models.email_settings import EmailSettings

async def test_yahoo_email():
    """Test sending email to Yahoo address"""
    
    print("=" * 60)
    print("TESTING EMAIL TO YAHOO")
    print("=" * 60)
    
    # Check current SMTP settings
    with Session(engine) as session:
        settings = session.query(EmailSettings).filter_by(is_active=True).first()
        if settings:
            print(f"✅ SMTP Settings found:")
            print(f"   Host: {settings.smtp_host}")
            print(f"   Port: {settings.smtp_port}")
            print(f"   From: {settings.smtp_from_email}")
            print(f"   Username: {settings.smtp_username}")
            print(f"   TLS: {settings.smtp_use_tls}")
            print(f"   Password stored: {'Yes' if settings.smtp_password else 'No'}")
        else:
            print("❌ No active SMTP settings found")
            return
    
    # Test connection first
    print("\n🔌 Testing SMTP connection...")
    conn_result = await email_service.test_smtp_connection()
    print(f"   Result: {conn_result}")
    
    if not conn_result.get("success"):
        print(f"❌ SMTP connection failed: {conn_result.get('error')}")
        print("\nPossible issues:")
        print("1. SMTP password not set correctly")
        print("2. Wrong SMTP settings")
        print("3. Firewall blocking connection")
        return
    
    # Send test email
    yahoo_email = "amulyabista@yahoo.com"
    print(f"\n📧 Sending test email to: {yahoo_email}")
    
    try:
        result = await email_service.send_email(
            to_email=yahoo_email,
            subject="Test Email from Clinical Dashboard",
            html_content="""
            <html>
            <body>
                <h2>Test Email Successful!</h2>
                <p>This is a test email from your Clinical Dashboard system.</p>
                <p>If you're reading this, your email system is working correctly!</p>
                <p>Sent via: GoDaddy SMTP (sagarmatha.ai)</p>
            </body>
            </html>
            """
        )
        
        if result["success"]:
            print(f"✅ Email sent successfully!")
            print(f"   Message ID: {result.get('message_id')}")
            print(f"   Duration: {result.get('duration_ms')}ms")
            print(f"\n💡 Check your Yahoo inbox (and spam folder)!")
        else:
            print(f"❌ Failed to send email")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("\nThis might mean:")
        print("1. SMTP credentials are incorrect")
        print("2. GoDaddy is blocking the recipient")
        print("3. Yahoo is rejecting emails from your domain")

if __name__ == "__main__":
    asyncio.run(test_yahoo_email())