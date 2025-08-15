# ABOUTME: Base integration class for external API connections
# ABOUTME: Provides common functionality for all clinical data integrations

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
import asyncio
import aiohttp
from sqlmodel import Session

from app.models.data_source import DataSource, DataSourceStatus
from app.core.logging import logger

class IntegrationType(str, Enum):
    MEDIDATA_RAVE = "medidata_rave"
    VEEVA_VAULT = "veeva_vault"
    REDCAP = "redcap"
    CUSTOM_API = "custom_api"

class IntegrationStatus(str, Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    SYNCING = "syncing"
    AUTHENTICATED = "authenticated"

class BaseIntegration(ABC):
    """Base class for all clinical data integrations"""
    
    def __init__(self, data_source: DataSource, db: Session):
        self.data_source = data_source
        self.db = db
        self.session: Optional[aiohttp.ClientSession] = None
        self.auth_token: Optional[str] = None
        self.base_url: Optional[str] = None
        self.rate_limit = 100  # requests per minute
        self.retry_attempts = 3
        self.timeout = 30  # seconds
        
    @abstractmethod
    async def authenticate(self) -> bool:
        """Authenticate with the external system"""
        pass
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """Test the connection to the external system"""
        pass
    
    @abstractmethod
    async def fetch_studies(self) -> List[Dict[str, Any]]:
        """Fetch available studies from the system"""
        pass
    
    @abstractmethod
    async def fetch_datasets(self, study_id: str) -> List[Dict[str, Any]]:
        """Fetch datasets for a specific study"""
        pass
    
    @abstractmethod
    async def download_data(self, study_id: str, dataset_name: str) -> bytes:
        """Download specific dataset data"""
        pass
    
    async def sync_data(self, study_id: str) -> Dict[str, Any]:
        """Sync all data for a study"""
        
        try:
            # Update status
            self.data_source.status = DataSourceStatus.TESTING
            self.data_source.last_sync = datetime.utcnow()
            self.db.add(self.data_source)
            self.db.commit()
            
            # Authenticate
            if not await self.authenticate():
                raise Exception("Authentication failed")
            
            # Fetch datasets
            datasets = await self.fetch_datasets(study_id)
            
            results = {
                "success": True,
                "datasets_synced": [],
                "errors": [],
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Download each dataset
            for dataset in datasets:
                try:
                    data = await self.download_data(study_id, dataset["name"])
                    
                    # Process and save data
                    await self.process_data(dataset["name"], data)
                    
                    results["datasets_synced"].append({
                        "name": dataset["name"],
                        "size": len(data),
                        "records": dataset.get("record_count", 0)
                    })
                    
                except Exception as e:
                    logger.error(f"Failed to sync dataset {dataset['name']}: {str(e)}")
                    results["errors"].append({
                        "dataset": dataset["name"],
                        "error": str(e)
                    })
            
            # Update status
            self.data_source.status = DataSourceStatus.ACTIVE
            self.data_source.sync_count += 1
            self.data_source.last_sync = datetime.utcnow()
            self.db.add(self.data_source)
            self.db.commit()
            
            return results
            
        except Exception as e:
            logger.error(f"Sync failed: {str(e)}")
            
            # Update status
            self.data_source.status = DataSourceStatus.ERROR
            self.data_source.last_error = str(e)
            self.data_source.error_count += 1
            self.db.add(self.data_source)
            self.db.commit()
            
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def process_data(self, dataset_name: str, data: bytes):
        """Process downloaded data and save to storage"""
        
        # This would integrate with the upload service
        # to convert to Parquet and version the data
        from app.services.data.upload_service import DataUploadService
        
        upload_service = DataUploadService(self.db)
        
        # Create temporary file
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
            tmp.write(data)
            tmp_path = tmp.name
        
        # Process through upload service
        # This would be implemented to handle the conversion
        pass
    
    async def create_session(self):
        """Create aiohttp session with proper settings"""
        
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            connector = aiohttp.TCPConnector(limit=50)
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                connector=connector
            )
        
        return self.session
    
    async def close_session(self):
        """Close aiohttp session"""
        
        if self.session:
            await self.session.close()
            self.session = None
    
    async def make_request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
        json: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make HTTP request with retry logic"""
        
        session = await self.create_session()
        
        for attempt in range(self.retry_attempts):
            try:
                async with session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    data=data,
                    json=json
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 429:  # Rate limited
                        wait_time = int(response.headers.get("Retry-After", 60))
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        error_text = await response.text()
                        raise Exception(f"Request failed: {response.status} - {error_text}")
                        
            except asyncio.TimeoutError:
                if attempt == self.retry_attempts - 1:
                    raise Exception("Request timed out")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                
            except Exception as e:
                if attempt == self.retry_attempts - 1:
                    raise e
                await asyncio.sleep(2 ** attempt)
        
        raise Exception("Max retry attempts exceeded")
    
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """Get configuration value from data source config"""
        
        if self.data_source.config:
            return self.data_source.config.get(key, default)
        return default
    
    def update_config(self, key: str, value: Any):
        """Update configuration value"""
        
        if not self.data_source.config:
            self.data_source.config = {}
        
        self.data_source.config[key] = value
        self.db.add(self.data_source)
        self.db.commit()