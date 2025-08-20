# ABOUTME: Filter validation service for widget filtering
# ABOUTME: Validates filter expressions against dataset schemas

import json
import logging
from typing import Dict, List, Optional, Set, Any, Tuple
from pathlib import Path
import pyarrow.parquet as pq
import pandas as pd
from datetime import datetime
from sqlalchemy.orm import Session

from app.models import Study, User
from app.services.filter_parser import (
    FilterParser, ASTNode, ColumnNode, LiteralNode, 
    BinaryOpNode, UnaryOpNode, InNode, BetweenNode, 
    LikeNode, IsNullNode, TokenType
)

logger = logging.getLogger(__name__)


class FilterValidator:
    """Validates filter expressions against dataset schemas"""
    
    def __init__(self, db: Session):
        self.db = db
        self.parser = FilterParser()
        self.logger = logger
    
    def validate_filter(
        self,
        study_id: str,
        widget_id: str,
        filter_expression: str,
        dataset_name: str,
        user: Optional[User] = None
    ) -> Dict[str, Any]:
        """
        Validate a filter expression against a dataset schema
        
        Args:
            study_id: Study ID
            widget_id: Widget ID
            filter_expression: SQL WHERE clause expression
            dataset_name: Name of the dataset to validate against
            user: User performing the validation (for audit)
            
        Returns:
            Validation result with:
            - is_valid: Whether the filter is valid
            - errors: List of validation errors
            - warnings: List of validation warnings
            - validated_columns: List of validated columns
            - schema_info: Dataset schema information
        """
        try:
            # Get study
            study = self.db.query(Study).filter(Study.id == study_id).first()
            if not study:
                return {
                    "is_valid": False,
                    "errors": ["Study not found"],
                    "warnings": [],
                    "validated_columns": [],
                    "schema_info": None
                }
            
            # Parse the expression
            parse_result = self.parser.parse(filter_expression)
            if not parse_result["is_valid"]:
                return {
                    "is_valid": False,
                    "errors": [f"Parse error: {parse_result['error']}"],
                    "warnings": [],
                    "validated_columns": [],
                    "schema_info": None
                }
            
            # Get dataset schema
            schema_info = self._get_dataset_schema(study, dataset_name)
            if not schema_info:
                return {
                    "is_valid": False,
                    "errors": [f"Dataset '{dataset_name}' not found"],
                    "warnings": [],
                    "validated_columns": [],
                    "schema_info": None
                }
            
            # Validate columns exist in schema
            errors = []
            warnings = []
            validated_columns = []
            
            for column in parse_result["columns"]:
                if column not in schema_info["columns"]:
                    errors.append(f"Column '{column}' not found in dataset '{dataset_name}'")
                else:
                    validated_columns.append({
                        "name": column,
                        "type": schema_info["columns"][column]["type"],
                        "nullable": schema_info["columns"][column].get("nullable", True)
                    })
            
            # Validate AST for type compatibility
            if parse_result["ast"]:
                ast_errors, ast_warnings = self._validate_ast(
                    parse_result["ast"],
                    schema_info["columns"]
                )
                errors.extend(ast_errors)
                warnings.extend(ast_warnings)
            
            # Check for performance warnings
            if len(validated_columns) > 5:
                warnings.append(f"Filter uses {len(validated_columns)} columns, which may impact performance")
            
            # Check for complex expressions
            complexity = self._calculate_complexity(parse_result["ast"])
            if complexity > 10:
                warnings.append(f"Complex filter expression (complexity: {complexity}), consider simplifying")
            
            # Store validation result in cache
            self._cache_validation_result(
                study_id=study_id,
                widget_id=widget_id,
                filter_expression=filter_expression,
                dataset_name=dataset_name,
                is_valid=len(errors) == 0,
                errors=errors,
                validated_columns=validated_columns
            )
            
            # Log audit entry if user provided
            if user:
                self._log_audit(
                    study_id=study_id,
                    widget_id=widget_id,
                    action="VALIDATE",
                    expression=filter_expression,
                    user_id=str(user.id),
                    details={
                        "dataset": dataset_name,
                        "is_valid": len(errors) == 0,
                        "errors": errors,
                        "warnings": warnings
                    }
                )
            
            return {
                "is_valid": len(errors) == 0,
                "errors": errors,
                "warnings": warnings,
                "validated_columns": validated_columns,
                "schema_info": schema_info,
                "complexity": complexity
            }
            
        except Exception as e:
            self.logger.error(f"Failed to validate filter: {str(e)}")
            return {
                "is_valid": False,
                "errors": [f"Validation error: {str(e)}"],
                "warnings": [],
                "validated_columns": [],
                "schema_info": None
            }
    
    def _get_dataset_schema(self, study: Study, dataset_name: str) -> Optional[Dict[str, Any]]:
        """Get schema information for a dataset"""
        try:
            # Get the latest data version path
            org_id = study.organization_id
            study_id = study.id
            
            base_path = Path(f"/data/{org_id}/studies/{study_id}")
            if not base_path.exists():
                return None
            
            # Find the latest data version
            data_versions = [d for d in base_path.iterdir() if d.is_dir() and d.name.startswith("2")]
            if not data_versions:
                return None
            
            latest_version = sorted(data_versions)[-1]
            dataset_path = latest_version / f"{dataset_name}.parquet"
            
            if not dataset_path.exists():
                return None
            
            # Read schema from parquet file
            parquet_file = pq.ParquetFile(dataset_path)
            schema = parquet_file.schema
            
            columns = {}
            for field in schema:
                # Map PyArrow types to simple types
                type_str = str(field.type)
                simple_type = self._map_arrow_type(type_str)
                
                columns[field.name] = {
                    "type": simple_type,
                    "arrow_type": type_str,
                    "nullable": field.nullable
                }
            
            # Get basic statistics
            df = pd.read_parquet(dataset_path, columns=[next(iter(columns))])
            row_count = len(df)
            
            return {
                "dataset": dataset_name,
                "path": str(dataset_path),
                "columns": columns,
                "row_count": row_count,
                "file_size": dataset_path.stat().st_size
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get dataset schema: {str(e)}")
            return None
    
    def _map_arrow_type(self, arrow_type: str) -> str:
        """Map PyArrow type to simple type string"""
        if "int" in arrow_type.lower():
            return "integer"
        elif "float" in arrow_type.lower() or "double" in arrow_type.lower():
            return "float"
        elif "string" in arrow_type.lower() or "utf8" in arrow_type.lower():
            return "string"
        elif "bool" in arrow_type.lower():
            return "boolean"
        elif "date" in arrow_type.lower():
            return "date"
        elif "timestamp" in arrow_type.lower():
            return "datetime"
        else:
            return "unknown"
    
    def _validate_ast(
        self,
        node: ASTNode,
        columns: Dict[str, Dict[str, Any]]
    ) -> Tuple[List[str], List[str]]:
        """Validate AST for type compatibility"""
        errors = []
        warnings = []
        
        if isinstance(node, BinaryOpNode):
            # Validate both sides
            left_errors, left_warnings = self._validate_ast(node.left, columns)
            right_errors, right_warnings = self._validate_ast(node.right, columns)
            errors.extend(left_errors + right_errors)
            warnings.extend(left_warnings + right_warnings)
            
            # Check type compatibility for comparisons
            if node.operator in (TokenType.EQ, TokenType.NEQ, TokenType.LT, 
                                TokenType.LTE, TokenType.GT, TokenType.GTE):
                left_type = self._get_node_type(node.left, columns)
                right_type = self._get_node_type(node.right, columns)
                
                if left_type and right_type and not self._types_compatible(left_type, right_type):
                    warnings.append(f"Type mismatch in comparison: {left_type} vs {right_type}")
        
        elif isinstance(node, UnaryOpNode):
            sub_errors, sub_warnings = self._validate_ast(node.operand, columns)
            errors.extend(sub_errors)
            warnings.extend(sub_warnings)
        
        elif isinstance(node, InNode):
            column_type = columns.get(node.column.name, {}).get("type")
            if column_type:
                for value in node.values:
                    value_type = self._get_literal_type(value.value)
                    if not self._types_compatible(column_type, value_type):
                        warnings.append(
                            f"Type mismatch in IN clause: column '{node.column.name}' "
                            f"({column_type}) vs value ({value_type})"
                        )
        
        elif isinstance(node, BetweenNode):
            column_type = columns.get(node.column.name, {}).get("type")
            if column_type:
                lower_type = self._get_literal_type(node.lower.value)
                upper_type = self._get_literal_type(node.upper.value)
                
                if not self._types_compatible(column_type, lower_type):
                    warnings.append(
                        f"Type mismatch in BETWEEN lower bound: column '{node.column.name}' "
                        f"({column_type}) vs value ({lower_type})"
                    )
                if not self._types_compatible(column_type, upper_type):
                    warnings.append(
                        f"Type mismatch in BETWEEN upper bound: column '{node.column.name}' "
                        f"({column_type}) vs value ({upper_type})"
                    )
                
                # Check if lower <= upper for numeric types
                if column_type in ("integer", "float") and isinstance(node.lower.value, (int, float)) \
                   and isinstance(node.upper.value, (int, float)):
                    if node.lower.value > node.upper.value:
                        errors.append(f"BETWEEN lower bound ({node.lower.value}) is greater than upper bound ({node.upper.value})")
        
        elif isinstance(node, LikeNode):
            column_type = columns.get(node.column.name, {}).get("type")
            if column_type and column_type != "string":
                warnings.append(f"LIKE operator used on non-string column '{node.column.name}' ({column_type})")
            
            # Check for potentially expensive patterns
            if node.pattern.startswith("%"):
                warnings.append(f"LIKE pattern starting with '%' may be slow on large datasets")
        
        return errors, warnings
    
    def _get_node_type(self, node: ASTNode, columns: Dict[str, Dict[str, Any]]) -> Optional[str]:
        """Get the type of an AST node"""
        if isinstance(node, ColumnNode):
            return columns.get(node.name, {}).get("type")
        elif isinstance(node, LiteralNode):
            return self._get_literal_type(node.value)
        else:
            return None
    
    def _get_literal_type(self, value: Any) -> str:
        """Get the type of a literal value"""
        if value is None:
            return "null"
        elif isinstance(value, bool):
            return "boolean"
        elif isinstance(value, int):
            return "integer"
        elif isinstance(value, float):
            return "float"
        elif isinstance(value, str):
            return "string"
        else:
            return "unknown"
    
    def _types_compatible(self, type1: str, type2: str) -> bool:
        """Check if two types are compatible for comparison"""
        # Null is compatible with everything
        if "null" in (type1, type2):
            return True
        
        # Same types are compatible
        if type1 == type2:
            return True
        
        # Numeric types are compatible with each other
        numeric_types = {"integer", "float"}
        if type1 in numeric_types and type2 in numeric_types:
            return True
        
        # String can be compared with dates (for date literals)
        if (type1 == "string" and type2 in ("date", "datetime")) or \
           (type2 == "string" and type1 in ("date", "datetime")):
            return True
        
        return False
    
    def _calculate_complexity(self, node: Optional[ASTNode], depth: int = 0) -> int:
        """Calculate complexity score of filter expression"""
        if node is None:
            return 0
        
        complexity = 1  # Base complexity for any node
        
        if isinstance(node, BinaryOpNode):
            complexity += self._calculate_complexity(node.left, depth + 1)
            complexity += self._calculate_complexity(node.right, depth + 1)
            # Add extra complexity for nested conditions
            if depth > 0:
                complexity += 1
        elif isinstance(node, UnaryOpNode):
            complexity += self._calculate_complexity(node.operand, depth + 1)
        elif isinstance(node, InNode):
            complexity += len(node.values)
        elif isinstance(node, BetweenNode):
            complexity += 2
        elif isinstance(node, LikeNode):
            # LIKE is more expensive
            complexity += 3
        
        return complexity
    
    def _cache_validation_result(
        self,
        study_id: str,
        widget_id: str,
        filter_expression: str,
        dataset_name: str,
        is_valid: bool,
        errors: List[str],
        validated_columns: List[Dict[str, Any]]
    ):
        """Store validation result in cache table"""
        try:
            # Create cache entry
            from sqlalchemy import text
            
            query = text("""
                INSERT INTO filter_validation_cache 
                (id, study_id, widget_id, filter_expression, dataset_name, 
                 is_valid, validation_errors, validated_columns, created_at, last_validated)
                VALUES 
                (gen_random_uuid(), :study_id, :widget_id, :filter_expression, :dataset_name,
                 :is_valid, :validation_errors, :validated_columns, NOW(), NOW())
                ON CONFLICT (study_id, widget_id) DO UPDATE SET
                    filter_expression = EXCLUDED.filter_expression,
                    dataset_name = EXCLUDED.dataset_name,
                    is_valid = EXCLUDED.is_valid,
                    validation_errors = EXCLUDED.validation_errors,
                    validated_columns = EXCLUDED.validated_columns,
                    last_validated = NOW()
            """)
            
            self.db.execute(query, {
                "study_id": study_id,
                "widget_id": widget_id,
                "filter_expression": filter_expression,
                "dataset_name": dataset_name,
                "is_valid": is_valid,
                "validation_errors": json.dumps(errors) if errors else None,
                "validated_columns": json.dumps(validated_columns) if validated_columns else None
            })
            self.db.commit()
            
        except Exception as e:
            self.logger.error(f"Failed to cache validation result: {str(e)}")
            self.db.rollback()
    
    def _log_audit(
        self,
        study_id: str,
        widget_id: str,
        action: str,
        expression: str,
        user_id: str,
        details: Dict[str, Any]
    ):
        """Log audit entry for filter operation"""
        try:
            from sqlalchemy import text
            
            query = text("""
                INSERT INTO filter_audit_log 
                (id, study_id, widget_id, action, new_expression, user_id, created_at, details)
                VALUES 
                (gen_random_uuid(), :study_id, :widget_id, :action, :expression, 
                 :user_id, NOW(), :details)
            """)
            
            self.db.execute(query, {
                "study_id": study_id,
                "widget_id": widget_id,
                "action": action,
                "expression": expression,
                "user_id": user_id,
                "details": json.dumps(details)
            })
            self.db.commit()
            
        except Exception as e:
            self.logger.error(f"Failed to log audit entry: {str(e)}")
            self.db.rollback()
    
    def get_cached_validation(
        self,
        study_id: str,
        widget_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get cached validation result"""
        try:
            from sqlalchemy import text
            
            query = text("""
                SELECT filter_expression, dataset_name, is_valid, 
                       validation_errors, validated_columns, last_validated
                FROM filter_validation_cache
                WHERE study_id = :study_id AND widget_id = :widget_id
            """)
            
            result = self.db.execute(query, {
                "study_id": study_id,
                "widget_id": widget_id
            }).first()
            
            if result:
                return {
                    "filter_expression": result[0],
                    "dataset_name": result[1],
                    "is_valid": result[2],
                    "errors": json.loads(result[3]) if result[3] else [],
                    "validated_columns": json.loads(result[4]) if result[4] else [],
                    "last_validated": result[5]
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get cached validation: {str(e)}")
            return None