# ABOUTME: Data upload service for handling file uploads and Parquet conversion
# ABOUTME: Manages versioning, validation, and data profiling for uploaded files

import os
import shutil
import hashlib
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
import uuid
import json
import zipfile
import tempfile
from fastapi import UploadFile, HTTPException
from sqlmodel import Session, select

from app.models.data_source_upload import (
    DataSourceUpload, 
    DataSourceUploadCreate,
    UploadStatus,
    FileFormat,
    ParquetFileInfo
)
from app.models.study import Study
from app.core.config import settings
from app.core.logging import logger

class DataUploadService:
    """Service for handling data uploads and conversions"""
    
    def __init__(self, db: Session):
        self.db = db
        self.base_upload_path = Path(settings.DATA_UPLOAD_PATH)
        self.base_parquet_path = Path(settings.DATA_PARQUET_PATH)
        
        # Ensure directories exist
        self.base_upload_path.mkdir(parents=True, exist_ok=True)
        self.base_parquet_path.mkdir(parents=True, exist_ok=True)
    
    async def upload_file(
        self,
        file: UploadFile,
        study_id: str,
        user_id: str,
        upload_name: str,
        description: Optional[str] = None
    ) -> DataSourceUpload:
        """Handle file upload and initiate processing"""
        
        # Validate study exists
        study = self.db.get(Study, study_id)
        if not study:
            raise HTTPException(status_code=404, detail="Study not found")
        
        # Determine file format
        file_format = self._detect_file_format(file.filename)
        
        # Create upload record
        upload_id = str(uuid.uuid4())
        timestamp = datetime.utcnow()
        
        # Create versioned directory structure
        study_path = self.base_upload_path / study_id
        version = self._get_next_version(study_id)
        version_path = study_path / f"v{version}" / timestamp.strftime("%Y%m%d_%H%M%S")
        version_path.mkdir(parents=True, exist_ok=True)
        
        # Save raw file
        raw_file_path = version_path / file.filename
        file_size_mb = 0
        
        try:
            # Save uploaded file
            with open(raw_file_path, "wb") as f:
                content = await file.read()
                f.write(content)
                file_size_mb = len(content) / (1024 * 1024)
            
            # Create upload record
            upload = DataSourceUpload(
                id=upload_id,
                study_id=study_id,
                upload_name=upload_name,
                description=description,
                original_filename=file.filename,
                file_format=file_format,
                file_size_mb=file_size_mb,
                raw_path=str(raw_file_path),
                status=UploadStatus.UPLOADED,
                version_number=version,
                created_by=user_id,
                upload_timestamp=timestamp
            )
            
            self.db.add(upload)
            self.db.commit()
            
            # Start async processing
            await self._process_upload(upload)
            
            return upload
            
        except Exception as e:
            logger.error(f"Upload failed: {str(e)}")
            # Clean up on failure
            if raw_file_path.exists():
                os.remove(raw_file_path)
            raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
    
    async def _process_upload(self, upload: DataSourceUpload):
        """Process uploaded file and convert to Parquet"""
        
        try:
            # Update status
            upload.status = UploadStatus.PROCESSING
            upload.processing_started_at = datetime.utcnow()
            self.db.add(upload)
            self.db.commit()
            
            # Process based on file type
            if upload.file_format == FileFormat.ZIP:
                parquet_files = await self._process_zip_file(upload)
            else:
                parquet_files = await self._process_single_file(upload)
            
            # Create Parquet storage path
            parquet_path = self.base_parquet_path / str(upload.study_id) / f"v{upload.version_number}"
            parquet_path.mkdir(parents=True, exist_ok=True)
            
            # Update upload record
            upload.status = UploadStatus.COMPLETED
            upload.processing_completed_at = datetime.utcnow()
            upload.processing_duration_seconds = (
                upload.processing_completed_at - upload.processing_started_at
            ).total_seconds()
            upload.processed_path = str(parquet_path)
            upload.files_extracted = [pf.dict() for pf in parquet_files]
            
            # Calculate totals
            upload.total_rows = sum(pf.row_count for pf in parquet_files)
            upload.total_columns = sum(pf.column_count for pf in parquet_files)
            
            self.db.add(upload)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Processing failed for upload {upload.id}: {str(e)}")
            upload.status = UploadStatus.FAILED
            upload.error_message = str(e)
            self.db.add(upload)
            self.db.commit()
    
    async def _process_single_file(self, upload: DataSourceUpload) -> List[ParquetFileInfo]:
        """Process a single data file"""
        
        raw_path = Path(upload.raw_path)
        parquet_info_list = []
        
        # Read file based on format
        df = self._read_file(raw_path, upload.file_format)
        
        if df is not None:
            # Profile data
            profile = self._profile_dataframe(df)
            
            # Convert to Parquet
            parquet_path = self.base_parquet_path / str(upload.study_id) / f"v{upload.version_number}"
            parquet_path.mkdir(parents=True, exist_ok=True)
            
            dataset_name = raw_path.stem
            parquet_file = parquet_path / f"{dataset_name}.parquet"
            
            # Write Parquet with compression
            table = pa.Table.from_pandas(df)
            pq.write_table(table, parquet_file, compression='snappy')
            
            # Create info object
            parquet_info = ParquetFileInfo(
                dataset_name=dataset_name,
                file_path=str(parquet_file),
                row_count=len(df),
                column_count=len(df.columns),
                columns=[{"name": col, "type": str(df[col].dtype)} for col in df.columns],
                file_size_mb=parquet_file.stat().st_size / (1024 * 1024),
                compression="snappy",
                created_at=datetime.utcnow()
            )
            
            parquet_info_list.append(parquet_info)
            
            # Store profile in upload metadata
            upload.upload_metadata = {"data_profile": profile}
        
        return parquet_info_list
    
    async def _process_zip_file(self, upload: DataSourceUpload) -> List[ParquetFileInfo]:
        """Process a ZIP file containing multiple datasets"""
        
        zip_path = Path(upload.raw_path)
        parquet_info_list = []
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Extract ZIP
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_path)
            
            # Process each file
            for file_path in temp_path.rglob('*'):
                if file_path.is_file():
                    file_format = self._detect_file_format(file_path.name)
                    
                    if file_format and file_format != FileFormat.ZIP:
                        df = self._read_file(file_path, file_format)
                        
                        if df is not None:
                            # Convert to Parquet
                            parquet_path = self.base_parquet_path / str(upload.study_id) / f"v{upload.version_number}"
                            parquet_path.mkdir(parents=True, exist_ok=True)
                            
                            dataset_name = file_path.stem
                            parquet_file = parquet_path / f"{dataset_name}.parquet"
                            
                            # Write Parquet
                            table = pa.Table.from_pandas(df)
                            pq.write_table(table, parquet_file, compression='snappy')
                            
                            # Create info object
                            parquet_info = ParquetFileInfo(
                                dataset_name=dataset_name,
                                file_path=str(parquet_file),
                                row_count=len(df),
                                column_count=len(df.columns),
                                columns=[{"name": col, "type": str(df[col].dtype)} for col in df.columns],
                                file_size_mb=parquet_file.stat().st_size / (1024 * 1024),
                                compression="snappy",
                                created_at=datetime.utcnow()
                            )
                            
                            parquet_info_list.append(parquet_info)
        
        return parquet_info_list
    
    def _read_file(self, file_path: Path, file_format: FileFormat) -> Optional[pd.DataFrame]:
        """Read file into DataFrame based on format"""
        
        try:
            if file_format == FileFormat.CSV:
                return pd.read_csv(file_path)
            elif file_format == FileFormat.XLSX:
                return pd.read_excel(file_path)
            elif file_format == FileFormat.PARQUET:
                return pd.read_parquet(file_path)
            elif file_format == FileFormat.SAS7BDAT:
                # Requires sas7bdat or pyreadstat library
                try:
                    import pyreadstat
                    df, meta = pyreadstat.read_sas7bdat(str(file_path))
                    return df
                except ImportError:
                    logger.warning("pyreadstat not installed, trying pandas")
                    return pd.read_sas(file_path)
            elif file_format == FileFormat.XPT:
                # SAS Transport format
                return pd.read_sas(file_path, format='xport')
            else:
                logger.warning(f"Unsupported format: {file_format}")
                return None
        except Exception as e:
            logger.error(f"Failed to read file {file_path}: {str(e)}")
            return None
    
    def _profile_dataframe(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate data profile for DataFrame"""
        
        profile = {
            "shape": {"rows": len(df), "columns": len(df.columns)},
            "columns": {},
            "memory_usage_mb": df.memory_usage(deep=True).sum() / (1024 * 1024)
        }
        
        for col in df.columns:
            col_profile = {
                "dtype": str(df[col].dtype),
                "null_count": df[col].isnull().sum(),
                "null_percentage": (df[col].isnull().sum() / len(df)) * 100,
                "unique_count": df[col].nunique(),
                "unique_percentage": (df[col].nunique() / len(df)) * 100
            }
            
            # Add statistics for numeric columns
            if pd.api.types.is_numeric_dtype(df[col]):
                col_profile.update({
                    "min": float(df[col].min()),
                    "max": float(df[col].max()),
                    "mean": float(df[col].mean()),
                    "median": float(df[col].median()),
                    "std": float(df[col].std())
                })
            
            # Sample values for categorical columns
            if pd.api.types.is_object_dtype(df[col]):
                top_values = df[col].value_counts().head(10).to_dict()
                col_profile["top_values"] = {str(k): v for k, v in top_values.items()}
            
            profile["columns"][col] = col_profile
        
        return profile
    
    def _detect_file_format(self, filename: str) -> Optional[FileFormat]:
        """Detect file format from filename"""
        
        ext = Path(filename).suffix.lower()
        
        format_map = {
            '.csv': FileFormat.CSV,
            '.xlsx': FileFormat.XLSX,
            '.xls': FileFormat.XLSX,
            '.sas7bdat': FileFormat.SAS7BDAT,
            '.xpt': FileFormat.XPT,
            '.parquet': FileFormat.PARQUET,
            '.zip': FileFormat.ZIP
        }
        
        return format_map.get(ext)
    
    def _get_next_version(self, study_id: str) -> int:
        """Get next version number for study uploads"""
        
        stmt = select(DataSourceUpload).where(
            DataSourceUpload.study_id == study_id
        ).order_by(DataSourceUpload.version_number.desc())
        
        latest = self.db.exec(stmt).first()
        
        if latest:
            return latest.version_number + 1
        return 1
    
    def get_available_datasets(self, study_id: str) -> List[Dict[str, Any]]:
        """Get list of available datasets for a study"""
        
        # Get latest active upload
        stmt = select(DataSourceUpload).where(
            DataSourceUpload.study_id == study_id,
            DataSourceUpload.is_active_version == True,
            DataSourceUpload.status == UploadStatus.COMPLETED
        ).order_by(DataSourceUpload.version_number.desc())
        
        upload = self.db.exec(stmt).first()
        
        if not upload or not upload.files_extracted:
            return []
        
        datasets = []
        for file_info in upload.files_extracted:
            datasets.append({
                "upload_id": str(upload.id),
                "dataset_name": file_info["dataset_name"],
                "columns": file_info["columns"],
                "row_count": file_info["row_count"],
                "version": upload.version_number,
                "uploaded_at": upload.upload_timestamp.isoformat()
            })
        
        return datasets
    
    def get_dataset_columns(self, study_id: str, dataset_name: str) -> List[Dict[str, str]]:
        """Get columns for a specific dataset"""
        
        datasets = self.get_available_datasets(study_id)
        
        for dataset in datasets:
            if dataset["dataset_name"] == dataset_name:
                return dataset["columns"]
        
        return []