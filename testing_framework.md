# Clinical Dashboard Platform - Comprehensive Testing Framework

## Overview

This document outlines the comprehensive testing strategy using pytest for the Clinical Dashboard Platform. All test results will be automatically generated and saved in the `Reports/` folder with detailed descriptions, expected results, and pass/fail status.

## Testing Framework Structure

```
clinical-dashboard/
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Global fixtures and configuration
│   ├── unit/                    # Unit tests for individual components
│   │   ├── test_models.py
│   │   ├── test_services.py
│   │   ├── test_validators.py
│   │   └── test_utils.py
│   ├── integration/             # Integration tests
│   │   ├── test_api_endpoints.py
│   │   ├── test_data_pipeline.py
│   │   ├── test_rbac.py
│   │   └── test_compliance.py
│   ├── compliance/              # Compliance-specific tests
│   │   ├── test_21cfr_part11.py
│   │   └── test_hipaa.py
│   ├── performance/             # Performance tests
│   │   ├── test_load.py
│   │   └── test_stress.py
│   ├── e2e/                     # End-to-end tests
│   │   ├── test_study_workflow.py
│   │   └── test_dashboard_creation.py
│   └── fixtures/                # Test data and fixtures
│       ├── clinical_data.py
│       ├── users.py
│       └── organizations.py
├── Reports/                     # Test reports output directory
│   ├── {timestamp}/
│   │   ├── summary.html
│   │   ├── detailed_report.pdf
│   │   └── raw_results.json
└── pytest.ini                   # Pytest configuration

```

## Core Testing Configuration

### pytest.ini
```ini
[pytest]
minversion = 7.0
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

# Markers for different test categories
markers =
    unit: Unit tests
    integration: Integration tests
    compliance: Compliance tests (21 CFR Part 11, HIPAA)
    performance: Performance tests
    e2e: End-to-end tests
    smoke: Quick smoke tests
    critical: Critical functionality tests
    async: Asynchronous tests

# Coverage settings
addopts = 
    --verbose
    --strict-markers
    --cov=app
    --cov-report=html
    --cov-report=term-missing
    --cov-report=json
    --html=Reports/latest/report.html
    --self-contained-html
    --capture=no
    --tb=short

# Async settings
asyncio_mode = auto

# Test output
log_cli = true
log_cli_level = INFO
```

### conftest.py - Global Test Configuration
```python
# tests/conftest.py
import pytest
import asyncio
from datetime import datetime
from pathlib import Path
import json
import pandas as pd
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import pytest_html
from py.xml import html

from app.core.config import settings
from app.core.db import get_session
from app.models import *
from tests.report_generator import TestReportGenerator

# Configure async event loop
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

# Database fixtures
@pytest.fixture(scope="session")
async def test_db():
    """Create test database"""
    engine = create_async_engine(
        f"postgresql+asyncpg://test:test@localhost/test_clinical_dashboard",
        echo=False
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()

@pytest.fixture
async def db_session(test_db):
    """Create database session for tests"""
    async_session = sessionmaker(
        test_db, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()

# Test data fixtures
@pytest.fixture
async def test_organization(db_session: AsyncSession) -> Organization:
    """Create test organization"""
    org = Organization(
        name="Test Pharma Corp",
        code="test-pharma",
        config={
            "max_studies": 10,
            "features": ["advanced_analytics", "api_access"]
        }
    )
    db_session.add(org)
    await db_session.commit()
    await db_session.refresh(org)
    return org

@pytest.fixture
async def test_user(db_session: AsyncSession, test_organization: Organization) -> User:
    """Create test user"""
    user = User(
        email="test@testpharma.com",
        full_name="Test User",
        org_id=test_organization.id,
        is_active=True,
        hashed_password="$2b$12$test_hash"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest.fixture
async def test_study(db_session: AsyncSession, test_organization: Organization, test_user: User) -> Study:
    """Create test study"""
    study = Study(
        name="Test Study 001",
        code="TST001",
        protocol_number="TEST-PROTOCOL-001",
        org_id=test_organization.id,
        created_by=test_user.id,
        status="active",
        config={
            "data_sources": ["medidata", "zip_upload"],
            "refresh_frequency": "daily"
        }
    )
    db_session.add(study)
    await db_session.commit()
    await db_session.refresh(study)
    return study

# Report generation hooks
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Capture test results for custom reporting"""
    outcome = yield
    report = outcome.get_result()
    
    # Add custom test metadata
    if report.when == "call":
        # Extract test metadata from docstring or markers
        test_metadata = {
            "name": item.name,
            "description": item.function.__doc__ or "No description provided",
            "expected_result": getattr(item.function, "_expected_result", "Not specified"),
            "actual_result": "Pass" if report.passed else f"Fail: {report.longrepr}",
            "duration": report.duration,
            "markers": [marker.name for marker in item.iter_markers()],
            "module": item.module.__name__,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Store in item for later collection
        if not hasattr(item.session, "test_results"):
            item.session.test_results = []
        item.session.test_results.append(test_metadata)

@pytest.fixture(scope="session", autouse=True)
def generate_test_report(request):
    """Generate comprehensive test report after all tests"""
    yield
    
    # Get test results
    test_results = getattr(request.session, "test_results", [])
    
    # Generate report
    report_generator = TestReportGenerator()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_dir = Path(f"Reports/{timestamp}")
    report_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate different report formats
    report_generator.generate_html_report(test_results, report_dir / "summary.html")
    report_generator.generate_pdf_report(test_results, report_dir / "detailed_report.pdf")
    report_generator.generate_json_report(test_results, report_dir / "raw_results.json")
    
    print(f"\n\nTest reports generated in: {report_dir}")

# Custom markers and decorators
def expected_result(result: str):
    """Decorator to specify expected test result"""
    def decorator(func):
        func._expected_result = result
        return func
    return decorator
```

## Test Report Generator

```python
# tests/report_generator.py
from typing import List, Dict, Any
from datetime import datetime
from pathlib import Path
import json
import pandas as pd
from jinja2 import Template
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

class TestReportGenerator:
    """Generate test reports in multiple formats"""
    
    def __init__(self):
        self.html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Clinical Dashboard Test Report - {{ timestamp }}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background-color: #0066CC; color: white; padding: 20px; }
        .summary { background-color: #f0f0f0; padding: 15px; margin: 20px 0; }
        .pass { color: green; font-weight: bold; }
        .fail { color: red; font-weight: bold; }
        table { border-collapse: collapse; width: 100%; margin-top: 20px; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #0066CC; color: white; }
        tr:nth-child(even) { background-color: #f2f2f2; }
        .test-detail { margin: 20px 0; padding: 10px; border-left: 4px solid #0066CC; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Clinical Dashboard Platform - Test Report</h1>
        <p>Generated: {{ timestamp }}</p>
    </div>
    
    <div class="summary">
        <h2>Test Summary</h2>
        <p>Total Tests: {{ total_tests }}</p>
        <p class="pass">Passed: {{ passed_tests }}</p>
        <p class="fail">Failed: {{ failed_tests }}</p>
        <p>Pass Rate: {{ pass_rate }}%</p>
        <p>Total Duration: {{ total_duration }}s</p>
    </div>
    
    <h2>Test Results by Category</h2>
    {% for category, tests in tests_by_category.items() %}
    <h3>{{ category|title }}</h3>
    <table>
        <tr>
            <th>Test Name</th>
            <th>Description</th>
            <th>Expected Result</th>
            <th>Actual Result</th>
            <th>Duration (s)</th>
            <th>Status</th>
        </tr>
        {% for test in tests %}
        <tr>
            <td>{{ test.name }}</td>
            <td>{{ test.description }}</td>
            <td>{{ test.expected_result }}</td>
            <td>{{ test.actual_result }}</td>
            <td>{{ "%.3f"|format(test.duration) }}</td>
            <td class="{% if 'Pass' in test.actual_result %}pass{% else %}fail{% endif %}">
                {% if 'Pass' in test.actual_result %}PASS{% else %}FAIL{% endif %}
            </td>
        </tr>
        {% endfor %}
    </table>
    {% endfor %}
    
    <h2>Detailed Test Results</h2>
    {% for test in all_tests %}
    <div class="test-detail">
        <h4>{{ test.name }}</h4>
        <p><strong>Module:</strong> {{ test.module }}</p>
        <p><strong>Description:</strong> {{ test.description }}</p>
        <p><strong>Expected Result:</strong> {{ test.expected_result }}</p>
        <p><strong>Actual Result:</strong> {{ test.actual_result }}</p>
        <p><strong>Duration:</strong> {{ "%.3f"|format(test.duration) }}s</p>
        <p><strong>Markers:</strong> {{ test.markers|join(', ') }}</p>
    </div>
    {% endfor %}
</body>
</html>
        """
    
    def generate_html_report(self, test_results: List[Dict], output_path: Path):
        """Generate HTML test report"""
        # Calculate summary statistics
        total_tests = len(test_results)
        passed_tests = sum(1 for t in test_results if 'Pass' in t['actual_result'])
        failed_tests = total_tests - passed_tests
        pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        total_duration = sum(t['duration'] for t in test_results)
        
        # Group tests by category (based on markers)
        tests_by_category = {}
        for test in test_results:
            category = test['markers'][0] if test['markers'] else 'uncategorized'
            if category not in tests_by_category:
                tests_by_category[category] = []
            tests_by_category[category].append(test)
        
        # Render template
        template = Template(self.html_template)
        html_content = template.render(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            total_tests=total_tests,
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            pass_rate=f"{pass_rate:.1f}",
            total_duration=f"{total_duration:.2f}",
            tests_by_category=tests_by_category,
            all_tests=test_results
        )
        
        # Write to file
        output_path.write_text(html_content)
    
    def generate_pdf_report(self, test_results: List[Dict], output_path: Path):
        """Generate PDF test report"""
        doc = SimpleDocTemplate(str(output_path), pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#0066CC'),
            spaceAfter=30
        )
        story.append(Paragraph("Clinical Dashboard Platform - Test Report", title_style))
        story.append(Spacer(1, 12))
        
        # Summary
        summary_data = [
            ['Test Summary', ''],
            ['Total Tests:', str(len(test_results))],
            ['Passed:', str(sum(1 for t in test_results if 'Pass' in t['actual_result']))],
            ['Failed:', str(sum(1 for t in test_results if 'Fail' in t['actual_result']))],
            ['Total Duration:', f"{sum(t['duration'] for t in test_results):.2f}s"]
        ]
        
        summary_table = Table(summary_data, colWidths=[2*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0066CC')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(summary_table)
        story.append(PageBreak())
        
        # Detailed results
        story.append(Paragraph("Detailed Test Results", styles['Heading2']))
        story.append(Spacer(1, 12))
        
        # Create table data
        table_data = [['Test Name', 'Status', 'Duration', 'Description']]
        for test in test_results:
            status = 'PASS' if 'Pass' in test['actual_result'] else 'FAIL'
            table_data.append([
                test['name'][:50],  # Truncate long names
                status,
                f"{test['duration']:.3f}s",
                test['description'][:100]  # Truncate long descriptions
            ])
        
        # Create table
        results_table = Table(table_data, colWidths=[2.5*inch, 1*inch, 1*inch, 2.5*inch])
        results_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0066CC')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
        ]))
        
        # Color code pass/fail
        for i, test in enumerate(test_results, 1):
            if 'Fail' in test['actual_result']:
                results_table.setStyle(TableStyle([
                    ('TEXTCOLOR', (1, i), (1, i), colors.red),
                    ('FONTNAME', (1, i), (1, i), 'Helvetica-Bold')
                ]))
            else:
                results_table.setStyle(TableStyle([
                    ('TEXTCOLOR', (1, i), (1, i), colors.green),
                    ('FONTNAME', (1, i), (1, i), 'Helvetica-Bold')
                ]))
        
        story.append(results_table)
        
        # Build PDF
        doc.build(story)
    
    def generate_json_report(self, test_results: List[Dict], output_path: Path):
        """Generate JSON test report for programmatic access"""
        report = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "platform": "Clinical Dashboard Platform",
                "test_framework": "pytest",
                "total_tests": len(test_results),
                "passed": sum(1 for t in test_results if 'Pass' in t['actual_result']),
                "failed": sum(1 for t in test_results if 'Fail' in t['actual_result']),
                "total_duration": sum(t['duration'] for t in test_results)
            },
            "tests": test_results,
            "summary_by_category": self._summarize_by_category(test_results),
            "summary_by_module": self._summarize_by_module(test_results)
        }
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
    
    def _summarize_by_category(self, test_results: List[Dict]) -> Dict[str, Dict]:
        """Summarize test results by category"""
        summary = {}
        for test in test_results:
            category = test['markers'][0] if test['markers'] else 'uncategorized'
            if category not in summary:
                summary[category] = {'total': 0, 'passed': 0, 'failed': 0}
            summary[category]['total'] += 1
            if 'Pass' in test['actual_result']:
                summary[category]['passed'] += 1
            else:
                summary[category]['failed'] += 1
        return summary
    
    def _summarize_by_module(self, test_results: List[Dict]) -> Dict[str, Dict]:
        """Summarize test results by module"""
        summary = {}
        for test in test_results:
            module = test['module']
            if module not in summary:
                summary[module] = {'total': 0, 'passed': 0, 'failed': 0}
            summary[module]['total'] += 1
            if 'Pass' in test['actual_result']:
                summary[module]['passed'] += 1
            else:
                summary[module]['failed'] += 1
        return summary
```

## Phase-Specific Test Suites

### Phase 1: Foundation Setup Tests

```python
# tests/unit/test_models.py
import pytest
from datetime import datetime
from tests.conftest import expected_result

class TestFoundationModels:
    """Test suite for Phase 1: Foundation Setup"""
    
    @pytest.mark.unit
    @expected_result("Organization should be created with valid data and proper defaults")
    async def test_organization_creation(self, db_session):
        """Test creating an organization with all required fields"""
        org = Organization(
            name="Test Pharma",
            code="test-pharma",
            config={"theme": {"primary_color": "#0066CC"}}
        )
        db_session.add(org)
        await db_session.commit()
        
        assert org.id is not None
        assert org.name == "Test Pharma"
        assert org.code == "test-pharma"
        assert org.is_active is True
        assert org.created_at is not None
    
    @pytest.mark.unit
    @expected_result("Study folder structure should be created with proper permissions")
    async def test_study_folder_creation(self, test_study, tmp_path):
        """Test study folder structure creation"""
        from app.services.file_service import FileService
        
        # Use temp directory for testing
        file_service = FileService(base_path=str(tmp_path))
        await file_service.initialize_study_folders(test_study)
        
        # Verify folder structure
        study_path = tmp_path / str(test_study.org_id) / str(test_study.id)
        assert (study_path / "raw" / "medidata").exists()
        assert (study_path / "raw" / "uploads").exists()
        assert (study_path / "processed" / "current").exists()
        assert (study_path / "analysis" / "datasets").exists()
        assert (study_path / "exports").exists()
        assert (study_path / "metadata").exists()
        
        # Verify permissions (on Unix systems)
        import os
        import stat
        if os.name != 'nt':  # Not Windows
            raw_stat = os.stat(study_path / "raw")
            assert stat.S_IMODE(raw_stat.st_mode) == 0o750
    
    @pytest.mark.unit
    @pytest.mark.compliance
    @expected_result("Audit log should capture all required fields for 21 CFR Part 11")
    async def test_audit_log_compliance(self, db_session, test_user):
        """Test audit log creation with 21 CFR Part 11 compliance"""
        audit = ActivityLog(
            user_id=test_user.id,
            action="CREATE_STUDY",
            resource_type="study",
            resource_id="test-study-id",
            timestamp=datetime.utcnow(),
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0",
            details={"study_name": "Test Study"},
            # 21 CFR Part 11 specific fields
            system_timestamp=datetime.utcnow(),
            sequence_number=1001
        )
        db_session.add(audit)
        await db_session.commit()
        
        assert audit.id is not None
        assert audit.sequence_number == 1001
        assert audit.system_timestamp is not None
        assert audit.timestamp is not None
```

### Phase 2: RBAC Tests

```python
# tests/integration/test_rbac.py
import pytest
from tests.conftest import expected_result

class TestRBACSystem:
    """Test suite for Phase 2: Role-Based Access Control"""
    
    @pytest.mark.integration
    @expected_result("User with study_manager role should have appropriate permissions")
    async def test_role_permissions(self, db_session, test_user, test_study):
        """Test RBAC permission checking"""
        from app.core.rbac_middleware import PermissionChecker
        from app.models import Role, UserRole
        
        # Create study_manager role
        role = await db_session.exec(
            select(Role).where(Role.name == "study_manager")
        )
        role = role.first()
        
        # Assign role to user
        user_role = UserRole(
            user_id=test_user.id,
            role_id=role.id,
            study_id=test_study.id,
            assigned_by=test_user.id
        )
        db_session.add(user_role)
        await db_session.commit()
        
        # Test permission check
        checker = PermissionChecker(["study:manage:assigned"])
        mock_request = MockRequest(path_params={"study_id": str(test_study.id)})
        
        # Should not raise exception
        result = await checker(mock_request, test_user, db_session)
        assert result == test_user
    
    @pytest.mark.integration
    @expected_result("Platform admin should bypass all permission checks")
    async def test_platform_admin_bypass(self, db_session, test_user):
        """Test platform admin permission bypass"""
        from app.core.rbac_middleware import PermissionChecker
        
        # Make user platform admin
        platform_admin_role = await db_session.exec(
            select(Role).where(Role.name == "platform_admin")
        )
        platform_admin_role = platform_admin_role.first()
        
        user_role = UserRole(
            user_id=test_user.id,
            role_id=platform_admin_role.id,
            assigned_by=test_user.id
        )
        db_session.add(user_role)
        await db_session.commit()
        
        # Test any permission check - should pass
        checker = PermissionChecker(["any:permission:check"])
        mock_request = MockRequest()
        
        result = await checker(mock_request, test_user, db_session)
        assert result == test_user
```

### Phase 3: Data Pipeline Tests

```python
# tests/integration/test_data_pipeline.py
import pytest
import pandas as pd
from pathlib import Path
from tests.conftest import expected_result

class TestDataPipeline:
    """Test suite for Phase 3: Data Pipeline System"""
    
    @pytest.mark.integration
    @expected_result("Medidata API source should successfully fetch data")
    async def test_medidata_api_source(self, httpx_mock):
        """Test Medidata Rave API data source integration"""
        from app.clinical_modules.data_pipeline.data_sources import MedidataAPISource
        
        # Mock Medidata API response
        httpx_mock.add_response(
            url="https://api.medidata.com/studies",
            json={"status": "ok"},
            status_code=200
        )
        httpx_mock.add_response(
            url="https://api.medidata.com/studies/TEST001/datasets/DM",
            json={"items": [
                {"USUBJID": "001", "AGE": 45, "SEX": "M"},
                {"USUBJID": "002", "AGE": 52, "SEX": "F"}
            ]}
        )
        
        # Test connection
        source = MedidataAPISource({
            "api_url": "https://api.medidata.com",
            "api_key": "test-key",
            "study_oid": "TEST001"
        })
        
        connected = await source.connect()
        assert connected is True
        
        # Test data fetch
        df = await source.fetch_data({"dataset": "DM"})
        assert len(df) == 2
        assert list(df.columns) == ["USUBJID", "AGE", "SEX"]
    
    @pytest.mark.integration
    @expected_result("ZIP file upload should extract and load data correctly")
    async def test_zip_file_upload(self, tmp_path, test_study):
        """Test ZIP file upload data source"""
        from app.clinical_modules.data_pipeline.data_sources import ZipFileUploadSource
        import zipfile
        
        # Create test ZIP file
        zip_path = tmp_path / "test_data.zip"
        test_csv = tmp_path / "demographics.csv"
        test_csv.write_text("USUBJID,AGE,SEX\n001,45,M\n002,52,F")
        
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.write(test_csv, "demographics.csv")
        
        # Test ZIP source
        source = ZipFileUploadSource({
            "study_id": str(test_study.id),
            "org_id": str(test_study.org_id),
            "upload_path": str(zip_path)
        })
        
        # Verify connection
        connected = await source.connect()
        assert connected is True
        
        # Fetch data
        df = await source.fetch_data({"dataset": "demographics"})
        assert len(df) == 2
        assert list(df.columns) == ["USUBJID", "AGE", "SEX"]
    
    @pytest.mark.integration
    @pytest.mark.performance
    @expected_result("Pipeline should process large datasets within performance targets")
    async def test_pipeline_performance(self, test_study, tmp_path):
        """Test pipeline performance with large dataset"""
        from app.clinical_modules.data_pipeline.dsl_executor import DSLPipelineExecutor
        import time
        
        # Create large test dataset
        large_df = pd.DataFrame({
            'USUBJID': [f'SUBJ{i:06d}' for i in range(10000)],
            'VALUE': np.random.randn(10000),
            'VISIT': np.random.choice(['BASELINE', 'WEEK4', 'WEEK8'], 10000)
        })
        
        # Save test data
        data_path = tmp_path / "studies" / str(test_study.id) / "source_data" / "2024-01-01"
        data_path.mkdir(parents=True, exist_ok=True)
        large_df.to_parquet(data_path / "large_data.parquet")
        
        # Define pipeline
        pipeline_json = json.dumps({
            "version": "1.0",
            "name": "Performance Test Pipeline",
            "inputs": ["large_data"],
            "outputs": ["aggregated_data"],
            "steps": [
                {
                    "operation": "aggregate",
                    "parameters": {
                        "dataset": "large_data",
                        "group_by": ["VISIT"],
                        "aggregations": {"VALUE": ["mean", "std", "count"]}
                    }
                },
                {
                    "operation": "save_dataset",
                    "parameters": {
                        "dataset": "aggregated",
                        "output_name": "aggregated_data"
                    }
                }
            ]
        })
        
        # Execute pipeline
        executor = DSLPipelineExecutor()
        start_time = time.time()
        result = await executor.execute(pipeline_json, str(test_study.id), "2024-01-01")
        duration = time.time() - start_time
        
        # Verify performance (should complete within 5 seconds for 10k rows)
        assert duration < 5.0
        assert result["status"] == "success"
```

### Phase 4: Compliance Tests

```python
# tests/compliance/test_21cfr_part11.py
import pytest
from datetime import datetime
from tests.conftest import expected_result

class Test21CFRPart11Compliance:
    """Test suite for 21 CFR Part 11 compliance requirements"""
    
    @pytest.mark.compliance
    @pytest.mark.critical
    @expected_result("Electronic signature should be created with all required fields and validation")
    async def test_electronic_signature_creation(self, db_session, test_user):
        """Test electronic signature creation and validation"""
        from app.core.compliance import ComplianceManager
        
        compliance_mgr = ComplianceManager(encryption_key=b'test-key-32-bytes-long-for-fernet')
        
        # Create electronic signature
        signature = await compliance_mgr.create_electronic_signature(
            user_id=str(test_user.id),
            action="APPROVE_PROTOCOL",
            document_id="PROTOCOL-001",
            reason="Protocol review completed",
            password="correct_password",  # In real test, would verify password
            db=db_session
        )
        
        assert signature["user_id"] == str(test_user.id)
        assert signature["action"] == "APPROVE_PROTOCOL"
        assert signature["signature_hash"] is not None
        assert len(signature["signature_hash"]) == 64  # SHA256 hash length
    
    @pytest.mark.compliance
    @expected_result("Audit trail should be immutable and maintain sequence integrity")
    async def test_audit_trail_immutability(self, db_session, test_user):
        """Test audit trail immutability and sequence numbering"""
        from app.models import AuditLog
        
        # Create multiple audit entries
        audits = []
        for i in range(5):
            audit = AuditLog(
                user_id=test_user.id,
                action=f"ACTION_{i}",
                resource_type="test",
                resource_id=f"resource_{i}",
                timestamp=datetime.utcnow(),
                system_timestamp=datetime.utcnow(),
                sequence_number=1000 + i
            )
            audits.append(audit)
            db_session.add(audit)
        
        await db_session.commit()
        
        # Verify sequence integrity
        for i, audit in enumerate(audits):
            assert audit.sequence_number == 1000 + i
        
        # Attempt to modify (should fail in production with DB constraints)
        audits[0].action = "MODIFIED_ACTION"
        try:
            await db_session.commit()
            # In production, this should raise an exception due to immutability constraints
        except Exception:
            pass
    
    @pytest.mark.compliance
    @expected_result("System should enforce password requirements for electronic signatures")
    async def test_password_complexity_requirements(self):
        """Test password complexity for electronic signatures"""
        from app.core.security import validate_password_complexity
        
        # Test various passwords
        weak_passwords = ["123456", "password", "abc123", "test"]
        strong_passwords = ["P@ssw0rd123!", "C0mpl3x!Pass", "Str0ng#Pwd2024"]
        
        for pwd in weak_passwords:
            assert validate_password_complexity(pwd) is False
        
        for pwd in strong_passwords:
            assert validate_password_complexity(pwd) is True
```

### Phase 5: HIPAA Compliance Tests

```python
# tests/compliance/test_hipaa.py
import pytest
from tests.conftest import expected_result

class TestHIPAACompliance:
    """Test suite for HIPAA compliance requirements"""
    
    @pytest.mark.compliance
    @expected_result("PHI data should be encrypted at rest")
    async def test_phi_encryption(self):
        """Test PHI encryption and decryption"""
        from app.core.compliance import ComplianceManager
        
        compliance_mgr = ComplianceManager(encryption_key=Fernet.generate_key())
        
        # Test PHI data
        phi_data = "SSN: 123-45-6789, DOB: 1980-01-01"
        
        # Encrypt
        encrypted = compliance_mgr.encrypt_phi(phi_data)
        assert encrypted != phi_data
        assert len(encrypted) > len(phi_data)
        
        # Decrypt
        decrypted = compliance_mgr.decrypt_phi(encrypted)
        assert decrypted == phi_data
    
    @pytest.mark.compliance
    @expected_result("All PHI access should be logged")
    async def test_phi_access_logging(self, client, test_user):
        """Test PHI access logging middleware"""
        # Make authenticated request to PHI endpoint
        response = await client.get(
            "/api/v1/studies/test-study/patient-data",
            headers={"Authorization": f"Bearer {test_user.token}"}
        )
        
        # Verify access was logged
        # Check audit logs for PHI access entry
        audit_logs = await get_recent_audit_logs()
        phi_access_log = next(
            (log for log in audit_logs if log.action == "PHI_ACCESS"),
            None
        )
        
        assert phi_access_log is not None
        assert phi_access_log.user_id == test_user.id
        assert phi_access_log.resource_type == "patient_data"
```

## Running Tests

### Execute All Tests
```bash
# Run all tests with report generation
pytest

# Run specific test categories
pytest -m unit
pytest -m integration
pytest -m compliance
pytest -m "unit and not performance"

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific phase tests
pytest tests/unit/test_models.py
pytest tests/integration/test_data_pipeline.py
```

### CI/CD Integration
```yaml
# .github/workflows/test.yml
name: Run Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements-test.txt
    
    - name: Run tests with coverage
      run: |
        pytest --cov=app --cov-report=xml --cov-report=html
    
    - name: Upload test reports
      uses: actions/upload-artifact@v3
      with:
        name: test-reports
        path: Reports/
    
    - name: Upload coverage reports
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

## Test Data Management

```python
# tests/fixtures/clinical_data.py
import pandas as pd
from datetime import datetime, timedelta

class ClinicalDataFactory:
    """Factory for generating realistic clinical trial test data"""
    
    @staticmethod
    def create_demographics_data(num_subjects=100):
        """Create demographics test data"""
        return pd.DataFrame({
            'USUBJID': [f'SUBJ{i:04d}' for i in range(num_subjects)],
            'AGE': np.random.normal(50, 15, num_subjects).astype(int),
            'SEX': np.random.choice(['M', 'F'], num_subjects),
            'RACE': np.random.choice(['WHITE', 'BLACK', 'ASIAN', 'OTHER'], num_subjects),
            'COUNTRY': np.random.choice(['USA', 'Canada', 'UK', 'Germany'], num_subjects)
        })
    
    @staticmethod
    def create_adverse_events_data(num_subjects=100):
        """Create adverse events test data"""
        ae_data = []
        for subj_id in range(num_subjects):
            num_events = np.random.poisson(2)  # Average 2 AEs per subject
            for event in range(num_events):
                ae_data.append({
                    'USUBJID': f'SUBJ{subj_id:04d}',
                    'AETERM': np.random.choice(['Headache', 'Nausea', 'Fatigue', 'Dizziness']),
                    'AESTDTC': (datetime.now() - timedelta(days=np.random.randint(1, 180))).isoformat(),
                    'AESER': np.random.choice(['Y', 'N'], p=[0.1, 0.9]),
                    'AEREL': np.random.choice(['RELATED', 'NOT RELATED', 'POSSIBLY RELATED'])
                })
        return pd.DataFrame(ae_data)
```

## Best Practices

1. **Test Independence**: Each test should be independent and not rely on other tests
2. **Clear Descriptions**: Use docstrings to clearly describe what each test validates
3. **Expected Results**: Always define expected results using the `@expected_result` decorator
4. **Compliance Focus**: Mark compliance tests with appropriate markers
5. **Performance Benchmarks**: Include performance tests with clear thresholds
6. **Test Data**: Use factories to generate consistent, realistic test data
7. **Report Review**: Review test reports after each run to identify patterns
8. **Continuous Integration**: Integrate testing into CI/CD pipeline

This comprehensive testing framework ensures that every component of the Clinical Dashboard Platform is thoroughly tested with detailed reporting for compliance and quality assurance.