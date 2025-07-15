# ABOUTME: Unit tests for FileConversionService
# ABOUTME: Tests file conversion from various formats to Parquet

import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import pandas as pd
import numpy as np
from pathlib import Path
from app.services.file_conversion_service import FileConversionService


@pytest.fixture
def service():
    return FileConversionService()


@pytest.fixture
def sample_dataframe():
    return pd.DataFrame({
        'USUBJID': ['001', '002', '003'],
        'AGE': [25, 30, 35],
        'SEX': ['M', 'F', 'M'],
        'VISITNUM': [1, 1, 1],
        'VISITDAT': pd.to_datetime(['2024-01-01', '2024-01-02', '2024-01-03'])
    })


@pytest.fixture
def mock_sas_file(tmp_path):
    file_path = tmp_path / "dm.sas7bdat"
    file_path.write_text("mock sas data")
    return str(file_path)


class TestFileDetection:
    def test_detect_file_format(self, service):
        # Test various file extensions
        assert service._detect_file_format("data.sas7bdat") == "sas"
        assert service._detect_file_format("data.xpt") == "xport"
        assert service._detect_file_format("data.csv") == "csv"
        assert service._detect_file_format("data.xlsx") == "excel"
        assert service._detect_file_format("data.xls") == "excel"
        assert service._detect_file_format("data.parquet") == "parquet"
        assert service._detect_file_format("data.unknown") == "unknown"
        
    def test_case_insensitive_detection(self, service):
        assert service._detect_file_format("DATA.SAS7BDAT") == "sas"
        assert service._detect_file_format("Data.CSV") == "csv"


class TestSASConversion:
    @pytest.mark.asyncio
    async def test_convert_sas_file(self, service, sample_dataframe, tmp_path):
        input_file = str(tmp_path / "dm.sas7bdat")
        output_file = str(tmp_path / "dm.parquet")
        
        # Mock pandas read_sas
        with patch('pandas.read_sas', return_value=sample_dataframe):
            # Execute conversion
            result = await service.convert_file(input_file, output_file, "sas")
            
            # Verify
            assert result["status"] == "success"
            assert result["format"] == "sas"
            assert result["rows"] == 3
            assert result["columns"] == 5
            assert "schema" in result
            
    @pytest.mark.asyncio
    async def test_convert_sas_with_encoding(self, service, sample_dataframe, tmp_path):
        input_file = str(tmp_path / "dm.sas7bdat")
        output_file = str(tmp_path / "dm.parquet")
        
        # Test different encodings
        encodings = ['utf-8', 'latin-1', 'iso-8859-1']
        
        for encoding in encodings:
            with patch('pandas.read_sas', return_value=sample_dataframe) as mock_read:
                await service.convert_file(input_file, output_file, "sas")
                # Verify encoding attempts
                assert mock_read.call_count > 0


class TestCSVConversion:
    @pytest.mark.asyncio
    async def test_convert_csv_file(self, service, sample_dataframe, tmp_path):
        input_file = str(tmp_path / "data.csv")
        output_file = str(tmp_path / "data.parquet")
        
        # Create actual CSV file
        sample_dataframe.to_csv(input_file, index=False)
        
        # Execute conversion
        result = await service.convert_file(input_file, output_file, "csv")
        
        # Verify
        assert result["status"] == "success"
        assert result["format"] == "csv"
        assert result["rows"] == 3
        
        # Check output file exists
        assert Path(output_file).exists()
        
    @pytest.mark.asyncio
    async def test_csv_type_inference(self, service, tmp_path):
        # Test CSV with mixed types
        df = pd.DataFrame({
            'ID': ['001', '002', '003'],
            'VALUE': ['1.5', '2.0', 'NA'],
            'DATE': ['2024-01-01', '2024-01-02', '2024-01-03']
        })
        
        input_file = str(tmp_path / "mixed.csv")
        output_file = str(tmp_path / "mixed.parquet")
        df.to_csv(input_file, index=False)
        
        # Execute
        result = await service.convert_file(input_file, output_file, "csv")
        
        # Verify type handling
        assert result["status"] == "success"
        schema = result["schema"]
        assert any(col["type"] == "string" for col in schema if col["name"] == "ID")


class TestExcelConversion:
    @pytest.mark.asyncio
    async def test_convert_excel_file(self, service, sample_dataframe, tmp_path):
        input_file = str(tmp_path / "data.xlsx")
        output_file = str(tmp_path / "data.parquet")
        
        # Mock pandas read_excel
        with patch('pandas.read_excel', return_value=sample_dataframe):
            # Execute conversion
            result = await service.convert_file(input_file, output_file, "excel")
            
            # Verify
            assert result["status"] == "success"
            assert result["format"] == "excel"
            assert result["rows"] == 3


class TestProgressCallback:
    @pytest.mark.asyncio
    async def test_progress_reporting(self, service, sample_dataframe, tmp_path):
        input_file = str(tmp_path / "data.csv")
        output_file = str(tmp_path / "data.parquet")
        sample_dataframe.to_csv(input_file, index=False)
        
        # Track progress calls
        progress_calls = []
        
        async def progress_callback(progress, message):
            progress_calls.append((progress, message))
        
        # Execute with callback
        await service.convert_file(
            input_file,
            output_file,
            "csv",
            progress_callback=progress_callback
        )
        
        # Verify progress was reported
        assert len(progress_calls) > 0
        assert any(p[0] == 100 for p in progress_calls)  # Completion reported


class TestStudyFileConversion:
    @pytest.mark.asyncio
    async def test_convert_study_files(self, service, sample_dataframe, tmp_path):
        # Setup test files
        study_id = "study123"
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        
        # Create test files
        files = ["dm.sas7bdat", "ae.csv", "lb.xlsx"]
        for f in files:
            (source_dir / f).write_text("test data")
        
        # Mock conversions
        with patch.object(service, 'convert_file', new_callable=AsyncMock) as mock_convert:
            mock_convert.return_value = {
                "status": "success",
                "rows": 100,
                "columns": 10,
                "output_size": 1024
            }
            
            # Execute
            result = await service.convert_study_files(
                study_id,
                str(source_dir)
            )
            
            # Verify
            assert result["converted_files"] == 3
            assert result["total_size"] > 0
            assert len(result["files"]) == 3
            assert mock_convert.call_count == 3


class TestErrorHandling:
    @pytest.mark.asyncio
    async def test_handle_corrupt_file(self, service, tmp_path):
        input_file = str(tmp_path / "corrupt.sas7bdat")
        output_file = str(tmp_path / "output.parquet")
        
        # Create corrupt file
        Path(input_file).write_bytes(b"corrupt data")
        
        # Mock read_sas to raise error
        with patch('pandas.read_sas', side_effect=Exception("Invalid SAS file")):
            result = await service.convert_file(input_file, output_file, "sas")
            
            # Verify error handling
            assert result["status"] == "error"
            assert "error" in result
            assert "Invalid SAS file" in result["error"]
            
    @pytest.mark.asyncio
    async def test_handle_missing_file(self, service):
        input_file = "/nonexistent/file.csv"
        output_file = "/tmp/output.parquet"
        
        # Execute
        result = await service.convert_file(input_file, output_file, "csv")
        
        # Verify
        assert result["status"] == "error"
        assert "error" in result


class TestDataValidation:
    @pytest.mark.asyncio
    async def test_validate_converted_data(self, service, tmp_path):
        # Create test data with various types
        df = pd.DataFrame({
            'ID': range(1000),
            'VALUE': np.random.randn(1000),
            'CATEGORY': ['A', 'B', 'C'] * 333 + ['A'],
            'DATE': pd.date_range('2024-01-01', periods=1000)
        })
        
        input_file = str(tmp_path / "test.csv")
        output_file = str(tmp_path / "test.parquet")
        df.to_csv(input_file, index=False)
        
        # Execute
        result = await service.convert_file(input_file, output_file, "csv")
        
        # Verify data integrity
        assert result["status"] == "success"
        assert result["rows"] == 1000
        assert result["columns"] == 4
        
        # Verify output file
        output_df = pd.read_parquet(output_file)
        assert len(output_df) == 1000
        assert list(output_df.columns) == ['ID', 'VALUE', 'CATEGORY', 'DATE']