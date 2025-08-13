#!/bin/bash
# ABOUTME: Database backup script for Clinical Dashboard Platform
# ABOUTME: Creates encrypted backups with rotation and optional S3 upload

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="/opt/clinical-dashboard/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="clinical_dashboard_backup_${TIMESTAMP}"

# Load environment variables
if [ -f "$PROJECT_ROOT/.env" ]; then
    export $(cat "$PROJECT_ROOT/.env" | grep -v '^#' | xargs)
fi

# Function to log messages
log() {
    echo -e "${2:-}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

# Function to check command success
check_success() {
    if [ $? -eq 0 ]; then
        log "✓ $1" "$GREEN"
        return 0
    else
        log "✗ $1 failed" "$RED"
        return 1
    fi
}

# Function to get container ID
get_container_id() {
    local service=$1
    docker compose -f "$PROJECT_ROOT/docker-compose.prod.yml" ps -q $service 2>/dev/null | head -1
}

# Function to cleanup old backups
cleanup_old_backups() {
    local retention_days=${BACKUP_RETENTION_DAYS:-30}
    log "Cleaning up backups older than $retention_days days..."
    
    find "$BACKUP_DIR" -name "clinical_dashboard_backup_*.tar.gz.enc" -type f -mtime +$retention_days -delete
    check_success "Old backups cleaned up"
}

# Function to upload to S3
upload_to_s3() {
    local file=$1
    
    if [ -z "${AWS_ACCESS_KEY_ID:-}" ] || [ -z "${S3_BUCKET_NAME:-}" ]; then
        log "S3 configuration not found, skipping upload" "$YELLOW"
        return 0
    fi
    
    log "Uploading backup to S3..."
    docker run --rm \
        -e AWS_ACCESS_KEY_ID="$AWS_ACCESS_KEY_ID" \
        -e AWS_SECRET_ACCESS_KEY="$AWS_SECRET_ACCESS_KEY" \
        -e AWS_DEFAULT_REGION="${AWS_DEFAULT_REGION:-us-east-1}" \
        -v "$file:/backup.tar.gz.enc" \
        amazon/aws-cli:latest \
        s3 cp /backup.tar.gz.enc "s3://$S3_BUCKET_NAME/backups/$(basename $file)"
    
    check_success "Backup uploaded to S3"
}

# Start backup process
log "Starting backup process..." "$GREEN"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Create temporary directory
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

# Step 1: Check if services are running
DB_CONTAINER=$(get_container_id db)
if [ -z "$DB_CONTAINER" ]; then
    log "Database container not found. Is the application running?" "$RED"
    exit 1
fi

# Step 2: Backup PostgreSQL database
log "Backing up PostgreSQL database..."
docker exec "$DB_CONTAINER" pg_dump \
    -U "$POSTGRES_USER" \
    -d "$POSTGRES_DB" \
    --no-owner \
    --no-acl \
    --clean \
    --if-exists \
    > "$TEMP_DIR/database.sql"

check_success "Database dumped"

# Get database size for logging
DB_SIZE=$(du -h "$TEMP_DIR/database.sql" | cut -f1)
log "Database dump size: $DB_SIZE"

# Step 3: Backup application data
log "Backing up application data..."

# Copy study data
if [ -d "$PROJECT_ROOT/data" ]; then
    cp -r "$PROJECT_ROOT/data" "$TEMP_DIR/"
    check_success "Study data copied"
fi

# Export widget definitions and templates
log "Exporting widget configurations..."
docker exec "$DB_CONTAINER" psql \
    -U "$POSTGRES_USER" \
    -d "$POSTGRES_DB" \
    -c "COPY (SELECT * FROM widget_definitions) TO STDOUT WITH CSV HEADER" \
    > "$TEMP_DIR/widget_definitions.csv"

docker exec "$DB_CONTAINER" psql \
    -U "$POSTGRES_USER" \
    -d "$POSTGRES_DB" \
    -c "COPY (SELECT * FROM dashboard_templates) TO STDOUT WITH CSV HEADER" \
    > "$TEMP_DIR/dashboard_templates.csv"

check_success "Widget configurations exported"

# Step 4: Create backup metadata
cat > "$TEMP_DIR/backup_metadata.json" <<EOF
{
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "version": "$(git -C "$PROJECT_ROOT" describe --tags --always 2>/dev/null || echo 'unknown')",
    "commit": "$(git -C "$PROJECT_ROOT" rev-parse HEAD 2>/dev/null || echo 'unknown')",
    "database_size": "$DB_SIZE",
    "postgres_version": "$(docker exec "$DB_CONTAINER" psql --version | head -1)",
    "backup_name": "$BACKUP_NAME"
}
EOF

# Step 5: Create compressed archive
log "Creating compressed archive..."
cd "$TEMP_DIR"
tar -czf "$BACKUP_DIR/${BACKUP_NAME}.tar.gz" .
check_success "Archive created"

ARCHIVE_SIZE=$(du -h "$BACKUP_DIR/${BACKUP_NAME}.tar.gz" | cut -f1)
log "Archive size: $ARCHIVE_SIZE"

# Step 6: Encrypt backup
log "Encrypting backup..."
if [ -n "${BACKUP_ENCRYPTION_KEY:-}" ]; then
    openssl enc -aes-256-cbc \
        -salt \
        -in "$BACKUP_DIR/${BACKUP_NAME}.tar.gz" \
        -out "$BACKUP_DIR/${BACKUP_NAME}.tar.gz.enc" \
        -pass pass:"$BACKUP_ENCRYPTION_KEY"
    
    # Remove unencrypted archive
    rm "$BACKUP_DIR/${BACKUP_NAME}.tar.gz"
    check_success "Backup encrypted"
    FINAL_BACKUP="$BACKUP_DIR/${BACKUP_NAME}.tar.gz.enc"
else
    log "No encryption key found, using unencrypted backup" "$YELLOW"
    FINAL_BACKUP="$BACKUP_DIR/${BACKUP_NAME}.tar.gz"
fi

# Step 7: Verify backup
log "Verifying backup..."
if [ -f "$FINAL_BACKUP" ] && [ -s "$FINAL_BACKUP" ]; then
    check_success "Backup file exists and is not empty"
else
    log "Backup verification failed" "$RED"
    exit 1
fi

# Step 8: Upload to S3 (if configured)
upload_to_s3 "$FINAL_BACKUP"

# Step 9: Cleanup old backups
cleanup_old_backups

# Step 10: Create backup report
REPORT_FILE="$BACKUP_DIR/backup_report_${TIMESTAMP}.txt"
cat > "$REPORT_FILE" <<EOF
Clinical Dashboard Platform Backup Report
========================================
Timestamp: $(date)
Backup Name: $BACKUP_NAME
Database Size: $DB_SIZE
Archive Size: $ARCHIVE_SIZE
Location: $FINAL_BACKUP
S3 Upload: $([ -n "${S3_BUCKET_NAME:-}" ] && echo "Yes" || echo "No")

Backup Contents:
- PostgreSQL database dump
- Application data files
- Widget definitions
- Dashboard templates
- Backup metadata

Retention Policy: ${BACKUP_RETENTION_DAYS:-30} days

To restore this backup, use:
./scripts/restore.sh $BACKUP_NAME
EOF

# Final summary
log "=========================================" "$GREEN"
log "Backup completed successfully!" "$GREEN"
log "=========================================" "$GREEN"
log "Backup Name: $BACKUP_NAME"
log "Location: $FINAL_BACKUP"
log "Report: $REPORT_FILE"
log ""

# Send notification if configured
if [ -n "${SLACK_WEBHOOK_URL:-}" ]; then
    curl -X POST -H 'Content-type: application/json' \
        --data "{\"text\":\"✅ Backup completed successfully\nName: $BACKUP_NAME\nSize: $ARCHIVE_SIZE\"}" \
        "$SLACK_WEBHOOK_URL" 2>/dev/null || true
fi

exit 0