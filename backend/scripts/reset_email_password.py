# ABOUTME: Reset email password to allow re-encryption with new key
# ABOUTME: Run this after changing ENCRYPTION_KEY to clear old encrypted passwords

from sqlmodel import Session, select
from app.core.db import engine
from app.models.email_settings import EmailSettings

def reset_email_passwords():
    """Clear encrypted passwords from email settings"""
    
    with Session(engine) as session:
        statement = select(EmailSettings).where(EmailSettings.is_active == True)
        settings = session.exec(statement).first()
        
        if settings:
            print(f"Found email settings for: {settings.smtp_host}")
            if settings.smtp_password:
                settings.smtp_password = None
                session.add(settings)
                session.commit()
                print("✅ Password cleared. Please re-enter password in UI.")
            else:
                print("No password was set.")
        else:
            print("No active email settings found.")

if __name__ == "__main__":
    reset_email_passwords()