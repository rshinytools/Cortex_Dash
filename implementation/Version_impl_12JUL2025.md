# Dashboard Template Versioning System Implementation
**Date**: January 12, 2025  
**Status**: In Progress  
**Developer**: Sagarmatha AI

## Overview

This document details the implementation of an automatic and robust versioning system for dashboard templates in the Clinical Dashboard Platform. The system provides automatic version detection, smart conflict resolution, and zero-friction user experience.

## Architecture

### 1. Database Schema

#### New Tables
```sql
-- Template drafts for real-time change tracking
CREATE TABLE template_drafts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    template_id UUID NOT NULL REFERENCES dashboard_templates(id),
    base_version_id UUID REFERENCES template_versions(id),
    draft_content JSONB NOT NULL,
    changes_summary JSONB DEFAULT '[]',
    auto_save_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    conflict_status VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE
);

-- Version change log for automatic detection
CREATE TABLE template_change_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    template_id UUID NOT NULL REFERENCES dashboard_templates(id),
    draft_id UUID REFERENCES template_drafts(id),
    change_type VARCHAR(50) NOT NULL, -- 'major', 'minor', 'patch'
    change_category VARCHAR(100) NOT NULL,
    change_description TEXT,
    change_data JSONB,
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_template_drafts_template_id ON template_drafts(template_id);
CREATE INDEX idx_template_drafts_created_by ON template_drafts(created_by);
CREATE INDEX idx_template_change_logs_template_id ON template_change_logs(template_id);
CREATE INDEX idx_template_change_logs_created_at ON template_change_logs(created_at);
```

#### Modified Tables
```sql
-- Add fields to template_versions table
ALTER TABLE template_versions ADD COLUMN IF NOT EXISTS version_type VARCHAR(10) CHECK (version_type IN ('major', 'minor', 'patch'));
ALTER TABLE template_versions ADD COLUMN IF NOT EXISTS auto_created BOOLEAN DEFAULT FALSE;
ALTER TABLE template_versions ADD COLUMN IF NOT EXISTS change_summary JSONB DEFAULT '[]';
ALTER TABLE template_versions ADD COLUMN IF NOT EXISTS created_by_name VARCHAR(255);
ALTER TABLE template_versions ADD COLUMN IF NOT EXISTS comparison_hash VARCHAR(64);
```

### 2. Backend Services

#### A. Change Detection Service
- **Location**: `/backend/app/services/template_change_detector.py`
- **Purpose**: Automatically detect and categorize changes
- **Key Methods**:
  - `detect_changes()`: Compare template states
  - `categorize_change()`: Determine change severity
  - `generate_change_summary()`: Create human-readable summary

#### B. Auto Versioning Service  
- **Location**: `/backend/app/services/template_auto_version.py`
- **Purpose**: Background service for automatic version creation
- **Key Methods**:
  - `should_create_version()`: Check versioning rules
  - `create_automatic_version()`: Create version with metadata
  - `cleanup_old_versions()`: Manage version storage

#### C. Draft Management Service
- **Location**: `/backend/app/services/template_draft_service.py`
- **Purpose**: Handle draft creation and updates
- **Key Methods**:
  - `create_or_update_draft()`: Manage draft state
  - `track_change()`: Log changes in real-time
  - `merge_drafts()`: Handle concurrent edits

### 3. API Endpoints

#### New Endpoints
```python
# Draft management
POST   /api/v1/dashboard-templates/{id}/draft         # Create/update draft
GET    /api/v1/dashboard-templates/{id}/draft         # Get current draft
DELETE /api/v1/dashboard-templates/{id}/draft         # Discard draft

# Version management  
POST   /api/v1/dashboard-templates/{id}/versions      # Create version (manual)
GET    /api/v1/dashboard-templates/{id}/versions      # List versions
GET    /api/v1/dashboard-templates/{id}/versions/{versionId}  # Get version
POST   /api/v1/dashboard-templates/{id}/versions/{versionId}/restore  # Restore
GET    /api/v1/dashboard-templates/{id}/versions/compare  # Compare versions
GET    /api/v1/dashboard-templates/{id}/version-status    # Current version info

# Change tracking
GET    /api/v1/dashboard-templates/{id}/changes       # Recent changes
POST   /api/v1/dashboard-templates/{id}/changes/ack   # Acknowledge changes
```

### 4. Frontend Components

#### A. Version Status Indicator
- **Location**: `/frontend/src/components/admin/version-status-indicator/index.tsx`
- **Shows**: Current version, draft changes, auto-save status

#### B. Version History Panel
- **Location**: `/frontend/src/components/admin/version-history-panel/index.tsx`
- **Features**: Timeline view, filters, restore actions

#### C. Version Comparison View
- **Location**: `/frontend/src/components/admin/version-comparison/index.tsx`
- **Features**: Side-by-side diff, change highlighting

#### D. Auto-save Manager
- **Location**: `/frontend/src/hooks/useAutoSave.ts`
- **Handles**: Periodic saves, conflict detection, version triggers

### 5. Implementation Phases

#### Phase 1: Core Infrastructure (Current)
- [x] Database schema updates
- [x] Basic draft management
- [x] Change detection service
- [ ] Auto-save functionality
- [ ] Version creation API

#### Phase 2: Automatic Versioning
- [ ] Background versioning service
- [ ] Time-based triggers
- [ ] Change-based triggers
- [ ] Event-based triggers
- [ ] Version cleanup service

#### Phase 3: UI Integration
- [ ] Version status indicator
- [ ] Version history panel
- [ ] Comparison view
- [ ] Auto-save notifications
- [ ] Conflict resolution UI

#### Phase 4: Advanced Features
- [ ] Selective rollback
- [ ] Branch management
- [ ] Version tagging
- [ ] Export/import versions
- [ ] Git integration

## Implementation Progress

### Completed ✅
1. Database schema design
2. Implementation plan
3. Service architecture
4. Database migration file (`003_add_template_versioning_system.py`)
5. SQLModel models for drafts and change logs
6. Change detection service (`template_change_detector.py`)
7. Draft management service (`template_draft_service.py`)
8. Auto-versioning service (`template_auto_version.py`)
9. All API endpoints for version management:
   - Draft management (create, update, discard)
   - Version listing and retrieval
   - Version creation and restoration
   - Version comparison
   - Version status and change tracking

### In Progress 🔄
1. Frontend components for version UI
2. Integration with existing template editor

### Next Steps 📋
1. Create frontend components:
   - Version status indicator
   - Version history panel
   - Version comparison view
   - Auto-save hook
2. Integrate with unified dashboard designer
3. Add comprehensive tests
4. Run database migrations
5. Test end-to-end functionality

## Configuration

### Auto-versioning Rules
```python
DEFAULT_VERSIONING_CONFIG = {
    "enabled": True,
    "strategy": "balanced",  # aggressive, balanced, conservative
    
    "time_triggers": {
        "draft_age_hours": 24,
        "idle_time_hours": 2,
        "max_draft_age_hours": 72
    },
    
    "change_triggers": {
        "major_changes": 1,
        "minor_changes": 10,
        "patch_changes": 25
    },
    
    "event_triggers": {
        "before_publish": True,
        "user_switch": True,
        "before_deployment": True
    },
    
    "storage": {
        "keep_all_major": True,
        "keep_minor_count": 10,
        "keep_patch_count": 5,
        "archive_after_days": 180,
        "compress_after_days": 90
    }
}
```

## Testing Strategy

### Unit Tests
- Change detection accuracy
- Version creation logic
- Conflict detection
- Storage optimization

### Integration Tests
- API endpoint functionality
- Database operations
- Background service reliability
- Frontend component integration

### Performance Tests
- Large template handling
- Version comparison speed
- Storage efficiency
- Query optimization

## Monitoring

### Metrics to Track
- Version creation frequency
- Storage usage
- Conflict occurrence rate
- Auto-save performance
- User adoption rate

### Alerts
- Failed version creation
- Storage threshold exceeded
- Conflict resolution timeout
- Service health issues

## Security Considerations

1. **Access Control**: Version operations respect template permissions
2. **Audit Trail**: All version operations are logged
3. **Data Integrity**: Checksums verify version consistency
4. **Backup**: Automatic backups before major operations

## User Documentation

### For End Users
- How automatic versioning works
- Understanding version numbers
- Reviewing version history
- Restoring previous versions

### For Administrators
- Configuring versioning rules
- Managing storage policies
- Monitoring version system
- Troubleshooting guide

## API Documentation

See `/docs/api/versioning.md` for detailed API documentation.

## Notes

- All timestamps are stored in UTC
- Version numbers follow semantic versioning (major.minor.patch)
- Drafts are automatically cleaned up after 7 days of inactivity
- Compressed versions use zlib compression
- Change detection uses deep object comparison with normalization

---

Last Updated: January 12, 2025