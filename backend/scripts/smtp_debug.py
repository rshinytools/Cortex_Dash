# ABOUTME: Debug SMTP to see what's really happening
# ABOUTME: Use raw SMTP commands to trace the exact issue

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from sqlmodel import Session
from app.core.db import engine
from app.core.encryption import encryption_service
from app.models.email_settings import EmailSettings

def debug_smtp():
    """Debug SMTP connection and sending with detailed logging"""
    
    print("=" * 60)
    print("SMTP DEBUG - RAW CONNECTION TEST")
    print("=" * 60)
    
    # Get settings from database
    with Session(engine) as session:
        settings = session.query(EmailSettings).filter_by(is_active=True).first()
        if not settings:
            print("❌ No active email settings")
            return
        
        print(f"Settings loaded:")
        print(f"  Host: {settings.smtp_host}")
        print(f"  Port: {settings.smtp_port}")
        print(f"  Username: {settings.smtp_username}")
        print(f"  From: {settings.smtp_from_email}")
        print(f"  TLS: {settings.smtp_use_tls}")
        print(f"  SSL: {settings.smtp_use_ssl}")
        
        # Decrypt password
        password = None
        if settings.smtp_password:
            try:
                password = encryption_service.decrypt(settings.smtp_password)
                print(f"  Password: {'*' * len(password)} ({len(password)} chars)")
            except Exception as e:
                print(f"❌ Password decryption failed: {e}")
                return
    
    # Test raw SMTP
    print("\n" + "=" * 60)
    print("RAW SMTP TEST")
    print("=" * 60)
    
    try:
        print(f"\n1. Connecting to {settings.smtp_host}:{settings.smtp_port}")
        
        if settings.smtp_use_ssl:
            print("   Using SSL connection")
            context = ssl.create_default_context()
            server = smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, context=context)
        else:
            print("   Using regular connection")
            server = smtplib.SMTP(settings.smtp_host, settings.smtp_port)
            server.set_debuglevel(2)  # Maximum debug level
            
            if settings.smtp_use_tls:
                print("   Starting TLS")
                server.starttls()
        
        print("\n2. Authenticating")
        print(f"   Username: {settings.smtp_username}")
        login_result = server.login(settings.smtp_username, password)
        print(f"   Login result: {login_result}")
        
        print("\n3. Creating test message")
        message = MIMEMultipart()
        message["From"] = settings.smtp_from_email
        message["To"] = "amulyabista@gmail.com"
        message["Subject"] = "SMTP Debug Test - Raw Connection"
        
        body = "This is a debug test email sent using raw SMTP commands.\n\nIf you receive this, the SMTP connection is working correctly."
        message.attach(MIMEText(body, "plain"))
        
        print(f"   From: {message['From']}")
        print(f"   To: {message['To']}")
        print(f"   Subject: {message['Subject']}")
        
        print("\n4. Sending email")
        recipients = ["amulyabista@gmail.com"]
        send_result = server.send_message(message, from_addr=settings.smtp_from_email, to_addrs=recipients)
        print(f"   Send result: {send_result}")
        
        # Check for refused recipients
        if send_result:
            print("   ⚠️ Some recipients were refused:")
            for recipient, (code, msg) in send_result.items():
                print(f"      {recipient}: {code} - {msg}")
        else:
            print("   ✅ All recipients accepted")
        
        print("\n5. Getting server response")
        response = server.noop()
        print(f"   NOOP response: {response}")
        
        print("\n6. Closing connection")
        quit_result = server.quit()
        print(f"   Quit result: {quit_result}")
        
        print("\n" + "=" * 60)
        print("✅ SMTP TEST COMPLETED")
        print("Check your Gmail inbox for the debug test email")
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"\n❌ Authentication failed: {e}")
        print("   Check username and password")
    except smtplib.SMTPConnectError as e:
        print(f"\n❌ Connection failed: {e}")
        print("   Check host and port")
    except smtplib.SMTPServerDisconnected as e:
        print(f"\n❌ Server disconnected: {e}")
    except smtplib.SMTPException as e:
        print(f"\n❌ SMTP error: {e}")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_smtp()