# ABOUTME: Template export/import service for sharing templates between systems and organizations
# ABOUTME: Handles template packaging, validation, and cross-system compatibility

import uuid
import json
import zipfile
import io
from typing import Dict, Any, List, Optional, Tuple, BinaryIO
from datetime import datetime
from dataclasses import dataclass, asdict
from pathlib import Path
import tempfile

from sqlalchemy.orm import Session
from ..models.dashboard import (
    DashboardTemplate, 
    TemplateVersion, 
    TemplateReview,
    TemplateExportData,
    DashboardCategory,
    TemplateStatus,
    InheritanceType
)
from ..models.user import User
from .template_validator import TemplateValidatorService, ValidationSeverity
from .template_inheritance import TemplateInheritanceService


@dataclass
class ExportOptions:
    """Options for template export"""
    include_versions: bool = True
    include_reviews: bool = False
    include_screenshots: bool = True
    resolve_inheritance: bool = True
    export_format: str = "zip"  # zip, json
    anonymize_data: bool = False


@dataclass
class ImportOptions:
    """Options for template import"""
    validate_structure: bool = True
    update_if_exists: bool = False
    preserve_ids: bool = False
    import_as_draft: bool = True
    assign_to_user: Optional[uuid.UUID] = None


class TemplateExportImportError(Exception):
    """Exception raised during export/import operations"""
    pass


class TemplateExportImportService:
    """Service for exporting and importing templates"""
    
    def __init__(self, db: Session):
        self.db = db
        self.validator = TemplateValidatorService()
        self.inheritance_service = TemplateInheritanceService(db)
    
    def export_template(
        self,
        template_id: uuid.UUID,
        options: ExportOptions = None,
        user_id: Optional[uuid.UUID] = None
    ) -> BinaryIO:
        """
        Export a template with specified options.
        
        Args:
            template_id: Template to export
            options: Export configuration options
            user_id: User performing the export (for permissions)
            
        Returns:
            Binary data of exported template
        """
        if options is None:
            options = ExportOptions()
        
        template = self.db.get(DashboardTemplate, template_id)
        if not template:
            raise TemplateExportImportError(f"Template {template_id} not found")
        
        # Check permissions
        if user_id and not self._can_export_template(template, user_id):
            raise TemplateExportImportError("Insufficient permissions to export template")
        
        # Collect export data
        export_data = self._collect_export_data(template, options)
        
        if options.export_format == "json":
            return self._export_as_json(export_data)
        else:  # zip
            return self._export_as_zip(export_data, options)
    
    def import_template(
        self,
        import_data: BinaryIO,
        options: ImportOptions = None,
        user_id: Optional[uuid.UUID] = None
    ) -> Tuple[uuid.UUID, Dict[str, Any]]:
        """
        Import a template from binary data.
        
        Args:
            import_data: Binary data of template to import
            options: Import configuration options
            user_id: User performing the import
            
        Returns:
            (template_id, import_result)
        """
        if options is None:
            options = ImportOptions()
        
        if not user_id:
            raise TemplateExportImportError("User ID required for import")
        
        # Parse import data
        template_data = self._parse_import_data(import_data)
        
        # Validate template structure
        if options.validate_structure:
            validation_result = self._validate_import_data(template_data)
            if not validation_result["is_valid"]:
                raise TemplateExportImportError(f"Invalid template structure: {validation_result['errors']}")
        
        # Check for existing template
        existing_template = None
        if "template" in template_data and "code" in template_data["template"]:
            existing_template = self.db.query(DashboardTemplate).filter(
                DashboardTemplate.code == template_data["template"]["code"]
            ).first()
        
        if existing_template and not options.update_if_exists:
            raise TemplateExportImportError(
                f"Template with code '{template_data['template']['code']}' already exists"
            )
        
        # Import template
        if existing_template and options.update_if_exists:
            template_id = self._update_existing_template(existing_template, template_data, options, user_id)
        else:
            template_id = self._create_new_template(template_data, options, user_id)
        
        return template_id, {
            "action": "updated" if existing_template else "created",
            "template_id": str(template_id),
            "message": "Template imported successfully"
        }
    
    def export_multiple_templates(
        self,
        template_ids: List[uuid.UUID],
        options: ExportOptions = None,
        user_id: Optional[uuid.UUID] = None
    ) -> BinaryIO:
        """Export multiple templates as a collection"""
        if options is None:
            options = ExportOptions()
        
        collection_data = {
            "export_type": "template_collection",
            "export_timestamp": datetime.utcnow().isoformat(),
            "exported_by": str(user_id) if user_id else None,
            "templates": []
        }
        
        for template_id in template_ids:
            try:
                template = self.db.get(DashboardTemplate, template_id)
                if template and self._can_export_template(template, user_id):
                    template_data = self._collect_export_data(template, options)
                    collection_data["templates"].append(template_data)
            except Exception as e:
                # Log error but continue with other templates
                print(f"Error exporting template {template_id}: {str(e)}")
        
        # Create zip file with all templates
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add collection metadata
            zipf.writestr("collection.json", json.dumps(collection_data, indent=2, default=str))
            
            # Add individual templates
            for i, template_data in enumerate(collection_data["templates"]):
                template_name = template_data.get("template", {}).get("name", f"template_{i}")
                template_filename = f"templates/{template_name.replace(' ', '_').lower()}.json"
                zipf.writestr(template_filename, json.dumps(template_data, indent=2, default=str))
        
        buffer.seek(0)
        return buffer
    
    def _collect_export_data(self, template: DashboardTemplate, options: ExportOptions) -> Dict[str, Any]:
        """Collect all data for template export"""
        
        # Get template structure
        template_structure = template.template_structure
        
        if options.resolve_inheritance and template.parent_template_id:
            # Get effective structure with inheritance resolved
            template_structure = self.inheritance_service.get_effective_template(template.id)
        
        # Base template data
        export_data = {
            "export_type": "single_template",
            "export_timestamp": datetime.utcnow().isoformat(),
            "export_options": asdict(options),
            "template": {
                "code": template.code,
                "name": template.name,
                "description": template.description,
                "category": template.category.value,
                "major_version": template.major_version,
                "minor_version": template.minor_version,
                "patch_version": template.patch_version,
                "status": template.status.value,
                "inheritance_type": template.inheritance_type.value,
                "parent_template_code": None,
                "template_structure": template_structure,
                "tags": template.tags,
                "screenshot_urls": template.screenshot_urls if options.include_screenshots else [],
                "documentation_url": template.documentation_url,
                "is_public": template.is_public,
                "created_at": template.created_at.isoformat(),
                "updated_at": template.updated_at.isoformat()
            }
        }
        
        # Get parent template code if exists
        if template.parent_template_id:
            parent_template = self.db.get(DashboardTemplate, template.parent_template_id)
            if parent_template:
                export_data["template"]["parent_template_code"] = parent_template.code
        
        # Add creator info (anonymized if requested)
        creator = self.db.get(User, template.created_by)
        if creator:
            if options.anonymize_data:
                export_data["template"]["creator"] = {
                    "name": "Anonymous",
                    "email": "anonymous@example.com"
                }
            else:
                export_data["template"]["creator"] = {
                    "name": creator.full_name,
                    "email": creator.email
                }
        
        # Add version history
        if options.include_versions:
            versions = self.db.query(TemplateVersion).filter(
                TemplateVersion.template_id == template.id
            ).order_by(TemplateVersion.created_at).all()
            
            export_data["versions"] = []
            for version in versions:
                version_data = {
                    "major_version": version.major_version,
                    "minor_version": version.minor_version,
                    "patch_version": version.patch_version,
                    "change_description": version.change_description,
                    "template_structure": version.template_structure,
                    "is_published": version.is_published,
                    "migration_notes": version.migration_notes,
                    "breaking_changes": version.breaking_changes,
                    "required_migrations": version.required_migrations,
                    "created_at": version.created_at.isoformat()
                }
                export_data["versions"].append(version_data)
        
        # Add reviews
        if options.include_reviews:
            reviews = self.db.query(TemplateReview).filter(
                TemplateReview.template_id == template.id
            ).all()
            
            export_data["reviews"] = []
            for review in reviews:
                reviewer = self.db.get(User, review.reviewed_by)
                review_data = {
                    "rating": review.rating,
                    "review_text": review.review_text,
                    "is_verified_user": review.is_verified_user,
                    "created_at": review.created_at.isoformat()
                }
                
                if not options.anonymize_data and reviewer:
                    review_data["reviewer"] = {
                        "name": reviewer.full_name,
                        "email": reviewer.email
                    }
                else:
                    review_data["reviewer"] = {
                        "name": "Anonymous",
                        "email": "anonymous@example.com"
                    }
                
                export_data["reviews"].append(review_data)
        
        return export_data
    
    def _export_as_json(self, export_data: Dict[str, Any]) -> BinaryIO:
        """Export data as JSON file"""
        buffer = io.BytesIO()
        json_str = json.dumps(export_data, indent=2, default=str)
        buffer.write(json_str.encode('utf-8'))
        buffer.seek(0)
        return buffer
    
    def _export_as_zip(self, export_data: Dict[str, Any], options: ExportOptions) -> BinaryIO:
        """Export data as ZIP archive"""
        buffer = io.BytesIO()
        
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add main template file
            zipf.writestr("template.json", json.dumps(export_data, indent=2, default=str))
            
            # Add README
            readme_content = self._generate_readme(export_data)
            zipf.writestr("README.md", readme_content)
            
            # Add screenshots if included
            if options.include_screenshots and export_data["template"].get("screenshot_urls"):
                # In a real implementation, download and include actual screenshot files
                zipf.writestr("screenshots/README.txt", "Screenshot files would be included here")
        
        buffer.seek(0)
        return buffer
    
    def _parse_import_data(self, import_data: BinaryIO) -> Dict[str, Any]:
        """Parse import data from binary stream"""
        try:
            # Reset stream position
            import_data.seek(0)
            
            # Try to read as JSON first
            try:
                content = import_data.read().decode('utf-8')
                return json.loads(content)
            except (UnicodeDecodeError, json.JSONDecodeError):
                pass
            
            # Try to read as ZIP
            import_data.seek(0)
            with zipfile.ZipFile(import_data, 'r') as zipf:
                # Look for template.json or collection.json
                if 'template.json' in zipf.namelist():
                    template_content = zipf.read('template.json').decode('utf-8')
                    return json.loads(template_content)
                elif 'collection.json' in zipf.namelist():
                    collection_content = zipf.read('collection.json').decode('utf-8')
                    return json.loads(collection_content)
                else:
                    raise TemplateExportImportError("No valid template file found in ZIP archive")
        
        except Exception as e:
            raise TemplateExportImportError(f"Failed to parse import data: {str(e)}")
    
    def _validate_import_data(self, template_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate imported template data"""
        errors = []
        
        # Check required fields
        if "template" not in template_data:
            errors.append("Missing 'template' section")
            return {"is_valid": False, "errors": errors}
        
        template = template_data["template"]
        required_fields = ["code", "name", "template_structure"]
        
        for field in required_fields:
            if field not in template:
                errors.append(f"Missing required field: {field}")
        
        # Validate template structure
        if "template_structure" in template:
            is_valid, validation_issues = self.validator.validate_template_structure(
                template["template_structure"]
            )
            if not is_valid:
                error_issues = [issue for issue in validation_issues if issue.severity == ValidationSeverity.ERROR]
                errors.extend([issue.message for issue in error_issues])
        
        # Validate category
        if "category" in template:
            try:
                DashboardCategory(template["category"])
            except ValueError:
                errors.append(f"Invalid category: {template['category']}")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": []  # Could add warnings for non-critical issues
        }
    
    def _create_new_template(
        self,
        template_data: Dict[str, Any],
        options: ImportOptions,
        user_id: uuid.UUID
    ) -> uuid.UUID:
        """Create new template from import data"""
        
        template_info = template_data["template"]
        
        # Generate unique code if needed
        code = template_info["code"]
        if not options.preserve_ids:
            original_code = code
            counter = 1
            while self.db.query(DashboardTemplate).filter(DashboardTemplate.code == code).first():
                code = f"{original_code}-imported-{counter}"
                counter += 1
        
        # Create template
        template = DashboardTemplate(
            code=code,
            name=template_info["name"],
            description=template_info.get("description"),
            category=DashboardCategory(template_info.get("category", "custom")),
            major_version=template_info.get("major_version", 1),
            minor_version=template_info.get("minor_version", 0),
            patch_version=template_info.get("patch_version", 0),
            status=TemplateStatus.DRAFT if options.import_as_draft else TemplateStatus.PUBLISHED,
            inheritance_type=InheritanceType(template_info.get("inheritance_type", "none")),
            template_structure=template_info["template_structure"],
            tags=template_info.get("tags", []),
            screenshot_urls=template_info.get("screenshot_urls", []),
            documentation_url=template_info.get("documentation_url"),
            is_public=False if options.import_as_draft else template_info.get("is_public", False),
            created_by=options.assign_to_user or user_id
        )
        
        self.db.add(template)
        self.db.flush()  # Get ID without committing
        
        # Import version history if present
        if "versions" in template_data:
            for version_data in template_data["versions"]:
                version = TemplateVersion(
                    template_id=template.id,
                    major_version=version_data["major_version"],
                    minor_version=version_data["minor_version"],
                    patch_version=version_data["patch_version"],
                    change_description=version_data.get("change_description", "Imported version"),
                    template_structure=version_data["template_structure"],
                    is_published=version_data.get("is_published", False),
                    migration_notes=version_data.get("migration_notes"),
                    breaking_changes=version_data.get("breaking_changes", False),
                    required_migrations=version_data.get("required_migrations"),
                    created_by=user_id
                )
                self.db.add(version)
        
        self.db.commit()
        return template.id
    
    def _update_existing_template(
        self,
        existing_template: DashboardTemplate,
        template_data: Dict[str, Any],
        options: ImportOptions,
        user_id: uuid.UUID
    ) -> uuid.UUID:
        """Update existing template with import data"""
        
        template_info = template_data["template"]
        
        # Update template fields
        existing_template.name = template_info["name"]
        existing_template.description = template_info.get("description")
        existing_template.category = DashboardCategory(template_info.get("category", existing_template.category))
        existing_template.template_structure = template_info["template_structure"]
        existing_template.tags = template_info.get("tags", existing_template.tags)
        existing_template.screenshot_urls = template_info.get("screenshot_urls", existing_template.screenshot_urls)
        existing_template.documentation_url = template_info.get("documentation_url")
        existing_template.updated_at = datetime.utcnow()
        
        # Increment version
        existing_template.minor_version += 1
        
        # Create version entry for the update
        version = TemplateVersion(
            template_id=existing_template.id,
            major_version=existing_template.major_version,
            minor_version=existing_template.minor_version,
            patch_version=existing_template.patch_version,
            change_description="Updated from import",
            template_structure=existing_template.template_structure,
            is_published=not options.import_as_draft,
            created_by=user_id
        )
        
        self.db.add(version)
        self.db.commit()
        
        return existing_template.id
    
    def _can_export_template(self, template: DashboardTemplate, user_id: Optional[uuid.UUID]) -> bool:
        """Check if user can export template"""
        if not user_id:
            return template.is_public
        
        # User can export if they created it or it's public
        return template.created_by == user_id or template.is_public
    
    def _generate_readme(self, export_data: Dict[str, Any]) -> str:
        """Generate README content for exported template"""
        template = export_data["template"]
        
        readme = f"""# {template['name']}

## Description
{template.get('description', 'No description provided')}

## Template Information
- **Code**: `{template['code']}`
- **Category**: {template['category'].title()}
- **Version**: {template['major_version']}.{template['minor_version']}.{template['patch_version']}
- **Status**: {template['status'].title()}

## Tags
{', '.join(template.get('tags', []))}

## Installation
1. Import this template into your Clinical Dashboard Platform
2. Configure data mappings as needed
3. Customize widgets and layout as required

## Requirements
Check the template structure for specific data requirements and field mappings.

## Export Information
- **Exported**: {export_data['export_timestamp']}
- **Export Type**: {export_data['export_type']}

## Support
For support and documentation, visit: {template.get('documentation_url', 'N/A')}
"""
        
        return readme