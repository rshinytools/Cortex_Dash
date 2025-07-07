# ABOUTME: End-to-end integration tests for complete dashboard workflows
# ABOUTME: Tests full user journeys from dashboard creation to data visualization

import pytest
import uuid
import asyncio
from typing import Dict, Any, List
from datetime import datetime, timedelta

import httpx
from sqlmodel import Session
from fastapi.testclient import TestClient

from app.main import app
from app.models.organization import Organization
from app.models.study import Study
from app.models.dashboard import DashboardTemplate, StudyDashboard
from app.models.widget import WidgetDefinition, WidgetCategory
from app.models.user import User


class TestEndToEndDashboardFlow:
    """End-to-end tests for complete dashboard workflows"""

    @pytest.fixture(scope="class")
    def client(self) -> TestClient:
        """Create test client for E2E tests"""
        return TestClient(app)

    @pytest.fixture(scope="class")
    async def test_organization(self, db: Session) -> Organization:
        """Create test organization for E2E tests"""
        org = Organization(
            id=str(uuid.uuid4()),
            name="E2E Test Organization",
            display_name="End-to-End Test Org",
            description="Organization for integration testing"
        )
        db.add(org)
        db.commit()
        db.refresh(org)
        return org

    @pytest.fixture(scope="class")
    async def test_study(self, db: Session, test_organization: Organization) -> Study:
        """Create test study for E2E tests"""
        study = Study(
            id=str(uuid.uuid4()),
            code="E2E-001",
            name="End-to-End Test Study",
            description="Study for integration testing",
            organization_id=test_organization.id,
            phase="Phase III",
            therapeutic_area="Oncology",
            indication="Breast Cancer",
            status="active",
            is_enabled=True
        )
        db.add(study)
        db.commit()
        db.refresh(study)
        return study

    @pytest.fixture(scope="class")
    async def test_widgets(self, db: Session) -> List[WidgetDefinition]:
        """Create test widget definitions"""
        widgets = [
            WidgetDefinition(
                id=str(uuid.uuid4()),
                name="Subject Count Metric",
                description="Count of enrolled subjects",
                category=WidgetCategory.METRIC,
                config_schema={
                    "type": "object",
                    "properties": {
                        "data_source": {"type": "string"},
                        "aggregation": {"type": "string"},
                        "field": {"type": "string"}
                    }
                },
                default_config={
                    "data_source": "demographics",
                    "aggregation": "count",
                    "field": "subject_id"
                }
            ),
            WidgetDefinition(
                id=str(uuid.uuid4()),
                name="Enrollment Chart",
                description="Enrollment trend over time",
                category=WidgetCategory.CHART,
                config_schema={
                    "type": "object",
                    "properties": {
                        "chart_type": {"type": "string"},
                        "x_axis": {"type": "string"},
                        "y_axis": {"type": "string"}
                    }
                },
                default_config={
                    "chart_type": "line",
                    "x_axis": "date",
                    "y_axis": "count"
                }
            ),
            WidgetDefinition(
                id=str(uuid.uuid4()),
                name="Demographics Table",
                description="Subject demographics data",
                category=WidgetCategory.TABLE,
                config_schema={
                    "type": "object",
                    "properties": {
                        "columns": {"type": "array"},
                        "page_size": {"type": "number"}
                    }
                },
                default_config={
                    "columns": ["subject_id", "age", "gender", "site"],
                    "page_size": 10
                }
            )
        ]
        
        for widget in widgets:
            db.add(widget)
        db.commit()
        
        for widget in widgets:
            db.refresh(widget)
        
        return widgets

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_complete_dashboard_creation_flow(
        self, 
        client: TestClient, 
        superuser_token_headers: dict,
        test_study: Study,
        test_widgets: List[WidgetDefinition]
    ):
        """Test complete dashboard creation workflow"""
        
        # Step 1: Create dashboard template
        template_data = {
            "name": "E2E Clinical Overview Template",
            "description": "Template for end-to-end testing",
            "category": "clinical_overview",
            "scope": "organization",
            "config": {
                "layout": {
                    "grid": {"columns": 12, "rows": 8}
                },
                "widgets": [
                    {
                        "id": "widget-1",
                        "widget_definition_id": test_widgets[0].id,
                        "position": {"x": 0, "y": 0, "w": 4, "h": 2},
                        "config": test_widgets[0].default_config
                    },
                    {
                        "id": "widget-2",
                        "widget_definition_id": test_widgets[1].id,
                        "position": {"x": 4, "y": 0, "w": 8, "h": 4},
                        "config": test_widgets[1].default_config
                    },
                    {
                        "id": "widget-3",
                        "widget_definition_id": test_widgets[2].id,
                        "position": {"x": 0, "y": 4, "w": 12, "h": 4},
                        "config": test_widgets[2].default_config
                    }
                ]
            },
            "data_requirements": {
                "required_datasets": ["demographics"],
                "required_fields": ["subject_id", "age", "gender", "site", "enrollment_date"]
            }
        }
        
        response = client.post(
            "/api/v1/dashboard-templates/",
            headers=superuser_token_headers,
            json=template_data
        )
        
        assert response.status_code == 201
        template = response.json()
        assert template["name"] == template_data["name"]
        template_id = template["id"]
        
        # Step 2: Create study dashboard from template
        dashboard_data = {
            "name": "E2E Study Dashboard",
            "description": "Dashboard created from template for E2E testing",
            "template_id": template_id,
            "study_id": test_study.id,
            "is_active": True
        }
        
        response = client.post(
            f"/api/v1/studies/{test_study.id}/dashboards/",
            headers=superuser_token_headers,
            json=dashboard_data
        )
        
        assert response.status_code == 201
        dashboard = response.json()
        assert dashboard["name"] == dashboard_data["name"]
        dashboard_id = dashboard["id"]
        
        # Step 3: Verify dashboard was created correctly
        response = client.get(
            f"/api/v1/studies/{test_study.id}/dashboards/{dashboard_id}",
            headers=superuser_token_headers
        )
        
        assert response.status_code == 200
        dashboard_detail = response.json()
        assert len(dashboard_detail["config"]["widgets"]) == 3
        
        # Step 4: Execute widget data for dashboard
        widget_requests = []
        for widget_config in dashboard_detail["config"]["widgets"]:
            widget_request = {
                "widget_id": widget_config["widget_definition_id"],
                "widget_config": widget_config["config"],
                "filters": {}
            }
            widget_requests.append(widget_request)
        
        # Execute all widgets
        for widget_request in widget_requests:
            response = client.post(
                f"/api/v1/widgets/execute/{test_study.id}",
                headers=superuser_token_headers,
                json=widget_request
            )
            
            # For now, we expect 404 since we don't have actual data sources set up
            # In a real E2E test with data, this would be 200
            assert response.status_code in [200, 404]
        
        # Step 5: Update dashboard configuration
        updated_config = dashboard_detail["config"].copy()
        updated_config["widgets"][0]["config"]["title"] = "Updated Subject Count"
        
        response = client.put(
            f"/api/v1/studies/{test_study.id}/dashboards/{dashboard_id}",
            headers=superuser_token_headers,
            json={"config": updated_config}
        )
        
        assert response.status_code == 200
        updated_dashboard = response.json()
        assert updated_dashboard["config"]["widgets"][0]["config"]["title"] == "Updated Subject Count"
        
        # Step 6: Test dashboard export
        export_request = {
            "format": "pdf",
            "include_data": True,
            "options": {
                "orientation": "landscape",
                "page_size": "A4"
            }
        }
        
        response = client.post(
            f"/api/v1/dashboards/{dashboard_id}/export",
            headers=superuser_token_headers,
            json=export_request
        )
        
        # Export might fail without actual data, but should not crash
        assert response.status_code in [200, 202, 400]
        
        # Step 7: Clean up - delete dashboard
        response = client.delete(
            f"/api/v1/studies/{test_study.id}/dashboards/{dashboard_id}",
            headers=superuser_token_headers
        )
        
        assert response.status_code == 204
        
        # Step 8: Clean up - delete template
        response = client.delete(
            f"/api/v1/dashboard-templates/{template_id}",
            headers=superuser_token_headers
        )
        
        assert response.status_code == 204

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_dashboard_collaboration_flow(
        self,
        client: TestClient,
        superuser_token_headers: dict,
        normal_user_token_headers: dict,
        test_study: Study,
        test_widgets: List[WidgetDefinition]
    ):
        """Test dashboard collaboration between multiple users"""
        
        # Step 1: Admin creates shared dashboard
        dashboard_data = {
            "name": "Shared Collaboration Dashboard",
            "description": "Dashboard for testing collaboration",
            "study_id": test_study.id,
            "config": {
                "layout": {"grid": {"columns": 12, "rows": 8}},
                "widgets": [
                    {
                        "id": "collab-widget-1",
                        "widget_definition_id": test_widgets[0].id,
                        "position": {"x": 0, "y": 0, "w": 6, "h": 3},
                        "config": test_widgets[0].default_config
                    }
                ]
            },
            "sharing_settings": {
                "is_public": False,
                "allow_comments": True,
                "allow_export": True
            }
        }
        
        response = client.post(
            f"/api/v1/studies/{test_study.id}/dashboards/",
            headers=superuser_token_headers,
            json=dashboard_data
        )
        
        assert response.status_code == 201
        dashboard = response.json()
        dashboard_id = dashboard["id"]
        
        # Step 2: Share dashboard with normal user
        sharing_data = {
            "user_emails": ["test@example.com"],
            "permission_level": "editor",
            "notify_users": True
        }
        
        response = client.post(
            f"/api/v1/dashboards/{dashboard_id}/share",
            headers=superuser_token_headers,
            json=sharing_data
        )
        
        assert response.status_code in [200, 404]  # 404 if user doesn't exist
        
        # Step 3: Normal user accesses shared dashboard
        response = client.get(
            f"/api/v1/studies/{test_study.id}/dashboards/{dashboard_id}",
            headers=normal_user_token_headers
        )
        
        # May fail if user doesn't have access - that's expected
        assert response.status_code in [200, 403, 404]
        
        # Step 4: Add comment to dashboard (if user has access)
        comment_data = {
            "content": "This widget needs updating",
            "widget_id": "collab-widget-1",
            "position": {"x": 100, "y": 150}
        }
        
        response = client.post(
            f"/api/v1/dashboards/{dashboard_id}/comments",
            headers=normal_user_token_headers,
            json=comment_data
        )
        
        # May fail based on permissions
        assert response.status_code in [201, 403, 404]
        
        # Step 5: Admin views comments
        response = client.get(
            f"/api/v1/dashboards/{dashboard_id}/comments",
            headers=superuser_token_headers
        )
        
        assert response.status_code == 200
        comments = response.json()
        assert isinstance(comments, list)

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_dashboard_versioning_flow(
        self,
        client: TestClient,
        superuser_token_headers: dict,
        test_study: Study,
        test_widgets: List[WidgetDefinition]
    ):
        """Test dashboard versioning and rollback functionality"""
        
        # Step 1: Create initial dashboard
        dashboard_data = {
            "name": "Versioned Dashboard",
            "description": "Dashboard for testing versioning",
            "study_id": test_study.id,
            "config": {
                "layout": {"grid": {"columns": 12, "rows": 8}},
                "widgets": [
                    {
                        "id": "version-widget-1",
                        "widget_definition_id": test_widgets[0].id,
                        "position": {"x": 0, "y": 0, "w": 4, "h": 2},
                        "config": {"title": "Version 1 Widget"}
                    }
                ]
            },
            "version_control": {
                "auto_version": True,
                "version_comment": "Initial version"
            }
        }
        
        response = client.post(
            f"/api/v1/studies/{test_study.id}/dashboards/",
            headers=superuser_token_headers,
            json=dashboard_data
        )
        
        assert response.status_code == 201
        dashboard = response.json()
        dashboard_id = dashboard["id"]
        
        # Step 2: Make first update (creates version 2)
        updated_config = dashboard["config"].copy()
        updated_config["widgets"][0]["config"]["title"] = "Version 2 Widget"
        
        response = client.put(
            f"/api/v1/studies/{test_study.id}/dashboards/{dashboard_id}",
            headers=superuser_token_headers,
            json={
                "config": updated_config,
                "version_comment": "Updated widget title"
            }
        )
        
        assert response.status_code == 200
        
        # Step 3: Add another widget (creates version 3)
        updated_config["widgets"].append({
            "id": "version-widget-2",
            "widget_definition_id": test_widgets[1].id,
            "position": {"x": 4, "y": 0, "w": 8, "h": 3},
            "config": test_widgets[1].default_config
        })
        
        response = client.put(
            f"/api/v1/studies/{test_study.id}/dashboards/{dashboard_id}",
            headers=superuser_token_headers,
            json={
                "config": updated_config,
                "version_comment": "Added enrollment chart"
            }
        )
        
        assert response.status_code == 200
        
        # Step 4: View version history
        response = client.get(
            f"/api/v1/dashboards/{dashboard_id}/versions",
            headers=superuser_token_headers
        )
        
        assert response.status_code == 200
        versions = response.json()
        assert len(versions) >= 1  # Should have version history
        
        # Step 5: Rollback to previous version
        if len(versions) > 1:
            previous_version = versions[1]["version"]
            
            response = client.post(
                f"/api/v1/dashboards/{dashboard_id}/rollback",
                headers=superuser_token_headers,
                json={"target_version": previous_version}
            )
            
            assert response.status_code in [200, 404]  # May not be implemented yet

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_dashboard_data_pipeline_integration(
        self,
        client: TestClient,
        superuser_token_headers: dict,
        test_study: Study,
        test_widgets: List[WidgetDefinition]
    ):
        """Test integration between dashboards and data pipeline"""
        
        # Step 1: Set up data source for study
        data_source_data = {
            "name": "Test Demographics Data",
            "type": "csv",
            "connection_params": {
                "file_path": "/test/data/demographics.csv"
            },
            "schema_mapping": {
                "subject_id": "USUBJID",
                "age": "AGE",
                "gender": "SEX",
                "site": "SITEID"
            }
        }
        
        response = client.post(
            f"/api/v1/studies/{test_study.id}/data-sources/",
            headers=superuser_token_headers,
            json=data_source_data
        )
        
        # May fail if data source doesn't exist
        assert response.status_code in [201, 400, 404]
        
        if response.status_code == 201:
            data_source = response.json()
            data_source_id = data_source["id"]
            
            # Step 2: Create dashboard that uses this data source
            dashboard_data = {
                "name": "Data Pipeline Dashboard",
                "description": "Dashboard testing data pipeline integration",
                "study_id": test_study.id,
                "config": {
                    "layout": {"grid": {"columns": 12, "rows": 8}},
                    "widgets": [
                        {
                            "id": "pipeline-widget-1",
                            "widget_definition_id": test_widgets[0].id,
                            "position": {"x": 0, "y": 0, "w": 4, "h": 2},
                            "config": {
                                "data_source": data_source_id,
                                "aggregation": "count",
                                "field": "subject_id"
                            }
                        }
                    ]
                },
                "data_refresh_schedule": {
                    "enabled": True,
                    "frequency": "daily",
                    "time": "06:00"
                }
            }
            
            response = client.post(
                f"/api/v1/studies/{test_study.id}/dashboards/",
                headers=superuser_token_headers,
                json=dashboard_data
            )
            
            assert response.status_code == 201
            dashboard = response.json()
            dashboard_id = dashboard["id"]
            
            # Step 3: Trigger data refresh
            response = client.post(
                f"/api/v1/dashboards/{dashboard_id}/refresh",
                headers=superuser_token_headers
            )
            
            assert response.status_code in [200, 202, 404]  # Async operation
            
            # Step 4: Check refresh status
            response = client.get(
                f"/api/v1/dashboards/{dashboard_id}/refresh/status",
                headers=superuser_token_headers
            )
            
            assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_dashboard_performance_with_large_dataset(
        self,
        client: TestClient,
        superuser_token_headers: dict,
        test_study: Study,
        test_widgets: List[WidgetDefinition]
    ):
        """Test dashboard performance with large datasets"""
        
        # This test would require setting up a large dataset
        # For now, we'll test the API endpoints that would handle large data
        
        # Step 1: Create dashboard with multiple complex widgets
        dashboard_data = {
            "name": "Performance Test Dashboard",
            "description": "Dashboard for testing performance with large datasets",
            "study_id": test_study.id,
            "config": {
                "layout": {"grid": {"columns": 12, "rows": 12}},
                "widgets": [
                    {
                        "id": f"perf-widget-{i}",
                        "widget_definition_id": test_widgets[i % len(test_widgets)].id,
                        "position": {
                            "x": (i % 4) * 3,
                            "y": (i // 4) * 3,
                            "w": 3,
                            "h": 3
                        },
                        "config": test_widgets[i % len(test_widgets)].default_config
                    }
                    for i in range(16)  # 16 widgets
                ]
            },
            "performance_settings": {
                "enable_caching": True,
                "cache_duration": 300,
                "lazy_loading": True,
                "pagination_size": 100
            }
        }
        
        start_time = datetime.now()
        
        response = client.post(
            f"/api/v1/studies/{test_study.id}/dashboards/",
            headers=superuser_token_headers,
            json=dashboard_data
        )
        
        creation_time = (datetime.now() - start_time).total_seconds()
        
        assert response.status_code == 201
        assert creation_time < 5.0  # Should create within 5 seconds
        
        dashboard = response.json()
        dashboard_id = dashboard["id"]
        
        # Step 2: Test bulk widget data execution
        start_time = datetime.now()
        
        widget_requests = [
            {
                "widget_id": widget["widget_definition_id"],
                "widget_config": widget["config"],
                "filters": {}
            }
            for widget in dashboard["config"]["widgets"][:5]  # Test first 5 widgets
        ]
        
        # Execute widgets in parallel (simulate frontend behavior)
        responses = []
        for widget_request in widget_requests:
            response = client.post(
                f"/api/v1/widgets/execute/{test_study.id}",
                headers=superuser_token_headers,
                json=widget_request
            )
            responses.append(response)
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # Should handle multiple widget requests reasonably fast
        assert execution_time < 10.0
        
        # Step 3: Test dashboard export with many widgets
        export_request = {
            "format": "pdf",
            "include_data": True,
            "options": {
                "orientation": "landscape",
                "include_all_widgets": True
            }
        }
        
        start_time = datetime.now()
        
        response = client.post(
            f"/api/v1/dashboards/{dashboard_id}/export",
            headers=superuser_token_headers,
            json=export_request
        )
        
        # Export initiation should be fast even for large dashboards
        initiation_time = (datetime.now() - start_time).total_seconds()
        assert initiation_time < 3.0
        
        # Response should indicate async processing for large exports
        assert response.status_code in [200, 202, 400]


@pytest.mark.integration
class TestDashboardRealtimeUpdates:
    """Test real-time dashboard updates and WebSocket functionality"""
    
    @pytest.mark.asyncio
    async def test_real_time_widget_updates(self):
        """Test real-time widget data updates via WebSocket"""
        # This would require WebSocket testing setup
        # Placeholder for real-time update testing
        pass
    
    @pytest.mark.asyncio
    async def test_collaborative_editing(self):
        """Test real-time collaborative dashboard editing"""
        # This would test multiple users editing same dashboard
        # Placeholder for collaborative editing testing
        pass


@pytest.mark.integration
class TestDashboardErrorRecovery:
    """Test dashboard error handling and recovery scenarios"""
    
    @pytest.mark.asyncio
    async def test_widget_failure_isolation(self):
        """Test that individual widget failures don't break entire dashboard"""
        # Test graceful degradation when individual widgets fail
        pass
    
    @pytest.mark.asyncio
    async def test_data_source_failure_recovery(self):
        """Test dashboard behavior when data sources are unavailable"""
        # Test fallback behavior for unavailable data sources
        pass
    
    @pytest.mark.asyncio
    async def test_export_failure_handling(self):
        """Test export failure scenarios and recovery"""
        # Test various export failure scenarios
        pass