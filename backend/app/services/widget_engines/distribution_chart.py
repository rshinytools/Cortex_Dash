# ABOUTME: Distribution Chart widget engine implementation  
# ABOUTME: Handles categorical distributions with multiple chart types (bar, pie, histogram, etc.)

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import math
from app.services.widget_engines.base_widget import WidgetEngine
from app.models.phase1_models import AggregationType, DataGranularity


class DistributionChartEngine(WidgetEngine):
    """Engine for Distribution Chart widgets supporting multiple chart types"""
    
    CHART_SUBTYPES = [
        "bar", "horizontal_bar", "pie", "donut", 
        "stacked_bar", "grouped_bar", "histogram",
        "box_plot", "treemap", "sunburst", "pareto"
    ]
    
    def get_data_contract(self) -> Dict[str, Any]:
        """Return Distribution Chart data contract"""
        return {
            "granularity": DataGranularity.RECORD_LEVEL,
            "required_fields": [
                {"name": "category_field", "type": "categorical", "description": "Category field"},
                {"name": "value_field", "type": "numeric", "description": "Value to aggregate"}
            ],
            "optional_fields": [
                {"name": "subcategory_field", "type": "categorical", "description": "Nested breakdown"},
                {"name": "series_field", "type": "categorical", "description": "Series for stacked/grouped"},
                {"name": "tooltip_fields", "type": "array", "description": "Additional tooltip data"}
            ],
            "supported_aggregations": [
                AggregationType.COUNT,
                AggregationType.COUNT_DISTINCT,
                AggregationType.SUM,
                AggregationType.AVG,
                AggregationType.MIN,
                AggregationType.MAX,
                AggregationType.MEDIAN,
                AggregationType.PERCENTILE
            ],
            "supports_grouping": True,
            "supports_filtering": True,
            "supports_joins": True,
            "max_join_datasets": 1,
            "recommended_cache_ttl": 3600
        }
    
    def validate_mapping(self) -> Tuple[bool, List[str]]:
        """Validate Distribution Chart mapping"""
        errors = []
        
        mappings = self.mapping_config.get("field_mappings", {})
        chart_subtype = self.mapping_config.get("chart_subtype", "bar")
        
        # Histogram has different requirements
        if chart_subtype == "histogram":
            if "value_field" not in mappings:
                errors.append("value_field is required for histogram")
        else:
            # Other charts need category field
            if "category_field" not in mappings:
                errors.append("category_field is required")
            if "value_field" not in mappings:
                errors.append("value_field is required")
        
        # Check chart subtype
        if chart_subtype not in self.CHART_SUBTYPES:
            errors.append(f"Invalid chart_subtype: {chart_subtype}")
        
        # Validate aggregation type
        agg_type = self.mapping_config.get("aggregation_type")
        if not agg_type:
            errors.append("aggregation_type is required")
        
        return len(errors) == 0, errors
    
    def build_query(self) -> str:
        """Build SQL query based on chart subtype"""
        chart_subtype = self.mapping_config.get("chart_subtype", "bar")
        
        if chart_subtype == "histogram":
            return self.build_histogram_query()
        elif chart_subtype == "box_plot":
            return self.build_boxplot_query()
        elif chart_subtype in ["stacked_bar", "grouped_bar"]:
            return self.build_multi_series_query()
        else:
            return self.build_standard_query()
    
    def build_standard_query(self) -> str:
        """Build query for standard bar/pie charts"""
        mappings = self.mapping_config.get("field_mappings", {})
        dataset = self.mapping_config.get("primary_dataset", "dataset")
        
        category_field = mappings.get("category_field", {}).get("source_field")
        value_field = mappings.get("value_field", {}).get("source_field")
        
        agg_type = self.mapping_config.get("aggregation_type", "COUNT")
        agg_enum = AggregationType[agg_type.upper()]
        
        # Build SELECT
        select_parts = [
            f"{category_field} as category",
            f"{self.get_aggregation_function(agg_enum, value_field)} as value"
        ]
        
        # Add count for percentage calculation
        if self.mapping_config.get("show_percentage", False):
            select_parts.append(f"COUNT(*) as count")
        
        # Build query
        query = f"""
            SELECT {', '.join(select_parts)}
            FROM {dataset}
            {self.build_join_clause()}
            {self.build_where_clause()}
            GROUP BY {category_field}
            ORDER BY value DESC
        """
        
        # Apply limit for top N
        top_n = self.mapping_config.get("top_n")
        if top_n:
            query += f" LIMIT {top_n}"
        
        return query.strip()
    
    def build_multi_series_query(self) -> str:
        """Build query for stacked/grouped bar charts"""
        mappings = self.mapping_config.get("field_mappings", {})
        dataset = self.mapping_config.get("primary_dataset", "dataset")
        
        category_field = mappings.get("category_field", {}).get("source_field")
        value_field = mappings.get("value_field", {}).get("source_field")
        series_field = mappings.get("series_field", {}).get("source_field")
        
        agg_type = self.mapping_config.get("aggregation_type", "COUNT")
        agg_enum = AggregationType[agg_type.upper()]
        
        if not series_field:
            # Fall back to standard query if no series field
            return self.build_standard_query()
        
        # Build SELECT
        select_parts = [
            f"{category_field} as category",
            f"{series_field} as series",
            f"{self.get_aggregation_function(agg_enum, value_field)} as value"
        ]
        
        query = f"""
            SELECT {', '.join(select_parts)}
            FROM {dataset}
            {self.build_join_clause()}
            {self.build_where_clause()}
            GROUP BY {category_field}, {series_field}
            ORDER BY {category_field}, {series_field}
        """
        
        return query.strip()
    
    def build_histogram_query(self) -> str:
        """Build query for histogram with dynamic binning"""
        mappings = self.mapping_config.get("field_mappings", {})
        dataset = self.mapping_config.get("primary_dataset", "dataset")
        
        value_field = mappings.get("value_field", {}).get("source_field")
        bin_count = self.mapping_config.get("bin_count", 10)
        
        # First, get min/max for binning
        range_query = f"""
            WITH value_range AS (
                SELECT 
                    MIN({value_field}) as min_val,
                    MAX({value_field}) as max_val
                FROM {dataset}
                {self.build_where_clause()}
            ),
            bins AS (
                SELECT 
                    generate_series(0, {bin_count - 1}) as bin_num,
                    min_val,
                    max_val,
                    (max_val - min_val) / {bin_count} as bin_width
                FROM value_range
            ),
            binned_data AS (
                SELECT 
                    FLOOR(({value_field} - b.min_val) / NULLIF(b.bin_width, 0)) as bin_num,
                    b.min_val + (FLOOR(({value_field} - b.min_val) / NULLIF(b.bin_width, 0)) * b.bin_width) as bin_start,
                    b.min_val + ((FLOOR(({value_field} - b.min_val) / NULLIF(b.bin_width, 0)) + 1) * b.bin_width) as bin_end,
                    {value_field} as value
                FROM {dataset} d
                CROSS JOIN value_range b
                {self.build_where_clause()}
            )
            SELECT 
                CONCAT(ROUND(bin_start::numeric, 2), ' - ', ROUND(bin_end::numeric, 2)) as category,
                bin_start,
                COUNT(*) as value
            FROM binned_data
            GROUP BY bin_start, bin_end
            ORDER BY bin_start
        """
        
        return range_query.strip()
    
    def build_boxplot_query(self) -> str:
        """Build query for box plot with statistical calculations"""
        mappings = self.mapping_config.get("field_mappings", {})
        dataset = self.mapping_config.get("primary_dataset", "dataset")
        
        category_field = mappings.get("category_field", {}).get("source_field")
        value_field = mappings.get("value_field", {}).get("source_field")
        
        query = f"""
            SELECT 
                {category_field} as category,
                MIN({value_field}) as min_value,
                PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY {value_field}) as q1,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY {value_field}) as median,
                PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY {value_field}) as q3,
                MAX({value_field}) as max_value,
                AVG({value_field}) as mean_value,
                COUNT({value_field}) as count
            FROM {dataset}
            {self.build_join_clause()}
            {self.build_where_clause()}
            GROUP BY {category_field}
            ORDER BY {category_field}
        """
        
        return query.strip()
    
    def calculate_pareto(self, data: List[Dict]) -> List[Dict]:
        """Calculate Pareto analysis (80/20 rule)"""
        # Sort by value descending
        sorted_data = sorted(data, key=lambda x: x.get("value", 0), reverse=True)
        
        # Calculate cumulative percentage
        total = sum(d.get("value", 0) for d in sorted_data)
        cumulative = 0
        
        for item in sorted_data:
            cumulative += item.get("value", 0)
            item["cumulative_value"] = cumulative
            item["cumulative_percentage"] = (cumulative / total * 100) if total > 0 else 0
            item["percentage"] = (item.get("value", 0) / total * 100) if total > 0 else 0
        
        return sorted_data
    
    def format_for_chart_type(self, data: List[Dict], chart_subtype: str) -> Dict[str, Any]:
        """Format data based on chart subtype"""
        
        if chart_subtype in ["pie", "donut"]:
            # Pie/Donut chart format
            return {
                "labels": [d.get("category", "") for d in data],
                "datasets": [{
                    "data": [d.get("value", 0) for d in data],
                    "percentages": [d.get("percentage", 0) for d in data] if "percentage" in data[0] else None
                }]
            }
        
        elif chart_subtype == "horizontal_bar":
            # Horizontal bar chart (swap axes)
            return {
                "labels": [d.get("category", "") for d in data],
                "datasets": [{
                    "label": self.mapping_config.get("display_config", {}).get("title", "Value"),
                    "data": [d.get("value", 0) for d in data],
                    "orientation": "horizontal"
                }]
            }
        
        elif chart_subtype in ["stacked_bar", "grouped_bar"]:
            # Multi-series bar chart
            # Group by category and series
            categories = sorted(list(set(d.get("category") for d in data)))
            series_names = sorted(list(set(d.get("series") for d in data if "series" in d)))
            
            if not series_names:
                # No series field, fall back to standard
                return self.format_for_chart_type(data, "bar")
            
            datasets = []
            for series in series_names:
                series_data = []
                for category in categories:
                    # Find value for this category/series combination
                    value = next(
                        (d.get("value", 0) for d in data 
                         if d.get("category") == category and d.get("series") == series),
                        0
                    )
                    series_data.append(value)
                
                datasets.append({
                    "label": series,
                    "data": series_data,
                    "stack": "stack1" if chart_subtype == "stacked_bar" else None
                })
            
            return {
                "labels": categories,
                "datasets": datasets
            }
        
        elif chart_subtype == "box_plot":
            # Box plot format
            return {
                "labels": [d.get("category", "") for d in data],
                "datasets": [{
                    "label": "Distribution",
                    "data": [
                        {
                            "min": d.get("min_value", 0),
                            "q1": d.get("q1", 0),
                            "median": d.get("median", 0),
                            "q3": d.get("q3", 0),
                            "max": d.get("max_value", 0),
                            "mean": d.get("mean_value", 0),
                            "outliers": []  # Would need separate query
                        }
                        for d in data
                    ]
                }]
            }
        
        elif chart_subtype == "pareto":
            # Pareto chart (bar + line)
            pareto_data = self.calculate_pareto(data)
            return {
                "labels": [d.get("category", "") for d in pareto_data],
                "datasets": [
                    {
                        "label": "Value",
                        "type": "bar",
                        "data": [d.get("value", 0) for d in pareto_data],
                        "yAxisID": "y"
                    },
                    {
                        "label": "Cumulative %",
                        "type": "line",
                        "data": [d.get("cumulative_percentage", 0) for d in pareto_data],
                        "yAxisID": "y1"
                    }
                ]
            }
        
        else:
            # Standard bar chart format
            return {
                "labels": [d.get("category", "") for d in data],
                "datasets": [{
                    "label": self.mapping_config.get("display_config", {}).get("title", "Value"),
                    "data": [d.get("value", 0) for d in data]
                }]
            }
    
    def transform_results(self, raw_data: List[Dict]) -> Dict[str, Any]:
        """Transform raw results into distribution chart format"""
        
        if not raw_data:
            return {
                "widget_type": "distribution_chart",
                "chart_subtype": self.mapping_config.get("chart_subtype", "bar"),
                "data": {"labels": [], "datasets": []},
                "metadata": {
                    "last_updated": datetime.utcnow().isoformat(),
                    "row_count": 0
                }
            }
        
        chart_subtype = self.mapping_config.get("chart_subtype", "bar")
        
        # Calculate total for percentage if needed
        if self.mapping_config.get("show_percentage", False):
            total = sum(d.get("value", 0) for d in raw_data)
            for item in raw_data:
                item["percentage"] = (item.get("value", 0) / total * 100) if total > 0 else 0
        
        # Apply sorting
        sort_by = self.mapping_config.get("sort_by", "value")
        sort_order = self.mapping_config.get("sort_order", "desc")
        
        if sort_by == "value":
            raw_data.sort(key=lambda x: x.get("value", 0), reverse=(sort_order == "desc"))
        elif sort_by == "category":
            raw_data.sort(key=lambda x: x.get("category", ""), reverse=(sort_order == "desc"))
        
        # Apply top N filtering if configured
        top_n = self.mapping_config.get("top_n")
        if top_n and len(raw_data) > top_n:
            # Keep top N and group others
            top_items = raw_data[:top_n]
            other_value = sum(d.get("value", 0) for d in raw_data[top_n:])
            if other_value > 0:
                top_items.append({
                    "category": "Others",
                    "value": other_value,
                    "percentage": (other_value / sum(d.get("value", 0) for d in raw_data) * 100)
                })
            raw_data = top_items
        
        # Format data for specific chart type
        formatted_data = self.format_for_chart_type(raw_data, chart_subtype)
        
        # Calculate summary statistics
        values = [d.get("value", 0) for d in raw_data]
        summary = {
            "total": sum(values),
            "categories": len(raw_data),
            "max_value": max(values) if values else 0,
            "min_value": min(values) if values else 0,
            "avg_value": sum(values) / len(values) if values else 0
        }
        
        # Add distribution metrics
        if chart_subtype == "pareto":
            # Find 80/20 point
            pareto_data = self.calculate_pareto(raw_data)
            for i, item in enumerate(pareto_data):
                if item.get("cumulative_percentage", 0) >= 80:
                    summary["pareto_point"] = {
                        "index": i + 1,
                        "percentage_items": ((i + 1) / len(pareto_data) * 100),
                        "percentage_value": item.get("cumulative_percentage", 0)
                    }
                    break
        
        return {
            "widget_type": "distribution_chart",
            "chart_subtype": chart_subtype,
            "data": formatted_data,
            "summary": summary,
            "metadata": {
                "last_updated": datetime.utcnow().isoformat(),
                "row_count": len(raw_data),
                "aggregation_type": self.mapping_config.get("aggregation_type", "COUNT"),
                "show_percentage": self.mapping_config.get("show_percentage", False),
                "sorted_by": sort_by,
                "sort_order": sort_order
            }
        }