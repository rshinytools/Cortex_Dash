# ABOUTME: Restore service that handles system restoration from backup files with safety mechanisms
# ABOUTME: Includes checksum verification, automatic safety backup, and rollback capabilities

import os
import zipfile
import subprocess
import shutil
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from uuid import UUID
import tempfile

from sqlmodel import Session
from app.core.db import engine
from app.core.config import settings
from app.services.backup.backup_service import backup_service
from app.services.backup.email_service import backup_email_service


class RestoreService:
    """Service for restoring system from backups"""
    
    def __init__(self):
        self.backup_dir = Path("/data/backups")
        self.studies_dir = Path("/data/studies")
        
    async def restore_backup(
        self,
        backup_id: UUID,
        user_id: UUID,
        create_safety_backup: bool = True
    ) -> Dict[str, Any]:
        """
        Restore system from a backup
        
        Args:
            backup_id: ID of the backup to restore
            user_id: ID of the user performing the restore
            create_safety_backup: Whether to create a safety backup before restore
            
        Returns:
            Dictionary with restore details
        """
        # Step 1: Get backup details
        backup = await backup_service.get_backup(backup_id)
        if not backup:
            raise ValueError(f"Backup {backup_id} not found")
        
        backup_path = self.backup_dir / backup["filename"]
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup file {backup['filename']} not found")
        
        # Step 2: Verify checksum
        print(f"Verifying backup integrity...")
        if not await backup_service.verify_checksum(backup_id):
            raise Exception("Backup checksum verification failed - file may be corrupted")
        
        # Step 3: Create safety backup if requested
        safety_backup_id = None
        if create_safety_backup:
            print(f"Creating safety backup before restore...")
            try:
                safety_result = await backup_service.create_backup(
                    user_id=user_id,
                    description=f"Safety backup before restoring {backup['filename']}",
                    backup_type="full"
                )
                safety_backup_id = safety_result["backup_id"]
                print(f"Safety backup created: {safety_result['filename']}")
            except Exception as e:
                print(f"Warning: Safety backup failed: {str(e)}")
                # Continue with restore anyway if safety backup fails
        
        # Step 4: Extract backup to temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            try:
                print(f"Extracting backup file...")
                with zipfile.ZipFile(backup_path, 'r') as zipf:
                    zipf.extractall(temp_path)
                
                # Step 5: Verify backup structure
                metadata_path = temp_path / "metadata.json"
                if not metadata_path.exists():
                    raise Exception("Invalid backup: metadata.json not found")
                
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                
                backup_type = metadata.get("backup_type", "full")
                
                # Step 6: Restore database if included
                if backup_type in ["full", "database"]:
                    db_dump_path = temp_path / "database.sql"
                    if db_dump_path.exists():
                        print(f"Restoring database...")
                        await self._restore_database(db_dump_path)
                    else:
                        print(f"Warning: Database dump not found in backup")
                
                # Step 7: Restore files if included
                if backup_type in ["full", "files"]:
                    studies_backup_path = temp_path / "studies"
                    if studies_backup_path.exists():
                        print(f"Restoring study files...")
                        await self._restore_files(studies_backup_path, self.studies_dir)
                    else:
                        print(f"Warning: Study files not found in backup")
                
                # Step 8: Save restore record
                restore_record = await self._save_restore_record(
                    backup_id=backup_id,
                    user_id=user_id,
                    safety_backup_id=safety_backup_id,
                    status="completed"
                )
                
                print(f"Restore completed successfully from {backup['filename']}")
                
                result = {
                    "success": True,
                    "backup_id": str(backup_id),
                    "backup_filename": backup["filename"],
                    "safety_backup_id": safety_backup_id,
                    "restored_at": restore_record["completed_at"]
                }
                
                # Send success email notification
                try:
                    await backup_email_service.send_restore_success_email(
                        user_id=str(user_id),
                        restore_details=result
                    )
                except Exception as email_error:
                    print(f"Failed to send email notification: {str(email_error)}")
                
                return result
                
            except Exception as e:
                print(f"Restore failed: {str(e)}")
                
                # Attempt rollback if safety backup was created
                if safety_backup_id:
                    print(f"Attempting rollback to safety backup...")
                    try:
                        await self.restore_backup(
                            backup_id=UUID(safety_backup_id),
                            user_id=user_id,
                            create_safety_backup=False  # Don't create another safety backup
                        )
                        print(f"Rollback successful")
                    except Exception as rollback_error:
                        print(f"Rollback failed: {str(rollback_error)}")
                
                # Save failed restore record
                await self._save_restore_record(
                    backup_id=backup_id,
                    user_id=user_id,
                    safety_backup_id=safety_backup_id,
                    status="failed",
                    error_message=str(e)
                )
                
                # Send failure email notification
                try:
                    await backup_email_service.send_restore_failure_email(
                        user_id=str(user_id),
                        error_details={
                            "error": str(e),
                            "backup_filename": backup["filename"],
                            "safety_backup_id": safety_backup_id,
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    )
                except Exception as email_error:
                    print(f"Failed to send email notification: {str(email_error)}")
                
                raise Exception(f"Restore failed: {str(e)}")
    
    async def _restore_database(self, dump_path: Path) -> None:
        """Restore PostgreSQL database from dump"""
        db_host = settings.POSTGRES_SERVER
        db_name = settings.POSTGRES_DB
        db_user = settings.POSTGRES_USER
        db_password = settings.POSTGRES_PASSWORD
        
        # Build psql command
        env = os.environ.copy()
        env['PGPASSWORD'] = db_password
        
        # First, drop and recreate the database (be very careful!)
        # Note: In production, you might want to rename the old database instead
        print(f"Preparing database for restore...")
        
        # Connect to postgres database to drop and recreate target database
        drop_create_cmds = f"""
        DROP DATABASE IF EXISTS {db_name}_old;
        ALTER DATABASE {db_name} RENAME TO {db_name}_old;
        CREATE DATABASE {db_name};
        """
        
        # Execute database preparation
        cmd_prep = [
            'psql',
            '-h', db_host,
            '-U', db_user,
            '-d', 'postgres',  # Connect to postgres database
            '-c', drop_create_cmds
        ]
        
        result_prep = subprocess.run(
            cmd_prep,
            env=env,
            capture_output=True,
            text=True
        )
        
        if result_prep.returncode != 0:
            # Try to restore without dropping (less destructive)
            print(f"Warning: Could not prepare database, attempting direct restore...")
        
        # Restore the dump
        cmd_restore = [
            'psql',
            '-h', db_host,
            '-U', db_user,
            '-d', db_name,
            '-f', str(dump_path),
            '--single-transaction'  # All or nothing
        ]
        
        result_restore = subprocess.run(
            cmd_restore,
            env=env,
            capture_output=True,
            text=True
        )
        
        if result_restore.returncode != 0:
            raise Exception(f"Database restore failed: {result_restore.stderr}")
        
        # Clean up old database if it exists
        try:
            cmd_cleanup = [
                'psql',
                '-h', db_host,
                '-U', db_user,
                '-d', 'postgres',
                '-c', f'DROP DATABASE IF EXISTS {db_name}_old;'
            ]
            subprocess.run(cmd_cleanup, env=env, capture_output=True)
        except:
            pass  # Cleanup is optional
    
    async def _restore_files(self, source_dir: Path, target_dir: Path) -> None:
        """Restore files from backup to target directory"""
        # Backup existing files first (rename directory)
        if target_dir.exists():
            backup_dir = target_dir.parent / f"{target_dir.name}_old"
            if backup_dir.exists():
                shutil.rmtree(backup_dir)
            target_dir.rename(backup_dir)
        
        # Copy files from backup
        try:
            shutil.copytree(source_dir, target_dir)
            
            # Remove old backup directory if restore was successful
            backup_dir = target_dir.parent / f"{target_dir.name}_old"
            if backup_dir.exists():
                shutil.rmtree(backup_dir)
        except Exception as e:
            # Try to restore old files on failure
            backup_dir = target_dir.parent / f"{target_dir.name}_old"
            if backup_dir.exists():
                if target_dir.exists():
                    shutil.rmtree(target_dir)
                backup_dir.rename(target_dir)
            raise e
    
    async def _save_restore_record(
        self,
        backup_id: UUID,
        user_id: UUID,
        safety_backup_id: Optional[str],
        status: str,
        error_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """Save restore operation record"""
        # For now, we'll just log this
        # In a full implementation, you'd save to a restore_operations table
        completed_at = datetime.utcnow()
        
        print(f"Restore operation: backup_id={backup_id}, user_id={user_id}, "
              f"status={status}, safety_backup_id={safety_backup_id}")
        
        if error_message:
            print(f"Error: {error_message}")
        
        return {
            "completed_at": completed_at.isoformat()
        }
    
    async def create_safety_backup(self, user_id: UUID) -> Dict[str, Any]:
        """
        Create a quick safety backup before any risky operation
        
        Args:
            user_id: ID of the user requesting the safety backup
            
        Returns:
            Dictionary with backup details
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        description = f"Safety backup created at {timestamp}"
        
        result = await backup_service.create_backup(
            user_id=user_id,
            description=description,
            backup_type="full"
        )
        
        # Rename the file to indicate it's a safety backup
        if result["success"]:
            old_path = self.backup_dir / result["filename"]
            new_filename = f"safety_{result['filename']}"
            new_path = self.backup_dir / new_filename
            
            if old_path.exists():
                old_path.rename(new_path)
                result["filename"] = new_filename
        
        return result


# Singleton instance
restore_service = RestoreService()