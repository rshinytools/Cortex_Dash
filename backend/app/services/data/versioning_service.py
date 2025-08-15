# ABOUTME: File versioning service for managing data versions and lineage
# ABOUTME: Tracks changes, enables rollback, and maintains data history

from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path
import shutil
import hashlib
import json
from sqlmodel import Session, select
from fastapi import HTTPException

from app.models.data_source_upload import DataSourceUpload, UploadStatus
from app.core.logging import logger

class VersioningService:
    """Service for managing data versions"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_version_history(self, study_id: str) -> List[Dict[str, Any]]:
        """Get version history for a study"""
        
        stmt = select(DataSourceUpload).where(
            DataSourceUpload.study_id == study_id
        ).order_by(DataSourceUpload.version_number.desc())
        
        uploads = self.db.exec(stmt).all()
        
        history = []
        for upload in uploads:
            history.append({
                "id": str(upload.id),
                "version": upload.version_number,
                "upload_name": upload.upload_name,
                "description": upload.description,
                "uploaded_at": upload.upload_timestamp.isoformat(),
                "uploaded_by": str(upload.created_by),
                "status": upload.status,
                "is_active": upload.is_active_version,
                "file_count": len(upload.files_extracted) if upload.files_extracted else 0,
                "total_rows": upload.total_rows,
                "file_size_mb": upload.file_size_mb
            })
        
        return history
    
    def set_active_version(self, study_id: str, version_number: int) -> bool:
        """Set a specific version as active"""
        
        # Deactivate all versions
        stmt = select(DataSourceUpload).where(
            DataSourceUpload.study_id == study_id
        )
        uploads = self.db.exec(stmt).all()
        
        target_found = False
        for upload in uploads:
            if upload.version_number == version_number:
                upload.is_active_version = True
                target_found = True
            else:
                upload.is_active_version = False
            self.db.add(upload)
        
        if not target_found:
            raise HTTPException(
                status_code=404,
                detail=f"Version {version_number} not found for study"
            )
        
        self.db.commit()
        return True
    
    def create_version_tag(
        self,
        study_id: str,
        version_number: int,
        tag: str,
        user_id: str
    ) -> DataSourceUpload:
        """Create a tag for a specific version"""
        
        stmt = select(DataSourceUpload).where(
            DataSourceUpload.study_id == study_id,
            DataSourceUpload.version_number == version_number
        )
        
        upload = self.db.exec(stmt).first()
        
        if not upload:
            raise HTTPException(
                status_code=404,
                detail=f"Version {version_number} not found"
            )
        
        # Store tag in metadata
        if not upload.upload_metadata:
            upload.upload_metadata = {}
        
        if "tags" not in upload.upload_metadata:
            upload.upload_metadata["tags"] = []
        
        upload.upload_metadata["tags"].append({
            "tag": tag,
            "created_by": user_id,
            "created_at": datetime.utcnow().isoformat()
        })
        
        self.db.add(upload)
        self.db.commit()
        self.db.refresh(upload)
        
        return upload
    
    def compare_versions(
        self,
        study_id: str,
        version1: int,
        version2: int
    ) -> Dict[str, Any]:
        """Compare two versions of data"""
        
        stmt1 = select(DataSourceUpload).where(
            DataSourceUpload.study_id == study_id,
            DataSourceUpload.version_number == version1
        )
        
        stmt2 = select(DataSourceUpload).where(
            DataSourceUpload.study_id == study_id,
            DataSourceUpload.version_number == version2
        )
        
        upload1 = self.db.exec(stmt1).first()
        upload2 = self.db.exec(stmt2).first()
        
        if not upload1 or not upload2:
            raise HTTPException(
                status_code=404,
                detail="One or both versions not found"
            )
        
        comparison = {
            "version1": {
                "number": version1,
                "uploaded_at": upload1.upload_timestamp.isoformat(),
                "file_count": len(upload1.files_extracted) if upload1.files_extracted else 0,
                "total_rows": upload1.total_rows,
                "datasets": self._extract_dataset_info(upload1)
            },
            "version2": {
                "number": version2,
                "uploaded_at": upload2.upload_timestamp.isoformat(),
                "file_count": len(upload2.files_extracted) if upload2.files_extracted else 0,
                "total_rows": upload2.total_rows,
                "datasets": self._extract_dataset_info(upload2)
            },
            "differences": self._calculate_differences(upload1, upload2)
        }
        
        return comparison
    
    def _extract_dataset_info(self, upload: DataSourceUpload) -> List[Dict[str, Any]]:
        """Extract dataset information from upload"""
        
        if not upload.files_extracted:
            return []
        
        datasets = []
        for file_info in upload.files_extracted:
            datasets.append({
                "name": file_info.get("dataset_name", ""),
                "rows": file_info.get("row_count", 0),
                "columns": file_info.get("column_count", 0),
                "columns_list": [col["name"] for col in file_info.get("columns", [])]
            })
        
        return datasets
    
    def _calculate_differences(
        self,
        upload1: DataSourceUpload,
        upload2: DataSourceUpload
    ) -> Dict[str, Any]:
        """Calculate differences between two uploads"""
        
        datasets1 = {d["dataset_name"]: d for d in (upload1.files_extracted or [])}
        datasets2 = {d["dataset_name"]: d for d in (upload2.files_extracted or [])}
        
        differences = {
            "added_datasets": list(set(datasets2.keys()) - set(datasets1.keys())),
            "removed_datasets": list(set(datasets1.keys()) - set(datasets2.keys())),
            "modified_datasets": [],
            "row_changes": {},
            "column_changes": {}
        }
        
        # Check for modified datasets
        for dataset_name in set(datasets1.keys()) & set(datasets2.keys()):
            d1 = datasets1[dataset_name]
            d2 = datasets2[dataset_name]
            
            if d1["row_count"] != d2["row_count"] or d1["column_count"] != d2["column_count"]:
                differences["modified_datasets"].append(dataset_name)
                
                differences["row_changes"][dataset_name] = {
                    "before": d1["row_count"],
                    "after": d2["row_count"],
                    "change": d2["row_count"] - d1["row_count"]
                }
                
                cols1 = set(col["name"] for col in d1.get("columns", []))
                cols2 = set(col["name"] for col in d2.get("columns", []))
                
                differences["column_changes"][dataset_name] = {
                    "added": list(cols2 - cols1),
                    "removed": list(cols1 - cols2)
                }
        
        return differences
    
    def create_version_checkpoint(
        self,
        study_id: str,
        version_number: int,
        checkpoint_name: str,
        description: str,
        user_id: str
    ) -> Dict[str, Any]:
        """Create a checkpoint for a version"""
        
        stmt = select(DataSourceUpload).where(
            DataSourceUpload.study_id == study_id,
            DataSourceUpload.version_number == version_number
        )
        
        upload = self.db.exec(stmt).first()
        
        if not upload:
            raise HTTPException(
                status_code=404,
                detail=f"Version {version_number} not found"
            )
        
        checkpoint = {
            "id": str(upload.id),
            "name": checkpoint_name,
            "description": description,
            "version": version_number,
            "created_by": user_id,
            "created_at": datetime.utcnow().isoformat(),
            "metadata": {
                "file_count": len(upload.files_extracted) if upload.files_extracted else 0,
                "total_rows": upload.total_rows,
                "datasets": [f["dataset_name"] for f in (upload.files_extracted or [])]
            }
        }
        
        # Store checkpoint in metadata
        if not upload.upload_metadata:
            upload.upload_metadata = {}
        
        if "checkpoints" not in upload.upload_metadata:
            upload.upload_metadata["checkpoints"] = []
        
        upload.upload_metadata["checkpoints"].append(checkpoint)
        
        self.db.add(upload)
        self.db.commit()
        
        return checkpoint
    
    def rollback_to_version(
        self,
        study_id: str,
        target_version: int,
        user_id: str
    ) -> DataSourceUpload:
        """Rollback to a specific version"""
        
        # Get target version
        stmt = select(DataSourceUpload).where(
            DataSourceUpload.study_id == study_id,
            DataSourceUpload.version_number == target_version
        )
        
        target_upload = self.db.exec(stmt).first()
        
        if not target_upload:
            raise HTTPException(
                status_code=404,
                detail=f"Version {target_version} not found"
            )
        
        # Create a new version as a copy of the target
        new_version = self._get_next_version(study_id)
        
        new_upload = DataSourceUpload(
            study_id=study_id,
            upload_name=f"Rollback to v{target_version}",
            description=f"Rollback from current to version {target_version}",
            original_filename=target_upload.original_filename,
            file_format=target_upload.file_format,
            file_size_mb=target_upload.file_size_mb,
            raw_path=target_upload.raw_path,
            processed_path=target_upload.processed_path,
            status=UploadStatus.COMPLETED,
            version_number=new_version,
            is_active_version=True,
            files_extracted=target_upload.files_extracted,
            total_rows=target_upload.total_rows,
            total_columns=target_upload.total_columns,
            created_by=user_id,
            upload_timestamp=datetime.utcnow(),
            upload_metadata={
                "rollback_from_version": target_version,
                "rollback_by": user_id,
                "rollback_at": datetime.utcnow().isoformat()
            }
        )
        
        # Deactivate all other versions
        stmt = select(DataSourceUpload).where(
            DataSourceUpload.study_id == study_id
        )
        uploads = self.db.exec(stmt).all()
        
        for upload in uploads:
            upload.is_active_version = False
            self.db.add(upload)
        
        self.db.add(new_upload)
        self.db.commit()
        self.db.refresh(new_upload)
        
        return new_upload
    
    def _get_next_version(self, study_id: str) -> int:
        """Get next version number"""
        
        stmt = select(DataSourceUpload).where(
            DataSourceUpload.study_id == study_id
        ).order_by(DataSourceUpload.version_number.desc())
        
        latest = self.db.exec(stmt).first()
        
        if latest:
            return latest.version_number + 1
        return 1