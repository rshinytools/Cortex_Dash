# ABOUTME: Test suite for widget engines implementation
# ABOUTME: Tests KPI Metric, Time Series, and Distribution chart engines

import pytest
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.services.widget_engines.kpi_metric_card import KPIMetricCardEngine
from backend.app.services.widget_engines.time_series_chart import TimeSeriesChartEngine
from backend.app.services.widget_engines.distribution_chart import DistributionChartEngine
from backend.app.models.phase1_models import AggregationType, DataGranularity


class TestKPIMetricCardEngine:
    """Test KPI Metric Card widget engine"""
    
    def test_data_contract(self):
        """Test KPI metric card data contract"""
        engine = KPIMetricCardEngine(
            widget_id=uuid.uuid4(),
            study_id=uuid.uuid4(),
            mapping_config={}
        )
        
        contract = engine.get_data_contract()
        
        assert contract["granularity"] == DataGranularity.SUBJECT_LEVEL
        assert len(contract["required_fields"]) == 1
        assert contract["required_fields"][0]["name"] == "measure_field"
        assert AggregationType.COUNT in contract["supported_aggregations"]
        assert contract["supports_grouping"] is True
        assert contract["supports_joins"] is False
    
    def test_validation_success(self):
        """Test successful validation"""
        mapping_config = {
            "field_mappings": {
                "measure_field": {"source_field": "SUBJID"}
            },
            "aggregation_type": "COUNT"
        }
        
        engine = KPIMetricCardEngine(
            widget_id=uuid.uuid4(),
            study_id=uuid.uuid4(),
            mapping_config=mapping_config
        )
        
        is_valid, errors = engine.validate_mapping()
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validation_failure(self):
        """Test validation with missing required fields"""
        mapping_config = {
            "field_mappings": {},
            "aggregation_type": "INVALID"
        }
        
        engine = KPIMetricCardEngine(
            widget_id=uuid.uuid4(),
            study_id=uuid.uuid4(),
            mapping_config=mapping_config
        )
        
        is_valid, errors = engine.validate_mapping()
        assert is_valid is False
        assert "measure_field is required" in errors
    
    def test_query_building(self):
        """Test SQL query generation"""
        mapping_config = {
            "field_mappings": {
                "measure_field": {"source_field": "SUBJID"},
                "group_field": {"source_field": "SITE_ID"}
            },
            "aggregation_type": "COUNT_DISTINCT",
            "primary_dataset": "demographics"
        }
        
        engine = KPIMetricCardEngine(
            widget_id=uuid.uuid4(),
            study_id=uuid.uuid4(),
            mapping_config=mapping_config
        )
        
        query = engine.build_query()
        
        assert "COUNT(DISTINCT SUBJID)" in query
        assert "FROM demographics" in query
        assert "GROUP BY SITE_ID" in query
        assert "as value" in query
        assert "as group_name" in query
    
    def test_comparison_calculation(self):
        """Test comparison calculations"""
        engine = KPIMetricCardEngine(
            widget_id=uuid.uuid4(),
            study_id=uuid.uuid4(),
            mapping_config={}
        )
        
        # Test target comparison
        comparison = engine.calculate_comparison(
            current_value=150,
            comparison_config={
                "type": "target",
                "target_value": 100
            }
        )
        
        assert comparison["type"] == "target"
        assert comparison["difference"] == 50
        assert comparison["percentage"] == 50.0
        assert comparison["status"] == "above"
    
    def test_transform_results(self):
        """Test result transformation"""
        mapping_config = {
            "aggregation_type": "COUNT",
            "display_config": {
                "format": "number",
                "decimals": 0
            }
        }
        
        engine = KPIMetricCardEngine(
            widget_id=uuid.uuid4(),
            study_id=uuid.uuid4(),
            mapping_config=mapping_config
        )
        
        raw_data = [{"value": 150}]
        result = engine.transform_results(raw_data)
        
        assert result["widget_type"] == "kpi_metric_card"
        assert result["value"] == 150
        assert result["formatted_value"] == "150"
        assert "comparison" in result
        assert "trend" in result
        assert "metadata" in result


class TestTimeSeriesChartEngine:
    """Test Time Series Chart widget engine"""
    
    def test_data_contract(self):
        """Test time series chart data contract"""
        engine = TimeSeriesChartEngine(
            widget_id=uuid.uuid4(),
            study_id=uuid.uuid4(),
            mapping_config={}
        )
        
        contract = engine.get_data_contract()
        
        assert contract["granularity"] == DataGranularity.RECORD_LEVEL
        assert len(contract["required_fields"]) == 2
        assert any(f["name"] == "date_field" for f in contract["required_fields"])
        assert any(f["name"] == "value_field" for f in contract["required_fields"])
        assert contract["supports_joins"] is True
        assert contract["max_join_datasets"] == 2
    
    def test_query_building_with_series(self):
        """Test query building with multiple series"""
        mapping_config = {
            "field_mappings": {
                "date_field": {"source_field": "VISIT_DATE"},
                "value_field": {"source_field": "LAB_VALUE"},
                "series_field": {"source_field": "TREATMENT_ARM"}
            },
            "time_granularity": "month",
            "aggregation_type": "AVG",
            "primary_dataset": "lab_results"
        }
        
        engine = TimeSeriesChartEngine(
            widget_id=uuid.uuid4(),
            study_id=uuid.uuid4(),
            mapping_config=mapping_config
        )
        
        query = engine.build_query()
        
        assert "DATE_TRUNC('month', VISIT_DATE)" in query
        assert "AVG(LAB_VALUE)" in query
        assert "TREATMENT_ARM as series" in query
        assert "GROUP BY period, TREATMENT_ARM" in query
    
    def test_cumulative_query(self):
        """Test cumulative aggregation query"""
        mapping_config = {
            "field_mappings": {
                "date_field": {"source_field": "ENROLL_DATE"},
                "value_field": {"source_field": "SUBJID"}
            },
            "time_granularity": "week",
            "aggregation_type": "COUNT_DISTINCT",
            "cumulative": True,
            "primary_dataset": "enrollment"
        }
        
        engine = TimeSeriesChartEngine(
            widget_id=uuid.uuid4(),
            study_id=uuid.uuid4(),
            mapping_config=mapping_config
        )
        
        query = engine.build_query()
        
        assert "SUM(value) OVER" in query
        assert "ORDER BY period" in query
        assert "ROWS UNBOUNDED PRECEDING" in query
    
    def test_moving_average_calculation(self):
        """Test moving average calculation"""
        engine = TimeSeriesChartEngine(
            widget_id=uuid.uuid4(),
            study_id=uuid.uuid4(),
            mapping_config={}
        )
        
        data = [
            {"period": "2024-01", "value": 10},
            {"period": "2024-02", "value": 20},
            {"period": "2024-03", "value": 15},
            {"period": "2024-04", "value": 25},
            {"period": "2024-05", "value": 30}
        ]
        
        result = engine.calculate_moving_average(data, window=3)
        
        assert len(result) == 5
        assert result[0]["moving_avg"] is None  # Not enough data
        assert result[1]["moving_avg"] is None  # Not enough data
        assert result[2]["moving_avg"] == 15.0  # (10+20+15)/3
        assert result[3]["moving_avg"] == 20.0  # (20+15+25)/3
        assert result[4]["moving_avg"] == 23.33  # (15+25+30)/3


class TestDistributionChartEngine:
    """Test Distribution Chart widget engine"""
    
    def test_data_contract(self):
        """Test distribution chart data contract"""
        engine = DistributionChartEngine(
            widget_id=uuid.uuid4(),
            study_id=uuid.uuid4(),
            mapping_config={}
        )
        
        contract = engine.get_data_contract()
        
        assert contract["granularity"] == DataGranularity.RECORD_LEVEL
        assert len(contract["required_fields"]) == 2
        assert any(f["name"] == "category_field" for f in contract["required_fields"])
        assert any(f["name"] == "value_field" for f in contract["required_fields"])
        assert AggregationType.PERCENTILE in contract["supported_aggregations"]
    
    def test_chart_subtypes(self):
        """Test different chart subtypes"""
        subtypes = ["bar", "pie", "donut", "histogram", "box_plot", "pareto"]
        
        for subtype in subtypes:
            mapping_config = {
                "chart_subtype": subtype,
                "field_mappings": {
                    "category_field": {"source_field": "SITE_ID"},
                    "value_field": {"source_field": "SUBJID"}
                },
                "aggregation_type": "COUNT"
            }
            
            engine = DistributionChartEngine(
                widget_id=uuid.uuid4(),
                study_id=uuid.uuid4(),
                mapping_config=mapping_config
            )
            
            # Should not raise error
            is_valid, errors = engine.validate_mapping()
            if subtype != "histogram":
                assert "category_field is required" not in errors
    
    def test_histogram_query(self):
        """Test histogram query with binning"""
        mapping_config = {
            "chart_subtype": "histogram",
            "field_mappings": {
                "value_field": {"source_field": "AGE"}
            },
            "bin_count": 5,
            "aggregation_type": "COUNT",
            "primary_dataset": "demographics"
        }
        
        engine = DistributionChartEngine(
            widget_id=uuid.uuid4(),
            study_id=uuid.uuid4(),
            mapping_config=mapping_config
        )
        
        query = engine.build_histogram_query()
        
        assert "MIN(AGE)" in query
        assert "MAX(AGE)" in query
        assert "generate_series" in query
        assert "bin_width" in query
        assert "GROUP BY bin_start" in query
    
    def test_pareto_calculation(self):
        """Test Pareto analysis calculation"""
        engine = DistributionChartEngine(
            widget_id=uuid.uuid4(),
            study_id=uuid.uuid4(),
            mapping_config={}
        )
        
        data = [
            {"category": "A", "value": 40},
            {"category": "B", "value": 30},
            {"category": "C", "value": 20},
            {"category": "D", "value": 10}
        ]
        
        result = engine.calculate_pareto(data)
        
        assert result[0]["category"] == "A"
        assert result[0]["cumulative_percentage"] == 40.0
        assert result[1]["cumulative_percentage"] == 70.0
        assert result[2]["cumulative_percentage"] == 90.0
        assert result[3]["cumulative_percentage"] == 100.0
    
    def test_format_for_chart_type(self):
        """Test data formatting for different chart types"""
        engine = DistributionChartEngine(
            widget_id=uuid.uuid4(),
            study_id=uuid.uuid4(),
            mapping_config={"display_config": {"title": "Test"}}
        )
        
        data = [
            {"category": "A", "value": 10},
            {"category": "B", "value": 20}
        ]
        
        # Test pie chart format
        pie_result = engine.format_for_chart_type(data, "pie")
        assert "labels" in pie_result
        assert pie_result["labels"] == ["A", "B"]
        assert pie_result["datasets"][0]["data"] == [10, 20]
        
        # Test bar chart format
        bar_result = engine.format_for_chart_type(data, "bar")
        assert bar_result["labels"] == ["A", "B"]
        assert bar_result["datasets"][0]["label"] == "Test"


class TestWidgetEngineIntegration:
    """Integration tests for widget engines"""
    
    def test_cache_key_generation(self):
        """Test cache key generation is unique"""
        config1 = {
            "field_mappings": {"measure_field": {"source_field": "SUBJID"}},
            "aggregation_type": "COUNT"
        }
        
        config2 = {
            "field_mappings": {"measure_field": {"source_field": "PATID"}},
            "aggregation_type": "COUNT"
        }
        
        engine1 = KPIMetricCardEngine(
            widget_id=uuid.uuid4(),
            study_id=uuid.uuid4(),
            mapping_config=config1
        )
        
        engine2 = KPIMetricCardEngine(
            widget_id=uuid.uuid4(),
            study_id=uuid.uuid4(),
            mapping_config=config2
        )
        
        key1 = engine1.get_cache_key()
        key2 = engine2.get_cache_key()
        
        assert key1 != key2
    
    def test_filter_building(self):
        """Test WHERE clause building"""
        engine = KPIMetricCardEngine(
            widget_id=uuid.uuid4(),
            study_id=uuid.uuid4(),
            mapping_config={}
        )
        
        engine.add_filter("STATUS", "equals", "ENROLLED")
        engine.add_filter("AGE", "greater_than", 18)
        engine.add_filter("SITE", "in", ["001", "002", "003"])
        
        where_clause = engine.build_where_clause()
        
        assert "STATUS = 'ENROLLED'" in where_clause
        assert "AGE > 18" in where_clause
        assert "SITE IN ('001', '002', '003')" in where_clause


def run_tests():
    """Run all widget engine tests"""
    print("\n" + "="*60)
    print("WIDGET ENGINE TESTS")
    print("="*60)
    
    # Run pytest programmatically
    import subprocess
    result = subprocess.run(
        ["python", "-m", "pytest", __file__, "-v", "--tb=short"],
        capture_output=True,
        text=True
    )
    
    print(result.stdout)
    if result.stderr:
        print("Errors:", result.stderr)
    
    return result.returncode


if __name__ == "__main__":
    import sys
    sys.exit(run_tests())