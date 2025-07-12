# Backup and Recovery Strategy

## Overview

This document outlines the backup and recovery procedures for the Clinical Dashboard Platform.

## Backup Components

### 1. Database (PostgreSQL)
- **What**: All application data including users, studies, configurations, widget definitions
- **Where**: Stored in `postgres_data` Docker volume
- **Backup Location**: `./backups/db/`
- **Format**: SQL dump files

### 2. Uploaded Files
- **What**: Study data files, transformation scripts, generated reports
- **Where**: Stored in `app_data` Docker volume
- **Backup Location**: `./backups/files/`
- **Format**: Compressed tar.gz archives

### 3. Application Code
- **What**: Source code and configurations
- **Where**: Git repository
- **Backup**: Use Git tags for version control

## Backup Commands

### Manual Backups

```bash
# Complete backup (recommended before major updates)
make backup-all

# Database only
make backup-db

# Files only
make backup-files
```

### Automated Backups

```bash
# Set up daily automated backups at 2 AM
make schedule-backup

# Or custom schedule (edit crontab)
crontab -e
# Add: 0 */6 * * * cd /path/to/project && make backup-all
```

## Backup Schedule Recommendations

### Production Environment

| Backup Type | Frequency | Retention | Notes |
|------------|-----------|-----------|-------|
| Database | Daily | 30 days | Critical data |
| Files | Daily | 30 days | Study data |
| Full System | Weekly | 90 days | Complete snapshot |
| Pre-deployment | Before each update | 7 days | Safety net |

### Development Environment

| Backup Type | Frequency | Retention | Notes |
|------------|-----------|-----------|-------|
| Database | Weekly | 7 days | Development data |
| Files | On-demand | 7 days | Test files |

## Recovery Procedures

### 1. Database Recovery

```bash
# List available backups
ls -la backups/db/

# Restore specific backup
make restore-db FILE=backups/db/backup_20240115_020000.sql

# Or restore latest
make restore-db FILE=$(ls -t backups/db/*.sql | head -1)
```

### 2. File Recovery

```bash
# List available backups
ls -la backups/files/

# Restore specific backup
make restore-files FILE=files_backup_20240115_020000.tar.gz
```

### 3. Point-in-Time Recovery

For critical production systems, consider:

1. **Enable PostgreSQL WAL archiving**:
```sql
-- In postgresql.conf
archive_mode = on
archive_command = 'cp %p /backup/wal/%f'
```

2. **Use pg_basebackup for consistent backups**:
```bash
docker exec $(docker ps -qf "name=db") pg_basebackup -D /backup/base -Ft -z -P
```

## Disaster Recovery Plan

### Scenario 1: Database Corruption

1. Stop the application:
   ```bash
   make emergency-stop
   ```

2. Restore from latest backup:
   ```bash
   make restore-db FILE=backups/db/latest_good_backup.sql
   ```

3. Restart services:
   ```bash
   make up-prod
   ```

4. Verify data integrity:
   ```bash
   make health-check
   ```

### Scenario 2: Complete System Failure

1. Provision new server

2. Clone repository:
   ```bash
   git clone [repository-url]
   cd clinical-dashboard
   ```

3. Restore environment:
   ```bash
   cp .env.backup .env
   ```

4. Start fresh system:
   ```bash
   make up-prod
   ```

5. Restore data:
   ```bash
   make restore-db FILE=latest_backup.sql
   make restore-files FILE=latest_files.tar.gz
   ```

## Backup Validation

### Regular Testing (Monthly)

```bash
# 1. Create test backup
make backup-all

# 2. Spin up test environment
docker-compose -f docker-compose.test.yml up -d

# 3. Restore to test environment
POSTGRES_HOST=localhost:5433 make restore-db FILE=latest_backup.sql

# 4. Verify data
docker exec test-backend python scripts/verify_backup.py

# 5. Clean up
docker-compose -f docker-compose.test.yml down
```

## Storage Recommendations

### Local Storage
- Keep latest 30 days on server
- Use RAID configuration for redundancy
- Monitor disk space usage

### Remote Storage
- **AWS S3**:
  ```bash
  aws s3 sync backups/ s3://your-bucket/backups/ --delete
  ```

- **Google Cloud Storage**:
  ```bash
  gsutil -m rsync -r -d backups/ gs://your-bucket/backups/
  ```

- **Network Attached Storage (NAS)**:
  ```bash
  rsync -avz backups/ /mnt/nas/clinical-dashboard-backups/
  ```

## Monitoring and Alerts

### Backup Monitoring Script

```bash
#!/bin/bash
# Check if backup is older than 24 hours
LATEST_BACKUP=$(ls -t backups/db/*.sql | head -1)
if [ -z "$LATEST_BACKUP" ] || [ $(find "$LATEST_BACKUP" -mtime +1) ]; then
    echo "WARNING: No recent backup found!" | mail -s "Backup Alert" admin@example.com
fi
```

### Disk Space Monitoring

```bash
# Add to crontab
0 * * * * df -h | grep -E "backups|docker" | awk '$5 > 80 {print "Disk space warning: " $0}' | mail -s "Disk Space Alert" admin@example.com
```

## Best Practices

1. **3-2-1 Rule**: Keep 3 copies of data, on 2 different media, with 1 offsite
2. **Test Restores**: Regularly test backup restoration (monthly)
3. **Document Everything**: Keep backup/restore logs
4. **Encrypt Sensitive Data**: Use GPG for encryption:
   ```bash
   # Encrypt backup
   gpg -c backups/db/backup.sql
   
   # Decrypt backup
   gpg -d backups/db/backup.sql.gpg > backup.sql
   ```
5. **Version Control**: Tag deployments in Git:
   ```bash
   git tag -a v1.2.3 -m "Production deployment"
   git push origin v1.2.3
   ```

## Emergency Contacts

- **System Administrator**: [Name] - [Phone] - [Email]
- **Database Administrator**: [Name] - [Phone] - [Email]
- **DevOps Lead**: [Name] - [Phone] - [Email]
- **AWS/Cloud Support**: [Support Number]

## Recovery Time Objectives (RTO)

| Component | Target RTO | Actual RTO | Notes |
|-----------|------------|------------|-------|
| Database | 30 minutes | ~20 minutes | Depends on size |
| Files | 1 hour | ~45 minutes | Depends on volume |
| Full System | 2 hours | ~1.5 hours | Complete recovery |

## Backup Checklist

### Daily
- [ ] Verify automated backups completed
- [ ] Check backup sizes are reasonable
- [ ] Monitor disk space

### Weekly
- [ ] Test restore to dev environment
- [ ] Sync backups to remote storage
- [ ] Review backup logs

### Monthly
- [ ] Full disaster recovery drill
- [ ] Clean up old backups
- [ ] Update documentation
- [ ] Review and optimize backup strategy