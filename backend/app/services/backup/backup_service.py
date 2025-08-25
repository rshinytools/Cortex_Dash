# ABOUTME: Main backup service that orchestrates database and file backups into a single ZIP file
# ABOUTME: Handles backup creation, compression, checksum calculation, and metadata management

import os
import zipfile
import hashlib
import subprocess
import shutil
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from uuid import UUID
import tempfile

from sqlmodel import Session, select
from sqlalchemy.dialects import postgresql

from app.core.db import engine
from app.core.config import settings
from app.models.user import User
from app.services.backup.email_service import backup_email_service


class BackupService:
    """Service for creating and managing system backups"""
    
    def __init__(self):
        self.backup_dir = Path("/data/backups")
        self.studies_dir = Path("/data/studies")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
    async def create_backup(
        self,
        user_id: UUID,
        description: Optional[str] = None,
        backup_type: str = "full"
    ) -> Dict[str, Any]:
        """
        Create a complete backup of the system
        
        Args:
            user_id: ID of the user creating the backup
            description: Optional description of the backup
            backup_type: Type of backup (full, database, files)
            
        Returns:
            Dictionary with backup details
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{timestamp}.zip"
        backup_path = self.backup_dir / backup_name
        
        # Create temporary directory for staging
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            try:
                # Step 1: Create database dump if needed
                if backup_type in ["full", "database"]:
                    print(f"Creating database dump...")
                    db_dump_path = temp_path / "database.sql"
                    await self._create_database_dump(db_dump_path)
                
                # Step 2: Copy files if needed
                if backup_type in ["full", "files"]:
                    print(f"Copying study files...")
                    if self.studies_dir.exists():
                        studies_backup_path = temp_path / "studies"
                        shutil.copytree(self.studies_dir, studies_backup_path)
                
                # Step 3: Create metadata file
                metadata = {
                    "backup_type": backup_type,
                    "created_at": datetime.utcnow().isoformat(),
                    "created_by": str(user_id),
                    "description": description,
                    "version": "1.0",
                    "system_info": {
                        "platform": "Clinical Dashboard",
                        "api_version": "v1"
                    }
                }
                
                metadata_path = temp_path / "metadata.json"
                with open(metadata_path, 'w') as f:
                    json.dump(metadata, f, indent=2)
                
                # Step 4: Create ZIP file with compression
                print(f"Creating ZIP archive: {backup_name}")
                with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zipf:
                    for root, dirs, files in os.walk(temp_path):
                        for file in files:
                            file_path = Path(root) / file
                            arc_name = file_path.relative_to(temp_path)
                            zipf.write(file_path, arc_name)
                
                # Step 5: Calculate checksum
                print(f"Calculating checksum...")
                checksum = await self._calculate_checksum(backup_path)
                
                # Step 6: Get file size
                file_size = backup_path.stat().st_size
                size_mb = round(file_size / (1024 * 1024), 2)
                
                # Step 7: Save backup record to database
                backup_record = await self._save_backup_record(
                    filename=backup_name,
                    size_mb=size_mb,
                    checksum=checksum,
                    description=description,
                    user_id=user_id,
                    metadata=metadata
                )
                
                print(f"Backup created successfully: {backup_name}")
                
                result = {
                    "success": True,
                    "backup_id": str(backup_record["id"]),
                    "filename": backup_name,
                    "size_mb": size_mb,
                    "checksum": checksum,
                    "created_at": backup_record["created_at"]
                }
                
                # Send success email notification
                try:
                    await backup_email_service.send_backup_success_email(
                        user_id=str(user_id),
                        backup_details=result
                    )
                except Exception as email_error:
                    print(f"Failed to send email notification: {str(email_error)}")
                
                return result
                
            except Exception as e:
                # Clean up on failure
                if backup_path.exists():
                    backup_path.unlink()
                
                print(f"Backup failed: {str(e)}")
                
                # Send failure email notification
                try:
                    await backup_email_service.send_backup_failure_email(
                        user_id=str(user_id),
                        error_details={
                            "error": str(e),
                            "backup_type": backup_type,
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    )
                except Exception as email_error:
                    print(f"Failed to send email notification: {str(email_error)}")
                
                raise Exception(f"Backup creation failed: {str(e)}")
    
    async def _create_database_dump(self, output_path: Path) -> None:
        """Create PostgreSQL database dump"""
        db_host = settings.POSTGRES_SERVER
        db_name = settings.POSTGRES_DB
        db_user = settings.POSTGRES_USER
        db_password = settings.POSTGRES_PASSWORD
        
        # Build pg_dump command
        env = os.environ.copy()
        env['PGPASSWORD'] = db_password
        
        cmd = [
            'pg_dump',
            '-h', db_host,
            '-U', db_user,
            '-d', db_name,
            '-f', str(output_path),
            '--verbose',
            '--no-owner',
            '--no-acl'
        ]
        
        # Execute pg_dump
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            raise Exception(f"Database dump failed: {result.stderr}")
    
    async def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA-256 checksum of a file"""
        sha256_hash = hashlib.sha256()
        
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        
        return sha256_hash.hexdigest()
    
    async def _save_backup_record(
        self,
        filename: str,
        size_mb: float,
        checksum: str,
        description: Optional[str],
        user_id: UUID,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Save backup record to database"""
        with Session(engine) as session:
            # Get user details for audit
            user = session.get(User, user_id)
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            # Create backup record using raw SQL to avoid model dependencies
            query = """
                INSERT INTO backups (
                    filename, size_mb, checksum, description,
                    created_by, created_by_name, created_by_email, metadata
                )
                VALUES (
                    :filename, :size_mb, :checksum, :description,
                    :created_by, :created_by_name, :created_by_email, :metadata
                )
                RETURNING id, created_at
            """
            
            result = session.execute(
                query,
                {
                    "filename": filename,
                    "size_mb": size_mb,
                    "checksum": checksum,
                    "description": description,
                    "created_by": user_id,
                    "created_by_name": user.full_name,
                    "created_by_email": user.email,
                    "metadata": json.dumps(metadata)
                }
            )
            
            row = result.fetchone()
            session.commit()
            
            return {
                "id": row[0],
                "created_at": row[1].isoformat()
            }
    
    async def list_backups(self, limit: int = 50) -> list:
        """List all backups"""
        with Session(engine) as session:
            query = """
                SELECT 
                    id, filename, size_mb, checksum, description,
                    created_by, created_by_name, created_by_email,
                    created_at, metadata
                FROM backups
                ORDER BY created_at DESC
                LIMIT :limit
            """
            
            result = session.execute(query, {"limit": limit})
            
            backups = []
            for row in result:
                backups.append({
                    "id": str(row[0]),
                    "filename": row[1],
                    "size_mb": row[2],
                    "checksum": row[3],
                    "description": row[4],
                    "created_by": str(row[5]),
                    "created_by_name": row[6],
                    "created_by_email": row[7],
                    "created_at": row[8].isoformat(),
                    "metadata": row[9]
                })
            
            return backups
    
    async def get_backup(self, backup_id: UUID) -> Optional[Dict[str, Any]]:
        """Get backup details by ID"""
        with Session(engine) as session:
            query = """
                SELECT 
                    id, filename, size_mb, checksum, description,
                    created_by, created_by_name, created_by_email,
                    created_at, metadata
                FROM backups
                WHERE id = :backup_id
            """
            
            result = session.execute(query, {"backup_id": backup_id})
            row = result.fetchone()
            
            if not row:
                return None
            
            return {
                "id": str(row[0]),
                "filename": row[1],
                "size_mb": row[2],
                "checksum": row[3],
                "description": row[4],
                "created_by": str(row[5]),
                "created_by_name": row[6],
                "created_by_email": row[7],
                "created_at": row[8].isoformat(),
                "metadata": row[9]
            }
    
    async def verify_checksum(self, backup_id: UUID) -> bool:
        """Verify backup file integrity"""
        backup = await self.get_backup(backup_id)
        if not backup:
            raise ValueError(f"Backup {backup_id} not found")
        
        backup_path = self.backup_dir / backup["filename"]
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup file {backup['filename']} not found")
        
        calculated_checksum = await self._calculate_checksum(backup_path)
        return calculated_checksum == backup["checksum"]


# Singleton instance
backup_service = BackupService()