# ABOUTME: Verify password is stored and send a test email
# ABOUTME: Complete check after user re-enters password

from sqlmodel import Session, select
from app.core.db import engine
from app.core.encryption import encryption_service
from app.models.email_settings import EmailSettings
from app.services.email.email_service import email_service
import asyncio

async def verify_and_send():
    """Verify password and send test email"""
    
    print("=" * 60)
    print("VERIFY PASSWORD AND SEND TEST")
    print("=" * 60)
    
    with Session(engine) as session:
        # Check password
        settings = session.exec(
            select(EmailSettings).where(EmailSettings.is_active == True)
        ).first()
        
        if not settings:
            print("❌ No active email settings")
            return
        
        print(f"Settings found:")
        print(f"  Host: {settings.smtp_host}")
        print(f"  Port: {settings.smtp_port}")
        print(f"  Username: {settings.smtp_username}")
        print(f"  From: {settings.smtp_from_email}")
        
        if settings.smtp_password:
            try:
                decrypted = encryption_service.decrypt(settings.smtp_password)
                print(f"\n✅ Password stored and decrypted")
                print(f"  Length: {len(decrypted)} chars")
                
                if decrypted and decrypted != "None":
                    print("✅ Password looks valid")
                    
                    # Test SMTP connection
                    print("\n" + "=" * 60)
                    print("TESTING SMTP CONNECTION")
                    print("=" * 60)
                    
                    test_result = await email_service.test_smtp_connection()
                    if test_result["success"]:
                        print("✅ SMTP connection successful")
                        
                        # Send test email
                        print("\n" + "=" * 60)
                        print("SENDING TEST EMAIL")
                        print("=" * 60)
                        
                        result = await email_service.send_test_email("amulyabista@gmail.com")
                        if result["success"]:
                            print("✅ Test email sent successfully!")
                            print(f"  Message ID: {result.get('message_id')}")
                            print(f"  Duration: {result.get('duration_ms')}ms")
                            print("\n📧 Check your Gmail inbox for the test email")
                        else:
                            print(f"❌ Failed to send: {result.get('error')}")
                    else:
                        print(f"❌ SMTP connection failed: {test_result.get('error')}")
                else:
                    print("❌ Password is empty or invalid")
                    print("Please re-enter the password in Email Settings")
            except Exception as e:
                print(f"❌ Error: {e}")
        else:
            print("\n❌ No password stored")
            print("Please enter the password in Email Settings")

if __name__ == "__main__":
    asyncio.run(verify_and_send())