# ABOUTME: Unit tests for StudyInitializationService
# ABOUTME: Tests all phases of study initialization process

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from app.services.study_initialization_service import StudyInitializationService
from app.models.study import Study
from app.models.dashboard import DashboardTemplate


@pytest.fixture
def service():
    return StudyInitializationService()


@pytest.fixture
def mock_study():
    study = Mock(spec=Study)
    study.id = "study123"
    study.name = "Test Study"
    study.code = "TST001"
    study.org_id = "org123"
    study.initialization_status = "not_started"
    study.initialization_progress = 0
    study.initialization_steps = {}
    return study


@pytest.fixture
def mock_template():
    template = Mock(spec=DashboardTemplate)
    template.id = "template123"
    template.name = "Test Template"
    template.template_structure = {
        "menuStructure": {
            "items": [
                {
                    "id": "safety",
                    "label": "Safety",
                    "items": []
                }
            ]
        },
        "dashboardTemplates": [
            {
                "id": "dash1",
                "title": "Safety Dashboard",
                "widgets": [
                    {
                        "id": "widget1",
                        "config": {
                            "dataRequirements": {
                                "primaryDataset": "AE",
                                "fields": ["USUBJID", "AEDECOD"]
                            }
                        }
                    }
                ]
            }
        ]
    }
    return template


class TestPhase1TemplateApplication:
    @pytest.mark.asyncio
    async def test_apply_template_success(self, service, mock_study, mock_template):
        # Mock dependencies
        service.db = AsyncMock()
        service.template_service = AsyncMock()
        service.template_service.apply_template_to_study = AsyncMock(return_value=mock_study)
        
        # Execute
        await service._phase1_apply_template(
            mock_study,
            "template123",
            service.db,
            Mock()
        )
        
        # Verify
        service.template_service.apply_template_to_study.assert_called_once_with(
            service.db,
            mock_study.id,
            "template123"
        )
        
    @pytest.mark.asyncio
    async def test_apply_template_failure(self, service, mock_study):
        # Mock dependencies
        service.db = AsyncMock()
        service.template_service = AsyncMock()
        service.template_service.apply_template_to_study = AsyncMock(
            side_effect=Exception("Template not found")
        )
        
        # Execute and verify exception
        with pytest.raises(Exception, match="Template not found"):
            await service._phase1_apply_template(
                mock_study,
                "invalid_template",
                service.db,
                Mock()
            )


class TestPhase2DataProcessing:
    @pytest.mark.asyncio
    async def test_process_uploaded_files(self, service, mock_study):
        # Mock file system
        mock_files = [
            {"name": "dm.sas7bdat", "path": "/data/dm.sas7bdat", "size": 1024},
            {"name": "ae.sas7bdat", "path": "/data/ae.sas7bdat", "size": 2048}
        ]
        
        with patch('os.path.exists', return_value=True):
            with patch('os.listdir', return_value=['dm.sas7bdat', 'ae.sas7bdat']):
                with patch('os.path.getsize', side_effect=[1024, 2048]):
                    # Mock conversion service
                    service.file_conversion_service = AsyncMock()
                    service.file_conversion_service.convert_study_files = AsyncMock(
                        return_value={
                            "converted_files": 2,
                            "total_size": 3072,
                            "files": ["dm.parquet", "ae.parquet"]
                        }
                    )
                    
                    # Execute
                    await service._phase2_process_data(
                        mock_study,
                        Mock(),
                        Mock()
                    )
                    
                    # Verify conversion was called
                    service.file_conversion_service.convert_study_files.assert_called_once()


class TestPhase3FieldMapping:
    @pytest.mark.asyncio
    async def test_generate_field_mappings(self, service, mock_study, mock_template):
        # Mock data requirements extraction
        expected_requirements = [
            {
                "widget_id": "widget1",
                "dataset": "AE",
                "fields": ["USUBJID", "AEDECOD"]
            }
        ]
        
        # Mock field mapping service
        service.field_mapping_service = AsyncMock()
        service.field_mapping_service.generate_mappings_for_study = AsyncMock(
            return_value={
                "total_mappings": 2,
                "auto_mapped": 2,
                "manual_required": 0
            }
        )
        
        # Mock template service
        service.template_service = AsyncMock()
        service.template_service.get_template = AsyncMock(return_value=mock_template)
        
        # Execute
        await service._phase3_configure_mappings(
            mock_study,
            AsyncMock(),
            Mock()
        )
        
        # Verify
        service.field_mapping_service.generate_mappings_for_study.assert_called_once()


class TestPhase4Activation:
    @pytest.mark.asyncio
    async def test_activate_study(self, service, mock_study):
        # Mock database
        service.db = AsyncMock()
        mock_study.status = "SETUP"
        mock_study.is_active = False
        
        # Execute
        await service._phase4_activate_study(
            mock_study,
            service.db,
            Mock()
        )
        
        # Verify study was activated
        assert mock_study.status == "ACTIVE"
        assert mock_study.is_active == True
        assert mock_study.activated_at is not None


class TestFullInitialization:
    @pytest.mark.asyncio
    async def test_initialize_study_full_flow(self, service, mock_study, mock_template):
        # Mock all services
        service.db = AsyncMock()
        service.template_service = AsyncMock()
        service.file_conversion_service = AsyncMock()
        service.field_mapping_service = AsyncMock()
        service.websocket_manager = AsyncMock()
        
        # Setup mocks
        service.template_service.get_template = AsyncMock(return_value=mock_template)
        service.template_service.apply_template_to_study = AsyncMock(return_value=mock_study)
        service.file_conversion_service.convert_study_files = AsyncMock(
            return_value={"converted_files": 2}
        )
        service.field_mapping_service.generate_mappings_for_study = AsyncMock(
            return_value={"total_mappings": 2}
        )
        
        # Execute
        with patch('os.path.exists', return_value=True):
            with patch('os.listdir', return_value=['dm.sas7bdat']):
                result = await service.initialize_study(
                    mock_study.id,
                    "template123",
                    skip_data_upload=False
                )
        
        # Verify result
        assert result["status"] == "completed"
        assert result["study_id"] == mock_study.id
        assert "phases" in result
        
    @pytest.mark.asyncio
    async def test_initialize_study_with_failure(self, service, mock_study):
        # Mock services with failure
        service.db = AsyncMock()
        service.template_service = AsyncMock()
        service.template_service.apply_template_to_study = AsyncMock(
            side_effect=Exception("Template error")
        )
        
        # Execute
        result = await service.initialize_study(
            mock_study.id,
            "template123"
        )
        
        # Verify failure handling
        assert result["status"] == "failed"
        assert "error" in result
        assert "Template error" in result["error"]


class TestProgressTracking:
    @pytest.mark.asyncio
    async def test_progress_callback(self, service, mock_study):
        # Mock websocket manager
        service.websocket_manager = AsyncMock()
        
        # Create progress callback
        callback = service._create_progress_callback(mock_study.id, "test_step")
        
        # Test callback
        await callback(50, "Processing...")
        
        # Verify websocket broadcast
        service.websocket_manager.broadcast_to_study.assert_called_once()
        call_args = service.websocket_manager.broadcast_to_study.call_args
        assert call_args[0][0] == mock_study.id
        assert call_args[0][1]["type"] == "progress"
        assert call_args[0][1]["progress"] == 50