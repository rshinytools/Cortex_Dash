# ABOUTME: Base connector class for all data source integrations
# ABOUTME: Provides common interface and functionality for data acquisition

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import logging
from pathlib import Path

from sqlmodel import Session
from app.models import DataSource, Study
from app.crud import activity_log as crud_activity


class DataSourceConnector(ABC):
    """Abstract base class for all data source connectors"""
    
    def __init__(
        self,
        data_source: DataSource,
        study: Study,
        db: Session,
        logger: Optional[logging.Logger] = None
    ):
        self.data_source = data_source
        self.study = study
        self.db = db
        self.logger = logger or logging.getLogger(__name__)
        self.config = data_source.config or {}
        
    @abstractmethod
    async def test_connection(self) -> Tuple[bool, Optional[str]]:
        """Test connection to data source
        
        Returns:
            Tuple of (success, error_message)
        """
        pass
    
    @abstractmethod
    async def list_available_data(self) -> List[Dict[str, Any]]:
        """List available data from source
        
        Returns:
            List of available datasets/files with metadata
        """
        pass
    
    @abstractmethod
    async def download_data(
        self,
        dataset_id: str,
        target_path: Path,
        progress_callback: Optional[callable] = None
    ) -> Tuple[bool, Optional[str]]:
        """Download specific dataset
        
        Args:
            dataset_id: Identifier for the dataset
            target_path: Where to save the data
            progress_callback: Optional callback for progress updates
            
        Returns:
            Tuple of (success, error_message)
        """
        pass
    
    @abstractmethod
    async def get_metadata(self, dataset_id: str) -> Dict[str, Any]:
        """Get metadata for a specific dataset
        
        Args:
            dataset_id: Identifier for the dataset
            
        Returns:
            Dictionary with dataset metadata
        """
        pass
    
    def log_activity(
        self,
        action: str,
        details: Dict[str, Any],
        success: bool = True,
        error_message: Optional[str] = None
    ):
        """Log activity for audit trail"""
        # Get current user from context if available
        # For now, we'll log as system activity
        crud_activity.create_activity_log(
            self.db,
            user=None,  # System activity
            action=f"data_source_{action}",
            resource_type="data_source",
            resource_id=str(self.data_source.id),
            details={
                **details,
                "study_id": str(self.study.id),
                "data_source_type": self.data_source.type,
                "data_source_name": self.data_source.name
            },
            success=success,
            error_message=error_message
        )
    
    def update_sync_status(
        self,
        status: str,
        error: Optional[str] = None
    ):
        """Update data source sync status"""
        self.data_source.sync_status = status
        self.data_source.last_sync = datetime.utcnow()
        if error:
            self.data_source.sync_error = error
        else:
            self.data_source.sync_error = None
        
        self.db.add(self.data_source)
        self.db.commit()
        
    async def validate_config(self) -> Tuple[bool, Optional[str]]:
        """Validate data source configuration
        
        Returns:
            Tuple of (valid, error_message)
        """
        required_fields = self.get_required_config_fields()
        
        for field in required_fields:
            if field not in self.config:
                return False, f"Missing required configuration field: {field}"
        
        return True, None
    
    @abstractmethod
    def get_required_config_fields(self) -> List[str]:
        """Get list of required configuration fields"""
        pass
    
    def get_download_path(self, dataset_id: str) -> Path:
        """Get standard download path for dataset"""
        # Import the folder structure utility
        from app.clinical_modules.utils.folder_structure import get_study_data_path, ensure_folder_exists
        
        # Get the standardized path with current timestamp
        dataset_path = get_study_data_path(
            org_id=self.study.org_id,
            study_id=self.study.id,
            timestamp=None  # Will use current timestamp in YYYYMMDD_HHMMSS format
        )
        
        # Ensure the folder exists
        ensure_folder_exists(dataset_path)
        
        return dataset_path