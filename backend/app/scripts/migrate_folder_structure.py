# ABOUTME: Script to migrate existing data folders to unified structure
# ABOUTME: Handles migration from old paths to new /data/studies/{org_id}/{study_id}/source_data/{timestamp} format

import os
import shutil
from pathlib import Path
from datetime import datetime
import json
import logging
from typing import Dict, List, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def convert_ddmmmyyyy_to_timestamp(date_str: str) -> str:
    """
    Convert DDMMMYYYY format to YYYYMMDD_HHMMSS format.
    Since we don't have time info, we'll use 000000 for time.
    """
    try:
        # Parse DDMMMYYYY format
        month_map = {
            'JAN': '01', 'FEB': '02', 'MAR': '03', 'APR': '04',
            'MAY': '05', 'JUN': '06', 'JUL': '07', 'AUG': '08',
            'SEP': '09', 'OCT': '10', 'NOV': '11', 'DEC': '12'
        }
        
        day = date_str[:2]
        month_abbr = date_str[2:5]
        year = date_str[5:9]
        
        month = month_map.get(month_abbr, '01')
        
        # Return in new format with 000000 for time
        return f"{year}{month}{day}_000000"
    except:
        # If conversion fails, return current timestamp
        return datetime.utcnow().strftime("%Y%m%d_%H%M%S")


def migrate_data_folders(base_path: str = "/data/studies", dry_run: bool = True) -> Dict[str, List[str]]:
    """
    Migrate data folders to unified structure.
    
    Args:
        base_path: Base path where study data is stored
        dry_run: If True, only report what would be done without making changes
        
    Returns:
        Dictionary with migration results
    """
    results = {
        "migrated": [],
        "skipped": [],
        "errors": []
    }
    
    base_path_obj = Path(base_path)
    
    if not base_path_obj.exists():
        logger.error(f"Base path does not exist: {base_path}")
        return results
    
    logger.info(f"Starting migration scan in: {base_path}")
    if dry_run:
        logger.info("DRY RUN MODE - No changes will be made")
    
    # Look for organization folders
    for org_folder in base_path_obj.iterdir():
        if not org_folder.is_dir():
            continue
            
        org_id = org_folder.name
        
        # Look for study folders
        for study_folder in org_folder.iterdir():
            if not study_folder.is_dir():
                continue
                
            study_id = study_folder.name
            
            # Check for old structure patterns
            
            # Pattern 1: /data/studies/{study_id}/source_data/{timestamp}
            # (missing org_id in path)
            old_source_data = base_path_obj / study_id / "source_data"
            if old_source_data.exists():
                logger.info(f"Found old structure (missing org_id): {old_source_data}")
                for timestamp_folder in old_source_data.iterdir():
                    if timestamp_folder.is_dir():
                        old_path = timestamp_folder
                        new_path = base_path_obj / org_id / study_id / "source_data" / timestamp_folder.name
                        
                        if dry_run:
                            logger.info(f"Would migrate: {old_path} -> {new_path}")
                            results["migrated"].append(str(old_path))
                        else:
                            try:
                                new_path.parent.mkdir(parents=True, exist_ok=True)
                                shutil.move(str(old_path), str(new_path))
                                logger.info(f"Migrated: {old_path} -> {new_path}")
                                results["migrated"].append(str(old_path))
                            except Exception as e:
                                logger.error(f"Error migrating {old_path}: {e}")
                                results["errors"].append(f"{old_path}: {str(e)}")
            
            # Pattern 2: /data/studies/{org_id}/{study_id}/raw/uploads/{DDMMMYYYY}
            # (old date format and different subfolder structure)
            old_raw_uploads = study_folder / "raw" / "uploads"
            if old_raw_uploads.exists():
                logger.info(f"Found old structure (raw/uploads): {old_raw_uploads}")
                for date_folder in old_raw_uploads.iterdir():
                    if date_folder.is_dir():
                        # Check if it's DDMMMYYYY format
                        folder_name = date_folder.name
                        if len(folder_name) == 9 and folder_name[2:5].isalpha():
                            # Convert date format
                            new_timestamp = convert_ddmmmyyyy_to_timestamp(folder_name)
                            old_path = date_folder
                            new_path = base_path_obj / org_id / study_id / "source_data" / new_timestamp
                            
                            if dry_run:
                                logger.info(f"Would migrate: {old_path} -> {new_path}")
                                results["migrated"].append(str(old_path))
                            else:
                                try:
                                    new_path.parent.mkdir(parents=True, exist_ok=True)
                                    shutil.move(str(old_path), str(new_path))
                                    logger.info(f"Migrated: {old_path} -> {new_path}")
                                    results["migrated"].append(str(old_path))
                                except Exception as e:
                                    logger.error(f"Error migrating {old_path}: {e}")
                                    results["errors"].append(f"{old_path}: {str(e)}")
            
            # Check if already in correct structure
            correct_source_data = study_folder / "source_data"
            if correct_source_data.exists():
                for timestamp_folder in correct_source_data.iterdir():
                    if timestamp_folder.is_dir() and "_" in timestamp_folder.name:
                        # Check if it's already in YYYYMMDD_HHMMSS format
                        if len(timestamp_folder.name) == 15 and timestamp_folder.name[8] == "_":
                            logger.debug(f"Already in correct format: {timestamp_folder}")
                            results["skipped"].append(str(timestamp_folder))
    
    # Summary
    logger.info("\n=== Migration Summary ===")
    logger.info(f"Folders to migrate: {len(results['migrated'])}")
    logger.info(f"Folders already correct: {len(results['skipped'])}")
    logger.info(f"Errors: {len(results['errors'])}")
    
    if results['errors']:
        logger.error("\nErrors encountered:")
        for error in results['errors']:
            logger.error(f"  - {error}")
    
    return results


def create_migration_report(results: Dict[str, List[str]], output_file: str = "migration_report.json"):
    """
    Create a detailed migration report.
    """
    report = {
        "timestamp": datetime.utcnow().isoformat(),
        "summary": {
            "total_migrated": len(results["migrated"]),
            "total_skipped": len(results["skipped"]),
            "total_errors": len(results["errors"])
        },
        "details": results
    }
    
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Migration report saved to: {output_file}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Migrate data folders to unified structure")
    parser.add_argument("--base-path", default="/data/studies", help="Base path for study data")
    parser.add_argument("--execute", action="store_true", help="Execute migration (default is dry run)")
    parser.add_argument("--report", default="migration_report.json", help="Output report file")
    
    args = parser.parse_args()
    
    # Run migration
    results = migrate_data_folders(
        base_path=args.base_path,
        dry_run=not args.execute
    )
    
    # Create report
    create_migration_report(results, args.report)
    
    if not args.execute:
        logger.info("\nThis was a DRY RUN. To execute the migration, run with --execute flag")