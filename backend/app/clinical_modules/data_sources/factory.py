# ABOUTME: Factory for creating appropriate data source connectors
# ABOUTME: Maps data source types to their respective connector implementations

from typing import Optional
import logging

from sqlmodel import Session
from app.models import DataSource, Study
from .base import DataSourceConnector
from .medidata_rave import MedidataRaveConnector
from .zip_upload import ZipUploadConnector
from .sftp import SFTPConnector


class DataSourceFactory:
    """Factory for creating data source connectors"""
    
    # Mapping of data source types to connector classes
    CONNECTOR_MAP = {
        "medidata_rave": MedidataRaveConnector,
        "medidata_api": MedidataRaveConnector,  # Alias for consistency
        "zip_upload": ZipUploadConnector,
        "sftp": SFTPConnector,
    }
    
    @classmethod
    def create_connector(
        cls,
        data_source: DataSource,
        study: Study,
        db: Session,
        logger: Optional[logging.Logger] = None
    ) -> DataSourceConnector:
        """Create appropriate connector for data source type
        
        Args:
            data_source: DataSource model instance
            study: Study model instance
            db: Database session
            logger: Optional logger instance
            
        Returns:
            DataSourceConnector instance
            
        Raises:
            ValueError: If data source type is not supported
        """
        connector_class = cls.CONNECTOR_MAP.get(data_source.type)
        
        if not connector_class:
            raise ValueError(f"Unsupported data source type: {data_source.type}")
        
        return connector_class(
            data_source=data_source,
            study=study,
            db=db,
            logger=logger
        )
    
    @classmethod
    def get_supported_types(cls) -> list[str]:
        """Get list of supported data source types"""
        return list(cls.CONNECTOR_MAP.keys())
    
    @classmethod
    def get_required_config_fields(cls, data_source_type: str) -> list[str]:
        """Get required configuration fields for a data source type"""
        connector_class = cls.CONNECTOR_MAP.get(data_source_type)
        
        if not connector_class:
            raise ValueError(f"Unsupported data source type: {data_source_type}")
        
        # Create a dummy instance to get required fields
        dummy_ds = DataSource(
            study_id=None,
            name="dummy",
            type=data_source_type,
            config={}
        )
        dummy_study = Study(
            org_id=None,
            name="dummy",
            protocol_number="dummy"
        )
        
        connector = connector_class(
            data_source=dummy_ds,
            study=dummy_study,
            db=None,
            logger=None
        )
        
        return connector.get_required_config_fields()