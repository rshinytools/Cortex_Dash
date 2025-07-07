# ABOUTME: SQL query builder for widget data with field mapping support
# ABOUTME: Builds safe parameterized queries based on widget configuration and data contracts

from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
import logging
from datetime import datetime, date

from sqlalchemy import text, select, func, and_, or_, desc, asc
from sqlalchemy.sql import Select
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class DataSourceType(str, Enum):
    """Supported data source types"""
    POSTGRESQL = "postgresql"
    PARQUET = "parquet"
    CSV = "csv"
    SAS = "sas"
    API = "api"


class QueryFilter(BaseModel):
    """Filter specification for queries"""
    field: str
    operator: str  # eq, ne, gt, lt, gte, lte, in, not_in, like, between
    value: Any
    field_type: Optional[str] = "string"


class QuerySort(BaseModel):
    """Sort specification for queries"""
    field: str
    direction: str = "asc"  # asc or desc


class QueryPagination(BaseModel):
    """Pagination specification for queries"""
    page: int = 1
    page_size: int = 20


class QueryBuilder:
    """Builds SQL queries for widget data retrieval"""
    
    def __init__(self, data_source_type: DataSourceType = DataSourceType.POSTGRESQL):
        self.data_source_type = data_source_type
        self.supported_operators = {
            "eq": "=",
            "ne": "!=",
            "gt": ">",
            "lt": "<",
            "gte": ">=",
            "lte": "<=",
            "in": "IN",
            "not_in": "NOT IN",
            "like": "LIKE",
            "ilike": "ILIKE",
            "between": "BETWEEN",
            "is_null": "IS NULL",
            "is_not_null": "IS NOT NULL"
        }
    
    def build_metric_query(self, 
                          table_name: str,
                          aggregation: str,
                          field: Optional[str] = None,
                          filters: Optional[List[QueryFilter]] = None,
                          field_mappings: Optional[Dict[str, str]] = None) -> Tuple[str, Dict[str, Any]]:
        """Build query for metric widgets"""
        
        # Apply field mappings
        if field and field_mappings:
            field = field_mappings.get(field, field)
        
        # Build SELECT clause based on aggregation
        if aggregation == "count":
            select_clause = "COUNT(*)"
        elif aggregation == "distinct":
            if not field:
                raise ValueError("Field is required for DISTINCT aggregation")
            select_clause = f"COUNT(DISTINCT {self._quote_identifier(field)})"
        elif aggregation in ["sum", "avg", "min", "max"]:
            if not field:
                raise ValueError(f"Field is required for {aggregation.upper()} aggregation")
            select_clause = f"{aggregation.upper()}({self._quote_identifier(field)})"
        else:
            raise ValueError(f"Unsupported aggregation: {aggregation}")
        
        # Build base query
        query = f"SELECT {select_clause} AS value FROM {self._quote_identifier(table_name)}"
        
        # Add filters
        params = {}
        where_conditions = []
        if filters:
            for i, filter_spec in enumerate(filters):
                condition, filter_params = self._build_filter_condition(filter_spec, i, field_mappings)
                where_conditions.append(condition)
                params.update(filter_params)
        
        if where_conditions:
            query += " WHERE " + " AND ".join(where_conditions)
        
        return query, params
    
    def build_chart_query(self,
                         table_name: str,
                         x_axis_field: str,
                         y_axis_field: str,
                         aggregation: str = "count",
                         group_by_field: Optional[str] = None,
                         filters: Optional[List[QueryFilter]] = None,
                         field_mappings: Optional[Dict[str, str]] = None,
                         limit: int = 1000) -> Tuple[str, Dict[str, Any]]:
        """Build query for chart widgets"""
        
        # Apply field mappings
        if field_mappings:
            x_axis_field = field_mappings.get(x_axis_field, x_axis_field)
            y_axis_field = field_mappings.get(y_axis_field, y_axis_field) if y_axis_field else None
            group_by_field = field_mappings.get(group_by_field, group_by_field) if group_by_field else None
        
        # Build SELECT clause
        select_parts = [f"{self._quote_identifier(x_axis_field)} AS x_value"]
        
        if group_by_field:
            select_parts.append(f"{self._quote_identifier(group_by_field)} AS group_value")
        
        # Add aggregation
        if aggregation == "count":
            select_parts.append("COUNT(*) AS y_value")
        elif y_axis_field and aggregation in ["sum", "avg", "min", "max"]:
            select_parts.append(f"{aggregation.upper()}({self._quote_identifier(y_axis_field)}) AS y_value")
        else:
            raise ValueError(f"Invalid aggregation '{aggregation}' for chart query")
        
        # Build query
        query = f"SELECT {', '.join(select_parts)} FROM {self._quote_identifier(table_name)}"
        
        # Add filters
        params = {}
        where_conditions = []
        if filters:
            for i, filter_spec in enumerate(filters):
                condition, filter_params = self._build_filter_condition(filter_spec, i, field_mappings)
                where_conditions.append(condition)
                params.update(filter_params)
        
        if where_conditions:
            query += " WHERE " + " AND ".join(where_conditions)
        
        # Add GROUP BY
        group_by_parts = [self._quote_identifier(x_axis_field)]
        if group_by_field:
            group_by_parts.append(self._quote_identifier(group_by_field))
        query += f" GROUP BY {', '.join(group_by_parts)}"
        
        # Add ORDER BY
        query += f" ORDER BY {self._quote_identifier(x_axis_field)}"
        
        # Add LIMIT
        query += f" LIMIT {limit}"
        
        return query, params
    
    def build_table_query(self,
                         table_name: str,
                         columns: List[str],
                         filters: Optional[List[QueryFilter]] = None,
                         sorts: Optional[List[QuerySort]] = None,
                         pagination: Optional[QueryPagination] = None,
                         field_mappings: Optional[Dict[str, str]] = None) -> Tuple[str, Dict[str, Any]]:
        """Build query for table widgets"""
        
        # Apply field mappings to columns
        if field_mappings:
            columns = [field_mappings.get(col, col) for col in columns]
        
        # Build SELECT clause
        select_parts = [self._quote_identifier(col) for col in columns]
        query = f"SELECT {', '.join(select_parts)} FROM {self._quote_identifier(table_name)}"
        
        # Add filters
        params = {}
        where_conditions = []
        if filters:
            for i, filter_spec in enumerate(filters):
                condition, filter_params = self._build_filter_condition(filter_spec, i, field_mappings)
                where_conditions.append(condition)
                params.update(filter_params)
        
        if where_conditions:
            query += " WHERE " + " AND ".join(where_conditions)
        
        # Add ORDER BY
        if sorts:
            order_parts = []
            for sort in sorts:
                field = field_mappings.get(sort.field, sort.field) if field_mappings else sort.field
                direction = "DESC" if sort.direction.lower() == "desc" else "ASC"
                order_parts.append(f"{self._quote_identifier(field)} {direction}")
            query += f" ORDER BY {', '.join(order_parts)}"
        
        # Add pagination
        if pagination:
            offset = (pagination.page - 1) * pagination.page_size
            query += f" LIMIT {pagination.page_size} OFFSET {offset}"
        
        return query, params
    
    def build_count_query(self,
                         table_name: str,
                         filters: Optional[List[QueryFilter]] = None,
                         field_mappings: Optional[Dict[str, str]] = None) -> Tuple[str, Dict[str, Any]]:
        """Build query to count total rows (for pagination)"""
        
        query = f"SELECT COUNT(*) AS total FROM {self._quote_identifier(table_name)}"
        
        # Add filters
        params = {}
        where_conditions = []
        if filters:
            for i, filter_spec in enumerate(filters):
                condition, filter_params = self._build_filter_condition(filter_spec, i, field_mappings)
                where_conditions.append(condition)
                params.update(filter_params)
        
        if where_conditions:
            query += " WHERE " + " AND ".join(where_conditions)
        
        return query, params
    
    def _build_filter_condition(self, 
                               filter_spec: QueryFilter, 
                               param_index: int,
                               field_mappings: Optional[Dict[str, str]] = None) -> Tuple[str, Dict[str, Any]]:
        """Build a single filter condition"""
        
        # Apply field mapping
        field = filter_spec.field
        if field_mappings:
            field = field_mappings.get(field, field)
        
        field_quoted = self._quote_identifier(field)
        operator = filter_spec.operator.lower()
        param_name = f"filter_{param_index}"
        
        if operator not in self.supported_operators:
            raise ValueError(f"Unsupported operator: {operator}")
        
        # Handle special operators
        if operator == "is_null":
            return f"{field_quoted} IS NULL", {}
        elif operator == "is_not_null":
            return f"{field_quoted} IS NOT NULL", {}
        elif operator == "in":
            if not isinstance(filter_spec.value, list):
                raise ValueError("IN operator requires a list value")
            placeholders = [f":{param_name}_{i}" for i in range(len(filter_spec.value))]
            condition = f"{field_quoted} IN ({', '.join(placeholders)})"
            params = {f"{param_name}_{i}": val for i, val in enumerate(filter_spec.value)}
            return condition, params
        elif operator == "not_in":
            if not isinstance(filter_spec.value, list):
                raise ValueError("NOT IN operator requires a list value")
            placeholders = [f":{param_name}_{i}" for i in range(len(filter_spec.value))]
            condition = f"{field_quoted} NOT IN ({', '.join(placeholders)})"
            params = {f"{param_name}_{i}": val for i, val in enumerate(filter_spec.value)}
            return condition, params
        elif operator == "between":
            if not isinstance(filter_spec.value, list) or len(filter_spec.value) != 2:
                raise ValueError("BETWEEN operator requires a list with exactly 2 values")
            condition = f"{field_quoted} BETWEEN :{param_name}_0 AND :{param_name}_1"
            params = {
                f"{param_name}_0": filter_spec.value[0],
                f"{param_name}_1": filter_spec.value[1]
            }
            return condition, params
        elif operator in ["like", "ilike"]:
            # Add wildcards if not present
            value = filter_spec.value
            if not value.startswith("%") and not value.endswith("%"):
                value = f"%{value}%"
            condition = f"{field_quoted} {self.supported_operators[operator]} :{param_name}"
            return condition, {param_name: value}
        else:
            # Standard operators
            sql_operator = self.supported_operators[operator]
            condition = f"{field_quoted} {sql_operator} :{param_name}"
            return condition, {param_name: filter_spec.value}
    
    def _quote_identifier(self, identifier: str) -> str:
        """Quote identifier to prevent SQL injection"""
        if self.data_source_type == DataSourceType.POSTGRESQL:
            # PostgreSQL uses double quotes
            return f'"{identifier}"'
        else:
            # Most others use backticks or square brackets
            return f"`{identifier}`"
    
    def validate_query(self, query: str) -> bool:
        """Basic validation to prevent SQL injection"""
        # Check for common SQL injection patterns
        dangerous_patterns = [
            ";",  # Multiple statements
            "--",  # SQL comments
            "/*",  # Block comments
            "*/",
            "xp_",  # SQL Server extended procedures
            "sp_",  # Stored procedures
            "DROP",
            "DELETE",
            "TRUNCATE",
            "EXEC",
            "EXECUTE",
            "INSERT",
            "UPDATE",
            "CREATE",
            "ALTER",
            "GRANT",
            "REVOKE"
        ]
        
        query_upper = query.upper()
        for pattern in dangerous_patterns:
            if pattern.upper() in query_upper:
                logger.warning(f"Potentially dangerous SQL pattern detected: {pattern}")
                return False
        
        return True