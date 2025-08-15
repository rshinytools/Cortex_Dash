# ABOUTME: Query optimization service for improving database query performance
# ABOUTME: Includes query plan analysis, index suggestions, and automatic query rewriting

import re
import hashlib
from typing import Dict, List, Optional, Any, Tuple, Set
from datetime import datetime, timedelta
import logging
from sqlalchemy import text, inspect, MetaData
from sqlalchemy.engine import Engine
from sqlalchemy.sql import Select
from sqlalchemy.orm import Query
import json

from app.core.cache import query_cache
from app.models.data_catalog import DataCatalog
from app.models.widget import Widget

logger = logging.getLogger(__name__)


class QueryOptimizer:
    """Query optimization service"""
    
    def __init__(self, engine: Engine):
        """Initialize query optimizer with database engine"""
        self.engine = engine
        self.metadata = MetaData()
        self.query_stats = {}
        self.index_suggestions = {}
        
    def optimize_query(
        self,
        query: str,
        params: Optional[Dict] = None,
        study_id: Optional[str] = None,
        use_cache: bool = True
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Optimize a SQL query for better performance.
        
        Args:
            query: SQL query string
            params: Query parameters
            study_id: Study ID for caching
            use_cache: Whether to use query cache
            
        Returns:
            Tuple of (optimized_query, execution_stats)
        """
        params = params or {}
        
        # Check cache first
        if use_cache and study_id:
            query_hash = query_cache.get_query_hash(query, params)
            cached_result = query_cache.get_query_result(query_hash, study_id)
            if cached_result is not None:
                logger.info(f"Query result retrieved from cache: {query_hash}")
                return query, {"cached": True, "cache_hit": True}
        
        # Analyze query
        analysis = self._analyze_query(query)
        
        # Apply optimizations
        optimized_query = self._apply_optimizations(query, analysis)
        
        # Get execution plan
        plan = self._get_execution_plan(optimized_query, params)
        
        # Generate index suggestions
        suggestions = self._suggest_indexes(analysis, plan)
        
        # Track query statistics
        self._track_query_stats(query, analysis, plan)
        
        stats = {
            "cached": False,
            "cache_hit": False,
            "original_query": query,
            "optimized": optimized_query != query,
            "analysis": analysis,
            "execution_plan": plan,
            "index_suggestions": suggestions
        }
        
        return optimized_query, stats
    
    def _analyze_query(self, query: str) -> Dict[str, Any]:
        """Analyze query structure and identify optimization opportunities"""
        analysis = {
            "tables": [],
            "joins": [],
            "where_conditions": [],
            "group_by": False,
            "order_by": False,
            "has_subquery": False,
            "has_aggregates": False,
            "estimated_complexity": "low"
        }
        
        # Extract tables
        table_pattern = r'FROM\s+(\w+)|JOIN\s+(\w+)'
        tables = re.findall(table_pattern, query, re.IGNORECASE)
        analysis["tables"] = list(set([t[0] or t[1] for t in tables]))
        
        # Check for joins
        join_pattern = r'(INNER|LEFT|RIGHT|FULL|CROSS)\s+JOIN'
        joins = re.findall(join_pattern, query, re.IGNORECASE)
        analysis["joins"] = joins
        
        # Check for WHERE conditions
        where_pattern = r'WHERE\s+(.*?)(?:GROUP|ORDER|LIMIT|$)'
        where_match = re.search(where_pattern, query, re.IGNORECASE | re.DOTALL)
        if where_match:
            conditions = where_match.group(1).strip()
            # Simple parsing of conditions
            analysis["where_conditions"] = [c.strip() for c in re.split(r'\s+AND\s+|\s+OR\s+', conditions, flags=re.IGNORECASE)]
        
        # Check for GROUP BY
        analysis["group_by"] = bool(re.search(r'GROUP\s+BY', query, re.IGNORECASE))
        
        # Check for ORDER BY
        analysis["order_by"] = bool(re.search(r'ORDER\s+BY', query, re.IGNORECASE))
        
        # Check for subqueries
        analysis["has_subquery"] = query.count('(SELECT') > 0 or query.count('(select') > 0
        
        # Check for aggregates
        aggregate_pattern = r'(COUNT|SUM|AVG|MAX|MIN|GROUP_CONCAT)\s*\('
        analysis["has_aggregates"] = bool(re.search(aggregate_pattern, query, re.IGNORECASE))
        
        # Estimate complexity
        complexity_score = (
            len(analysis["tables"]) * 2 +
            len(analysis["joins"]) * 3 +
            (5 if analysis["has_subquery"] else 0) +
            (2 if analysis["has_aggregates"] else 0) +
            (2 if analysis["group_by"] else 0)
        )
        
        if complexity_score <= 5:
            analysis["estimated_complexity"] = "low"
        elif complexity_score <= 10:
            analysis["estimated_complexity"] = "medium"
        else:
            analysis["estimated_complexity"] = "high"
        
        return analysis
    
    def _apply_optimizations(self, query: str, analysis: Dict[str, Any]) -> str:
        """Apply query optimizations based on analysis"""
        optimized = query
        
        # 1. Add DISTINCT removal if unnecessary
        if 'DISTINCT' in optimized and not analysis["has_aggregates"]:
            # Check if DISTINCT is necessary based on query structure
            # This is a simplified check - real implementation would be more sophisticated
            if len(analysis["joins"]) == 0 and not analysis["has_subquery"]:
                logger.info("Considering DISTINCT removal optimization")
        
        # 2. Optimize JOIN order (place smaller tables first)
        if len(analysis["joins"]) > 1:
            logger.info("Multiple JOINs detected - consider reordering for optimization")
        
        # 3. Push down predicates to subqueries
        if analysis["has_subquery"] and analysis["where_conditions"]:
            logger.info("Subquery with WHERE conditions - consider predicate pushdown")
        
        # 4. Add index hints for large tables
        for table in analysis["tables"]:
            if self._is_large_table(table):
                logger.info(f"Large table {table} detected - consider index hints")
        
        # 5. Limit optimization for pagination
        if 'LIMIT' not in optimized.upper() and 'dashboard' in query.lower():
            # Add default limit for dashboard queries to prevent loading too much data
            optimized += " LIMIT 1000"
            logger.info("Added LIMIT clause for dashboard query optimization")
        
        return optimized
    
    def _get_execution_plan(self, query: str, params: Dict) -> Dict[str, Any]:
        """Get query execution plan from database"""
        plan = {
            "type": "unknown",
            "estimated_rows": 0,
            "estimated_cost": 0,
            "actual_time": None
        }
        
        try:
            # PostgreSQL EXPLAIN ANALYZE
            explain_query = f"EXPLAIN (FORMAT JSON, ANALYZE FALSE) {query}"
            
            with self.engine.connect() as conn:
                result = conn.execute(text(explain_query), params)
                plan_data = result.fetchone()
                
                if plan_data:
                    plan_json = plan_data[0]
                    if isinstance(plan_json, str):
                        plan_json = json.loads(plan_json)
                    
                    if plan_json and len(plan_json) > 0:
                        root_plan = plan_json[0].get("Plan", {})
                        plan["type"] = root_plan.get("Node Type", "unknown")
                        plan["estimated_rows"] = root_plan.get("Plan Rows", 0)
                        plan["estimated_cost"] = root_plan.get("Total Cost", 0)
                        
        except Exception as e:
            logger.warning(f"Could not get execution plan: {e}")
        
        return plan
    
    def _suggest_indexes(self, analysis: Dict[str, Any], plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Suggest indexes based on query analysis and execution plan"""
        suggestions = []
        
        # Suggest indexes for WHERE conditions
        for condition in analysis["where_conditions"]:
            # Extract column names from conditions
            column_pattern = r'(\w+)\s*[=<>!]'
            columns = re.findall(column_pattern, condition)
            
            for column in columns:
                suggestion = {
                    "type": "index",
                    "column": column,
                    "reason": f"Column {column} used in WHERE clause",
                    "impact": "medium"
                }
                
                # Check if this is a high-impact suggestion
                if plan["estimated_cost"] > 1000:
                    suggestion["impact"] = "high"
                
                suggestions.append(suggestion)
        
        # Suggest indexes for JOIN columns
        if analysis["joins"]:
            join_pattern = r'ON\s+(\w+)\.(\w+)\s*=\s*(\w+)\.(\w+)'
            matches = re.findall(join_pattern, ' '.join(analysis["joins"]), re.IGNORECASE)
            
            for match in matches:
                suggestions.append({
                    "type": "index",
                    "column": f"{match[0]}.{match[1]}",
                    "reason": "Column used in JOIN condition",
                    "impact": "high" if len(analysis["joins"]) > 2 else "medium"
                })
        
        # Suggest composite indexes for GROUP BY
        if analysis["group_by"]:
            suggestions.append({
                "type": "composite_index",
                "columns": "GROUP BY columns",
                "reason": "Optimize GROUP BY operation",
                "impact": "medium"
            })
        
        # Suggest covering indexes for complex queries
        if analysis["estimated_complexity"] == "high":
            suggestions.append({
                "type": "covering_index",
                "columns": "SELECT and WHERE columns",
                "reason": "Consider covering index for complex query",
                "impact": "high"
            })
        
        return suggestions
    
    def _is_large_table(self, table_name: str) -> bool:
        """Check if a table is considered large (>100k rows)"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(
                    text(f"SELECT COUNT(*) FROM {table_name} LIMIT 1")
                )
                count = result.scalar()
                return count > 100000
        except:
            return False
    
    def _track_query_stats(self, query: str, analysis: Dict, plan: Dict):
        """Track query statistics for monitoring"""
        query_hash = hashlib.md5(query.encode()).hexdigest()[:8]
        
        if query_hash not in self.query_stats:
            self.query_stats[query_hash] = {
                "query": query[:100],  # Store first 100 chars
                "count": 0,
                "total_cost": 0,
                "avg_cost": 0,
                "complexity": analysis["estimated_complexity"],
                "first_seen": datetime.utcnow(),
                "last_seen": datetime.utcnow()
            }
        
        stats = self.query_stats[query_hash]
        stats["count"] += 1
        stats["total_cost"] += plan["estimated_cost"]
        stats["avg_cost"] = stats["total_cost"] / stats["count"]
        stats["last_seen"] = datetime.utcnow()
    
    def get_slow_queries(self, threshold_cost: float = 1000) -> List[Dict]:
        """Get queries with high average cost"""
        slow_queries = []
        
        for query_hash, stats in self.query_stats.items():
            if stats["avg_cost"] > threshold_cost:
                slow_queries.append({
                    "hash": query_hash,
                    "query": stats["query"],
                    "avg_cost": stats["avg_cost"],
                    "count": stats["count"],
                    "complexity": stats["complexity"],
                    "last_seen": stats["last_seen"]
                })
        
        return sorted(slow_queries, key=lambda x: x["avg_cost"], reverse=True)
    
    def optimize_widget_query(
        self,
        widget: Widget,
        base_query: str,
        filters: Optional[Dict] = None
    ) -> Tuple[str, Dict]:
        """Optimize query specifically for widget execution"""
        
        # Add widget-specific optimizations
        optimizations = []
        
        # 1. Add appropriate LIMIT based on widget type
        if widget.widget_type == "kpi_metric":
            # KPI metrics only need single value
            if "LIMIT" not in base_query.upper():
                base_query += " LIMIT 1"
                optimizations.append("Added LIMIT 1 for KPI metric")
        
        elif widget.widget_type == "data_table":
            # Data tables need pagination
            config = widget.configuration or {}
            page_size = config.get("page_size", 100)
            if "LIMIT" not in base_query.upper():
                base_query += f" LIMIT {page_size}"
                optimizations.append(f"Added LIMIT {page_size} for data table")
        
        # 2. Optimize time series queries
        elif widget.widget_type == "time_series":
            config = widget.configuration or {}
            if "date_field" in config:
                # Add index hint for date field
                optimizations.append("Consider index on date field for time series")
        
        # 3. Apply standard optimizations
        optimized_query, stats = self.optimize_query(
            base_query,
            filters,
            study_id=widget.study_id,
            use_cache=True
        )
        
        stats["widget_optimizations"] = optimizations
        
        return optimized_query, stats


class QueryBatchOptimizer:
    """Optimize batch query execution"""
    
    def __init__(self, optimizer: QueryOptimizer):
        self.optimizer = optimizer
        
    def optimize_batch(
        self,
        queries: List[Tuple[str, Optional[Dict]]],
        parallel: bool = False
    ) -> List[Tuple[str, Dict]]:
        """
        Optimize a batch of queries.
        
        Args:
            queries: List of (query, params) tuples
            parallel: Whether queries can be executed in parallel
            
        Returns:
            List of (optimized_query, stats) tuples
        """
        results = []
        
        # Group similar queries for better caching
        query_groups = self._group_similar_queries(queries)
        
        for group in query_groups:
            if len(group) > 1 and parallel:
                # Combine similar queries if possible
                combined = self._try_combine_queries(group)
                if combined:
                    optimized, stats = self.optimizer.optimize_query(combined[0], combined[1])
                    results.append((optimized, stats))
                    continue
            
            # Process individually
            for query, params in group:
                optimized, stats = self.optimizer.optimize_query(query, params)
                results.append((optimized, stats))
        
        return results
    
    def _group_similar_queries(
        self,
        queries: List[Tuple[str, Optional[Dict]]]
    ) -> List[List[Tuple[str, Optional[Dict]]]]:
        """Group similar queries for optimization"""
        groups = {}
        
        for query, params in queries:
            # Create signature for grouping
            # Remove parameter values to find structurally similar queries
            signature = re.sub(r'=\s*\S+', '= ?', query)
            signature = re.sub(r'IN\s*\([^)]+\)', 'IN (?)', signature)
            
            if signature not in groups:
                groups[signature] = []
            groups[signature].append((query, params))
        
        return list(groups.values())
    
    def _try_combine_queries(
        self,
        queries: List[Tuple[str, Optional[Dict]]]
    ) -> Optional[Tuple[str, Dict]]:
        """Try to combine similar queries into one"""
        if not queries:
            return None
        
        # Simple combination for queries differing only in filter values
        # This is a simplified implementation
        base_query = queries[0][0]
        
        # Check if all queries have same structure
        if all(self._same_structure(base_query, q[0]) for q in queries[1:]):
            # Try to combine with UNION ALL or IN clause
            # Implementation would depend on specific query patterns
            pass
        
        return None
    
    def _same_structure(self, query1: str, query2: str) -> bool:
        """Check if two queries have the same structure"""
        # Remove values and compare
        pattern1 = re.sub(r'=\s*\S+', '= ?', query1)
        pattern2 = re.sub(r'=\s*\S+', '= ?', query2)
        return pattern1 == pattern2


class IndexAdvisor:
    """Suggest and manage database indexes"""
    
    def __init__(self, engine: Engine):
        self.engine = engine
        self.existing_indexes = self._load_existing_indexes()
        
    def _load_existing_indexes(self) -> Dict[str, List[str]]:
        """Load existing indexes from database"""
        indexes = {}
        
        try:
            inspector = inspect(self.engine)
            for table_name in inspector.get_table_names():
                table_indexes = []
                for index in inspector.get_indexes(table_name):
                    table_indexes.append({
                        "name": index["name"],
                        "columns": index["column_names"],
                        "unique": index["unique"]
                    })
                indexes[table_name] = table_indexes
        except Exception as e:
            logger.error(f"Error loading indexes: {e}")
        
        return indexes
    
    def suggest_missing_indexes(
        self,
        query_stats: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Suggest missing indexes based on query statistics"""
        suggestions = []
        
        # Analyze frequently used columns in WHERE clauses
        where_columns = self._extract_where_columns(query_stats)
        
        for table, columns in where_columns.items():
            existing = self.existing_indexes.get(table, [])
            existing_cols = set()
            for idx in existing:
                existing_cols.update(idx.get("columns", []))
            
            for column, frequency in columns.items():
                if column not in existing_cols and frequency > 10:
                    suggestions.append({
                        "table": table,
                        "column": column,
                        "type": "btree",
                        "reason": f"Column used in WHERE clause {frequency} times",
                        "estimated_impact": self._estimate_impact(frequency),
                        "create_statement": f"CREATE INDEX idx_{table}_{column} ON {table}({column});"
                    })
        
        return suggestions
    
    def _extract_where_columns(self, query_stats: Dict) -> Dict[str, Dict[str, int]]:
        """Extract columns used in WHERE clauses from query statistics"""
        where_columns = {}
        
        # This would parse query stats to find frequently filtered columns
        # Simplified implementation
        return where_columns
    
    def _estimate_impact(self, frequency: int) -> str:
        """Estimate the impact of creating an index"""
        if frequency > 100:
            return "high"
        elif frequency > 50:
            return "medium"
        else:
            return "low"