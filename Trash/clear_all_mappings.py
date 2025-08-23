# ABOUTME: Script to clear ALL field mappings from a study
# ABOUTME: Allows starting fresh with manual mapping configuration

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
import uuid

# Create database engine
engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))

def clear_all_mappings(study_id: str = None):
    """Clear all field mappings from specified study or all studies"""
    with Session(engine) as db:
        if study_id:
            # Clear mappings for specific study
            study = db.get(Study, uuid.UUID(study_id))
            if study:
                print(f"\nStudy: {study.name} ({study.id})")
                print(f"Current mappings: {json.dumps(study.field_mappings, indent=2)}")
                
                # Clear all mappings
                study.field_mappings = {}
                
                # Mark the field as modified so SQLAlchemy knows to update it
                from sqlalchemy.orm.attributes import flag_modified
                flag_modified(study, "field_mappings")
                
                db.add(study)
                db.commit()
                print(f"\nAll mappings cleared for study: {study.name}")
            else:
                print(f"Study {study_id} not found")
        else:
            # Clear mappings for all studies
            studies = db.exec(select(Study)).all()
            
            for study in studies:
                if study.field_mappings:
                    print(f"\nStudy: {study.name} ({study.id})")
                    print(f"Current mappings: {json.dumps(study.field_mappings, indent=2)}")
                    
                    # Clear all mappings
                    study.field_mappings = {}
                    
                    # Mark the field as modified so SQLAlchemy knows to update it
                    from sqlalchemy.orm.attributes import flag_modified
                    flag_modified(study, "field_mappings")
                    
                    db.add(study)
                    print(f"  All mappings cleared")
            
            db.commit()
            print("\nAll mappings cleared successfully!")

if __name__ == "__main__":
    # Clear mappings for the Demo study
    clear_all_mappings("521b4b98-87ec-4643-9103-eae78e2dad79")