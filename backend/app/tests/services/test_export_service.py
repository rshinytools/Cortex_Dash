# ABOUTME: Comprehensive test suite for dashboard export functionality
# ABOUTME: Tests PDF, Excel, PowerPoint, and image export capabilities with various configurations

import pytest
import uuid
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from typing import Dict, Any, List
import json
from datetime import datetime

from app.services.export_service import (
    ExportService, 
    ExportFormat, 
    ExportRequest,
    PDFExporter,
    ExcelExporter,
    PowerPointExporter,
    ImageExporter,
    ExportResult
)
from app.models.dashboard import StudyDashboard, DashboardTemplate
from app.models.study import Study
from app.models.organization import Organization


class TestExportService:
    """Test suite for main ExportService class"""

    @pytest.fixture
    def export_service(self) -> ExportService:
        """Create ExportService instance for testing"""
        return ExportService()

    @pytest.fixture
    def sample_dashboard_data(self) -> Dict[str, Any]:
        """Create sample dashboard data for export testing"""
        return {
            "dashboard_info": {
                "id": str(uuid.uuid4()),
                "name": "Test Dashboard",
                "description": "Dashboard for testing exports",
                "study_name": "Test Study 001",
                "organization": "Test Organization",
                "generated_at": datetime.now().isoformat()
            },
            "widgets": [
                {
                    "id": "widget1",
                    "type": "metric",
                    "title": "Total Subjects",
                    "value": 150,
                    "format": "number",
                    "position": {"x": 0, "y": 0, "w": 4, "h": 2}
                },
                {
                    "id": "widget2",
                    "type": "chart",
                    "title": "Age Distribution",
                    "chart_type": "bar",
                    "data": [
                        {"category": "18-30", "value": 45},
                        {"category": "31-45", "value": 60},
                        {"category": "46-60", "value": 35},
                        {"category": "60+", "value": 10}
                    ],
                    "position": {"x": 4, "y": 0, "w": 8, "h": 4}
                },
                {
                    "id": "widget3",
                    "type": "table",
                    "title": "Subject Demographics",
                    "data": [
                        {"subject_id": "S001", "age": 25, "gender": "M"},
                        {"subject_id": "S002", "age": 30, "gender": "F"},
                        {"subject_id": "S003", "age": 35, "gender": "M"}
                    ],
                    "columns": ["subject_id", "age", "gender"],
                    "position": {"x": 0, "y": 4, "w": 12, "h": 4}
                }
            ],
            "metadata": {
                "total_widgets": 3,
                "export_timestamp": datetime.now().isoformat(),
                "data_freshness": "2024-01-07T10:00:00Z"
            }
        }

    @pytest.fixture
    def export_request(self) -> ExportRequest:
        """Create sample export request"""
        return ExportRequest(
            dashboard_id=str(uuid.uuid4()),
            format=ExportFormat.PDF,
            include_data=True,
            include_metadata=True,
            custom_options={
                "orientation": "landscape",
                "include_charts": True,
                "page_size": "A4"
            }
        )

    def test_export_service_initialization(self, export_service):
        """Test ExportService initialization"""
        assert export_service is not None
        assert hasattr(export_service, 'pdf_exporter')
        assert hasattr(export_service, 'excel_exporter')
        assert hasattr(export_service, 'powerpoint_exporter')
        assert hasattr(export_service, 'image_exporter')

    @pytest.mark.asyncio
    async def test_export_dashboard_pdf(self, export_service, sample_dashboard_data, export_request):
        """Test PDF dashboard export"""
        export_request.format = ExportFormat.PDF
        
        with patch.object(export_service.pdf_exporter, 'export_dashboard') as mock_export:
            mock_export.return_value = ExportResult(
                success=True,
                file_path="/tmp/test_dashboard.pdf",
                file_size=1024000,
                export_time=2.5
            )
            
            result = await export_service.export_dashboard(export_request, sample_dashboard_data)
            
            assert result.success is True
            assert result.file_path.endswith('.pdf')
            assert result.file_size > 0
            mock_export.assert_called_once()

    @pytest.mark.asyncio
    async def test_export_dashboard_excel(self, export_service, sample_dashboard_data, export_request):
        """Test Excel dashboard export"""
        export_request.format = ExportFormat.EXCEL
        
        with patch.object(export_service.excel_exporter, 'export_dashboard') as mock_export:
            mock_export.return_value = ExportResult(
                success=True,
                file_path="/tmp/test_dashboard.xlsx",
                file_size=512000,
                export_time=1.8
            )
            
            result = await export_service.export_dashboard(export_request, sample_dashboard_data)
            
            assert result.success is True
            assert result.file_path.endswith('.xlsx')
            mock_export.assert_called_once()

    @pytest.mark.asyncio
    async def test_export_dashboard_powerpoint(self, export_service, sample_dashboard_data, export_request):
        """Test PowerPoint dashboard export"""
        export_request.format = ExportFormat.POWERPOINT
        
        with patch.object(export_service.powerpoint_exporter, 'export_dashboard') as mock_export:
            mock_export.return_value = ExportResult(
                success=True,
                file_path="/tmp/test_dashboard.pptx",
                file_size=2048000,
                export_time=3.2
            )
            
            result = await export_service.export_dashboard(export_request, sample_dashboard_data)
            
            assert result.success is True
            assert result.file_path.endswith('.pptx')
            mock_export.assert_called_once()

    @pytest.mark.asyncio
    async def test_export_dashboard_image(self, export_service, sample_dashboard_data, export_request):
        """Test image dashboard export"""
        export_request.format = ExportFormat.PNG
        
        with patch.object(export_service.image_exporter, 'export_dashboard') as mock_export:
            mock_export.return_value = ExportResult(
                success=True,
                file_path="/tmp/test_dashboard.png",
                file_size=256000,
                export_time=1.2
            )
            
            result = await export_service.export_dashboard(export_request, sample_dashboard_data)
            
            assert result.success is True
            assert result.file_path.endswith('.png')
            mock_export.assert_called_once()

    @pytest.mark.asyncio
    async def test_export_dashboard_error_handling(self, export_service, sample_dashboard_data, export_request):
        """Test export error handling"""
        with patch.object(export_service.pdf_exporter, 'export_dashboard') as mock_export:
            mock_export.side_effect = Exception("Export failed")
            
            result = await export_service.export_dashboard(export_request, sample_dashboard_data)
            
            assert result.success is False
            assert "Export failed" in result.error_message

    def test_validate_export_request(self, export_service, export_request):
        """Test export request validation"""
        # Valid request
        is_valid, errors = export_service.validate_export_request(export_request)
        assert is_valid is True
        assert len(errors) == 0
        
        # Invalid request - missing dashboard_id
        export_request.dashboard_id = ""
        is_valid, errors = export_service.validate_export_request(export_request)
        assert is_valid is False
        assert len(errors) > 0

    def test_get_supported_formats(self, export_service):
        """Test getting supported export formats"""
        formats = export_service.get_supported_formats()
        
        assert ExportFormat.PDF in formats
        assert ExportFormat.EXCEL in formats
        assert ExportFormat.POWERPOINT in formats
        assert ExportFormat.PNG in formats


class TestPDFExporter:
    """Test suite for PDFExporter"""

    @pytest.fixture
    def pdf_exporter(self) -> PDFExporter:
        """Create PDFExporter instance for testing"""
        return PDFExporter()

    @pytest.fixture
    def sample_dashboard_data(self) -> Dict[str, Any]:
        """Create sample dashboard data for PDF testing"""
        return {
            "dashboard_info": {
                "name": "Clinical Overview Dashboard",
                "study_name": "ONCOLOGY-001",
                "generated_at": datetime.now().isoformat()
            },
            "widgets": [
                {
                    "type": "metric",
                    "title": "Total Enrolled",
                    "value": 245,
                    "format": "number"
                },
                {
                    "type": "chart",
                    "title": "Enrollment by Site",
                    "chart_type": "bar",
                    "data": [
                        {"site": "Site 001", "enrolled": 45},
                        {"site": "Site 002", "enrolled": 38},
                        {"site": "Site 003", "enrolled": 52}
                    ]
                }
            ]
        }

    @patch('app.services.export_service.FPDF')
    def test_pdf_export_basic(self, mock_fpdf, pdf_exporter, sample_dashboard_data):
        """Test basic PDF export functionality"""
        mock_pdf_instance = MagicMock()
        mock_fpdf.return_value = mock_pdf_instance
        
        options = {
            "orientation": "landscape",
            "page_size": "A4",
            "include_charts": True
        }
        
        result = pdf_exporter.export_dashboard(sample_dashboard_data, options)
        
        assert result.success is True
        assert result.file_path.endswith('.pdf')
        mock_pdf_instance.add_page.assert_called()
        mock_pdf_instance.output.assert_called()

    @patch('app.services.export_service.FPDF')
    def test_pdf_export_with_header_footer(self, mock_fpdf, pdf_exporter, sample_dashboard_data):
        """Test PDF export with custom header and footer"""
        mock_pdf_instance = MagicMock()
        mock_fpdf.return_value = mock_pdf_instance
        
        options = {
            "include_header": True,
            "include_footer": True,
            "header_text": "Clinical Trial Dashboard",
            "footer_text": "Confidential - Study ONCOLOGY-001"
        }
        
        result = pdf_exporter.export_dashboard(sample_dashboard_data, options)
        
        assert result.success is True
        # Verify header and footer are added
        mock_pdf_instance.cell.assert_called()

    @patch('app.services.export_service.matplotlib.pyplot')
    def test_pdf_chart_rendering(self, mock_plt, pdf_exporter):
        """Test chart rendering for PDF export"""
        chart_data = {
            "type": "chart",
            "chart_type": "bar",
            "title": "Test Chart",
            "data": [
                {"category": "A", "value": 10},
                {"category": "B", "value": 15},
                {"category": "C", "value": 8}
            ]
        }
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            chart_path = pdf_exporter._render_chart_for_pdf(chart_data, temp_file.name)
            
            assert chart_path is not None
            mock_plt.figure.assert_called()
            mock_plt.savefig.assert_called()
            
            # Cleanup
            os.unlink(temp_file.name)

    def test_pdf_table_formatting(self, pdf_exporter):
        """Test table formatting for PDF"""
        table_data = {
            "type": "table",
            "title": "Subject Demographics",
            "data": [
                {"subject_id": "S001", "age": 25, "gender": "M"},
                {"subject_id": "S002", "age": 30, "gender": "F"}
            ],
            "columns": ["subject_id", "age", "gender"]
        }
        
        formatted_table = pdf_exporter._format_table_for_pdf(table_data)
        
        assert formatted_table is not None
        assert len(formatted_table['rows']) == 2
        assert formatted_table['headers'] == ["subject_id", "age", "gender"]

    def test_pdf_metric_formatting(self, pdf_exporter):
        """Test metric formatting for PDF"""
        metric_data = {
            "type": "metric",
            "title": "Total Subjects",
            "value": 1250,
            "format": "number",
            "trend": "up",
            "change": 5.2
        }
        
        formatted_metric = pdf_exporter._format_metric_for_pdf(metric_data)
        
        assert formatted_metric['value'] == "1,250"
        assert formatted_metric['title'] == "Total Subjects"
        assert "trend" in formatted_metric


class TestExcelExporter:
    """Test suite for ExcelExporter"""

    @pytest.fixture
    def excel_exporter(self) -> ExcelExporter:
        """Create ExcelExporter instance for testing"""
        return ExcelExporter()

    @pytest.fixture
    def sample_dashboard_data(self) -> Dict[str, Any]:
        """Create sample dashboard data for Excel testing"""
        return {
            "dashboard_info": {
                "name": "Safety Analysis Dashboard",
                "study_name": "CARDIO-002"
            },
            "widgets": [
                {
                    "type": "table",
                    "title": "Adverse Events Summary",
                    "data": [
                        {"event": "Headache", "count": 12, "severity": "Mild"},
                        {"event": "Nausea", "count": 8, "severity": "Moderate"},
                        {"event": "Fatigue", "count": 15, "severity": "Mild"}
                    ]
                },
                {
                    "type": "chart",
                    "title": "AE by Severity",
                    "data": [
                        {"severity": "Mild", "count": 27},
                        {"severity": "Moderate", "count": 8},
                        {"severity": "Severe", "count": 2}
                    ]
                }
            ]
        }

    @patch('app.services.export_service.openpyxl')
    def test_excel_export_basic(self, mock_openpyxl, excel_exporter, sample_dashboard_data):
        """Test basic Excel export functionality"""
        mock_workbook = MagicMock()
        mock_worksheet = MagicMock()
        mock_openpyxl.Workbook.return_value = mock_workbook
        mock_workbook.active = mock_worksheet
        
        options = {
            "include_charts": True,
            "separate_sheets": True,
            "apply_formatting": True
        }
        
        result = excel_exporter.export_dashboard(sample_dashboard_data, options)
        
        assert result.success is True
        assert result.file_path.endswith('.xlsx')
        mock_workbook.save.assert_called()

    @patch('app.services.export_service.openpyxl')
    def test_excel_multiple_sheets(self, mock_openpyxl, excel_exporter, sample_dashboard_data):
        """Test Excel export with multiple sheets"""
        mock_workbook = MagicMock()
        mock_openpyxl.Workbook.return_value = mock_workbook
        
        options = {"separate_sheets": True}
        
        result = excel_exporter.export_dashboard(sample_dashboard_data, options)
        
        assert result.success is True
        # Should create separate sheets for different widget types
        mock_workbook.create_sheet.assert_called()

    def test_excel_data_formatting(self, excel_exporter):
        """Test Excel data formatting"""
        table_data = {
            "type": "table",
            "data": [
                {"date": "2024-01-01", "value": 1234.56, "percentage": 0.125},
                {"date": "2024-01-02", "value": 2345.67, "percentage": 0.235}
            ]
        }
        
        formatted_data = excel_exporter._format_data_for_excel(table_data)
        
        assert formatted_data is not None
        # Should properly format dates, numbers, and percentages

    @patch('app.services.export_service.openpyxl.chart')
    def test_excel_chart_creation(self, mock_chart, excel_exporter):
        """Test Excel chart creation"""
        chart_data = {
            "type": "chart",
            "chart_type": "bar",
            "title": "Test Chart",
            "data": [
                {"category": "A", "value": 10},
                {"category": "B", "value": 15}
            ]
        }
        
        mock_worksheet = MagicMock()
        
        excel_exporter._create_excel_chart(chart_data, mock_worksheet)
        
        # Should create chart and add to worksheet
        mock_worksheet.add_chart.assert_called()

    def test_excel_styling_application(self, excel_exporter):
        """Test Excel styling and formatting"""
        options = {
            "apply_formatting": True,
            "header_style": "bold",
            "data_style": "normal",
            "chart_style": "colorful"
        }
        
        style_config = excel_exporter._get_style_configuration(options)
        
        assert style_config is not None
        assert style_config['header_style'] == "bold"


class TestPowerPointExporter:
    """Test suite for PowerPointExporter"""

    @pytest.fixture
    def powerpoint_exporter(self) -> PowerPointExporter:
        """Create PowerPointExporter instance for testing"""
        return PowerPointExporter()

    @pytest.fixture
    def sample_dashboard_data(self) -> Dict[str, Any]:
        """Create sample dashboard data for PowerPoint testing"""
        return {
            "dashboard_info": {
                "name": "Executive Summary Dashboard",
                "study_name": "NEURO-003"
            },
            "widgets": [
                {
                    "type": "metric",
                    "title": "Primary Endpoint Met",
                    "value": True,
                    "format": "boolean"
                },
                {
                    "type": "chart",
                    "title": "Efficacy Over Time",
                    "chart_type": "line",
                    "data": [
                        {"week": 1, "efficacy": 45.2},
                        {"week": 4, "efficacy": 52.8},
                        {"week": 8, "efficacy": 61.3}
                    ]
                }
            ]
        }

    @patch('app.services.export_service.pptx.Presentation')
    def test_powerpoint_export_basic(self, mock_presentation, powerpoint_exporter, sample_dashboard_data):
        """Test basic PowerPoint export functionality"""
        mock_prs = MagicMock()
        mock_presentation.return_value = mock_prs
        
        options = {
            "template": "default",
            "slides_per_widget": False,
            "include_title_slide": True
        }
        
        result = powerpoint_exporter.export_dashboard(sample_dashboard_data, options)
        
        assert result.success is True
        assert result.file_path.endswith('.pptx')
        mock_prs.save.assert_called()

    @patch('app.services.export_service.pptx.Presentation')
    def test_powerpoint_template_usage(self, mock_presentation, powerpoint_exporter, sample_dashboard_data):
        """Test PowerPoint export with custom template"""
        mock_prs = MagicMock()
        mock_presentation.return_value = mock_prs
        
        options = {
            "template_path": "/path/to/custom_template.pptx",
            "use_template_layouts": True
        }
        
        result = powerpoint_exporter.export_dashboard(sample_dashboard_data, options)
        
        assert result.success is True
        # Should use custom template if provided

    def test_powerpoint_slide_layout_selection(self, powerpoint_exporter):
        """Test slide layout selection for different widget types"""
        metric_widget = {"type": "metric", "title": "Test Metric"}
        chart_widget = {"type": "chart", "title": "Test Chart"}
        table_widget = {"type": "table", "title": "Test Table"}
        
        metric_layout = powerpoint_exporter._get_slide_layout_for_widget(metric_widget)
        chart_layout = powerpoint_exporter._get_slide_layout_for_widget(chart_widget)
        table_layout = powerpoint_exporter._get_slide_layout_for_widget(table_widget)
        
        # Different widget types should get appropriate layouts
        assert metric_layout != chart_layout
        assert chart_layout != table_layout

    @patch('app.services.export_service.matplotlib.pyplot')
    def test_powerpoint_chart_embedding(self, mock_plt, powerpoint_exporter):
        """Test chart embedding in PowerPoint slides"""
        chart_data = {
            "type": "chart",
            "chart_type": "pie",
            "title": "Distribution Chart",
            "data": [
                {"category": "A", "value": 30},
                {"category": "B", "value": 70}
            ]
        }
        
        mock_slide = MagicMock()
        
        powerpoint_exporter._add_chart_to_slide(chart_data, mock_slide)
        
        # Should create chart image and add to slide
        mock_plt.figure.assert_called()


class TestImageExporter:
    """Test suite for ImageExporter"""

    @pytest.fixture
    def image_exporter(self) -> ImageExporter:
        """Create ImageExporter instance for testing"""
        return ImageExporter()

    @pytest.fixture
    def sample_dashboard_data(self) -> Dict[str, Any]:
        """Create sample dashboard data for image testing"""
        return {
            "widgets": [
                {
                    "type": "metric",
                    "title": "Key Metric",
                    "value": 85.7,
                    "position": {"x": 0, "y": 0, "w": 6, "h": 3}
                },
                {
                    "type": "chart",
                    "title": "Trend Chart", 
                    "position": {"x": 6, "y": 0, "w": 6, "h": 6}
                }
            ]
        }

    @patch('app.services.export_service.html2canvas')
    def test_image_export_png(self, mock_html2canvas, image_exporter, sample_dashboard_data):
        """Test PNG image export"""
        options = {
            "format": "png",
            "width": 1920,
            "height": 1080,
            "quality": 90
        }
        
        result = image_exporter.export_dashboard(sample_dashboard_data, options)
        
        assert result.success is True
        assert result.file_path.endswith('.png')

    @patch('app.services.export_service.html2canvas')
    def test_image_export_jpeg(self, mock_html2canvas, image_exporter, sample_dashboard_data):
        """Test JPEG image export"""
        options = {
            "format": "jpeg",
            "width": 1600,
            "height": 900,
            "quality": 85
        }
        
        result = image_exporter.export_dashboard(sample_dashboard_data, options)
        
        assert result.success is True
        assert result.file_path.endswith('.jpg')

    def test_image_resolution_calculation(self, image_exporter):
        """Test image resolution calculation"""
        dashboard_layout = {
            "grid": {"columns": 12, "rows": 8},
            "width": 1200,
            "height": 800
        }
        
        options = {"width": 1920, "height": 1080}
        
        calculated_size = image_exporter._calculate_optimal_size(dashboard_layout, options)
        
        assert calculated_size['width'] == 1920
        assert calculated_size['height'] == 1080

    @patch('app.services.export_service.selenium')
    def test_image_browser_rendering(self, mock_selenium, image_exporter, sample_dashboard_data):
        """Test browser-based dashboard rendering for image export"""
        mock_driver = MagicMock()
        mock_selenium.webdriver.Chrome.return_value = mock_driver
        
        options = {"use_browser_rendering": True}
        
        result = image_exporter.export_dashboard(sample_dashboard_data, options)
        
        assert result.success is True
        mock_driver.get_screenshot_as_file.assert_called()


@pytest.mark.integration
class TestExportServiceIntegration:
    """Integration tests for export service"""

    async def test_complete_export_workflow(self, db):
        """Test complete export workflow from dashboard to file"""
        # Test end-to-end export process
        pass

    async def test_concurrent_exports(self, db):
        """Test handling of concurrent export requests"""
        # Test multiple simultaneous export operations
        pass

    async def test_large_dashboard_export(self, db):
        """Test export of dashboards with large amounts of data"""
        # Test performance with large datasets
        pass

    async def test_export_with_real_data(self, db):
        """Test export with real dashboard and data"""
        # Integration test with actual database data
        pass


@pytest.mark.performance
class TestExportServicePerformance:
    """Performance tests for export service"""

    def test_pdf_export_performance(self):
        """Test PDF export performance with large dashboards"""
        # Performance test for PDF generation
        pass

    def test_excel_export_memory_usage(self):
        """Test Excel export memory efficiency"""
        # Test memory usage with large datasets
        pass

    def test_image_export_rendering_speed(self):
        """Test image export rendering performance"""
        # Test image generation speed
        pass

    def test_concurrent_export_performance(self):
        """Test performance under concurrent export load"""
        # Load testing for export service
        pass


class TestExportFormatValidation:
    """Test suite for export format validation and error handling"""

    def test_unsupported_format_handling(self):
        """Test handling of unsupported export formats"""
        with pytest.raises(ValueError, match="Unsupported export format"):
            ExportFormat("unsupported_format")

    def test_invalid_export_options(self):
        """Test validation of export options"""
        exporter = ExportService()
        
        invalid_options = {
            "page_size": "Invalid",
            "orientation": "diagonal",  # Invalid orientation
            "quality": 150  # Invalid quality (should be 0-100)
        }
        
        is_valid, errors = exporter._validate_export_options(invalid_options)
        assert is_valid is False
        assert len(errors) > 0

    def test_file_permission_handling(self):
        """Test handling of file permission errors during export"""
        # Test export to read-only directory
        pass

    def test_disk_space_handling(self):
        """Test handling of insufficient disk space"""
        # Test export when disk space is limited
        pass