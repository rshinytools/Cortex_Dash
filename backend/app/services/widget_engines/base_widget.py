# ABOUTME: Base widget engine class that all widget types inherit from
# ABOUTME: Provides common functionality for data fetching, aggregation, and caching

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import hashlib
import json
from enum import Enum
from uuid import UUID

from sqlalchemy import text, create_engine
from sqlalchemy.pool import NullPool
from sqlmodel import Session

from app.models.phase1_models import (
    DataGranularity, 
    AggregationType,
    JoinType
)


class WidgetEngine(ABC):
    """Base class for all widget engines"""
    
    def __init__(
        self,
        widget_id: UUID,
        study_id: UUID,
        mapping_config: Dict[str, Any],
        cache_ttl: Optional[int] = None
    ):
        self.widget_id = widget_id
        self.study_id = study_id
        self.mapping_config = mapping_config
        self.cache_ttl = cache_ttl or 3600  # Default 1 hour
        self.filters = []
        self.joins = []
        
    @abstractmethod
    def get_data_contract(self) -> Dict[str, Any]:
        """Return the data contract for this widget type"""
        pass
    
    @abstractmethod
    def validate_mapping(self) -> Tuple[bool, List[str]]:
        """Validate that mapping satisfies data contract"""
        pass
    
    @abstractmethod
    def build_query(self) -> str:
        """Build SQL query based on mapping configuration"""
        pass
    
    @abstractmethod
    def transform_results(self, raw_data: List[Dict]) -> Dict[str, Any]:
        """Transform raw query results into widget-specific format"""
        pass
    
    def get_cache_key(self, extra_params: Optional[Dict] = None) -> str:
        """Generate cache key for this query"""
        cache_data = {
            "widget_id": str(self.widget_id),
            "study_id": str(self.study_id),
            "mapping": self.mapping_config,
            "filters": self.filters,
            "extra": extra_params or {}
        }
        
        # Create hash of configuration
        cache_string = json.dumps(cache_data, sort_keys=True)
        cache_hash = hashlib.sha256(cache_string.encode()).hexdigest()
        
        return f"widget_{self.widget_id}_{cache_hash[:16]}"
    
    def check_cache(self, session: Session) -> Optional[Dict[str, Any]]:
        """Check if valid cached data exists"""
        # TODO: Implement caching with QueryCache model
        # cache_key = self.get_cache_key()
        # 
        # # Query cache table
        # cached = session.query(QueryCache).filter(
        #     QueryCache.cache_key == cache_key,
        #     QueryCache.expires_at > datetime.utcnow()
        # ).first()
        # 
        # if cached:
        #     # Update hit count
        #     cached.hit_count += 1
        #     cached.last_accessed = datetime.utcnow()
        #     session.commit()
        #     return cached.result_data
            
        return None
    
    def save_to_cache(
        self, 
        session: Session, 
        data: Dict[str, Any],
        execution_time_ms: int
    ):
        """Save query results to cache"""
        # TODO: Implement caching with QueryCache model
        # cache_key = self.get_cache_key()
        # expires_at = datetime.utcnow() + timedelta(seconds=self.cache_ttl)
        # 
        # # Check if cache entry exists
        # existing = session.query(QueryCache).filter(
        #     QueryCache.cache_key == cache_key
        # ).first()
        # 
        # if existing:
        #     # Update existing cache
        #     existing.result_data = data
        #     existing.expires_at = expires_at
        #     existing.execution_time_ms = execution_time_ms
        #     existing.created_at = datetime.utcnow()
        # else:
        #     # Create new cache entry
        #     cache_entry = QueryCache(
        #         cache_key=cache_key,
        #         study_id=self.study_id,
        #         widget_id=self.widget_id,
        #         query_hash=hashlib.sha256(self.build_query().encode()).hexdigest()[:64],
        #         query_text=self.build_query()[:5000],  # Truncate long queries
        #         result_data=data,
        #         result_count=len(data.get("data", [])) if isinstance(data.get("data"), list) else 1,
        #         execution_time_ms=execution_time_ms,
        #         expires_at=expires_at
        #     )
        #     session.add(cache_entry)
        # 
        # session.commit()
        pass
    
    def add_filter(self, field: str, operator: str, value: Any):
        """Add a filter to the query"""
        self.filters.append({
            "field": field,
            "operator": operator,
            "value": value
        })
    
    def add_join(
        self,
        table: str,
        join_type: JoinType,
        left_key: str,
        right_key: str
    ):
        """Add a join to the query"""
        self.joins.append({
            "table": table,
            "type": join_type,
            "left_key": left_key,
            "right_key": right_key
        })
    
    def build_where_clause(self) -> str:
        """Build WHERE clause from filters"""
        if not self.filters:
            return ""
        
        conditions = []
        for f in self.filters:
            field = f["field"]
            op = f["operator"]
            value = f["value"]
            
            if op == "equals":
                conditions.append(f"{field} = '{value}'")
            elif op == "not_equals":
                conditions.append(f"{field} != '{value}'")
            elif op == "greater_than":
                conditions.append(f"{field} > {value}")
            elif op == "less_than":
                conditions.append(f"{field} < {value}")
            elif op == "between":
                conditions.append(f"{field} BETWEEN {value[0]} AND {value[1]}")
            elif op == "in":
                values = "', '".join(str(v) for v in value)
                conditions.append(f"{field} IN ('{values}')")
            elif op == "contains":
                conditions.append(f"{field} LIKE '%{value}%'")
            elif op == "is_null":
                conditions.append(f"{field} IS NULL")
            elif op == "not_null":
                conditions.append(f"{field} IS NOT NULL")
        
        return "WHERE " + " AND ".join(conditions)
    
    def build_join_clause(self) -> str:
        """Build JOIN clause from joins configuration"""
        if not self.joins:
            return ""
        
        join_statements = []
        for j in self.joins:
            join_type = j["type"].value.upper()
            table = j["table"]
            left_key = j["left_key"]
            right_key = j["right_key"]
            
            join_statements.append(
                f"{join_type} JOIN {table} ON {left_key} = {table}.{right_key}"
            )
        
        return " ".join(join_statements)
    
    def execute_query(self, session: Session) -> Tuple[List[Dict], int]:
        """Execute the query and return results with execution time"""
        # Check cache first
        cached_data = self.check_cache(session)
        if cached_data:
            return cached_data.get("data", []), 0
        
        # Build and execute query
        query = self.build_query()
        start_time = datetime.utcnow()
        
        # Execute query
        result = session.exec(text(query))
        rows = [dict(row) for row in result]
        
        # Calculate execution time
        execution_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        # Transform results
        transformed_data = self.transform_results(rows)
        
        # Save to cache
        self.save_to_cache(session, transformed_data, execution_time_ms)
        
        return transformed_data, execution_time_ms
    
    def get_aggregation_function(self, agg_type: AggregationType, field: str) -> str:
        """Get SQL aggregation function"""
        if agg_type == AggregationType.COUNT:
            return f"COUNT({field})"
        elif agg_type == AggregationType.COUNT_DISTINCT:
            return f"COUNT(DISTINCT {field})"
        elif agg_type == AggregationType.SUM:
            return f"SUM({field})"
        elif agg_type == AggregationType.AVG:
            return f"AVG({field})"
        elif agg_type == AggregationType.MIN:
            return f"MIN({field})"
        elif agg_type == AggregationType.MAX:
            return f"MAX({field})"
        elif agg_type == AggregationType.MEDIAN:
            return f"PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY {field})"
        elif agg_type == AggregationType.STDDEV:
            return f"STDDEV({field})"
        elif agg_type == AggregationType.VARIANCE:
            return f"VARIANCE({field})"
        else:
            return f"COUNT({field})"
    
    def format_date_truncation(self, date_field: str, granularity: str) -> str:
        """Format date truncation based on granularity"""
        if granularity == "day":
            return f"DATE_TRUNC('day', {date_field})"
        elif granularity == "week":
            return f"DATE_TRUNC('week', {date_field})"
        elif granularity == "month":
            return f"DATE_TRUNC('month', {date_field})"
        elif granularity == "quarter":
            return f"DATE_TRUNC('quarter', {date_field})"
        elif granularity == "year":
            return f"DATE_TRUNC('year', {date_field})"
        else:
            return date_field