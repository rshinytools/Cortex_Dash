# ABOUTME: Manually set SMTP password in database
# ABOUTME: Direct database update to ensure password is properly stored

import getpass
from sqlmodel import Session, select
from app.core.db import engine
from app.core.encryption import encryption_service
from app.models.email_settings import EmailSettings

def set_password():
    """Manually set SMTP password"""
    
    print("=" * 60)
    print("SET SMTP PASSWORD")
    print("=" * 60)
    
    # Get password from user
    password = getpass.getpass("Enter SMTP password for admin@sagarmatha.ai: ")
    
    if not password:
        print("❌ Password cannot be empty")
        return
    
    print(f"\nPassword received: {len(password)} characters")
    
    with Session(engine) as session:
        # Get active settings
        settings = session.exec(
            select(EmailSettings).where(EmailSettings.is_active == True)
        ).first()
        
        if not settings:
            print("❌ No active email settings found")
            return
        
        print(f"\nCurrent settings:")
        print(f"  Host: {settings.smtp_host}")
        print(f"  Port: {settings.smtp_port}")
        print(f"  Username: {settings.smtp_username}")
        
        # Encrypt and store password
        try:
            encrypted = encryption_service.encrypt(password)
            settings.smtp_password = encrypted
            
            print(f"\n✅ Password encrypted successfully")
            print(f"  Encrypted length: {len(encrypted)}")
            
            # Save to database
            session.add(settings)
            session.commit()
            
            print("✅ Password saved to database")
            
            # Verify by decrypting
            decrypted = encryption_service.decrypt(encrypted)
            if decrypted == password:
                print("✅ Verification successful - password can be decrypted")
            else:
                print("❌ Verification failed - decrypted password doesn't match")
                
        except Exception as e:
            print(f"\n❌ Error: {e}")
            session.rollback()

if __name__ == "__main__":
    set_password()