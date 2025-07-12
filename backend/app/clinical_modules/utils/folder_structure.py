# ABOUTME: Utility functions for managing folder structures across all data sources
# ABOUTME: Ensures consistent folder naming convention for ALL data sources (manual, API, SFTP)

from pathlib import Path
from datetime import datetime
import uuid
from typing import Optional


def get_timestamp_folder() -> str:
    """
    Generate timestamp folder name in YYYYMMDD_HHMMSS format.
    This is used for ALL data sources to ensure consistency.
    """
    return datetime.utcnow().strftime("%Y%m%d_%H%M%S")


def get_study_data_path(
    org_id: uuid.UUID,
    study_id: uuid.UUID,
    timestamp: Optional[str] = None
) -> Path:
    """
    Get the standardized path for study data storage.
    
    Args:
        org_id: Organization ID
        study_id: Study ID
        timestamp: Timestamp in YYYYMMDD_HHMMSS format (if None, generates from current UTC time)
    
    Returns:
        Path object for the data directory
    """
    if timestamp is None:
        timestamp = get_timestamp_folder()
    
    # Unified path structure for ALL data sources
    data_path = Path("/data/studies") / str(org_id) / str(study_id) / "source_data" / timestamp
    
    return data_path


def ensure_folder_exists(path: Path) -> Path:
    """
    Create folder structure if it doesn't exist.
    
    Args:
        path: Path to create
    
    Returns:
        The created path
    """
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_archive_path(
    org_id: uuid.UUID,
    study_id: uuid.UUID,
    timestamp: str
) -> Path:
    """
    Get the archive path for older data extracts.
    
    Args:
        org_id: Organization ID
        study_id: Study ID
        timestamp: Timestamp in YYYYMMDD_HHMMSS format
    
    Returns:
        Path object for the archive directory
    """
    base_path = Path("/data/studies") / str(org_id) / str(study_id)
    archive_path = base_path / "archive" / timestamp
    
    return archive_path


def validate_timestamp_format(timestamp: str) -> bool:
    """
    Validate timestamp format (YYYYMMDD_HHMMSS).
    
    Args:
        timestamp: Timestamp string to validate
    
    Returns:
        True if valid, False otherwise
    """
    import re
    pattern = re.compile(r'^[0-9]{8}_[0-9]{6}$')
    return bool(pattern.match(timestamp))