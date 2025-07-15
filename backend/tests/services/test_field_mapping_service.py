# ABOUTME: Unit tests for FieldMappingService
# ABOUTME: Tests field mapping generation and CDISC pattern matching

import pytest
from unittest.mock import Mock, AsyncMock
from app.services.field_mapping_service import FieldMappingService
from app.models.field_mapping import FieldMapping


@pytest.fixture
def service():
    return FieldMappingService()


@pytest.fixture
def mock_study():
    study = Mock()
    study.id = "study123"
    study.org_id = "org123"
    return study


@pytest.fixture
def mock_parquet_files():
    return [
        {
            "path": "/data/dm.parquet",
            "dataset": "DM",
            "columns": ["USUBJID", "SUBJID", "SITEID", "AGE", "SEX", "RACE"]
        },
        {
            "path": "/data/ae.parquet",
            "dataset": "AE",
            "columns": ["USUBJID", "AEDECOD", "AESER", "AESTDTC", "AEENDTC"]
        }
    ]


class TestSDTMPatternMatching:
    def test_match_common_sdtm_fields(self, service):
        # Test exact matches
        assert service._calculate_field_similarity("USUBJID", "USUBJID") == 1.0
        assert service._calculate_field_similarity("AEDECOD", "AEDECOD") == 1.0
        
        # Test case insensitive
        assert service._calculate_field_similarity("usubjid", "USUBJID") > 0.9
        
        # Test partial matches
        assert service._calculate_field_similarity("SUBJECT_ID", "USUBJID") > 0.7
        assert service._calculate_field_similarity("ADVERSE_EVENT", "AEDECOD") > 0.6
        
    def test_sdtm_pattern_detection(self, service):
        # Test SDTM patterns
        patterns = service._get_field_patterns()
        
        # Verify key patterns exist
        assert "USUBJID" in patterns
        assert "AEDECOD" in patterns
        assert "VISITNUM" in patterns
        
        # Test pattern matching
        assert any("SUBJ" in p for p in patterns["USUBJID"]["patterns"])
        assert any("DECOD" in p for p in patterns["AEDECOD"]["patterns"])


class TestFieldMappingGeneration:
    @pytest.mark.asyncio
    async def test_generate_mappings_basic(self, service, mock_study, mock_parquet_files):
        # Mock database
        service.db = AsyncMock()
        
        # Data requirements
        data_requirements = [
            {
                "widget_id": "widget1",
                "dataset": "DM",
                "fields": ["USUBJID", "AGE", "SEX"]
            },
            {
                "widget_id": "widget2",
                "dataset": "AE",
                "fields": ["USUBJID", "AEDECOD"]
            }
        ]
        
        # Mock file reading
        with Mock.patch('pyarrow.parquet.read_schema') as mock_read:
            mock_read.return_value = Mock(names=mock_parquet_files[0]["columns"])
            
            # Execute
            result = await service.generate_mappings_for_study(
                service.db,
                mock_study,
                data_requirements,
                mock_parquet_files
            )
        
        # Verify results
        assert result["total_mappings"] > 0
        assert result["auto_mapped"] > 0
        assert "mappings" in result
        
    @pytest.mark.asyncio
    async def test_fuzzy_matching(self, service):
        # Test fuzzy matching for common variations
        test_cases = [
            ("SUBJECT_ID", "USUBJID", 0.7),
            ("PATIENT_ID", "USUBJID", 0.6),
            ("AE_TERM", "AEDECOD", 0.6),
            ("ADVERSE_EVENT_TERM", "AEDECOD", 0.5)
        ]
        
        for source, target, min_score in test_cases:
            score = service._calculate_field_similarity(source, target)
            assert score >= min_score, f"{source} -> {target} score {score} < {min_score}"
            
    @pytest.mark.asyncio
    async def test_confidence_scoring(self, service):
        # Test confidence calculation
        mappings = [
            {"similarity_score": 1.0, "pattern_match": True},  # Perfect match
            {"similarity_score": 0.8, "pattern_match": True},  # Good match with pattern
            {"similarity_score": 0.7, "pattern_match": False}, # Good match no pattern
            {"similarity_score": 0.5, "pattern_match": False}  # Poor match
        ]
        
        for mapping in mappings:
            confidence = service._calculate_confidence(
                mapping["similarity_score"],
                mapping["pattern_match"]
            )
            
            if mapping["similarity_score"] == 1.0:
                assert confidence >= 0.95
            elif mapping["similarity_score"] >= 0.8 and mapping["pattern_match"]:
                assert confidence >= 0.85
            else:
                assert confidence < 0.85


class TestMappingValidation:
    @pytest.mark.asyncio
    async def test_validate_required_fields(self, service, mock_study):
        # Mock database and existing mappings
        service.db = AsyncMock()
        
        # Mock query result
        mock_mappings = [
            Mock(target_field="USUBJID", is_mapped=True),
            Mock(target_field="AEDECOD", is_mapped=True),
            Mock(target_field="AESER", is_mapped=False)
        ]
        
        service.db.execute = AsyncMock()
        service.db.execute.return_value.scalars = Mock(return_value=Mock(all=Mock(return_value=mock_mappings)))
        
        # Execute validation
        required_fields = ["USUBJID", "AEDECOD", "AESER", "AESTDTC"]
        result = await service.validate_study_mappings(
            service.db,
            mock_study.id,
            required_fields
        )
        
        # Verify results
        assert result["is_valid"] == False  # Not all required fields mapped
        assert result["mapped_count"] == 2
        assert result["missing_count"] == 2
        assert "AESER" in result["unmapped_fields"]  # Not mapped
        assert "AESTDTC" in result["unmapped_fields"]  # Not found


class TestMappingUpdates:
    @pytest.mark.asyncio
    async def test_update_mapping(self, service, mock_study):
        # Mock database
        service.db = AsyncMock()
        
        # Mock existing mapping
        mock_mapping = Mock(spec=FieldMapping)
        mock_mapping.id = "mapping123"
        mock_mapping.source_field = "PATIENT_ID"
        mock_mapping.is_mapped = False
        
        service.db.get = AsyncMock(return_value=mock_mapping)
        
        # Execute update
        update_data = {
            "source_field": "USUBJID",
            "is_mapped": True,
            "confidence_score": 0.95
        }
        
        result = await service.update_field_mapping(
            service.db,
            "mapping123",
            update_data
        )
        
        # Verify
        assert mock_mapping.source_field == "USUBJID"
        assert mock_mapping.is_mapped == True
        assert mock_mapping.confidence_score == 0.95
        service.db.commit.assert_called_once()


class TestBulkOperations:
    @pytest.mark.asyncio
    async def test_bulk_create_mappings(self, service):
        # Mock database
        service.db = AsyncMock()
        
        # Test data
        mappings_data = [
            {
                "study_id": "study123",
                "widget_id": "widget1",
                "target_field": "USUBJID",
                "source_field": "USUBJID",
                "confidence_score": 1.0
            },
            {
                "study_id": "study123",
                "widget_id": "widget1", 
                "target_field": "AGE",
                "source_field": "AGE",
                "confidence_score": 1.0
            }
        ]
        
        # Execute
        created_mappings = await service._bulk_create_mappings(
            service.db,
            mappings_data
        )
        
        # Verify
        assert len(created_mappings) == 2
        service.db.commit.assert_called_once()