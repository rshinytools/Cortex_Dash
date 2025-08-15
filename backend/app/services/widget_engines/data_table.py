# ABOUTME: Data Table widget engine implementation
# ABOUTME: Handles detailed record display with pagination, sorting, and column configuration

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from app.services.widget_engines.base_widget import WidgetEngine
from app.models.phase1_models import AggregationType, DataGranularity, JoinType


class DataTableEngine(WidgetEngine):
    """Engine for Data Table widgets"""
    
    def get_data_contract(self) -> Dict[str, Any]:
        """Return Data Table data contract"""
        return {
            "granularity": DataGranularity.RECORD_LEVEL,
            "required_fields": [
                {"name": "display_columns", "type": "array", "description": "Columns to display"}
            ],
            "optional_fields": [
                {"name": "id_column", "type": "string", "description": "Unique identifier column"},
                {"name": "link_column", "type": "string", "description": "Column for row links"},
                {"name": "group_column", "type": "categorical", "description": "Column for grouping"},
                {"name": "highlight_columns", "type": "array", "description": "Columns to highlight"},
                {"name": "computed_columns", "type": "array", "description": "Calculated columns"}
            ],
            "supported_aggregations": [
                AggregationType.COUNT,
                AggregationType.COUNT_DISTINCT
            ],
            "supports_grouping": True,
            "supports_filtering": True,
            "supports_sorting": True,
            "supports_pagination": True,
            "supports_joins": True,
            "max_join_datasets": 3,
            "recommended_cache_ttl": 1800
        }
    
    def validate_mapping(self) -> Tuple[bool, List[str]]:
        """Validate Data Table mapping"""
        errors = []
        
        mappings = self.mapping_config.get("field_mappings", {})
        
        # Check required fields
        if "display_columns" not in mappings:
            errors.append("display_columns is required")
        else:
            display_columns = mappings.get("display_columns", {})
            if not display_columns or not isinstance(display_columns, dict):
                errors.append("display_columns must be a non-empty mapping")
        
        # Validate pagination settings
        pagination = self.mapping_config.get("pagination", {})
        if pagination.get("enabled", True):
            page_size = pagination.get("page_size", 10)
            if not isinstance(page_size, int) or page_size < 1:
                errors.append("page_size must be a positive integer")
        
        return len(errors) == 0, errors
    
    def build_query(self) -> str:
        """Build SQL query for data table"""
        mappings = self.mapping_config.get("field_mappings", {})
        dataset = self.mapping_config.get("primary_dataset", "dataset")
        
        # Get column mappings
        display_columns = mappings.get("display_columns", {})
        id_column = mappings.get("id_column", {}).get("source_field")
        group_column = mappings.get("group_column", {}).get("source_field")
        
        # Build SELECT clause
        select_parts = []
        
        # Add ID column first if specified
        if id_column:
            select_parts.append(f"{id_column} as row_id")
        
        # Add display columns
        for alias, config in display_columns.items():
            source_field = config.get("source_field")
            if source_field:
                # Check if column has formatting
                format_type = config.get("format")
                if format_type == "date":
                    select_parts.append(f"TO_CHAR({source_field}, 'YYYY-MM-DD') as {alias}")
                elif format_type == "datetime":
                    select_parts.append(f"TO_CHAR({source_field}, 'YYYY-MM-DD HH24:MI:SS') as {alias}")
                elif format_type == "number":
                    decimals = config.get("decimals", 2)
                    select_parts.append(f"ROUND({source_field}::numeric, {decimals}) as {alias}")
                else:
                    select_parts.append(f"{source_field} as {alias}")
        
        # Add computed columns
        computed_columns = mappings.get("computed_columns", {})
        for alias, config in computed_columns.items():
            expression = config.get("expression")
            if expression:
                select_parts.append(f"{expression} as {alias}")
        
        # Build FROM clause
        from_clause = f"FROM {dataset}"
        
        # Build JOIN clause
        join_clause = self.build_join_clause()
        
        # Build WHERE clause
        where_clause = self.build_where_clause()
        
        # Add search filter if present
        search_config = self.mapping_config.get("search", {})
        if search_config.get("enabled") and search_config.get("value"):
            search_value = search_config.get("value")
            search_columns = search_config.get("columns", list(display_columns.keys()))
            
            search_conditions = []
            for col in search_columns:
                if col in display_columns:
                    source = display_columns[col].get("source_field")
                    if source:
                        search_conditions.append(f"CAST({source} AS TEXT) ILIKE '%{search_value}%'")
            
            if search_conditions:
                search_clause = "(" + " OR ".join(search_conditions) + ")"
                if where_clause:
                    where_clause += f" AND {search_clause}"
                else:
                    where_clause = f"WHERE {search_clause}"
        
        # Build ORDER BY clause
        order_by_parts = []
        
        # Handle sorting
        sort_config = self.mapping_config.get("sort", {})
        if sort_config:
            sort_column = sort_config.get("column")
            sort_direction = sort_config.get("direction", "ASC").upper()
            
            if sort_column and sort_column in display_columns:
                source = display_columns[sort_column].get("source_field")
                if source:
                    order_by_parts.append(f"{source} {sort_direction}")
        
        # Default sort by ID if available
        if not order_by_parts and id_column:
            order_by_parts.append(f"{id_column} ASC")
        
        order_by_clause = ""
        if order_by_parts:
            order_by_clause = f"ORDER BY {', '.join(order_by_parts)}"
        
        # Build LIMIT/OFFSET for pagination
        pagination = self.mapping_config.get("pagination", {})
        limit_clause = ""
        
        if pagination.get("enabled", True):
            page_size = pagination.get("page_size", 10)
            current_page = pagination.get("current_page", 1)
            offset = (current_page - 1) * page_size
            
            limit_clause = f"LIMIT {page_size} OFFSET {offset}"
        
        # Combine query parts
        query = f"""
            SELECT {', '.join(select_parts)}
            {from_clause}
            {join_clause}
            {where_clause}
            {order_by_clause}
            {limit_clause}
        """
        
        return query.strip()
    
    def build_count_query(self) -> str:
        """Build query to count total rows"""
        dataset = self.mapping_config.get("primary_dataset", "dataset")
        
        # Build base query without pagination
        query = f"""
            SELECT COUNT(*) as total_count
            FROM {dataset}
            {self.build_join_clause()}
            {self.build_where_clause()}
        """
        
        return query.strip()
    
    def format_cell_value(self, value: Any, format_config: Dict) -> Any:
        """Format cell value based on configuration"""
        if value is None:
            return format_config.get("null_display", "-")
        
        format_type = format_config.get("format", "text")
        
        if format_type == "boolean":
            true_display = format_config.get("true_display", "Yes")
            false_display = format_config.get("false_display", "No")
            return true_display if value else false_display
        
        elif format_type == "percentage":
            decimals = format_config.get("decimals", 1)
            return f"{round(float(value) * 100, decimals)}%"
        
        elif format_type == "currency":
            currency = format_config.get("currency", "$")
            decimals = format_config.get("decimals", 2)
            return f"{currency}{float(value):,.{decimals}f}"
        
        elif format_type == "status":
            # Map values to status badges
            status_map = format_config.get("status_map", {})
            return status_map.get(str(value), str(value))
        
        return value
    
    def apply_row_formatting(self, row: Dict, row_config: Dict) -> Dict:
        """Apply row-level formatting and highlighting"""
        formatted_row = {}
        
        # Get display columns configuration
        display_columns = self.mapping_config.get("field_mappings", {}).get("display_columns", {})
        
        for key, value in row.items():
            # Get column-specific formatting
            if key in display_columns:
                col_config = display_columns[key]
                formatted_value = self.format_cell_value(value, col_config)
            else:
                formatted_value = value
            
            formatted_row[key] = formatted_value
        
        # Add row metadata
        row_metadata = {}
        
        # Check for row highlighting conditions
        highlight_rules = row_config.get("highlight_rules", [])
        for rule in highlight_rules:
            column = rule.get("column")
            condition = rule.get("condition")
            value_check = rule.get("value")
            highlight_class = rule.get("class", "highlight")
            
            if column in row:
                row_value = row[column]
                
                if condition == "equals" and row_value == value_check:
                    row_metadata["highlight"] = highlight_class
                elif condition == "greater_than" and row_value > value_check:
                    row_metadata["highlight"] = highlight_class
                elif condition == "less_than" and row_value < value_check:
                    row_metadata["highlight"] = highlight_class
                elif condition == "contains" and str(value_check) in str(row_value):
                    row_metadata["highlight"] = highlight_class
        
        # Add row actions if configured
        actions_config = row_config.get("actions", [])
        if actions_config:
            row_actions = []
            for action in actions_config:
                action_type = action.get("type")
                if action_type == "link":
                    link_template = action.get("url_template", "")
                    link_column = action.get("id_column", "row_id")
                    if link_column in row:
                        url = link_template.replace("{id}", str(row[link_column]))
                        row_actions.append({
                            "type": "link",
                            "label": action.get("label", "View"),
                            "url": url
                        })
                elif action_type == "custom":
                    row_actions.append({
                        "type": "custom",
                        "label": action.get("label", "Action"),
                        "action": action.get("action"),
                        "params": {k: row.get(k) for k in action.get("param_columns", [])}
                    })
            
            if row_actions:
                row_metadata["actions"] = row_actions
        
        if row_metadata:
            formatted_row["_metadata"] = row_metadata
        
        return formatted_row
    
    def transform_results(self, raw_data: List[Dict]) -> Dict[str, Any]:
        """Transform raw results into data table format"""
        
        # Get configuration
        display_columns = self.mapping_config.get("field_mappings", {}).get("display_columns", {})
        pagination = self.mapping_config.get("pagination", {})
        row_config = self.mapping_config.get("row_config", {})
        
        # Format rows
        formatted_rows = []
        for row in raw_data:
            formatted_row = self.apply_row_formatting(row, row_config)
            formatted_rows.append(formatted_row)
        
        # Build column definitions
        columns = []
        for alias, config in display_columns.items():
            column_def = {
                "key": alias,
                "label": config.get("label", alias),
                "sortable": config.get("sortable", True),
                "searchable": config.get("searchable", True),
                "width": config.get("width"),
                "align": config.get("align", "left"),
                "format": config.get("format", "text"),
                "wrap": config.get("wrap", False)
            }
            
            # Add column-specific features
            if config.get("editable"):
                column_def["editable"] = True
                column_def["edit_type"] = config.get("edit_type", "text")
            
            if config.get("filterable"):
                column_def["filterable"] = True
                column_def["filter_type"] = config.get("filter_type", "text")
            
            columns.append(column_def)
        
        # Calculate summary statistics if configured
        summary = {}
        if self.mapping_config.get("show_summary", False):
            summary = {
                "total_rows": len(raw_data),
                "columns_count": len(columns)
            }
            
            # Add column-specific summaries
            for alias, config in display_columns.items():
                if config.get("show_summary"):
                    col_values = [row.get(alias) for row in raw_data if row.get(alias) is not None]
                    if col_values and all(isinstance(v, (int, float)) for v in col_values):
                        summary[f"{alias}_sum"] = sum(col_values)
                        summary[f"{alias}_avg"] = sum(col_values) / len(col_values)
                        summary[f"{alias}_min"] = min(col_values)
                        summary[f"{alias}_max"] = max(col_values)
        
        # Build response
        response = {
            "widget_type": "data_table",
            "columns": columns,
            "rows": formatted_rows,
            "pagination": {
                "enabled": pagination.get("enabled", True),
                "current_page": pagination.get("current_page", 1),
                "page_size": pagination.get("page_size", 10),
                "total_rows": pagination.get("total_rows", len(raw_data)),
                "total_pages": 0  # Will be calculated based on total_rows
            },
            "metadata": {
                "last_updated": datetime.utcnow().isoformat(),
                "row_count": len(formatted_rows),
                "has_more": False  # Will be set based on pagination
            }
        }
        
        # Calculate pagination metadata
        if pagination.get("enabled", True):
            total_rows = pagination.get("total_rows", len(raw_data))
            page_size = pagination.get("page_size", 10)
            total_pages = (total_rows + page_size - 1) // page_size
            
            response["pagination"]["total_pages"] = total_pages
            response["pagination"]["has_previous"] = pagination.get("current_page", 1) > 1
            response["pagination"]["has_next"] = pagination.get("current_page", 1) < total_pages
            response["metadata"]["has_more"] = response["pagination"]["has_next"]
        
        # Add summary if calculated
        if summary:
            response["summary"] = summary
        
        # Add export configuration if enabled
        if self.mapping_config.get("export", {}).get("enabled", False):
            response["export"] = {
                "formats": self.mapping_config.get("export", {}).get("formats", ["csv", "excel"]),
                "include_headers": True,
                "filename_template": f"data_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            }
        
        return response