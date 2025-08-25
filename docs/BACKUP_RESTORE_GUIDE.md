# Backup and Restore System Guide

## Overview

The Clinical Dashboard Platform includes a comprehensive backup and restore system that ensures data protection and business continuity. This system is designed to meet 21 CFR Part 11 compliance requirements for electronic records.

## Features

- **Full System Backups**: Complete database and file system backups
- **Selective Backups**: Option to backup only database or files
- **Compression**: Automatic GZIP compression to reduce storage requirements
- **Integrity Verification**: SHA-256 checksums for all backups
- **Safety Backups**: Automatic safety backup before restore operations
- **Email Notifications**: Automated email alerts for backup/restore operations
- **Audit Trail**: Complete logging of all backup operations for compliance

## API Endpoints

### Create Backup

```bash
POST /api/v1/backup
```

**Request Body:**
```json
{
  "description": "Daily backup",
  "backup_type": "full"  // Options: "full", "database", "files"
}
```

**Response:**
```json
{
  "success": true,
  "backup_id": "uuid",
  "filename": "backup_20240825_143022.zip",
  "size_mb": 125.5,
  "checksum": "sha256-hash",
  "created_at": "2024-08-25T14:30:22Z"
}
```

### List Backups

```bash
GET /api/v1/backups?limit=50
```

**Response:**
```json
[
  {
    "id": "uuid",
    "filename": "backup_20240825_143022.zip",
    "size_mb": 125.5,
    "checksum": "sha256-hash",
    "description": "Daily backup",
    "created_by": "user-uuid",
    "created_by_name": "John Doe",
    "created_by_email": "john@example.com",
    "created_at": "2024-08-25T14:30:22Z",
    "metadata": {...}
  }
]
```

### Restore from Backup

```bash
POST /api/v1/restore/{backup_id}
```

**Request Body:**
```json
{
  "create_safety_backup": true  // Recommended: always true
}
```

**Response:**
```json
{
  "success": true,
  "backup_id": "uuid",
  "backup_filename": "backup_20240825_143022.zip",
  "safety_backup_id": "safety-backup-uuid",
  "restored_at": "2024-08-25T15:30:22Z"
}
```

### Download Backup

```bash
GET /api/v1/backup/{backup_id}/download
```

Downloads the backup ZIP file directly.

### Verify Backup Integrity

```bash
POST /api/v1/backup/{backup_id}/verify
```

**Response:**
```json
{
  "backup_id": "uuid",
  "valid": true,
  "message": "Backup integrity verified"
}
```

## Backup File Structure

Each backup is a ZIP file containing:

```
backup_20240825_143022.zip
├── database.sql          # PostgreSQL dump
├── studies/              # All study files
│   ├── study_001/
│   ├── study_002/
│   └── ...
└── metadata.json         # Backup metadata
```

## Email Notifications

The system sends email notifications for:

1. **Backup Success**: Confirmation with backup details
2. **Backup Failure**: Alert with error details and recommended actions
3. **Restore Success**: Confirmation with post-restore checklist
4. **Restore Failure**: Critical alert with recovery options

Emails are sent to:
- The user who initiated the operation
- All system administrators

## Security & Compliance

### 21 CFR Part 11 Compliance

- **Audit Trail**: All backup/restore operations are logged with user, timestamp, and details
- **Data Integrity**: SHA-256 checksums ensure backup file integrity
- **Access Control**: Only SYSTEM_ADMIN users can perform backup/restore operations
- **Electronic Records**: Backup metadata stored in database with full audit trail

### Security Features

- Backups stored in protected `/data/backups/` directory
- Checksum validation before any restore operation
- Automatic safety backup before restore
- No public URLs for backup downloads
- All operations require authentication

## Best Practices

### Backup Schedule

- **Daily**: Incremental or full backup of critical data
- **Weekly**: Full system backup
- **Monthly**: Archive backup for long-term storage
- **Before Major Changes**: Always create backup before system updates

### Storage Management

- Monitor backup storage usage regularly
- Implement retention policy (recommended: 7 years for compliance)
- Consider off-site storage for disaster recovery
- Regularly verify backup integrity

### Testing

- Perform regular restore tests in test environment
- Document restore procedures
- Train administrators on backup/restore operations
- Conduct disaster recovery drills quarterly

## Troubleshooting

### Common Issues

#### Backup Fails

**Symptoms**: Backup operation returns error
**Possible Causes**:
- Insufficient disk space
- Database connection issues
- Permission problems

**Solutions**:
1. Check available disk space: `df -h /data/backups`
2. Verify database connectivity
3. Check directory permissions: `ls -la /data/backups`
4. Review error logs for specific issues

#### Restore Fails

**Symptoms**: Restore operation fails or system is in inconsistent state
**Possible Causes**:
- Corrupted backup file
- Database conflicts
- Insufficient permissions

**Solutions**:
1. Verify backup integrity using the verify endpoint
2. Restore from safety backup if available
3. Try alternative backup file
4. Contact system administrator

#### Email Notifications Not Received

**Symptoms**: No email notifications for backup operations
**Possible Causes**:
- SMTP configuration issues
- Email server problems
- Spam filters

**Solutions**:
1. Verify SMTP settings in environment configuration
2. Check email server logs
3. Verify recipient email addresses
4. Check spam/junk folders

## Disaster Recovery

### Recovery Time Objectives

- **RTO (Recovery Time Objective)**: 4 hours
- **RPO (Recovery Point Objective)**: 24 hours

### Recovery Procedure

1. **Assess Situation**: Determine extent of data loss
2. **Identify Backup**: Select most recent valid backup
3. **Create Safety Backup**: If possible, backup current state
4. **Perform Restore**: Execute restore operation
5. **Verify Data**: Check data integrity and completeness
6. **Test System**: Verify all critical functions
7. **Notify Users**: Inform users of restoration
8. **Document Incident**: Record all actions for compliance

## Configuration

### Environment Variables

```bash
# Backup Configuration
BACKUP_DIR=/data/backups
BACKUP_RETENTION_DAYS=2555  # 7 years
BACKUP_COMPRESSION_LEVEL=6  # 1-9, higher = better compression

# Email Configuration
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=notifications@example.com
SMTP_PASSWORD=secure_password
SMTP_TLS=true
EMAILS_FROM_EMAIL=noreply@example.com
EMAILS_FROM_NAME="Clinical Dashboard"
```

### Directory Structure

```
/data/
├── backups/                    # Backup storage
│   ├── backup_*.zip           # Regular backups
│   └── safety_backup_*.zip    # Safety backups
└── studies/                    # Study data files
```

## API Authentication

All backup API endpoints require authentication with a valid JWT token:

```bash
curl -X POST http://localhost:8000/api/v1/backup \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"description": "Manual backup", "backup_type": "full"}'
```

## Monitoring

### Health Checks

- Monitor backup directory space usage
- Check backup operation success rate
- Verify email notification delivery
- Track backup/restore duration trends

### Alerts

Set up alerts for:
- Backup failures
- Low disk space (< 20% free)
- Backup not created in 48 hours
- Restore operations (always notify)

## Support

For assistance with backup and restore operations:

1. Check this documentation
2. Review system logs
3. Contact system administrator
4. For critical issues, follow escalation procedures

---

**Document Version**: 1.0
**Last Updated**: August 25, 2025
**Status**: Production Ready