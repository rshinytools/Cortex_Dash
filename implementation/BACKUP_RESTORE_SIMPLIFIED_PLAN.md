# Simplified Backup and Restore System Implementation Plan

## Overview
A streamlined enterprise-level backup and restore system that prioritizes simplicity and reliability while maintaining 21 CFR Part 11 compliance.

**Timeline**: 1-2 weeks  
**Priority**: High  
**Complexity**: Low-Medium  

---

## Core Principle: Keep It Simple

**Two Operations Only:**
1. **BACKUP**: Database + Files → Single ZIP file
2. **RESTORE**: ZIP file → Database + Files

---

## Implementation Phases

### **Phase 1: Core Backup Functionality (Days 1-2)**

#### Database Schema (Simple)
```sql
-- Only ONE table needed
CREATE TABLE backups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename VARCHAR(255) NOT NULL UNIQUE,
    size_mb DECIMAL(10,2),
    checksum VARCHAR(64) NOT NULL,  -- For 21 CFR Part 11
    description TEXT,
    
    -- Audit fields (21 CFR Part 11)
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_by_name VARCHAR(255),
    created_by_email VARCHAR(255),
    
    -- Simple metadata
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_backups_created ON backups(created_at DESC);
```

#### Tasks Checklist
- [ ] Create database migration for backups table
- [ ] Create `/data/backups/` directory structure
- [ ] Create `backup_service.py` with single backup function
- [ ] Implement ZIP creation with compression
- [ ] Implement SHA-256 checksum calculation
- [ ] Test backup creation with small dataset

#### Backup Service Structure
```
backend/app/services/
└── backup_service.py      # All backup logic in ONE file
```

---

### **Phase 2: Core Restore Functionality (Days 3-4)**

#### Tasks Checklist
- [ ] Implement restore function in `backup_service.py`
- [ ] Add checksum verification
- [ ] Implement automatic safety backup before restore
- [ ] Add rollback capability on failure
- [ ] Test restore with sample backup
- [ ] Verify data integrity after restore

#### Key Functions
```python
async def create_backup(user_id: str, description: str = None) -> dict
async def restore_backup(backup_id: str, user_id: str) -> dict
async def verify_checksum(backup_file: str, stored_checksum: str) -> bool
async def create_safety_backup(user_id: str) -> dict
```

---

### **Phase 3: API Endpoints (Day 5)**

#### Tasks Checklist
- [ ] Create `/backend/app/api/routes/backup.py`
- [ ] Implement 4 simple endpoints:
  - [ ] `POST /api/v1/backup` - Create backup
  - [ ] `GET /api/v1/backups` - List backups
  - [ ] `POST /api/v1/restore/{backup_id}` - Restore from backup
  - [ ] `GET /api/v1/backup/{backup_id}/download` - Download backup file
- [ ] Add SYSTEM_ADMIN permission checks
- [ ] Add audit logging for all operations
- [ ] Test endpoints with Postman/curl

---

### **Phase 4: Email Notifications (Day 6)**

#### Email Templates Checklist
- [ ] Create `email_templates.py` with 4 templates:
  - [ ] Backup Success Email
  - [ ] Backup Failed Email
  - [ ] Restore Success Email
  - [ ] Restore Failed Email
- [ ] Include all relevant details (filename, size, checksum, timestamp)
- [ ] Add actionable information for failures

#### Email Integration
- [ ] Integrate email sending in `create_backup()` function
- [ ] Integrate email sending in `restore_backup()` function
- [ ] Send to user who initiated + all system admins
- [ ] Test email delivery

#### Email Content Requirements
- Success emails: Include backup details, size, checksum
- Failure emails: Include error message, recommended actions
- All emails: Include timestamp, user who initiated, audit trail note

---

### **Phase 5: Simple Admin UI (Days 7-8)**

#### UI Structure
```
frontend/src/app/admin/backup/
└── page.tsx               # Single page for everything
```

#### UI Components Checklist
- [ ] Create backup page at `/admin/backup`
- [ ] Add "Create Backup" button (one click)
- [ ] Display backup list table with:
  - [ ] Date/Time
  - [ ] Size
  - [ ] Created By
  - [ ] Download button
  - [ ] Restore button (with double confirmation)
- [ ] Add loading states
- [ ] Add success/error toast notifications
- [ ] Add to admin navigation menu

#### UI Features
- No complex wizards - just buttons
- Big warning for restore operation
- Download capability for off-site storage
- Simple table - no fancy filters needed

---

### **Phase 6: Testing & Documentation (Days 9-10)**

#### Testing Checklist
- [ ] Create test data generator script
- [ ] Test backup creation:
  - [ ] Small database (< 100MB)
  - [ ] Large database (> 1GB)
  - [ ] Verify ZIP file integrity
  - [ ] Verify checksum
- [ ] Test restore process:
  - [ ] Create backup
  - [ ] Delete some data
  - [ ] Restore
  - [ ] Verify data recovered
- [ ] Test failure scenarios:
  - [ ] Corrupted backup file
  - [ ] Missing backup file
  - [ ] Insufficient disk space
- [ ] Test email notifications:
  - [ ] Success emails sent
  - [ ] Failure emails sent
  - [ ] Correct recipients

#### Documentation Checklist
- [ ] Create `BACKUP_RESTORE_GUIDE.md` with:
  - [ ] How to create backup
  - [ ] How to restore
  - [ ] Troubleshooting guide
  - [ ] Best practices
- [ ] Add inline code comments
- [ ] Update main README
- [ ] Create disaster recovery checklist

---

## Technical Specifications

### Backup Process Flow
```
1. User clicks "Create Backup"
2. System creates database dump (pg_dump)
3. System archives /data/ directory
4. Creates single ZIP file with both
5. Calculates SHA-256 checksum
6. Saves backup record to database
7. Sends success email
8. Returns success message
```

### Restore Process Flow
```
1. User selects backup and confirms (twice)
2. System verifies checksum
3. Creates safety backup automatically
4. Extracts ZIP file
5. Restores database (psql)
6. Restores files to /data/
7. Validates restoration
8. Sends success email
9. Forces re-login for all users
```

### File Structure
```
/data/backups/
├── backup_20240823_143022.zip    # Regular backups
├── backup_20240824_090015.zip
└── safety_backup_[uuid].zip      # Auto-created before restore
```

### ZIP File Contents
```
backup_20240823_143022.zip
├── database.sql                  # PostgreSQL dump
└── studies/                      # All study files
    ├── study_001/
    ├── study_002/
    └── ...
```

---

## Security & Compliance

### 21 CFR Part 11 Requirements
- ✅ **Audit Trail**: All backup/restore operations logged with user, timestamp
- ✅ **Data Integrity**: SHA-256 checksum for each backup
- ✅ **Access Control**: SYSTEM_ADMIN only
- ✅ **Electronic Records**: Backup records stored in database
- ✅ **Email Documentation**: Email trail for all operations

### Security Measures
- Backups stored in protected directory
- Checksum validation before restore
- Automatic safety backup before restore
- Admin-only access
- No public download URLs

---

## Simplified Code Examples

### Complete Backup Function
```python
async def create_backup(user_id: str, description: str = None):
    """Create a complete backup - that's it!"""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"backup_{timestamp}.zip"
    
    # 1. Database dump
    subprocess.run(["pg_dump", "-d", DB_NAME, "-f", "/tmp/database.sql"])
    
    # 2. Create ZIP
    with zipfile.ZipFile(f"/data/backups/{backup_name}", 'w') as z:
        z.write("/tmp/database.sql", "database.sql")
        for root, dirs, files in os.walk("/data/studies"):
            for file in files:
                z.write(os.path.join(root, file))
    
    # 3. Checksum
    checksum = hashlib.sha256(
        open(f"/data/backups/{backup_name}", 'rb').read()
    ).hexdigest()
    
    # 4. Save record
    backup = save_backup_record(backup_name, checksum, user_id)
    
    # 5. Send email
    send_backup_success_email(user_id, backup)
    
    return backup
```

### Complete Restore Function
```python
async def restore_backup(backup_id: str, user_id: str):
    """Restore from backup - with safety!"""
    
    backup = get_backup(backup_id)
    
    # 1. Verify checksum
    if not verify_checksum(backup.filename, backup.checksum):
        raise Exception("Backup corrupted!")
    
    # 2. Safety backup first!
    create_backup(user_id, "Safety backup before restore")
    
    # 3. Extract and restore
    with zipfile.ZipFile(f"/data/backups/{backup.filename}", 'r') as z:
        z.extractall("/tmp/restore")
    
    subprocess.run(["psql", "-d", DB_NAME, "-f", "/tmp/restore/database.sql"])
    shutil.copytree("/tmp/restore/studies", "/data/studies")
    
    # 4. Send email
    send_restore_success_email(user_id, backup)
    
    return {"success": True}
```

---

## Why This Approach Works

1. **Simple = Reliable**: Less code means fewer bugs
2. **Fast Implementation**: Can be done in 1-2 weeks
3. **Easy to Test**: Just backup and restore
4. **Easy to Maintain**: Any developer can understand it
5. **Fully Compliant**: Meets all 21 CFR Part 11 requirements
6. **User Friendly**: One button to backup, one button to restore

---

## Success Criteria

- [ ] Can create complete backup in < 5 minutes for 1GB database
- [ ] Can restore from backup successfully
- [ ] Checksum validation works
- [ ] Email notifications sent
- [ ] Audit trail complete
- [ ] System admin can download backups
- [ ] Safety backup created before restore
- [ ] All tests passing

---

## Future Enhancements (Not Now)

These can be added later if needed:
- Scheduled automatic backups
- Cloud storage (S3/Azure)
- Incremental backups
- Encryption at rest
- Retention policies
- Backup size predictions

But start with this simple version that **works today**.

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Backup fails | Email notification, manual retry |
| Restore fails | Automatic safety backup, rollback |
| Corruption | SHA-256 checksum validation |
| Data loss | Download capability for off-site storage |
| No notification | Emails to multiple admins |

---

## Dependencies

```python
# Backend
import subprocess  # For pg_dump/psql
import zipfile     # For compression
import hashlib     # For checksums
import shutil      # For file operations

# No additional libraries needed!
```

---

## Implementation Checklist Summary

### Week 1
- [ ] Day 1-2: Basic backup function
- [ ] Day 3-4: Restore function with safety
- [ ] Day 5: API endpoints
- [ ] Day 6: Email notifications

### Week 2  
- [ ] Day 7-8: Simple UI
- [ ] Day 9: Testing
- [ ] Day 10: Documentation & buffer

---

## Sign-off

- [ ] Development Complete
- [ ] Testing Complete
- [ ] Documentation Complete
- [ ] Admin Training Complete
- [ ] Ready for Production

---

**Document Version**: 2.0 (Simplified)  
**Created Date**: 2024-08-23  
**Last Updated**: 2024-08-23  
**Author**: Claude (AI Assistant)  
**Status**: READY FOR IMPLEMENTATION

---

## Quick Start Commands

```bash
# Create backup (API)
curl -X POST http://localhost:8000/api/v1/backup \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"description": "Daily backup"}'

# List backups
curl http://localhost:8000/api/v1/backups \
  -H "Authorization: Bearer $TOKEN"

# Restore (BE CAREFUL!)
curl -X POST http://localhost:8000/api/v1/restore/{backup_id} \
  -H "Authorization: Bearer $TOKEN"

# Download backup
curl http://localhost:8000/api/v1/backup/{backup_id}/download \
  -H "Authorization: Bearer $TOKEN" \
  -o backup.zip
```