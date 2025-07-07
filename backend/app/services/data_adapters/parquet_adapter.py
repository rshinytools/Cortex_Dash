# ABOUTME: Parquet file adapter for efficient columnar data reading
# ABOUTME: Leverages pyarrow for fast parquet file operations

from typing import Any, Dict, List, Optional, Union
import pandas as pd
import pyarrow.parquet as pq
from pathlib import Path
import logging

from .base import FileBasedAdapter

logger = logging.getLogger(__name__)


class ParquetAdapter(FileBasedAdapter):
    """Adapter for reading Parquet files efficiently."""
    
    def _get_file_extension(self) -> str:
        """Parquet files have .parquet extension."""
        return ".parquet"
    
    async def query(
        self,
        query: Union[str, Dict[str, Any]],
        field_mappings: Optional[Dict[str, str]] = None,
        limit: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Read data from a Parquet file.
        
        For Parquet files, the query should be either:
        - A string with the filename
        - A dict with 'file' key and optional 'columns' list and 'filters' list
        
        Filters should be in the format: [('column', 'operator', value)]
        Where operator can be: '=', '!=', '<', '>', '<=', '>=', 'in', 'not in'
        """
        if isinstance(query, str):
            filename = query
            columns = None
            filters = None
        else:
            filename = query.get('file')
            columns = query.get('columns')
            filters = query.get('filters')
            
        if not filename:
            raise ValueError("Filename is required for Parquet adapter")
        
        file_path = self._get_file_path(filename)
        
        try:
            # Parquet files support efficient column selection and filtering
            # Use pyarrow for better performance
            if columns or filters:
                # Use pyarrow's read_parquet for column/filter pushdown
                table = pq.read_table(
                    file_path,
                    columns=columns,
                    filters=filters
                )
                df = table.to_pandas()
            else:
                # Simple read without filters
                df = pd.read_parquet(file_path, engine='pyarrow')
            
            # Apply field mappings
            if field_mappings:
                df = self.apply_field_mappings(df, field_mappings)
            
            # Apply limit
            if limit:
                limit = self._validate_limit(limit)
                df = df.head(limit)
            
            return df
            
        except Exception as e:
            logger.error(f"Error reading Parquet file {filename}: {str(e)}")
            raise
    
    async def get_schema(self) -> Dict[str, Any]:
        """Get schema information for all Parquet files."""
        if self._schema_cache:
            return self._schema_cache
        
        schema = {"files": {}}
        
        # Find all Parquet files
        parquet_files = list(self.base_path.glob("**/*.parquet"))
        
        for file_path in parquet_files:
            try:
                # Use pyarrow to read metadata efficiently
                parquet_file = pq.ParquetFile(file_path)
                metadata = parquet_file.metadata
                arrow_schema = parquet_file.schema_arrow
                
                # Build column info
                columns = []
                for i, field in enumerate(arrow_schema):
                    # Get column statistics if available
                    col_stats = self._get_column_stats(parquet_file, i)
                    
                    columns.append({
                        "name": field.name,
                        "type": self._map_arrow_type_to_generic(field.type),
                        "arrow_type": str(field.type),
                        "nullable": field.nullable,
                        "metadata": field.metadata,
                        **col_stats
                    })
                
                # Get file-level metadata
                relative_path = file_path.relative_to(self.base_path)
                schema["files"][str(relative_path)] = {
                    "columns": columns,
                    "row_count": metadata.num_rows,
                    "row_groups": metadata.num_row_groups,
                    "file_size": file_path.stat().st_size,
                    "created_by": metadata.created_by if hasattr(metadata, 'created_by') else None,
                    "format_version": str(metadata.format_version) if hasattr(metadata, 'format_version') else None,
                    "serialized_size": metadata.serialized_size,
                    "compression": self._get_compression_info(parquet_file)
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
        """Get a preview of data from a Parquet file."""
        file_path = self._get_file_path(table_or_file)
        
        try:
            # For efficient preview with offset, we'll use pyarrow
            parquet_file = pq.ParquetFile(file_path)
            
            # Get total rows
            total_rows = parquet_file.metadata.num_rows
            
            # Calculate which row groups to read
            rows_per_group = []
            for i in range(parquet_file.metadata.num_row_groups):
                rows_per_group.append(parquet_file.metadata.row_group(i).num_rows)
            
            # Find which row groups contain our desired range
            row_groups_to_read = []
            current_row = 0
            
            for i, group_rows in enumerate(rows_per_group):
                if current_row + group_rows > offset:
                    row_groups_to_read.append(i)
                    if current_row + group_rows >= offset + limit:
                        break
                current_row += group_rows
            
            # Read only necessary row groups
            if row_groups_to_read:
                table = parquet_file.read_row_groups(row_groups_to_read)
                df = table.to_pandas()
                
                # Apply offset and limit within the dataframe
                start_idx = offset - sum(rows_per_group[:row_groups_to_read[0]])
                end_idx = start_idx + limit
                df_preview = df.iloc[start_idx:end_idx]
            else:
                df_preview = pd.DataFrame()
            
            # Convert to list of dicts for JSON serialization
            data = df_preview.to_dict('records')
            
            # Build column info
            columns = []
            arrow_schema = parquet_file.schema_arrow
            for i, field in enumerate(arrow_schema):
                col_stats = self._get_column_stats(parquet_file, i)
                columns.append({
                    "name": field.name,
                    "type": self._map_arrow_type_to_generic(field.type),
                    "arrow_type": str(field.type),
                    "nullable": field.nullable,
                    **col_stats
                })
            
            return {
                "data": data,
                "columns": columns,
                "total_rows": total_rows,
                "offset": offset,
                "limit": limit,
                "row_groups": parquet_file.metadata.num_row_groups,
                "compression": self._get_compression_info(parquet_file)
            }
            
        except Exception as e:
            logger.error(f"Error previewing Parquet file {table_or_file}: {str(e)}")
            raise
    
    def _get_column_stats(self, parquet_file: pq.ParquetFile, column_index: int) -> Dict[str, Any]:
        """Extract column statistics from parquet metadata."""
        stats = {}
        
        try:
            # Get statistics from first row group
            if parquet_file.metadata.num_row_groups > 0:
                row_group = parquet_file.metadata.row_group(0)
                if column_index < row_group.num_columns:
                    col_meta = row_group.column(column_index)
                    if col_meta.statistics:
                        stats_obj = col_meta.statistics
                        if hasattr(stats_obj, 'min') and stats_obj.min is not None:
                            stats['min_value'] = stats_obj.min
                        if hasattr(stats_obj, 'max') and stats_obj.max is not None:
                            stats['max_value'] = stats_obj.max
                        if hasattr(stats_obj, 'null_count'):
                            stats['null_count'] = stats_obj.null_count
                        if hasattr(stats_obj, 'distinct_count') and stats_obj.distinct_count is not None:
                            stats['distinct_count'] = stats_obj.distinct_count
        except Exception as e:
            logger.debug(f"Could not extract column statistics: {e}")
        
        return stats
    
    def _get_compression_info(self, parquet_file: pq.ParquetFile) -> Optional[str]:
        """Get compression codec used in the parquet file."""
        try:
            if parquet_file.metadata.num_row_groups > 0:
                row_group = parquet_file.metadata.row_group(0)
                if row_group.num_columns > 0:
                    col_meta = row_group.column(0)
                    return col_meta.compression
        except Exception:
            pass
        return None
    
    def _map_arrow_type_to_generic(self, arrow_type) -> str:
        """Map PyArrow data type to generic type name."""
        type_str = str(arrow_type).lower()
        
        if 'int' in type_str or 'uint' in type_str:
            return 'integer'
        elif 'float' in type_str or 'double' in type_str or 'decimal' in type_str:
            return 'numeric'
        elif 'bool' in type_str:
            return 'boolean'
        elif 'timestamp' in type_str or 'date' in type_str or 'time' in type_str:
            return 'datetime'
        elif 'string' in type_str or 'utf8' in type_str or 'large_string' in type_str:
            return 'text'
        elif 'binary' in type_str or 'large_binary' in type_str:
            return 'binary'
        elif 'list' in type_str or 'array' in type_str:
            return 'array'
        elif 'struct' in type_str:
            return 'struct'
        elif 'map' in type_str:
            return 'map'
        else:
            return 'unknown'