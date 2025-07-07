# ABOUTME: Comprehensive test suite for data adapter functionality
# ABOUTME: Tests all data source adapters including CSV, Parquet, SAS, and PostgreSQL

import pytest
import uuid
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd
import numpy as np

from app.services.data_adapters.base import BaseDataAdapter, DataAdapterError
from app.services.data_adapters.csv_adapter import CSVDataAdapter
from app.services.data_adapters.parquet_adapter import ParquetDataAdapter
from app.services.data_adapters.sas_adapter import SASDataAdapter
from app.services.data_adapters.postgres_adapter import PostgreSQLDataAdapter


class TestBaseDataAdapter:
    """Test suite for BaseDataAdapter abstract class"""

    def test_base_adapter_abstract_methods(self):
        """Test that BaseDataAdapter cannot be instantiated directly"""
        with pytest.raises(TypeError):
            BaseDataAdapter()

    def test_adapter_interface_methods(self):
        """Test that adapter interface methods are properly defined"""
        # All adapters should implement these methods
        required_methods = [
            'connect', 'disconnect', 'get_schema', 'query_data',
            'validate_connection', 'get_table_list', 'get_column_info'
        ]
        
        for method in required_methods:
            assert hasattr(BaseDataAdapter, method)


class TestCSVDataAdapter:
    """Test suite for CSVDataAdapter"""

    @pytest.fixture
    def csv_adapter(self) -> CSVDataAdapter:
        """Create CSVDataAdapter instance for testing"""
        return CSVDataAdapter()

    @pytest.fixture
    def sample_csv_file(self) -> str:
        """Create a sample CSV file for testing"""
        data = {
            'subject_id': ['S001', 'S002', 'S003', 'S004', 'S005'],
            'age': [25, 30, 35, 40, 45],
            'gender': ['M', 'F', 'M', 'F', 'M'],
            'visit_date': ['2024-01-01', '2024-01-02', '2024-01-03', '2024-01-04', '2024-01-05'],
            'lab_value': [10.5, 12.3, 9.8, 11.2, 13.1]
        }
        df = pd.DataFrame(data)
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        df.to_csv(temp_file.name, index=False)
        temp_file.close()
        
        yield temp_file.name
        
        # Cleanup
        os.unlink(temp_file.name)

    @pytest.fixture
    def malformed_csv_file(self) -> str:
        """Create a malformed CSV file for testing"""
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        temp_file.write("subject_id,age,gender\n")
        temp_file.write("S001,25,M\n")
        temp_file.write("S002,invalid_age,F\n")  # Invalid age
        temp_file.write("S003,35\n")  # Missing gender
        temp_file.close()
        
        yield temp_file.name
        
        # Cleanup
        os.unlink(temp_file.name)

    def test_csv_adapter_initialization(self, csv_adapter):
        """Test CSV adapter initialization"""
        assert csv_adapter is not None
        assert csv_adapter.adapter_type == "csv"

    def test_csv_connect_success(self, csv_adapter, sample_csv_file):
        """Test successful CSV file connection"""
        connection_params = {"file_path": sample_csv_file}
        
        result = csv_adapter.connect(connection_params)
        
        assert result is True
        assert csv_adapter.is_connected is True

    def test_csv_connect_file_not_found(self, csv_adapter):
        """Test CSV connection with non-existent file"""
        connection_params = {"file_path": "/nonexistent/file.csv"}
        
        with pytest.raises(DataAdapterError, match="File not found"):
            csv_adapter.connect(connection_params)

    def test_csv_get_schema(self, csv_adapter, sample_csv_file):
        """Test CSV schema extraction"""
        csv_adapter.connect({"file_path": sample_csv_file})
        
        schema = csv_adapter.get_schema()
        
        assert 'subject_id' in schema['columns']
        assert 'age' in schema['columns']
        assert 'gender' in schema['columns']
        assert schema['row_count'] == 5

    def test_csv_query_data_all(self, csv_adapter, sample_csv_file):
        """Test querying all data from CSV"""
        csv_adapter.connect({"file_path": sample_csv_file})
        
        data = csv_adapter.query_data()
        
        assert isinstance(data, pd.DataFrame)
        assert len(data) == 5
        assert list(data.columns) == ['subject_id', 'age', 'gender', 'visit_date', 'lab_value']

    def test_csv_query_data_with_filters(self, csv_adapter, sample_csv_file):
        """Test querying CSV data with filters"""
        csv_adapter.connect({"file_path": sample_csv_file})
        
        filters = {"gender": "M"}
        data = csv_adapter.query_data(filters=filters)
        
        assert len(data) == 3  # Only male subjects
        assert all(data['gender'] == 'M')

    def test_csv_query_data_with_columns(self, csv_adapter, sample_csv_file):
        """Test querying specific columns from CSV"""
        csv_adapter.connect({"file_path": sample_csv_file})
        
        columns = ['subject_id', 'age']
        data = csv_adapter.query_data(columns=columns)
        
        assert list(data.columns) == columns
        assert len(data) == 5

    def test_csv_query_data_with_limit(self, csv_adapter, sample_csv_file):
        """Test querying CSV data with row limit"""
        csv_adapter.connect({"file_path": sample_csv_file})
        
        data = csv_adapter.query_data(limit=3)
        
        assert len(data) == 3

    def test_csv_validate_connection(self, csv_adapter, sample_csv_file):
        """Test CSV connection validation"""
        csv_adapter.connect({"file_path": sample_csv_file})
        
        is_valid = csv_adapter.validate_connection()
        
        assert is_valid is True

    def test_csv_handle_malformed_data(self, csv_adapter, malformed_csv_file):
        """Test handling of malformed CSV data"""
        csv_adapter.connect({"file_path": malformed_csv_file})
        
        # Should handle malformed data gracefully
        data = csv_adapter.query_data(handle_errors='coerce')
        
        assert len(data) >= 2  # Should read valid rows
        # Invalid age should be NaN
        assert pd.isna(data.loc[data['subject_id'] == 'S002', 'age'].iloc[0])

    def test_csv_get_column_info(self, csv_adapter, sample_csv_file):
        """Test getting detailed column information"""
        csv_adapter.connect({"file_path": sample_csv_file})
        
        column_info = csv_adapter.get_column_info()
        
        assert 'subject_id' in column_info
        assert column_info['subject_id']['dtype'] == 'object'
        assert column_info['age']['dtype'] in ['int64', 'float64']


class TestParquetDataAdapter:
    """Test suite for ParquetDataAdapter"""

    @pytest.fixture
    def parquet_adapter(self) -> ParquetDataAdapter:
        """Create ParquetDataAdapter instance for testing"""
        return ParquetDataAdapter()

    @pytest.fixture
    def sample_parquet_file(self) -> str:
        """Create a sample Parquet file for testing"""
        data = {
            'subject_id': ['S001', 'S002', 'S003', 'S004', 'S005'],
            'age': [25, 30, 35, 40, 45],
            'gender': ['M', 'F', 'M', 'F', 'M'],
            'visit_date': pd.date_range('2024-01-01', periods=5),
            'lab_value': [10.5, 12.3, 9.8, 11.2, 13.1],
            'is_active': [True, True, False, True, False]
        }
        df = pd.DataFrame(data)
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(suffix='.parquet', delete=False)
        df.to_parquet(temp_file.name, index=False)
        temp_file.close()
        
        yield temp_file.name
        
        # Cleanup
        os.unlink(temp_file.name)

    def test_parquet_adapter_initialization(self, parquet_adapter):
        """Test Parquet adapter initialization"""
        assert parquet_adapter is not None
        assert parquet_adapter.adapter_type == "parquet"

    def test_parquet_connect_success(self, parquet_adapter, sample_parquet_file):
        """Test successful Parquet file connection"""
        connection_params = {"file_path": sample_parquet_file}
        
        result = parquet_adapter.connect(connection_params)
        
        assert result is True
        assert parquet_adapter.is_connected is True

    def test_parquet_get_schema(self, parquet_adapter, sample_parquet_file):
        """Test Parquet schema extraction"""
        parquet_adapter.connect({"file_path": sample_parquet_file})
        
        schema = parquet_adapter.get_schema()
        
        assert 'subject_id' in schema['columns']
        assert 'visit_date' in schema['columns']
        assert schema['row_count'] == 5
        
        # Check data types
        assert schema['columns']['age']['dtype'] in ['int64', 'Int64']
        assert 'datetime' in str(schema['columns']['visit_date']['dtype']).lower()

    def test_parquet_query_data_with_complex_filters(self, parquet_adapter, sample_parquet_file):
        """Test Parquet querying with complex filters"""
        parquet_adapter.connect({"file_path": sample_parquet_file})
        
        filters = {
            "age": {"operator": ">=", "value": 30},
            "gender": "M"
        }
        data = parquet_adapter.query_data(filters=filters)
        
        assert len(data) == 2  # Male subjects >= 30 years old
        assert all(data['age'] >= 30)
        assert all(data['gender'] == 'M')

    def test_parquet_efficient_column_selection(self, parquet_adapter, sample_parquet_file):
        """Test efficient column selection (Parquet's columnar advantage)"""
        parquet_adapter.connect({"file_path": sample_parquet_file})
        
        # Should only read specified columns
        columns = ['subject_id', 'age']
        data = parquet_adapter.query_data(columns=columns)
        
        assert list(data.columns) == columns
        assert len(data) == 5

    def test_parquet_date_filtering(self, parquet_adapter, sample_parquet_file):
        """Test date-based filtering with Parquet"""
        parquet_adapter.connect({"file_path": sample_parquet_file})
        
        filters = {
            "visit_date": {
                "operator": ">=", 
                "value": "2024-01-03"
            }
        }
        data = parquet_adapter.query_data(filters=filters)
        
        assert len(data) == 3  # Last 3 visits


class TestSASDataAdapter:
    """Test suite for SASDataAdapter"""

    @pytest.fixture
    def sas_adapter(self) -> SASDataAdapter:
        """Create SASDataAdapter instance for testing"""
        return SASDataAdapter()

    @pytest.fixture
    def mock_sas_file(self):
        """Mock SAS file for testing"""
        # Since we don't have actual SAS files, we'll mock the pyreadstat library
        mock_data = pd.DataFrame({
            'USUBJID': ['STUDY-001', 'STUDY-002', 'STUDY-003'],
            'VISITNUM': [1, 2, 1],
            'VISITDT': pd.date_range('2024-01-01', periods=3),
            'AGE': [25, 30, 35],
            'SEX': ['M', 'F', 'M']
        })
        return mock_data

    def test_sas_adapter_initialization(self, sas_adapter):
        """Test SAS adapter initialization"""
        assert sas_adapter is not None
        assert sas_adapter.adapter_type == "sas"

    @patch('app.services.data_adapters.sas_adapter.pyreadstat')
    def test_sas_connect_success(self, mock_pyreadstat, sas_adapter, mock_sas_file):
        """Test successful SAS file connection"""
        mock_pyreadstat.read_sas7bdat.return_value = (mock_sas_file, {})
        
        connection_params = {"file_path": "/path/to/file.sas7bdat"}
        result = sas_adapter.connect(connection_params)
        
        assert result is True
        assert sas_adapter.is_connected is True

    @patch('app.services.data_adapters.sas_adapter.pyreadstat')
    def test_sas_get_schema(self, mock_pyreadstat, sas_adapter, mock_sas_file):
        """Test SAS schema extraction"""
        mock_pyreadstat.read_sas7bdat.return_value = (mock_sas_file, {
            'column_labels': {'USUBJID': 'Unique Subject ID', 'AGE': 'Age in Years'},
            'variable_value_labels': {'SEX': {1: 'Male', 2: 'Female'}}
        })
        
        sas_adapter.connect({"file_path": "/path/to/file.sas7bdat"})
        schema = sas_adapter.get_schema()
        
        assert 'USUBJID' in schema['columns']
        assert schema['columns']['USUBJID']['label'] == 'Unique Subject ID'
        assert 'value_labels' in schema
        assert schema['row_count'] == 3

    @patch('app.services.data_adapters.sas_adapter.pyreadstat')
    def test_sas_query_data_with_cdisc_compliance(self, mock_pyreadstat, sas_adapter, mock_sas_file):
        """Test SAS data querying with CDISC compliance features"""
        mock_pyreadstat.read_sas7bdat.return_value = (mock_sas_file, {})
        
        sas_adapter.connect({"file_path": "/path/to/file.sas7bdat"})
        data = sas_adapter.query_data(cdisc_compliant=True)
        
        # Should maintain CDISC variable naming conventions
        assert 'USUBJID' in data.columns
        assert 'VISITNUM' in data.columns
        assert len(data) == 3

    @patch('app.services.data_adapters.sas_adapter.pyreadstat')
    def test_sas_handle_formats_and_labels(self, mock_pyreadstat, sas_adapter, mock_sas_file):
        """Test handling of SAS formats and labels"""
        metadata = {
            'column_labels': {'USUBJID': 'Unique Subject ID'},
            'variable_value_labels': {'SEX': {1: 'Male', 2: 'Female'}},
            'variable_format': {'VISITDT': 'DATE9.'}
        }
        mock_pyreadstat.read_sas7bdat.return_value = (mock_sas_file, metadata)
        
        sas_adapter.connect({"file_path": "/path/to/file.sas7bdat"})
        
        # Test getting formatted data
        data = sas_adapter.query_data(apply_formats=True)
        column_info = sas_adapter.get_column_info()
        
        assert column_info['USUBJID']['label'] == 'Unique Subject ID'
        assert 'value_labels' in column_info['SEX']


class TestPostgreSQLDataAdapter:
    """Test suite for PostgreSQLDataAdapter"""

    @pytest.fixture
    def postgres_adapter(self) -> PostgreSQLDataAdapter:
        """Create PostgreSQLDataAdapter instance for testing"""
        return PostgreSQLDataAdapter()

    @pytest.fixture
    def mock_postgres_connection(self):
        """Mock PostgreSQL connection for testing"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        return mock_conn, mock_cursor

    def test_postgres_adapter_initialization(self, postgres_adapter):
        """Test PostgreSQL adapter initialization"""
        assert postgres_adapter is not None
        assert postgres_adapter.adapter_type == "postgresql"

    @patch('app.services.data_adapters.postgres_adapter.psycopg2')
    def test_postgres_connect_success(self, mock_psycopg2, postgres_adapter):
        """Test successful PostgreSQL connection"""
        mock_conn = MagicMock()
        mock_psycopg2.connect.return_value = mock_conn
        
        connection_params = {
            "host": "localhost",
            "port": 5432,
            "database": "test_db",
            "username": "test_user",
            "password": "test_pass"
        }
        
        result = postgres_adapter.connect(connection_params)
        
        assert result is True
        assert postgres_adapter.is_connected is True
        mock_psycopg2.connect.assert_called_once()

    @patch('app.services.data_adapters.postgres_adapter.psycopg2')
    def test_postgres_connect_failure(self, mock_psycopg2, postgres_adapter):
        """Test PostgreSQL connection failure"""
        mock_psycopg2.connect.side_effect = Exception("Connection failed")
        
        connection_params = {
            "host": "invalid_host",
            "database": "test_db",
            "username": "test_user",
            "password": "test_pass"
        }
        
        with pytest.raises(DataAdapterError, match="Connection failed"):
            postgres_adapter.connect(connection_params)

    @patch('app.services.data_adapters.postgres_adapter.psycopg2')
    def test_postgres_get_table_list(self, mock_psycopg2, postgres_adapter):
        """Test getting list of tables from PostgreSQL"""
        mock_conn, mock_cursor = MagicMock(), MagicMock()
        mock_psycopg2.connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Mock table list query result
        mock_cursor.fetchall.return_value = [
            ('demographics',), ('adverse_events',), ('laboratory',)
        ]
        
        postgres_adapter.connect({"host": "localhost", "database": "test_db"})
        tables = postgres_adapter.get_table_list()
        
        assert 'demographics' in tables
        assert 'adverse_events' in tables
        assert 'laboratory' in tables

    @patch('app.services.data_adapters.postgres_adapter.pd.read_sql')
    @patch('app.services.data_adapters.postgres_adapter.psycopg2')
    def test_postgres_query_data_with_sql(self, mock_psycopg2, mock_read_sql, postgres_adapter):
        """Test PostgreSQL data querying with custom SQL"""
        mock_conn = MagicMock()
        mock_psycopg2.connect.return_value = mock_conn
        
        sample_data = pd.DataFrame({
            'subject_id': ['S001', 'S002'],
            'age': [25, 30]
        })
        mock_read_sql.return_value = sample_data
        
        postgres_adapter.connect({"host": "localhost", "database": "test_db"})
        
        sql_query = "SELECT subject_id, age FROM demographics WHERE age > 18"
        data = postgres_adapter.query_data(sql=sql_query)
        
        assert len(data) == 2
        mock_read_sql.assert_called_once()

    @patch('app.services.data_adapters.postgres_adapter.psycopg2')
    def test_postgres_get_schema_info(self, mock_psycopg2, postgres_adapter):
        """Test getting detailed schema information from PostgreSQL"""
        mock_conn, mock_cursor = MagicMock(), MagicMock()
        mock_psycopg2.connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Mock schema query result
        mock_cursor.fetchall.return_value = [
            ('subject_id', 'character varying', 'NO', None),
            ('age', 'integer', 'YES', '0'),
            ('visit_date', 'date', 'YES', None)
        ]
        
        postgres_adapter.connect({"host": "localhost", "database": "test_db"})
        schema = postgres_adapter.get_schema("demographics")
        
        assert 'subject_id' in schema['columns']
        assert schema['columns']['subject_id']['data_type'] == 'character varying'
        assert schema['columns']['subject_id']['is_nullable'] == 'NO'

    @patch('app.services.data_adapters.postgres_adapter.psycopg2')
    def test_postgres_transaction_handling(self, mock_psycopg2, postgres_adapter):
        """Test PostgreSQL transaction handling"""
        mock_conn, mock_cursor = MagicMock(), MagicMock()
        mock_psycopg2.connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        postgres_adapter.connect({"host": "localhost", "database": "test_db"})
        
        # Test transaction methods
        postgres_adapter.begin_transaction()
        postgres_adapter.commit_transaction()
        postgres_adapter.rollback_transaction()
        
        mock_conn.cursor.assert_called()


class TestDataAdapterFactory:
    """Test suite for Data Adapter Factory"""

    def test_create_csv_adapter(self):
        """Test factory creation of CSV adapter"""
        from app.services.data_adapters import create_adapter
        
        adapter = create_adapter("csv")
        assert isinstance(adapter, CSVDataAdapter)

    def test_create_parquet_adapter(self):
        """Test factory creation of Parquet adapter"""
        from app.services.data_adapters import create_adapter
        
        adapter = create_adapter("parquet")
        assert isinstance(adapter, ParquetDataAdapter)

    def test_create_sas_adapter(self):
        """Test factory creation of SAS adapter"""
        from app.services.data_adapters import create_adapter
        
        adapter = create_adapter("sas")
        assert isinstance(adapter, SASDataAdapter)

    def test_create_postgres_adapter(self):
        """Test factory creation of PostgreSQL adapter"""
        from app.services.data_adapters import create_adapter
        
        adapter = create_adapter("postgresql")
        assert isinstance(adapter, PostgreSQLDataAdapter)

    def test_create_invalid_adapter(self):
        """Test factory with invalid adapter type"""
        from app.services.data_adapters import create_adapter
        
        with pytest.raises(ValueError, match="Unsupported adapter type"):
            create_adapter("invalid_type")


@pytest.mark.integration
class TestDataAdapterIntegration:
    """Integration tests for data adapters"""

    async def test_adapter_performance_comparison(self):
        """Test performance comparison between different adapters"""
        # Create same dataset in different formats and compare query performance
        pass

    async def test_cross_adapter_data_consistency(self):
        """Test data consistency across different adapter types"""
        # Ensure same data queried through different adapters yields same results
        pass

    async def test_adapter_caching_behavior(self):
        """Test caching behavior across different adapters"""
        # Test that caching works correctly for each adapter type
        pass


@pytest.mark.performance
class TestDataAdapterPerformance:
    """Performance tests for data adapters"""

    def test_large_csv_performance(self):
        """Test CSV adapter performance with large files"""
        # Test performance with large CSV files
        pass

    def test_parquet_columnar_performance(self):
        """Test Parquet adapter's columnar performance advantage"""
        # Test performance benefits of columnar storage
        pass

    def test_postgres_query_optimization(self):
        """Test PostgreSQL adapter query optimization"""
        # Test query performance and optimization
        pass

    def test_concurrent_adapter_access(self):
        """Test concurrent access to adapters"""
        # Test thread safety and concurrent access patterns
        pass