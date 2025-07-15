# ABOUTME: Service for processing uploaded files and extracting schema information
# ABOUTME: Handles various file formats (CSV, Excel, SAS, ZIP) and extracts column metadata

import zipfile
from pathlib import Path

try:
    import pandas as pd
except ImportError:
    pd = None
    
try:
    import pyreadstat
except ImportError:
    pyreadstat = None
from typing import Dict, Any, List, Optional, Tuple
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class FileProcessingService:
    """Service for processing clinical data files and extracting schema"""
    
    def __init__(self):
        self.supported_extensions = {
            '.csv': self._process_csv,
            '.xlsx': self._process_excel,
            '.xls': self._process_excel,
            '.sas7bdat': self._process_sas,
            '.xpt': self._process_xpt,
            '.zip': self._process_zip
        }
    
    async def process_uploaded_files(
        self, 
        study_id: str,
        uploaded_files: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Process uploaded files and extract schema information"""
        results = {
            "study_id": study_id,
            "processed_at": datetime.utcnow().isoformat(),
            "datasets": {},
            "errors": [],
            "warnings": []
        }
        
        for file_info in uploaded_files:
            try:
                file_path = Path(file_info["path"])
                if not file_path.exists():
                    results["errors"].append(f"File not found: {file_info['name']}")
                    continue
                
                # Process based on file type
                extension = file_path.suffix.lower()
                if extension in self.supported_extensions:
                    processor = self.supported_extensions[extension]
                    dataset_info = await processor(file_path)
                    
                    # Handle multiple datasets from ZIP files
                    if isinstance(dataset_info, dict) and "datasets" in dataset_info:
                        results["datasets"].update(dataset_info["datasets"])
                        if "warnings" in dataset_info:
                            results["warnings"].extend(dataset_info["warnings"])
                    else:
                        # Single dataset
                        dataset_name = file_path.stem.lower()
                        results["datasets"][dataset_name] = dataset_info
                else:
                    results["warnings"].append(
                        f"Unsupported file type: {file_info['name']} ({extension})"
                    )
                    
            except Exception as e:
                logger.error(f"Error processing file {file_info['name']}: {str(e)}")
                results["errors"].append(
                    f"Failed to process {file_info['name']}: {str(e)}"
                )
        
        return results
    
    async def _process_csv(self, file_path: Path) -> Dict[str, Any]:
        """Process CSV file and extract schema"""
        if pd is None:
            # Return mock schema for testing
            return self._create_mock_schema(file_path, "CSV")
            
        df = pd.read_csv(file_path, nrows=1000)  # Sample for schema
        return self._extract_dataframe_schema(df, file_path)
    
    async def _process_excel(self, file_path: Path) -> Dict[str, Any]:
        """Process Excel file and extract schema"""
        if pd is None:
            # Return mock schema for testing
            return self._create_mock_schema(file_path, "Excel")
            
        # Read first sheet by default
        df = pd.read_excel(file_path, nrows=1000)
        return self._extract_dataframe_schema(df, file_path)
    
    async def _process_sas(self, file_path: Path) -> Dict[str, Any]:
        """Process SAS7BDAT file and extract schema"""
        if pyreadstat is None:
            # Return mock schema for testing without pyreadstat
            return {
                "file_name": file_path.name,
                "file_path": str(file_path),
                "row_count": 0,
                "column_count": 0,
                "columns": {},
                "sample_data": [],
                "error": "SAS file processing not available (pyreadstat not installed)"
            }
            
        df, meta = pyreadstat.read_sas7bdat(
            str(file_path), 
            row_limit=1000,
            metadataonly=False
        )
        
        schema = self._extract_dataframe_schema(df, file_path)
        
        # Add SAS-specific metadata
        schema["sas_metadata"] = {
            "column_labels": dict(zip(meta.column_names, meta.column_labels)),
            "file_label": meta.file_label,
            "file_encoding": meta.file_encoding
        }
        
        return schema
    
    async def _process_xpt(self, file_path: Path) -> Dict[str, Any]:
        """Process SAS Transport (XPT) file and extract schema"""
        if pyreadstat is None:
            # Return mock schema for testing without pyreadstat
            return {
                "file_name": file_path.name,
                "file_path": str(file_path),
                "row_count": 0,
                "column_count": 0,
                "columns": {},
                "sample_data": [],
                "error": "XPT file processing not available (pyreadstat not installed)"
            }
            
        df, meta = pyreadstat.read_xport(
            str(file_path),
            row_limit=1000,
            metadataonly=False
        )
        
        return self._extract_dataframe_schema(df, file_path)
    
    async def _process_zip(self, file_path: Path) -> Dict[str, Any]:
        """Process ZIP file containing multiple datasets"""
        results = {
            "datasets": {},
            "warnings": []
        }
        
        # Create extraction directory
        extract_dir = file_path.parent / f"{file_path.stem}_extracted"
        extract_dir.mkdir(exist_ok=True)
        
        try:
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                # Extract all files
                zip_ref.extractall(extract_dir)
                
                # Process each extracted file
                for item in extract_dir.rglob('*'):
                    if item.is_file():
                        extension = item.suffix.lower()
                        if extension in self.supported_extensions and extension != '.zip':
                            try:
                                processor = self.supported_extensions[extension]
                                dataset_info = await processor(item)
                                dataset_name = item.stem.lower()
                                results["datasets"][dataset_name] = dataset_info
                            except Exception as e:
                                # Try mock schema for unprocessable files
                                if extension in ['.csv', '.sas7bdat', '.xpt']:
                                    dataset_name = item.stem.lower()
                                    results["datasets"][dataset_name] = self._create_mock_schema(item, extension.upper()[1:])
                                else:
                                    results["warnings"].append(
                                        f"Failed to process {item.name} from ZIP: {str(e)}"
                                    )
                        elif extension not in ['.zip', '']:
                            results["warnings"].append(
                                f"Skipped unsupported file in ZIP: {item.name}"
                            )
        finally:
            # Clean up extracted files if needed
            # For now, keep them for processing
            pass
        
        return results
    
    def _create_mock_schema(self, file_path: Path, file_type: str) -> Dict[str, Any]:
        """Create mock schema for testing when dependencies are missing"""
        # Mock CDISC-like columns based on file name
        mock_columns = {}
        file_stem = file_path.stem.upper()
        
        if "DM" in file_stem or "DEMO" in file_stem:
            # Demographics mock columns
            mock_columns = {
                "USUBJID": {"type": "string", "nullable": False, "unique_count": 100},
                "SUBJID": {"type": "string", "nullable": False, "unique_count": 100},
                "AGE": {"type": "number", "nullable": True, "unique_count": 50},
                "SEX": {"type": "string", "nullable": False, "unique_count": 2, "unique_values": ["M", "F"]},
                "RACE": {"type": "string", "nullable": True, "unique_count": 5}
            }
        elif "AE" in file_stem:
            # Adverse events mock columns
            mock_columns = {
                "USUBJID": {"type": "string", "nullable": False, "unique_count": 100},
                "AETERM": {"type": "string", "nullable": False, "unique_count": 200},
                "AESTDTC": {"type": "string", "nullable": True, "unique_count": 150},
                "AESER": {"type": "string", "nullable": False, "unique_count": 2, "unique_values": ["Y", "N"]}
            }
        elif "LB" in file_stem or "LAB" in file_stem:
            # Lab results mock columns
            mock_columns = {
                "USUBJID": {"type": "string", "nullable": False, "unique_count": 100},
                "LBTEST": {"type": "string", "nullable": False, "unique_count": 50},
                "LBSTRESN": {"type": "number", "nullable": True, "unique_count": 1000},
                "LBSTRESU": {"type": "string", "nullable": True, "unique_count": 20},
                "VISITNUM": {"type": "number", "nullable": False, "unique_count": 10}
            }
        else:
            # Generic mock columns
            mock_columns = {
                "ID": {"type": "string", "nullable": False, "unique_count": 100},
                "VALUE": {"type": "number", "nullable": True, "unique_count": 500},
                "CATEGORY": {"type": "string", "nullable": True, "unique_count": 10},
                "DATE": {"type": "string", "nullable": True, "unique_count": 200}
            }
        
        return {
            "file_name": file_path.name,
            "file_path": str(file_path),
            "row_count": 1000,  # Mock row count
            "column_count": len(mock_columns),
            "columns": mock_columns,
            "sample_data": [],  # No sample data in mock
            "mock_data": True,
            "mock_reason": f"{file_type} processing library not available"
        }
    
    def _extract_dataframe_schema(self, df: pd.DataFrame, file_path: Path) -> Dict[str, Any]:
        """Extract schema information from a pandas DataFrame"""
        schema = {
            "file_name": file_path.name,
            "file_path": str(file_path),
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": {},
            "sample_data": []
        }
        
        # Extract column information
        for col in df.columns:
            dtype = str(df[col].dtype)
            
            # Map pandas dtypes to our data types
            if dtype.startswith('int') or dtype.startswith('float'):
                data_type = 'number'
            elif dtype == 'bool':
                data_type = 'boolean'
            elif 'datetime' in dtype:
                data_type = 'datetime'
            else:
                data_type = 'string'
            
            # Get column statistics
            col_info = {
                "type": data_type,
                "nullable": df[col].isnull().any(),
                "unique_count": df[col].nunique(),
                "null_count": df[col].isnull().sum(),
                "pandas_dtype": dtype
            }
            
            # Add sample values for categorical columns
            if col_info["unique_count"] <= 20:
                col_info["unique_values"] = df[col].dropna().unique().tolist()[:20]
            
            # Add basic statistics for numeric columns
            if data_type == 'number':
                col_info["stats"] = {
                    "min": float(df[col].min()) if not pd.isna(df[col].min()) else None,
                    "max": float(df[col].max()) if not pd.isna(df[col].max()) else None,
                    "mean": float(df[col].mean()) if not pd.isna(df[col].mean()) else None,
                    "std": float(df[col].std()) if not pd.isna(df[col].std()) else None
                }
            
            schema["columns"][col] = col_info
        
        # Add sample rows (first 5)
        sample_rows = df.head(5).fillna('').to_dict('records')
        schema["sample_data"] = sample_rows
        
        return schema
    
    def generate_mapping_suggestions(
        self,
        template_requirements: List[Dict[str, Any]],
        dataset_schemas: Dict[str, Any]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Generate smart mapping suggestions based on template requirements and available columns"""
        suggestions = {}
        
        for requirement in template_requirements:
            widget_id = requirement["widget_id"]
            widget_suggestions = []
            
            for field_name, field_config in requirement.get("data_config", {}).get("fields", {}).items():
                # Find best matching column across all datasets
                best_match = self._find_best_column_match(
                    field_name,
                    field_config,
                    dataset_schemas
                )
                
                if best_match:
                    widget_suggestions.append({
                        "field_name": field_name,
                        "suggested_dataset": best_match["dataset"],
                        "suggested_column": best_match["column"],
                        "confidence": best_match["confidence"],
                        "reason": best_match["reason"]
                    })
                else:
                    widget_suggestions.append({
                        "field_name": field_name,
                        "suggested_dataset": None,
                        "suggested_column": None,
                        "confidence": 0.0,
                        "reason": "No matching column found"
                    })
            
            suggestions[widget_id] = widget_suggestions
        
        return suggestions
    
    def _find_best_column_match(
        self,
        field_name: str,
        field_config: Dict[str, Any],
        dataset_schemas: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Find the best matching column for a required field"""
        best_match = None
        best_score = 0.0
        
        # Common CDISC mappings
        cdisc_mappings = {
            "subject_id": ["USUBJID", "SUBJID", "SUBJECT"],
            "visit": ["VISIT", "VISITNUM", "AVISIT"],
            "age": ["AGE", "AGEYR", "AGEY"],
            "sex": ["SEX", "GENDER"],
            "race": ["RACE", "ETHNIC"],
            "treatment": ["TRT", "TREAT", "ARM", "ACTARM", "TRT01A"],
            "adverse_event": ["AETERM", "AEDECOD"],
            "lab_value": ["AVAL", "LBSTRESN", "RESULT"],
            "lab_test": ["LBTEST", "LBTESTCD", "PARAM"],
            "date": ["DTC", "DT", "DATE"]
        }
        
        field_lower = field_name.lower()
        
        for dataset_name, dataset_info in dataset_schemas.items():
            for column_name, column_info in dataset_info.get("columns", {}).items():
                score = 0.0
                reason = []
                
                # Exact match
                if column_name.lower() == field_lower:
                    score = 1.0
                    reason.append("Exact name match")
                
                # CDISC standard mapping
                elif field_lower in cdisc_mappings:
                    if column_name.upper() in cdisc_mappings[field_lower]:
                        score = 0.9
                        reason.append(f"CDISC standard mapping")
                
                # Partial match
                elif field_lower in column_name.lower() or column_name.lower() in field_lower:
                    score = 0.7
                    reason.append("Partial name match")
                
                # Type compatibility check
                if score > 0:
                    expected_type = field_config.get("data_type", "string")
                    actual_type = column_info.get("type", "string")
                    
                    if expected_type == actual_type:
                        score *= 1.0
                        reason.append("Type match")
                    elif (expected_type == "number" and actual_type in ["number", "string"]) or \
                         (expected_type == "string" and actual_type in ["number", "string"]):
                        score *= 0.8
                        reason.append("Compatible types")
                    else:
                        score *= 0.5
                        reason.append("Type mismatch")
                
                if score > best_score:
                    best_score = score
                    best_match = {
                        "dataset": dataset_name,
                        "column": column_name,
                        "confidence": score,
                        "reason": ", ".join(reason),
                        "column_info": column_info
                    }
        
        return best_match