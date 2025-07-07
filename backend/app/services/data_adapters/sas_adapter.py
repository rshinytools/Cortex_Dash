# ABOUTME: SAS file adapter for reading SAS7BDAT and XPT files
# ABOUTME: Uses pandas to read SAS files with proper type handling

from typing import Any, Dict, List, Optional, Union
import pandas as pd
from pathlib import Path
import logging

from .base import FileBasedAdapter

logger = logging.getLogger(__name__)


class SASAdapter(FileBasedAdapter):
    """Adapter for reading SAS files (SAS7BDAT and XPT formats)."""
    
    def _get_file_extension(self) -> str:
        """SAS files can have .sas7bdat or .xpt extensions."""
        return ".sas7bdat"  # Primary extension
    
    async def query(
        self,
        query: Union[str, Dict[str, Any]],
        field_mappings: Optional[Dict[str, str]] = None,
        limit: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Read data from a SAS file.
        
        For SAS files, the query should be either:
        - A string with the filename
        - A dict with 'file' key and optional 'columns' list
        """
        if isinstance(query, str):
            filename = query
            columns = None
        else:
            filename = query.get('file')
            columns = query.get('columns')
            
        if not filename:
            raise ValueError("Filename is required for SAS adapter")
        
        file_path = self._get_file_path(filename)
        
        try:
            # Read SAS file
            if file_path.suffix.lower() == '.xpt':
                df = pd.read_sas(file_path, format='xport', encoding='utf-8')
            else:
                df = pd.read_sas(file_path, encoding='utf-8')
            
            # Select specific columns if requested
            if columns:
                available_columns = [col for col in columns if col in df.columns]
                if not available_columns:
                    raise ValueError(f"None of the requested columns found in file: {columns}")
                df = df[available_columns]
            
            # Apply field mappings
            if field_mappings:
                df = self.apply_field_mappings(df, field_mappings)
            
            # Apply limit
            if limit:
                limit = self._validate_limit(limit)
                df = df.head(limit)
            
            return df
            
        except Exception as e:
            logger.error(f"Error reading SAS file {filename}: {str(e)}")
            raise
    
    async def get_schema(self) -> Dict[str, Any]:
        """Get schema information for all SAS files."""
        if self._schema_cache:
            return self._schema_cache
        
        schema = {"files": {}}
        
        # Find all SAS files
        sas_files = list(self.base_path.glob("**/*.sas7bdat"))
        sas_files.extend(list(self.base_path.glob("**/*.xpt")))
        
        for file_path in sas_files:
            try:
                # Read just the first row to get column info
                if file_path.suffix.lower() == '.xpt':
                    df_sample = pd.read_sas(file_path, format='xport', encoding='utf-8', chunksize=1)
                else:
                    df_sample = pd.read_sas(file_path, encoding='utf-8', chunksize=1)
                
                # Get first chunk
                for chunk in df_sample:
                    df_first = chunk
                    break
                
                # Get full row count (this is efficient for SAS files)
                if file_path.suffix.lower() == '.xpt':
                    df_info = pd.read_sas(file_path, format='xport', encoding='utf-8', iterator=True)
                else:
                    df_info = pd.read_sas(file_path, encoding='utf-8', iterator=True)
                
                row_count = 0
                for chunk in df_info:
                    row_count += len(chunk)
                
                # Build column info
                columns = []
                for col in df_first.columns:
                    dtype = str(df_first[col].dtype)
                    columns.append({
                        "name": col,
                        "type": self._map_dtype_to_generic(dtype),
                        "pandas_dtype": dtype,
                        "nullable": df_first[col].isnull().any()
                    })
                
                relative_path = file_path.relative_to(self.base_path)
                schema["files"][str(relative_path)] = {
                    "columns": columns,
                    "row_count": row_count,
                    "file_size": file_path.stat().st_size,
                    "format": "xport" if file_path.suffix.lower() == '.xpt' else "sas7bdat"
                }
                
            except Exception as e:
                logger.warning(f"Error reading schema from {file_path}: {str(e)}")
                schema["files"][str(file_path.relative_to(self.base_path))] = {
                    "error": str(e)
                }
        
        self._schema_cache = schema
        return schema
    
    async def preview_data(
        self,
        table_or_file: str,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Get a preview of data from a SAS file."""
        file_path = self._get_file_path(table_or_file)
        
        try:
            # For preview, we'll read the file in chunks to handle offset efficiently
            if file_path.suffix.lower() == '.xpt':
                reader = pd.read_sas(file_path, format='xport', encoding='utf-8', chunksize=limit)
            else:
                reader = pd.read_sas(file_path, encoding='utf-8', chunksize=limit)
            
            # Skip to the offset
            rows_skipped = 0
            df_preview = None
            
            for chunk in reader:
                if rows_skipped + len(chunk) <= offset:
                    rows_skipped += len(chunk)
                    continue
                
                # We've reached the offset
                start_row = offset - rows_skipped
                end_row = start_row + limit
                df_preview = chunk.iloc[start_row:end_row]
                break
            
            if df_preview is None or df_preview.empty:
                # Offset is beyond the file
                df_preview = pd.DataFrame()
            
            # Get total row count
            total_rows = 0
            if file_path.suffix.lower() == '.xpt':
                counter = pd.read_sas(file_path, format='xport', encoding='utf-8', iterator=True)
            else:
                counter = pd.read_sas(file_path, encoding='utf-8', iterator=True)
            
            for chunk in counter:
                total_rows += len(chunk)
            
            # Convert to list of dicts for JSON serialization
            data = df_preview.to_dict('records') if not df_preview.empty else []
            
            # Build column info
            columns = []
            if not df_preview.empty:
                for col in df_preview.columns:
                    columns.append({
                        "name": col,
                        "type": self._map_dtype_to_generic(str(df_preview[col].dtype)),
                        "pandas_dtype": str(df_preview[col].dtype)
                    })
            
            return {
                "data": data,
                "columns": columns,
                "total_rows": total_rows,
                "offset": offset,
                "limit": limit
            }
            
        except Exception as e:
            logger.error(f"Error previewing SAS file {table_or_file}: {str(e)}")
            raise
    
    async def list_files(self) -> List[str]:
        """List all SAS files (both .sas7bdat and .xpt)."""
        files = []
        
        # Find .sas7bdat files
        files.extend([
            str(f.relative_to(self.base_path))
            for f in self.base_path.glob("**/*.sas7bdat")
            if f.is_file()
        ])
        
        # Find .xpt files
        files.extend([
            str(f.relative_to(self.base_path))
            for f in self.base_path.glob("**/*.xpt")
            if f.is_file()
        ])
        
        return sorted(files)
    
    def _map_dtype_to_generic(self, dtype: str) -> str:
        """Map pandas dtype to generic type name."""
        dtype_lower = dtype.lower()
        
        if 'int' in dtype_lower:
            return 'integer'
        elif 'float' in dtype_lower or 'double' in dtype_lower:
            return 'numeric'
        elif 'bool' in dtype_lower:
            return 'boolean'
        elif 'datetime' in dtype_lower or 'date' in dtype_lower:
            return 'datetime'
        elif 'object' in dtype_lower or 'string' in dtype_lower:
            return 'text'
        else:
            return 'unknown'