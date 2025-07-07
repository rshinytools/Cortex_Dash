# ABOUTME: Data source manager for auto-detecting and routing queries to appropriate adapters
# ABOUTME: Handles connection pooling, caching, and adapter lifecycle management

from typing import Any, Dict, List, Optional, Type, Union
import pandas as pd
from pathlib import Path
import logging
from enum import Enum
import asyncio
from datetime import datetime, timedelta

from app.services.data_adapters.base import DataSourceAdapter
from app.services.data_adapters.sas_adapter import SASAdapter
from app.services.data_adapters.csv_adapter import CSVAdapter
from app.services.data_adapters.parquet_adapter import ParquetAdapter
from app.services.data_adapters.postgres_adapter import PostgreSQLAdapter

logger = logging.getLogger(__name__)


class DataSourceType(Enum):
    """Supported data source types."""
    SAS = "sas"
    CSV = "csv"
    PARQUET = "parquet"
    POSTGRESQL = "postgresql"
    UNKNOWN = "unknown"


class DataSourceManager:
    """
    Manages data source adapters and routes queries to appropriate adapters.
    
    Provides:
    - Auto-detection of data source types
    - Connection pooling and lifecycle management
    - Schema caching with TTL
    - Query routing and execution
    """
    
    # Adapter class mapping
    ADAPTER_CLASSES: Dict[DataSourceType, Type[DataSourceAdapter]] = {
        DataSourceType.SAS: SASAdapter,
        DataSourceType.CSV: CSVAdapter,
        DataSourceType.PARQUET: ParquetAdapter,
        DataSourceType.POSTGRESQL: PostgreSQLAdapter
    }
    
    def __init__(self, cache_ttl_minutes: int = 60):
        """
        Initialize the data source manager.
        
        Args:
            cache_ttl_minutes: How long to cache schemas (default: 60 minutes)
        """
        self._adapters: Dict[str, DataSourceAdapter] = {}
        self._adapter_types: Dict[str, DataSourceType] = {}
        self._schema_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
        self.cache_ttl = timedelta(minutes=cache_ttl_minutes)
        self._lock = asyncio.Lock()
    
    async def register_data_source(
        self,
        source_name: str,
        source_type: Optional[DataSourceType] = None,
        connection_params: Optional[Dict[str, Any]] = None,
        base_path: Optional[str] = None
    ) -> None:
        """
        Register a data source with the manager.
        
        Args:
            source_name: Unique name for this data source
            source_type: Type of data source (auto-detected if not provided)
            connection_params: Connection parameters for the adapter
            base_path: Base path for file-based sources
        """
        async with self._lock:
            # Auto-detect type if not provided
            if source_type is None and base_path:
                source_type = await self._detect_source_type(base_path)
            
            if source_type is None or source_type == DataSourceType.UNKNOWN:
                raise ValueError(f"Could not determine data source type for {source_name}")
            
            # Prepare connection parameters
            if connection_params is None:
                connection_params = {}
            
            if base_path and source_type in [DataSourceType.SAS, DataSourceType.CSV, DataSourceType.PARQUET]:
                connection_params['base_path'] = base_path
            
            # Create adapter instance
            adapter_class = self.ADAPTER_CLASSES.get(source_type)
            if not adapter_class:
                raise ValueError(f"No adapter available for source type: {source_type}")
            
            adapter = adapter_class(connection_params)
            
            # Connect if needed (for database adapters)
            if hasattr(adapter, 'connect') and source_type == DataSourceType.POSTGRESQL:
                await adapter.connect()
            
            # Store adapter
            self._adapters[source_name] = adapter
            self._adapter_types[source_name] = source_type
            
            logger.info(f"Registered data source '{source_name}' of type {source_type.value}")
    
    async def unregister_data_source(self, source_name: str) -> None:
        """Unregister a data source and clean up resources."""
        async with self._lock:
            if source_name in self._adapters:
                adapter = self._adapters[source_name]
                
                # Disconnect if needed
                if hasattr(adapter, 'disconnect'):
                    await adapter.disconnect()
                
                # Remove from registries
                del self._adapters[source_name]
                del self._adapter_types[source_name]
                
                # Clear cache
                if source_name in self._schema_cache:
                    del self._schema_cache[source_name]
                if source_name in self._cache_timestamps:
                    del self._cache_timestamps[source_name]
                
                logger.info(f"Unregistered data source '{source_name}'")
    
    async def query(
        self,
        source_name: str,
        query: Union[str, Dict[str, Any]],
        field_mappings: Optional[Dict[str, str]] = None,
        limit: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Execute a query against a registered data source.
        
        Args:
            source_name: Name of the registered data source
            query: Query to execute (format depends on adapter type)
            field_mappings: Optional field name mappings
            limit: Optional row limit
            
        Returns:
            DataFrame with query results
        """
        adapter = self._get_adapter(source_name)
        return await adapter.query(query, field_mappings, limit)
    
    async def get_schema(self, source_name: str, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Get schema for a data source (with caching).
        
        Args:
            source_name: Name of the registered data source
            force_refresh: Force refresh even if cached
            
        Returns:
            Schema information
        """
        # Check cache first
        if not force_refresh and self._is_cache_valid(source_name):
            return self._schema_cache[source_name]
        
        # Get fresh schema
        adapter = self._get_adapter(source_name)
        schema = await adapter.get_schema()
        
        # Update cache
        self._schema_cache[source_name] = schema
        self._cache_timestamps[source_name] = datetime.now()
        
        return schema
    
    async def preview_data(
        self,
        source_name: str,
        table_or_file: str,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Get a preview of data from a source.
        
        Args:
            source_name: Name of the registered data source
            table_or_file: Table name or file name to preview
            limit: Number of rows to return
            offset: Number of rows to skip
            
        Returns:
            Preview data with metadata
        """
        adapter = self._get_adapter(source_name)
        return await adapter.preview_data(table_or_file, limit, offset)
    
    async def test_connection(self, source_name: str) -> Dict[str, Any]:
        """Test connection to a data source."""
        adapter = self._get_adapter(source_name)
        return await adapter.test_connection()
    
    async def list_sources(self) -> Dict[str, Dict[str, Any]]:
        """
        List all registered data sources with their metadata.
        
        Returns:
            Dictionary of source names to metadata
        """
        sources = {}
        for name, adapter in self._adapters.items():
            sources[name] = {
                "type": self._adapter_types[name].value,
                "connected": True,  # All registered sources are connected
                "schema_cached": name in self._schema_cache,
                "cache_age": self._get_cache_age(name)
            }
        return sources
    
    async def get_available_files(self, source_name: str) -> List[str]:
        """
        Get list of available files for file-based sources.
        
        Args:
            source_name: Name of the registered data source
            
        Returns:
            List of file names
        """
        adapter = self._get_adapter(source_name)
        
        if hasattr(adapter, 'list_files'):
            return await adapter.list_files()
        else:
            # For database sources, return table names
            schema = await self.get_schema(source_name)
            if 'tables' in schema:
                return list(schema['tables'].keys())
            return []
    
    async def auto_discover_sources(self, study_id: str, base_data_path: str = "/data/studies") -> Dict[str, DataSourceType]:
        """
        Auto-discover data sources for a study.
        
        Args:
            study_id: Study identifier
            base_data_path: Base path for study data
            
        Returns:
            Dictionary of discovered source paths to types
        """
        discovered = {}
        study_path = Path(base_data_path) / study_id / "source_data"
        
        if not study_path.exists():
            return discovered
        
        # Look for data directories (usually organized by date)
        for date_dir in study_path.iterdir():
            if date_dir.is_dir():
                source_type = await self._detect_source_type(str(date_dir))
                if source_type != DataSourceType.UNKNOWN:
                    discovered[str(date_dir)] = source_type
        
        return discovered
    
    async def _detect_source_type(self, path: str) -> DataSourceType:
        """Auto-detect the type of data source based on path contents."""
        path_obj = Path(path)
        
        if not path_obj.exists():
            return DataSourceType.UNKNOWN
        
        if path_obj.is_dir():
            # Check for different file types
            files = list(path_obj.iterdir())
            
            # Count file types
            file_types = {
                'sas': len(list(path_obj.glob("*.sas7bdat"))) + len(list(path_obj.glob("*.xpt"))),
                'csv': len(list(path_obj.glob("*.csv"))),
                'parquet': len(list(path_obj.glob("*.parquet")))
            }
            
            # Return the most common type
            if file_types['sas'] > 0:
                return DataSourceType.SAS
            elif file_types['parquet'] > 0:
                return DataSourceType.PARQUET
            elif file_types['csv'] > 0:
                return DataSourceType.CSV
        
        return DataSourceType.UNKNOWN
    
    def _get_adapter(self, source_name: str) -> DataSourceAdapter:
        """Get adapter for a source, raising error if not found."""
        if source_name not in self._adapters:
            raise ValueError(f"Data source '{source_name}' not registered")
        return self._adapters[source_name]
    
    def _is_cache_valid(self, source_name: str) -> bool:
        """Check if cached schema is still valid."""
        if source_name not in self._schema_cache:
            return False
        
        timestamp = self._cache_timestamps.get(source_name)
        if not timestamp:
            return False
        
        return datetime.now() - timestamp < self.cache_ttl
    
    def _get_cache_age(self, source_name: str) -> Optional[str]:
        """Get human-readable cache age."""
        if source_name not in self._cache_timestamps:
            return None
        
        age = datetime.now() - self._cache_timestamps[source_name]
        
        if age.days > 0:
            return f"{age.days} days"
        elif age.seconds > 3600:
            return f"{age.seconds // 3600} hours"
        elif age.seconds > 60:
            return f"{age.seconds // 60} minutes"
        else:
            return f"{age.seconds} seconds"
    
    async def cleanup(self) -> None:
        """Clean up all resources."""
        async with self._lock:
            # Disconnect all adapters
            for adapter in self._adapters.values():
                if hasattr(adapter, 'disconnect'):
                    try:
                        await adapter.disconnect()
                    except Exception as e:
                        logger.error(f"Error disconnecting adapter: {e}")
            
            # Clear all registries
            self._adapters.clear()
            self._adapter_types.clear()
            self._schema_cache.clear()
            self._cache_timestamps.clear()


# Singleton instance
_data_source_manager: Optional[DataSourceManager] = None


def get_data_source_manager() -> DataSourceManager:
    """Get the singleton data source manager instance."""
    global _data_source_manager
    if _data_source_manager is None:
        _data_source_manager = DataSourceManager()
    return _data_source_manager