# ABOUTME: Comprehensive test suite for Phase 1 widget architecture
# ABOUTME: Tests database schema, models, APIs, and widget contracts

import pytest
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List
import json
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, SQLModel

# Test configuration
TEST_DATABASE_URL = "postgresql://postgres:changethis@localhost:5432/test_clinical_dashboard"


class TestPhase1DatabaseSchema:
    """Test Phase 1 database schema and migrations"""
    
    def test_widget_definitions_data_contract(self, db_session):
        """Test data_contract column in widget_definitions"""
        from app.models import WidgetDefinition
        
        # Create widget with data contract
        contract = {
            "granularity": "subject_level",
            "required_fields": ["subject_id", "value"],
            "supported_aggregations": ["count", "sum", "avg"],
            "cache_ttl": 1800
        }
        
        widget = WidgetDefinition(
            code="test_metric",
            name="Test Metric",
            category="metrics",
            config_schema={"type": "object"},
            data_contract=contract,
            cache_ttl=1800
        )
        
        db_session.add(widget)
        db_session.commit()
        
        # Verify data contract is stored correctly
        saved_widget = db_session.get(WidgetDefinition, widget.id)
        assert saved_widget.data_contract == contract
        assert saved_widget.cache_ttl == 1800
    
    def test_dataset_metadata_table(self, db_session):
        """Test dataset_metadata table creation and fields"""
        from app.models.phase1_models import DatasetMetadata
        
        metadata = DatasetMetadata(
            study_id=uuid.uuid4(),
            filename="demographics.csv",
            file_type="csv",
            file_size=1024000,
            row_count=500,
            column_metadata={
                "columns": [
                    {"name": "SUBJID", "type": "string", "unique": True},
                    {"name": "AGE", "type": "integer", "min": 18, "max": 85}
                ]
            },
            granularity="subject_level",
            data_quality_score=0.95
        )
        
        db_session.add(metadata)
        db_session.commit()
        
        assert metadata.id is not None
        assert metadata.upload_date is not None
    
    def test_study_data_mappings_table(self, db_session):
        """Test study_data_mappings table with relationships"""
        from app.models.phase1_models import StudyDataMapping
        
        mapping = StudyDataMapping(
            study_id=uuid.uuid4(),
            widget_id=uuid.uuid4(),
            dataset_id=uuid.uuid4(),
            field_mappings={
                "subject_id": {"source_field": "SUBJID"},
                "enrollment_date": {"source_field": "ENROLL_DT", "transform": "to_date"}
            },
            join_config={
                "type": "left",
                "secondary_dataset": "adverse_events",
                "join_keys": {"primary": "SUBJID", "secondary": "SUBJECT_ID"}
            },
            cache_override=7200
        )
        
        db_session.add(mapping)
        db_session.commit()
        
        assert mapping.id is not None
        assert mapping.created_at is not None
    
    def test_widget_mapping_templates(self, db_session):
        """Test widget_mapping_templates table"""
        from app.models.phase1_models import WidgetMappingTemplate
        
        template = WidgetMappingTemplate(
            name="Standard EDC Enrollment",
            widget_type="kpi_metric_card",
            edc_system="medidata_rave",
            field_patterns={
                "subject_id": ["SUBJID", "SUBJECT_ID", "USUBJID"],
                "dates": ["*DT", "*DTC", "*_DATE"]
            },
            default_mappings={
                "subject_id": "SUBJID",
                "enrollment_date": "ENROLL_DT"
            }
        )
        
        db_session.add(template)
        db_session.commit()
        
        assert template.id is not None
        assert template.usage_count == 0
    
    def test_query_cache_table(self, db_session):
        """Test query_cache table and expiration"""
        from app.models.phase1_models import QueryCache
        
        cache_entry = QueryCache(
            cache_key="study_123_widget_456_hash_789",
            study_id=uuid.uuid4(),
            widget_id=uuid.uuid4(),
            query_hash="abc123def456",
            result_data={"total": 150, "data": [1, 2, 3]},
            result_count=150,
            execution_time_ms=234,
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        
        db_session.add(cache_entry)
        db_session.commit()
        
        assert cache_entry.hit_count == 0
        assert cache_entry.created_at is not None


class TestPhase1WidgetContracts:
    """Test widget data contracts for 5 core widgets"""
    
    def test_kpi_metric_card_contract(self):
        """Test KPI Metric Card data contract"""
        from app.models.phase1_models import KPIMetricCardContract
        
        contract = KPIMetricCardContract()
        
        assert contract.granularity == "subject_level"
        assert len(contract.required_fields) == 1
        assert contract.required_fields[0]["name"] == "measure_field"
        assert "COUNT" in contract.supported_aggregations
        assert "COUNT_DISTINCT" in contract.supported_aggregations
        assert contract.supports_grouping is True
        assert contract.supports_joins is False
        assert contract.recommended_cache_ttl == 1800
    
    def test_time_series_chart_contract(self):
        """Test Time Series Chart data contract"""
        from app.models.phase1_models import TimeSeriesChartContract
        
        contract = TimeSeriesChartContract()
        
        assert contract.granularity == "record_level"
        assert len(contract.required_fields) == 2
        assert any(f["name"] == "date_field" for f in contract.required_fields)
        assert any(f["name"] == "value_field" for f in contract.required_fields)
        assert contract.supports_joins is True
        assert contract.max_join_datasets == 2
        assert "day" in contract.grouping_fields
        assert "month" in contract.grouping_fields
    
    def test_distribution_chart_contract(self):
        """Test Distribution Chart data contract"""
        from app.models.phase1_models import DistributionChartContract
        
        contract = DistributionChartContract()
        
        assert contract.granularity == "record_level"
        assert len(contract.required_fields) == 2
        assert any(f["name"] == "category_field" for f in contract.required_fields)
        assert any(f["name"] == "value_field" for f in contract.required_fields)
        assert "PERCENTILE" in contract.supported_aggregations
        assert contract.supports_grouping is True
    
    def test_data_table_contract(self):
        """Test Data Table data contract"""
        from app.models.phase1_models import DataTableContract
        
        contract = DataTableContract()
        
        assert contract.granularity == "record_level"
        assert contract.supports_pagination is True
        assert contract.max_result_rows == 10000
        assert contract.supports_joins is True
        assert contract.max_join_datasets == 3
    
    def test_subject_timeline_contract(self):
        """Test Subject Timeline data contract"""
        from app.models.phase1_models import SubjectTimelineContract
        
        contract = SubjectTimelineContract()
        
        assert contract.granularity == "event_level"
        assert len(contract.required_fields) == 3
        assert any(f["name"] == "subject_id" for f in contract.required_fields)
        assert any(f["name"] == "event_date" for f in contract.required_fields)
        assert any(f["name"] == "event_type" for f in contract.required_fields)
        assert "subject_id" in contract.grouping_fields


class TestPhase1APIs:
    """Test Phase 1 API endpoints"""
    
    def test_create_widget_with_contract(self, client: TestClient, auth_headers):
        """Test creating widget with data contract"""
        widget_data = {
            "code": "enrollment_metric",
            "name": "Enrollment Metric",
            "category": "metrics",
            "config_schema": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"}
                }
            },
            "data_contract": {
                "granularity": "subject_level",
                "required_fields": [
                    {"name": "subject_id", "type": "identifier"}
                ],
                "supported_aggregations": ["count", "count_distinct"],
                "cache_ttl": 1800
            },
            "cache_ttl": 1800
        }
        
        response = client.post(
            "/api/v1/admin/widgets",
            json=widget_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["code"] == "enrollment_metric"
        assert data["data_contract"] is not None
        assert data["cache_ttl"] == 1800
    
    def test_dataset_metadata_extraction(self, client: TestClient, auth_headers):
        """Test dataset metadata extraction endpoint"""
        request_data = {
            "file_path": "/data/test/demographics.csv",
            "study_id": str(uuid.uuid4()),
            "auto_detect_granularity": True,
            "sample_rows": 100
        }
        
        response = client.post(
            "/api/v1/datasets/analyze",
            json=request_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "dataset_id" in data
        assert "columns" in data
        assert "granularity" in data
        assert "data_quality_score" in data
    
    def test_create_study_mapping(self, client: TestClient, auth_headers):
        """Test creating study data mapping"""
        mapping_data = {
            "study_id": str(uuid.uuid4()),
            "widget_id": str(uuid.uuid4()),
            "dataset_id": str(uuid.uuid4()),
            "field_mappings": {
                "subject_id": {
                    "source_field": "SUBJID",
                    "transform": "uppercase"
                },
                "enrollment_date": {
                    "source_field": "ENROLL_DT",
                    "transform": "to_date"
                }
            },
            "cache_override": 7200
        }
        
        response = client.post(
            "/api/v1/study/mappings",
            json=mapping_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["field_mappings"] is not None
        assert data["cache_override"] == 7200
    
    def test_mapping_template_creation(self, client: TestClient, auth_headers):
        """Test creating mapping template"""
        template_data = {
            "name": "Standard Demographics",
            "widget_type": "data_table",
            "edc_system": "medidata_rave",
            "field_patterns": {
                "subject_id": ["SUBJID", "SUBJECT_ID"],
                "age": ["AGE", "AGE_YRS"],
                "sex": ["SEX", "GENDER"]
            },
            "default_mappings": {
                "subject_id": "SUBJID",
                "age": "AGE",
                "sex": "SEX"
            }
        }
        
        response = client.post(
            "/api/v1/mapping-templates",
            json=template_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Standard Demographics"
        assert data["usage_count"] == 0
    
    def test_calculation_validation(self, client: TestClient, auth_headers):
        """Test calculation validation endpoint"""
        calculation_data = {
            "name": "age_at_enrollment",
            "expression": "DATE_DIFF(enrollment_date, birth_date, 'years')",
            "expression_type": "date_diff",
            "input_fields": ["enrollment_date", "birth_date"],
            "test_data": {
                "enrollment_date": "2024-01-15",
                "birth_date": "1980-05-20"
            }
        }
        
        response = client.post(
            "/api/v1/calculations/validate",
            json=calculation_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is True
        assert data["output_type"] == "numeric"
        assert data["test_result"] == 43  # Age calculation
    
    def test_widget_preview_with_mapping(self, client: TestClient, auth_headers):
        """Test widget preview with mapped data"""
        preview_request = {
            "widget_id": str(uuid.uuid4()),
            "mapping_id": str(uuid.uuid4()),
            "filters": {
                "site_id": "001"
            },
            "limit": 50
        }
        
        response = client.post(
            "/api/v1/widgets/preview",
            json=preview_request,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "widget_type" in data
        assert "data" in data
        assert "row_count" in data
        assert "execution_time_ms" in data


class TestPhase1Integration:
    """Integration tests for Phase 1 functionality"""
    
    def test_end_to_end_widget_mapping_flow(self, client: TestClient, auth_headers):
        """Test complete flow from dataset upload to widget display"""
        
        # Step 1: Upload and analyze dataset
        analysis_response = client.post(
            "/api/v1/datasets/analyze",
            json={
                "file_path": "/data/test/enrollment.csv",
                "study_id": str(uuid.uuid4()),
                "auto_detect_granularity": True
            },
            headers=auth_headers
        )
        assert analysis_response.status_code == 200
        dataset_id = analysis_response.json()["dataset_id"]
        
        # Step 2: Create widget with data contract
        widget_response = client.post(
            "/api/v1/admin/widgets",
            json={
                "code": "enrollment_kpi",
                "name": "Enrollment KPI",
                "category": "metrics",
                "config_schema": {"type": "object"},
                "data_contract": {
                    "granularity": "subject_level",
                    "required_fields": [{"name": "subject_id", "type": "identifier"}],
                    "supported_aggregations": ["count_distinct"]
                }
            },
            headers=auth_headers
        )
        assert widget_response.status_code == 201
        widget_id = widget_response.json()["id"]
        
        # Step 3: Generate mapping suggestions
        mapping_response = client.post(
            "/api/v1/mappings/generate",
            json={
                "study_id": str(uuid.uuid4()),
                "widget_id": widget_id,
                "dataset_id": dataset_id
            },
            headers=auth_headers
        )
        assert mapping_response.status_code == 200
        suggested_mappings = mapping_response.json()["suggested_mappings"]
        
        # Step 4: Create mapping
        create_mapping_response = client.post(
            "/api/v1/study/mappings",
            json={
                "study_id": str(uuid.uuid4()),
                "widget_id": widget_id,
                "dataset_id": dataset_id,
                "field_mappings": suggested_mappings
            },
            headers=auth_headers
        )
        assert create_mapping_response.status_code == 201
        mapping_id = create_mapping_response.json()["id"]
        
        # Step 5: Preview widget with data
        preview_response = client.post(
            "/api/v1/widgets/preview",
            json={
                "widget_id": widget_id,
                "mapping_id": mapping_id,
                "limit": 10
            },
            headers=auth_headers
        )
        assert preview_response.status_code == 200
        preview_data = preview_response.json()
        assert preview_data["widget_type"] == "kpi_metric_card"
        assert len(preview_data["data"]) > 0
    
    def test_cache_functionality(self, client: TestClient, auth_headers):
        """Test query caching functionality"""
        
        # First request - should miss cache
        first_response = client.post(
            "/api/v1/widgets/preview",
            json={
                "widget_id": str(uuid.uuid4()),
                "mapping_id": str(uuid.uuid4())
            },
            headers=auth_headers
        )
        assert first_response.status_code == 200
        assert first_response.json()["cache_hit"] is False
        
        # Second identical request - should hit cache
        second_response = client.post(
            "/api/v1/widgets/preview",
            json={
                "widget_id": str(uuid.uuid4()),
                "mapping_id": str(uuid.uuid4())
            },
            headers=auth_headers
        )
        assert second_response.status_code == 200
        assert second_response.json()["cache_hit"] is True
        
        # Verify execution time is lower for cached request
        assert second_response.json()["execution_time_ms"] < first_response.json()["execution_time_ms"]
    
    def test_multi_dataset_join(self, client: TestClient, auth_headers):
        """Test joining multiple datasets for a widget"""
        
        join_config = {
            "primary_dataset": "demographics",
            "joins": [
                {
                    "dataset": "adverse_events",
                    "type": "left",
                    "keys": {"primary": "SUBJID", "secondary": "SUBJECT_ID"}
                },
                {
                    "dataset": "lab_results",
                    "type": "left",
                    "keys": {"primary": "SUBJID", "secondary": "SUBJ_ID"}
                }
            ]
        }
        
        response = client.post(
            "/api/v1/study/mappings",
            json={
                "study_id": str(uuid.uuid4()),
                "widget_id": str(uuid.uuid4()),
                "join_config": join_config,
                "field_mappings": {
                    "subject_id": {"source_field": "SUBJID"},
                    "ae_count": {"source_field": "ae.COUNT", "dataset": "adverse_events"},
                    "lab_abnormal": {"source_field": "lab.ABNORMAL_FLAG", "dataset": "lab_results"}
                }
            },
            headers=auth_headers
        )
        
        assert response.status_code == 201
        assert response.json()["join_config"] is not None


# Fixtures
@pytest.fixture
def db_session():
    """Create test database session"""
    engine = create_engine(TEST_DATABASE_URL)
    SQLModel.metadata.create_all(engine)
    
    with Session(engine) as session:
        yield session
    
    SQLModel.metadata.drop_all(engine)


@pytest.fixture
def client():
    """Create test client"""
    from app.main import app
    from fastapi.testclient import TestClient
    
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Create auth headers for testing"""
    return {
        "Authorization": "Bearer test_token_123",
        "Content-Type": "application/json"
    }


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])