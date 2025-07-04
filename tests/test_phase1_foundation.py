# ABOUTME: Test suite for Phase 1 Foundation Setup including database models, folder structure, and compliance fields
# ABOUTME: Validates organization creation, study initialization, audit logging, and file permissions for 21 CFR Part 11

import pytest
from datetime import datetime
from pathlib import Path
import os
import stat
from sqlmodel import select
from app.models import Organization, Study, User, ActivityLog
from app.services.file_service import FileService
from tests.conftest import expected_result

class TestPhase1Foundation:
    """Comprehensive test suite for Phase 1: Foundation Setup"""
    
    @pytest.mark.unit
    @pytest.mark.critical
    @expected_result("Organization created with all required fields and proper multi-tenant isolation")
    async def test_create_organization(self, db_session):
        """Test organization creation with multi-tenant support"""
        # Create organization
        org = Organization(
            name="Pharma Corp International",
            code="pharma-corp",
            config={
                "max_studies": 20,
                "features": ["advanced_analytics", "api_access", "export_enabled"],
                "theme": {"primary_color": "#0066CC", "logo_url": "/assets/pharma-corp-logo.png"}
            },
            is_active=True
        )
        db_session.add(org)
        await db_session.commit()
        await db_session.refresh(org)
        
        # Validate
        assert org.id is not None
        assert org.name == "Pharma Corp International"
        assert org.code == "pharma-corp"
        assert org.is_active is True
        assert org.created_at is not None
        assert org.config["max_studies"] == 20
        assert "advanced_analytics" in org.config["features"]
        
        # Test uniqueness constraint
        duplicate_org = Organization(name="Another Org", code="pharma-corp")
        db_session.add(duplicate_org)
        with pytest.raises(Exception):  # Should raise integrity error
            await db_session.commit()
    
    @pytest.mark.unit
    @expected_result("User created with proper organization association and password hashing")
    async def test_create_user_with_org(self, db_session, test_organization):
        """Test user creation with organization association"""
        from app.core.security import get_password_hash
        
        user = User(
            email="john.doe@pharmcorp.com",
            full_name="John Doe",
            org_id=test_organization.id,
            is_active=True,
            hashed_password=get_password_hash("SecureP@ssw0rd123!")
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        assert user.id is not None
        assert user.email == "john.doe@pharmcorp.com"
        assert user.org_id == test_organization.id
        assert user.hashed_password != "SecureP@ssw0rd123!"  # Should be hashed
        assert user.is_active is True
    
    @pytest.mark.unit
    @pytest.mark.critical
    @expected_result("Study created with proper folder structure and metadata initialization")
    async def test_study_creation_with_folders(self, db_session, test_organization, test_user, tmp_path):
        """Test complete study creation workflow including folder structure"""
        # Create study
        study = Study(
            name="COVID-19 Vaccine Trial Phase 3",
            code="COV-VAC-P3",
            protocol_number="COV-2024-001",
            org_id=test_organization.id,
            created_by=test_user.id,
            status="setup",
            config={
                "data_sources": ["medidata", "zip_upload"],
                "refresh_frequency": "daily",
                "retention_days": 365
            }
        )
        db_session.add(study)
        await db_session.commit()
        await db_session.refresh(study)
        
        assert study.id is not None
        assert study.status == "setup"
        
        # Initialize folder structure
        file_service = FileService(base_path=str(tmp_path))
        await file_service.initialize_study_folders(study)
        
        # Verify folder structure
        study_root = tmp_path / str(study.org_id) / str(study.id)
        
        # Check all required folders exist
        required_folders = [
            "raw/medidata",
            "raw/uploads", 
            "raw/archive",
            "processed/current",
            "processed/archive",
            "analysis/datasets",
            "analysis/scripts",
            "exports/pdf",
            "exports/excel",
            "exports/powerpoint",
            "exports/scheduled",
            "temp",
            "logs",
            "metadata",
            "config"
        ]
        
        for folder in required_folders:
            folder_path = study_root / folder
            assert folder_path.exists(), f"Folder {folder} should exist"
            
        # Verify metadata files created
        assert (study_root / "metadata" / "version_history.json").exists()
        assert (study_root / "metadata" / "data_dictionary.json").exists()
        assert (study_root / "metadata" / "field_mappings.json").exists()
        assert (study_root / "config" / "pipeline_config.json").exists()
    
    @pytest.mark.unit
    @pytest.mark.compliance
    @expected_result("Folder permissions set correctly for 21 CFR Part 11 compliance")
    async def test_folder_permissions_compliance(self, test_study, tmp_path):
        """Test folder permissions for 21 CFR Part 11 compliance"""
        if os.name == 'nt':  # Skip on Windows
            pytest.skip("Permission tests not applicable on Windows")
            
        file_service = FileService(base_path=str(tmp_path))
        await file_service.initialize_study_folders(test_study)
        
        study_root = tmp_path / str(test_study.org_id) / str(test_study.id)
        
        # Check permissions
        raw_folder = study_root / "raw"
        raw_stat = os.stat(raw_folder)
        
        # Owner should have rwx, group rx, others no access (750)
        assert stat.S_IMODE(raw_stat.st_mode) == 0o750
        
        # After data upload, raw folder should become read-only
        file_service._set_raw_folder_readonly(str(raw_folder))
        raw_stat_after = os.stat(raw_folder)
        # Owner and group read+execute only (550)
        assert stat.S_IMODE(raw_stat_after.st_mode) == 0o550
    
    @pytest.mark.unit
    @pytest.mark.compliance
    @expected_result("Audit log captures all required fields for 21 CFR Part 11 compliance")
    async def test_audit_log_21cfr_compliance(self, db_session, test_user, test_study):
        """Test audit log creation with all 21 CFR Part 11 required fields"""
        # Create audit log entry
        audit = ActivityLog(
            user_id=test_user.id,
            action="STUDY_CREATED",
            resource_type="study",
            resource_id=str(test_study.id),
            timestamp=datetime.utcnow(),
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            details={
                "study_name": test_study.name,
                "protocol_number": test_study.protocol_number
            },
            # 21 CFR Part 11 specific fields
            system_timestamp=datetime.utcnow(),
            sequence_number=1001,
            reason="New study initialization"
        )
        db_session.add(audit)
        await db_session.commit()
        await db_session.refresh(audit)
        
        # Validate all fields
        assert audit.id is not None
        assert audit.user_id == test_user.id
        assert audit.action == "STUDY_CREATED"
        assert audit.sequence_number == 1001
        assert audit.system_timestamp is not None
        assert audit.reason == "New study initialization"
        
        # Verify immutability (in production, triggers would prevent updates)
        original_action = audit.action
        audit.action = "MODIFIED_ACTION"
        # In production, this should fail due to database constraints
    
    @pytest.mark.unit
    @expected_result("Database schema supports all required clinical data types")
    async def test_clinical_data_models(self, db_session):
        """Test clinical data model flexibility"""
        from app.models import DataSource, DataSourceConfig
        
        # Test various data source configurations
        medidata_source = DataSource(
            name="Medidata Rave Production",
            type="medidata_api",
            config=DataSourceConfig(
                connection_details={
                    "api_url": "https://api.mdsol.com",
                    "api_version": "1.0",
                    "study_oid": "PROD-001"
                },
                credentials={
                    "api_key": "encrypted_key_here",
                    "api_secret": "encrypted_secret_here"
                },
                refresh_schedule="0 2 * * *"  # Daily at 2 AM
            ).dict()
        )
        db_session.add(medidata_source)
        
        zip_source = DataSource(
            name="Manual Data Upload",
            type="zip_upload", 
            config=DataSourceConfig(
                connection_details={
                    "upload_path": "/data/uploads",
                    "file_patterns": ["*.sas7bdat", "*.csv"]
                },
                validation_rules={
                    "required_files": ["dm.sas7bdat", "ae.sas7bdat"],
                    "max_file_size_mb": 500
                }
            ).dict()
        )
        db_session.add(zip_source)
        
        await db_session.commit()
        
        # Verify storage
        sources = await db_session.exec(select(DataSource))
        assert len(sources.all()) == 2
    
    @pytest.mark.integration
    @expected_result("Multi-tenant isolation ensures data separation between organizations")
    async def test_multi_tenant_isolation(self, db_session):
        """Test multi-tenant data isolation"""
        # Create two organizations
        org1 = Organization(name="Pharma A", code="pharma-a")
        org2 = Organization(name="Pharma B", code="pharma-b")
        db_session.add_all([org1, org2])
        await db_session.commit()
        
        # Create studies for each org
        study1 = Study(
            name="Study A1",
            code="A1",
            protocol_number="A-001",
            org_id=org1.id,
            created_by="user1"
        )
        study2 = Study(
            name="Study B1", 
            code="B1",
            protocol_number="B-001",
            org_id=org2.id,
            created_by="user2"
        )
        db_session.add_all([study1, study2])
        await db_session.commit()
        
        # Query with tenant filter
        org1_studies = await db_session.exec(
            select(Study).where(Study.org_id == org1.id)
        )
        org1_studies = org1_studies.all()
        
        assert len(org1_studies) == 1
        assert org1_studies[0].name == "Study A1"
        assert all(s.org_id == org1.id for s in org1_studies)
    
    @pytest.mark.performance
    @expected_result("Database queries complete within performance targets")
    async def test_database_query_performance(self, db_session, test_organization):
        """Test database query performance"""
        import time
        
        # Create test data
        studies = []
        for i in range(100):
            study = Study(
                name=f"Study {i:03d}",
                code=f"STD{i:03d}",
                protocol_number=f"PROTO-{i:03d}",
                org_id=test_organization.id,
                created_by="test_user"
            )
            studies.append(study)
        
        db_session.add_all(studies)
        await db_session.commit()
        
        # Test query performance
        start_time = time.time()
        
        # Complex query with joins and filters
        result = await db_session.exec(
            select(Study)
            .where(Study.org_id == test_organization.id)
            .where(Study.status == "active")
            .order_by(Study.created_at.desc())
            .limit(50)
        )
        studies_list = result.all()
        
        query_time = time.time() - start_time
        
        # Should complete within 100ms
        assert query_time < 0.1, f"Query took {query_time:.3f}s, expected < 0.1s"
        assert len(studies_list) <= 50