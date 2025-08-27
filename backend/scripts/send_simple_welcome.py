# ABOUTME: Send a simple plain text welcome email to avoid spam filters
# ABOUTME: Test if complex HTML is causing delivery issues

import asyncio
from app.services.email.email_service import email_service

async def send_simple_welcome():
    """Send simple welcome email"""
    
    print("Sending simple welcome email...")
    
    try:
        result = await email_service.send_email(
            to_email="amulyabista@yahoo.com",
            subject="Your Clinical Dashboard Account",
            html_content="<p>Hi Amulya,</p><p>Your Clinical Dashboard account is ready.</p><p>Email: amulyabista@yahoo.com<br>Password: Welcome123!</p><p>Login at http://localhost:3000</p>",
            plain_content="Hi Amulya,\n\nYour Clinical Dashboard account is ready.\n\nEmail: amulyabista@yahoo.com\nPassword: Welcome123!\n\nLogin at http://localhost:3000"
        )
        
        if result["success"]:
            print(f"✅ Simple email sent! Check Yahoo inbox.")
        else:
            print(f"❌ Failed to send")
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(send_simple_welcome())