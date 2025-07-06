# ABOUTME: Utility functions for managing folder structures across all data sources
# ABOUTME: Ensures consistent folder naming convention for API, SFTP, and manual uploads

from pathlib import Path
from datetime import datetime
import uuid
from typing import Optional


def get_extract_date_folder() -> str:
    """
    Generate extract date folder name in DDMMMYYYY format.
    This is used when data is pulled from API or SFTP sources.
    """
    now = datetime.utcnow()
    month_names = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 
                   'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
    
    day = now.strftime('%d')
    month = month_names[now.month - 1]
    year = now.strftime('%Y')
    
    return f"{day}{month}{year}"


def get_study_data_path(
    org_id: uuid.UUID,
    study_id: uuid.UUID,
    extract_date: Optional[str] = None,
    data_type: str = "raw"
) -> Path:
    """
    Get the standardized path for study data storage.
    
    Args:
        org_id: Organization ID
        study_id: Study ID
        extract_date: Extract date in DDMMMYYYY format (if None, generates from current date)
        data_type: Type of data (raw, processed, etc.)
    
    Returns:
        Path object for the data directory
    """
    if extract_date is None:
        extract_date = get_extract_date_folder()
    
    base_path = Path("/data/studies") / str(org_id) / str(study_id)
    data_path = base_path / data_type / "uploads" / extract_date
    
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
    extract_date: str
) -> Path:
    """
    Get the archive path for older data extracts.
    
    Args:
        org_id: Organization ID
        study_id: Study ID
        extract_date: Extract date in DDMMMYYYY format
    
    Returns:
        Path object for the archive directory
    """
    base_path = Path("/data/studies") / str(org_id) / str(study_id)
    archive_path = base_path / "archive" / extract_date
    
    return archive_path


def validate_extract_date_format(extract_date: str) -> bool:
    """
    Validate extract date format (DDMMMYYYY).
    
    Args:
        extract_date: Date string to validate
    
    Returns:
        True if valid, False otherwise
    """
    import re
    pattern = re.compile(r'^[0-9]{2}[A-Z]{3}[0-9]{4}$')
    return bool(pattern.match(extract_date))