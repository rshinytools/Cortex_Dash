# ABOUTME: Check if password is properly stored and decrypted
# ABOUTME: Direct database check to verify encryption/decryption

from sqlmodel import Session, select
from app.core.db import engine
from app.core.encryption import encryption_service
from app.models.email_settings import EmailSettings

def check_password():
    """Check password storage and decryption"""
    
    print("=" * 60)
    print("PASSWORD CHECK")
    print("=" * 60)
    
    with Session(engine) as session:
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
        print(f"  Password encrypted: {settings.smtp_password[:50]}..." if settings.smtp_password else "None")
        print(f"  Password length: {len(settings.smtp_password) if settings.smtp_password else 0}")
        
        if settings.smtp_password:
            try:
                decrypted = encryption_service.decrypt(settings.smtp_password)
                print(f"\n✅ Password decrypted successfully")
                print(f"  Length: {len(decrypted) if decrypted else 0} chars")
                print(f"  Value: {'*' * len(decrypted) if decrypted else 'None'}")
                
                # Check if it's actually None string
                if decrypted == "None" or decrypted is None or decrypted == "":
                    print("\n⚠️ WARNING: Password is empty or 'None'")
                    print("  Please re-enter the password in the Email Settings")
                else:
                    print(f"\n✅ Password looks valid")
                    
            except Exception as e:
                print(f"\n❌ Decryption failed: {e}")
                
        else:
            print("\n❌ No password stored in database")

if __name__ == "__main__":
    check_password()