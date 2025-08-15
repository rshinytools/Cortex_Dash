# ABOUTME: KPI Metric Card widget engine implementation
# ABOUTME: Handles single metric aggregations with comparisons and trends

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from app.services.widget_engines.base_widget import WidgetEngine
from app.models.phase1_models import AggregationType, DataGranularity


class KPIMetricCardEngine(WidgetEngine):
    """Engine for KPI Metric Card widgets"""
    
    def get_data_contract(self) -> Dict[str, Any]:
        """Return KPI Metric Card data contract"""
        return {
            "granularity": DataGranularity.SUBJECT_LEVEL,
            "required_fields": [
                {"name": "measure_field", "type": "any", "description": "Field to aggregate"}
            ],
            "optional_fields": [
                {"name": "group_field", "type": "categorical", "description": "Field for segmentation"},
                {"name": "date_field", "type": "date", "description": "Date for trending"},
                {"name": "comparison_field", "type": "numeric", "description": "Field for comparison"}
            ],
            "supported_aggregations": [
                AggregationType.COUNT,
                AggregationType.COUNT_DISTINCT,
                AggregationType.SUM,
                AggregationType.AVG,
                AggregationType.MIN,
                AggregationType.MAX,
                AggregationType.MEDIAN
            ],
            "supports_grouping": True,
            "supports_filtering": True,
            "supports_joins": False,
            "recommended_cache_ttl": 1800
        }
    
    def validate_mapping(self) -> Tuple[bool, List[str]]:
        """Validate KPI Metric Card mapping"""
        errors = []
        
        # Check required fields
        if "measure_field" not in self.mapping_config.get("field_mappings", {}):
            errors.append("measure_field is required")
        
        # Check aggregation type
        agg_type = self.mapping_config.get("aggregation_type")
        if not agg_type:
            errors.append("aggregation_type is required")
        
        # Validate aggregation is supported
        contract = self.get_data_contract()
        supported_aggs = [agg.value for agg in contract["supported_aggregations"]]
        if agg_type and agg_type.upper() not in supported_aggs:
            errors.append(f"Aggregation {agg_type} not supported")
        
        return len(errors) == 0, errors
    
    def build_query(self) -> str:
        """Build SQL query for KPI metric"""
        # Get configuration
        mappings = self.mapping_config.get("field_mappings", {})
        dataset = self.mapping_config.get("primary_dataset", "dataset")
        measure_field = mappings.get("measure_field", {}).get("source_field")
        group_field = mappings.get("group_field", {}).get("source_field")
        date_field = mappings.get("date_field", {}).get("source_field")
        
        # Get aggregation
        agg_type = self.mapping_config.get("aggregation_type", "COUNT")
        agg_enum = AggregationType[agg_type.upper()]
        
        # Build SELECT clause
        select_parts = []
        
        # Main aggregation
        agg_sql = self.get_aggregation_function(agg_enum, measure_field or "*")
        select_parts.append(f"{agg_sql} as value")
        
        # Add grouping field if present
        if group_field:
            select_parts.append(f"{group_field} as group_name")
        
        # Add date field if present (for trending)
        if date_field:
            date_granularity = self.mapping_config.get("date_granularity", "month")
            truncated_date = self.format_date_truncation(date_field, date_granularity)
            select_parts.append(f"{truncated_date} as period")
        
        # Build FROM clause
        from_clause = f"FROM {dataset}"
        
        # Build WHERE clause
        where_clause = self.build_where_clause()
        
        # Build GROUP BY clause
        group_by_parts = []
        if group_field:
            group_by_parts.append(group_field)
        if date_field:
            group_by_parts.append("period")
        
        group_by_clause = ""
        if group_by_parts:
            group_by_clause = f"GROUP BY {', '.join(group_by_parts)}"
        
        # Build ORDER BY clause (for trending)
        order_by_clause = ""
        if date_field:
            order_by_clause = "ORDER BY period"
        
        # Combine query parts
        query = f"""
            SELECT {', '.join(select_parts)}
            {from_clause}
            {where_clause}
            {group_by_clause}
            {order_by_clause}
        """
        
        return query.strip()
    
    def calculate_comparison(self, current_value: float, comparison_config: Dict) -> Dict[str, Any]:
        """Calculate comparison metrics"""
        comparison_type = comparison_config.get("type", "none")
        comparison_result = {
            "type": comparison_type,
            "show": comparison_type != "none"
        }
        
        if comparison_type == "target":
            target_value = comparison_config.get("target_value", 0)
            difference = current_value - target_value
            percentage = (difference / target_value * 100) if target_value != 0 else 0
            
            comparison_result.update({
                "target_value": target_value,
                "difference": difference,
                "percentage": round(percentage, 1),
                "status": "above" if difference > 0 else "below" if difference < 0 else "on_target"
            })
            
        elif comparison_type == "previous_period":
            # This would require a separate query for previous period
            # For now, return placeholder
            comparison_result.update({
                "previous_value": None,
                "difference": None,
                "percentage": None,
                "status": "no_data"
            })
            
        elif comparison_type == "percentage_of_total":
            total_value = comparison_config.get("total_value", 100)
            percentage = (current_value / total_value * 100) if total_value != 0 else 0
            
            comparison_result.update({
                "total_value": total_value,
                "percentage": round(percentage, 1)
            })
        
        return comparison_result
    
    def calculate_trend(self, time_series_data: List[Dict]) -> Dict[str, Any]:
        """Calculate trend from time series data"""
        if len(time_series_data) < 2:
            return {"trend": "flat", "spark_data": []}
        
        # Extract values
        values = [row.get("value", 0) for row in time_series_data]
        
        # Simple trend calculation (comparing last vs first)
        first_value = values[0]
        last_value = values[-1]
        
        if first_value == 0:
            trend = "flat"
        elif last_value > first_value:
            trend = "up"
        elif last_value < first_value:
            trend = "down"
        else:
            trend = "flat"
        
        # Calculate trend percentage
        if first_value != 0:
            trend_percentage = ((last_value - first_value) / first_value) * 100
        else:
            trend_percentage = 0
        
        return {
            "trend": trend,
            "trend_percentage": round(trend_percentage, 1),
            "spark_data": values,
            "periods": len(values)
        }
    
    def transform_results(self, raw_data: List[Dict]) -> Dict[str, Any]:
        """Transform raw results into KPI metric format"""
        
        # Handle empty results
        if not raw_data:
            return {
                "widget_type": "kpi_metric_card",
                "value": 0,
                "formatted_value": "0",
                "comparison": {"show": False},
                "trend": {"trend": "flat", "spark_data": []},
                "metadata": {
                    "last_updated": datetime.utcnow().isoformat(),
                    "row_count": 0
                }
            }
        
        # Get display configuration
        display_config = self.mapping_config.get("display_config", {})
        
        # If we have time series data (trending)
        if "period" in raw_data[0]:
            # Sort by period
            sorted_data = sorted(raw_data, key=lambda x: x.get("period", ""))
            
            # Get latest value
            current_value = sorted_data[-1].get("value", 0)
            
            # Calculate trend
            trend_info = self.calculate_trend(sorted_data)
        else:
            # Single value or grouped values
            if len(raw_data) == 1:
                current_value = raw_data[0].get("value", 0)
            else:
                # If grouped, sum all groups (or take first based on config)
                aggregate_groups = display_config.get("aggregate_groups", True)
                if aggregate_groups:
                    current_value = sum(row.get("value", 0) for row in raw_data)
                else:
                    current_value = raw_data[0].get("value", 0)
            
            trend_info = {"trend": "flat", "spark_data": []}
        
        # Format value based on configuration
        format_type = display_config.get("format", "number")
        decimals = display_config.get("decimals", 0)
        
        if format_type == "percentage":
            formatted_value = f"{round(current_value, decimals)}%"
        elif format_type == "currency":
            currency = display_config.get("currency", "$")
            formatted_value = f"{currency}{current_value:,.{decimals}f}"
        else:
            formatted_value = f"{current_value:,.{decimals}f}"
        
        # Calculate comparison if configured
        comparison_config = self.mapping_config.get("comparison_config", {})
        comparison_result = self.calculate_comparison(current_value, comparison_config)
        
        # Build response
        response = {
            "widget_type": "kpi_metric_card",
            "value": current_value,
            "formatted_value": formatted_value,
            "comparison": comparison_result,
            "trend": trend_info,
            "metadata": {
                "last_updated": datetime.utcnow().isoformat(),
                "row_count": len(raw_data),
                "aggregation_type": self.mapping_config.get("aggregation_type", "COUNT")
            }
        }
        
        # Add grouped data if present
        if "group_name" in raw_data[0]:
            response["grouped_data"] = [
                {
                    "group": row.get("group_name"),
                    "value": row.get("value", 0)
                }
                for row in raw_data
            ]
        
        # Add time series data if present
        if "period" in raw_data[0]:
            response["time_series"] = [
                {
                    "period": row.get("period"),
                    "value": row.get("value", 0)
                }
                for row in sorted(raw_data, key=lambda x: x.get("period", ""))
            ]
        
        return response