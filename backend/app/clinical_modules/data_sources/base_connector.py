# ABOUTME: Base connector class for all data source types
# ABOUTME: Provides common functionality for folder management and data handling

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Tuple, List, Optional
from datetime import datetime
import logging
import uuid

from app.clinical_modules.utils.folder_structure import (
    get_study_data_path,
    ensure_folder_exists,
    get_extract_date_folder
)


logger = logging.getLogger(__name__)


class BaseDataSourceConnector(ABC):
    """
    Base class for all data source connectors.
    Ensures consistent folder structure across all data source types.
    """
    
    def __init__(
        self,
        config: Dict[str, Any],
        org_id: uuid.UUID,
        study_id: uuid.UUID
    ):
        self.config = config
        self.org_id = org_id
        self.study_id = study_id
        self.extract_date = get_extract_date_folder()
        
    @abstractmethod
    async def test_connection(self) -> Tuple[bool, str]:
        """
        Test the connection to the data source.
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        pass
    
    @abstractmethod
    async def fetch_data(self) -> List[Path]:
        """
        Fetch data from the source and save to standardized folder structure.
        
        Returns:
            List of paths to downloaded files
        """
        pass
    
    @abstractmethod
    def get_available_datasets(self) -> List[Dict[str, Any]]:
        """
        Get list of available datasets from the source.
        
        Returns:
            List of dataset information
        """
        pass
    
    def get_data_path(self, extract_date: Optional[str] = None) -> Path:
        """
        Get the standardized data path for this connector.
        Uses current date if extract_date not provided.
        
        Args:
            extract_date: Optional extract date in DDMMMYYYY format
        
        Returns:
            Path object for data storage
        """
        if extract_date is None:
            extract_date = self.extract_date
            
        return get_study_data_path(
            org_id=self.org_id,
            study_id=self.study_id,
            extract_date=extract_date,
            data_type="raw"
        )
    
    def prepare_download_folder(self) -> Path:
        """
        Prepare the download folder for incoming data.
        
        Returns:
            Path to the prepared folder
        """
        data_path = self.get_data_path()
        ensure_folder_exists(data_path)
        
        logger.info(f"Prepared download folder: {data_path}")
        return data_path
    
    def log_download_metadata(self, files: List[Path]) -> None:
        """
        Log metadata about downloaded files.
        
        Args:
            files: List of downloaded file paths
        """
        metadata_path = self.get_data_path() / "_metadata.json"
        
        metadata = {
            "download_timestamp": datetime.utcnow().isoformat(),
            "extract_date": self.extract_date,
            "source_type": self.__class__.__name__,
            "files": [
                {
                    "filename": f.name,
                    "size_bytes": f.stat().st_size,
                    "path": str(f)
                }
                for f in files
            ],
            "total_files": len(files),
            "org_id": str(self.org_id),
            "study_id": str(self.study_id)
        }
        
        import json
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
            
        logger.info(f"Saved download metadata to {metadata_path}")