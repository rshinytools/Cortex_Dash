# ABOUTME: PostgreSQL database adapter for connecting to PostgreSQL databases
# ABOUTME: Supports async operations with connection pooling and efficient queries

from typing import Any, Dict, List, Optional, Union
import pandas as pd
import asyncpg
import logging
from urllib.parse import urlparse
import json

from .base import DataSourceAdapter

logger = logging.getLogger(__name__)


class PostgreSQLAdapter(DataSourceAdapter):
    """Adapter for connecting to PostgreSQL databases."""
    
    def __init__(self, connection_params: Dict[str, Any]):
        """
        Initialize PostgreSQL adapter.
        
        Connection params should include either:
        - connection_string: Full PostgreSQL connection string
        OR
        - host, port, database, user, password as separate fields
        
        Optional params:
        - schema: Database schema to use (default: public)
        - ssl: Enable SSL connection (default: False)
        - pool_size: Connection pool size (default: 10)
        """
        super().__init__(connection_params)
        
        # Parse connection parameters
        if 'connection_string' in connection_params:
            self._parse_connection_string(connection_params['connection_string'])
        else:
            self.host = connection_params.get('host', 'localhost')
            self.port = connection_params.get('port', 5432)
            self.database = connection_params.get('database')
            self.user = connection_params.get('user')
            self.password = connection_params.get('password')
        
        self.schema = connection_params.get('schema', 'public')
        self.ssl = connection_params.get('ssl', False)
        self.pool_size = connection_params.get('pool_size', 10)
        
        self._pool: Optional[asyncpg.Pool] = None
    
    def _parse_connection_string(self, connection_string: str) -> None:
        """Parse PostgreSQL connection string."""
        parsed = urlparse(connection_string)
        self.host = parsed.hostname or 'localhost'
        self.port = parsed.port or 5432
        self.database = parsed.path.lstrip('/')
        self.user = parsed.username
        self.password = parsed.password
    
    async def connect(self) -> None:
        """Create connection pool to PostgreSQL."""
        try:
            self._pool = await asyncpg.create_pool(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password,
                min_size=1,
                max_size=self.pool_size,
                command_timeout=60
            )
            logger.info(f"Connected to PostgreSQL database: {self.database}")
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {str(e)}")
            raise
    
    async def disconnect(self) -> None:
        """Close connection pool."""
        if self._pool:
            await self._pool.close()
            self._pool = None
            logger.info("Disconnected from PostgreSQL")
    
    async def query(
        self,
        query: Union[str, Dict[str, Any]],
        field_mappings: Optional[Dict[str, str]] = None,
        limit: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Execute a query against PostgreSQL.
        
        Query can be:
        - A SQL string
        - A dict with 'table' and optional 'columns', 'where', 'order_by'
        """
        if not self._pool:
            await self.connect()
        
        # Build SQL query
        if isinstance(query, str):
            sql = query
        else:
            sql = self._build_sql_query(query)
        
        # Add limit if specified and not already in query
        if limit and 'limit' not in sql.lower():
            limit = self._validate_limit(limit)
            sql += f" LIMIT {limit}"
        
        try:
            async with self._pool.acquire() as conn:
                # Execute query and fetch results
                rows = await conn.fetch(sql)
                
                # Convert to pandas DataFrame
                if rows:
                    data = [dict(row) for row in rows]
                    df = pd.DataFrame(data)
                else:
                    df = pd.DataFrame()
                
                # Apply field mappings
                if field_mappings and not df.empty:
                    df = self.apply_field_mappings(df, field_mappings)
                
                return df
                
        except Exception as e:
            logger.error(f"Error executing PostgreSQL query: {str(e)}")
            raise
    
    async def get_schema(self) -> Dict[str, Any]:
        """Get database schema information."""
        if self._schema_cache:
            return self._schema_cache
        
        if not self._pool:
            await self.connect()
        
        schema = {"tables": {}}
        
        try:
            async with self._pool.acquire() as conn:
                # Get all tables in the schema
                tables_query = """
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = $1
                    AND table_type = 'BASE TABLE'
                    ORDER BY table_name
                """
                tables = await conn.fetch(tables_query, self.schema)
                
                for table_row in tables:
                    table_name = table_row['table_name']
                    
                    # Get column information
                    columns_query = """
                        SELECT 
                            column_name,
                            data_type,
                            is_nullable,
                            column_default,
                            character_maximum_length,
                            numeric_precision,
                            numeric_scale
                        FROM information_schema.columns
                        WHERE table_schema = $1
                        AND table_name = $2
                        ORDER BY ordinal_position
                    """
                    columns = await conn.fetch(columns_query, self.schema, table_name)
                    
                    # Get row count
                    count_query = f'SELECT COUNT(*) as count FROM "{self.schema}"."{table_name}"'
                    count_result = await conn.fetchrow(count_query)
                    row_count = count_result['count']
                    
                    # Get indexes
                    indexes_query = """
                        SELECT indexname, indexdef
                        FROM pg_indexes
                        WHERE schemaname = $1
                        AND tablename = $2
                    """
                    indexes = await conn.fetch(indexes_query, self.schema, table_name)
                    
                    # Build column info
                    column_info = []
                    for col in columns:
                        column_info.append({
                            "name": col['column_name'],
                            "type": self._map_postgres_type_to_generic(col['data_type']),
                            "postgres_type": col['data_type'],
                            "nullable": col['is_nullable'] == 'YES',
                            "default": col['column_default'],
                            "max_length": col['character_maximum_length'],
                            "numeric_precision": col['numeric_precision'],
                            "numeric_scale": col['numeric_scale']
                        })
                    
                    schema["tables"][table_name] = {
                        "columns": column_info,
                        "row_count": row_count,
                        "indexes": [
                            {
                                "name": idx['indexname'],
                                "definition": idx['indexdef']
                            }
                            for idx in indexes
                        ]
                    }
                
                # Get database size
                size_query = "SELECT pg_database_size($1) as size"
                size_result = await conn.fetchrow(size_query, self.database)
                schema["database_size"] = size_result['size']
                
                # Get PostgreSQL version
                version_query = "SELECT version()"
                version_result = await conn.fetchrow(version_query)
                schema["postgres_version"] = version_result['version']
                
        except Exception as e:
            logger.error(f"Error getting PostgreSQL schema: {str(e)}")
            raise
        
        self._schema_cache = schema
        return schema
    
    async def preview_data(
        self,
        table_or_file: str,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Get a preview of data from a PostgreSQL table."""
        if not self._pool:
            await self.connect()
        
        try:
            async with self._pool.acquire() as conn:
                # Build preview query
                preview_query = f"""
                    SELECT *
                    FROM "{self.schema}"."{table_or_file}"
                    LIMIT $1 OFFSET $2
                """
                
                # Get preview data
                rows = await conn.fetch(preview_query, limit, offset)
                data = [dict(row) for row in rows]
                
                # Get total row count
                count_query = f'SELECT COUNT(*) as count FROM "{self.schema}"."{table_or_file}"'
                count_result = await conn.fetchrow(count_query)
                total_rows = count_result['count']
                
                # Get column information
                columns_query = """
                    SELECT 
                        column_name,
                        data_type,
                        is_nullable
                    FROM information_schema.columns
                    WHERE table_schema = $1
                    AND table_name = $2
                    ORDER BY ordinal_position
                """
                columns = await conn.fetch(columns_query, self.schema, table_or_file)
                
                column_info = []
                for col in columns:
                    column_info.append({
                        "name": col['column_name'],
                        "type": self._map_postgres_type_to_generic(col['data_type']),
                        "postgres_type": col['data_type'],
                        "nullable": col['is_nullable'] == 'YES'
                    })
                
                return {
                    "data": data,
                    "columns": column_info,
                    "total_rows": total_rows,
                    "offset": offset,
                    "limit": limit
                }
                
        except Exception as e:
            logger.error(f"Error previewing PostgreSQL table {table_or_file}: {str(e)}")
            raise
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test PostgreSQL connection."""
        try:
            # Try to create a connection
            conn = await asyncpg.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password
            )
            
            # Test with a simple query
            version = await conn.fetchval("SELECT version()")
            await conn.close()
            
            return {
                "success": True,
                "message": "Successfully connected to PostgreSQL",
                "details": {
                    "host": self.host,
                    "port": self.port,
                    "database": self.database,
                    "version": version
                }
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to connect to PostgreSQL: {str(e)}",
                "details": {
                    "error": str(e),
                    "host": self.host,
                    "port": self.port,
                    "database": self.database
                }
            }
    
    def _build_sql_query(self, query_dict: Dict[str, Any]) -> str:
        """Build SQL query from structured query dict."""
        table = query_dict.get('table')
        if not table:
            raise ValueError("Table name is required in query dict")
        
        # Start with SELECT
        columns = query_dict.get('columns', ['*'])
        if isinstance(columns, list):
            columns_str = ', '.join(f'"{col}"' for col in columns)
        else:
            columns_str = columns
        
        sql = f'SELECT {columns_str} FROM "{self.schema}"."{table}"'
        
        # Add WHERE clause
        where = query_dict.get('where')
        if where:
            if isinstance(where, dict):
                # Convert dict to WHERE clause
                conditions = []
                for key, value in where.items():
                    if value is None:
                        conditions.append(f'"{key}" IS NULL')
                    elif isinstance(value, (list, tuple)):
                        # IN clause
                        values_str = ', '.join(f"'{v}'" if isinstance(v, str) else str(v) for v in value)
                        conditions.append(f'"{key}" IN ({values_str})')
                    else:
                        conditions.append(f'"{key}" = \'{value}\'' if isinstance(value, str) else f'"{key}" = {value}')
                sql += ' WHERE ' + ' AND '.join(conditions)
            else:
                # Assume it's a string WHERE clause
                sql += f' WHERE {where}'
        
        # Add ORDER BY
        order_by = query_dict.get('order_by')
        if order_by:
            if isinstance(order_by, list):
                order_str = ', '.join(f'"{col}"' for col in order_by)
            else:
                order_str = f'"{order_by}"'
            sql += f' ORDER BY {order_str}'
        
        return sql
    
    def _map_postgres_type_to_generic(self, pg_type: str) -> str:
        """Map PostgreSQL data type to generic type name."""
        pg_type_lower = pg_type.lower()
        
        # Integer types
        if any(t in pg_type_lower for t in ['int', 'serial']):
            return 'integer'
        
        # Numeric types
        if any(t in pg_type_lower for t in ['numeric', 'decimal', 'real', 'double', 'float', 'money']):
            return 'numeric'
        
        # Boolean
        if 'bool' in pg_type_lower:
            return 'boolean'
        
        # Date/Time types
        if any(t in pg_type_lower for t in ['timestamp', 'date', 'time', 'interval']):
            return 'datetime'
        
        # Text types
        if any(t in pg_type_lower for t in ['text', 'char', 'varchar', 'name']):
            return 'text'
        
        # JSON types
        if 'json' in pg_type_lower:
            return 'json'
        
        # Binary
        if 'bytea' in pg_type_lower:
            return 'binary'
        
        # Array
        if '[]' in pg_type or 'array' in pg_type_lower:
            return 'array'
        
        # UUID
        if 'uuid' in pg_type_lower:
            return 'uuid'
        
        return 'unknown'