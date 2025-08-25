# ABOUTME: Test script for verifying backup and restore system functionality
# ABOUTME: Creates a test backup and verifies all components are working

import asyncio
import sys
import os
from pathlib import Path
from uuid import UUID

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.backup.backup_service import backup_service
from app.services.backup.restore_service import restore_service
from app.models.user import User
from app.core.db import engine
from sqlmodel import Session, select


async def test_backup_system():
    """Test the backup system"""
    
    print("=" * 60)
    print("BACKUP SYSTEM TEST")
    print("=" * 60)
    
    # Get a superuser for testing
    with Session(engine) as session:
        stmt = select(User).where(User.is_superuser == True).limit(1)
        user = session.exec(stmt).first()
        
        if not user:
            print("❌ No superuser found. Please create a superuser first.")
            return False
        
        print(f"✅ Using superuser: {user.email}")
    
    # Test 1: Create a backup
    print("\n" + "=" * 60)
    print("TEST 1: CREATE BACKUP")
    print("=" * 60)
    
    try:
        print("Creating test backup...")
        backup_result = await backup_service.create_backup(
            user_id=user.id,
            description="Test backup from test script",
            backup_type="full"
        )
        
        if backup_result["success"]:
            print(f"✅ Backup created successfully!")
            print(f"   - Filename: {backup_result['filename']}")
            print(f"   - Size: {backup_result['size_mb']} MB")
            print(f"   - Checksum: {backup_result['checksum'][:16]}...")
            print(f"   - Backup ID: {backup_result['backup_id']}")
            backup_id = backup_result["backup_id"]
        else:
            print("❌ Backup creation failed")
            return False
            
    except Exception as e:
        print(f"❌ Backup creation error: {str(e)}")
        return False
    
    # Test 2: List backups
    print("\n" + "=" * 60)
    print("TEST 2: LIST BACKUPS")
    print("=" * 60)
    
    try:
        backups = await backup_service.list_backups(limit=5)
        print(f"✅ Found {len(backups)} backup(s):")
        for backup in backups[:3]:  # Show first 3
            print(f"   - {backup['filename']} ({backup['size_mb']} MB)")
    except Exception as e:
        print(f"❌ List backups error: {str(e)}")
        return False
    
    # Test 3: Verify checksum
    print("\n" + "=" * 60)
    print("TEST 3: VERIFY BACKUP INTEGRITY")
    print("=" * 60)
    
    try:
        is_valid = await backup_service.verify_checksum(UUID(backup_id))
        if is_valid:
            print("✅ Backup checksum verified - file integrity confirmed")
        else:
            print("❌ Backup checksum mismatch - file may be corrupted")
            return False
    except Exception as e:
        print(f"❌ Checksum verification error: {str(e)}")
        return False
    
    # Test 4: Check backup file exists
    print("\n" + "=" * 60)
    print("TEST 4: CHECK BACKUP FILE")
    print("=" * 60)
    
    backup_dir = Path("/data/backups")
    backup_file = backup_dir / backup_result["filename"]
    
    if backup_file.exists():
        file_size_mb = backup_file.stat().st_size / (1024 * 1024)
        print(f"✅ Backup file exists: {backup_file}")
        print(f"   - Actual size: {file_size_mb:.2f} MB")
    else:
        print(f"❌ Backup file not found: {backup_file}")
        return False
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print("✅ All backup tests passed successfully!")
    print("\nNext steps:")
    print("1. Check /data/backups/ directory for the backup file")
    print("2. Test the restore functionality (requires caution)")
    print("3. Check email notifications (if SMTP is configured)")
    print("4. Access the backup via API endpoints")
    
    return True


async def test_restore_system():
    """Test the restore system (USE WITH CAUTION)"""
    
    print("\n" + "=" * 60)
    print("⚠️  RESTORE SYSTEM TEST - USE WITH CAUTION")
    print("=" * 60)
    print("\nThis test will:")
    print("1. Create a safety backup")
    print("2. Attempt to restore from the latest backup")
    print("3. This may affect your current data")
    
    response = input("\nDo you want to continue? (yes/no): ")
    if response.lower() != "yes":
        print("Restore test cancelled.")
        return False
    
    # Get a superuser for testing
    with Session(engine) as session:
        stmt = select(User).where(User.is_superuser == True).limit(1)
        user = session.exec(stmt).first()
        
        if not user:
            print("❌ No superuser found.")
            return False
    
    # Get the latest backup
    backups = await backup_service.list_backups(limit=1)
    if not backups:
        print("❌ No backups available for restore test")
        return False
    
    latest_backup = backups[0]
    backup_id = UUID(latest_backup["id"])
    
    print(f"\n📦 Will restore from: {latest_backup['filename']}")
    print(f"   Created: {latest_backup['created_at']}")
    print(f"   Size: {latest_backup['size_mb']} MB")
    
    try:
        print("\n🔄 Starting restore process...")
        restore_result = await restore_service.restore_backup(
            backup_id=backup_id,
            user_id=user.id,
            create_safety_backup=True
        )
        
        if restore_result["success"]:
            print("✅ Restore completed successfully!")
            print(f"   - Safety backup: {restore_result.get('safety_backup_id', 'N/A')}")
            print(f"   - Restored at: {restore_result['restored_at']}")
        else:
            print("❌ Restore failed")
            return False
            
    except Exception as e:
        print(f"❌ Restore error: {str(e)}")
        return False
    
    return True


def main():
    """Main test function"""
    
    print("\nClinical Dashboard Backup System Test")
    print("=====================================\n")
    
    # Run backup tests
    success = asyncio.run(test_backup_system())
    
    if success:
        print("\n" + "=" * 60)
        print("✅ BACKUP SYSTEM IS OPERATIONAL")
        print("=" * 60)
        
        # Optionally test restore
        print("\nWould you like to test the restore system?")
        print("⚠️  WARNING: This will restore data from a backup")
        response = input("Test restore? (yes/no): ")
        
        if response.lower() == "yes":
            asyncio.run(test_restore_system())
    else:
        print("\n" + "=" * 60)
        print("❌ BACKUP SYSTEM TEST FAILED")
        print("=" * 60)
        print("\nPlease check:")
        print("1. Database connection")
        print("2. /data/backups directory exists and is writable")
        print("3. PostgreSQL client tools (pg_dump) are installed")
        print("4. Error messages above for specific issues")


if __name__ == "__main__":
    main()