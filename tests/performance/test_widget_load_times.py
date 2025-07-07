# ABOUTME: Performance tests for widget loading and rendering times
# ABOUTME: Tests widget execution speed, caching effectiveness, and scalability

import pytest
import time
import asyncio
import statistics
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import uuid

import pandas as pd
from sqlmodel import Session

from app.services.widget_data_executor import WidgetDataExecutor, WidgetDataRequest
from app.services.redis_cache import get_redis_cache
from app.models.widget import WidgetDefinition, WidgetCategory
from app.models.study import Study
from app.models.organization import Organization


@pytest.mark.performance
class TestWidgetPerformance:
    """Performance tests for widget data execution"""

    @pytest.fixture
    def large_sample_data(self) -> pd.DataFrame:
        """Create large sample dataset for performance testing"""
        import numpy as np
        
        # Generate 100,000 records
        n_records = 100000
        
        data = {
            'subject_id': [f'S{i:06d}' for i in range(n_records)],
            'age': np.random.randint(18, 80, n_records),
            'gender': np.random.choice(['M', 'F'], n_records),
            'site': np.random.choice([f'Site {i:03d}' for i in range(1, 21)], n_records),
            'enrollment_date': pd.date_range('2020-01-01', periods=n_records, freq='H'),
            'weight': np.random.normal(70, 15, n_records),
            'height': np.random.normal(170, 20, n_records),
            'lab_value_1': np.random.normal(100, 25, n_records),
            'lab_value_2': np.random.normal(50, 10, n_records),
            'visit_number': np.random.randint(1, 10, n_records),
            'status': np.random.choice(['active', 'completed', 'withdrawn'], n_records, p=[0.7, 0.2, 0.1])
        }
        
        return pd.DataFrame(data)

    @pytest.fixture
    def performance_study(self, db: Session) -> Study:
        """Create study for performance testing"""
        org = Organization(
            id=str(uuid.uuid4()),
            name="Performance Test Org",
            display_name="Performance Testing"
        )
        db.add(org)
        
        study = Study(
            id=str(uuid.uuid4()),
            code="PERF-001",
            name="Performance Test Study",
            organization_id=org.id,
            status="active"
        )
        db.add(study)
        db.commit()
        db.refresh(study)
        return study

    @pytest.fixture
    def metric_widget(self, db: Session) -> WidgetDefinition:
        """Create metric widget for performance testing"""
        widget = WidgetDefinition(
            id=str(uuid.uuid4()),
            name="Performance Metric Widget",
            category=WidgetCategory.METRIC,
            config_schema={"type": "object"},
            default_config={
                "data_source": "demographics",
                "aggregation": "count",
                "field": "subject_id"
            }
        )
        db.add(widget)
        db.commit()
        db.refresh(widget)
        return widget

    def test_metric_widget_performance_baseline(self, large_sample_data: pd.DataFrame):
        """Test baseline performance for metric widget execution"""
        executor = WidgetDataExecutor()
        
        # Test different aggregation types
        aggregations = ['count', 'sum', 'avg', 'min', 'max', 'distinct']
        performance_results = {}
        
        for aggregation in aggregations:
            config = {
                "aggregation": aggregation,
                "field": "age" if aggregation != "count" else "subject_id"
            }
            
            # Warm up
            executor.metric_executor.execute(large_sample_data, config)
            
            # Measure performance
            start_time = time.perf_counter()
            
            for _ in range(10):  # Run 10 times for average
                result = executor.metric_executor.execute(large_sample_data, config)
            
            end_time = time.perf_counter()
            avg_time = (end_time - start_time) / 10
            
            performance_results[aggregation] = avg_time
            
            # Performance assertions
            assert avg_time < 0.1, f"{aggregation} aggregation took {avg_time:.3f}s, should be < 0.1s"
            assert result is not None
        
        print(f"Metric widget performance results: {performance_results}")

    def test_chart_widget_performance_with_large_dataset(self, large_sample_data: pd.DataFrame):
        """Test chart widget performance with large datasets"""
        executor = WidgetDataExecutor()
        
        chart_configs = [
            {
                "chart_type": "bar",
                "x_axis": "site",
                "y_axis": "age",
                "aggregation": "avg"
            },
            {
                "chart_type": "line",
                "x_axis": "enrollment_date",
                "y_axis": "subject_id",
                "aggregation": "count"
            },
            {
                "chart_type": "pie",
                "category": "gender",
                "value": "subject_id",
                "aggregation": "count"
            }
        ]
        
        for config in chart_configs:
            start_time = time.perf_counter()
            
            result = executor.chart_executor.execute(large_sample_data, config)
            
            end_time = time.perf_counter()
            execution_time = end_time - start_time
            
            assert execution_time < 2.0, f"Chart widget took {execution_time:.3f}s, should be < 2.0s"
            assert result is not None
            assert 'data' in result
            
            print(f"Chart widget ({config['chart_type']}) execution time: {execution_time:.3f}s")

    def test_table_widget_pagination_performance(self, large_sample_data: pd.DataFrame):
        """Test table widget pagination performance"""
        executor = WidgetDataExecutor()
        
        page_sizes = [10, 50, 100, 500, 1000]
        
        for page_size in page_sizes:
            config = {
                "columns": ["subject_id", "age", "gender", "site"],
                "page_size": page_size,
                "page": 1
            }
            
            start_time = time.perf_counter()
            
            result = executor.table_executor.execute(large_sample_data, config)
            
            end_time = time.perf_counter()
            execution_time = end_time - start_time
            
            # Pagination should be fast regardless of dataset size
            assert execution_time < 0.5, f"Table pagination took {execution_time:.3f}s, should be < 0.5s"
            assert len(result['data']) == page_size
            assert result['total_count'] == len(large_sample_data)
            
            print(f"Table widget (page_size={page_size}) execution time: {execution_time:.3f}s")

    def test_widget_caching_performance(self, large_sample_data: pd.DataFrame):
        """Test widget caching performance improvements"""
        executor = WidgetDataExecutor()
        cache = get_redis_cache()
        
        config = {
            "aggregation": "count",
            "field": "subject_id"
        }
        
        # Clear cache
        cache.clear()
        
        # First execution (cache miss)
        start_time = time.perf_counter()
        result1 = executor.metric_executor.execute(large_sample_data, config)
        first_execution_time = time.perf_counter() - start_time
        
        # Second execution (cache hit)
        start_time = time.perf_counter()
        result2 = executor.metric_executor.execute(large_sample_data, config)
        second_execution_time = time.perf_counter() - start_time
        
        # Cache hit should be significantly faster
        assert second_execution_time < first_execution_time * 0.1, "Cache hit should be 10x faster"
        assert result1 == result2, "Cached result should match original"
        
        print(f"Cache miss: {first_execution_time:.3f}s, Cache hit: {second_execution_time:.3f}s")
        print(f"Cache speedup: {first_execution_time / second_execution_time:.1f}x")

    def test_concurrent_widget_execution_performance(
        self, 
        large_sample_data: pd.DataFrame,
        performance_study: Study,
        metric_widget: WidgetDefinition
    ):
        """Test performance under concurrent widget execution load"""
        
        def execute_widget():
            executor = WidgetDataExecutor()
            request = WidgetDataRequest(
                widget_id=metric_widget.id,
                widget_config={
                    "data_source": "demographics",
                    "aggregation": "count",
                    "field": "subject_id"
                }
            )
            
            start_time = time.perf_counter()
            with unittest.mock.patch.object(executor, '_get_widget_data', return_value=large_sample_data):
                result = asyncio.run(executor.execute_widget(request, performance_study.id, db=None))
            execution_time = time.perf_counter() - start_time
            
            return execution_time, result
        
        # Test with different concurrency levels
        concurrency_levels = [1, 5, 10, 20, 50]
        
        for concurrency in concurrency_levels:
            start_time = time.perf_counter()
            
            with ThreadPoolExecutor(max_workers=concurrency) as executor:
                futures = [executor.submit(execute_widget) for _ in range(concurrency)]
                results = [future.result() for future in as_completed(futures)]
            
            total_time = time.perf_counter() - start_time
            execution_times = [result[0] for result in results]
            
            avg_execution_time = statistics.mean(execution_times)
            max_execution_time = max(execution_times)
            
            # Performance assertions
            assert avg_execution_time < 1.0, f"Average execution time {avg_execution_time:.3f}s too high"
            assert max_execution_time < 2.0, f"Max execution time {max_execution_time:.3f}s too high"
            
            print(f"Concurrency {concurrency}: avg={avg_execution_time:.3f}s, max={max_execution_time:.3f}s, total={total_time:.3f}s")

    def test_memory_usage_with_large_datasets(self, large_sample_data: pd.DataFrame):
        """Test memory usage patterns with large datasets"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        
        # Measure baseline memory
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        executor = WidgetDataExecutor()
        
        # Execute multiple operations
        configs = [
            {"aggregation": "count", "field": "subject_id"},
            {"aggregation": "avg", "field": "age"},
            {"aggregation": "sum", "field": "weight"},
            {"aggregation": "distinct", "field": "site"}
        ]
        
        for config in configs:
            result = executor.metric_executor.execute(large_sample_data, config)
            current_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = current_memory - baseline_memory
            
            # Memory usage should not grow excessively
            assert memory_increase < 500, f"Memory usage increased by {memory_increase:.1f}MB, should be < 500MB"
        
        print(f"Baseline memory: {baseline_memory:.1f}MB")
        print(f"Peak memory increase: {memory_increase:.1f}MB")

    def test_widget_execution_scalability(self):
        """Test widget execution scalability with increasing data sizes"""
        executor = WidgetDataExecutor()
        
        data_sizes = [1000, 10000, 50000, 100000, 500000]
        execution_times = []
        
        for size in data_sizes:
            # Generate data of specific size
            sample_data = pd.DataFrame({
                'subject_id': [f'S{i:06d}' for i in range(size)],
                'age': pd.np.random.randint(18, 80, size),
                'value': pd.np.random.normal(100, 20, size)
            })
            
            config = {"aggregation": "avg", "field": "age"}
            
            start_time = time.perf_counter()
            result = executor.metric_executor.execute(sample_data, config)
            execution_time = time.perf_counter() - start_time
            
            execution_times.append(execution_time)
            
            # Execution time should scale sub-linearly (better than O(n))
            if len(execution_times) > 1:
                size_ratio = size / data_sizes[len(execution_times) - 2]
                time_ratio = execution_time / execution_times[-2]
                
                # Time ratio should be less than size ratio (sub-linear scaling)
                assert time_ratio < size_ratio * 1.5, f"Poor scalability: {time_ratio:.2f}x time for {size_ratio:.2f}x data"
            
            print(f"Data size: {size:,} records, Execution time: {execution_time:.3f}s")

    def test_widget_data_filtering_performance(self, large_sample_data: pd.DataFrame):
        """Test performance of data filtering operations"""
        executor = WidgetDataExecutor()
        
        filter_scenarios = [
            {"gender": "M"},  # Simple equality filter
            {"age": {"operator": ">=", "value": 30}},  # Comparison filter
            {"site": {"operator": "in", "value": ["Site 001", "Site 002", "Site 003"]}},  # IN filter
            {"gender": "F", "age": {"operator": ">=", "value": 25}},  # Multiple filters
            {"enrollment_date": {"operator": ">=", "value": "2022-01-01"}},  # Date filter
        ]
        
        config = {"aggregation": "count", "field": "subject_id"}
        
        for filters in filter_scenarios:
            start_time = time.perf_counter()
            
            result = executor.metric_executor.execute(large_sample_data, config, filters)
            
            execution_time = time.perf_counter() - start_time
            
            # Filtering should not significantly impact performance
            assert execution_time < 0.5, f"Filtering took {execution_time:.3f}s, should be < 0.5s"
            assert result is not None
            
            print(f"Filter {filters}: {execution_time:.3f}s, result: {result.get('value', 0):,} records")

    def test_widget_aggregation_performance_comparison(self, large_sample_data: pd.DataFrame):
        """Compare performance of different aggregation methods"""
        executor = WidgetDataExecutor()
        
        # Test pandas native vs custom aggregations
        field = "age"
        
        # Pandas native aggregations
        pandas_results = {}
        for agg in ['count', 'sum', 'mean', 'min', 'max']:
            start_time = time.perf_counter()
            
            if agg == 'count':
                result = len(large_sample_data)
            else:
                result = getattr(large_sample_data[field], agg)()
            
            pandas_time = time.perf_counter() - start_time
            pandas_results[agg] = pandas_time
        
        # Widget executor aggregations
        executor_results = {}
        for agg in ['count', 'sum', 'avg', 'min', 'max']:
            config = {"aggregation": agg, "field": field if agg != 'count' else 'subject_id'}
            
            start_time = time.perf_counter()
            result = executor.metric_executor.execute(large_sample_data, config)
            executor_time = time.perf_counter() - start_time
            
            executor_results[agg] = executor_time
        
        # Widget executor should be competitive with pandas
        for agg in ['count', 'sum', 'min', 'max']:
            pandas_agg = agg if agg != 'avg' else 'mean'
            if pandas_agg in pandas_results:
                ratio = executor_results[agg] / pandas_results[pandas_agg]
                assert ratio < 5.0, f"Widget executor {agg} is {ratio:.1f}x slower than pandas"
        
        print("Pandas vs Widget Executor Performance:")
        for agg in executor_results:
            pandas_agg = agg if agg != 'avg' else 'mean'
            if pandas_agg in pandas_results:
                print(f"  {agg}: pandas={pandas_results[pandas_agg]:.4f}s, executor={executor_results[agg]:.4f}s")


@pytest.mark.performance
class TestWidgetRenderingPerformance:
    """Performance tests for widget rendering and UI updates"""
    
    def test_widget_component_render_time(self):
        """Test React component rendering performance"""
        # This would require a React testing environment
        # Placeholder for frontend performance testing
        pass
    
    def test_dashboard_layout_performance(self):
        """Test dashboard layout calculation performance"""
        # Test grid layout calculations with many widgets
        pass
    
    def test_real_time_update_performance(self):
        """Test performance of real-time widget updates"""
        # Test WebSocket update performance
        pass


@pytest.mark.performance
class TestWidgetDataAdapterPerformance:
    """Performance tests for different data adapter types"""
    
    def test_csv_adapter_performance(self):
        """Test CSV data adapter performance"""
        # Test reading large CSV files
        pass
    
    def test_parquet_adapter_performance(self):
        """Test Parquet data adapter performance"""
        # Test reading large Parquet files
        pass
    
    def test_postgres_adapter_performance(self):
        """Test PostgreSQL adapter performance"""
        # Test database query performance
        pass
    
    def test_adapter_performance_comparison(self):
        """Compare performance across different data adapters"""
        # Compare CSV vs Parquet vs Database performance
        pass


if __name__ == "__main__":
    # Run performance tests
    pytest.main([__file__, "-v", "-s", "--tb=short"])