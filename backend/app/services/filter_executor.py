# ABOUTME: Filter executor service for widget filtering
# ABOUTME: Executes SQL WHERE clauses on Parquet datasets using PyArrow and Pandas

import time
import logging
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import pyarrow.parquet as pq
import pyarrow.compute as pc
import pandas as pd
from datetime import datetime
from sqlalchemy.orm import Session

from app.models import Study
from app.services.filter_parser import (
    FilterParser, ASTNode, ColumnNode, LiteralNode,
    BinaryOpNode, UnaryOpNode, InNode, BetweenNode,
    LikeNode, IsNullNode, TokenType
)

logger = logging.getLogger(__name__)


class FilterExecutor:
    """Executes filter expressions on Parquet datasets"""
    
    def __init__(self, db: Session):
        self.db = db
        self.parser = FilterParser()
        self.logger = logger
    
    def execute_filter(
        self,
        study_id: str,
        widget_id: str,
        filter_expression: str,
        dataset_path: Union[str, Path],
        columns: Optional[List[str]] = None,
        track_metrics: bool = True
    ) -> Dict[str, Any]:
        """
        Execute a filter expression on a Parquet dataset
        
        Args:
            study_id: Study ID
            widget_id: Widget ID
            filter_expression: SQL WHERE clause expression
            dataset_path: Path to the Parquet file
            columns: Specific columns to read (None for all)
            track_metrics: Whether to track execution metrics
            
        Returns:
            Dictionary containing:
            - data: Filtered DataFrame
            - row_count: Number of rows after filtering
            - original_count: Number of rows before filtering
            - execution_time_ms: Execution time in milliseconds
            - filter_applied: The filter expression that was applied
        """
        start_time = time.time()
        
        try:
            # Parse the filter expression
            parse_result = self.parser.parse(filter_expression)
            if not parse_result["is_valid"]:
                raise ValueError(f"Invalid filter expression: {parse_result['error']}")
            
            # Read the Parquet file
            dataset_path = Path(dataset_path)
            if not dataset_path.exists():
                raise FileNotFoundError(f"Dataset not found: {dataset_path}")
            
            # Determine columns to read
            filter_columns = parse_result["columns"]
            if columns:
                # Include both requested columns and filter columns
                read_columns = list(set(columns + filter_columns))
            else:
                read_columns = None  # Read all columns
            
            # Read data with PyArrow for better performance
            df = pd.read_parquet(dataset_path, columns=read_columns)
            original_count = len(df)
            
            # Apply the filter
            if parse_result["ast"]:
                # Convert AST to pandas query
                pandas_query = self._ast_to_pandas_query(parse_result["ast"])
                
                # Special case: handle "1=1" or "True" which means no filtering
                if pandas_query in ["True", "1 == 1", "(1) == (1)"]:
                    filtered_df = df
                else:
                    # Execute the query
                    try:
                        filtered_df = df.query(pandas_query)
                    except Exception as e:
                        # Fallback to manual filtering if query fails
                        self.logger.warning(f"Pandas query failed, using manual filtering: {e}")
                        mask = self._evaluate_ast(parse_result["ast"], df)
                        filtered_df = df[mask]
            else:
                filtered_df = df
            
            filtered_count = len(filtered_df)
            
            # Calculate execution time
            execution_time_ms = (time.time() - start_time) * 1000
            
            # Track metrics if requested
            if track_metrics:
                self._track_execution_metrics(
                    study_id=study_id,
                    widget_id=widget_id,
                    filter_expression=filter_expression,
                    execution_time_ms=execution_time_ms,
                    rows_before=original_count,
                    rows_after=filtered_count
                )
            
            return {
                "data": filtered_df,
                "row_count": filtered_count,
                "original_count": original_count,
                "execution_time_ms": execution_time_ms,
                "filter_applied": filter_expression,
                "reduction_percentage": round((1 - filtered_count/original_count) * 100, 2) if original_count > 0 else 0
            }
            
        except Exception as e:
            self.logger.error(f"Failed to execute filter: {str(e)}")
            execution_time_ms = (time.time() - start_time) * 1000
            
            return {
                "data": pd.DataFrame(),
                "row_count": 0,
                "original_count": 0,
                "execution_time_ms": execution_time_ms,
                "filter_applied": filter_expression,
                "error": str(e)
            }
    
    def execute_filter_pyarrow(
        self,
        study_id: str,
        widget_id: str,
        filter_expression: str,
        dataset_path: Union[str, Path],
        columns: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Execute filter using PyArrow for better performance on large datasets
        
        This method pushes filtering down to the Parquet reader level
        for optimal performance.
        """
        start_time = time.time()
        
        try:
            # Parse the filter expression
            parse_result = self.parser.parse(filter_expression)
            if not parse_result["is_valid"]:
                raise ValueError(f"Invalid filter expression: {parse_result['error']}")
            
            dataset_path = Path(dataset_path)
            if not dataset_path.exists():
                raise FileNotFoundError(f"Dataset not found: {dataset_path}")
            
            # Open Parquet file
            parquet_file = pq.ParquetFile(dataset_path)
            
            # Get row count before filtering
            original_count = parquet_file.metadata.num_rows
            
            # Convert AST to PyArrow filter expression
            if parse_result["ast"]:
                arrow_filter = self._ast_to_arrow_filter(parse_result["ast"])
                
                # Read with filter pushed down
                table = pq.read_table(
                    dataset_path,
                    columns=columns,
                    filters=arrow_filter if arrow_filter else None
                )
            else:
                table = pq.read_table(dataset_path, columns=columns)
            
            # Convert to pandas DataFrame
            df = table.to_pandas()
            filtered_count = len(df)
            
            execution_time_ms = (time.time() - start_time) * 1000
            
            return {
                "data": df,
                "row_count": filtered_count,
                "original_count": original_count,
                "execution_time_ms": execution_time_ms,
                "filter_applied": filter_expression,
                "reduction_percentage": round((1 - filtered_count/original_count) * 100, 2) if original_count > 0 else 0
            }
            
        except Exception as e:
            self.logger.error(f"Failed to execute PyArrow filter: {str(e)}")
            execution_time_ms = (time.time() - start_time) * 1000
            
            return {
                "data": pd.DataFrame(),
                "row_count": 0,
                "original_count": 0,
                "execution_time_ms": execution_time_ms,
                "filter_applied": filter_expression,
                "error": str(e)
            }
    
    def _ast_to_pandas_query(self, node: ASTNode) -> str:
        """Convert AST to pandas query string"""
        if isinstance(node, ColumnNode):
            # Escape column name if needed
            if ' ' in node.name or '-' in node.name:
                return f"`{node.name}`"
            return node.name
        
        elif isinstance(node, LiteralNode):
            if node.value is None:
                return "None"
            elif isinstance(node.value, str):
                # Escape single quotes in string
                escaped = node.value.replace("'", "\\'")
                return f"'{escaped}'"
            elif isinstance(node.value, bool):
                return str(node.value)
            elif isinstance(node.value, (int, float)):
                return str(node.value)
            else:
                return str(node.value)
        
        elif isinstance(node, BinaryOpNode):
            left = self._ast_to_pandas_query(node.left)
            right = self._ast_to_pandas_query(node.right)
            
            if node.operator == TokenType.AND:
                return f"({left}) & ({right})"
            elif node.operator == TokenType.OR:
                return f"({left}) | ({right})"
            elif node.operator == TokenType.EQ:
                return f"{left} == {right}"
            elif node.operator == TokenType.NEQ:
                return f"{left} != {right}"
            elif node.operator == TokenType.LT:
                return f"{left} < {right}"
            elif node.operator == TokenType.LTE:
                return f"{left} <= {right}"
            elif node.operator == TokenType.GT:
                return f"{left} > {right}"
            elif node.operator == TokenType.GTE:
                return f"{left} >= {right}"
            else:
                raise ValueError(f"Unsupported operator: {node.operator}")
        
        elif isinstance(node, UnaryOpNode):
            operand = self._ast_to_pandas_query(node.operand)
            if node.operator == TokenType.NOT:
                return f"~({operand})"
            else:
                raise ValueError(f"Unsupported unary operator: {node.operator}")
        
        elif isinstance(node, InNode):
            column = self._ast_to_pandas_query(node.column)
            values = [self._ast_to_pandas_query(v) for v in node.values]
            values_str = f"[{', '.join(values)}]"
            
            if node.negate:
                return f"~({column}.isin({values_str}))"
            else:
                return f"{column}.isin({values_str})"
        
        elif isinstance(node, BetweenNode):
            column = self._ast_to_pandas_query(node.column)
            lower = self._ast_to_pandas_query(node.lower)
            upper = self._ast_to_pandas_query(node.upper)
            return f"({column} >= {lower}) & ({column} <= {upper})"
        
        elif isinstance(node, LikeNode):
            column = self._ast_to_pandas_query(node.column)
            # Convert SQL LIKE pattern to regex
            pattern = node.pattern.replace("%", ".*").replace("_", ".")
            
            if node.negate:
                return f"~({column}.str.contains('{pattern}', na=False, regex=True))"
            else:
                return f"{column}.str.contains('{pattern}', na=False, regex=True)"
        
        elif isinstance(node, IsNullNode):
            column = self._ast_to_pandas_query(node.column)
            if node.negate:
                return f"{column}.notna()"
            else:
                return f"{column}.isna()"
        
        else:
            raise ValueError(f"Unsupported node type: {type(node)}")
    
    def _evaluate_ast(self, node: ASTNode, df: pd.DataFrame) -> pd.Series:
        """Manually evaluate AST on DataFrame (fallback method)"""
        if isinstance(node, ColumnNode):
            return df[node.name]
        
        elif isinstance(node, LiteralNode):
            return pd.Series([node.value] * len(df), index=df.index)
        
        elif isinstance(node, BinaryOpNode):
            left = self._evaluate_ast(node.left, df)
            right = self._evaluate_ast(node.right, df)
            
            if node.operator == TokenType.AND:
                return left & right
            elif node.operator == TokenType.OR:
                return left | right
            elif node.operator == TokenType.EQ:
                return left == right
            elif node.operator == TokenType.NEQ:
                return left != right
            elif node.operator == TokenType.LT:
                return left < right
            elif node.operator == TokenType.LTE:
                return left <= right
            elif node.operator == TokenType.GT:
                return left > right
            elif node.operator == TokenType.GTE:
                return left >= right
            else:
                raise ValueError(f"Unsupported operator: {node.operator}")
        
        elif isinstance(node, UnaryOpNode):
            operand = self._evaluate_ast(node.operand, df)
            if node.operator == TokenType.NOT:
                return ~operand
            else:
                raise ValueError(f"Unsupported unary operator: {node.operator}")
        
        elif isinstance(node, InNode):
            column = df[node.column.name]
            values = [v.value for v in node.values]
            result = column.isin(values)
            return ~result if node.negate else result
        
        elif isinstance(node, BetweenNode):
            column = df[node.column.name]
            return (column >= node.lower.value) & (column <= node.upper.value)
        
        elif isinstance(node, LikeNode):
            column = df[node.column.name]
            # Convert SQL LIKE pattern to regex
            pattern = node.pattern.replace("%", ".*").replace("_", ".")
            result = column.str.contains(pattern, na=False, regex=True)
            return ~result if node.negate else result
        
        elif isinstance(node, IsNullNode):
            column = df[node.column.name]
            result = column.isna()
            return ~result if node.negate else result
        
        else:
            raise ValueError(f"Unsupported node type: {type(node)}")
    
    def _ast_to_arrow_filter(self, node: ASTNode) -> Optional[List]:
        """
        Convert AST to PyArrow filter format for pushdown
        
        PyArrow filters are in DNF (Disjunctive Normal Form):
        [[('col1', '=', val1), ('col2', '>', val2)], ...]
        where inner lists are AND'd and outer lists are OR'd
        """
        try:
            # For now, we'll convert simple cases
            # Complex expressions will fall back to pandas filtering
            if isinstance(node, BinaryOpNode):
                if node.operator == TokenType.EQ:
                    if isinstance(node.left, ColumnNode) and isinstance(node.right, LiteralNode):
                        return [[(node.left.name, '==', node.right.value)]]
                elif node.operator == TokenType.NEQ:
                    if isinstance(node.left, ColumnNode) and isinstance(node.right, LiteralNode):
                        return [[(node.left.name, '!=', node.right.value)]]
                elif node.operator == TokenType.LT:
                    if isinstance(node.left, ColumnNode) and isinstance(node.right, LiteralNode):
                        return [[(node.left.name, '<', node.right.value)]]
                elif node.operator == TokenType.LTE:
                    if isinstance(node.left, ColumnNode) and isinstance(node.right, LiteralNode):
                        return [[(node.left.name, '<=', node.right.value)]]
                elif node.operator == TokenType.GT:
                    if isinstance(node.left, ColumnNode) and isinstance(node.right, LiteralNode):
                        return [[(node.left.name, '>', node.right.value)]]
                elif node.operator == TokenType.GTE:
                    if isinstance(node.left, ColumnNode) and isinstance(node.right, LiteralNode):
                        return [[(node.left.name, '>=', node.right.value)]]
            
            elif isinstance(node, InNode):
                if not node.negate:
                    return [[(node.column.name, 'in', [v.value for v in node.values])]]
            
            elif isinstance(node, IsNullNode):
                if not node.negate:
                    return [[(node.column.name, 'is', None)]]
                else:
                    return [[(node.column.name, 'is not', None)]]
            
            # For complex expressions, return None to use pandas filtering
            return None
            
        except Exception as e:
            self.logger.warning(f"Could not convert to Arrow filter: {e}")
            return None
    
    def _track_execution_metrics(
        self,
        study_id: str,
        widget_id: str,
        filter_expression: str,
        execution_time_ms: int,
        rows_before: int,
        rows_after: int
    ):
        """Track filter execution metrics"""
        try:
            from sqlalchemy import text
            
            reduction_pct = round((1 - rows_after/rows_before) * 100, 2) if rows_before > 0 else 0
            
            query = text("""
                INSERT INTO filter_metrics 
                (id, study_id, widget_id, filter_expression, execution_time_ms,
                 rows_before, rows_after, reduction_percentage, executed_at)
                VALUES 
                (gen_random_uuid(), :study_id, :widget_id, :filter_expression, :execution_time_ms,
                 :rows_before, :rows_after, :reduction_percentage, NOW())
            """)
            
            self.db.execute(query, {
                "study_id": study_id,
                "widget_id": widget_id,
                "filter_expression": filter_expression,
                "execution_time_ms": execution_time_ms,
                "rows_before": rows_before,
                "rows_after": rows_after,
                "reduction_percentage": reduction_pct
            })
            self.db.commit()
            
        except Exception as e:
            self.logger.error(f"Failed to track execution metrics: {str(e)}")
            self.db.rollback()
    
    def get_execution_metrics(
        self,
        study_id: str,
        widget_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get execution metrics for filters"""
        try:
            from sqlalchemy import text
            
            if widget_id:
                query = text("""
                    SELECT widget_id, filter_expression, execution_time_ms,
                           rows_before, rows_after, reduction_percentage, executed_at
                    FROM filter_metrics
                    WHERE study_id = :study_id AND widget_id = :widget_id
                    ORDER BY executed_at DESC
                    LIMIT :limit
                """)
                params = {"study_id": study_id, "widget_id": widget_id, "limit": limit}
            else:
                query = text("""
                    SELECT widget_id, filter_expression, execution_time_ms,
                           rows_before, rows_after, reduction_percentage, executed_at
                    FROM filter_metrics
                    WHERE study_id = :study_id
                    ORDER BY executed_at DESC
                    LIMIT :limit
                """)
                params = {"study_id": study_id, "limit": limit}
            
            results = self.db.execute(query, params).fetchall()
            
            return [
                {
                    "widget_id": row[0],
                    "filter_expression": row[1],
                    "execution_time_ms": row[2],
                    "rows_before": row[3],
                    "rows_after": row[4],
                    "reduction_percentage": row[5],
                    "executed_at": row[6].isoformat() if row[6] else None
                }
                for row in results
            ]
            
        except Exception as e:
            self.logger.error(f"Failed to get execution metrics: {str(e)}")
            return []