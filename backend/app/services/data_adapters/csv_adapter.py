# ABOUTME: CSV file adapter for reading CSV files with type inference
# ABOUTME: Handles various CSV formats with automatic delimiter detection

from typing import Any, Dict, List, Optional, Union
import pandas as pd
from pathlib import Path
import logging
import csv

from .base import FileBasedAdapter

logger = logging.getLogger(__name__)


class CSVAdapter(FileBasedAdapter):
    """Adapter for reading CSV files with automatic type inference."""
    
    def _get_file_extension(self) -> str:
        """CSV files have .csv extension."""
        return ".csv"
    
    def _detect_delimiter(self, file_path: Path, sample_size: int = 1024) -> str:
        """Detect the delimiter used in a CSV file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                sample = f.read(sample_size)
                sniffer = csv.Sniffer()
                delimiter = sniffer.sniff(sample).delimiter
                return delimiter
        except Exception:
            # Default to comma if detection fails
            return ','
    
    def _get_csv_params(self, file_path: Path) -> Dict[str, Any]:
        """Get optimal parameters for reading the CSV file."""
        delimiter = self._detect_delimiter(file_path)
        
        # Base parameters
        params = {
            'sep': delimiter,
            'encoding': 'utf-8',
            'low_memory': False,
            'parse_dates': True,
            'infer_datetime_format': True,
            'keep_default_na': True,
            'na_values': ['', 'NA', 'N/A', 'null', 'NULL', 'None', 'NONE', '.', ' ']
        }
        
        # Try to detect if there's a header
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
                # Simple heuristic: if first line contains non-numeric values, it's likely a header
                fields = first_line.split(delimiter)
                has_header = any(not self._is_numeric(field.strip('"')) for field in fields)
                params['header'] = 0 if has_header else None
        except Exception:
            params['header'] = 0  # Default to having header
        
        return params
    
    def _is_numeric(self, value: str) -> bool:
        """Check if a string value is numeric."""
        try:
            float(value)
            return True
        except ValueError:
            return False
    
    async def query(
        self,
        query: Union[str, Dict[str, Any]],
        field_mappings: Optional[Dict[str, str]] = None,
        limit: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Read data from a CSV file.
        
        For CSV files, the query should be either:
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
            raise ValueError("Filename is required for CSV adapter")
        
        file_path = self._get_file_path(filename)
        
        try:
            # Get CSV parameters
            csv_params = self._get_csv_params(file_path)
            
            # Add column selection if specified
            if columns:
                csv_params['usecols'] = columns
            
            # Add row limit if specified
            if limit:
                limit = self._validate_limit(limit)
                csv_params['nrows'] = limit
            
            # Read CSV file
            df = pd.read_csv(file_path, **csv_params)
            
            # Apply field mappings
            if field_mappings:
                df = self.apply_field_mappings(df, field_mappings)
            
            return df
            
        except Exception as e:
            logger.error(f"Error reading CSV file {filename}: {str(e)}")
            raise
    
    async def get_schema(self) -> Dict[str, Any]:
        """Get schema information for all CSV files."""
        if self._schema_cache:
            return self._schema_cache
        
        schema = {"files": {}}
        
        # Find all CSV files
        csv_files = list(self.base_path.glob("**/*.csv"))
        
        for file_path in csv_files:
            try:
                # Get CSV parameters
                csv_params = self._get_csv_params(file_path)
                
                # Read just first few rows to infer schema
                df_sample = pd.read_csv(file_path, **{**csv_params, 'nrows': 1000})
                
                # Get row count efficiently
                with open(file_path, 'r', encoding='utf-8') as f:
                    row_count = sum(1 for _ in f) - (1 if csv_params.get('header') == 0 else 0)
                
                # Build column info
                columns = []
                for col in df_sample.columns:
                    # Infer better data types
                    sample_col = df_sample[col]
                    inferred_type = self._infer_column_type(sample_col)
                    
                    columns.append({
                        "name": col,
                        "type": inferred_type,
                        "pandas_dtype": str(sample_col.dtype),
                        "nullable": sample_col.isnull().any(),
                        "unique_values": int(sample_col.nunique()) if len(sample_col) > 0 else 0
                    })
                
                relative_path = file_path.relative_to(self.base_path)
                schema["files"][str(relative_path)] = {
                    "columns": columns,
                    "row_count": row_count,
                    "file_size": file_path.stat().st_size,
                    "delimiter": csv_params['sep'],
                    "has_header": csv_params.get('header') == 0
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
        """Get a preview of data from a CSV file."""
        file_path = self._get_file_path(table_or_file)
        
        try:
            # Get CSV parameters
            csv_params = self._get_csv_params(file_path)
            
            # Read with skiprows for offset
            if offset > 0:
                csv_params['skiprows'] = range(1, offset + 1) if csv_params.get('header') == 0 else range(offset)
            csv_params['nrows'] = limit
            
            df_preview = pd.read_csv(file_path, **csv_params)
            
            # Get total row count
            with open(file_path, 'r', encoding='utf-8') as f:
                total_rows = sum(1 for _ in f) - (1 if csv_params.get('header') == 0 else 0)
            
            # Convert to list of dicts for JSON serialization
            data = df_preview.to_dict('records')
            
            # Build column info with better type inference
            columns = []
            for col in df_preview.columns:
                inferred_type = self._infer_column_type(df_preview[col])
                columns.append({
                    "name": col,
                    "type": inferred_type,
                    "pandas_dtype": str(df_preview[col].dtype),
                    "sample_values": df_preview[col].dropna().head(5).tolist() if len(df_preview) > 0 else []
                })
            
            return {
                "data": data,
                "columns": columns,
                "total_rows": total_rows,
                "offset": offset,
                "limit": limit,
                "delimiter": csv_params['sep']
            }
            
        except Exception as e:
            logger.error(f"Error previewing CSV file {table_or_file}: {str(e)}")
            raise
    
    def _infer_column_type(self, series: pd.Series) -> str:
        """Infer the data type of a pandas Series."""
        # Remove null values for type inference
        non_null = series.dropna()
        
        if len(non_null) == 0:
            return 'unknown'
        
        dtype_str = str(series.dtype).lower()
        
        # Check for datetime
        if 'datetime' in dtype_str:
            return 'datetime'
        
        # Check for boolean
        if dtype_str == 'bool' or (set(non_null.unique()) <= {True, False, 1, 0, '1', '0', 'true', 'false', 'True', 'False'}):
            return 'boolean'
        
        # Check for integer
        if 'int' in dtype_str:
            return 'integer'
        
        # Check for float
        if 'float' in dtype_str:
            return 'numeric'
        
        # For object types, do more checking
        if dtype_str == 'object':
            # Sample some values
            sample_values = non_null.head(100)
            
            # Check if all values are numeric strings
            numeric_count = sum(1 for v in sample_values if isinstance(v, str) and self._is_numeric(v))
            if numeric_count == len(sample_values):
                # Check if they're all integers
                int_count = sum(1 for v in sample_values if isinstance(v, str) and '.' not in v and self._is_numeric(v))
                if int_count == len(sample_values):
                    return 'integer'
                return 'numeric'
            
            # Check if values look like dates
            try:
                pd.to_datetime(sample_values, errors='coerce')
                parsed_dates = pd.to_datetime(sample_values, errors='coerce')
                if parsed_dates.notna().sum() > len(sample_values) * 0.8:
                    return 'datetime'
            except Exception:
                pass
            
            return 'text'
        
        return 'unknown'