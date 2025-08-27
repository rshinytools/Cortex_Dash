# Backup System Fix Summary

## Issue Identified
The backup system was only backing up the database and a single metadata.json file, but not the actual study data files (parquet files, dataset-specific metadata, etc.).

## Root Cause
The backup service was looking for study files in `/data/studies/` but the actual directory structure was:
```
/data/{organization_id}/studies/{study_id}/source_data/{timestamp}/
```

## Fix Applied

### 1. Updated `backup_service.py`
- Changed `self.studies_dir = Path("/data/studies")` to `self.data_dir = Path("/data")`
- Modified the file copying logic to iterate through organization directories
- Now backs up the complete structure: `/data/{org_id}/studies/{study_id}/`

### 2. Updated `restore_service.py`
- Changed to handle the new directory structure
- Added backward compatibility for old backup format
- Restores files to the correct `/data/{org_id}/studies/` structure

## Files Modified
1. `backend/app/services/backup/backup_service.py`
2. `backend/app/services/backup/restore_service.py`

## Backup Types
- **full**: Backs up database + all study data files
- **database**: Only backs up the database
- **files**: Only backs up study data files

## Directory Structure Backed Up
```
backup.zip
├── metadata.json
├── database.sql (if full or database type)
└── {org_id}/
    └── studies/
        └── {study_id}/
            └── source_data/
                └── {timestamp}/
                    ├── *.parquet
                    └── *_metadata.json
```

## Testing Required
After restarting the backend container, create a new "full" backup and verify it contains:
1. metadata.json
2. database.sql
3. All organization folders with study data

## Next Steps
1. Get a fresh authentication token
2. Create a new full backup: 
   ```bash
   curl -X POST "http://localhost:8000/api/v1/backup" \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"description": "Full backup with all data", "backup_type": "full"}'
   ```
3. Verify backup contents contain study files
4. Test restore functionality with the new backup format