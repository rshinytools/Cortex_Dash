# ABOUTME: Advanced filter executor with support for date ranges, subqueries, and complex conditions
# ABOUTME: Extends base executor with optimized handling of grouped conditions and relative dates

import time
import logging
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import pyarrow.parquet as pq
import pyarrow.compute as pc
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models import Study
from app.services.filter_executor import FilterExecutor
from app.services.advanced_filter_parser import (
    AdvancedFilterParser, DateRangeNode, SubqueryNode, GroupNode,
    ASTNode, ColumnNode, LiteralNode, BinaryOpNode, UnaryOpNode,
    InNode, BetweenNode, LikeNode, IsNullNode, TokenType
)

logger = logging.getLogger(__name__)


class AdvancedFilterExecutor(FilterExecutor):
    """Enhanced filter executor with advanced features"""
    
    def __init__(self, db: Session):
        super().__init__(db)
        self.parser = AdvancedFilterParser()
        self.subquery_cache = {}  # Cache subquery results
    
    def execute_filter(
        self,
        study_id: str,
        widget_id: str,
        filter_expression: str,
        dataset_path: Union[str, Path],
        columns: Optional[List[str]] = None,
        track_metrics: bool = True,
        context_datasets: Optional[Dict[str, Path]] = None
    ) -> Dict[str, Any]:
        """
        Enhanced filter execution with support for advanced features
        
        Args:
            study_id: Study ID
            widget_id: Widget ID
            filter_expression: SQL WHERE clause expression with advanced features
            dataset_path: Path to the primary Parquet file
            columns: Specific columns to read (None for all)
            track_metrics: Whether to track execution metrics
            context_datasets: Additional datasets for subqueries
            
        Returns:
            Dictionary containing filtered data and metrics
        """
        start_time = time.time()
        
        try:
            # Parse with advanced parser
            parse_result = self.parser.parse(filter_expression)
            if not parse_result["is_valid"]:
                raise ValueError(f"Invalid filter expression: {parse_result['error']}")
            
            # Read the primary dataset
            dataset_path = Path(dataset_path)
            if not dataset_path.exists():
                raise FileNotFoundError(f"Dataset not found: {dataset_path}")
            
            # Determine columns to read
            filter_columns = parse_result["columns"]
            if columns:
                read_columns = list(set(columns + filter_columns))
            else:
                read_columns = None
            
            # Read data
            df = pd.read_parquet(dataset_path, columns=read_columns)
            original_count = len(df)
            
            # Apply the filter with advanced features
            if parse_result["ast"]:
                mask = self._evaluate_advanced_ast(
                    parse_result["ast"], 
                    df, 
                    context_datasets
                )
                filtered_df = df[mask]
            else:
                filtered_df = df
            
            # Track metrics
            execution_time_ms = (time.time() - start_time) * 1000
            
            result = {
                "data": filtered_df,
                "row_count": len(filtered_df),
                "original_count": original_count,
                "execution_time_ms": execution_time_ms,
                "filter_applied": filter_expression,
                "filter_efficiency": (1 - len(filtered_df) / original_count) * 100 if original_count > 0 else 0,
                "has_date_ranges": parse_result.get("has_date_ranges", False),
                "has_subqueries": parse_result.get("has_subqueries", False)
            }
            
            # Log metrics if tracking
            if track_metrics:
                self._log_metrics(study_id, widget_id, result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Filter execution failed: {str(e)}")
            raise
    
    def _evaluate_advanced_ast(
        self, 
        node: ASTNode, 
        df: pd.DataFrame,
        context_datasets: Optional[Dict[str, Path]] = None
    ) -> pd.Series:
        """
        Evaluate AST with support for advanced node types
        """
        # Handle date range nodes
        if isinstance(node, DateRangeNode):
            return self._evaluate_date_range(node, df)
        
        # Handle subquery nodes
        elif isinstance(node, SubqueryNode):
            return self._evaluate_subquery(node, df, context_datasets)
        
        # Handle group nodes
        elif isinstance(node, GroupNode):
            return self._evaluate_group(node, df, context_datasets)
        
        # Handle standard nodes using base implementation
        else:
            return self._evaluate_ast(node, df)
    
    def _evaluate_date_range(self, node: DateRangeNode, df: pd.DataFrame) -> pd.Series:
        """
        Evaluate date range filter
        """
        column_name = node.column.name
        
        if column_name not in df.columns:
            raise ValueError(f"Column '{column_name}' not found in dataset")
        
        # Get absolute date range
        start_date, end_date = node.to_absolute_range()
        
        # Convert column to datetime if needed
        col_data = pd.to_datetime(df[column_name], errors='coerce')
        
        # Apply range filter
        mask = (col_data >= start_date) & (col_data <= end_date)
        
        self.logger.debug(f"Date range filter: {column_name} from {start_date} to {end_date}")
        
        return mask
    
    def _evaluate_subquery(
        self, 
        node: SubqueryNode, 
        df: pd.DataFrame,
        context_datasets: Optional[Dict[str, Path]] = None
    ) -> pd.Series:
        """
        Evaluate subquery filter
        """
        column_name = node.column.name
        
        if column_name not in df.columns:
            raise ValueError(f"Column '{column_name}' not found in dataset")
        
        # Check cache first
        cache_key = f"{node.query}_{node.dataset}"
        if cache_key in self.subquery_cache:
            subquery_result = self.subquery_cache[cache_key]
        else:
            # Execute subquery
            subquery_result = self._execute_subquery(node.query, node.dataset, context_datasets)
            self.subquery_cache[cache_key] = subquery_result
        
        # Apply the operator
        if node.operator == "IN":
            mask = df[column_name].isin(subquery_result)
        elif node.operator == "NOT IN":
            mask = ~df[column_name].isin(subquery_result)
        elif node.operator == "EXISTS":
            # For EXISTS, just check if subquery returns any results
            mask = pd.Series([len(subquery_result) > 0] * len(df), index=df.index)
        elif node.operator == "NOT EXISTS":
            mask = pd.Series([len(subquery_result) == 0] * len(df), index=df.index)
        else:
            raise ValueError(f"Unsupported subquery operator: {node.operator}")
        
        return mask
    
    def _execute_subquery(
        self, 
        query: str, 
        dataset: Optional[str],
        context_datasets: Optional[Dict[str, Path]] = None
    ) -> List[Any]:
        """
        Execute a subquery on a dataset
        
        Note: This is a simplified implementation. In production,
        you would use a proper SQL engine or query parser.
        """
        # Parse the subquery (simplified - extracts SELECT column and WHERE condition)
        import re
        
        # Extract components
        select_match = re.search(r'SELECT\s+(\w+)', query, re.IGNORECASE)
        from_match = re.search(r'FROM\s+(\w+)', query, re.IGNORECASE)
        where_match = re.search(r'WHERE\s+(.+)$', query, re.IGNORECASE)
        
        if not select_match or not from_match:
            raise ValueError(f"Invalid subquery: {query}")
        
        select_column = select_match.group(1)
        from_table = from_match.group(1)
        where_condition = where_match.group(1) if where_match else None
        
        # Determine dataset path
        if context_datasets and from_table in context_datasets:
            dataset_path = context_datasets[from_table]
        elif dataset:
            # Use provided dataset name
            dataset_path = Path(f"/data/{dataset}/{from_table}.parquet")
        else:
            raise ValueError(f"Cannot determine path for dataset: {from_table}")
        
        # Read the dataset
        if not dataset_path.exists():
            self.logger.warning(f"Subquery dataset not found: {dataset_path}")
            return []
        
        subquery_df = pd.read_parquet(dataset_path)
        
        # Apply WHERE condition if present
        if where_condition:
            # Parse and apply the WHERE condition
            # This is simplified - in production, use proper SQL parser
            try:
                filtered_df = subquery_df.query(where_condition)
            except:
                # Fallback to simple equality check
                parts = where_condition.split('=')
                if len(parts) == 2:
                    col = parts[0].strip()
                    val = parts[1].strip().strip("'\"")
                    filtered_df = subquery_df[subquery_df[col] == val]
                else:
                    filtered_df = subquery_df
        else:
            filtered_df = subquery_df
        
        # Return unique values from the selected column
        if select_column in filtered_df.columns:
            return filtered_df[select_column].unique().tolist()
        else:
            return []
    
    def _evaluate_group(
        self, 
        node: GroupNode, 
        df: pd.DataFrame,
        context_datasets: Optional[Dict[str, Path]] = None
    ) -> pd.Series:
        """
        Evaluate grouped conditions
        """
        if not node.conditions:
            return pd.Series([True] * len(df), index=df.index)
        
        # Evaluate each condition
        condition_masks = [
            self._evaluate_advanced_ast(cond, df, context_datasets)
            for cond in node.conditions
        ]
        
        # Combine based on operator
        if node.operator == TokenType.AND:
            # All conditions must be true
            result = condition_masks[0]
            for mask in condition_masks[1:]:
                result = result & mask
        elif node.operator == TokenType.OR:
            # At least one condition must be true
            result = condition_masks[0]
            for mask in condition_masks[1:]:
                result = result | mask
        else:
            raise ValueError(f"Unsupported group operator: {node.operator}")
        
        return result
    
    def _evaluate_ast(self, node: ASTNode, df: pd.DataFrame) -> pd.Series:
        """
        Extended AST evaluation for standard nodes
        """
        if isinstance(node, ColumnNode):
            if node.name not in df.columns:
                raise ValueError(f"Column '{node.name}' not found in dataset")
            return df[node.name]
        
        elif isinstance(node, LiteralNode):
            return pd.Series([node.value] * len(df), index=df.index)
        
        elif isinstance(node, BinaryOpNode):
            left = self._evaluate_advanced_ast(node.left, df, None)
            right = self._evaluate_advanced_ast(node.right, df, None)
            
            # Handle comparison operators
            if node.operator == TokenType.EQ:
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
            elif node.operator == TokenType.AND:
                return left & right
            elif node.operator == TokenType.OR:
                return left | right
            else:
                raise ValueError(f"Unsupported operator: {node.operator}")
        
        elif isinstance(node, UnaryOpNode):
            operand = self._evaluate_advanced_ast(node.operand, df, None)
            if node.operator == TokenType.NOT:
                return ~operand
            else:
                raise ValueError(f"Unsupported unary operator: {node.operator}")
        
        elif isinstance(node, InNode):
            column_data = df[node.column.name]
            values = [v.value for v in node.values]
            mask = column_data.isin(values)
            return ~mask if node.negate else mask
        
        elif isinstance(node, BetweenNode):
            column_data = df[node.column.name]
            return (column_data >= node.lower.value) & (column_data <= node.upper.value)
        
        elif isinstance(node, LikeNode):
            column_data = df[node.column.name].astype(str)
            # Convert SQL LIKE pattern to regex
            pattern = node.pattern.replace('%', '.*').replace('_', '.')
            mask = column_data.str.match(pattern, case=False)
            return ~mask if node.negate else mask
        
        elif isinstance(node, IsNullNode):
            column_data = df[node.column.name]
            mask = column_data.isna()
            return ~mask if node.negate else mask
        
        else:
            raise ValueError(f"Unsupported node type: {type(node)}")
    
    def _log_metrics(self, study_id: str, widget_id: str, result: Dict[str, Any]):
        """
        Log filter execution metrics for monitoring
        """
        self.logger.info(
            f"Filter executed - Study: {study_id}, Widget: {widget_id}, "
            f"Rows: {result['original_count']} -> {result['row_count']}, "
            f"Efficiency: {result['filter_efficiency']:.1f}%, "
            f"Time: {result['execution_time_ms']:.2f}ms"
        )
    
    def optimize_filter(self, filter_expression: str) -> str:
        """
        Optimize filter expression for better performance
        
        Examples:
        - Reorder conditions to filter on indexed columns first
        - Combine multiple IN clauses
        - Convert LIKE to equality when possible
        """
        # Parse the expression
        parse_result = self.parser.parse(filter_expression)
        
        if not parse_result["is_valid"]:
            return filter_expression
        
        # TODO: Implement optimization rules
        # For now, return as-is
        return filter_expression


# Example usage
if __name__ == "__main__":
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    # Create a test session
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    session = Session()
    
    executor = AdvancedFilterExecutor(session)
    
    # Test with date range
    result = executor.execute_filter(
        study_id="test",
        widget_id="widget1", 
        filter_expression="visit_date in last 30 days AND status = 'Active'",
        dataset_path="/data/test.parquet"
    )
    print("Date range result:", result)