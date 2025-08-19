# ABOUTME: Data source manager that handles different data acquisition methods per study
# ABOUTME: Supports Medidata Rave, Veeva Vault, and manual uploads with scheduling

import uuid
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import pyreadstat
import pyarrow as pa
import pyarrow.parquet as pq
from sqlmodel import Session, select
from app.models import Study, DataSource, DataSourceType, DataSourceStatus
from app.services.edc_pattern_mapper import EDCPatternMapper
from app.services.parquet_query_engine import ParquetQueryEngine
import asyncio
import aiohttp
from croniter import croniter

logger = logging.getLogger(__name__)


class DataSourceManager:
    """Manages different data sources for each study"""
    
    def __init__(self, db: Session):
        self.db = db
        self.edc_mapper = EDCPatternMapper()
    
    async def configure_study_data_source(
        self,
        study_id: uuid.UUID,
        source_type: DataSourceType,
        config: Dict[str, Any]
    ) -> DataSource:
        """Configure data source for a study"""
        
        # Check if study exists
        study = self.db.get(Study, study_id)
        if not study:
            raise ValueError(f"Study {study_id} not found")
        
        # Create or update data source
        existing_source = self.db.exec(
            select(DataSource).where(
                DataSource.study_id == study_id,
                DataSource.type == source_type
            )
        ).first()
        
        if existing_source:
            # Update existing
            for key, value in config.items():
                setattr(existing_source, key, value)
            existing_source.updated_at = datetime.utcnow()
            data_source = existing_source
        else:
            # Create new
            data_source = DataSource(
                study_id=study_id,
                name=f"{study.name} - {source_type.value}",
                type=source_type,
                config=config,
                status=DataSourceStatus.INACTIVE,
                created_by=config.get('created_by', study.created_by)
            )
            self.db.add(data_source)
        
        self.db.commit()
        self.db.refresh(data_source)
        
        # Test connection based on type
        if source_type == DataSourceType.MEDIDATA_API:
            await self._test_medidata_connection(data_source)
        elif source_type == DataSourceType.EDC_API:
            await self._test_veeva_connection(data_source)
        elif source_type == DataSourceType.ZIP_UPLOAD:
            # Manual upload - always active
            data_source.status = DataSourceStatus.ACTIVE
            self.db.commit()
        
        return data_source
    
    async def _test_medidata_connection(self, data_source: DataSource) -> bool:
        """Test Medidata Rave API connection"""
        try:
            config = data_source.config
            base_url = config.get('base_url', 'https://api.mdsol.com')
            study_oid = config.get('study_oid')
            
            # Would implement actual Medidata API test here
            # For now, mark as active if config looks valid
            if study_oid and config.get('username') and config.get('password'):
                data_source.status = DataSourceStatus.ACTIVE
                data_source.last_connected = datetime.utcnow()
            else:
                data_source.status = DataSourceStatus.ERROR
                data_source.last_error = "Missing required configuration"
            
            self.db.commit()
            return data_source.status == DataSourceStatus.ACTIVE
            
        except Exception as e:
            logger.error(f"Medidata connection test failed: {str(e)}")
            data_source.status = DataSourceStatus.ERROR
            data_source.last_error = str(e)
            self.db.commit()
            return False
    
    async def _test_veeva_connection(self, data_source: DataSource) -> bool:
        """Test Veeva Vault API connection"""
        try:
            config = data_source.config
            vault_url = config.get('vault_url')
            
            # Would implement actual Veeva API test here
            if vault_url and config.get('username') and config.get('password'):
                data_source.status = DataSourceStatus.ACTIVE
                data_source.last_connected = datetime.utcnow()
            else:
                data_source.status = DataSourceStatus.ERROR
                data_source.last_error = "Missing required configuration"
            
            self.db.commit()
            return data_source.status == DataSourceStatus.ACTIVE
            
        except Exception as e:
            logger.error(f"Veeva connection test failed: {str(e)}")
            data_source.status = DataSourceStatus.ERROR
            data_source.last_error = str(e)
            self.db.commit()
            return False
    
    async def sync_study_data(self, study_id: uuid.UUID) -> Dict[str, Any]:
        """Sync data from all configured sources for a study"""
        
        # Get all active data sources for study
        data_sources = self.db.exec(
            select(DataSource).where(
                DataSource.study_id == study_id,
                DataSource.is_active == True
            )
        ).all()
        
        results = {
            "synced_sources": [],
            "failed_sources": [],
            "total_records": 0
        }
        
        for source in data_sources:
            try:
                if source.type == DataSourceType.MEDIDATA_API:
                    records = await self._sync_medidata_data(study_id, source)
                elif source.type == DataSourceType.EDC_API:
                    records = await self._sync_veeva_data(study_id, source)
                elif source.type == DataSourceType.ZIP_UPLOAD:
                    # Manual uploads are handled separately
                    continue
                else:
                    logger.warning(f"Unknown source type: {source.type}")
                    continue
                
                results["synced_sources"].append(source.name)
                results["total_records"] += records
                
                # Update sync statistics
                source.last_sync = datetime.utcnow()
                source.sync_count += 1
                source.records_synced += records
                self.db.commit()
                
            except Exception as e:
                logger.error(f"Failed to sync {source.name}: {str(e)}")
                results["failed_sources"].append({
                    "source": source.name,
                    "error": str(e)
                })
                source.last_error = str(e)
                source.error_count += 1
                self.db.commit()
        
        return results
    
    async def _sync_medidata_data(
        self,
        study_id: uuid.UUID,
        data_source: DataSource
    ) -> int:
        """Sync data from Medidata Rave"""
        # This would implement actual Medidata Rave API calls
        # For now, return mock success
        logger.info(f"Syncing Medidata data for study {study_id}")
        return 0
    
    async def _sync_veeva_data(
        self,
        study_id: uuid.UUID,
        data_source: DataSource
    ) -> int:
        """Sync data from Veeva Vault"""
        # This would implement actual Veeva Vault API calls
        # For now, return mock success
        logger.info(f"Syncing Veeva data for study {study_id}")
        return 0
    
    def process_sas_datasets(
        self,
        study_id: uuid.UUID,
        sas_files: List[Path]
    ) -> Dict[str, Any]:
        """Process SAS datasets and convert to Parquet"""
        
        study = self.db.get(Study, study_id)
        if not study:
            raise ValueError(f"Study {study_id} not found")
        
        # Create output directory
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        output_dir = Path(f"/data/{study.org_id}/studies/{study_id}/processed_data/{timestamp}")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        processed = []
        failed = []
        
        for sas_file in sas_files:
            try:
                logger.info(f"Processing SAS file: {sas_file}")
                
                # Read SAS file
                df, meta = pyreadstat.read_sas7bdat(str(sas_file))
                
                # Detect EDC system and patterns
                edc_system = self.edc_mapper.detect_edc_system(df)
                
                # Convert column names to uppercase for consistency
                df.columns = [col.upper() for col in df.columns]
                
                # Save as Parquet
                dataset_name = sas_file.stem.lower()
                parquet_path = output_dir / f"{dataset_name}.parquet"
                
                # Convert to PyArrow table for better type handling
                table = pa.Table.from_pandas(df)
                pq.write_table(table, parquet_path)
                
                # Store metadata in database
                from sqlalchemy import text
                
                metadata = {
                    "original_file": sas_file.name,
                    "edc_system": edc_system,
                    "row_count": len(df),
                    "column_count": len(df.columns),
                    "columns": df.columns.tolist(),
                    "detected_patterns": self._detect_dataset_patterns(df, dataset_name)
                }
                
                # Insert into dataset_metadata table
                query = text("""
                    INSERT INTO dataset_metadata 
                    (id, org_id, study_id, dataset_name, dataset_type, 
                     file_path, parquet_path, row_count, column_count, 
                     columns_info, detected_patterns, file_size, created_at)
                    VALUES 
                    (:id, :org_id, :study_id, :dataset_name, :dataset_type,
                     :file_path, :parquet_path, :row_count, :column_count,
                     :columns_info, :detected_patterns, :file_size, :created_at)
                    ON CONFLICT (study_id, dataset_name, version) DO UPDATE
                    SET row_count = EXCLUDED.row_count,
                        column_count = EXCLUDED.column_count,
                        columns_info = EXCLUDED.columns_info,
                        updated_at = NOW()
                """)
                
                self.db.execute(query, {
                    "id": str(uuid.uuid4()),
                    "org_id": str(study.org_id),
                    "study_id": str(study_id),
                    "dataset_name": dataset_name,
                    "dataset_type": "SDTM" if edc_system == "medidata_rave" else "Custom",
                    "file_path": str(sas_file),
                    "parquet_path": str(parquet_path),
                    "row_count": metadata["row_count"],
                    "column_count": metadata["column_count"],
                    "columns_info": metadata,
                    "detected_patterns": metadata["detected_patterns"],
                    "file_size": sas_file.stat().st_size,
                    "created_at": datetime.utcnow()
                })
                
                processed.append({
                    "file": sas_file.name,
                    "dataset": dataset_name,
                    "rows": len(df),
                    "parquet": str(parquet_path)
                })
                
            except Exception as e:
                logger.error(f"Failed to process {sas_file}: {str(e)}")
                failed.append({
                    "file": sas_file.name,
                    "error": str(e)
                })
        
        self.db.commit()
        
        return {
            "processed": processed,
            "failed": failed,
            "output_dir": str(output_dir)
        }
    
    def _detect_dataset_patterns(self, df: pd.DataFrame, dataset_name: str) -> Dict[str, Any]:
        """Detect patterns in dataset for auto-mapping"""
        patterns = {
            "dataset_type": None,
            "key_fields": [],
            "date_fields": [],
            "categorical_fields": [],
            "numeric_fields": []
        }
        
        # Detect dataset type based on name and columns
        if dataset_name in ['dm', 'demographics']:
            patterns["dataset_type"] = "demographics"
        elif dataset_name in ['ae', 'adverse_events']:
            patterns["dataset_type"] = "adverse_events"
        elif dataset_name in ['lb', 'lab', 'laboratory']:
            patterns["dataset_type"] = "laboratory"
        elif dataset_name in ['vs', 'vitals']:
            patterns["dataset_type"] = "vital_signs"
        
        # Detect key fields
        for col in df.columns:
            col_upper = col.upper()
            
            # Subject ID patterns
            if any(pattern in col_upper for pattern in ['USUBJID', 'SUBJID', 'SUBJECT']):
                patterns["key_fields"].append(col)
            
            # Date patterns
            if any(pattern in col_upper for pattern in ['DATE', 'DTC', 'DAT']):
                patterns["date_fields"].append(col)
            
            # Analyze data type
            if df[col].dtype == 'object':
                unique_ratio = df[col].nunique() / len(df)
                if unique_ratio < 0.1:  # Less than 10% unique values
                    patterns["categorical_fields"].append(col)
            elif df[col].dtype in ['int64', 'float64']:
                patterns["numeric_fields"].append(col)
        
        return patterns
    
    def schedule_data_refresh(
        self,
        study_id: uuid.UUID,
        schedule: str  # Cron expression
    ) -> bool:
        """Schedule automatic data refresh for a study"""
        
        # Validate cron expression
        if not croniter.is_valid(schedule):
            raise ValueError(f"Invalid cron expression: {schedule}")
        
        # Get data sources for study
        data_sources = self.db.exec(
            select(DataSource).where(
                DataSource.study_id == study_id,
                DataSource.is_active == True
            )
        ).all()
        
        # Update refresh schedule for each source
        for source in data_sources:
            source.config["refresh_schedule"] = schedule
            
            # Calculate next sync time
            cron = croniter(schedule, datetime.utcnow())
            source.next_sync = cron.get_next(datetime)
            
            self.db.add(source)
        
        self.db.commit()
        
        logger.info(f"Scheduled data refresh for study {study_id}: {schedule}")
        return True