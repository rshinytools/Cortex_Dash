# ABOUTME: Comprehensive test suite for study transformation API endpoints
# ABOUTME: Tests transformation creation, execution, validation, and security

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
import json
from unittest.mock import patch, MagicMock, AsyncMock
import os
import tempfile
import pandas as pd
import pyarrow.parquet as pq
from datetime import datetime

from app.models.study import Study
from app.models.study_transformation import StudyTransformation, TransformationStatus
from app.models.user import User
from app.core.security import create_access_token


@pytest.fixture
async def test_study(db: AsyncSession, test_user: User):
    """Create a test study for transformation tests."""
    study = Study(
        name="Test Study",
        description="Study for transformation testing",
        owner_id=test_user.id,
        protocol_number="TEST-001",
        therapeutic_area="Oncology",
        phase="Phase III",
        sponsor_name="Test Sponsor",
        indication="Test Indication"
    )
    db.add(study)
    await db.commit()
    await db.refresh(study)
    return study


@pytest.fixture
async def test_transformation(db: AsyncSession, test_study: Study):
    """Create a test transformation."""
    transformation = StudyTransformation(
        study_id=test_study.id,
        name="Test Transformation",
        description="Test transformation pipeline",
        script_content="df['new_col'] = df['old_col'] * 2",
        input_datasets=["dm", "ae"],
        output_dataset="transformed_data",
        status=TransformationStatus.DRAFT,
        created_by=test_study.owner_id
    )
    db.add(transformation)
    await db.commit()
    await db.refresh(transformation)
    return transformation


@pytest.fixture
def mock_data_directory(tmp_path):
    """Create mock data directory structure with test datasets."""
    study_dir = tmp_path / "studies" / "test-study-id" / "source_data" / "2024-01-01"
    study_dir.mkdir(parents=True)
    
    # Create mock DM dataset
    dm_data = pd.DataFrame({
        'USUBJID': ['001', '002', '003'],
        'AGE': [45, 52, 38],
        'SEX': ['M', 'F', 'M'],
        'RACE': ['WHITE', 'BLACK', 'ASIAN']
    })
    dm_data.to_parquet(study_dir / 'dm.parquet')
    
    # Create mock AE dataset
    ae_data = pd.DataFrame({
        'USUBJID': ['001', '001', '002', '003'],
        'AETERM': ['Headache', 'Nausea', 'Fatigue', 'Dizziness'],
        'AESEV': ['MILD', 'MODERATE', 'MILD', 'SEVERE']
    })
    ae_data.to_parquet(study_dir / 'ae.parquet')
    
    return tmp_path


class TestStudyTransformationAPI:
    """Test suite for study transformation API endpoints."""
    
    @pytest.mark.asyncio
    async def test_create_transformation(
        self,
        client: AsyncClient,
        test_study: Study,
        test_user: User
    ):
        """Test creating a new transformation."""
        token = create_access_token(subject=test_user.id)
        headers = {"Authorization": f"Bearer {token}"}
        
        transformation_data = {
            "name": "New Transformation",
            "description": "Test transformation creation",
            "script_content": "# Simple transformation\ndf['calculated'] = df['value'] * 1.5",
            "input_datasets": ["dm", "ae"],
            "output_dataset": "analysis_ready"
        }
        
        response = await client.post(
            f"/api/v1/studies/{test_study.id}/transformations/",
            json=transformation_data,
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == transformation_data["name"]
        assert data["status"] == "draft"
        assert data["study_id"] == test_study.id
    
    @pytest.mark.asyncio
    async def test_create_transformation_invalid_script(
        self,
        client: AsyncClient,
        test_study: Study,
        test_user: User
    ):
        """Test creating transformation with security violations."""
        token = create_access_token(subject=test_user.id)
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test with import statement
        transformation_data = {
            "name": "Malicious Transformation",
            "description": "Should be rejected",
            "script_content": "import os\nos.system('rm -rf /')",
            "input_datasets": ["dm"],
            "output_dataset": "output"
        }
        
        response = await client.post(
            f"/api/v1/studies/{test_study.id}/transformations/",
            json=transformation_data,
            headers=headers
        )
        
        assert response.status_code == 400
        assert "security violation" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_get_transformations(
        self,
        client: AsyncClient,
        test_study: Study,
        test_transformation: StudyTransformation,
        test_user: User
    ):
        """Test retrieving transformations for a study."""
        token = create_access_token(subject=test_user.id)
        headers = {"Authorization": f"Bearer {token}"}
        
        response = await client.get(
            f"/api/v1/studies/{test_study.id}/transformations/",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == test_transformation.id
        assert data[0]["name"] == test_transformation.name
    
    @pytest.mark.asyncio
    async def test_get_transformation_by_id(
        self,
        client: AsyncClient,
        test_study: Study,
        test_transformation: StudyTransformation,
        test_user: User
    ):
        """Test retrieving a specific transformation."""
        token = create_access_token(subject=test_user.id)
        headers = {"Authorization": f"Bearer {token}"}
        
        response = await client.get(
            f"/api/v1/studies/{test_study.id}/transformations/{test_transformation.id}",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_transformation.id
        assert data["script_content"] == test_transformation.script_content
    
    @pytest.mark.asyncio
    async def test_update_transformation(
        self,
        client: AsyncClient,
        test_study: Study,
        test_transformation: StudyTransformation,
        test_user: User
    ):
        """Test updating a transformation."""
        token = create_access_token(subject=test_user.id)
        headers = {"Authorization": f"Bearer {token}"}
        
        update_data = {
            "name": "Updated Transformation",
            "description": "Updated description",
            "script_content": "df['updated'] = True"
        }
        
        response = await client.put(
            f"/api/v1/studies/{test_study.id}/transformations/{test_transformation.id}",
            json=update_data,
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["script_content"] == update_data["script_content"]
    
    @pytest.mark.asyncio
    async def test_delete_transformation(
        self,
        client: AsyncClient,
        test_study: Study,
        test_transformation: StudyTransformation,
        test_user: User,
        db: AsyncSession
    ):
        """Test deleting a transformation."""
        token = create_access_token(subject=test_user.id)
        headers = {"Authorization": f"Bearer {token}"}
        
        response = await client.delete(
            f"/api/v1/studies/{test_study.id}/transformations/{test_transformation.id}",
            headers=headers
        )
        
        assert response.status_code == 200
        
        # Verify deletion
        result = await db.get(StudyTransformation, test_transformation.id)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_validate_transformation(
        self,
        client: AsyncClient,
        test_study: Study,
        test_user: User,
        mock_data_directory
    ):
        """Test transformation validation endpoint."""
        token = create_access_token(subject=test_user.id)
        headers = {"Authorization": f"Bearer {token}"}
        
        with patch('app.services.study_transformation.DATA_DIR', mock_data_directory):
            validation_data = {
                "script_content": "df['age_group'] = pd.cut(df['AGE'], bins=[0, 50, 100])",
                "input_datasets": ["dm"]
            }
            
            response = await client.post(
                f"/api/v1/studies/{test_study.id}/transformations/validate",
                json=validation_data,
                headers=headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["is_valid"] is True
            assert "sample_output" in data
    
    @pytest.mark.asyncio
    async def test_validate_transformation_with_error(
        self,
        client: AsyncClient,
        test_study: Study,
        test_user: User
    ):
        """Test transformation validation with script errors."""
        token = create_access_token(subject=test_user.id)
        headers = {"Authorization": f"Bearer {token}"}
        
        validation_data = {
            "script_content": "df['invalid'] = undefined_variable",
            "input_datasets": ["dm"]
        }
        
        response = await client.post(
            f"/api/v1/studies/{test_study.id}/transformations/validate",
            json=validation_data,
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is False
        assert "error" in data
    
    @pytest.mark.asyncio
    async def test_execute_transformation(
        self,
        client: AsyncClient,
        test_study: Study,
        test_transformation: StudyTransformation,
        test_user: User,
        mock_data_directory
    ):
        """Test transformation execution endpoint."""
        token = create_access_token(subject=test_user.id)
        headers = {"Authorization": f"Bearer {token}"}
        
        # Mock Celery task
        with patch('app.api.v1.endpoints.study_transformation.execute_transformation_task') as mock_task:
            mock_task.delay.return_value.id = "test-task-id"
            
            response = await client.post(
                f"/api/v1/studies/{test_study.id}/transformations/{test_transformation.id}/execute",
                headers=headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["task_id"] == "test-task-id"
            assert data["status"] == "running"
            
            mock_task.delay.assert_called_once_with(
                test_transformation.id,
                test_study.id
            )
    
    @pytest.mark.asyncio
    async def test_get_transformation_status(
        self,
        client: AsyncClient,
        test_study: Study,
        test_transformation: StudyTransformation,
        test_user: User
    ):
        """Test getting transformation execution status."""
        token = create_access_token(subject=test_user.id)
        headers = {"Authorization": f"Bearer {token}"}
        
        # Mock Celery AsyncResult
        with patch('app.api.v1.endpoints.study_transformation.AsyncResult') as mock_result:
            mock_instance = MagicMock()
            mock_instance.state = "SUCCESS"
            mock_instance.info = {
                "current": 100,
                "total": 100,
                "status": "Transformation completed successfully"
            }
            mock_result.return_value = mock_instance
            
            response = await client.get(
                f"/api/v1/studies/{test_study.id}/transformations/status/test-task-id",
                headers=headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["state"] == "SUCCESS"
            assert data["current"] == 100
            assert data["total"] == 100
    
    @pytest.mark.asyncio
    async def test_transformation_unauthorized(
        self,
        client: AsyncClient,
        test_study: Study
    ):
        """Test accessing transformations without authentication."""
        response = await client.get(
            f"/api/v1/studies/{test_study.id}/transformations/"
        )
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_transformation_forbidden(
        self,
        client: AsyncClient,
        test_study: Study,
        db: AsyncSession
    ):
        """Test accessing transformations for another user's study."""
        # Create another user
        other_user = User(
            email="other@example.com",
            hashed_password="hashed",
            full_name="Other User"
        )
        db.add(other_user)
        await db.commit()
        await db.refresh(other_user)
        
        token = create_access_token(subject=other_user.id)
        headers = {"Authorization": f"Bearer {token}"}
        
        response = await client.get(
            f"/api/v1/studies/{test_study.id}/transformations/",
            headers=headers
        )
        
        assert response.status_code == 403


class TestStudyTransformationService:
    """Test suite for StudyTransformationService."""
    
    @pytest.mark.asyncio
    async def test_validate_script_security(self):
        """Test script security validation."""
        from app.services.study_transformation import StudyTransformationService
        
        service = StudyTransformationService(None)  # DB not needed for validation
        
        # Test allowed operations
        valid_scripts = [
            "df['new'] = df['old'] * 2",
            "df = df[df['age'] > 18]",
            "df.groupby('treatment').mean()",
            "pd.merge(df1, df2, on='id')"
        ]
        
        for script in valid_scripts:
            result = service._validate_script_security(script)
            assert result is True
        
        # Test forbidden operations
        invalid_scripts = [
            "import os",
            "from subprocess import call",
            "__import__('os')",
            "exec('malicious code')",
            "eval('malicious code')",
            "open('/etc/passwd')",
            "compile('malicious', 'string', 'exec')"
        ]
        
        for script in invalid_scripts:
            result = service._validate_script_security(script)
            assert result is False
    
    @pytest.mark.asyncio
    async def test_execute_transformation_script(self, mock_data_directory):
        """Test safe execution of transformation scripts."""
        from app.services.study_transformation import StudyTransformationService
        
        service = StudyTransformationService(None)
        
        # Load test data
        dm_path = mock_data_directory / "studies" / "test-study-id" / "source_data" / "2024-01-01" / "dm.parquet"
        dm_df = pd.read_parquet(dm_path)
        
        # Test successful transformation
        script = """
df['age_category'] = pd.cut(df['AGE'], bins=[0, 40, 60, 100], labels=['Young', 'Middle', 'Senior'])
df['is_male'] = df['SEX'] == 'M'
"""
        
        result_df = service._execute_transformation_script(
            script,
            {'dm': dm_df}
        )
        
        assert 'age_category' in result_df.columns
        assert 'is_male' in result_df.columns
        assert len(result_df) == len(dm_df)
    
    @pytest.mark.asyncio
    async def test_resource_limits(self, mock_data_directory):
        """Test resource limit enforcement during transformation."""
        from app.services.study_transformation import StudyTransformationService
        
        service = StudyTransformationService(None)
        
        # Create large dataset
        large_df = pd.DataFrame({
            'id': range(1000000),
            'value': range(1000000)
        })
        
        # Test memory-intensive operation
        script = """
# This should work within limits
df['squared'] = df['value'] ** 2
df['cubed'] = df['value'] ** 3
"""
        
        # Should complete successfully
        result_df = service._execute_transformation_script(
            script,
            {'large': large_df}
        )
        
        assert 'squared' in result_df.columns
        assert 'cubed' in result_df.columns
    
    @pytest.mark.asyncio
    async def test_merge_datasets(self, mock_data_directory):
        """Test merging multiple input datasets."""
        from app.services.study_transformation import StudyTransformationService
        
        service = StudyTransformationService(None)
        
        # Load test datasets
        study_dir = mock_data_directory / "studies" / "test-study-id" / "source_data" / "2024-01-01"
        dm_df = pd.read_parquet(study_dir / "dm.parquet")
        ae_df = pd.read_parquet(study_dir / "ae.parquet")
        
        # Test merge operation
        script = """
# Merge demographics with adverse events
df = pd.merge(dm, ae, on='USUBJID', how='left')
df['has_ae'] = ~df['AETERM'].isna()
"""
        
        result_df = service._execute_transformation_script(
            script,
            {'dm': dm_df, 'ae': ae_df}
        )
        
        assert 'has_ae' in result_df.columns
        assert 'AGE' in result_df.columns  # From DM
        assert 'AETERM' in result_df.columns  # From AE


class TestTransformationEdgeCases:
    """Test edge cases and error scenarios."""
    
    @pytest.mark.asyncio
    async def test_empty_dataset_handling(self):
        """Test transformation with empty datasets."""
        from app.services.study_transformation import StudyTransformationService
        
        service = StudyTransformationService(None)
        
        empty_df = pd.DataFrame()
        script = "df['new_col'] = 'default_value'"
        
        result_df = service._execute_transformation_script(
            script,
            {'empty': empty_df}
        )
        
        assert result_df.empty
        assert 'new_col' in result_df.columns
    
    @pytest.mark.asyncio
    async def test_malformed_script_handling(self):
        """Test handling of malformed transformation scripts."""
        from app.services.study_transformation import StudyTransformationService
        
        service = StudyTransformationService(None)
        
        test_df = pd.DataFrame({'col1': [1, 2, 3]})
        
        # Syntax error
        script = "df['new'] = df['col1'] +"  # Incomplete expression
        
        with pytest.raises(SyntaxError):
            service._execute_transformation_script(script, {'test': test_df})
        
        # Runtime error
        script = "df['new'] = df['nonexistent_column'] * 2"
        
        with pytest.raises(KeyError):
            service._execute_transformation_script(script, {'test': test_df})
    
    @pytest.mark.asyncio
    async def test_output_validation(self):
        """Test validation of transformation output."""
        from app.services.study_transformation import StudyTransformationService
        
        service = StudyTransformationService(None)
        
        test_df = pd.DataFrame({'col1': [1, 2, 3]})
        
        # Script that doesn't produce a DataFrame
        script = "df = 'not a dataframe'"
        
        with pytest.raises(ValueError):
            service._execute_transformation_script(script, {'test': test_df})
        
        # Script that produces None
        script = "df = None"
        
        with pytest.raises(ValueError):
            service._execute_transformation_script(script, {'test': test_df})


class TestTransformationPerformance:
    """Test performance aspects of transformations."""
    
    @pytest.mark.asyncio
    async def test_large_dataset_transformation(self):
        """Test transformation performance with large datasets."""
        from app.services.study_transformation import StudyTransformationService
        import time
        
        service = StudyTransformationService(None)
        
        # Create large dataset (100k rows)
        large_df = pd.DataFrame({
            'id': range(100000),
            'value1': range(100000),
            'value2': range(100000, 200000),
            'category': ['A', 'B', 'C', 'D'] * 25000
        })
        
        script = """
# Complex transformation
df['ratio'] = df['value1'] / df['value2']
df['value_sum'] = df['value1'] + df['value2']
df['category_encoded'] = pd.Categorical(df['category']).codes
grouped = df.groupby('category').agg({
    'ratio': 'mean',
    'value_sum': 'sum'
}).reset_index()
df = pd.merge(df, grouped, on='category', suffixes=('', '_group'))
"""
        
        start_time = time.time()
        result_df = service._execute_transformation_script(
            script,
            {'large': large_df}
        )
        execution_time = time.time() - start_time
        
        # Should complete in reasonable time
        assert execution_time < 5.0  # 5 seconds max
        assert len(result_df) == len(large_df)
        assert 'ratio_group' in result_df.columns