# ABOUTME: Filter query builder for translating dashboard filters into data source queries
# ABOUTME: Handles filter optimization, validation, and conversion to various query formats

import json
import re
from datetime import datetime, date
from typing import Dict, List, Any, Optional, Union, Tuple
from enum import Enum
import pandas as pd
import logging

from app.services.widget_interaction_service import FilterDefinition, FilterOperator

logger = logging.getLogger(__name__)


class QueryType(str, Enum):
    """Supported query types"""
    SQL = "sql"
    PANDAS = "pandas"
    MONGO = "mongo"
    ELASTICSEARCH = "elasticsearch"
    PARQUET = "parquet"


class FilterQueryBuilder:
    """Builder for converting dashboard filters to data source queries"""
    
    def __init__(self):
        self.field_mappings: Dict[str, str] = {}
        self.type_mappings: Dict[str, str] = {}
        self.custom_operators: Dict[str, callable] = {}
        
    def set_field_mappings(self, mappings: Dict[str, str]) -> None:
        """Set field name mappings for the target data source"""
        self.field_mappings = mappings
    
    def set_type_mappings(self, mappings: Dict[str, str]) -> None:
        """Set data type mappings for the target data source"""
        self.type_mappings = mappings
    
    def add_custom_operator(self, operator: str, func: callable) -> None:
        """Add custom operator implementation"""
        self.custom_operators[operator] = func
    
    def build_query(
        self,
        filters: List[FilterDefinition],
        query_type: QueryType,
        base_query: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Build query from filters for specified query type"""
        
        if not filters:
            return base_query or {}
        
        # Filter out inactive filters
        active_filters = [f for f in filters if f.active]
        
        if not active_filters:
            return base_query or {}
        
        # Build query based on type
        if query_type == QueryType.SQL:
            return self._build_sql_query(active_filters, base_query)
        elif query_type == QueryType.PANDAS:
            return self._build_pandas_query(active_filters, base_query)
        elif query_type == QueryType.MONGO:
            return self._build_mongo_query(active_filters, base_query)
        elif query_type == QueryType.ELASTICSEARCH:
            return self._build_elasticsearch_query(active_filters, base_query)
        elif query_type == QueryType.PARQUET:
            return self._build_parquet_query(active_filters, base_query)
        else:
            raise ValueError(f"Unsupported query type: {query_type}")
    
    def _build_sql_query(
        self,
        filters: List[FilterDefinition],
        base_query: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Build SQL WHERE clause from filters"""
        
        where_conditions = []
        parameters = {}
        param_counter = 0
        
        for filter_def in filters:
            field = self._map_field_name(filter_def.field)
            
            # Validate field name for SQL injection prevention
            if not self._is_valid_sql_identifier(field):
                logger.warning(f"Invalid field name for SQL: {field}")
                continue
            
            condition, filter_params = self._build_sql_condition(
                field, 
                filter_def.operator, 
                filter_def.values,
                param_counter
            )
            
            if condition:
                where_conditions.append(condition)
                parameters.update(filter_params)
                param_counter += len(filter_params)
        
        query = base_query or {}
        
        if where_conditions:
            where_clause = " AND ".join(where_conditions)
            
            # Combine with existing WHERE clause if present
            if query.get("where"):
                where_clause = f"({query['where']}) AND ({where_clause})"
            
            query["where"] = where_clause
            query["parameters"] = {**query.get("parameters", {}), **parameters}
        
        return query
    
    def _build_sql_condition(
        self,
        field: str,
        operator: FilterOperator,
        values: List[Any],
        param_start: int
    ) -> Tuple[str, Dict[str, Any]]:
        """Build SQL condition for a single filter"""
        
        if not values and operator not in [FilterOperator.IS_NULL, FilterOperator.IS_NOT_NULL]:
            return "", {}
        
        parameters = {}
        
        if operator == FilterOperator.EQ:
            if len(values) == 1:
                param_name = f"param_{param_start}"
                parameters[param_name] = values[0]
                return f"{field} = :{param_name}", parameters
            else:
                # Multiple values - use IN
                param_names = [f"param_{param_start + i}" for i in range(len(values))]
                for i, value in enumerate(values):
                    parameters[param_names[i]] = value
                placeholders = ":" + ", :".join(param_names)
                return f"{field} IN ({placeholders})", parameters
        
        elif operator == FilterOperator.NE:
            if len(values) == 1:
                param_name = f"param_{param_start}"
                parameters[param_name] = values[0]
                return f"{field} != :{param_name}", parameters
            else:
                # Multiple values - use NOT IN
                param_names = [f"param_{param_start + i}" for i in range(len(values))]
                for i, value in enumerate(values):
                    parameters[param_names[i]] = value
                placeholders = ":" + ", :".join(param_names)
                return f"{field} NOT IN ({placeholders})", parameters
        
        elif operator == FilterOperator.GT:
            param_name = f"param_{param_start}"
            parameters[param_name] = values[0]
            return f"{field} > :{param_name}", parameters
        
        elif operator == FilterOperator.GTE:
            param_name = f"param_{param_start}"
            parameters[param_name] = values[0]
            return f"{field} >= :{param_name}", parameters
        
        elif operator == FilterOperator.LT:
            param_name = f"param_{param_start}"
            parameters[param_name] = values[0]
            return f"{field} < :{param_name}", parameters
        
        elif operator == FilterOperator.LTE:
            param_name = f"param_{param_start}"
            parameters[param_name] = values[0]
            return f"{field} <= :{param_name}", parameters
        
        elif operator == FilterOperator.IN:
            param_names = [f"param_{param_start + i}" for i in range(len(values))]
            for i, value in enumerate(values):
                parameters[param_names[i]] = value
            placeholders = ":" + ", :".join(param_names)
            return f"{field} IN ({placeholders})", parameters
        
        elif operator == FilterOperator.NOT_IN:
            param_names = [f"param_{param_start + i}" for i in range(len(values))]
            for i, value in enumerate(values):
                parameters[param_names[i]] = value
            placeholders = ":" + ", :".join(param_names)
            return f"{field} NOT IN ({placeholders})", parameters
        
        elif operator == FilterOperator.CONTAINS:
            param_name = f"param_{param_start}"
            parameters[param_name] = f"%{values[0]}%"
            return f"{field} LIKE :{param_name}", parameters
        
        elif operator == FilterOperator.STARTS_WITH:
            param_name = f"param_{param_start}"
            parameters[param_name] = f"{values[0]}%"
            return f"{field} LIKE :{param_name}", parameters
        
        elif operator == FilterOperator.ENDS_WITH:
            param_name = f"param_{param_start}"
            parameters[param_name] = f"%{values[0]}"
            return f"{field} LIKE :{param_name}", parameters
        
        elif operator == FilterOperator.IS_NULL:
            return f"{field} IS NULL", parameters
        
        elif operator == FilterOperator.IS_NOT_NULL:
            return f"{field} IS NOT NULL", parameters
        
        else:
            logger.warning(f"Unsupported SQL operator: {operator}")
            return "", {}
    
    def _build_pandas_query(
        self,
        filters: List[FilterDefinition],
        base_query: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Build pandas query expressions from filters"""
        
        query_expressions = []
        
        for filter_def in filters:
            field = self._map_field_name(filter_def.field)
            
            # Escape field name for pandas query
            field_escaped = f"`{field}`" if " " in field else field
            
            expression = self._build_pandas_expression(
                field_escaped,
                filter_def.operator,
                filter_def.values
            )
            
            if expression:
                query_expressions.append(expression)
        
        query = base_query or {}
        
        if query_expressions:
            combined_query = " and ".join(f"({expr})" for expr in query_expressions)
            
            # Combine with existing query if present
            if query.get("query"):
                combined_query = f"({query['query']}) and ({combined_query})"
            
            query["query"] = combined_query
        
        return query
    
    def _build_pandas_expression(
        self,
        field: str,
        operator: FilterOperator,
        values: List[Any]
    ) -> str:
        """Build pandas query expression for a single filter"""
        
        if not values and operator not in [FilterOperator.IS_NULL, FilterOperator.IS_NOT_NULL]:
            return ""
        
        # Convert values to pandas-compatible format
        formatted_values = [self._format_pandas_value(v) for v in values]
        
        if operator == FilterOperator.EQ:
            if len(values) == 1:
                return f"{field} == {formatted_values[0]}"
            else:
                values_str = "[" + ", ".join(formatted_values) + "]"
                return f"{field}.isin({values_str})"
        
        elif operator == FilterOperator.NE:
            if len(values) == 1:
                return f"{field} != {formatted_values[0]}"
            else:
                values_str = "[" + ", ".join(formatted_values) + "]"
                return f"~{field}.isin({values_str})"
        
        elif operator == FilterOperator.GT:
            return f"{field} > {formatted_values[0]}"
        
        elif operator == FilterOperator.GTE:
            return f"{field} >= {formatted_values[0]}"
        
        elif operator == FilterOperator.LT:
            return f"{field} < {formatted_values[0]}"
        
        elif operator == FilterOperator.LTE:
            return f"{field} <= {formatted_values[0]}"
        
        elif operator == FilterOperator.IN:
            values_str = "[" + ", ".join(formatted_values) + "]"
            return f"{field}.isin({values_str})"
        
        elif operator == FilterOperator.NOT_IN:
            values_str = "[" + ", ".join(formatted_values) + "]"
            return f"~{field}.isin({values_str})"
        
        elif operator == FilterOperator.CONTAINS:
            return f"{field}.str.contains({formatted_values[0]}, na=False)"
        
        elif operator == FilterOperator.STARTS_WITH:
            return f"{field}.str.startswith({formatted_values[0]}, na=False)"
        
        elif operator == FilterOperator.ENDS_WITH:
            return f"{field}.str.endswith({formatted_values[0]}, na=False)"
        
        elif operator == FilterOperator.IS_NULL:
            return f"{field}.isna()"
        
        elif operator == FilterOperator.IS_NOT_NULL:
            return f"{field}.notna()"
        
        else:
            logger.warning(f"Unsupported pandas operator: {operator}")
            return ""
    
    def _build_mongo_query(
        self,
        filters: List[FilterDefinition],
        base_query: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Build MongoDB query from filters"""
        
        conditions = []
        
        for filter_def in filters:
            field = self._map_field_name(filter_def.field)
            
            condition = self._build_mongo_condition(
                field,
                filter_def.operator,
                filter_def.values
            )
            
            if condition:
                conditions.append(condition)
        
        query = base_query or {}
        
        if conditions:
            if len(conditions) == 1:
                combined_condition = conditions[0]
            else:
                combined_condition = {"$and": conditions}
            
            # Combine with existing query
            if query:
                query = {"$and": [query, combined_condition]}
            else:
                query = combined_condition
        
        return query
    
    def _build_mongo_condition(
        self,
        field: str,
        operator: FilterOperator,
        values: List[Any]
    ) -> Dict[str, Any]:
        """Build MongoDB condition for a single filter"""
        
        if not values and operator not in [FilterOperator.IS_NULL, FilterOperator.IS_NOT_NULL]:
            return {}
        
        if operator == FilterOperator.EQ:
            if len(values) == 1:
                return {field: values[0]}
            else:
                return {field: {"$in": values}}
        
        elif operator == FilterOperator.NE:
            if len(values) == 1:
                return {field: {"$ne": values[0]}}
            else:
                return {field: {"$nin": values}}
        
        elif operator == FilterOperator.GT:
            return {field: {"$gt": values[0]}}
        
        elif operator == FilterOperator.GTE:
            return {field: {"$gte": values[0]}}
        
        elif operator == FilterOperator.LT:
            return {field: {"$lt": values[0]}}
        
        elif operator == FilterOperator.LTE:
            return {field: {"$lte": values[0]}}
        
        elif operator == FilterOperator.IN:
            return {field: {"$in": values}}
        
        elif operator == FilterOperator.NOT_IN:
            return {field: {"$nin": values}}
        
        elif operator == FilterOperator.CONTAINS:
            return {field: {"$regex": re.escape(str(values[0])), "$options": "i"}}
        
        elif operator == FilterOperator.STARTS_WITH:
            return {field: {"$regex": f"^{re.escape(str(values[0]))}", "$options": "i"}}
        
        elif operator == FilterOperator.ENDS_WITH:
            return {field: {"$regex": f"{re.escape(str(values[0]))}$", "$options": "i"}}
        
        elif operator == FilterOperator.IS_NULL:
            return {field: {"$eq": None}}
        
        elif operator == FilterOperator.IS_NOT_NULL:
            return {field: {"$ne": None}}
        
        else:
            logger.warning(f"Unsupported MongoDB operator: {operator}")
            return {}
    
    def _build_elasticsearch_query(
        self,
        filters: List[FilterDefinition],
        base_query: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Build Elasticsearch query from filters"""
        
        must_clauses = []
        
        for filter_def in filters:
            field = self._map_field_name(filter_def.field)
            
            clause = self._build_elasticsearch_clause(
                field,
                filter_def.operator,
                filter_def.values
            )
            
            if clause:
                must_clauses.append(clause)
        
        if not must_clauses:
            return base_query or {"query": {"match_all": {}}}
        
        # Build bool query
        bool_query = {"bool": {"must": must_clauses}}
        
        # Combine with base query if present
        if base_query and base_query.get("query"):
            bool_query["bool"]["must"].append(base_query["query"])
        
        query = base_query or {}
        query["query"] = bool_query
        
        return query
    
    def _build_elasticsearch_clause(
        self,
        field: str,
        operator: FilterOperator,
        values: List[Any]
    ) -> Dict[str, Any]:
        """Build Elasticsearch clause for a single filter"""
        
        if not values and operator not in [FilterOperator.IS_NULL, FilterOperator.IS_NOT_NULL]:
            return {}
        
        if operator == FilterOperator.EQ:
            if len(values) == 1:
                return {"term": {field: values[0]}}
            else:
                return {"terms": {field: values}}
        
        elif operator == FilterOperator.NE:
            if len(values) == 1:
                return {"bool": {"must_not": {"term": {field: values[0]}}}}
            else:
                return {"bool": {"must_not": {"terms": {field: values}}}}
        
        elif operator == FilterOperator.GT:
            return {"range": {field: {"gt": values[0]}}}
        
        elif operator == FilterOperator.GTE:
            return {"range": {field: {"gte": values[0]}}}
        
        elif operator == FilterOperator.LT:
            return {"range": {field: {"lt": values[0]}}}
        
        elif operator == FilterOperator.LTE:
            return {"range": {field: {"lte": values[0]}}}
        
        elif operator == FilterOperator.IN:
            return {"terms": {field: values}}
        
        elif operator == FilterOperator.NOT_IN:
            return {"bool": {"must_not": {"terms": {field: values}}}}
        
        elif operator == FilterOperator.CONTAINS:
            return {"wildcard": {field: f"*{values[0]}*"}}
        
        elif operator == FilterOperator.STARTS_WITH:
            return {"prefix": {field: values[0]}}
        
        elif operator == FilterOperator.ENDS_WITH:
            return {"wildcard": {field: f"*{values[0]}"}}
        
        elif operator == FilterOperator.IS_NULL:
            return {"bool": {"must_not": {"exists": {"field": field}}}}
        
        elif operator == FilterOperator.IS_NOT_NULL:
            return {"exists": {"field": field}}
        
        else:
            logger.warning(f"Unsupported Elasticsearch operator: {operator}")
            return {}
    
    def _build_parquet_query(
        self,
        filters: List[FilterDefinition],
        base_query: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Build Parquet filter expressions (PyArrow-style)"""
        
        # For Parquet, we'll build pandas-style expressions
        # that can be used with PyArrow or converted to PyArrow filters
        return self._build_pandas_query(filters, base_query)
    
    def _map_field_name(self, field: str) -> str:
        """Map field name using configured mappings"""
        return self.field_mappings.get(field, field)
    
    def _is_valid_sql_identifier(self, identifier: str) -> bool:
        """Validate SQL identifier for injection prevention"""
        # Basic validation - should be enhanced for production
        pattern = r"^[a-zA-Z_][a-zA-Z0-9_]*$"
        return re.match(pattern, identifier) is not None
    
    def _format_pandas_value(self, value: Any) -> str:
        """Format value for pandas query expression"""
        if isinstance(value, str):
            return f"'{value}'"
        elif isinstance(value, (datetime, date)):
            return f"'{value.isoformat()}'"
        elif value is None:
            return "None"
        else:
            return str(value)
    
    def optimize_filters(self, filters: List[FilterDefinition]) -> List[FilterDefinition]:
        """Optimize filter list by combining and simplifying conditions"""
        
        if not filters:
            return filters
        
        # Group filters by field
        field_groups = {}
        for filter_def in filters:
            field = filter_def.field
            if field not in field_groups:
                field_groups[field] = []
            field_groups[field].append(filter_def)
        
        optimized_filters = []
        
        for field, field_filters in field_groups.items():
            if len(field_filters) == 1:
                optimized_filters.append(field_filters[0])
            else:
                # Try to combine multiple filters on the same field
                combined = self._combine_field_filters(field_filters)
                optimized_filters.extend(combined)
        
        return optimized_filters
    
    def _combine_field_filters(self, filters: List[FilterDefinition]) -> List[FilterDefinition]:
        """Combine multiple filters on the same field"""
        
        if len(filters) <= 1:
            return filters
        
        # Group by operator type
        eq_filters = [f for f in filters if f.operator == FilterOperator.EQ]
        in_filters = [f for f in filters if f.operator == FilterOperator.IN]
        other_filters = [f for f in filters if f.operator not in [FilterOperator.EQ, FilterOperator.IN]]
        
        combined_filters = []
        
        # Combine EQ and IN filters
        if eq_filters or in_filters:
            all_values = []
            combined_filter = None
            
            for f in eq_filters + in_filters:
                all_values.extend(f.values)
                if combined_filter is None:
                    combined_filter = f
            
            if combined_filter:
                combined_filter.operator = FilterOperator.IN
                combined_filter.values = list(set(all_values))  # Remove duplicates
                combined_filters.append(combined_filter)
        
        # Add other filters as-is
        combined_filters.extend(other_filters)
        
        return combined_filters
    
    def validate_filters(self, filters: List[FilterDefinition]) -> List[str]:
        """Validate filters and return list of validation errors"""
        
        errors = []
        
        for i, filter_def in enumerate(filters):
            # Validate field name
            if not filter_def.field:
                errors.append(f"Filter {i}: Field name is required")
            
            # Validate operator
            if filter_def.operator not in FilterOperator:
                errors.append(f"Filter {i}: Invalid operator '{filter_def.operator}'")
            
            # Validate values based on operator
            if filter_def.operator in [FilterOperator.IS_NULL, FilterOperator.IS_NOT_NULL]:
                # These operators don't need values
                pass
            elif not filter_def.values:
                errors.append(f"Filter {i}: Values are required for operator '{filter_def.operator}'")
            elif filter_def.operator in [FilterOperator.GT, FilterOperator.GTE, FilterOperator.LT, FilterOperator.LTE]:
                if len(filter_def.values) != 1:
                    errors.append(f"Filter {i}: Comparison operators require exactly one value")
        
        return errors


# Factory function
def get_filter_query_builder() -> FilterQueryBuilder:
    """Get filter query builder instance"""
    return FilterQueryBuilder()