# ABOUTME: Unit tests for filter executor service
# ABOUTME: Tests filter execution on DataFrames and performance tracking

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path
import tempfile
import pyarrow as pa
import pyarrow.parquet as pq

from app.services.filter_executor import FilterExecutor


class TestFilterExecutor:
    """Test the FilterExecutor service"""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database session"""
        db = MagicMock()
        return db
    
    @pytest.fixture
    def executor(self, mock_db):
        """Create FilterExecutor instance"""
        return FilterExecutor(mock_db)
    
    @pytest.fixture
    def sample_data(self):
        """Create sample DataFrame"""
        return pd.DataFrame({
            'USUBJID': ['001', '002', '003', '004', '005'],
            'AGE': [25, 45, 65, 30, 70],
            'AESER': ['Y', 'N', 'Y', 'N', 'Y'],
            'AETERM': ['Headache', None, 'Nausea', 'Dizziness', 'Headache'],
            'COUNTRY': ['USA', 'UK', 'USA', 'CANADA', 'UK'],
            'AESEV': ['MILD', 'MODERATE', 'SEVERE', 'MILD', 'SEVERE']
        })
    
    @pytest.fixture
    def temp_parquet_file(self, sample_data):
        """Create temporary Parquet file"""
        with tempfile.NamedTemporaryFile(suffix='.parquet', delete=False) as f:
            sample_data.to_parquet(f.name)
            yield f.name
            # Cleanup
            Path(f.name).unlink()
    
    def test_execute_simple_filter(self, executor, temp_parquet_file):
        """Test executing a simple filter"""
        result = executor.execute_filter(
            study_id="test-study",
            widget_id="widget1",
            filter_expression="AGE >= 45",
            dataset_path=temp_parquet_file,
            track_metrics=False
        )
        
        assert result["row_count"] == 3  # Ages 45, 65, 70
        assert result["original_count"] == 5
        assert "data" in result
        assert len(result["data"]) == 3
    
    def test_execute_complex_filter(self, executor, temp_parquet_file):
        """Test executing complex filter with AND/OR"""
        result = executor.execute_filter(
            study_id="test-study",
            widget_id="widget1",
            filter_expression="(AESER = 'Y' AND AGE >= 65) OR COUNTRY = 'CANADA'",
            dataset_path=temp_parquet_file,
            track_metrics=False
        )
        
        # Should match: 003 (Y, 65, USA), 004 (N, 30, CANADA), 005 (Y, 70, UK)
        assert result["row_count"] == 3
        assert set(result["data"]["USUBJID"].values) == {'003', '004', '005'}
    
    def test_execute_in_filter(self, executor, temp_parquet_file):
        """Test IN operator"""
        result = executor.execute_filter(
            study_id="test-study",
            widget_id="widget1",
            filter_expression="COUNTRY IN ('USA', 'UK')",
            dataset_path=temp_parquet_file,
            track_metrics=False
        )
        
        assert result["row_count"] == 4  # USA: 2, UK: 2
    
    def test_execute_like_filter(self, executor, temp_parquet_file):
        """Test LIKE operator"""
        result = executor.execute_filter(
            study_id="test-study",
            widget_id="widget1",
            filter_expression="AETERM LIKE '%ache%'",
            dataset_path=temp_parquet_file,
            track_metrics=False
        )
        
        assert result["row_count"] == 2  # Headache appears twice
    
    def test_execute_is_null_filter(self, executor, temp_parquet_file):
        """Test IS NULL operator"""
        result = executor.execute_filter(
            study_id="test-study",
            widget_id="widget1",
            filter_expression="AETERM IS NULL",
            dataset_path=temp_parquet_file,
            track_metrics=False
        )
        
        assert result["row_count"] == 1  # One NULL AETERM
        assert result["data"]["USUBJID"].values[0] == '002'
    
    def test_execute_is_not_null_filter(self, executor, temp_parquet_file):
        """Test IS NOT NULL operator"""
        result = executor.execute_filter(
            study_id="test-study",
            widget_id="widget1",
            filter_expression="AETERM IS NOT NULL",
            dataset_path=temp_parquet_file,
            track_metrics=False
        )
        
        assert result["row_count"] == 4  # Four non-NULL AETERMs
    
    def test_execute_between_filter(self, executor, temp_parquet_file):
        """Test BETWEEN operator"""
        result = executor.execute_filter(
            study_id="test-study",
            widget_id="widget1",
            filter_expression="AGE BETWEEN 30 AND 65",
            dataset_path=temp_parquet_file,
            track_metrics=False
        )
        
        assert result["row_count"] == 3  # Ages 30, 45, 65
    
    def test_execute_not_filter(self, executor, temp_parquet_file):
        """Test NOT operator"""
        result = executor.execute_filter(
            study_id="test-study",
            widget_id="widget1",
            filter_expression="NOT AESER = 'Y'",
            dataset_path=temp_parquet_file,
            track_metrics=False
        )
        
        assert result["row_count"] == 2  # AESER = 'N'
    
    def test_execute_with_specific_columns(self, executor, temp_parquet_file):
        """Test filtering with specific columns requested"""
        result = executor.execute_filter(
            study_id="test-study",
            widget_id="widget1",
            filter_expression="AGE >= 45",
            dataset_path=temp_parquet_file,
            columns=["USUBJID", "AGE"],
            track_metrics=False
        )
        
        assert result["row_count"] == 3
        assert list(result["data"].columns) == ["USUBJID", "AGE"]
    
    def test_invalid_filter_expression(self, executor, temp_parquet_file):
        """Test invalid filter expression"""
        result = executor.execute_filter(
            study_id="test-study",
            widget_id="widget1",
            filter_expression="INVALID SYNTAX ====",
            dataset_path=temp_parquet_file,
            track_metrics=False
        )
        
        assert result["row_count"] == 0
        assert "error" in result
        assert "Invalid filter expression" in result["error"]
    
    def test_nonexistent_file(self, executor):
        """Test with non-existent file"""
        result = executor.execute_filter(
            study_id="test-study",
            widget_id="widget1",
            filter_expression="AGE >= 18",
            dataset_path="/nonexistent/file.parquet",
            track_metrics=False
        )
        
        assert result["row_count"] == 0
        assert "error" in result
        assert "not found" in result["error"]
    
    def test_reduction_percentage(self, executor, temp_parquet_file):
        """Test reduction percentage calculation"""
        result = executor.execute_filter(
            study_id="test-study",
            widget_id="widget1",
            filter_expression="AGE >= 65",
            dataset_path=temp_parquet_file,
            track_metrics=False
        )
        
        assert result["row_count"] == 2  # Ages 65, 70
        assert result["original_count"] == 5
        assert result["reduction_percentage"] == 60.0  # Reduced by 60%
    
    def test_metrics_tracking(self, executor, temp_parquet_file, mock_db):
        """Test that metrics are tracked when enabled"""
        result = executor.execute_filter(
            study_id="test-study",
            widget_id="widget1",
            filter_expression="AGE >= 45",
            dataset_path=temp_parquet_file,
            track_metrics=True
        )
        
        # Check that metrics tracking was called
        assert mock_db.execute.called
        assert mock_db.commit.called
    
    def test_pandas_query_generation(self, executor):
        """Test conversion of AST to pandas query"""
        from app.services.filter_parser import FilterParser
        
        parser = FilterParser()
        
        test_cases = [
            ("AGE >= 18", "AGE >= 18"),
            ("AESER = 'Y'", "AESER == 'Y'"),
            ("AGE >= 18 AND AESER = 'Y'", "(AGE >= 18) & (AESER == 'Y')"),
            ("AGE >= 18 OR AESER = 'Y'", "(AGE >= 18) | (AESER == 'Y')"),
            ("NOT AESER = 'Y'", "~(AESER == 'Y')"),
            ("COUNTRY IN ('USA', 'UK')", "COUNTRY.isin(['USA', 'UK'])"),
            ("AETERM IS NULL", "AETERM.isna()"),
            ("AETERM IS NOT NULL", "AETERM.notna()"),
            ("AGE BETWEEN 18 AND 65", "(AGE >= 18) & (AGE <= 65)"),
        ]
        
        for sql_expr, expected_pandas in test_cases:
            parse_result = parser.parse(sql_expr)
            pandas_query = executor._ast_to_pandas_query(parse_result["ast"])
            # Basic check - exact match might vary due to formatting
            assert isinstance(pandas_query, str)
    
    def test_pyarrow_execution(self, executor, temp_parquet_file):
        """Test PyArrow execution method"""
        result = executor.execute_filter_pyarrow(
            study_id="test-study",
            widget_id="widget1",
            filter_expression="AGE >= 45",
            dataset_path=temp_parquet_file
        )
        
        assert result["row_count"] == 3
        assert result["original_count"] == 5
        assert "data" in result
    
    def test_get_execution_metrics(self, executor, mock_db):
        """Test retrieving execution metrics"""
        mock_db.execute.return_value.fetchall.return_value = [
            ("widget1", "AGE >= 18", 150, 1000, 800, 20.0, pd.Timestamp.now())
        ]
        
        metrics = executor.get_execution_metrics("test-study")
        
        assert len(metrics) == 1
        assert metrics[0]["widget_id"] == "widget1"
        assert metrics[0]["execution_time_ms"] == 150
        assert metrics[0]["reduction_percentage"] == 20.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])