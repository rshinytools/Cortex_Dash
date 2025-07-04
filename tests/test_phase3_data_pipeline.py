# ABOUTME: Test suite for Phase 3 Data Pipeline System including Medidata integration and ZIP uploads
# ABOUTME: Validates data source connections, pipeline execution, transformations, and asynchronous processing

import pytest
import pandas as pd
import numpy as np
import json
import zipfile
import asyncio
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch
from app.clinical_modules.data_pipeline.data_sources import (
    MedidataAPISource, ZipFileUploadSource, SFTPDataSource
)
from app.clinical_modules.data_pipeline.dsl_executor import DSLPipelineExecutor
from app.clinical_modules.data_pipeline.python_executor import PythonPipelineExecutor
from tests.conftest import expected_result

class TestPhase3DataPipeline:
    """Comprehensive test suite for Phase 3: Data Pipeline System"""
    
    @pytest.mark.integration
    @pytest.mark.critical
    @expected_result("Medidata API connection established and data fetched successfully")
    async def test_medidata_api_integration(self, httpx_mock):
        """Test Medidata Rave API integration - PRIMARY DATA SOURCE"""
        # Mock Medidata API responses
        httpx_mock.add_response(
            url="https://api.mdsol.com/studies",
            json={"studies": [{"oid": "TEST-001", "name": "Test Study"}]},
            status_code=200
        )
        
        httpx_mock.add_response(
            url="https://api.mdsol.com/studies/TEST-001/datasets/DM",
            json={
                "items": [
                    {
                        "USUBJID": "TEST-001-001",
                        "AGE": 45,
                        "SEX": "M",
                        "RACE": "WHITE",
                        "COUNTRY": "USA",
                        "VISITNUM": 1,
                        "VISITDAT": "2024-01-15"
                    },
                    {
                        "USUBJID": "TEST-001-002", 
                        "AGE": 52,
                        "SEX": "F",
                        "RACE": "ASIAN",
                        "COUNTRY": "Japan",
                        "VISITNUM": 1,
                        "VISITDAT": "2024-01-16"
                    }
                ]
            },
            status_code=200
        )
        
        # Initialize data source
        source = MedidataAPISource({
            "api_url": "https://api.mdsol.com",
            "api_key": "test-api-key-12345",
            "study_oid": "TEST-001"
        })
        
        # Test connection
        connected = await source.connect()
        assert connected is True
        
        # Fetch demographics data
        df = await source.fetch_data({"dataset": "DM"})
        
        # Validate data
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert list(df.columns) == ["USUBJID", "AGE", "SEX", "RACE", "COUNTRY", "VISITNUM", "VISITDAT"]
        assert df["USUBJID"].iloc[0] == "TEST-001-001"
        assert df["AGE"].iloc[1] == 52
    
    @pytest.mark.integration
    @pytest.mark.critical
    @expected_result("ZIP file upload processes multiple file types correctly")
    async def test_zip_file_upload_processing(self, tmp_path, test_study):
        """Test ZIP file upload data source - PRIMARY DATA SOURCE"""
        # Create test data files
        demographics_csv = tmp_path / "dm.csv"
        demographics_csv.write_text(
            "USUBJID,AGE,SEX,RACE,COUNTRY\n"
            "SUBJ001,45,M,WHITE,USA\n"
            "SUBJ002,38,F,BLACK,USA\n"
            "SUBJ003,52,M,ASIAN,China\n"
        )
        
        adverse_events_csv = tmp_path / "ae.csv"
        adverse_events_csv.write_text(
            "USUBJID,AETERM,AESTDTC,AESER,AEREL\n"
            "SUBJ001,Headache,2024-01-15,N,POSSIBLY RELATED\n"
            "SUBJ001,Nausea,2024-01-20,N,RELATED\n"
            "SUBJ002,Fatigue,2024-01-18,N,NOT RELATED\n"
        )
        
        # Create SAS dataset (mock with parquet for testing)
        lab_data = pd.DataFrame({
            "USUBJID": ["SUBJ001", "SUBJ001", "SUBJ002"],
            "LBTEST": ["WBC", "RBC", "WBC"],
            "LBSTRESN": [7.5, 4.8, 6.9],
            "LBSTRESU": ["10^9/L", "10^12/L", "10^9/L"]
        })
        lab_parquet = tmp_path / "lb.parquet"
        lab_data.to_parquet(lab_parquet)
        
        # Create ZIP file
        zip_path = tmp_path / "clinical_data_extract.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.write(demographics_csv, "dm.csv")
            zf.write(adverse_events_csv, "ae.csv") 
            zf.write(lab_parquet, "lb.parquet")
        
        # Initialize ZIP source
        source = ZipFileUploadSource({
            "study_id": str(test_study.id),
            "org_id": str(test_study.org_id),
            "upload_path": str(zip_path)
        })
        
        # Test connection
        connected = await source.connect()
        assert connected is True
        
        # Test fetching specific dataset
        dm_df = await source.fetch_data({"dataset": "dm"})
        assert len(dm_df) == 3
        assert "USUBJID" in dm_df.columns
        
        # Test fetching all datasets
        all_data = await source.fetch_data({})
        assert isinstance(all_data, pd.DataFrame)
    
    @pytest.mark.unit
    @expected_result("DSL executor performs standard transformations safely")
    async def test_dsl_pipeline_executor(self, tmp_path, test_study):
        """Test Layer 1: DSL-based safe transformations"""
        # Create test data
        test_data = pd.DataFrame({
            "USUBJID": ["S001", "S002", "S003", "S004"],
            "AGE": [45, 52, 38, 61],
            "SEX": ["M", "F", "F", "M"],
            "VISITNUM": [1, 1, 1, 1],
            "WEIGHT": [75.5, 62.3, 68.9, 82.1]
        })
        
        # Save test data
        data_path = tmp_path / "studies" / str(test_study.id) / "source_data" / "2024-01-01"
        data_path.mkdir(parents=True, exist_ok=True)
        test_data.to_parquet(data_path / "demographics.parquet")
        
        # Define DSL pipeline
        pipeline_def = {
            "version": "1.0",
            "name": "Demographics Processing",
            "description": "Process demographics data",
            "inputs": ["demographics"],
            "outputs": ["demographics_clean"],
            "steps": [
                {
                    "operation": "filter_rows",
                    "parameters": {
                        "dataset": "demographics",
                        "condition": "AGE >= 40"
                    }
                },
                {
                    "operation": "add_calculated_column",
                    "parameters": {
                        "dataset": "demographics",
                        "column_name": "AGE_GROUP",
                        "expression": "['40-50' if x < 50 else '50+' for x in demographics['AGE']]"
                    }
                },
                {
                    "operation": "drop_columns",
                    "parameters": {
                        "dataset": "demographics",
                        "columns": ["VISITNUM"]
                    }
                },
                {
                    "operation": "save_dataset",
                    "parameters": {
                        "dataset": "demographics",
                        "output_name": "demographics_clean"
                    }
                }
            ]
        }
        
        # Execute pipeline
        executor = DSLPipelineExecutor()
        result = await executor.execute(
            json.dumps(pipeline_def),
            str(test_study.id),
            "2024-01-01"
        )
        
        # Validate results
        assert result["status"] == "success"
        assert len(result["outputs"]) == 1
        assert "demographics_clean" in result["outputs"]
        
        # Check output file
        output_path = tmp_path / "studies" / str(test_study.id) / "analysis_data" / "2024-01-01" / "demographics_clean.parquet"
        assert output_path.exists()
        
        # Validate transformed data
        output_df = pd.read_parquet(output_path)
        assert len(output_df) == 3  # Filtered to AGE >= 40
        assert "AGE_GROUP" in output_df.columns
        assert "VISITNUM" not in output_df.columns
    
    @pytest.mark.integration
    @expected_result("Python executor runs complex transformations in isolated container")
    async def test_python_pipeline_executor(self, tmp_path, test_study):
        """Test Layer 2: Containerized Python execution for complex scripts"""
        # Create test data
        ae_data = pd.DataFrame({
            "USUBJID": ["S001", "S001", "S002", "S002", "S003"],
            "AETERM": ["Headache", "Nausea", "Fatigue", "Headache", "Dizziness"],
            "AESTDTC": ["2024-01-15", "2024-01-20", "2024-01-18", "2024-01-22", "2024-01-19"],
            "AESER": ["N", "N", "N", "Y", "N"],
            "AEREL": ["RELATED", "RELATED", "NOT RELATED", "POSSIBLY RELATED", "RELATED"]
        })
        
        # Save test data
        data_path = tmp_path / "studies" / str(test_study.id) / "source_data" / "2024-01-01"
        data_path.mkdir(parents=True, exist_ok=True)
        ae_data.to_parquet(data_path / "ae.parquet")
        
        # Python script for complex analysis
        python_script = """
import pandas as pd
import numpy as np
from datetime import datetime

# Load adverse events data
ae = load_parquet('ae.parquet')

# Complex transformations
# 1. Parse dates
ae['AESTDTC'] = pd.to_datetime(ae['AESTDTC'])

# 2. Create severity score
severity_map = {'N': 1, 'Y': 3}
ae['SEVERITY_SCORE'] = ae['AESER'].map(severity_map)

# 3. Calculate days from first AE per subject
ae['FIRST_AE_DATE'] = ae.groupby('USUBJID')['AESTDTC'].transform('min')
ae['DAYS_FROM_FIRST'] = (ae['AESTDTC'] - ae['FIRST_AE_DATE']).dt.days

# 4. Create summary statistics
ae_summary = ae.groupby('USUBJID').agg({
    'AETERM': 'count',
    'SEVERITY_SCORE': 'max',
    'DAYS_FROM_FIRST': 'max'
}).rename(columns={
    'AETERM': 'TOTAL_AES',
    'SEVERITY_SCORE': 'MAX_SEVERITY',
    'DAYS_FROM_FIRST': 'AE_DURATION_DAYS'
})

# 5. Add risk categorization
ae_summary['RISK_CATEGORY'] = pd.cut(
    ae_summary['TOTAL_AES'] * ae_summary['MAX_SEVERITY'],
    bins=[0, 2, 5, float('inf')],
    labels=['LOW', 'MEDIUM', 'HIGH']
)

# Save results
save_parquet(ae_summary, 'ae_risk_analysis.parquet')
"""
        
        # Execute in container (mocked for testing)
        with patch('app.clinical_modules.data_pipeline.python_executor.docker') as mock_docker:
            # Mock container execution
            mock_container = Mock()
            mock_container.run.return_value = (0, "Success")
            mock_docker.from_env.return_value.containers.run.return_value = mock_container
            
            executor = PythonPipelineExecutor()
            result = await executor.execute(
                python_script,
                str(test_study.id),
                "2024-01-01",
                timeout=300
            )
            
            # In real execution, this would run in Docker
            assert result["status"] == "success"
    
    @pytest.mark.integration
    @pytest.mark.async
    @expected_result("Pipeline execution runs asynchronously with Celery")
    async def test_async_pipeline_execution(self, test_study, celery_app, celery_worker):
        """Test asynchronous pipeline execution with Celery"""
        from app.tasks.pipeline_tasks import execute_pipeline_task
        
        # Queue pipeline execution
        task = execute_pipeline_task.delay(
            study_id=str(test_study.id),
            pipeline_config={
                "type": "dsl",
                "steps": [
                    {"operation": "select_columns", "parameters": {"columns": ["USUBJID", "AGE"]}}
                ]
            },
            run_date="2024-01-01"
        )
        
        # Wait for completion (with timeout)
        result = task.get(timeout=10)
        
        assert result["status"] in ["success", "completed"]
        assert "task_id" in result
    
    @pytest.mark.unit
    @expected_result("Pipeline validates input data and configurations")
    async def test_pipeline_validation(self):
        """Test pipeline validation and error handling"""
        executor = DSLPipelineExecutor()
        
        # Test 1: Invalid operation
        invalid_pipeline = {
            "version": "1.0",
            "name": "Invalid Pipeline",
            "inputs": ["data"],
            "outputs": ["output"],
            "steps": [
                {
                    "operation": "invalid_operation",  # This should fail
                    "parameters": {}
                }
            ]
        }
        
        with pytest.raises(ValueError) as exc_info:
            await executor.execute(json.dumps(invalid_pipeline), "study-123", "2024-01-01")
        assert "Operation 'invalid_operation' not allowed" in str(exc_info.value)
        
        # Test 2: Missing required parameters
        missing_params_pipeline = {
            "version": "1.0",
            "name": "Missing Params",
            "inputs": ["data"],
            "outputs": ["output"],
            "steps": [
                {
                    "operation": "filter_rows",
                    "parameters": {}  # Missing 'condition' parameter
                }
            ]
        }
        
        # Should handle gracefully
        result = await executor.execute(json.dumps(missing_params_pipeline), "study-123", "2024-01-01")
        assert result["status"] == "error"
    
    @pytest.mark.performance
    @expected_result("Pipeline processes large datasets within performance targets")
    async def test_pipeline_performance_large_data(self, tmp_path, test_study):
        """Test pipeline performance with large clinical datasets"""
        import time
        
        # Create large dataset (100k rows)
        large_data = pd.DataFrame({
            "USUBJID": [f"SUBJ{i:06d}" for i in range(100000)],
            "VISITNUM": np.random.randint(1, 10, 100000),
            "VISITDAT": pd.date_range("2024-01-01", periods=100000, freq="H"),
            "VALUE1": np.random.randn(100000),
            "VALUE2": np.random.randn(100000),
            "CATEGORY": np.random.choice(["A", "B", "C", "D"], 100000)
        })
        
        # Save data
        data_path = tmp_path / "studies" / str(test_study.id) / "source_data" / "2024-01-01"
        data_path.mkdir(parents=True, exist_ok=True)
        large_data.to_parquet(data_path / "large_dataset.parquet")
        
        # Complex pipeline
        pipeline_def = {
            "version": "1.0",
            "name": "Large Data Processing",
            "inputs": ["large_dataset"],
            "outputs": ["processed_data"],
            "steps": [
                {
                    "operation": "filter_rows",
                    "parameters": {
                        "dataset": "large_dataset",
                        "condition": "VISITNUM <= 5"
                    }
                },
                {
                    "operation": "aggregate",
                    "parameters": {
                        "dataset": "large_dataset",
                        "group_by": ["USUBJID", "CATEGORY"],
                        "aggregations": {
                            "VALUE1": ["mean", "std"],
                            "VALUE2": ["min", "max"]
                        }
                    }
                },
                {
                    "operation": "save_dataset",
                    "parameters": {
                        "dataset": "large_dataset",
                        "output_name": "processed_data"
                    }
                }
            ]
        }
        
        executor = DSLPipelineExecutor()
        
        start_time = time.time()
        result = await executor.execute(
            json.dumps(pipeline_def),
            str(test_study.id),
            "2024-01-01"
        )
        execution_time = time.time() - start_time
        
        # Should complete within 10 seconds for 100k rows
        assert execution_time < 10.0
        assert result["status"] == "success"
    
    @pytest.mark.integration
    @expected_result("Pipeline handles multiple data sources in sequence")
    async def test_multi_source_pipeline(self, tmp_path, test_study, httpx_mock):
        """Test pipeline with multiple data sources"""
        # Setup Medidata mock
        httpx_mock.add_response(
            url="https://api.mdsol.com/studies",
            json={"status": "ok"},
            status_code=200
        )
        
        # Create ZIP file
        csv_data = "USUBJID,AETERM\nSUBJ001,Headache\nSUBJ002,Nausea"
        csv_path = tmp_path / "ae.csv"
        csv_path.write_text(csv_data)
        
        zip_path = tmp_path / "supplement.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.write(csv_path, "ae.csv")
        
        # Test fetching from multiple sources
        sources = [
            MedidataAPISource({
                "api_url": "https://api.mdsol.com",
                "api_key": "test-key",
                "study_oid": "TEST-001"
            }),
            ZipFileUploadSource({
                "study_id": str(test_study.id),
                "org_id": str(test_study.org_id),
                "upload_path": str(zip_path)
            })
        ]
        
        # Both sources should connect
        for source in sources:
            connected = await source.connect()
            assert connected is True
    
    @pytest.mark.compliance
    @expected_result("Pipeline maintains data lineage for audit trail")
    async def test_pipeline_data_lineage(self, db_session, test_study):
        """Test data lineage tracking for compliance"""
        from app.models import PipelineExecution, DataLineage
        
        # Record pipeline execution
        execution = PipelineExecution(
            study_id=test_study.id,
            pipeline_name="Demographics Processing",
            started_at=datetime.utcnow(),
            status="running",
            config={
                "type": "dsl",
                "version": "1.0"
            }
        )
        db_session.add(execution)
        await db_session.commit()
        
        # Record data lineage
        lineage = DataLineage(
            execution_id=execution.id,
            input_datasets=["raw/demographics.sas7bdat"],
            output_datasets=["processed/demographics_clean.parquet"],
            transformations=[
                {
                    "step": 1,
                    "operation": "filter_rows",
                    "parameters": {"condition": "AGE >= 18"}
                }
            ],
            created_at=datetime.utcnow()
        )
        db_session.add(lineage)
        await db_session.commit()
        
        # Verify lineage tracking
        assert lineage.execution_id == execution.id
        assert len(lineage.input_datasets) == 1
        assert len(lineage.output_datasets) == 1