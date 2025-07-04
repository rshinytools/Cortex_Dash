# ABOUTME: File service for managing study folder structures and permissions
# ABOUTME: Creates compliant folder hierarchy for clinical data storage with 21 CFR Part 11 considerations

import os
import json
import stat
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from app.models import Study
from app.core.config import settings


class FileService:
    """Service for managing study file structures and permissions"""
    
    def __init__(self, base_path: Optional[str] = None):
        self.base_path = base_path or settings.DATA_STORAGE_PATH
        
    async def initialize_study_folders(self, study: Study) -> None:
        """Create all required folders for a new study with proper permissions"""
        
        study_root = Path(self.base_path) / str(study.org_id) / str(study.id)
        
        # Define folder structure
        folders = [
            # Raw data folders (will be read-only after data upload)
            study_root / "raw" / "medidata",           # Medidata Rave extracts
            study_root / "raw" / "uploads",            # Manual ZIP uploads
            study_root / "raw" / "archive",            # Old versions
            
            # Processed data folders
            study_root / "processed" / "current",      # Latest processed data
            study_root / "processed" / "archive",      # Historical processed data
            
            # Analysis folders
            study_root / "analysis" / "datasets",      # Analysis-ready data
            study_root / "analysis" / "scripts",       # Transformation scripts
            
            # Export folders
            study_root / "exports" / "pdf",
            study_root / "exports" / "excel",
            study_root / "exports" / "powerpoint",
            study_root / "exports" / "scheduled",      # Scheduled report outputs
            
            # Supporting folders
            study_root / "temp",                       # Temporary processing files
            study_root / "logs",                       # Pipeline execution logs
            study_root / "metadata",                   # Data dictionaries, mappings
            study_root / "config",                     # Study-specific configurations
        ]
        
        # Create all folders
        for folder in folders:
            folder.mkdir(parents=True, exist_ok=True)
            
        # Set permissions for 21 CFR Part 11 compliance
        self._set_folder_permissions(study_root)
        
        # Create initial metadata files
        await self._create_initial_metadata(study, study_root)
        
        # Update study record with folder path
        study.folder_path = str(study_root)
        
    def _set_folder_permissions(self, study_root: Path) -> None:
        """Set appropriate permissions for study folders"""
        
        # Skip on Windows
        if os.name == 'nt':
            return
            
        # Set permissions for all folders
        # Owner: read, write, execute (7)
        # Group: read, execute (5) 
        # Others: no access (0)
        for root, dirs, files in os.walk(study_root):
            for dir_name in dirs:
                dir_path = Path(root) / dir_name
                try:
                    os.chmod(dir_path, 0o750)
                except Exception:
                    pass  # Handle permission errors gracefully
                    
            for file_name in files:
                file_path = Path(root) / file_name
                try:
                    os.chmod(file_path, 0o640)
                except Exception:
                    pass
                    
    def _set_raw_folder_readonly(self, raw_folder: str) -> None:
        """Make raw data folder read-only after data upload (21 CFR Part 11)"""
        
        # Skip on Windows
        if os.name == 'nt':
            return
            
        try:
            # Remove write permissions - owner and group can only read and execute
            os.chmod(raw_folder, 0o550)
            
            # Make all files in raw folder read-only
            for root, dirs, files in os.walk(raw_folder):
                for file_name in files:
                    file_path = Path(root) / file_name
                    os.chmod(file_path, 0o440)  # Read-only for owner and group
        except Exception:
            pass  # Handle permission errors gracefully
            
    async def _create_initial_metadata(self, study: Study, study_root: Path) -> None:
        """Create initial metadata files for the study"""
        
        # Version history
        version_history = {
            "study_id": str(study.id),
            "study_name": study.name,
            "protocol_number": study.protocol_number,
            "created_at": datetime.utcnow().isoformat(),
            "versions": []
        }
        
        # Data dictionary template
        data_dictionary = {
            "study_id": str(study.id),
            "datasets": {},
            "created_at": datetime.utcnow().isoformat(),
            "last_updated": datetime.utcnow().isoformat()
        }
        
        # Field mappings template
        field_mappings = {
            "study_id": str(study.id),
            "source_to_standard": {},
            "standard_to_analysis": {},
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Pipeline config template
        pipeline_config = {
            "study_id": str(study.id),
            "data_sources": [],
            "transformation_steps": [],
            "schedule": None,
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Dashboard config template
        dashboard_config = {
            "study_id": str(study.id),
            "widgets": [],
            "layout": {
                "grid": [],
                "breakpoints": {"lg": 1200, "md": 996, "sm": 768}
            },
            "refresh_interval": 300,  # 5 minutes
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Save metadata files
        await self._save_json(study_root / "metadata" / "version_history.json", version_history)
        await self._save_json(study_root / "metadata" / "data_dictionary.json", data_dictionary)
        await self._save_json(study_root / "metadata" / "field_mappings.json", field_mappings)
        await self._save_json(study_root / "config" / "pipeline_config.json", pipeline_config)
        await self._save_json(study_root / "config" / "dashboard_config.json", dashboard_config)
        
        # Create README for the study
        readme_content = f"""# Study: {study.name}

## Protocol: {study.protocol_number}

### Folder Structure

- **raw/**: Original source data (read-only after upload)
  - medidata/: Data from Medidata Rave API
  - uploads/: Manually uploaded ZIP files
  - archive/: Previous versions of raw data

- **processed/**: Standardized and cleaned data
  - current/: Latest processed datasets
  - archive/: Historical processed data

- **analysis/**: Derived datasets and analysis scripts
  - datasets/: Analysis-ready data
  - scripts/: Transformation and analysis scripts

- **exports/**: Generated reports and exports
  - pdf/: PDF reports
  - excel/: Excel exports
  - powerpoint/: PowerPoint presentations
  - scheduled/: Automated report outputs

- **metadata/**: Data documentation
  - version_history.json: Track data versions
  - data_dictionary.json: Field definitions
  - field_mappings.json: Source to standard mappings

- **config/**: Study configuration files
  - pipeline_config.json: Data pipeline settings
  - dashboard_config.json: Dashboard layout and widgets

### Compliance Notes

This folder structure supports 21 CFR Part 11 compliance:
- Raw data folders become read-only after data upload
- All changes are tracked in version history
- Audit trail maintained for all operations

Created: {datetime.utcnow().isoformat()}
"""
        
        readme_path = study_root / "README.md"
        readme_path.write_text(readme_content)
        
    async def _save_json(self, file_path: Path, data: Dict[str, Any]) -> None:
        """Save JSON data to file"""
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
            
    def get_study_path(self, org_id: str, study_id: str) -> Path:
        """Get the full path for a study"""
        return Path(self.base_path) / org_id / study_id
        
    def ensure_path_exists(self, path: Path) -> None:
        """Ensure a path exists, creating it if necessary"""
        path.mkdir(parents=True, exist_ok=True)