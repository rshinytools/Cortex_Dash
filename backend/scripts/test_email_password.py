# ABOUTME: Test script to verify email password is being saved and encrypted properly
# ABOUTME: Also tests real SMTP connection with GoDaddy settings

import asyncio
from sqlmodel import Session, select
from app.core.db import engine
from app.models.email_settings import EmailSettings
from app.core.encryption import encryption_service
from app.services.email.email_service import email_service
import smtplib
from datetime import datetime

async def test_email_password():
    """Test that email password is saved, encrypted, and works with SMTP"""
    
    print("=" * 60)
    print("EMAIL PASSWORD AND SMTP CONNECTION TEST")
    print("=" * 60)
    
    with Session(engine) as session:
        # Get the active email settings
        statement = select(EmailSettings).where(EmailSettings.is_active == True)
        settings = session.exec(statement).first()
        
        if not settings:
            print("❌ No active email settings found")
            print("Please configure email settings at http://localhost:3000/admin/email")
            return
        
        print(f"✅ Found active email settings")
        print(f"   Host: {settings.smtp_host}")
        print(f"   Port: {settings.smtp_port}")
        print(f"   From: {settings.smtp_from_email}")
        print(f"   Username: {settings.smtp_username}")
        
        # Check if password is stored
        if not settings.smtp_password:
            print("❌ No password stored in database")
            print("   Please add password in email settings")
            return
        
        print(f"✅ Password is stored (encrypted length: {len(settings.smtp_password)} chars)")
        
        # Try to decrypt the password
        try:
            decrypted_password = encryption_service.decrypt(settings.smtp_password)
            if not decrypted_password:
                print("❌ Password decryption returned empty string")
                return
            print(f"✅ Password successfully decrypted (length: {len(decrypted_password)} chars)")
            # Don't print the actual password for security
            print(f"   First char: '{decrypted_password[0]}', Last char: '{decrypted_password[-1]}'")
        except Exception as e:
            print(f"❌ Failed to decrypt password: {str(e)}")
            return
        
        print("\n" + "=" * 60)
        print("TESTING SMTP CONNECTION")
        print("=" * 60)
        
        # Test SMTP connection with the decrypted password
        try:
            print(f"Connecting to {settings.smtp_host}:{settings.smtp_port}...")
            
            if settings.smtp_use_ssl:
                server = smtplib.SMTP_SSL(
                    settings.smtp_host, 
                    settings.smtp_port,
                    timeout=settings.smtp_timeout or 30
                )
                print("✅ SSL connection established")
            else:
                server = smtplib.SMTP(
                    settings.smtp_host,
                    settings.smtp_port,
                    timeout=settings.smtp_timeout or 30
                )
                print("✅ Connection established")
                
                if settings.smtp_use_tls:
                    server.starttls()
                    print("✅ TLS encryption enabled")
            
            # Try to authenticate
            if settings.smtp_username and decrypted_password:
                print(f"Authenticating as {settings.smtp_username}...")
                server.login(settings.smtp_username, decrypted_password)
                print("✅ Authentication successful!")
            
            # Get server capabilities
            if hasattr(server, 'esmtp_features'):
                print("\nServer capabilities:")
                for feature in server.esmtp_features:
                    print(f"  - {feature}")
            
            server.quit()
            print("\n✅ SMTP connection test SUCCESSFUL")
            print("Your email settings are properly configured!")
            
        except smtplib.SMTPAuthenticationError as e:
            print(f"❌ Authentication failed: {str(e)}")
            print("\nPossible issues:")
            print("  1. Incorrect username or password")
            print("  2. Account locked or 2FA enabled")
            print("  3. App-specific password may be required")
            
        except smtplib.SMTPConnectError as e:
            print(f"❌ Connection failed: {str(e)}")
            print("\nPossible issues:")
            print("  1. Incorrect host or port")
            print("  2. Firewall blocking connection")
            print("  3. Server requires different security settings")
            
        except Exception as e:
            print(f"❌ SMTP test failed: {str(e)}")
            print("\nPlease check your email settings")
    
    print("\n" + "=" * 60)
    print("TESTING EMAIL SERVICE")
    print("=" * 60)
    
    # Test the email service's test connection method
    try:
        result = await email_service.test_smtp_connection()
        if result["success"]:
            print("✅ Email service connection test passed")
            print(f"   {result['message']}")
        else:
            print("❌ Email service connection test failed")
            print(f"   Error: {result['error']}")
    except Exception as e:
        print(f"❌ Email service test failed: {str(e)}")
    
    print("\n" + "=" * 60)
    print("SENDING TEST EMAIL")
    print("=" * 60)
    
    # If connection is successful, try sending a test email
    if result.get("success"):
        test_email = input("Enter email address to send test to (or press Enter to skip): ")
        if test_email and "@" in test_email:
            try:
                print(f"Sending test email to {test_email}...")
                email_result = await email_service.send_test_email(test_email)
                if email_result["success"]:
                    print("✅ Test email sent successfully!")
                    print(f"   Message ID: {email_result.get('message_id')}")
                    print(f"   Duration: {email_result.get('duration_ms')}ms")
                    print(f"\n✨ Check your email inbox for the test message!")
                else:
                    print("❌ Failed to send test email")
                    print(f"   Error: {email_result.get('error')}")
            except Exception as e:
                print(f"❌ Error sending test email: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_email_password())