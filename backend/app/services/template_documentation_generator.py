# ABOUTME: Template documentation generator for auto-generating comprehensive template documentation
# ABOUTME: Creates user guides, technical docs, and API references from template structures

import uuid
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import json
import markdown
from jinja2 import Environment, BaseLoader, Template

from sqlalchemy.orm import Session
from ..models.dashboard import DashboardTemplate, TemplateVersion, MenuItemType
from ..models.widget import WidgetDefinition
from ..services.template_inheritance import TemplateInheritanceService


class DocumentationType(str, Enum):
    """Types of documentation that can be generated"""
    USER_GUIDE = "user_guide"
    TECHNICAL_REFERENCE = "technical_reference"
    API_DOCUMENTATION = "api_documentation"
    INSTALLATION_GUIDE = "installation_guide"
    WIDGET_REFERENCE = "widget_reference"
    DATA_REQUIREMENTS = "data_requirements"
    COMPLETE_DOCUMENTATION = "complete"


class OutputFormat(str, Enum):
    """Output formats for documentation"""
    MARKDOWN = "markdown"
    HTML = "html"
    PDF = "pdf"
    JSON = "json"


@dataclass
class DocumentationOptions:
    """Options for documentation generation"""
    doc_type: DocumentationType = DocumentationType.COMPLETE_DOCUMENTATION
    output_format: OutputFormat = OutputFormat.MARKDOWN
    include_screenshots: bool = True
    include_code_examples: bool = True
    include_widget_details: bool = True
    include_data_mappings: bool = True
    include_version_history: bool = True
    generate_toc: bool = True
    custom_branding: Optional[Dict[str, str]] = None


@dataclass
class WidgetDocumentation:
    """Documentation for a widget"""
    widget_code: str
    widget_name: str
    description: str
    data_requirements: Dict[str, Any]
    configuration_options: Dict[str, Any]
    position: Dict[str, Any]
    screenshot_url: Optional[str] = None


@dataclass
class MenuDocumentation:
    """Documentation for menu structure"""
    item_id: str
    item_type: str
    label: str
    description: str
    children: List['MenuDocumentation'] = None
    dashboard_info: Optional[Dict[str, Any]] = None


class TemplateDocumentationGenerator:
    """Service for generating comprehensive template documentation"""
    
    def __init__(self, db: Session):
        self.db = db
        self.inheritance_service = TemplateInheritanceService(db)
        self.jinja_env = Environment(loader=BaseLoader())
        
        # Load widget definitions for reference
        self.widget_definitions = self._load_widget_definitions()
    
    def generate_documentation(
        self,
        template_id: uuid.UUID,
        options: DocumentationOptions = None
    ) -> Tuple[str, str]:
        """
        Generate documentation for a template.
        
        Args:
            template_id: Template to document
            options: Documentation generation options
            
        Returns:
            (content, filename)
        """
        if options is None:
            options = DocumentationOptions()
        
        template = self.db.get(DashboardTemplate, template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")
        
        # Get effective template structure
        template_structure = self.inheritance_service.get_effective_template(template_id)
        
        # Generate documentation based on type
        if options.doc_type == DocumentationType.USER_GUIDE:
            content = self._generate_user_guide(template, template_structure, options)
        elif options.doc_type == DocumentationType.TECHNICAL_REFERENCE:
            content = self._generate_technical_reference(template, template_structure, options)
        elif options.doc_type == DocumentationType.API_DOCUMENTATION:
            content = self._generate_api_documentation(template, template_structure, options)
        elif options.doc_type == DocumentationType.INSTALLATION_GUIDE:
            content = self._generate_installation_guide(template, template_structure, options)
        elif options.doc_type == DocumentationType.WIDGET_REFERENCE:
            content = self._generate_widget_reference(template, template_structure, options)
        elif options.doc_type == DocumentationType.DATA_REQUIREMENTS:
            content = self._generate_data_requirements(template, template_structure, options)
        else:  # COMPLETE_DOCUMENTATION
            content = self._generate_complete_documentation(template, template_structure, options)
        
        # Convert to requested format
        if options.output_format == OutputFormat.HTML:
            content = self._convert_to_html(content, options)
        elif options.output_format == OutputFormat.PDF:
            content = self._convert_to_pdf(content, options)
        elif options.output_format == OutputFormat.JSON:
            content = self._convert_to_json(template, template_structure, options)
        
        # Generate filename
        filename = self._generate_filename(template, options)
        
        return content, filename
    
    def _generate_user_guide(
        self,
        template: DashboardTemplate,
        template_structure: Dict[str, Any],
        options: DocumentationOptions
    ) -> str:
        """Generate user-friendly guide for template usage"""
        
        sections = []
        
        # Header
        sections.append(f"# {template.name} - User Guide")
        sections.append(f"*Version {template.version_string}*\n")
        
        # Description
        if template.description:
            sections.append("## Overview")
            sections.append(template.description)
            sections.append("")
        
        # Table of Contents
        if options.generate_toc:
            sections.append("## Table of Contents")
            sections.append("1. [Getting Started](#getting-started)")
            sections.append("2. [Dashboard Overview](#dashboard-overview)")
            sections.append("3. [Using the Widgets](#using-the-widgets)")
            sections.append("4. [Data Requirements](#data-requirements)")
            sections.append("5. [Customization](#customization)")
            sections.append("6. [Troubleshooting](#troubleshooting)")
            sections.append("")
        
        # Getting Started
        sections.append("## Getting Started")
        sections.append("This guide will help you understand and use the dashboard template effectively.")
        sections.append("")
        sections.append("### Prerequisites")
        sections.append("- Access to Clinical Dashboard Platform")
        sections.append("- Required data sources configured")
        sections.append("- Appropriate user permissions")
        sections.append("")
        
        # Dashboard Overview
        sections.append("## Dashboard Overview")
        menu_docs = self._extract_menu_documentation(template_structure)
        for menu_item in menu_docs:
            sections.append(f"### {menu_item.label}")
            if menu_item.description:
                sections.append(menu_item.description)
            
            if menu_item.dashboard_info:
                widget_count = len(menu_item.dashboard_info.get("widgets", []))
                sections.append(f"This dashboard contains {widget_count} widgets providing key insights.")
            sections.append("")
        
        # Widget Usage
        if options.include_widget_details:
            sections.append("## Using the Widgets")
            widget_docs = self._extract_widget_documentation(template_structure)
            
            for widget_doc in widget_docs:
                sections.append(f"### {widget_doc.widget_name}")
                sections.append(widget_doc.description)
                
                if widget_doc.configuration_options:
                    sections.append("**Configuration Options:**")
                    for key, value in widget_doc.configuration_options.items():
                        sections.append(f"- **{key}**: {value}")
                
                sections.append("")
        
        # Data Requirements
        if options.include_data_mappings:
            sections.append("## Data Requirements")
            data_requirements = self._extract_data_requirements(template_structure)
            
            if data_requirements.get("required_datasets"):
                sections.append("### Required Datasets")
                for dataset in data_requirements["required_datasets"]:
                    sections.append(f"- {dataset}")
                sections.append("")
            
            if data_requirements.get("field_mappings"):
                sections.append("### Field Mappings")
                for dataset, fields in data_requirements["field_mappings"].items():
                    sections.append(f"**{dataset}:**")
                    for field in fields:
                        sections.append(f"- {field}")
                    sections.append("")
        
        # Customization
        sections.append("## Customization")
        sections.append("You can customize this template by:")
        sections.append("1. Modifying widget configurations in the admin panel")
        sections.append("2. Adjusting layout and positioning")
        sections.append("3. Adding or removing widgets as needed")
        sections.append("4. Customizing data source mappings")
        sections.append("")
        
        # Troubleshooting
        sections.append("## Troubleshooting")
        sections.append("### Common Issues")
        sections.append("**No data displayed:**")
        sections.append("- Check data source connections")
        sections.append("- Verify field mappings")
        sections.append("- Ensure data exists for the selected time period")
        sections.append("")
        sections.append("**Widgets not loading:**")
        sections.append("- Check widget configuration")
        sections.append("- Verify user permissions")
        sections.append("- Review browser console for errors")
        sections.append("")
        
        return "\n".join(sections)
    
    def _generate_technical_reference(
        self,
        template: DashboardTemplate,
        template_structure: Dict[str, Any],
        options: DocumentationOptions
    ) -> str:
        """Generate technical reference documentation"""
        
        sections = []
        
        # Header
        sections.append(f"# {template.name} - Technical Reference")
        sections.append(f"*Version {template.version_string}*\n")
        
        # Template Information
        sections.append("## Template Information")
        sections.append(f"- **Code**: `{template.code}`")
        sections.append(f"- **Category**: {template.category.value}")
        sections.append(f"- **Version**: {template.version_string}")
        sections.append(f"- **Status**: {template.status.value}")
        sections.append(f"- **Inheritance**: {template.inheritance_type.value}")
        if template.parent_template_id:
            parent = self.db.get(DashboardTemplate, template.parent_template_id)
            if parent:
                sections.append(f"- **Parent Template**: {parent.name} (`{parent.code}`)")
        sections.append("")
        
        # Structure Overview
        sections.append("## Structure Overview")
        sections.append("```json")
        sections.append(json.dumps(template_structure, indent=2))
        sections.append("```")
        sections.append("")
        
        # Menu Structure
        sections.append("## Menu Structure")
        self._document_menu_structure(template_structure.get("menu", {}), sections, 0)
        sections.append("")
        
        # Widget Specifications
        sections.append("## Widget Specifications")
        widget_docs = self._extract_widget_documentation(template_structure)
        
        for widget_doc in widget_docs:
            sections.append(f"### {widget_doc.widget_code}")
            sections.append(f"**Position**: {widget_doc.position}")
            sections.append(f"**Data Requirements**: {widget_doc.data_requirements}")
            sections.append(f"**Configuration**: {widget_doc.configuration_options}")
            sections.append("")
        
        # Data Mappings
        if template_structure.get("data_mappings"):
            sections.append("## Data Mappings")
            sections.append("```json")
            sections.append(json.dumps(template_structure["data_mappings"], indent=2))
            sections.append("```")
            sections.append("")
        
        # Version History
        if options.include_version_history:
            versions = self.db.query(TemplateVersion).filter(
                TemplateVersion.template_id == template.id
            ).order_by(TemplateVersion.created_at.desc()).all()
            
            if versions:
                sections.append("## Version History")
                for version in versions:
                    sections.append(f"### v{version.version_string}")
                    sections.append(f"*Released: {version.created_at.strftime('%Y-%m-%d')}*")
                    if version.change_description:
                        sections.append(version.change_description)
                    if version.breaking_changes:
                        sections.append("⚠️ **Breaking Changes**")
                    sections.append("")
        
        return "\n".join(sections)
    
    def _generate_widget_reference(
        self,
        template: DashboardTemplate,
        template_structure: Dict[str, Any],
        options: DocumentationOptions
    ) -> str:
        """Generate detailed widget reference documentation"""
        
        sections = []
        
        # Header
        sections.append(f"# {template.name} - Widget Reference")
        sections.append(f"*Version {template.version_string}*\n")
        
        # Overview
        widget_docs = self._extract_widget_documentation(template_structure)
        sections.append(f"This template contains {len(widget_docs)} widgets:")
        sections.append("")
        
        # Widget Index
        for i, widget_doc in enumerate(widget_docs, 1):
            sections.append(f"{i}. [{widget_doc.widget_name}](#{widget_doc.widget_code.lower().replace('_', '-')})")
        sections.append("")
        
        # Detailed Widget Documentation
        for widget_doc in widget_docs:
            sections.append(f"## {widget_doc.widget_name}")
            sections.append(f"**Widget Code**: `{widget_doc.widget_code}`")
            sections.append("")
            
            if widget_doc.description:
                sections.append("### Description")
                sections.append(widget_doc.description)
                sections.append("")
            
            # Configuration
            if widget_doc.configuration_options:
                sections.append("### Configuration Options")
                sections.append("| Option | Type | Description | Default |")
                sections.append("|--------|------|-------------|---------|")
                
                for key, value in widget_doc.configuration_options.items():
                    value_type = type(value).__name__
                    sections.append(f"| `{key}` | {value_type} | Configuration option | `{value}` |")
                sections.append("")
            
            # Data Requirements
            if widget_doc.data_requirements:
                sections.append("### Data Requirements")
                
                if widget_doc.data_requirements.get("dataset"):
                    sections.append(f"**Dataset**: {widget_doc.data_requirements['dataset']}")
                
                if widget_doc.data_requirements.get("fields"):
                    sections.append("**Required Fields**:")
                    for field in widget_doc.data_requirements["fields"]:
                        sections.append(f"- `{field}`")
                
                if widget_doc.data_requirements.get("calculation"):
                    sections.append(f"**Calculation**: {widget_doc.data_requirements['calculation']}")
                
                sections.append("")
            
            # Position and Layout
            sections.append("### Position and Layout")
            position = widget_doc.position
            sections.append(f"- **X Position**: {position.get('x', 0)}")
            sections.append(f"- **Y Position**: {position.get('y', 0)}")
            sections.append(f"- **Width**: {position.get('w', 1)} grid units")
            sections.append(f"- **Height**: {position.get('h', 1)} grid units")
            sections.append("")
            
            # Widget Definition Reference
            widget_def = self.widget_definitions.get(widget_doc.widget_code)
            if widget_def:
                sections.append("### Widget Definition")
                sections.append(f"**Category**: {widget_def.category}")
                sections.append(f"**Data Contract**: {widget_def.data_contract}")
                if widget_def.description:
                    sections.append(f"**Description**: {widget_def.description}")
                sections.append("")
        
        return "\n".join(sections)
    
    def _generate_data_requirements(
        self,
        template: DashboardTemplate,
        template_structure: Dict[str, Any],
        options: DocumentationOptions
    ) -> str:
        """Generate data requirements documentation"""
        
        sections = []
        
        # Header
        sections.append(f"# {template.name} - Data Requirements")
        sections.append(f"*Version {template.version_string}*\n")
        
        # Overview
        sections.append("## Overview")
        sections.append("This document outlines the data requirements for the template.")
        sections.append("")
        
        # Extract all data requirements
        all_requirements = self._extract_comprehensive_data_requirements(template_structure)
        
        # Required Datasets
        if all_requirements["datasets"]:
            sections.append("## Required Datasets")
            sections.append("The following datasets must be available:")
            sections.append("")
            
            for dataset in sorted(all_requirements["datasets"]):
                sections.append(f"### {dataset}")
                
                # Get fields for this dataset
                dataset_fields = all_requirements["field_mappings"].get(dataset, [])
                if dataset_fields:
                    sections.append("**Required Fields:**")
                    for field in sorted(dataset_fields):
                        sections.append(f"- `{field}`")
                
                # Get widgets using this dataset
                using_widgets = all_requirements["dataset_usage"].get(dataset, [])
                if using_widgets:
                    sections.append("**Used by widgets:**")
                    for widget in using_widgets:
                        sections.append(f"- {widget}")
                
                sections.append("")
        
        # Field Mappings
        sections.append("## Field Mappings Reference")
        sections.append("| Dataset | Field | Type | Required | Used By |")
        sections.append("|---------|-------|------|----------|---------|")
        
        for dataset, fields in all_requirements["field_mappings"].items():
            for field in sorted(fields):
                using_widgets = all_requirements["field_usage"].get(f"{dataset}.{field}", [])
                widget_list = ", ".join(using_widgets) if using_widgets else "N/A"
                sections.append(f"| {dataset} | `{field}` | string | Yes | {widget_list} |")
        
        sections.append("")
        
        # Data Quality Requirements
        sections.append("## Data Quality Requirements")
        sections.append("### General Requirements")
        sections.append("- All required fields must be present")
        sections.append("- Date fields should be in ISO 8601 format")
        sections.append("- Numeric fields should not contain null values unless specified")
        sections.append("- Text fields should be properly encoded (UTF-8)")
        sections.append("")
        
        # Calculations
        calculations = all_requirements["calculations"]
        if calculations:
            sections.append("## Calculation Requirements")
            for calc_type, widgets in calculations.items():
                sections.append(f"### {calc_type.title()} Calculations")
                sections.append(f"Used by: {', '.join(widgets)}")
                sections.append("")
        
        # Performance Considerations
        sections.append("## Performance Considerations")
        sections.append("- Ensure proper indexing on frequently queried fields")
        sections.append("- Consider data archival for large historical datasets")
        sections.append("- Monitor query performance for complex calculations")
        sections.append("")
        
        return "\n".join(sections)
    
    def _generate_complete_documentation(
        self,
        template: DashboardTemplate,
        template_structure: Dict[str, Any],
        options: DocumentationOptions
    ) -> str:
        """Generate complete documentation combining all sections"""
        
        sections = []
        
        # Title Page
        sections.append(f"# {template.name}")
        sections.append(f"## Complete Documentation")
        sections.append(f"*Version {template.version_string}*")
        sections.append(f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
        sections.append("")
        
        if template.description:
            sections.append("## Description")
            sections.append(template.description)
            sections.append("")
        
        # Table of Contents
        sections.append("## Table of Contents")
        sections.append("1. [Template Information](#template-information)")
        sections.append("2. [User Guide](#user-guide)")
        sections.append("3. [Technical Reference](#technical-reference)")
        sections.append("4. [Widget Reference](#widget-reference)")
        sections.append("5. [Data Requirements](#data-requirements)")
        sections.append("6. [Installation Guide](#installation-guide)")
        sections.append("")
        
        # Generate each section
        temp_options = DocumentationOptions(
            doc_type=DocumentationType.TECHNICAL_REFERENCE,
            output_format=options.output_format,
            include_screenshots=options.include_screenshots,
            include_widget_details=options.include_widget_details,
            include_version_history=options.include_version_history,
            generate_toc=False
        )
        
        # Technical Reference
        sections.append("## Template Information")
        tech_ref = self._generate_technical_reference(template, template_structure, temp_options)
        sections.append(tech_ref.split("## Template Information")[1].split("## Structure Overview")[0])
        
        # User Guide
        sections.append("## User Guide")
        temp_options.doc_type = DocumentationType.USER_GUIDE
        user_guide = self._generate_user_guide(template, template_structure, temp_options)
        sections.append(user_guide.split("# ")[1].split("## Table of Contents")[0])
        
        # Widget Reference
        sections.append("## Widget Reference")
        temp_options.doc_type = DocumentationType.WIDGET_REFERENCE
        widget_ref = self._generate_widget_reference(template, template_structure, temp_options)
        sections.append(widget_ref.split("*Version")[1].split("This template contains")[1])
        
        # Data Requirements
        sections.append("## Data Requirements")
        temp_options.doc_type = DocumentationType.DATA_REQUIREMENTS
        data_req = self._generate_data_requirements(template, template_structure, temp_options)
        sections.append(data_req.split("## Overview")[1])
        
        # Installation Guide
        sections.append("## Installation Guide")
        temp_options.doc_type = DocumentationType.INSTALLATION_GUIDE
        install_guide = self._generate_installation_guide(template, template_structure, temp_options)
        sections.append(install_guide.split("*Version")[1])
        
        return "\n".join(sections)
    
    def _generate_installation_guide(
        self,
        template: DashboardTemplate,
        template_structure: Dict[str, Any],
        options: DocumentationOptions
    ) -> str:
        """Generate installation and setup guide"""
        
        sections = []
        
        # Header
        sections.append(f"# {template.name} - Installation Guide")
        sections.append(f"*Version {template.version_string}*\n")
        
        # Prerequisites
        sections.append("## Prerequisites")
        sections.append("Before installing this template, ensure you have:")
        sections.append("- Clinical Dashboard Platform v2.0 or higher")
        sections.append("- Administrator access to the system")
        sections.append("- Required data sources configured")
        sections.append("")
        
        # Installation Steps
        sections.append("## Installation Steps")
        sections.append("### 1. Download Template")
        sections.append("Download the template file from the marketplace or import the JSON file.")
        sections.append("")
        
        sections.append("### 2. Import Template")
        sections.append("1. Navigate to Admin > Dashboard Templates")
        sections.append("2. Click 'Import Template'")
        sections.append("3. Select the downloaded template file")
        sections.append("4. Review the import settings")
        sections.append("5. Click 'Import'")
        sections.append("")
        
        sections.append("### 3. Configure Data Sources")
        data_requirements = self._extract_data_requirements(template_structure)
        if data_requirements.get("required_datasets"):
            sections.append("Configure the following data sources:")
            for dataset in data_requirements["required_datasets"]:
                sections.append(f"- {dataset}")
            sections.append("")
        
        sections.append("### 4. Assign to Studies")
        sections.append("1. Navigate to Studies")
        sections.append("2. Select the study to apply the template")
        sections.append("3. Go to Dashboard Configuration")
        sections.append("4. Select this template")
        sections.append("5. Configure study-specific settings")
        sections.append("")
        
        # Configuration
        sections.append("## Configuration")
        sections.append("### Data Mapping")
        sections.append("Map your data fields to the template requirements:")
        
        if data_requirements.get("field_mappings"):
            for dataset, fields in data_requirements["field_mappings"].items():
                sections.append(f"**{dataset}:**")
                for field in fields:
                    sections.append(f"- {field}")
                sections.append("")
        
        sections.append("### Widget Customization")
        sections.append("Customize widget settings as needed:")
        sections.append("1. Enter edit mode for the dashboard")
        sections.append("2. Click on any widget to configure")
        sections.append("3. Adjust titles, colors, and calculations")
        sections.append("4. Save changes")
        sections.append("")
        
        # Verification
        sections.append("## Verification")
        sections.append("To verify the installation:")
        sections.append("1. Check that all widgets load without errors")
        sections.append("2. Verify data is displaying correctly")
        sections.append("3. Test all dashboard navigation")
        sections.append("4. Review data refresh functionality")
        sections.append("")
        
        # Troubleshooting
        sections.append("## Troubleshooting")
        sections.append("### Common Issues")
        sections.append("**Import fails:**")
        sections.append("- Check template file format")
        sections.append("- Verify you have admin permissions")
        sections.append("- Ensure no naming conflicts")
        sections.append("")
        
        sections.append("**No data showing:**")
        sections.append("- Verify data source connections")
        sections.append("- Check field mappings")
        sections.append("- Review data permissions")
        sections.append("")
        
        return "\n".join(sections)
    
    def _generate_api_documentation(
        self,
        template: DashboardTemplate,
        template_structure: Dict[str, Any],
        options: DocumentationOptions
    ) -> str:
        """Generate API documentation for template"""
        
        sections = []
        
        # Header
        sections.append(f"# {template.name} - API Documentation")
        sections.append(f"*Version {template.version_string}*\n")
        
        # API Endpoints
        sections.append("## API Endpoints")
        sections.append("### Template Information")
        sections.append(f"**GET** `/api/v1/templates/{template.id}`")
        sections.append("Returns complete template information")
        sections.append("")
        
        sections.append("### Template Structure")
        sections.append(f"**GET** `/api/v1/templates/{template.id}/structure`")
        sections.append("Returns the template structure with resolved inheritance")
        sections.append("")
        
        # Data Contracts
        sections.append("## Data Contracts")
        widget_docs = self._extract_widget_documentation(template_structure)
        
        for widget_doc in widget_docs:
            sections.append(f"### {widget_doc.widget_code}")
            sections.append("**Request Format:**")
            sections.append("```json")
            sections.append(json.dumps(widget_doc.data_requirements, indent=2))
            sections.append("```")
            sections.append("")
        
        return "\n".join(sections)
    
    def _extract_menu_documentation(self, template_structure: Dict[str, Any]) -> List[MenuDocumentation]:
        """Extract menu structure for documentation"""
        menu_docs = []
        
        menu = template_structure.get("menu", {})
        items = menu.get("items", [])
        
        for item in items:
            menu_doc = MenuDocumentation(
                item_id=item.get("id", ""),
                item_type=item.get("type", ""),
                label=item.get("label", ""),
                description=item.get("description", ""),
                dashboard_info=item.get("dashboard")
            )
            menu_docs.append(menu_doc)
        
        return menu_docs
    
    def _extract_widget_documentation(self, template_structure: Dict[str, Any]) -> List[WidgetDocumentation]:
        """Extract widget information for documentation"""
        widget_docs = []
        
        menu = template_structure.get("menu", {})
        items = menu.get("items", [])
        
        for item in items:
            if item.get("type") == "dashboard" and "dashboard" in item:
                dashboard = item["dashboard"]
                widgets = dashboard.get("widgets", [])
                
                for widget in widgets:
                    widget_code = widget.get("widget_code", "")
                    widget_def = self.widget_definitions.get(widget_code)
                    
                    widget_doc = WidgetDocumentation(
                        widget_code=widget_code,
                        widget_name=widget_def.name if widget_def else widget_code.replace("_", " ").title(),
                        description=widget_def.description if widget_def else "",
                        data_requirements=widget.get("data_requirements", {}),
                        configuration_options=widget.get("instance_config", {}),
                        position=widget.get("position", {})
                    )
                    widget_docs.append(widget_doc)
        
        return widget_docs
    
    def _extract_data_requirements(self, template_structure: Dict[str, Any]) -> Dict[str, Any]:
        """Extract data requirements from template structure"""
        return template_structure.get("data_mappings", {})
    
    def _extract_comprehensive_data_requirements(self, template_structure: Dict[str, Any]) -> Dict[str, Any]:
        """Extract comprehensive data requirements including widget-level requirements"""
        
        requirements = {
            "datasets": set(),
            "field_mappings": {},
            "calculations": {},
            "dataset_usage": {},
            "field_usage": {}
        }
        
        # Get template-level data mappings
        data_mappings = template_structure.get("data_mappings", {})
        if data_mappings.get("required_datasets"):
            requirements["datasets"].update(data_mappings["required_datasets"])
        
        if data_mappings.get("field_mappings"):
            requirements["field_mappings"].update(data_mappings["field_mappings"])
        
        # Extract widget-level requirements
        menu = template_structure.get("menu", {})
        items = menu.get("items", [])
        
        for item in items:
            if item.get("type") == "dashboard" and "dashboard" in item:
                dashboard = item["dashboard"]
                widgets = dashboard.get("widgets", [])
                
                for widget in widgets:
                    widget_code = widget.get("widget_code", "")
                    data_req = widget.get("data_requirements", {})
                    
                    if data_req.get("dataset"):
                        dataset = data_req["dataset"]
                        requirements["datasets"].add(dataset)
                        
                        # Track usage
                        if dataset not in requirements["dataset_usage"]:
                            requirements["dataset_usage"][dataset] = []
                        requirements["dataset_usage"][dataset].append(widget_code)
                    
                    if data_req.get("fields"):
                        dataset = data_req.get("dataset", "")
                        fields = data_req["fields"]
                        
                        if dataset:
                            if dataset not in requirements["field_mappings"]:
                                requirements["field_mappings"][dataset] = set()
                            requirements["field_mappings"][dataset].update(fields)
                            
                            # Track field usage
                            for field in fields:
                                field_key = f"{dataset}.{field}"
                                if field_key not in requirements["field_usage"]:
                                    requirements["field_usage"][field_key] = []
                                requirements["field_usage"][field_key].append(widget_code)
                    
                    if data_req.get("calculation"):
                        calc = data_req["calculation"]
                        if calc not in requirements["calculations"]:
                            requirements["calculations"][calc] = []
                        requirements["calculations"][calc].append(widget_code)
        
        # Convert sets to lists for JSON serialization
        requirements["datasets"] = list(requirements["datasets"])
        for dataset in requirements["field_mappings"]:
            if isinstance(requirements["field_mappings"][dataset], set):
                requirements["field_mappings"][dataset] = list(requirements["field_mappings"][dataset])
        
        return requirements
    
    def _document_menu_structure(self, menu: Dict[str, Any], sections: List[str], level: int):
        """Recursively document menu structure"""
        items = menu.get("items", [])
        
        for item in items:
            indent = "  " * level
            item_type = item.get("type", "")
            label = item.get("label", "")
            
            sections.append(f"{indent}- **{label}** ({item_type})")
            
            if item.get("dashboard"):
                dashboard = item["dashboard"]
                widget_count = len(dashboard.get("widgets", []))
                sections.append(f"{indent}  - Contains {widget_count} widgets")
    
    def _load_widget_definitions(self) -> Dict[str, WidgetDefinition]:
        """Load widget definitions for reference"""
        widgets = self.db.query(WidgetDefinition).all()
        return {widget.code: widget for widget in widgets}
    
    def _convert_to_html(self, content: str, options: DocumentationOptions) -> str:
        """Convert markdown content to HTML"""
        html = markdown.markdown(content, extensions=['tables', 'toc', 'codehilite'])
        
        # Add basic styling if custom branding is provided
        if options.custom_branding:
            style = f"""
            <style>
                body {{ font-family: {options.custom_branding.get('font_family', 'Arial, sans-serif')}; }}
                h1, h2, h3 {{ color: {options.custom_branding.get('primary_color', '#333')}; }}
                .header {{ background-color: {options.custom_branding.get('header_bg', '#f8f9fa')}; }}
            </style>
            """
            html = f"<html><head>{style}</head><body>{html}</body></html>"
        
        return html
    
    def _convert_to_pdf(self, content: str, options: DocumentationOptions) -> str:
        """Convert content to PDF (placeholder - would need library like weasyprint)"""
        # This would require a PDF generation library
        # For now, return HTML version
        return self._convert_to_html(content, options)
    
    def _convert_to_json(
        self,
        template: DashboardTemplate,
        template_structure: Dict[str, Any],
        options: DocumentationOptions
    ) -> str:
        """Convert documentation to structured JSON"""
        
        doc_data = {
            "template": {
                "id": str(template.id),
                "code": template.code,
                "name": template.name,
                "description": template.description,
                "version": template.version_string,
                "category": template.category.value,
                "created_at": template.created_at.isoformat()
            },
            "structure": template_structure,
            "widgets": [asdict(widget) for widget in self._extract_widget_documentation(template_structure)],
            "menu": [asdict(menu) for menu in self._extract_menu_documentation(template_structure)],
            "data_requirements": self._extract_comprehensive_data_requirements(template_structure),
            "generated_at": datetime.utcnow().isoformat()
        }
        
        return json.dumps(doc_data, indent=2, default=str)
    
    def _generate_filename(self, template: DashboardTemplate, options: DocumentationOptions) -> str:
        """Generate appropriate filename for documentation"""
        
        base_name = template.code.replace(" ", "_").lower()
        doc_type = options.doc_type.value
        timestamp = datetime.now().strftime("%Y%m%d")
        
        if options.output_format == OutputFormat.HTML:
            extension = "html"
        elif options.output_format == OutputFormat.PDF:
            extension = "pdf"
        elif options.output_format == OutputFormat.JSON:
            extension = "json"
        else:
            extension = "md"
        
        return f"{base_name}_{doc_type}_{timestamp}.{extension}"