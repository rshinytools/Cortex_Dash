# ABOUTME: Widget mapping service for simplified dropdown-based data mapping
# ABOUTME: Maps uploaded dataset columns to widget requirements

from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid
from sqlmodel import Session, select
from fastapi import HTTPException

from app.models.widget import Widget
from app.models.data_source_upload import DataSourceUpload
from app.models.widget_instance_mapping import WidgetInstanceMapping
from app.core.logging import logger

class WidgetMappingService:
    """Service for mapping data to widgets"""
    
    # Widget field requirements by type
    WIDGET_REQUIREMENTS = {
        "metric": {
            "required": ["value", "label"],
            "optional": ["target", "unit", "trend_value"]
        },
        "timeseries": {
            "required": ["date", "value", "series"],
            "optional": ["lower_bound", "upper_bound"]
        },
        "categorical": {
            "required": ["category", "value"],
            "optional": ["percentage", "color"]
        },
        "heatmap": {
            "required": ["x_axis", "y_axis", "value"],
            "optional": ["label", "tooltip"]
        },
        "scatter": {
            "required": ["x_value", "y_value"],
            "optional": ["size", "color", "label", "group"]
        }
    }
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_widget_requirements(self, widget_type: str) -> Dict[str, List[str]]:
        """Get field requirements for a widget type"""
        
        return self.WIDGET_REQUIREMENTS.get(
            widget_type, 
            {"required": [], "optional": []}
        )
    
    def get_available_mappings(
        self, 
        study_id: str, 
        widget_id: str
    ) -> Dict[str, Any]:
        """Get available datasets and columns for mapping"""
        
        # Get widget
        widget = self.db.get(Widget, widget_id)
        if not widget:
            raise HTTPException(status_code=404, detail="Widget not found")
        
        # Get widget requirements
        requirements = self.get_widget_requirements(widget.widget_type)
        
        # Get available datasets
        from app.services.data.upload_service import DataUploadService
        upload_service = DataUploadService(self.db)
        datasets = upload_service.get_available_datasets(study_id)
        
        # Format response
        return {
            "widget": {
                "id": widget.id,
                "name": widget.name,
                "type": widget.widget_type,
                "requirements": requirements
            },
            "available_datasets": datasets,
            "current_mappings": self._get_current_mappings(widget_id)
        }
    
    def create_mapping(
        self,
        widget_id: str,
        upload_id: str,
        dataset_name: str,
        field_mappings: Dict[str, str],
        user_id: str
    ) -> WidgetInstanceMapping:
        """Create or update widget mapping"""
        
        # Validate widget
        widget = self.db.get(Widget, widget_id)
        if not widget:
            raise HTTPException(status_code=404, detail="Widget not found")
        
        # Validate upload
        upload = self.db.get(DataSourceUpload, upload_id)
        if not upload:
            raise HTTPException(status_code=404, detail="Upload not found")
        
        # Validate required fields are mapped
        requirements = self.get_widget_requirements(widget.widget_type)
        for required_field in requirements["required"]:
            if required_field not in field_mappings:
                raise HTTPException(
                    status_code=400,
                    detail=f"Required field '{required_field}' not mapped"
                )
        
        # Check if mapping exists
        stmt = select(WidgetInstanceMapping).where(
            WidgetInstanceMapping.widget_id == widget_id
        )
        existing = self.db.exec(stmt).first()
        
        if existing:
            # Update existing mapping
            existing.data_upload_id = upload_id
            existing.dataset_name = dataset_name
            existing.field_mappings = field_mappings
            existing.updated_at = datetime.utcnow()
            existing.updated_by = user_id
            
            self.db.add(existing)
            self.db.commit()
            self.db.refresh(existing)
            
            return existing
        else:
            # Create new mapping
            mapping = WidgetInstanceMapping(
                id=str(uuid.uuid4()),
                widget_id=widget_id,
                data_upload_id=upload_id,
                dataset_name=dataset_name,
                field_mappings=field_mappings,
                is_active=True,
                created_by=user_id
            )
            
            self.db.add(mapping)
            self.db.commit()
            self.db.refresh(mapping)
            
            return mapping
    
    def validate_mapping(
        self,
        widget_type: str,
        dataset_columns: List[str],
        field_mappings: Dict[str, str]
    ) -> Dict[str, Any]:
        """Validate if mapping is complete and valid"""
        
        requirements = self.get_widget_requirements(widget_type)
        validation_result = {
            "is_valid": True,
            "missing_required": [],
            "invalid_columns": [],
            "warnings": []
        }
        
        # Check required fields
        for required_field in requirements["required"]:
            if required_field not in field_mappings:
                validation_result["is_valid"] = False
                validation_result["missing_required"].append(required_field)
        
        # Check column existence
        for widget_field, data_column in field_mappings.items():
            if data_column not in dataset_columns:
                validation_result["is_valid"] = False
                validation_result["invalid_columns"].append({
                    "field": widget_field,
                    "column": data_column
                })
        
        # Add warnings for unmapped optional fields
        for optional_field in requirements.get("optional", []):
            if optional_field not in field_mappings:
                validation_result["warnings"].append(
                    f"Optional field '{optional_field}' is not mapped"
                )
        
        return validation_result
    
    def get_mapping_suggestions(
        self,
        widget_type: str,
        dataset_columns: List[Dict[str, str]]
    ) -> Dict[str, str]:
        """Suggest automatic mappings based on column names"""
        
        requirements = self.get_widget_requirements(widget_type)
        suggestions = {}
        
        # Common column name patterns
        patterns = {
            "value": ["value", "val", "result", "score", "amount", "count"],
            "label": ["label", "name", "title", "description", "category"],
            "date": ["date", "datetime", "time", "period", "visit", "visitdat"],
            "category": ["category", "cat", "type", "group", "class"],
            "series": ["series", "group", "cohort", "arm", "treatment"],
            "target": ["target", "goal", "threshold", "limit"],
            "unit": ["unit", "units", "uom"],
            "x_axis": ["x", "x_val", "x_value"],
            "y_axis": ["y", "y_val", "y_value"],
            "x_value": ["x", "x_val", "independent"],
            "y_value": ["y", "y_val", "dependent"]
        }
        
        column_names = [col["name"].lower() for col in dataset_columns]
        
        # Try to match required and optional fields
        all_fields = requirements["required"] + requirements.get("optional", [])
        
        for field in all_fields:
            if field in patterns:
                for pattern in patterns[field]:
                    for idx, col_name in enumerate(column_names):
                        if pattern in col_name:
                            suggestions[field] = dataset_columns[idx]["name"]
                            break
                    if field in suggestions:
                        break
        
        return suggestions
    
    def _get_current_mappings(self, widget_id: str) -> Optional[Dict[str, Any]]:
        """Get current mappings for a widget"""
        
        stmt = select(WidgetInstanceMapping).where(
            WidgetInstanceMapping.widget_id == widget_id,
            WidgetInstanceMapping.is_active == True
        )
        
        mapping = self.db.exec(stmt).first()
        
        if mapping:
            return {
                "upload_id": mapping.data_upload_id,
                "dataset_name": mapping.dataset_name,
                "field_mappings": mapping.field_mappings,
                "created_at": mapping.created_at.isoformat(),
                "updated_at": mapping.updated_at.isoformat() if mapping.updated_at else None
            }
        
        return None
    
    def delete_mapping(self, widget_id: str) -> bool:
        """Delete widget mapping"""
        
        stmt = select(WidgetInstanceMapping).where(
            WidgetInstanceMapping.widget_id == widget_id
        )
        
        mapping = self.db.exec(stmt).first()
        
        if mapping:
            self.db.delete(mapping)
            self.db.commit()
            return True
        
        return False