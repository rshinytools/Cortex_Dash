# ABOUTME: Integration tests for study initialization API endpoints
# ABOUTME: Tests the complete initialization flow through API

import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from sqlmodel import Session
import json
from io import BytesIO


@pytest.fixture
def mock_study():
    study = Mock()
    study.id = "study123"
    study.name = "Test Study"
    study.org_id = "org123"
    study.initialization_status = "not_started"
    return study


@pytest.fixture
def mock_template():
    template = Mock()
    template.id = "template123"
    template.name = "Safety Template"
    return template


class TestInitializationEndpoints:
    def test_initialize_study(self, client: TestClient, mock_study, mock_template):
        # Mock dependencies
        with patch('app.api.v1.endpoints.study_initialization.get_study_by_id') as mock_get_study:
            with patch('app.api.v1.endpoints.study_initialization.StudyInitializationService') as mock_service:
                mock_get_study.return_value = mock_study
                mock_service_instance = mock_service.return_value
                mock_service_instance.initialize_study = AsyncMock(
                    return_value={"task_id": "task123", "status": "queued"}
                )
                
                # Make request
                response = client.post(
                    f"/api/v1/studies/{mock_study.id}/initialize",
                    json={
                        "template_id": "template123",
                        "skip_data_upload": False
                    }
                )
                
                # Verify
                assert response.status_code == 200
                data = response.json()
                assert data["task_id"] == "task123"
                assert data["status"] == "queued"
                
    def test_initialize_study_not_found(self, client: TestClient):
        with patch('app.api.v1.endpoints.study_initialization.get_study_by_id') as mock_get_study:
            mock_get_study.return_value = None
            
            response = client.post(
                "/api/v1/studies/nonexistent/initialize",
                json={"template_id": "template123"}
            )
            
            assert response.status_code == 404
            
    def test_get_initialization_status(self, client: TestClient, mock_study):
        mock_study.initialization_status = "in_progress"
        mock_study.initialization_progress = 50
        mock_study.initialization_steps = {
            "current_step": "data_conversion",
            "steps": {
                "template_application": {"status": "completed", "progress": 100},
                "data_upload": {"status": "completed", "progress": 100},
                "data_conversion": {"status": "in_progress", "progress": 50},
                "field_mapping": {"status": "pending", "progress": 0}
            }
        }
        
        with patch('app.api.v1.endpoints.study_initialization.get_study_by_id') as mock_get_study:
            mock_get_study.return_value = mock_study
            
            response = client.get(f"/api/v1/studies/{mock_study.id}/initialization/status")
            
            assert response.status_code == 200
            data = response.json()
            assert data["initialization_status"] == "in_progress"
            assert data["initialization_progress"] == 50
            assert "initialization_steps" in data


class TestDataUploadEndpoints:
    def test_upload_study_data(self, client: TestClient, mock_study):
        # Create test files
        files = [
            ("files", ("dm.csv", b"USUBJID,AGE\n001,25\n002,30", "text/csv")),
            ("files", ("ae.csv", b"USUBJID,AEDECOD\n001,HEADACHE", "text/csv"))
        ]
        
        with patch('app.api.v1.endpoints.study_initialization.get_study_by_id') as mock_get_study:
            with patch('app.api.v1.endpoints.study_initialization.handle_file_upload') as mock_upload:
                mock_get_study.return_value = mock_study
                mock_upload.return_value = {
                    "uploaded_files": ["dm.csv", "ae.csv"],
                    "total_size": 1024,
                    "total_files": 2
                }
                
                response = client.post(
                    f"/api/v1/studies/{mock_study.id}/data/upload",
                    files=files
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["total_files"] == 2
                assert len(data["uploaded_files"]) == 2
                
    def test_upload_invalid_file_type(self, client: TestClient, mock_study):
        files = [
            ("files", ("test.exe", b"binary data", "application/x-msdownload"))
        ]
        
        with patch('app.api.v1.endpoints.study_initialization.get_study_by_id') as mock_get_study:
            mock_get_study.return_value = mock_study
            
            response = client.post(
                f"/api/v1/studies/{mock_study.id}/data/upload",
                files=files
            )
            
            # Should reject invalid file types
            assert response.status_code in [400, 422]


class TestWizardEndpoints:
    def test_start_wizard(self, client: TestClient):
        with patch('app.api.v1.endpoints.study_wizard.WizardStateManager') as mock_manager:
            mock_instance = mock_manager.return_value
            mock_instance.create_session.return_value = {
                "session_id": "wizard123",
                "current_step": 1,
                "total_steps": 4,
                "state": {}
            }
            
            response = client.post("/api/v1/study-wizard/start")
            
            assert response.status_code == 200
            data = response.json()
            assert data["session_id"] == "wizard123"
            assert data["current_step"] == 1
            
    def test_submit_wizard_step(self, client: TestClient):
        session_id = "wizard123"
        step_data = {
            "step": 1,
            "data": {
                "study_name": "Test Study",
                "study_code": "TST001"
            }
        }
        
        with patch('app.api.v1.endpoints.study_wizard.WizardStateManager') as mock_manager:
            mock_instance = mock_manager.return_value
            mock_instance.update_step.return_value = {
                "session_id": session_id,
                "current_step": 2,
                "can_proceed": True
            }
            
            response = client.post(
                f"/api/v1/study-wizard/{session_id}/step",
                json=step_data
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["current_step"] == 2
            assert data["can_proceed"] == True
            
    def test_complete_wizard(self, client: TestClient, mock_study):
        session_id = "wizard123"
        
        with patch('app.api.v1.endpoints.study_wizard.WizardStateManager') as mock_manager:
            with patch('app.api.v1.endpoints.study_wizard.create_study_from_wizard') as mock_create:
                mock_instance = mock_manager.return_value
                mock_instance.get_session.return_value = {
                    "state": {
                        "study_info": {"name": "Test Study"},
                        "template_id": "template123",
                        "uploaded_files": ["dm.csv"]
                    }
                }
                mock_create.return_value = mock_study
                
                response = client.post(f"/api/v1/study-wizard/{session_id}/complete")
                
                assert response.status_code == 200
                data = response.json()
                assert data["study_id"] == mock_study.id


class TestRetryAndCancel:
    def test_retry_initialization(self, client: TestClient, mock_study):
        mock_study.initialization_status = "failed"
        
        with patch('app.api.v1.endpoints.study_initialization.get_study_by_id') as mock_get_study:
            with patch('app.api.v1.endpoints.study_initialization.StudyInitializationService') as mock_service:
                mock_get_study.return_value = mock_study
                mock_service_instance = mock_service.return_value
                mock_service_instance.retry_initialization = AsyncMock(
                    return_value={"task_id": "retry123", "status": "queued"}
                )
                
                response = client.post(f"/api/v1/studies/{mock_study.id}/initialization/retry")
                
                assert response.status_code == 200
                data = response.json()
                assert data["task_id"] == "retry123"
                
    def test_cancel_initialization(self, client: TestClient, mock_study):
        mock_study.initialization_status = "in_progress"
        
        with patch('app.api.v1.endpoints.study_initialization.get_study_by_id') as mock_get_study:
            with patch('app.api.v1.endpoints.study_initialization.cancel_study_initialization') as mock_cancel:
                mock_get_study.return_value = mock_study
                mock_cancel.return_value = {"status": "cancelled"}
                
                response = client.post(f"/api/v1/studies/{mock_study.id}/initialization/cancel")
                
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "cancelled"


class TestFieldMappingEndpoints:
    def test_get_field_mappings(self, client: TestClient, mock_study):
        with patch('app.api.v1.endpoints.study_initialization.get_study_by_id') as mock_get_study:
            with patch('app.api.v1.endpoints.study_initialization.get_study_field_mappings') as mock_mappings:
                mock_get_study.return_value = mock_study
                mock_mappings.return_value = [
                    {
                        "id": "mapping1",
                        "target_field": "USUBJID",
                        "source_field": "SUBJECT_ID",
                        "confidence_score": 0.9
                    }
                ]
                
                response = client.get(f"/api/v1/studies/{mock_study.id}/field-mappings")
                
                assert response.status_code == 200
                data = response.json()
                assert len(data) == 1
                assert data[0]["target_field"] == "USUBJID"
                
    def test_update_field_mapping(self, client: TestClient):
        mapping_id = "mapping123"
        update_data = {
            "source_field": "USUBJID",
            "is_mapped": True,
            "confidence_score": 1.0
        }
        
        with patch('app.api.v1.endpoints.study_initialization.update_field_mapping') as mock_update:
            mock_update.return_value = {
                "id": mapping_id,
                **update_data
            }
            
            response = client.put(
                f"/api/v1/field-mappings/{mapping_id}",
                json=update_data
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["source_field"] == "USUBJID"
            assert data["is_mapped"] == True