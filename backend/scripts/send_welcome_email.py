# ABOUTME: Send a welcome email directly to test delivery
# ABOUTME: Uses the exact same template as user creation

import asyncio
from app.services.email.email_service import email_service
from datetime import datetime

async def send_welcome_email():
    """Send welcome email to Yahoo address"""
    
    print("=" * 60)
    print("SENDING WELCOME EMAIL DIRECTLY")
    print("=" * 60)
    
    # Email variables for the template
    email_variables = {
        "user_name": "Amulya Bista",
        "user_email": "amulyabista@yahoo.com",
        "temp_password": "Welcome123!",
        "user_role": "admin",
        "organization": "Sagarmatha AI",
        "created_by": "System Administrator",
        "login_url": "http://localhost:3000/login"
    }
    
    print("\n📧 Sending welcome email to: amulyabista@yahoo.com")
    print("   Using template: user_created")
    
    try:
        # First try to queue it like the system does
        queue_id = await email_service.queue_email(
            to_email="amulyabista@yahoo.com",
            template_key="user_created",
            variables=email_variables,
            priority=1
        )
        
        if queue_id:
            print(f"✅ Email queued with ID: {queue_id}")
            
            # Now process the queue immediately
            print("\n⚙️ Processing queue...")
            result = await email_service.process_queue()
            print(f"   Processed: {result}")
            
            if result['sent'] > 0:
                print("\n✅ Welcome email sent successfully!")
            else:
                print("\n⚠️ Email queued but not sent in this batch")
        else:
            print("❌ Failed to queue email")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    # Also try sending a direct email without template
    print("\n" + "=" * 60)
    print("SENDING DIRECT HTML EMAIL")
    print("=" * 60)
    
    try:
        result = await email_service.send_email(
            to_email="amulyabista@yahoo.com",
            subject="Welcome to Clinical Dashboard - Direct Test",
            html_content="""
            <html>
            <head>
                <style>
                    body { font-family: Arial, sans-serif; }
                    .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                    .header { background-color: #1e40af; color: white; padding: 20px; border-radius: 8px; }
                    .content { background-color: #f3f4f6; padding: 20px; margin-top: 20px; border-radius: 8px; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Welcome to Clinical Dashboard!</h1>
                    </div>
                    <div class="content">
                        <p>Dear Amulya Bista,</p>
                        <p>Your account has been successfully created.</p>
                        <h3>Your Login Details:</h3>
                        <ul>
                            <li><strong>Email:</strong> amulyabista@yahoo.com</li>
                            <li><strong>Password:</strong> Welcome123!</li>
                            <li><strong>Role:</strong> Admin</li>
                        </ul>
                        <p>Please login at: <a href="http://localhost:3000/login">http://localhost:3000/login</a></p>
                        <p>For security, please change your password after first login.</p>
                        <hr>
                        <p><small>This is a direct test email to verify delivery.</small></p>
                    </div>
                </div>
            </body>
            </html>
            """
        )
        
        if result["success"]:
            print(f"✅ Direct email sent successfully!")
            print(f"   Message ID: {result.get('message_id')}")
        else:
            print(f"❌ Failed to send direct email")
            
    except Exception as e:
        print(f"❌ Error sending direct email: {str(e)}")

if __name__ == "__main__":
    asyncio.run(send_welcome_email())