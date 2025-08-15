# ABOUTME: Time Series Chart widget engine implementation
# ABOUTME: Handles temporal data visualization with multiple series and aggregations

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from app.services.widget_engines.base_widget import WidgetEngine
from app.models.phase1_models import AggregationType, DataGranularity, JoinType


class TimeSeriesChartEngine(WidgetEngine):
    """Engine for Time Series Chart widgets"""
    
    def get_data_contract(self) -> Dict[str, Any]:
        """Return Time Series Chart data contract"""
        return {
            "granularity": DataGranularity.RECORD_LEVEL,
            "required_fields": [
                {"name": "date_field", "type": "date", "description": "Date/time field"},
                {"name": "value_field", "type": "numeric", "description": "Value to plot"}
            ],
            "optional_fields": [
                {"name": "series_field", "type": "categorical", "description": "Field for multiple series"},
                {"name": "error_field", "type": "numeric", "description": "Error bar values"},
                {"name": "group_field", "type": "categorical", "description": "Field for faceting"}
            ],
            "supported_aggregations": [
                AggregationType.SUM,
                AggregationType.AVG,
                AggregationType.COUNT,
                AggregationType.COUNT_DISTINCT,
                AggregationType.MIN,
                AggregationType.MAX,
                AggregationType.MEDIAN
            ],
            "supports_grouping": True,
            "grouping_fields": ["hour", "day", "week", "month", "quarter", "year"],
            "supports_filtering": True,
            "supports_joins": True,
            "max_join_datasets": 2,
            "recommended_cache_ttl": 3600
        }
    
    def validate_mapping(self) -> Tuple[bool, List[str]]:
        """Validate Time Series Chart mapping"""
        errors = []
        
        mappings = self.mapping_config.get("field_mappings", {})
        
        # Check required fields
        if "date_field" not in mappings:
            errors.append("date_field is required")
        if "value_field" not in mappings:
            errors.append("value_field is required")
        
        # Check time granularity
        time_granularity = self.mapping_config.get("time_granularity")
        if not time_granularity:
            errors.append("time_granularity is required")
        elif time_granularity not in ["hour", "day", "week", "month", "quarter", "year"]:
            errors.append(f"Invalid time_granularity: {time_granularity}")
        
        # Check aggregation type
        agg_type = self.mapping_config.get("aggregation_type")
        if not agg_type:
            errors.append("aggregation_type is required")
        
        return len(errors) == 0, errors
    
    def build_query(self) -> str:
        """Build SQL query for time series data"""
        mappings = self.mapping_config.get("field_mappings", {})
        dataset = self.mapping_config.get("primary_dataset", "dataset")
        
        # Get field mappings
        date_field = mappings.get("date_field", {}).get("source_field")
        value_field = mappings.get("value_field", {}).get("source_field")
        series_field = mappings.get("series_field", {}).get("source_field")
        error_field = mappings.get("error_field", {}).get("source_field")
        
        # Get configuration
        time_granularity = self.mapping_config.get("time_granularity", "day")
        agg_type = self.mapping_config.get("aggregation_type", "AVG")
        agg_enum = AggregationType[agg_type.upper()]
        
        # Check for cumulative mode
        is_cumulative = self.mapping_config.get("cumulative", False)
        
        # Build SELECT clause
        select_parts = []
        
        # Date truncation for grouping
        truncated_date = self.format_date_truncation(date_field, time_granularity)
        select_parts.append(f"{truncated_date} as period")
        
        # Main aggregation
        agg_sql = self.get_aggregation_function(agg_enum, value_field)
        select_parts.append(f"{agg_sql} as value")
        
        # Add series field if present
        if series_field:
            select_parts.append(f"{series_field} as series")
        
        # Add error field if present (for error bars)
        if error_field:
            select_parts.append(f"STDDEV({error_field}) as error_margin")
            select_parts.append(f"COUNT({error_field}) as sample_size")
        
        # Add additional statistics
        if self.mapping_config.get("include_statistics", False):
            select_parts.append(f"MIN({value_field}) as min_value")
            select_parts.append(f"MAX({value_field}) as max_value")
            select_parts.append(f"PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY {value_field}) as q1")
            select_parts.append(f"PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY {value_field}) as median")
            select_parts.append(f"PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY {value_field}) as q3")
        
        # Build FROM clause with JOINs
        from_clause = f"FROM {dataset}"
        join_clause = self.build_join_clause()
        
        # Build WHERE clause
        where_clause = self.build_where_clause()
        
        # Add date range filter if specified
        date_range = self.mapping_config.get("date_range", {})
        if date_range:
            start_date = date_range.get("start")
            end_date = date_range.get("end")
            if start_date and end_date:
                date_filter = f"{date_field} BETWEEN '{start_date}' AND '{end_date}'"
                if where_clause:
                    where_clause += f" AND {date_filter}"
                else:
                    where_clause = f"WHERE {date_filter}"
        
        # Build GROUP BY clause
        group_by_parts = ["period"]
        if series_field:
            group_by_parts.append(series_field)
        group_by_clause = f"GROUP BY {', '.join(group_by_parts)}"
        
        # Build ORDER BY clause
        order_by_parts = ["period"]
        if series_field:
            order_by_parts.append(series_field)
        order_by_clause = f"ORDER BY {', '.join(order_by_parts)}"
        
        # Build base query
        base_query = f"""
            SELECT {', '.join(select_parts)}
            {from_clause}
            {join_clause}
            {where_clause}
            {group_by_clause}
            {order_by_clause}
        """
        
        # If cumulative, wrap in window function
        if is_cumulative:
            window_partition = f"PARTITION BY series" if series_field else ""
            query = f"""
                SELECT 
                    period,
                    {'series,' if series_field else ''}
                    SUM(value) OVER ({window_partition} ORDER BY period ROWS UNBOUNDED PRECEDING) as value
                    {'error_margin,' if error_field else ''}
                    {'sample_size' if error_field else ''}
                FROM ({base_query.strip()}) as base_data
                ORDER BY period {'series' if series_field else ''}
            """
        else:
            query = base_query
        
        return query.strip()
    
    def calculate_moving_average(self, data: List[Dict], window: int = 7) -> List[Dict]:
        """Calculate moving average for smoothing"""
        if len(data) < window:
            return data
        
        result = []
        for i in range(len(data)):
            if i < window - 1:
                # Not enough data for full window
                result.append({
                    **data[i],
                    "moving_avg": None
                })
            else:
                # Calculate moving average
                window_values = [data[j]["value"] for j in range(i - window + 1, i + 1)]
                moving_avg = sum(window_values) / window
                result.append({
                    **data[i],
                    "moving_avg": round(moving_avg, 2)
                })
        
        return result
    
    def calculate_forecast(self, data: List[Dict], periods: int = 3) -> List[Dict]:
        """Simple linear forecast for future periods"""
        if len(data) < 2:
            return []
        
        # Extract values for trend calculation
        values = [d["value"] for d in data]
        n = len(values)
        
        # Simple linear regression
        x_mean = (n - 1) / 2
        y_mean = sum(values) / n
        
        numerator = sum((i - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            slope = 0
        else:
            slope = numerator / denominator
        
        intercept = y_mean - slope * x_mean
        
        # Generate forecast
        forecast = []
        last_period = data[-1]["period"]
        
        for i in range(1, periods + 1):
            forecast_value = intercept + slope * (n - 1 + i)
            forecast.append({
                "period": f"Forecast +{i}",
                "value": round(max(0, forecast_value), 2),
                "is_forecast": True
            })
        
        return forecast
    
    def transform_results(self, raw_data: List[Dict]) -> Dict[str, Any]:
        """Transform raw results into time series format"""
        
        if not raw_data:
            return {
                "widget_type": "time_series_chart",
                "chart_type": self.mapping_config.get("chart_type", "line"),
                "data": [],
                "series": [],
                "metadata": {
                    "last_updated": datetime.utcnow().isoformat(),
                    "row_count": 0,
                    "time_granularity": self.mapping_config.get("time_granularity", "day")
                }
            }
        
        # Group data by series if present
        has_series = "series" in raw_data[0]
        
        if has_series:
            # Group by series
            series_data = {}
            for row in raw_data:
                series_name = row.get("series", "Default")
                if series_name not in series_data:
                    series_data[series_name] = []
                series_data[series_name].append({
                    "period": row.get("period"),
                    "value": row.get("value", 0),
                    "error_margin": row.get("error_margin"),
                    "sample_size": row.get("sample_size")
                })
            
            # Format for chart library
            formatted_data = {
                "labels": sorted(list(set(row["period"] for row in raw_data))),
                "datasets": []
            }
            
            for series_name, series_points in series_data.items():
                # Sort by period
                sorted_points = sorted(series_points, key=lambda x: x["period"])
                
                # Apply moving average if configured
                if self.mapping_config.get("moving_average", {}).get("enabled", False):
                    window = self.mapping_config.get("moving_average", {}).get("window", 7)
                    sorted_points = self.calculate_moving_average(sorted_points, window)
                
                dataset = {
                    "label": series_name,
                    "data": [p["value"] for p in sorted_points],
                    "periods": [p["period"] for p in sorted_points]
                }
                
                # Add error bars if present
                if sorted_points[0].get("error_margin") is not None:
                    dataset["error_bars"] = [p.get("error_margin", 0) for p in sorted_points]
                
                # Add moving average line if calculated
                if "moving_avg" in sorted_points[0]:
                    dataset["moving_average"] = [p.get("moving_avg") for p in sorted_points]
                
                formatted_data["datasets"].append(dataset)
        else:
            # Single series
            sorted_data = sorted(raw_data, key=lambda x: x.get("period", ""))
            
            # Apply moving average if configured
            if self.mapping_config.get("moving_average", {}).get("enabled", False):
                window = self.mapping_config.get("moving_average", {}).get("window", 7)
                sorted_data = self.calculate_moving_average(sorted_data, window)
            
            # Add forecast if configured
            forecast_data = []
            if self.mapping_config.get("forecast", {}).get("enabled", False):
                periods = self.mapping_config.get("forecast", {}).get("periods", 3)
                forecast_data = self.calculate_forecast(sorted_data, periods)
            
            formatted_data = {
                "labels": [row["period"] for row in sorted_data] + [f["period"] for f in forecast_data],
                "datasets": [{
                    "label": self.mapping_config.get("display_config", {}).get("title", "Value"),
                    "data": [row.get("value", 0) for row in sorted_data] + [f["value"] for f in forecast_data],
                    "is_forecast": [False] * len(sorted_data) + [True] * len(forecast_data)
                }]
            }
            
            # Add moving average if calculated
            if sorted_data and "moving_avg" in sorted_data[0]:
                formatted_data["datasets"].append({
                    "label": "Moving Average",
                    "data": [row.get("moving_avg") for row in sorted_data],
                    "type": "line",
                    "borderDash": [5, 5]
                })
        
        # Calculate summary statistics
        all_values = [row.get("value", 0) for row in raw_data]
        summary = {
            "min": min(all_values) if all_values else 0,
            "max": max(all_values) if all_values else 0,
            "avg": sum(all_values) / len(all_values) if all_values else 0,
            "total": sum(all_values),
            "data_points": len(all_values)
        }
        
        return {
            "widget_type": "time_series_chart",
            "chart_type": self.mapping_config.get("chart_type", "line"),
            "data": formatted_data,
            "summary": summary,
            "metadata": {
                "last_updated": datetime.utcnow().isoformat(),
                "row_count": len(raw_data),
                "time_granularity": self.mapping_config.get("time_granularity", "day"),
                "aggregation_type": self.mapping_config.get("aggregation_type", "AVG"),
                "is_cumulative": self.mapping_config.get("cumulative", False)
            }
        }