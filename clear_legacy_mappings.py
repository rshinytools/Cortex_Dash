# ABOUTME: Script to clear legacy hardcoded field mappings from the database
# ABOUTME: Removes old mappings like subject_enrolled and total_sae that shouldn't exist

import os
import sys
from pathlib import Path

# Add the backend directory to the Python path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from sqlmodel import Session, select, create_engine
from app.models.study import Study
from app.core.config import settings
import json

# Create database engine
engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))

def clear_legacy_mappings():
    """Remove legacy hardcoded mappings from all studies"""
    with Session(engine) as db:
        # Get all studies
        studies = db.exec(select(Study)).all()
        
        for study in studies:
            if study.field_mappings:
                print(f"\nStudy: {study.name} ({study.id})")
                print(f"Current mappings: {json.dumps(study.field_mappings, indent=2)}")
                
                # Remove legacy mappings
                legacy_keys = ["subject_enrolled", "total_sae"]
                modified = False
                
                for key in legacy_keys:
                    if key in study.field_mappings:
                        del study.field_mappings[key]
                        modified = True
                        print(f"  - Removed legacy mapping: {key}")
                
                if modified:
                    # Mark the field as modified so SQLAlchemy knows to update it
                    from sqlalchemy.orm.attributes import flag_modified
                    flag_modified(study, "field_mappings")
                    
                    db.add(study)
                    print(f"  Updated mappings: {json.dumps(study.field_mappings, indent=2)}")
                else:
                    print("  No legacy mappings found")
        
        db.commit()
        print("\nLegacy mappings cleared successfully!")

if __name__ == "__main__":
    clear_legacy_mappings()