# ABOUTME: Service for converting various file formats to parquet
# ABOUTME: Handles CSV, SAS7BDAT, XPT, XLSX to parquet conversion with data profiling

import os
import zipfile
import shutil
import json

try:
    import pandas as pd
    import pyarrow as pa
    import pyarrow.parquet as pq
except ImportError:
    pd = None
    pa = None
    pq = None

try:
    import pyreadstat
except ImportError:
    pyreadstat = None

from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Callable, Awaitable
from datetime import datetime
import logging
from dataclasses import dataclass
import aiofiles
import asyncio
import uuid

from app.clinical_modules.utils.folder_structure import (
    get_study_data_path,
    ensure_folder_exists,
    get_timestamp_folder
)

logger = logging.getLogger(__name__)


@dataclass
class ConversionResult:
    """Result of file conversion process"""
    success: bool
    files_extracted: List[Dict[str, Any]]
    total_rows: int
    total_columns: int
    error_message: Optional[str] = None
    warnings: Optional[List[str]] = None


class FileConversionService:
    """Service for converting clinical data files to parquet format"""
    
    SUPPORTED_FORMATS = {
        '.csv': 'read_csv',
        '.sas7bdat': 'read_sas',
        '.xpt': 'read_sas',
        '.xlsx': 'read_excel',
        '.xls': 'read_excel'
    }
    
    def __init__(self):
        self.warnings = []
    
    async def process_upload(
        self,
        upload_id: str,
        file_path: str,
        output_path: str,
        file_format: str
    ) -> ConversionResult:
        """
        Process an uploaded file and convert to parquet.
        """
        self.warnings = []
        files_extracted = []
        total_rows = 0
        total_columns = 0
        
        try:
            # Handle ZIP files
            if file_format.lower() == 'zip':
                return await self._process_zip_file(file_path, output_path)
            else:
                # Process single file
                return await self._process_single_file(file_path, output_path, file_format)
                
        except Exception as e:
            logger.error(f"Failed to process upload {upload_id}: {str(e)}")
            return ConversionResult(
                success=False,
                files_extracted=[],
                total_rows=0,
                total_columns=0,
                error_message=str(e),
                warnings=self.warnings
            )
    
    async def _process_zip_file(self, zip_path: str, output_path: str) -> ConversionResult:
        """Extract and process files from a ZIP archive."""
        files_extracted = []
        total_rows = 0
        total_columns = 0
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_file:
                # Extract all files
                extract_path = Path(output_path).parent / "extracted"
                extract_path.mkdir(exist_ok=True)
                zip_file.extractall(extract_path)
                
                # Process each file
                for file_name in zip_file.namelist():
                    if file_name.endswith('/'):  # Skip directories
                        continue
                    
                    file_path = extract_path / file_name
                    file_extension = Path(file_name).suffix.lower()
                    
                    if file_extension in self.SUPPORTED_FORMATS:
                        try:
                            # Convert to parquet
                            dataset_name = Path(file_name).stem
                            parquet_path = Path(output_path) / f"{dataset_name}.parquet"
                            
                            df = await self._read_file(str(file_path), file_extension)
                            
                            if df is not None and not df.empty:
                                # Save as parquet
                                await self._save_parquet(df, str(parquet_path))
                                
                                # Collect metadata
                                file_info = {
                                    "name": file_name,
                                    "dataset_name": dataset_name,
                                    "format": file_extension[1:],
                                    "size_mb": file_path.stat().st_size / (1024 * 1024),
                                    "rows": len(df),
                                    "columns": len(df.columns),
                                    "column_info": self._get_column_info(df),
                                    "parquet_path": str(parquet_path)
                                }
                                
                                files_extracted.append(file_info)
                                total_rows += len(df)
                                total_columns = max(total_columns, len(df.columns))
                            else:
                                self.warnings.append(f"File {file_name} is empty or could not be read")
                                
                        except Exception as e:
                            self.warnings.append(f"Failed to process {file_name}: {str(e)}")
                    else:
                        self.warnings.append(f"Unsupported file format: {file_name}")
                
                # Clean up extracted files
                import shutil
                shutil.rmtree(extract_path)
                
            return ConversionResult(
                success=True,
                files_extracted=files_extracted,
                total_rows=total_rows,
                total_columns=total_columns,
                warnings=self.warnings if self.warnings else None
            )
            
        except Exception as e:
            return ConversionResult(
                success=False,
                files_extracted=[],
                total_rows=0,
                total_columns=0,
                error_message=f"Failed to process ZIP file: {str(e)}",
                warnings=self.warnings
            )
    
    async def _process_single_file(
        self, 
        file_path: str, 
        output_path: str, 
        file_format: str
    ) -> ConversionResult:
        """Process a single data file."""
        try:
            file_extension = f".{file_format.lower()}"
            if file_extension not in self.SUPPORTED_FORMATS:
                return ConversionResult(
                    success=False,
                    files_extracted=[],
                    total_rows=0,
                    total_columns=0,
                    error_message=f"Unsupported file format: {file_format}"
                )
            
            # Read the file
            df = await self._read_file(file_path, file_extension)
            
            if df is None or df.empty:
                return ConversionResult(
                    success=False,
                    files_extracted=[],
                    total_rows=0,
                    total_columns=0,
                    error_message="File is empty or could not be read"
                )
            
            # Save as parquet
            dataset_name = Path(file_path).stem
            parquet_path = Path(output_path) / f"{dataset_name}.parquet"
            await self._save_parquet(df, str(parquet_path))
            
            # Collect metadata
            file_info = {
                "name": Path(file_path).name,
                "dataset_name": dataset_name,
                "format": file_format,
                "size_mb": Path(file_path).stat().st_size / (1024 * 1024),
                "rows": len(df),
                "columns": len(df.columns),
                "column_info": self._get_column_info(df),
                "parquet_path": str(parquet_path)
            }
            
            return ConversionResult(
                success=True,
                files_extracted=[file_info],
                total_rows=len(df),
                total_columns=len(df.columns),
                warnings=self.warnings if self.warnings else None
            )
            
        except Exception as e:
            return ConversionResult(
                success=False,
                files_extracted=[],
                total_rows=0,
                total_columns=0,
                error_message=str(e),
                warnings=self.warnings
            )
    
    async def _read_file(self, file_path: str, file_extension: str) -> Optional[pd.DataFrame]:
        """Read a file into a pandas DataFrame."""
        try:
            method_name = self.SUPPORTED_FORMATS.get(file_extension)
            if not method_name:
                return None
            
            # Run pandas read operation in thread pool
            loop = asyncio.get_event_loop()
            
            if method_name == 'read_csv':
                df = await loop.run_in_executor(
                    None, 
                    lambda: pd.read_csv(file_path, encoding='utf-8', low_memory=False)
                )
            elif method_name == 'read_sas':
                df = await loop.run_in_executor(
                    None,
                    lambda: pd.read_sas(file_path, encoding='utf-8')
                )
            elif method_name == 'read_excel':
                df = await loop.run_in_executor(
                    None,
                    lambda: pd.read_excel(file_path)
                )
            else:
                return None
            
            # Clean column names
            df.columns = [self._clean_column_name(col) for col in df.columns]
            
            # Convert date columns
            df = self._convert_date_columns(df)
            
            return df
            
        except UnicodeDecodeError:
            # Try with different encoding
            if method_name == 'read_csv':
                try:
                    loop = asyncio.get_event_loop()
                    df = await loop.run_in_executor(
                        None,
                        lambda: pd.read_csv(file_path, encoding='latin-1', low_memory=False)
                    )
                    self.warnings.append(f"File {file_path} read with latin-1 encoding")
                    return df
                except Exception as e:
                    logger.error(f"Failed to read file with alternative encoding: {str(e)}")
                    return None
            return None
        except Exception as e:
            logger.error(f"Failed to read file {file_path}: {str(e)}")
            return None
    
    async def _save_parquet(self, df: pd.DataFrame, output_path: str):
        """Save DataFrame as parquet file."""
        try:
            # Convert to pyarrow table
            table = pa.Table.from_pandas(df)
            
            # Write parquet file with compression
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: pq.write_table(
                    table, 
                    output_path,
                    compression='snappy',
                    use_dictionary=True,
                    row_group_size=50000
                )
            )
            
        except Exception as e:
            logger.error(f"Failed to save parquet file: {str(e)}")
            raise
    
    def _clean_column_name(self, col_name: str) -> str:
        """Clean column name for parquet compatibility."""
        # Remove special characters and spaces
        import re
        cleaned = re.sub(r'[^\w\s]', '', str(col_name))
        cleaned = cleaned.strip().replace(' ', '_')
        return cleaned if cleaned else f"column_{hash(col_name)}"
    
    def _convert_date_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Attempt to convert date columns to datetime."""
        for col in df.columns:
            if df[col].dtype == 'object':
                # Try to convert to datetime
                try:
                    # Check if it looks like a date
                    sample = df[col].dropna().head(10)
                    if sample.empty:
                        continue
                    
                    # Common date patterns
                    date_patterns = ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%Y%m%d']
                    
                    for pattern in date_patterns:
                        try:
                            df[col] = pd.to_datetime(df[col], format=pattern, errors='coerce')
                            if df[col].notna().sum() > len(df) * 0.5:  # If more than 50% converted successfully
                                break
                        except:
                            continue
                            
                except Exception:
                    pass
        
        return df
    
    def _get_column_info(self, df: pd.DataFrame) -> List[Dict[str, str]]:
        """Get column information from DataFrame."""
        columns = []
        for col in df.columns:
            dtype = str(df[col].dtype)
            
            # Simplify dtype names
            if 'int' in dtype:
                dtype_simple = 'integer'
            elif 'float' in dtype:
                dtype_simple = 'numeric'
            elif 'datetime' in dtype:
                dtype_simple = 'datetime'
            elif 'bool' in dtype:
                dtype_simple = 'boolean'
            else:
                dtype_simple = 'string'
            
            columns.append({
                "name": col,
                "type": dtype_simple,
                "nullable": df[col].isna().any()
            })
        
        return columns
    
    async def convert_study_files(
        self,
        org_id: uuid.UUID,
        study_id: uuid.UUID,
        files: List[Dict[str, Any]],
        progress_callback: Optional[Callable[[int, Optional[str]], Awaitable[None]]] = None
    ) -> Dict[str, Any]:
        """
        Convert multiple study files to parquet with progress tracking
        
        Args:
            org_id: Organization ID
            study_id: The study ID
            files: List of file information dictionaries
            progress_callback: Async callback for progress updates
            
        Returns:
            Comprehensive results including datasets, converted files, and folder information
        """
        results = {
            "org_id": str(org_id),
            "study_id": str(study_id),
            "timestamp": get_timestamp_folder(),
            "processed_at": datetime.utcnow().isoformat(),
            "datasets": {},
            "converted_files": [],
            "errors": [],
            "warnings": []
        }
        
        # Use the folder where files are already uploaded (extract from first file path)
        # Files are already in the correct location, we just need to convert them to parquet
        if files and files[0].get("path"):
            # Extract the existing path from the first file
            first_file_path = Path(files[0]["path"])
            target_path = first_file_path.parent  # Use the existing folder
        else:
            # Fallback to creating new path if no files
            target_path = get_study_data_path(org_id, study_id, results["timestamp"])
            ensure_folder_exists(target_path)
        
        # Track progress
        total_steps = len(files) * 3  # Extract, convert, schema for each file
        current_step = 0
        
        async def update_progress(message: str):
            nonlocal current_step
            current_step += 1
            if progress_callback:
                percent = int((current_step / total_steps) * 100)
                await progress_callback(percent, message)
        
        # Process each uploaded file
        for file_info in files:
            try:
                file_path = Path(file_info["path"])
                if not file_path.exists():
                    results["errors"].append(f"File not found: {file_info['name']}")
                    continue
                
                # Step 1: Extract if ZIP
                if file_path.suffix.lower() == '.zip':
                    await update_progress(f"Extracting {file_info['name']}...")
                    extracted_files = await self._extract_zip_file_v2(file_path, target_path)
                    
                    # Process each extracted file
                    for extracted_file in extracted_files:
                        if extracted_file.suffix.lower() in self.SUPPORTED_FORMATS:
                            await update_progress(f"Converting {extracted_file.name} to parquet...")
                            parquet_path = await self._convert_to_parquet_v2(extracted_file, target_path)
                            
                            if parquet_path:
                                await update_progress(f"Extracting schema from {parquet_path.name}...")
                                schema_info = await self._extract_parquet_schema_v2(parquet_path)
                                dataset_name = parquet_path.stem.lower()
                                results["datasets"][dataset_name] = schema_info
                                results["converted_files"].append({
                                    "original": str(extracted_file),
                                    "parquet": str(parquet_path),
                                    "dataset": dataset_name
                                })
                else:
                    # Step 2: Convert to parquet
                    await update_progress(f"Converting {file_info['name']} to parquet...")
                    
                    # Files are already in the correct location (uploaded to source_data folder)
                    # Just convert them in place
                    parquet_path = await self._convert_to_parquet_v2(file_path, file_path.parent)
                    
                    if parquet_path:
                        # Step 3: Extract schema
                        await update_progress(f"Extracting schema from {parquet_path.name}...")
                        schema_info = await self._extract_parquet_schema_v2(parquet_path)
                        dataset_name = parquet_path.stem.lower()
                        results["datasets"][dataset_name] = schema_info
                        results["converted_files"].append({
                            "original": str(file_path),
                            "parquet": str(parquet_path),
                            "dataset": dataset_name
                        })
                        
            except Exception as e:
                logger.error(f"Error processing file {file_info['name']}: {str(e)}")
                results["errors"].append(f"Failed to process {file_info['name']}: {str(e)}")
        
        # Final progress update
        if progress_callback:
            await progress_callback(100, "Processing complete")
        
        # Add summary statistics
        results["summary"] = {
            "total_files_uploaded": len(files),
            "total_datasets_created": len(results["datasets"]),
            "total_files_converted": len(results["converted_files"]),
            "data_folder": str(target_path),
            "has_errors": len(results["errors"]) > 0
        }
        
        # Merge warnings from self.warnings
        if self.warnings:
            results["warnings"].extend(self.warnings)
        
        return results
    
    async def _extract_zip_file_v2(self, zip_path: Path, target_dir: Path) -> List[Path]:
        """Extract ZIP file and return list of extracted files"""
        extracted_files = []
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Extract to temporary folder first
                temp_extract = target_dir / f"_temp_extract_{zip_path.stem}"
                temp_extract.mkdir(exist_ok=True)
                
                zip_ref.extractall(temp_extract)
                
                # Move files to target directory (flattening structure)
                for item in temp_extract.rglob('*'):
                    if item.is_file() and not item.name.startswith('.'):
                        # Skip hidden files and non-data files
                        if item.suffix.lower() in ['.csv', '.xlsx', '.xls', '.sas7bdat', '.xpt']:
                            target_file = target_dir / item.name
                            
                            # Handle duplicate names
                            if target_file.exists():
                                base = target_file.stem
                                ext = target_file.suffix
                                counter = 1
                                while target_file.exists():
                                    target_file = target_dir / f"{base}_{counter}{ext}"
                                    counter += 1
                            
                            shutil.move(str(item), str(target_file))
                            extracted_files.append(target_file)
                
                # Clean up temp directory
                shutil.rmtree(temp_extract)
                
        except Exception as e:
            logger.error(f"Error extracting ZIP file: {str(e)}")
            raise
        
        return extracted_files
    
    async def _convert_to_parquet_v2(self, file_path: Path, target_dir: Path) -> Optional[Path]:
        """Convert file to parquet format"""
        extension = file_path.suffix.lower()
        
        if extension not in self.SUPPORTED_FORMATS:
            logger.warning(f"Unsupported file type for conversion: {extension}")
            return None
        
        try:
            # Use appropriate converter based on extension
            if extension == '.csv':
                return await self._convert_csv_to_parquet_v2(file_path, target_dir)
            elif extension in ['.xlsx', '.xls']:
                return await self._convert_excel_to_parquet_v2(file_path, target_dir)
            elif extension == '.sas7bdat':
                return await self._convert_sas_to_parquet_v2(file_path, target_dir)
            elif extension == '.xpt':
                return await self._convert_xpt_to_parquet_v2(file_path, target_dir)
            else:
                return None
        except Exception as e:
            logger.error(f"Error converting {file_path.name}: {str(e)}")
            return None
    
    async def _convert_csv_to_parquet_v2(self, file_path: Path, target_dir: Path) -> Optional[Path]:
        """Convert CSV to parquet"""
        if pd is None:
            logger.error("pandas not available for CSV conversion")
            return None
        
        try:
            loop = asyncio.get_event_loop()
            
            # Read CSV with proper handling
            df = await loop.run_in_executor(
                None,
                lambda: pd.read_csv(
                    file_path,
                    encoding='utf-8',
                    encoding_errors='replace',
                    low_memory=False,
                    na_values=['', 'NA', 'N/A', 'null', 'NULL', '.', ' ']
                )
            )
            
            # Clean column names
            df.columns = [col.strip().upper() for col in df.columns]
            
            # Save as parquet
            parquet_path = target_dir / f"{file_path.stem}.parquet"
            
            await loop.run_in_executor(
                None,
                lambda: df.to_parquet(parquet_path, engine='pyarrow', compression='snappy')
            )
            
            return parquet_path
            
        except Exception as e:
            logger.error(f"Error converting CSV to parquet: {str(e)}")
            return None
    
    async def _convert_excel_to_parquet_v2(self, file_path: Path, target_dir: Path) -> Optional[Path]:
        """Convert Excel to parquet"""
        if pd is None:
            logger.error("pandas not available for Excel conversion")
            return None
        
        try:
            loop = asyncio.get_event_loop()
            
            # Read Excel
            df = await loop.run_in_executor(
                None,
                lambda: pd.read_excel(file_path, engine='openpyxl' if file_path.suffix == '.xlsx' else None)
            )
            
            # Clean column names
            df.columns = [col.strip().upper() for col in df.columns]
            
            # Save as parquet
            parquet_path = target_dir / f"{file_path.stem}.parquet"
            
            await loop.run_in_executor(
                None,
                lambda: df.to_parquet(parquet_path, engine='pyarrow', compression='snappy')
            )
            
            return parquet_path
            
        except Exception as e:
            logger.error(f"Error converting Excel to parquet: {str(e)}")
            return None
    
    async def _convert_sas_to_parquet_v2(self, file_path: Path, target_dir: Path) -> Optional[Path]:
        """Convert SAS7BDAT to parquet"""
        if pyreadstat is None:
            logger.error("pyreadstat not available for SAS conversion")
            return None
        
        try:
            loop = asyncio.get_event_loop()
            
            # Read SAS file
            df, meta = await loop.run_in_executor(
                None,
                lambda: pyreadstat.read_sas7bdat(str(file_path))
            )
            
            # Clean column names
            df.columns = [col.strip().upper() for col in df.columns]
            
            # Save as parquet
            parquet_path = target_dir / f"{file_path.stem}.parquet"
            
            await loop.run_in_executor(
                None,
                lambda: df.to_parquet(parquet_path, engine='pyarrow', compression='snappy')
            )
            
            # Save metadata
            meta_path = target_dir / f"{file_path.stem}_metadata.json"
            metadata = {
                "column_labels": dict(zip(meta.column_names, meta.column_labels)) if hasattr(meta, 'column_labels') and meta.column_labels else {},
                "file_label": meta.file_label if hasattr(meta, 'file_label') else None,
                "file_encoding": meta.file_encoding if hasattr(meta, 'file_encoding') else None,
                "original_format": "sas7bdat"
            }
            with open(meta_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            return parquet_path
            
        except Exception as e:
            logger.error(f"Error converting SAS to parquet: {str(e)}")
            return None
    
    async def _convert_xpt_to_parquet_v2(self, file_path: Path, target_dir: Path) -> Optional[Path]:
        """Convert XPT to parquet"""
        if pyreadstat is None:
            logger.error("pyreadstat not available for XPT conversion")
            return None
        
        try:
            loop = asyncio.get_event_loop()
            
            # Read XPT file
            df, meta = await loop.run_in_executor(
                None,
                lambda: pyreadstat.read_xport(str(file_path))
            )
            
            # Clean column names
            df.columns = [col.strip().upper() for col in df.columns]
            
            # Save as parquet
            parquet_path = target_dir / f"{file_path.stem}.parquet"
            
            await loop.run_in_executor(
                None,
                lambda: df.to_parquet(parquet_path, engine='pyarrow', compression='snappy')
            )
            
            # Save metadata
            meta_path = target_dir / f"{file_path.stem}_metadata.json"
            metadata = {
                "column_labels": dict(zip(meta.column_names, meta.column_labels)) if hasattr(meta, 'column_labels') and meta.column_labels else {},
                "original_format": "xpt"
            }
            with open(meta_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            return parquet_path
            
        except Exception as e:
            logger.error(f"Error converting XPT to parquet: {str(e)}")
            return None
    
    async def _extract_parquet_schema_v2(self, parquet_path: Path) -> Dict[str, Any]:
        """Extract schema information from parquet file"""
        if pq is None or pd is None:
            logger.error("pyarrow/pandas not available for parquet schema extraction")
            return {}
        
        try:
            loop = asyncio.get_event_loop()
            
            # Read parquet file
            def read_parquet_schema():
                parquet_file = pq.ParquetFile(parquet_path)
                metadata = parquet_file.metadata
                schema = parquet_file.schema
                
                # Get first few rows for sampling
                table = parquet_file.read(columns=None, use_threads=True)
                df = table.to_pandas()
                
                return metadata, schema, df
            
            metadata, schema, df = await loop.run_in_executor(None, read_parquet_schema)
            
            # Build schema info
            schema_info = {
                "file_name": parquet_path.name,
                "file_path": str(parquet_path),
                "row_count": metadata.num_rows,
                "column_count": len(schema),
                "file_size_mb": round(parquet_path.stat().st_size / (1024 * 1024), 2),
                "columns": {},
                "sample_data": []
            }
            
            # Extract column information
            for field in schema:
                col_name = field.name
                
                # Get pandas dtype for better type mapping
                pandas_dtype = str(df[col_name].dtype)
                
                # Map to our standard types
                if 'int' in pandas_dtype or 'float' in pandas_dtype:
                    data_type = 'number'
                elif 'bool' in pandas_dtype:
                    data_type = 'boolean'
                elif 'datetime' in pandas_dtype:
                    data_type = 'datetime'
                else:
                    data_type = 'string'
                
                # Get column statistics
                col_info = {
                    "type": data_type,
                    "parquet_type": str(field.physical_type) if hasattr(field, 'physical_type') else str(field),
                    "pandas_dtype": pandas_dtype,
                    "nullable": True,  # Parquet field doesn't have nullable attribute
                    "null_count": int(df[col_name].isnull().sum()),
                    "unique_count": int(df[col_name].nunique())
                }
                
                # Add sample values for categorical columns
                if col_info["unique_count"] <= 20:
                    unique_values = df[col_name].dropna().unique().tolist()
                    # Convert to string to handle datetime/Timestamp objects
                    col_info["unique_values"] = []
                    for v in unique_values[:20]:
                        if pd.api.types.is_datetime64_any_dtype(type(v)):
                            col_info["unique_values"].append(str(v))
                        elif hasattr(v, 'isoformat'):  # Handle datetime objects
                            col_info["unique_values"].append(v.isoformat())
                        else:
                            col_info["unique_values"].append(str(v))
                
                # Add statistics for numeric columns
                if data_type == 'number':
                    col_info["stats"] = {
                        "min": float(df[col_name].min()) if not pd.isna(df[col_name].min()) else None,
                        "max": float(df[col_name].max()) if not pd.isna(df[col_name].max()) else None,
                        "mean": float(df[col_name].mean()) if not pd.isna(df[col_name].mean()) else None,
                        "std": float(df[col_name].std()) if not pd.isna(df[col_name].std()) else None
                    }
                
                schema_info["columns"][col_name] = col_info
            
            # Add sample rows (first 5)
            sample_df = df.head(5).fillna('')
            # Convert datetime columns to strings for JSON serialization
            for col in sample_df.columns:
                if pd.api.types.is_datetime64_any_dtype(sample_df[col]):
                    sample_df[col] = sample_df[col].astype(str)
            schema_info["sample_data"] = sample_df.to_dict('records')
            
            # Check for metadata file
            meta_path = parquet_path.parent / f"{parquet_path.stem}_metadata.json"
            if meta_path.exists():
                with open(meta_path, 'r') as f:
                    schema_info["original_metadata"] = json.load(f)
            
            return schema_info
            
        except Exception as e:
            logger.error(f"Error extracting parquet schema: {str(e)}")
            return {
                "file_name": parquet_path.name,
                "file_path": str(parquet_path),
                "error": str(e)
            }