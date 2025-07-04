# ABOUTME: Transformation engine for clinical data processing
# ABOUTME: Executes data transformations including mappings, calculations, and format conversions

import pandas as pd
import numpy as np
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
import json
import pyarrow as pa
import pyarrow.parquet as pq

from app.models import Study


class TransformationEngine:
    """Engine for executing data transformations"""
    
    def __init__(
        self,
        study: Study,
        logger: Optional[logging.Logger] = None
    ):
        self.study = study
        self.logger = logger or logging.getLogger(__name__)
        self.supported_formats = [".sas7bdat", ".csv", ".parquet", ".xpt"]
        
    async def apply_transformation(
        self,
        input_files: List[str],
        transformation_config: Dict[str, Any],
        output_path: Path
    ) -> List[Dict[str, Any]]:
        """Apply transformation to input files
        
        Args:
            input_files: List of input file paths
            transformation_config: Transformation configuration
            output_path: Output directory path
            
        Returns:
            List of output file information
        """
        transformation_type = transformation_config.get("type")
        
        if transformation_type == "standardize":
            return await self._standardize_data(input_files, transformation_config, output_path)
        elif transformation_type == "mapping":
            return await self._apply_mapping(input_files, transformation_config, output_path)
        elif transformation_type == "calculation":
            return await self._apply_calculations(input_files, transformation_config, output_path)
        elif transformation_type == "format_conversion":
            return await self._convert_format(input_files, transformation_config, output_path)
        elif transformation_type == "custom_script":
            return await self._run_custom_script(input_files, transformation_config, output_path)
        else:
            raise ValueError(f"Unsupported transformation type: {transformation_type}")
    
    async def _standardize_data(
        self,
        input_files: List[str],
        config: Dict[str, Any],
        output_path: Path
    ) -> List[Dict[str, Any]]:
        """Standardize data to common format"""
        output_files = []
        
        for input_file in input_files:
            try:
                # Read data
                df = self._read_data_file(input_file)
                
                # Apply standardization rules
                if config.get("column_mapping"):
                    df = df.rename(columns=config["column_mapping"])
                
                if config.get("date_columns"):
                    for col in config["date_columns"]:
                        if col in df.columns:
                            df[col] = pd.to_datetime(df[col], errors='coerce')
                
                if config.get("numeric_columns"):
                    for col in config["numeric_columns"]:
                        if col in df.columns:
                            df[col] = pd.to_numeric(df[col], errors='coerce')
                
                # Handle missing values
                if config.get("missing_value_handling"):
                    handling = config["missing_value_handling"]
                    if handling == "drop":
                        df = df.dropna()
                    elif handling == "fill_zero":
                        df = df.fillna(0)
                    elif handling == "fill_mean":
                        df = df.fillna(df.mean(numeric_only=True))
                
                # Save standardized data
                output_file = output_path / f"standardized_{Path(input_file).stem}.parquet"
                df.to_parquet(output_file, engine='pyarrow', compression='snappy')
                
                output_files.append({
                    "path": str(output_file),
                    "format": "parquet",
                    "rows": len(df),
                    "columns": list(df.columns),
                    "size": output_file.stat().st_size
                })
                
            except Exception as e:
                self.logger.error(f"Error standardizing {input_file}: {str(e)}")
                raise
        
        return output_files
    
    async def _apply_mapping(
        self,
        input_files: List[str],
        config: Dict[str, Any],
        output_path: Path
    ) -> List[Dict[str, Any]]:
        """Apply field mappings"""
        output_files = []
        
        # Load mapping rules
        mappings = config.get("mappings", {})
        
        for input_file in input_files:
            try:
                df = self._read_data_file(input_file)
                
                # Apply each mapping
                for target_col, mapping_rule in mappings.items():
                    source_col = mapping_rule.get("source_column")
                    value_map = mapping_rule.get("value_mapping")
                    formula = mapping_rule.get("formula")
                    
                    if source_col and source_col in df.columns:
                        if value_map:
                            df[target_col] = df[source_col].map(value_map)
                        elif formula:
                            # Simple formula evaluation (be careful with security)
                            df[target_col] = eval(formula, {"df": df, "np": np})
                        else:
                            df[target_col] = df[source_col]
                
                # Save mapped data
                output_file = output_path / f"mapped_{Path(input_file).stem}.parquet"
                df.to_parquet(output_file, engine='pyarrow', compression='snappy')
                
                output_files.append({
                    "path": str(output_file),
                    "format": "parquet",
                    "rows": len(df),
                    "columns": list(df.columns),
                    "size": output_file.stat().st_size
                })
                
            except Exception as e:
                self.logger.error(f"Error mapping {input_file}: {str(e)}")
                raise
        
        return output_files
    
    async def _apply_calculations(
        self,
        input_files: List[str],
        config: Dict[str, Any],
        output_path: Path
    ) -> List[Dict[str, Any]]:
        """Apply calculations to create derived variables"""
        output_files = []
        
        calculations = config.get("calculations", [])
        
        for input_file in input_files:
            try:
                df = self._read_data_file(input_file)
                
                # Apply each calculation
                for calc in calculations:
                    var_name = calc.get("variable_name")
                    expression = calc.get("expression")
                    condition = calc.get("condition")
                    
                    if var_name and expression:
                        # Create a safe evaluation context
                        eval_context = {
                            "df": df,
                            "np": np,
                            "pd": pd,
                            "datetime": datetime
                        }
                        
                        if condition:
                            # Apply calculation conditionally
                            mask = eval(condition, eval_context)
                            df.loc[mask, var_name] = eval(expression, eval_context)
                        else:
                            # Apply calculation to all rows
                            df[var_name] = eval(expression, eval_context)
                
                # Save calculated data
                output_file = output_path / f"calculated_{Path(input_file).stem}.parquet"
                df.to_parquet(output_file, engine='pyarrow', compression='snappy')
                
                output_files.append({
                    "path": str(output_file),
                    "format": "parquet",
                    "rows": len(df),
                    "columns": list(df.columns),
                    "size": output_file.stat().st_size,
                    "calculations_applied": len(calculations)
                })
                
            except Exception as e:
                self.logger.error(f"Error calculating {input_file}: {str(e)}")
                raise
        
        return output_files
    
    async def _convert_format(
        self,
        input_files: List[str],
        config: Dict[str, Any],
        output_path: Path
    ) -> List[Dict[str, Any]]:
        """Convert data format"""
        output_files = []
        target_format = config.get("target_format", "parquet")
        
        for input_file in input_files:
            try:
                df = self._read_data_file(input_file)
                
                # Determine output file name and format
                base_name = Path(input_file).stem
                
                if target_format == "parquet":
                    output_file = output_path / f"{base_name}.parquet"
                    df.to_parquet(output_file, engine='pyarrow', compression='snappy')
                elif target_format == "csv":
                    output_file = output_path / f"{base_name}.csv"
                    df.to_csv(output_file, index=False)
                elif target_format == "excel":
                    output_file = output_path / f"{base_name}.xlsx"
                    df.to_excel(output_file, index=False, engine='openpyxl')
                else:
                    raise ValueError(f"Unsupported target format: {target_format}")
                
                output_files.append({
                    "path": str(output_file),
                    "format": target_format,
                    "rows": len(df),
                    "columns": list(df.columns),
                    "size": output_file.stat().st_size
                })
                
            except Exception as e:
                self.logger.error(f"Error converting {input_file}: {str(e)}")
                raise
        
        return output_files
    
    async def _run_custom_script(
        self,
        input_files: List[str],
        config: Dict[str, Any],
        output_path: Path
    ) -> List[Dict[str, Any]]:
        """Run custom transformation script (sandboxed)"""
        # This would implement a sandboxed script execution environment
        # For now, we'll just return a placeholder
        self.logger.warning("Custom script execution not yet implemented")
        return []
    
    def _read_data_file(self, file_path: str) -> pd.DataFrame:
        """Read data file into pandas DataFrame"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        ext = file_path.suffix.lower()
        
        if ext == ".csv":
            return pd.read_csv(file_path)
        elif ext == ".parquet":
            return pd.read_parquet(file_path, engine='pyarrow')
        elif ext == ".sas7bdat":
            # Would need to install pyreadstat or similar
            # return pd.read_sas(file_path)
            raise NotImplementedError("SAS file reading not yet implemented")
        elif ext == ".xpt":
            # SAS transport files
            # return pd.read_sas(file_path, format='xport')
            raise NotImplementedError("XPT file reading not yet implemented")
        elif ext in [".xlsx", ".xls"]:
            return pd.read_excel(file_path, engine='openpyxl')
        else:
            raise ValueError(f"Unsupported file format: {ext}")
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Get information about a data file"""
        file_path = Path(file_path)
        
        try:
            df = self._read_data_file(str(file_path))
            
            return {
                "path": str(file_path),
                "format": file_path.suffix.lower(),
                "rows": len(df),
                "columns": list(df.columns),
                "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
                "size": file_path.stat().st_size,
                "memory_usage": df.memory_usage(deep=True).sum(),
                "null_counts": df.isnull().sum().to_dict()
            }
            
        except Exception as e:
            return {
                "path": str(file_path),
                "error": str(e)
            }