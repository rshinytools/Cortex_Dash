# ABOUTME: Set SMTP password directly with hardcoded value
# ABOUTME: Temporary script to fix password storage issue

from sqlmodel import Session, select
from app.core.db import engine
from app.core.encryption import encryption_service
from app.models.email_settings import EmailSettings
import sys

def set_password(password):
    """Set SMTP password directly"""
    
    print("=" * 60)
    print("SETTING SMTP PASSWORD")
    print("=" * 60)
    
    if not password:
        print("❌ Password cannot be empty")
        return
    
    print(f"Password length: {len(password)} characters")
    
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
        print(f"  Current password stored: {bool(settings.smtp_password)}")
        
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
                print("✅ Verification successful - password matches")
                print(f"  Decrypted: {'*' * len(decrypted)}")
            else:
                print("❌ Verification failed - decrypted password doesn't match")
                
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            session.rollback()

if __name__ == "__main__":
    # Get password from command line or use a default
    if len(sys.argv) > 1:
        password = sys.argv[1]
    else:
        # You need to provide the actual password here
        print("Usage: python set_password_direct.py <password>")
        print("Please provide the SMTP password as an argument")
        sys.exit(1)
    
    set_password(password)