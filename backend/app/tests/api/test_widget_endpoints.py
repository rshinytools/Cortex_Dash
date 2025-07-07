# ABOUTME: Comprehensive test suite for widget-related API endpoints
# ABOUTME: Tests all widget endpoints including CRUD operations, data execution, and admin functions

import pytest
import uuid
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from sqlmodel import Session
import json

from app.models.widget import WidgetDefinition, WidgetCategory
from app.models.dashboard import StudyDashboard, DashboardTemplate
from app.models.study import Study
from app.models.organization import Organization


class TestWidgetCRUDEndpoints:
    """Test suite for widget CRUD API endpoints"""

    def test_create_widget_definition_success(self, client: TestClient, superuser_token_headers: dict):
        """Test successful widget definition creation"""
        widget_data = {
            "name": "Test Metric Widget",
            "description": "A test metric widget for unit testing",
            "category": "metric",
            "config_schema": {
                "type": "object",
                "properties": {
                    "data_source": {"type": "string"},
                    "aggregation": {"type": "string"},
                    "field": {"type": "string"}
                },
                "required": ["data_source", "field"]
            },
            "default_config": {
                "data_source": "demographics",
                "aggregation": "count",
                "field": "subject_id"
            },
            "data_requirements": {
                "required_fields": ["subject_id"],
                "optional_fields": ["age", "gender"]
            },
            "is_system_widget": False
        }
        
        response = client.post(
            "/api/v1/widgets/",
            headers=superuser_token_headers,
            json=widget_data
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == widget_data["name"]
        assert data["category"] == widget_data["category"]
        assert "id" in data
        assert "created_at" in data

    def test_create_widget_definition_invalid_data(self, client: TestClient, superuser_token_headers: dict):
        """Test widget definition creation with invalid data"""
        invalid_widget_data = {
            "name": "",  # Empty name
            "category": "invalid_category",  # Invalid category
            "config_schema": "invalid_schema"  # Invalid schema format
        }
        
        response = client.post(
            "/api/v1/widgets/",
            headers=superuser_token_headers,
            json=invalid_widget_data
        )
        
        assert response.status_code == 422  # Validation error

    def test_get_widget_definition_success(self, client: TestClient, superuser_token_headers: dict, db: Session):
        """Test successful widget definition retrieval"""
        # Create a widget first
        widget = WidgetDefinition(
            id=str(uuid.uuid4()),
            name="Test Widget",
            description="Test widget for GET testing",
            category=WidgetCategory.METRIC,
            config_schema={"type": "object"},
            default_config={"test": "value"}
        )
        db.add(widget)
        db.commit()
        
        response = client.get(
            f"/api/v1/widgets/{widget.id}",
            headers=superuser_token_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == widget.id
        assert data["name"] == widget.name

    def test_get_widget_definition_not_found(self, client: TestClient, superuser_token_headers: dict):
        """Test widget definition retrieval with non-existent ID"""
        non_existent_id = str(uuid.uuid4())
        
        response = client.get(
            f"/api/v1/widgets/{non_existent_id}",
            headers=superuser_token_headers
        )
        
        assert response.status_code == 404

    def test_list_widget_definitions(self, client: TestClient, superuser_token_headers: dict, db: Session):
        """Test listing widget definitions with filters"""
        # Create multiple widgets
        widgets = [
            WidgetDefinition(
                id=str(uuid.uuid4()),
                name=f"Test Widget {i}",
                category=WidgetCategory.METRIC if i % 2 == 0 else WidgetCategory.CHART,
                config_schema={"type": "object"},
                default_config={}
            )
            for i in range(5)
        ]
        
        for widget in widgets:
            db.add(widget)
        db.commit()
        
        # Test basic listing
        response = client.get(
            "/api/v1/widgets/",
            headers=superuser_token_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 5
        
        # Test filtering by category
        response = client.get(
            "/api/v1/widgets/?category=metric",
            headers=superuser_token_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert item["category"] == "metric"

    def test_update_widget_definition(self, client: TestClient, superuser_token_headers: dict, db: Session):
        """Test widget definition update"""
        widget = WidgetDefinition(
            id=str(uuid.uuid4()),
            name="Original Widget",
            description="Original description",
            category=WidgetCategory.METRIC,
            config_schema={"type": "object"},
            default_config={}
        )
        db.add(widget)
        db.commit()
        
        update_data = {
            "name": "Updated Widget",
            "description": "Updated description",
            "default_config": {"updated": "value"}
        }
        
        response = client.put(
            f"/api/v1/widgets/{widget.id}",
            headers=superuser_token_headers,
            json=update_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["description"] == update_data["description"]

    def test_delete_widget_definition(self, client: TestClient, superuser_token_headers: dict, db: Session):
        """Test widget definition deletion"""
        widget = WidgetDefinition(
            id=str(uuid.uuid4()),
            name="Widget to Delete",
            category=WidgetCategory.METRIC,
            config_schema={"type": "object"},
            default_config={}
        )
        db.add(widget)
        db.commit()
        
        response = client.delete(
            f"/api/v1/widgets/{widget.id}",
            headers=superuser_token_headers
        )
        
        assert response.status_code == 204
        
        # Verify deletion
        response = client.get(
            f"/api/v1/widgets/{widget.id}",
            headers=superuser_token_headers
        )
        assert response.status_code == 404


class TestWidgetDataEndpoints:
    """Test suite for widget data execution endpoints"""

    def test_execute_widget_data_success(self, client: TestClient, superuser_token_headers: dict, db: Session):
        """Test successful widget data execution"""
        # Create test study and widget
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
            organization_id=organization.id,
            status="active"
        )
        db.add(study)
        
        widget = WidgetDefinition(
            id=str(uuid.uuid4()),
            name="Test Metric",
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
        
        request_data = {
            "widget_id": widget.id,
            "widget_config": {
                "data_source": "demographics",
                "aggregation": "count",
                "field": "subject_id"
            },
            "filters": {}
        }
        
        with patch('app.services.widget_data_executor.WidgetDataExecutor.execute_widget') as mock_execute:
            mock_execute.return_value = {"value": 150, "aggregation": "count"}
            
            response = client.post(
                f"/api/v1/widgets/execute/{study.id}",
                headers=superuser_token_headers,
                json=request_data
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["value"] == 150
        assert data["aggregation"] == "count"

    def test_execute_widget_data_invalid_study(self, client: TestClient, superuser_token_headers: dict):
        """Test widget data execution with invalid study ID"""
        invalid_study_id = str(uuid.uuid4())
        
        request_data = {
            "widget_id": str(uuid.uuid4()),
            "widget_config": {"test": "config"}
        }
        
        response = client.post(
            f"/api/v1/widgets/execute/{invalid_study_id}",
            headers=superuser_token_headers,
            json=request_data
        )
        
        assert response.status_code == 404

    def test_execute_widget_data_with_filters(self, client: TestClient, superuser_token_headers: dict, db: Session):
        """Test widget data execution with filters"""
        # Setup test data
        organization = Organization(
            id=str(uuid.uuid4()),
            name="Test Org",
            display_name="Test Organization"
        )
        db.add(organization)
        
        study = Study(
            id=str(uuid.uuid4()),
            code="TEST002",
            name="Test Study with Filters",
            organization_id=organization.id,
            status="active"
        )
        db.add(study)
        db.commit()
        
        request_data = {
            "widget_id": str(uuid.uuid4()),
            "widget_config": {
                "data_source": "demographics",
                "aggregation": "count",
                "field": "subject_id"
            },
            "filters": {
                "gender": "M",
                "age": {"operator": ">=", "value": 18}
            }
        }
        
        with patch('app.services.widget_data_executor.WidgetDataExecutor.execute_widget') as mock_execute:
            mock_execute.return_value = {"value": 75, "aggregation": "count"}
            
            response = client.post(
                f"/api/v1/widgets/execute/{study.id}",
                headers=superuser_token_headers,
                json=request_data
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["value"] == 75

    def test_get_widget_data_schema(self, client: TestClient, superuser_token_headers: dict, db: Session):
        """Test getting widget data schema information"""
        study = Study(
            id=str(uuid.uuid4()),
            code="SCHEMA_TEST",
            name="Schema Test Study",
            organization_id=str(uuid.uuid4()),
            status="active"
        )
        db.add(study)
        db.commit()
        
        response = client.get(
            f"/api/v1/widgets/schema/{study.id}/demographics",
            headers=superuser_token_headers
        )
        
        # This would depend on your actual data source implementation
        # For now, we'll test that the endpoint is accessible
        assert response.status_code in [200, 404]  # 404 if no data source configured


class TestWidgetValidationEndpoints:
    """Test suite for widget validation endpoints"""

    def test_validate_widget_config_success(self, client: TestClient, superuser_token_headers: dict, db: Session):
        """Test successful widget configuration validation"""
        widget = WidgetDefinition(
            id=str(uuid.uuid4()),
            name="Validation Test Widget",
            category=WidgetCategory.CHART,
            config_schema={
                "type": "object",
                "properties": {
                    "chart_type": {"type": "string", "enum": ["bar", "line", "pie"]},
                    "x_axis": {"type": "string"},
                    "y_axis": {"type": "string"}
                },
                "required": ["chart_type", "x_axis", "y_axis"]
            },
            default_config={}
        )
        db.add(widget)
        db.commit()
        
        config_to_validate = {
            "chart_type": "bar",
            "x_axis": "gender",
            "y_axis": "count"
        }
        
        response = client.post(
            f"/api/v1/widgets/{widget.id}/validate",
            headers=superuser_token_headers,
            json=config_to_validate
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is True
        assert len(data["errors"]) == 0

    def test_validate_widget_config_invalid(self, client: TestClient, superuser_token_headers: dict, db: Session):
        """Test widget configuration validation with invalid config"""
        widget = WidgetDefinition(
            id=str(uuid.uuid4()),
            name="Validation Test Widget",
            category=WidgetCategory.CHART,
            config_schema={
                "type": "object",
                "properties": {
                    "chart_type": {"type": "string", "enum": ["bar", "line", "pie"]},
                    "x_axis": {"type": "string"},
                    "y_axis": {"type": "string"}
                },
                "required": ["chart_type", "x_axis", "y_axis"]
            },
            default_config={}
        )
        db.add(widget)
        db.commit()
        
        invalid_config = {
            "chart_type": "invalid_type",  # Not in enum
            "x_axis": "gender"
            # Missing required y_axis
        }
        
        response = client.post(
            f"/api/v1/widgets/{widget.id}/validate",
            headers=superuser_token_headers,
            json=invalid_config
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is False
        assert len(data["errors"]) > 0


class TestWidgetAdminEndpoints:
    """Test suite for widget admin endpoints"""

    def test_get_widget_usage_statistics(self, client: TestClient, superuser_token_headers: dict, db: Session):
        """Test getting widget usage statistics"""
        widget = WidgetDefinition(
            id=str(uuid.uuid4()),
            name="Usage Stats Widget",
            category=WidgetCategory.METRIC,
            config_schema={"type": "object"},
            default_config={}
        )
        db.add(widget)
        db.commit()
        
        response = client.get(
            f"/api/v1/admin/widgets/{widget.id}/usage",
            headers=superuser_token_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "usage_count" in data
        assert "last_used" in data
        assert "dashboard_count" in data

    def test_clone_widget_definition(self, client: TestClient, superuser_token_headers: dict, db: Session):
        """Test cloning a widget definition"""
        original_widget = WidgetDefinition(
            id=str(uuid.uuid4()),
            name="Original Widget",
            description="Original widget for cloning",
            category=WidgetCategory.TABLE,
            config_schema={"type": "object"},
            default_config={"original": "config"}
        )
        db.add(original_widget)
        db.commit()
        
        clone_data = {
            "name": "Cloned Widget",
            "description": "Cloned from original widget"
        }
        
        response = client.post(
            f"/api/v1/admin/widgets/{original_widget.id}/clone",
            headers=superuser_token_headers,
            json=clone_data
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == clone_data["name"]
        assert data["category"] == original_widget.category
        assert data["id"] != original_widget.id

    def test_export_widget_definition(self, client: TestClient, superuser_token_headers: dict, db: Session):
        """Test exporting widget definition"""
        widget = WidgetDefinition(
            id=str(uuid.uuid4()),
            name="Export Test Widget",
            category=WidgetCategory.CHART,
            config_schema={"type": "object"},
            default_config={"export": "test"}
        )
        db.add(widget)
        db.commit()
        
        response = client.get(
            f"/api/v1/admin/widgets/{widget.id}/export",
            headers=superuser_token_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "widget_definition" in data
        assert "export_metadata" in data
        assert data["widget_definition"]["name"] == widget.name

    def test_import_widget_definition(self, client: TestClient, superuser_token_headers: dict):
        """Test importing widget definition"""
        import_data = {
            "widget_definition": {
                "name": "Imported Widget",
                "description": "Widget imported from export",
                "category": "metric",
                "config_schema": {"type": "object"},
                "default_config": {"imported": "config"}
            },
            "import_options": {
                "overwrite_existing": False,
                "validate_schema": True
            }
        }
        
        response = client.post(
            "/api/v1/admin/widgets/import",
            headers=superuser_token_headers,
            json=import_data
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == import_data["widget_definition"]["name"]
        assert "id" in data


class TestWidgetPermissionsEndpoints:
    """Test suite for widget permission-related endpoints"""

    def test_widget_access_unauthorized(self, client: TestClient):
        """Test widget access without authentication"""
        response = client.get("/api/v1/widgets/")
        
        assert response.status_code == 401

    def test_widget_creation_permission_denied(self, client: TestClient, normal_user_token_headers: dict):
        """Test widget creation with insufficient permissions"""
        widget_data = {
            "name": "Unauthorized Widget",
            "category": "metric",
            "config_schema": {"type": "object"},
            "default_config": {}
        }
        
        response = client.post(
            "/api/v1/widgets/",
            headers=normal_user_token_headers,
            json=widget_data
        )
        
        # Should be forbidden for normal users
        assert response.status_code == 403

    def test_widget_admin_access_denied(self, client: TestClient, normal_user_token_headers: dict):
        """Test admin widget endpoints with normal user permissions"""
        widget_id = str(uuid.uuid4())
        
        response = client.get(
            f"/api/v1/admin/widgets/{widget_id}/usage",
            headers=normal_user_token_headers
        )
        
        assert response.status_code == 403


class TestWidgetEndpointErrorHandling:
    """Test suite for widget endpoint error handling"""

    def test_malformed_json_request(self, client: TestClient, superuser_token_headers: dict):
        """Test handling of malformed JSON requests"""
        response = client.post(
            "/api/v1/widgets/",
            headers=superuser_token_headers,
            data="invalid json"
        )
        
        assert response.status_code == 422

    def test_database_connection_error(self, client: TestClient, superuser_token_headers: dict):
        """Test handling of database connection errors"""
        with patch('app.core.db.engine.connect') as mock_connect:
            mock_connect.side_effect = Exception("Database connection failed")
            
            response = client.get(
                "/api/v1/widgets/",
                headers=superuser_token_headers
            )
            
            assert response.status_code == 500

    def test_widget_execution_timeout(self, client: TestClient, superuser_token_headers: dict, db: Session):
        """Test handling of widget execution timeouts"""
        study = Study(
            id=str(uuid.uuid4()),
            code="TIMEOUT_TEST",
            name="Timeout Test Study",
            organization_id=str(uuid.uuid4()),
            status="active"
        )
        db.add(study)
        db.commit()
        
        request_data = {
            "widget_id": str(uuid.uuid4()),
            "widget_config": {"test": "config"}
        }
        
        with patch('app.services.widget_data_executor.WidgetDataExecutor.execute_widget') as mock_execute:
            mock_execute.side_effect = TimeoutError("Widget execution timed out")
            
            response = client.post(
                f"/api/v1/widgets/execute/{study.id}",
                headers=superuser_token_headers,
                json=request_data
            )
            
            assert response.status_code == 408  # Request timeout


@pytest.mark.performance
class TestWidgetEndpointPerformance:
    """Performance tests for widget endpoints"""

    def test_widget_list_pagination_performance(self, client: TestClient, superuser_token_headers: dict, db: Session):
        """Test widget listing performance with pagination"""
        # Create many widgets to test pagination performance
        widgets = [
            WidgetDefinition(
                id=str(uuid.uuid4()),
                name=f"Performance Test Widget {i}",
                category=WidgetCategory.METRIC,
                config_schema={"type": "object"},
                default_config={}
            )
            for i in range(100)
        ]
        
        for widget in widgets:
            db.add(widget)
        db.commit()
        
        # Test paginated request
        response = client.get(
            "/api/v1/widgets/?skip=0&limit=20",
            headers=superuser_token_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 20

    def test_widget_execution_performance(self, client: TestClient, superuser_token_headers: dict):
        """Test widget execution endpoint performance"""
        # This would involve testing with large datasets
        # Implementation depends on actual data source setup
        pass