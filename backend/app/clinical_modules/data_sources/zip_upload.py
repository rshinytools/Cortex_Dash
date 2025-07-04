# ABOUTME: ZIP file upload connector for manual data uploads
# ABOUTME: Handles ZIP file validation, extraction, and processing

import zipfile
import shutil
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
import hashlib
import json

from .base import DataSourceConnector


class ZipUploadConnector(DataSourceConnector):
    """Connector for manual ZIP file uploads"""
    
    def get_required_config_fields(self) -> List[str]:
        return [
            "allowed_extensions",
            "max_file_size_mb",
            "scan_for_viruses",
            "validate_structure"
        ]
    
    async def test_connection(self) -> Tuple[bool, Optional[str]]:
        """Test connection - for ZIP uploads this validates configuration"""
        valid, error = await self.validate_config()
        
        if valid:
            # Check if upload directory exists and is writable
            upload_path = Path(self.study.folder_path) / "raw" / "uploads"
            try:
                upload_path.mkdir(parents=True, exist_ok=True)
                test_file = upload_path / ".test_write"
                test_file.touch()
                test_file.unlink()
                
                self.log_activity("test_connection", {"status": "success"})
                return True, None
            except Exception as e:
                error = f"Upload directory not writable: {str(e)}"
                self.log_activity("test_connection", {"status": "failed"}, False, error)
                return False, error
        else:
            return False, error
    
    async def list_available_data(self) -> List[Dict[str, Any]]:
        """List uploaded ZIP files"""
        uploads = []
        upload_path = Path(self.study.folder_path) / "raw" / "uploads"
        
        try:
            if upload_path.exists():
                for zip_dir in upload_path.iterdir():
                    if zip_dir.is_dir():
                        # Look for metadata file
                        metadata_file = zip_dir / "metadata.json"
                        if metadata_file.exists():
                            with open(metadata_file, "r") as f:
                                metadata = json.load(f)
                                uploads.append(metadata)
                        else:
                            # Create basic metadata from directory
                            uploads.append({
                                "id": zip_dir.name,
                                "name": zip_dir.name,
                                "type": "zip_upload",
                                "format": "mixed",
                                "upload_date": datetime.fromtimestamp(
                                    zip_dir.stat().st_mtime
                                ).isoformat(),
                                "size": sum(
                                    f.stat().st_size for f in zip_dir.rglob("*") if f.is_file()
                                ),
                                "file_count": len(list(zip_dir.rglob("*")))
                            })
            
            self.log_activity("list_data", {"count": len(uploads)})
            
        except Exception as e:
            self.logger.error(f"Error listing uploads: {str(e)}")
            self.log_activity("list_data", {"error": str(e)}, False, str(e))
            
        return uploads
    
    async def download_data(
        self,
        dataset_id: str,
        target_path: Path,
        progress_callback: Optional[callable] = None
    ) -> Tuple[bool, Optional[str]]:
        """For ZIP uploads, this processes an uploaded file"""
        # ZIP uploads are already in the study folder, so we don't download
        # Instead, we might copy or process them
        upload_path = Path(self.study.folder_path) / "raw" / "uploads" / dataset_id
        
        if not upload_path.exists():
            return False, f"Upload not found: {dataset_id}"
        
        try:
            # Copy to target path if different
            if upload_path != target_path:
                shutil.copytree(upload_path, target_path, dirs_exist_ok=True)
            
            self.log_activity(
                "process_upload",
                {
                    "dataset_id": dataset_id,
                    "source_path": str(upload_path),
                    "target_path": str(target_path)
                }
            )
            
            return True, None
            
        except Exception as e:
            error = f"Processing error: {str(e)}"
            self.log_activity("process_upload", {"dataset_id": dataset_id}, False, error)
            return False, error
    
    async def get_metadata(self, dataset_id: str) -> Dict[str, Any]:
        """Get metadata for uploaded ZIP"""
        upload_path = Path(self.study.folder_path) / "raw" / "uploads" / dataset_id
        metadata_file = upload_path / "metadata.json"
        
        if metadata_file.exists():
            with open(metadata_file, "r") as f:
                return json.load(f)
        
        return {"dataset_id": dataset_id, "error": "Metadata not found"}
    
    async def process_zip_upload(
        self,
        zip_file_path: Path,
        upload_name: str,
        user_metadata: Optional[Dict[str, Any]] = None,
        progress_callback: Optional[callable] = None
    ) -> Tuple[bool, Optional[str]]:
        """Process a new ZIP file upload"""
        try:
            self.update_sync_status("processing")
            
            # Validate file
            if not await self._validate_zip_file(zip_file_path):
                error = "Invalid ZIP file"
                self.update_sync_status("failed", error)
                return False, error
            
            # Create upload directory
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            upload_id = f"{upload_name}_{timestamp}"
            upload_path = Path(self.study.folder_path) / "raw" / "uploads" / upload_id
            upload_path.mkdir(parents=True, exist_ok=True)
            
            # Extract ZIP file
            if progress_callback:
                progress_callback(10, "Extracting ZIP file")
            
            with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
                total_files = len(zip_ref.namelist())
                
                for i, file_info in enumerate(zip_ref.infolist()):
                    # Security check - prevent path traversal
                    if ".." in file_info.filename or file_info.filename.startswith("/"):
                        continue
                    
                    # Check allowed extensions
                    allowed_exts = self.config.get("allowed_extensions", [".sas7bdat", ".csv", ".xpt", ".txt"])
                    if not any(file_info.filename.lower().endswith(ext) for ext in allowed_exts):
                        continue
                    
                    zip_ref.extract(file_info, upload_path)
                    
                    if progress_callback:
                        progress = 10 + (80 * (i + 1) / total_files)
                        progress_callback(progress, f"Extracting: {file_info.filename}")
            
            # Create metadata
            metadata = {
                "id": upload_id,
                "name": upload_name,
                "type": "zip_upload",
                "format": "mixed",
                "upload_date": datetime.utcnow().isoformat(),
                "original_file": zip_file_path.name,
                "file_hash": await self._calculate_file_hash(zip_file_path),
                "size": zip_file_path.stat().st_size,
                "extracted_files": self._inventory_files(upload_path),
                "user_metadata": user_metadata or {},
                "processing_status": "completed"
            }
            
            # Save metadata
            with open(upload_path / "metadata.json", "w") as f:
                json.dump(metadata, f, indent=2)
            
            # Validate structure if required
            if self.config.get("validate_structure", False):
                if progress_callback:
                    progress_callback(90, "Validating data structure")
                
                valid, validation_errors = await self._validate_data_structure(upload_path)
                metadata["validation"] = {
                    "valid": valid,
                    "errors": validation_errors
                }
                
                # Update metadata with validation results
                with open(upload_path / "metadata.json", "w") as f:
                    json.dump(metadata, f, indent=2)
            
            self.update_sync_status("completed")
            self.log_activity(
                "upload_processed",
                {
                    "upload_id": upload_id,
                    "file_count": len(metadata["extracted_files"]),
                    "size": metadata["size"]
                }
            )
            
            if progress_callback:
                progress_callback(100, "Upload processed successfully")
            
            return True, None
            
        except Exception as e:
            error = f"Upload processing error: {str(e)}"
            self.logger.error(error)
            self.update_sync_status("failed", error)
            self.log_activity("upload_failed", {"error": str(e)}, False, error)
            return False, error
    
    async def _validate_zip_file(self, zip_file_path: Path) -> bool:
        """Validate ZIP file"""
        try:
            # Check file size
            max_size_mb = self.config.get("max_file_size_mb", 1000)
            if zip_file_path.stat().st_size > max_size_mb * 1024 * 1024:
                return False
            
            # Verify it's a valid ZIP
            with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
                # Test ZIP integrity
                bad_file = zip_ref.testzip()
                if bad_file:
                    self.logger.error(f"Corrupted file in ZIP: {bad_file}")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"ZIP validation error: {str(e)}")
            return False
    
    async def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def _inventory_files(self, directory: Path) -> List[Dict[str, Any]]:
        """Create inventory of extracted files"""
        inventory = []
        
        for file_path in directory.rglob("*"):
            if file_path.is_file() and file_path.name != "metadata.json":
                inventory.append({
                    "name": file_path.name,
                    "path": str(file_path.relative_to(directory)),
                    "size": file_path.stat().st_size,
                    "extension": file_path.suffix.lower(),
                    "modified": datetime.fromtimestamp(
                        file_path.stat().st_mtime
                    ).isoformat()
                })
        
        return inventory
    
    async def _validate_data_structure(self, upload_path: Path) -> Tuple[bool, List[str]]:
        """Validate uploaded data structure"""
        errors = []
        
        # Check for expected file types
        file_types = set()
        for file_path in upload_path.rglob("*"):
            if file_path.is_file():
                file_types.add(file_path.suffix.lower())
        
        # Basic validation rules
        if not file_types:
            errors.append("No data files found")
        
        if ".sas7bdat" in file_types:
            # Check for common SAS datasets
            expected_datasets = ["dm", "ae", "lb", "vs"]  # Demographics, Adverse Events, Labs, Vital Signs
            found_datasets = set()
            
            for file_path in upload_path.glob("**/*.sas7bdat"):
                dataset_name = file_path.stem.lower()
                if dataset_name in expected_datasets:
                    found_datasets.add(dataset_name)
            
            missing = set(expected_datasets) - found_datasets
            if missing:
                errors.append(f"Missing expected datasets: {', '.join(missing)}")
        
        return len(errors) == 0, errors