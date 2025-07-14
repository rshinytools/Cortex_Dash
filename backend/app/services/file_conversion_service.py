# ABOUTME: Service for converting various file formats to parquet
# ABOUTME: Handles CSV, SAS7BDAT, XPT, XLSX to parquet conversion with data profiling

import os
import zipfile
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Callable, Awaitable
from datetime import datetime
import logging
from dataclasses import dataclass
import aiofiles
import asyncio
import uuid

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
        study_id: uuid.UUID,
        files: List[Dict[str, Any]],
        progress_callback: Optional[Callable[[int, Optional[str]], Awaitable[None]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Convert multiple study files to parquet with progress tracking
        
        Args:
            study_id: The study ID
            files: List of file information dictionaries
            progress_callback: Async callback for progress updates
            
        Returns:
            List of converted file information
        """
        converted_files = []
        total_files = len(files)
        
        for idx, file_info in enumerate(files):
            try:
                # Update progress
                if progress_callback:
                    current_file = file_info.get("name", "unknown")
                    progress = int((idx / total_files) * 100)
                    await progress_callback(progress, current_file)
                
                # Determine file format
                file_path = Path(file_info["path"])
                file_extension = file_path.suffix.lower()
                
                # Set up output path
                output_dir = Path(f"/data/studies/{study_id}/parquet_data")
                output_dir.mkdir(parents=True, exist_ok=True)
                
                # Convert based on file type
                if file_info.get("type", "").lower() == "zip" or file_extension == ".zip":
                    result = await self._process_zip_file(str(file_path), str(output_dir))
                else:
                    result = await self._process_single_file(
                        str(file_path),
                        str(output_dir),
                        file_extension[1:] if file_extension else file_info.get("type", "unknown")
                    )
                
                if result.success:
                    # Add conversion metadata
                    for extracted_file in result.files_extracted:
                        converted_files.append({
                            **extracted_file,
                            "source_file": file_info["name"],
                            "converted_at": datetime.utcnow().isoformat()
                        })
                else:
                    logger.error(f"Failed to convert {file_info['name']}: {result.error_message}")
                    if progress_callback:
                        # Still update progress even on failure
                        await progress_callback(
                            int(((idx + 1) / total_files) * 100),
                            f"Failed: {file_info['name']}"
                        )
                
            except Exception as e:
                logger.error(f"Error converting file {file_info.get('name', 'unknown')}: {str(e)}")
                continue
        
        # Final progress update
        if progress_callback:
            await progress_callback(100, "Conversion complete")
        
        return converted_files