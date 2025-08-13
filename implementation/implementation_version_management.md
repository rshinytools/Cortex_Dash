# Phase 2.5: Version Management System

## Overview
Implement comprehensive version management for data uploads, allowing users to switch between versions, compare changes, and understand impact before making changes.

## Features to Implement

### 1. Backend API Endpoints

#### Version Activation Endpoint
```python
@router.post("/studies/{study_id}/uploads/{upload_id}/activate")
async def activate_upload_version(
    study_id: uuid.UUID,
    upload_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Activate a specific upload version as the current active version.
    Deactivates all other versions for the study.
    """
```

#### Version Comparison Endpoint
```python
@router.get("/studies/{study_id}/uploads/compare")
async def compare_upload_versions(
    study_id: uuid.UUID,
    version1_id: uuid.UUID = Query(...),
    version2_id: uuid.UUID = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Compare two upload versions, returning:
    - File differences
    - Row count changes
    - Column changes
    - Size differences
    """
```

#### Active Version Endpoint
```python
@router.get("/studies/{study_id}/uploads/active")
async def get_active_version(
    study_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get the currently active upload version for a study.
    """
```

### 2. Frontend Components

#### Version Comparison UI

##### High-Level Summary Comparison
Side-by-side cards showing:
```
Version 1 (20240115_143045)        |  Version 2 (20240215_091523)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Files: 5                           |  Files: 7 (+2)
Total Rows: 15,234                 |  Total Rows: 18,456 (+3,222)
Total Size: 45.2 MB                |  Total Size: 52.1 MB (+6.9 MB)
Upload Date: Jan 15, 2024          |  Upload Date: Feb 15, 2024
```

##### Dataset-Level Comparison
Table showing what changed between versions:
```
Dataset Name     | V1 Rows  | V2 Rows  | Change    | Status
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
demographics.csv | 1,234    | 1,456    | +222      | Modified ✏️
adverse_events   | 5,432    | 6,789    | +1,357    | Modified ✏️
labs.csv        | 8,568    | 8,568    | 0         | Unchanged ✓
vitals.csv      | -        | 2,100    | +2,100    | New 🆕
medications.sas | 500      | -        | -500      | Removed ❌
```

##### Column-Level Changes (Expandable per dataset)
When user clicks on a dataset:
```
demographics.csv Column Changes:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Column Name    | V1 Type  | V2 Type  | Status
SUBJID         | string   | string   | Unchanged
AGE            | integer  | numeric  | Type Changed ⚠️
GENDER         | string   | string   | Unchanged
RACE           | string   | string   | Unchanged
COUNTRY        | -        | string   | New Column 🆕
SITE_ID        | string   | -        | Removed ❌
```

##### Impact Analysis View
Shows what will be affected by version switch:
```
⚠️ Switching to Version 2 will affect:

Widgets Using This Data:
• "Enrollment Metrics" - Uses demographics.csv (222 new rows)
• "Safety Dashboard" - Uses adverse_events (1,357 new events)
• "Lab Results Chart" - Uses labs.csv (no changes)

Data Changes Summary:
• 2 new datasets added (vitals.csv, another_file.csv)
• 1 dataset removed (medications.sas)
• 3 datasets modified with more rows
• 2 datasets have column changes

⚠️ Important Column Changes:
• demographics.csv: Added 'COUNTRY', Removed 'SITE_ID'
• adverse_events.csv: Changed type of 'SEVERITY' from string to numeric

Last Dashboard Refresh: Jan 16, 2024 10:30 AM
Recommendation: Refresh all dashboards after switching versions
```

#### Visual Diff Options
- Toggle View: Switch between "Show All" / "Show Changes Only"
- Filter by: New/Modified/Removed/Unchanged
- Search: Find specific datasets or columns
- Export: Download comparison report as PDF/CSV

#### Quick Actions from Comparison
```
[Switch to V2] [Create Test Dashboard] [Download Diff Report] [Cancel]
```

### 3. Component Implementation Details

#### VersionComparison Component
```typescript
interface VersionComparisonProps {
  studyId: string;
  version1Id: string;
  version2Id: string;
  onVersionSwitch: (versionId: string) => void;
}

export function VersionComparison({
  studyId,
  version1Id,
  version2Id,
  onVersionSwitch
}: VersionComparisonProps) {
  // Component implementation
}
```

#### VersionSwitcher Component
```typescript
interface VersionSwitcherProps {
  studyId: string;
  currentVersionId: string;
  availableVersions: DataSourceUpload[];
  onSwitch: (versionId: string) => Promise<void>;
}

export function VersionSwitcher({
  studyId,
  currentVersionId,
  availableVersions,
  onSwitch
}: VersionSwitcherProps) {
  // Component implementation
}
```

### 4. Database Schema Updates

Add comparison metadata storage:
```python
class VersionComparison(SQLModel, table=True):
    """Store version comparison results for caching"""
    __tablename__ = "version_comparisons"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    study_id: uuid.UUID = Field(foreign_key="studies.id", index=True)
    version1_id: uuid.UUID = Field(foreign_key="data_source_uploads.id")
    version2_id: uuid.UUID = Field(foreign_key="data_source_uploads.id")
    comparison_data: Dict[str, Any] = Field(sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime  # Cache expiration
```

### 5. Implementation Checklist

- [ ] Create version activation API endpoint
- [ ] Create version comparison API endpoint
- [ ] Create active version API endpoint
- [ ] Implement comparison calculation logic
- [ ] Build VersionComparison UI component
- [ ] Build VersionSwitcher UI component
- [ ] Create dataset diff view
- [ ] Implement column change detection
- [ ] Build impact analysis view
- [ ] Add version filtering and search
- [ ] Implement comparison export functionality
- [ ] Add version switch confirmation dialog
- [ ] Update DataSourceManager to show version controls
- [ ] Add version comparison caching
- [ ] Write unit tests for version management
- [ ] Write integration tests for version switching
- [ ] Update documentation

## Technical Considerations

### Performance
- Cache comparison results to avoid recalculation
- Use Parquet column metadata for quick schema comparison
- Implement pagination for large dataset comparisons

### Security
- Verify user permissions before allowing version switches
- Log all version changes for audit trail
- Validate version IDs belong to the correct study

### User Experience
- Show loading states during comparison calculation
- Provide clear warnings about impacts
- Allow preview before actual switch
- Maintain version history for rollback

## Integration Points

### With Existing System
- Update widget configurations when version changes
- Trigger dashboard refresh notifications
- Update data pipeline references
- Maintain backward compatibility

### Future Enhancements
- Automated impact analysis based on widget usage
- Version branching for testing
- Scheduled version switches
- Version approval workflows