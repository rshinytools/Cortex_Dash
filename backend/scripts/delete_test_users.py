# ABOUTME: Delete test user accounts for email testing
# ABOUTME: Remove Yahoo and Gmail test accounts to recreate them

from sqlmodel import Session, select, delete
from app.core.db import engine
from app.models.user import User
from app.models.activity_log import ActivityLog

def delete_test_users():
    """Delete test user accounts"""
    
    print("=" * 60)
    print("DELETING TEST USERS")
    print("=" * 60)
    
    test_emails = ["amulyabista@yahoo.com", "amulyabista@gmail.com"]
    
    with Session(engine) as session:
        for email in test_emails:
            # Find user
            statement = select(User).where(User.email == email)
            user = session.exec(statement).first()
            
            if user:
                print(f"\nDeleting user: {email}")
                print(f"  ID: {user.id}")
                print(f"  Name: {user.full_name}")
                
                # Delete related activity logs first
                delete_logs = delete(ActivityLog).where(ActivityLog.user_id == user.id)
                session.exec(delete_logs)
                
                # Delete user
                session.delete(user)
                session.commit()
                
                print(f"✅ User {email} deleted")
            else:
                print(f"⚠️ User {email} not found")
    
    print("\n✅ Test users deleted successfully")

if __name__ == "__main__":
    delete_test_users()