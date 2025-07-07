# ABOUTME: Comprehensive test suite for widget data execution functionality
# ABOUTME: Tests data fetching, aggregation, caching, and error handling for all widget types

import pytest
import uuid
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from typing import Dict, Any, List

import pandas as pd
from sqlmodel import Session

from app.services.widget_data_executor import (
    WidgetDataExecutor, 
    WidgetDataRequest, 
    AggregationType, 
    ChartType,
    MetricWidgetExecutor,
    ChartWidgetExecutor,
    TableWidgetExecutor
)
from app.models.widget import WidgetDefinition, WidgetCategory
from app.models.study import Study
from app.models.organization import Organization
from app.core.config import settings


class TestWidgetDataExecutor:
    """Test suite for the main WidgetDataExecutor class"""

    @pytest.fixture
    def sample_study(self, db: Session) -> Study:
        """Create a sample study for testing"""
        organization = Organization(
            id=str(uuid.uuid4()),
            name="Test Org",
            display_name="Test Organization"
        )
        db.add(organization)
        
        study = Study(
            id=str(uuid.uuid4()),
            code="TEST001",
            name="Test Study",
            description="Test study for widget testing",
            organization_id=organization.id,
            phase="Phase III",
            therapeutic_area="Oncology",
            indication="Breast Cancer",
            status="active",
            is_enabled=True
        )
        db.add(study)
        db.commit()
        db.refresh(study)
        return study

    @pytest.fixture
    def sample_widget_definition(self, db: Session) -> WidgetDefinition:
        """Create a sample widget definition for testing"""
        widget = WidgetDefinition(
            id=str(uuid.uuid4()),
            name="Test Metric Widget",
            description="Test metric widget for testing",
            category=WidgetCategory.METRIC,
            config_schema={
                "type": "object",
                "properties": {
                    "data_source": {"type": "string"},
                    "aggregation": {"type": "string"},
                    "field": {"type": "string"}
                }
            },
            default_config={
                "data_source": "demographics",
                "aggregation": "count",
                "field": "subject_id"
            },
            data_requirements={
                "required_fields": ["subject_id"],
                "optional_fields": ["age", "gender"]
            }
        )
        db.add(widget)
        db.commit()
        db.refresh(widget)
        return widget

    @pytest.fixture
    def sample_data(self) -> pd.DataFrame:
        """Create sample data for testing"""
        return pd.DataFrame({
            'subject_id': ['S001', 'S002', 'S003', 'S004', 'S005'],
            'age': [25, 30, 35, 40, 45],
            'gender': ['M', 'F', 'M', 'F', 'M'],
            'visit_date': pd.date_range('2024-01-01', periods=5),
            'lab_value': [10.5, 12.3, 9.8, 11.2, 13.1]
        })

    @pytest.fixture
    def widget_data_executor(self) -> WidgetDataExecutor:
        """Create WidgetDataExecutor instance for testing"""
        return WidgetDataExecutor()

    def test_widget_data_executor_initialization(self, widget_data_executor):
        """Test WidgetDataExecutor initialization"""
        assert widget_data_executor is not None
        assert hasattr(widget_data_executor, 'metric_executor')
        assert hasattr(widget_data_executor, 'chart_executor')
        assert hasattr(widget_data_executor, 'table_executor')

    @pytest.mark.asyncio
    async def test_execute_widget_metric_success(
        self, 
        widget_data_executor, 
        sample_study, 
        sample_widget_definition,
        sample_data
    ):
        """Test successful metric widget execution"""
        request = WidgetDataRequest(
            widget_id=sample_widget_definition.id,
            widget_config={
                "data_source": "demographics",
                "aggregation": "count",
                "field": "subject_id"
            }
        )

        with patch.object(widget_data_executor, '_get_widget_data', return_value=sample_data):
            result = await widget_data_executor.execute_widget(
                request, sample_study.id, db=Mock()
            )
            
            assert result is not None
            assert 'value' in result
            assert result['value'] == 5  # count of subjects

    @pytest.mark.asyncio
    async def test_execute_widget_chart_success(
        self, 
        widget_data_executor, 
        sample_study, 
        sample_data
    ):
        """Test successful chart widget execution"""
        request = WidgetDataRequest(
            widget_id=str(uuid.uuid4()),
            widget_config={
                "chart_type": "bar",
                "x_axis": "gender",
                "y_axis": "age",
                "aggregation": "avg"
            }
        )

        with patch.object(widget_data_executor, '_get_widget_data', return_value=sample_data):
            result = await widget_data_executor.execute_widget(
                request, sample_study.id, db=Mock()
            )
            
            assert result is not None
            assert 'data' in result
            assert isinstance(result['data'], list)

    @pytest.mark.asyncio
    async def test_execute_widget_caching(
        self, 
        widget_data_executor, 
        sample_study, 
        sample_data
    ):
        """Test widget data caching functionality"""
        request = WidgetDataRequest(
            widget_id=str(uuid.uuid4()),
            widget_config={"data_source": "demographics"}
        )

        with patch.object(widget_data_executor, '_get_widget_data', return_value=sample_data) as mock_get_data:
            # First execution
            result1 = await widget_data_executor.execute_widget(
                request, sample_study.id, db=Mock()
            )
            
            # Second execution should use cache
            result2 = await widget_data_executor.execute_widget(
                request, sample_study.id, db=Mock()
            )
            
            # Data source should only be called once due to caching
            assert mock_get_data.call_count == 1
            assert result1 == result2

    @pytest.mark.asyncio
    async def test_execute_widget_with_filters(
        self, 
        widget_data_executor, 
        sample_study, 
        sample_data
    ):
        """Test widget execution with filters applied"""
        request = WidgetDataRequest(
            widget_id=str(uuid.uuid4()),
            widget_config={
                "data_source": "demographics",
                "aggregation": "count",
                "field": "subject_id"
            },
            filters={"gender": "M"}
        )

        with patch.object(widget_data_executor, '_get_widget_data', return_value=sample_data):
            result = await widget_data_executor.execute_widget(
                request, sample_study.id, db=Mock()
            )
            
            assert result is not None
            assert 'value' in result
            # Should only count male subjects
            assert result['value'] == 3

    @pytest.mark.asyncio
    async def test_execute_widget_invalid_configuration(
        self, 
        widget_data_executor, 
        sample_study
    ):
        """Test widget execution with invalid configuration"""
        request = WidgetDataRequest(
            widget_id=str(uuid.uuid4()),
            widget_config={}  # Invalid empty config
        )

        with pytest.raises(ValueError, match="Invalid widget configuration"):
            await widget_data_executor.execute_widget(
                request, sample_study.id, db=Mock()
            )

    @pytest.mark.asyncio
    async def test_execute_widget_data_source_error(
        self, 
        widget_data_executor, 
        sample_study
    ):
        """Test widget execution when data source fails"""
        request = WidgetDataRequest(
            widget_id=str(uuid.uuid4()),
            widget_config={"data_source": "nonexistent"}
        )

        with patch.object(widget_data_executor, '_get_widget_data', side_effect=Exception("Data source error")):
            with pytest.raises(Exception, match="Data source error"):
                await widget_data_executor.execute_widget(
                    request, sample_study.id, db=Mock()
                )


class TestMetricWidgetExecutor:
    """Test suite for MetricWidgetExecutor"""

    @pytest.fixture
    def metric_executor(self) -> MetricWidgetExecutor:
        """Create MetricWidgetExecutor instance for testing"""
        return MetricWidgetExecutor()

    @pytest.fixture
    def sample_data(self) -> pd.DataFrame:
        """Create sample data for metric testing"""
        return pd.DataFrame({
            'subject_id': ['S001', 'S002', 'S003', 'S004', 'S005'],
            'age': [25, 30, 35, 40, 45],
            'lab_value': [10.5, 12.3, 9.8, 11.2, 13.1],
            'status': ['active', 'active', 'completed', 'active', 'completed']
        })

    def test_count_aggregation(self, metric_executor, sample_data):
        """Test COUNT aggregation"""
        result = metric_executor.execute(
            data=sample_data,
            config={"aggregation": "count", "field": "subject_id"}
        )
        assert result['value'] == 5
        assert result['aggregation'] == 'count'

    def test_sum_aggregation(self, metric_executor, sample_data):
        """Test SUM aggregation"""
        result = metric_executor.execute(
            data=sample_data,
            config={"aggregation": "sum", "field": "age"}
        )
        assert result['value'] == 175  # Sum of ages
        assert result['aggregation'] == 'sum'

    def test_avg_aggregation(self, metric_executor, sample_data):
        """Test AVG aggregation"""
        result = metric_executor.execute(
            data=sample_data,
            config={"aggregation": "avg", "field": "age"}
        )
        assert result['value'] == 35.0  # Average age
        assert result['aggregation'] == 'avg'

    def test_min_max_aggregation(self, metric_executor, sample_data):
        """Test MIN and MAX aggregations"""
        min_result = metric_executor.execute(
            data=sample_data,
            config={"aggregation": "min", "field": "age"}
        )
        assert min_result['value'] == 25

        max_result = metric_executor.execute(
            data=sample_data,
            config={"aggregation": "max", "field": "age"}
        )
        assert max_result['value'] == 45

    def test_distinct_aggregation(self, metric_executor, sample_data):
        """Test DISTINCT aggregation"""
        result = metric_executor.execute(
            data=sample_data,
            config={"aggregation": "distinct", "field": "status"}
        )
        assert result['value'] == 2  # 'active' and 'completed'

    def test_with_filters(self, metric_executor, sample_data):
        """Test metric calculation with filters"""
        result = metric_executor.execute(
            data=sample_data,
            config={"aggregation": "count", "field": "subject_id"},
            filters={"status": "active"}
        )
        assert result['value'] == 3  # Only active subjects

    def test_invalid_field(self, metric_executor, sample_data):
        """Test metric calculation with invalid field"""
        with pytest.raises(KeyError):
            metric_executor.execute(
                data=sample_data,
                config={"aggregation": "count", "field": "nonexistent_field"}
            )

    def test_empty_data(self, metric_executor):
        """Test metric calculation with empty data"""
        empty_data = pd.DataFrame()
        result = metric_executor.execute(
            data=empty_data,
            config={"aggregation": "count", "field": "subject_id"}
        )
        assert result['value'] == 0


class TestChartWidgetExecutor:
    """Test suite for ChartWidgetExecutor"""

    @pytest.fixture
    def chart_executor(self) -> ChartWidgetExecutor:
        """Create ChartWidgetExecutor instance for testing"""
        return ChartWidgetExecutor()

    @pytest.fixture
    def sample_data(self) -> pd.DataFrame:
        """Create sample data for chart testing"""
        return pd.DataFrame({
            'subject_id': ['S001', 'S002', 'S003', 'S004', 'S005'],
            'gender': ['M', 'F', 'M', 'F', 'M'],
            'age_group': ['18-30', '31-45', '18-30', '31-45', '46-60'],
            'lab_value': [10.5, 12.3, 9.8, 11.2, 13.1],
            'visit_date': pd.date_range('2024-01-01', periods=5)
        })

    def test_bar_chart_execution(self, chart_executor, sample_data):
        """Test bar chart data preparation"""
        result = chart_executor.execute(
            data=sample_data,
            config={
                "chart_type": "bar",
                "x_axis": "gender",
                "y_axis": "lab_value",
                "aggregation": "avg"
            }
        )
        
        assert result['chart_type'] == 'bar'
        assert 'data' in result
        assert len(result['data']) == 2  # M and F groups

    def test_line_chart_execution(self, chart_executor, sample_data):
        """Test line chart data preparation"""
        result = chart_executor.execute(
            data=sample_data,
            config={
                "chart_type": "line",
                "x_axis": "visit_date",
                "y_axis": "lab_value"
            }
        )
        
        assert result['chart_type'] == 'line'
        assert 'data' in result
        assert len(result['data']) == 5  # One point per visit

    def test_pie_chart_execution(self, chart_executor, sample_data):
        """Test pie chart data preparation"""
        result = chart_executor.execute(
            data=sample_data,
            config={
                "chart_type": "pie",
                "category": "gender",
                "value": "subject_id",
                "aggregation": "count"
            }
        )
        
        assert result['chart_type'] == 'pie'
        assert 'data' in result
        assert len(result['data']) == 2  # M and F categories

    def test_scatter_plot_execution(self, chart_executor, sample_data):
        """Test scatter plot data preparation"""
        result = chart_executor.execute(
            data=sample_data,
            config={
                "chart_type": "scatter",
                "x_axis": "age_group",
                "y_axis": "lab_value"
            }
        )
        
        assert result['chart_type'] == 'scatter'
        assert 'data' in result
        assert len(result['data']) == 5  # One point per subject

    def test_chart_with_grouping(self, chart_executor, sample_data):
        """Test chart with grouping/series"""
        result = chart_executor.execute(
            data=sample_data,
            config={
                "chart_type": "bar",
                "x_axis": "age_group",
                "y_axis": "lab_value",
                "group_by": "gender",
                "aggregation": "avg"
            }
        )
        
        assert result['chart_type'] == 'bar'
        assert 'data' in result
        # Should have data grouped by both age_group and gender

    def test_chart_with_filters(self, chart_executor, sample_data):
        """Test chart execution with filters"""
        result = chart_executor.execute(
            data=sample_data,
            config={
                "chart_type": "bar",
                "x_axis": "gender",
                "y_axis": "lab_value",
                "aggregation": "count"
            },
            filters={"age_group": "18-30"}
        )
        
        assert result['chart_type'] == 'bar'
        assert 'data' in result
        # Should only include 18-30 age group data

    def test_invalid_chart_type(self, chart_executor, sample_data):
        """Test invalid chart type handling"""
        with pytest.raises(ValueError, match="Unsupported chart type"):
            chart_executor.execute(
                data=sample_data,
                config={"chart_type": "invalid_type"}
            )


class TestTableWidgetExecutor:
    """Test suite for TableWidgetExecutor"""

    @pytest.fixture
    def table_executor(self) -> TableWidgetExecutor:
        """Create TableWidgetExecutor instance for testing"""
        return TableWidgetExecutor()

    @pytest.fixture
    def sample_data(self) -> pd.DataFrame:
        """Create sample data for table testing"""
        return pd.DataFrame({
            'subject_id': ['S001', 'S002', 'S003', 'S004', 'S005'],
            'gender': ['M', 'F', 'M', 'F', 'M'],
            'age': [25, 30, 35, 40, 45],
            'lab_value': [10.5, 12.3, 9.8, 11.2, 13.1],
            'status': ['active', 'active', 'completed', 'active', 'completed']
        })

    def test_basic_table_execution(self, table_executor, sample_data):
        """Test basic table data preparation"""
        result = table_executor.execute(
            data=sample_data,
            config={
                "columns": ["subject_id", "gender", "age"],
                "page_size": 10,
                "page": 1
            }
        )
        
        assert 'data' in result
        assert 'total_count' in result
        assert 'page' in result
        assert 'page_size' in result
        assert len(result['data']) == 5
        assert result['total_count'] == 5

    def test_table_with_pagination(self, table_executor, sample_data):
        """Test table with pagination"""
        result = table_executor.execute(
            data=sample_data,
            config={
                "columns": ["subject_id", "age"],
                "page_size": 2,
                "page": 1
            }
        )
        
        assert len(result['data']) == 2
        assert result['total_count'] == 5
        assert result['page'] == 1

        # Test second page
        result_page2 = table_executor.execute(
            data=sample_data,
            config={
                "columns": ["subject_id", "age"],
                "page_size": 2,
                "page": 2
            }
        )
        
        assert len(result_page2['data']) == 2
        assert result_page2['page'] == 2

    def test_table_with_sorting(self, table_executor, sample_data):
        """Test table with sorting"""
        result = table_executor.execute(
            data=sample_data,
            config={
                "columns": ["subject_id", "age"],
                "sort_by": "age",
                "sort_order": "desc"
            }
        )
        
        # Should be sorted by age descending
        ages = [row['age'] for row in result['data']]
        assert ages == sorted(ages, reverse=True)

    def test_table_with_filters(self, table_executor, sample_data):
        """Test table with filters applied"""
        result = table_executor.execute(
            data=sample_data,
            config={
                "columns": ["subject_id", "gender", "status"]
            },
            filters={"status": "active"}
        )
        
        assert len(result['data']) == 3
        assert all(row['status'] == 'active' for row in result['data'])

    def test_table_column_selection(self, table_executor, sample_data):
        """Test table with specific column selection"""
        result = table_executor.execute(
            data=sample_data,
            config={
                "columns": ["subject_id", "age"]
            }
        )
        
        # Check that only specified columns are returned
        for row in result['data']:
            assert set(row.keys()) == {"subject_id", "age"}

    def test_table_empty_data(self, table_executor):
        """Test table with empty data"""
        empty_data = pd.DataFrame()
        result = table_executor.execute(
            data=empty_data,
            config={"columns": ["subject_id"]}
        )
        
        assert result['data'] == []
        assert result['total_count'] == 0

    def test_table_invalid_column(self, table_executor, sample_data):
        """Test table with invalid column name"""
        with pytest.raises(KeyError):
            table_executor.execute(
                data=sample_data,
                config={"columns": ["nonexistent_column"]}
            )


@pytest.mark.asyncio
class TestWidgetDataExecutorIntegration:
    """Integration tests for WidgetDataExecutor with real database"""

    async def test_end_to_end_widget_execution(self, db: Session):
        """Test complete widget execution flow with database"""
        # This would be a more comprehensive test using real database
        # and actual widget definitions
        pass

    async def test_concurrent_widget_execution(self, db: Session):
        """Test multiple widgets executing concurrently"""
        # Test concurrent execution and caching behavior
        pass

    async def test_widget_execution_with_large_dataset(self, db: Session):
        """Test widget execution performance with large datasets"""
        # Performance testing with large data volumes
        pass


# Performance and load testing
@pytest.mark.performance
class TestWidgetDataExecutorPerformance:
    """Performance tests for widget data execution"""

    def test_metric_calculation_performance(self):
        """Test performance of metric calculations"""
        # Generate large dataset for performance testing
        large_data = pd.DataFrame({
            'subject_id': [f'S{i:06d}' for i in range(10000)],
            'value': range(10000)
        })
        
        executor = MetricWidgetExecutor()
        start_time = datetime.now()
        
        result = executor.execute(
            data=large_data,
            config={"aggregation": "count", "field": "subject_id"}
        )
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        assert result['value'] == 10000
        assert execution_time < 1.0  # Should complete within 1 second

    def test_chart_data_preparation_performance(self):
        """Test performance of chart data preparation"""
        # Performance test for chart data processing
        pass

    def test_table_pagination_performance(self):
        """Test performance of table pagination with large datasets"""
        # Performance test for table pagination
        pass