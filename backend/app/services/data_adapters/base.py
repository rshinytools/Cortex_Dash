# ABOUTME: Base adapter interface for data source adapters
# ABOUTME: Defines abstract methods for connecting to and querying various data sources

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
import pandas as pd
from pathlib import Path


class DataSourceAdapter(ABC):
    """Abstract base class for all data source adapters."""
    
    def __init__(self, connection_params: Dict[str, Any]):
        """
        Initialize the adapter with connection parameters.
        
        Args:
            connection_params: Dictionary containing connection-specific parameters
        """
        self.connection_params = connection_params
        self._connection = None
        self._schema_cache: Optional[Dict[str, Any]] = None
    
    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to the data source."""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection to the data source."""
        pass
    
    @abstractmethod
    async def query(
        self,
        query: Union[str, Dict[str, Any]],
        field_mappings: Optional[Dict[str, str]] = None,
        limit: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Execute a query against the data source.
        
        Args:
            query: Query string or structured query dict
            field_mappings: Optional field name mappings to apply
            limit: Optional row limit for the result
            
        Returns:
            DataFrame with query results
        """
        pass
    
    @abstractmethod
    async def get_schema(self) -> Dict[str, Any]:
        """
        Get the schema/structure of the data source.
        
        Returns:
            Dictionary containing schema information including:
            - tables/datasets available
            - columns and their data types
            - row counts if available
        """
        pass
    
    @abstractmethod
    async def preview_data(
        self,
        table_or_file: str,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Get a preview of data from a specific table or file.
        
        Args:
            table_or_file: Name of the table or file to preview
            limit: Number of rows to return
            offset: Number of rows to skip
            
        Returns:
            Dictionary containing:
            - data: List of dictionaries representing rows
            - columns: List of column definitions
            - total_rows: Total number of rows if available
        """
        pass
    
    @abstractmethod
    async def test_connection(self) -> Dict[str, Any]:
        """
        Test the connection to the data source.
        
        Returns:
            Dictionary containing:
            - success: Boolean indicating connection success
            - message: Description of the result
            - details: Additional connection details
        """
        pass
    
    def apply_field_mappings(
        self,
        df: pd.DataFrame,
        field_mappings: Dict[str, str]
    ) -> pd.DataFrame:
        """
        Apply field mappings to rename columns in the DataFrame.
        
        Args:
            df: Input DataFrame
            field_mappings: Dictionary mapping source fields to target fields
            
        Returns:
            DataFrame with renamed columns
        """
        if not field_mappings:
            return df
        
        # Only rename columns that exist in the DataFrame
        columns_to_rename = {
            old: new for old, new in field_mappings.items()
            if old in df.columns
        }
        
        return df.rename(columns=columns_to_rename)
    
    def _validate_limit(self, limit: Optional[int]) -> Optional[int]:
        """Validate and constrain limit parameter."""
        if limit is None:
            return None
        if limit <= 0:
            raise ValueError("Limit must be positive")
        # Cap at reasonable maximum to prevent memory issues
        return min(limit, 1000000)


class FileBasedAdapter(DataSourceAdapter):
    """Base class for file-based data adapters (SAS, CSV, Parquet)."""
    
    def __init__(self, connection_params: Dict[str, Any]):
        super().__init__(connection_params)
        self.base_path = Path(connection_params.get('base_path', ''))
        if not self.base_path.exists():
            raise ValueError(f"Base path does not exist: {self.base_path}")
    
    async def connect(self) -> None:
        """File-based adapters don't need persistent connections."""
        pass
    
    async def disconnect(self) -> None:
        """File-based adapters don't need to disconnect."""
        pass
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test access to the file system."""
        try:
            # Check if we can list files in the base path
            files = list(self.base_path.iterdir())
            return {
                "success": True,
                "message": f"Successfully accessed {self.base_path}",
                "details": {
                    "path": str(self.base_path),
                    "file_count": len(files),
                    "readable": self.base_path.is_dir() and os.access(self.base_path, os.R_OK)
                }
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to access path: {str(e)}",
                "details": {"error": str(e)}
            }
    
    def _get_file_path(self, filename: str) -> Path:
        """Get the full path for a file."""
        file_path = self.base_path / filename
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        return file_path
    
    @abstractmethod
    def _get_file_extension(self) -> str:
        """Get the file extension this adapter handles."""
        pass
    
    async def list_files(self) -> List[str]:
        """List all files of the appropriate type in the base path."""
        extension = self._get_file_extension()
        return [
            f.name for f in self.base_path.glob(f"**/*{extension}")
            if f.is_file()
        ]


import os