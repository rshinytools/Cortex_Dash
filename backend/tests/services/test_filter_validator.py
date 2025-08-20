# ABOUTME: Unit tests for filter validation service  
# ABOUTME: Tests schema validation, type checking, and caching

import pytest
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from datetime import datetime

from app.services.filter_validator import FilterValidator
from app.models import Study, User


class TestFilterValidator:
    """Test the FilterValidator service"""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database session"""
        db = MagicMock()
        return db
    
    @pytest.fixture
    def mock_study(self):
        """Create mock study"""
        study = Mock(spec=Study)
        study.id = "test-study-id"
        study.organization_id = "test-org-id"
        study.field_mappings = {"widget1": "dm.USUBJID"}
        return study
    
    @pytest.fixture
    def mock_user(self):
        """Create mock user"""
        user = Mock(spec=User)
        user.id = "test-user-id"
        return user
    
    @pytest.fixture
    def validator(self, mock_db):
        """Create FilterValidator instance"""
        return FilterValidator(mock_db)
    
    def test_validate_simple_filter(self, validator, mock_db, mock_study):
        """Test validating a simple filter"""
        # Setup mock database
        mock_db.query.return_value.filter.return_value.first.return_value = mock_study
        
        # Mock dataset schema
        with patch.object(validator, '_get_dataset_schema') as mock_schema:
            mock_schema.return_value = {
                "dataset": "dm",
                "columns": {
                    "USUBJID": {"type": "string", "nullable": False},
                    "AGE": {"type": "integer", "nullable": True}
                },
                "row_count": 1000
            }
            
            # Validate filter
            result = validator.validate_filter(
                study_id="test-study-id",
                widget_id="widget1",
                filter_expression="AGE >= 18",
                dataset_name="dm"
            )
            
            assert result["is_valid"] is True
            assert len(result["errors"]) == 0
            assert "AGE" in [col["name"] for col in result["validated_columns"]]
    
    def test_validate_invalid_column(self, validator, mock_db, mock_study):
        """Test validation with invalid column"""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_study
        
        with patch.object(validator, '_get_dataset_schema') as mock_schema:
            mock_schema.return_value = {
                "dataset": "dm",
                "columns": {
                    "USUBJID": {"type": "string", "nullable": False}
                },
                "row_count": 1000
            }
            
            result = validator.validate_filter(
                study_id="test-study-id",
                widget_id="widget1",
                filter_expression="INVALID_COL = 'value'",
                dataset_name="dm"
            )
            
            assert result["is_valid"] is False
            assert any("INVALID_COL" in error for error in result["errors"])
    
    def test_validate_type_mismatch_warning(self, validator, mock_db, mock_study):
        """Test type mismatch warning"""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_study
        
        with patch.object(validator, '_get_dataset_schema') as mock_schema:
            mock_schema.return_value = {
                "dataset": "dm",
                "columns": {
                    "AGE": {"type": "integer", "nullable": True}
                },
                "row_count": 1000
            }
            
            result = validator.validate_filter(
                study_id="test-study-id",
                widget_id="widget1",
                filter_expression="AGE = 'eighteen'",
                dataset_name="dm"
            )
            
            # Should be valid but with warning
            assert result["is_valid"] is True
            assert any("Type mismatch" in warning for warning in result["warnings"])
    
    def test_validate_between_bounds(self, validator, mock_db, mock_study):
        """Test BETWEEN validation with incorrect bounds"""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_study
        
        with patch.object(validator, '_get_dataset_schema') as mock_schema:
            mock_schema.return_value = {
                "dataset": "dm",
                "columns": {
                    "AGE": {"type": "integer", "nullable": True}
                },
                "row_count": 1000
            }
            
            result = validator.validate_filter(
                study_id="test-study-id",
                widget_id="widget1",
                filter_expression="AGE BETWEEN 65 AND 18",  # Wrong order
                dataset_name="dm"
            )
            
            assert result["is_valid"] is False
            assert any("lower bound" in error and "greater than" in error for error in result["errors"])
    
    def test_validate_like_on_non_string(self, validator, mock_db, mock_study):
        """Test LIKE operator on non-string column"""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_study
        
        with patch.object(validator, '_get_dataset_schema') as mock_schema:
            mock_schema.return_value = {
                "dataset": "dm",
                "columns": {
                    "AGE": {"type": "integer", "nullable": True}
                },
                "row_count": 1000
            }
            
            result = validator.validate_filter(
                study_id="test-study-id",
                widget_id="widget1",
                filter_expression="AGE LIKE '1%'",
                dataset_name="dm"
            )
            
            assert result["is_valid"] is True  # Valid but with warning
            assert any("LIKE operator used on non-string" in warning for warning in result["warnings"])
    
    def test_validate_complex_filter(self, validator, mock_db, mock_study):
        """Test complex filter validation"""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_study
        
        with patch.object(validator, '_get_dataset_schema') as mock_schema:
            mock_schema.return_value = {
                "dataset": "ae",
                "columns": {
                    "AESER": {"type": "string", "nullable": True},
                    "AETERM": {"type": "string", "nullable": True},
                    "AESIDAT": {"type": "date", "nullable": True},
                    "AESEV": {"type": "string", "nullable": True}
                },
                "row_count": 5000
            }
            
            result = validator.validate_filter(
                study_id="test-study-id",
                widget_id="widget1",
                filter_expression="(AESER = 'Y' AND AETERM IS NOT NULL) OR (AESEV IN ('SEVERE', 'LIFE THREATENING'))",
                dataset_name="ae"
            )
            
            assert result["is_valid"] is True
            assert len(result["validated_columns"]) == 3  # AESER, AETERM, AESEV
            assert result["complexity"] > 5
    
    def test_performance_warning(self, validator, mock_db, mock_study):
        """Test performance warning for many columns"""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_study
        
        columns = {f"COL{i}": {"type": "string", "nullable": True} for i in range(10)}
        
        with patch.object(validator, '_get_dataset_schema') as mock_schema:
            mock_schema.return_value = {
                "dataset": "test",
                "columns": columns,
                "row_count": 10000
            }
            
            # Create filter with many columns
            filter_expr = " AND ".join([f"COL{i} = 'value'" for i in range(6)])
            
            result = validator.validate_filter(
                study_id="test-study-id",
                widget_id="widget1",
                filter_expression=filter_expr,
                dataset_name="test"
            )
            
            assert result["is_valid"] is True
            assert any("may impact performance" in warning for warning in result["warnings"])
    
    def test_wildcard_like_warning(self, validator, mock_db, mock_study):
        """Test warning for LIKE pattern starting with %"""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_study
        
        with patch.object(validator, '_get_dataset_schema') as mock_schema:
            mock_schema.return_value = {
                "dataset": "ae",
                "columns": {
                    "AETERM": {"type": "string", "nullable": True}
                },
                "row_count": 5000
            }
            
            result = validator.validate_filter(
                study_id="test-study-id",
                widget_id="widget1",
                filter_expression="AETERM LIKE '%headache'",
                dataset_name="ae"
            )
            
            assert result["is_valid"] is True
            assert any("starting with '%' may be slow" in warning for warning in result["warnings"])
    
    @patch('app.services.filter_validator.Path')
    @patch('app.services.filter_validator.pq.ParquetFile')
    def test_get_dataset_schema(self, mock_pq, mock_path, validator, mock_study):
        """Test getting dataset schema from parquet file"""
        # Setup mock paths
        mock_base = MagicMock()
        mock_base.exists.return_value = True
        mock_version_dir = MagicMock()
        mock_version_dir.name = "20240120"
        mock_version_dir.is_dir.return_value = True
        mock_base.iterdir.return_value = [mock_version_dir]
        
        mock_dataset_path = MagicMock()
        mock_dataset_path.exists.return_value = True
        mock_dataset_path.stat.return_value.st_size = 1024000
        
        mock_path.return_value = mock_base
        mock_version_dir.__truediv__ = lambda self, other: mock_dataset_path
        
        # Setup mock parquet schema
        mock_field1 = MagicMock()
        mock_field1.name = "USUBJID"
        mock_field1.type = pa.string()
        mock_field1.nullable = False
        
        mock_field2 = MagicMock()
        mock_field2.name = "AGE"
        mock_field2.type = pa.int64()
        mock_field2.nullable = True
        
        mock_schema = MagicMock()
        mock_schema.__iter__ = lambda self: iter([mock_field1, mock_field2])
        
        mock_parquet = MagicMock()
        mock_parquet.schema = mock_schema
        mock_pq.return_value = mock_parquet
        
        # Mock pandas read
        with patch('app.services.filter_validator.pd.read_parquet') as mock_read:
            mock_df = pd.DataFrame({"USUBJID": ["001", "002"]})
            mock_read.return_value = mock_df
            
            schema = validator._get_dataset_schema(mock_study, "dm")
            
            assert schema is not None
            assert schema["dataset"] == "dm"
            assert "USUBJID" in schema["columns"]
            assert "AGE" in schema["columns"]
            assert schema["row_count"] == 2
    
    def test_cache_validation_result(self, validator, mock_db):
        """Test caching validation results"""
        validator._cache_validation_result(
            study_id="test-study-id",
            widget_id="widget1",
            filter_expression="AGE >= 18",
            dataset_name="dm",
            is_valid=True,
            errors=[],
            validated_columns=[{"name": "AGE", "type": "integer"}]
        )
        
        # Check that execute was called with correct query
        assert mock_db.execute.called
        assert mock_db.commit.called
    
    def test_get_cached_validation(self, validator, mock_db):
        """Test retrieving cached validation"""
        mock_result = [
            "AGE >= 18",  # filter_expression
            "dm",  # dataset_name
            True,  # is_valid
            None,  # validation_errors
            '[{"name": "AGE", "type": "integer"}]',  # validated_columns
            datetime.now()  # last_validated
        ]
        
        mock_db.execute.return_value.first.return_value = mock_result
        
        cached = validator.get_cached_validation("test-study-id", "widget1")
        
        assert cached is not None
        assert cached["filter_expression"] == "AGE >= 18"
        assert cached["is_valid"] is True
        assert len(cached["validated_columns"]) == 1
    
    def test_audit_logging(self, validator, mock_db, mock_user):
        """Test audit logging"""
        mock_db.query.return_value.filter.return_value.first.return_value = Mock(
            id="test-study-id",
            organization_id="test-org-id"
        )
        
        with patch.object(validator, '_get_dataset_schema') as mock_schema:
            mock_schema.return_value = {
                "dataset": "dm",
                "columns": {"AGE": {"type": "integer"}},
                "row_count": 1000
            }
            
            validator.validate_filter(
                study_id="test-study-id",
                widget_id="widget1",
                filter_expression="AGE >= 18",
                dataset_name="dm",
                user=mock_user
            )
            
            # Check that audit log was created
            calls = mock_db.execute.call_args_list
            audit_call = next((c for c in calls if "filter_audit_log" in str(c)), None)
            assert audit_call is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])