# ABOUTME: Celery tasks for data source operations
# ABOUTME: Handles async data synchronization and testing

from celery import shared_task, current_task
from typing import Dict, Any, Optional, Tuple
import logging

from sqlmodel import Session
from app.core.db import engine
from app.models import Study, DataSource, User
from app.clinical_modules.data_sources.factory import DataSourceFactory


logger = logging.getLogger(__name__)


@shared_task(bind=True, name="app.clinical_modules.data_sources.tasks.test_data_source")
def test_data_source(self, data_source_id: str) -> Dict[str, Any]:
    """Test data source connection asynchronously"""
    try:
        with Session(engine) as db:
            # Get data source
            data_source = db.get(DataSource, data_source_id)
            if not data_source:
                raise ValueError(f"Data source not found: {data_source_id}")
            
            # Get study
            study = db.get(Study, data_source.study_id)
            if not study:
                raise ValueError(f"Study not found: {data_source.study_id}")
            
            # Create connector
            connector = DataSourceFactory.create_connector(
                data_source, study, db, logger
            )
            
            # Test connection
            import asyncio
            success, error = asyncio.run(connector.test_connection())
            
            return {
                "data_source_id": data_source_id,
                "data_source_name": data_source.name,
                "type": data_source.type,
                "success": success,
                "error": error,
                "tested_at": data_source.last_sync.isoformat() if data_source.last_sync else None
            }
            
    except Exception as e:
        logger.error(f"Data source test failed: {str(e)}")
        return {
            "data_source_id": data_source_id,
            "success": False,
            "error": str(e)
        }


@shared_task(bind=True, name="app.clinical_modules.data_sources.tasks.sync_data_source")
def sync_data_source(
    self,
    data_source_id: str,
    datasets: Optional[list] = None,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """Synchronize data from a data source"""
    try:
        with Session(engine) as db:
            # Get data source
            data_source = db.get(DataSource, data_source_id)
            if not data_source:
                raise ValueError(f"Data source not found: {data_source_id}")
            
            # Get study
            study = db.get(Study, data_source.study_id)
            if not study:
                raise ValueError(f"Study not found: {data_source.study_id}")
            
            # Create connector
            connector = DataSourceFactory.create_connector(
                data_source, study, db, logger
            )
            
            # Update progress callback
            def update_progress(progress: int, message: str):
                current_task.update_state(
                    state="PROGRESS",
                    meta={
                        "current": progress,
                        "total": 100,
                        "status": message
                    }
                )
            
            # Test connection first
            import asyncio
            connected, error = asyncio.run(connector.test_connection())
            if not connected:
                raise Exception(f"Connection failed: {error}")
            
            update_progress(10, "Connection successful, listing available data")
            
            # List available data
            available_data = asyncio.run(connector.list_available_data())
            
            # Filter datasets if specified
            if datasets:
                available_data = [d for d in available_data if d["id"] in datasets]
            
            # Download each dataset
            results = {
                "data_source_id": data_source_id,
                "data_source_name": data_source.name,
                "datasets_synced": [],
                "errors": []
            }
            
            for i, dataset in enumerate(available_data):
                progress = 20 + (70 * i / len(available_data))
                update_progress(progress, f"Downloading {dataset['name']}")
                
                try:
                    download_path = connector.get_download_path(dataset["id"])
                    success, error = asyncio.run(
                        connector.download_data(
                            dataset["id"],
                            download_path,
                            lambda p, m: update_progress(
                                progress + (p * 0.7 / len(available_data)),
                                m
                            )
                        )
                    )
                    
                    if success:
                        results["datasets_synced"].append({
                            "id": dataset["id"],
                            "name": dataset["name"],
                            "path": str(download_path)
                        })
                    else:
                        results["errors"].append({
                            "dataset_id": dataset["id"],
                            "error": error
                        })
                        
                except Exception as e:
                    results["errors"].append({
                        "dataset_id": dataset["id"],
                        "error": str(e)
                    })
            
            update_progress(100, "Synchronization completed")
            
            return results
            
    except Exception as e:
        logger.error(f"Data source sync failed: {str(e)}")
        current_task.update_state(
            state="FAILURE",
            meta={
                "error": str(e)
            }
        )
        raise


@shared_task(name="app.clinical_modules.data_sources.tasks.process_zip_upload")
def process_zip_upload(
    data_source_id: str,
    zip_file_path: str,
    upload_name: str,
    user_metadata: Optional[Dict[str, Any]] = None,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """Process an uploaded ZIP file"""
    try:
        with Session(engine) as db:
            # Get data source
            data_source = db.get(DataSource, data_source_id)
            if not data_source:
                raise ValueError(f"Data source not found: {data_source_id}")
            
            # Get study
            study = db.get(Study, data_source.study_id)
            if not study:
                raise ValueError(f"Study not found: {data_source.study_id}")
            
            # Create ZIP upload connector
            from app.clinical_modules.data_sources.zip_upload import ZipUploadConnector
            connector = ZipUploadConnector(data_source, study, db, logger)
            
            # Process the upload
            from pathlib import Path
            import asyncio
            
            success, error = asyncio.run(
                connector.process_zip_upload(
                    Path(zip_file_path),
                    upload_name,
                    user_metadata
                )
            )
            
            return {
                "data_source_id": data_source_id,
                "upload_name": upload_name,
                "success": success,
                "error": error
            }
            
    except Exception as e:
        logger.error(f"ZIP upload processing failed: {str(e)}")
        return {
            "data_source_id": data_source_id,
            "success": False,
            "error": str(e)
        }