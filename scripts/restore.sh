#!/bin/bash
# ABOUTME: Database restore script for Clinical Dashboard Platform
# ABOUTME: Restores encrypted backups with verification and safety checks

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="/opt/clinical-dashboard/backups"

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

# Check arguments
if [ $# -eq 0 ]; then
    log "Usage: $0 <backup_name> [--force]" "$RED"
    log "Example: $0 clinical_dashboard_backup_20240107_120000" "$RED"
    log ""
    log "Available backups:" "$YELLOW"
    ls -1 "$BACKUP_DIR" | grep -E "clinical_dashboard_backup_.*\.(tar\.gz|tar\.gz\.enc)$" | sed 's/\.tar\.gz.*$//'
    exit 1
fi

BACKUP_NAME=$1
FORCE_RESTORE=${2:-}

# Find backup file
if [ -f "$BACKUP_DIR/${BACKUP_NAME}.tar.gz.enc" ]; then
    BACKUP_FILE="$BACKUP_DIR/${BACKUP_NAME}.tar.gz.enc"
    ENCRYPTED=true
elif [ -f "$BACKUP_DIR/${BACKUP_NAME}.tar.gz" ]; then
    BACKUP_FILE="$BACKUP_DIR/${BACKUP_NAME}.tar.gz"
    ENCRYPTED=false
else
    log "Backup file not found: $BACKUP_NAME" "$RED"
    exit 1
fi

log "Restore Process Starting" "$GREEN"
log "========================" "$GREEN"
log "Backup: $BACKUP_NAME"
log "File: $BACKUP_FILE"
log "Encrypted: $ENCRYPTED"

# Safety check
if [ "$FORCE_RESTORE" != "--force" ]; then
    log "" "$YELLOW"
    log "⚠️  WARNING: This will replace all current data!" "$YELLOW"
    log "⚠️  Make sure you have a recent backup of current data!" "$YELLOW"
    log "" "$YELLOW"
    read -p "$(echo -e ${BLUE}Type \'RESTORE\' to continue: ${NC})" confirmation
    
    if [ "$confirmation" != "RESTORE" ]; then
        log "Restore cancelled" "$RED"
        exit 1
    fi
fi

# Create temporary directory
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

# Step 1: Create safety backup
log "Creating safety backup of current data..."
"$SCRIPT_DIR/backup.sh"
check_success "Safety backup created"

# Step 2: Stop application services
log "Stopping application services..."
docker compose -f "$PROJECT_ROOT/docker-compose.prod.yml" stop backend frontend celery_worker celery_beat
check_success "Application services stopped"

# Step 3: Decrypt backup if needed
if [ "$ENCRYPTED" = true ]; then
    log "Decrypting backup..."
    if [ -z "${BACKUP_ENCRYPTION_KEY:-}" ]; then
        log "Encryption key not found in environment" "$RED"
        read -s -p "$(echo -e ${BLUE}Enter backup encryption key: ${NC})" BACKUP_ENCRYPTION_KEY
        echo
    fi
    
    openssl enc -aes-256-cbc -d \
        -in "$BACKUP_FILE" \
        -out "$TEMP_DIR/backup.tar.gz" \
        -pass pass:"$BACKUP_ENCRYPTION_KEY"
    
    check_success "Backup decrypted"
    ARCHIVE_FILE="$TEMP_DIR/backup.tar.gz"
else
    ARCHIVE_FILE="$BACKUP_FILE"
fi

# Step 4: Extract backup
log "Extracting backup archive..."
cd "$TEMP_DIR"
tar -xzf "$ARCHIVE_FILE"
check_success "Archive extracted"

# Verify backup contents
if [ ! -f "$TEMP_DIR/database.sql" ]; then
    log "Invalid backup: database.sql not found" "$RED"
    exit 1
fi

# Show backup metadata
if [ -f "$TEMP_DIR/backup_metadata.json" ]; then
    log "Backup metadata:" "$BLUE"
    cat "$TEMP_DIR/backup_metadata.json" | python -m json.tool
fi

# Step 5: Restore database
log "Restoring PostgreSQL database..."
DB_CONTAINER=$(get_container_id db)

# Drop existing connections
docker exec "$DB_CONTAINER" psql -U "$POSTGRES_USER" -d postgres -c \
    "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='$POSTGRES_DB' AND pid <> pg_backend_pid();"

# Restore database
docker exec -i "$DB_CONTAINER" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" < "$TEMP_DIR/database.sql"
check_success "Database restored"

# Step 6: Restore application data
if [ -d "$TEMP_DIR/data" ]; then
    log "Restoring application data..."
    
    # Backup current data
    if [ -d "$PROJECT_ROOT/data" ]; then
        mv "$PROJECT_ROOT/data" "$PROJECT_ROOT/data.backup.$(date +%Y%m%d_%H%M%S)"
    fi
    
    # Copy restored data
    cp -r "$TEMP_DIR/data" "$PROJECT_ROOT/"
    check_success "Application data restored"
fi

# Step 7: Import widget configurations if available
if [ -f "$TEMP_DIR/widget_definitions.csv" ]; then
    log "Importing widget definitions..."
    docker exec -i "$DB_CONTAINER" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c \
        "TRUNCATE widget_definitions CASCADE;"
    docker exec -i "$DB_CONTAINER" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c \
        "\COPY widget_definitions FROM STDIN WITH CSV HEADER" < "$TEMP_DIR/widget_definitions.csv"
    check_success "Widget definitions imported"
fi

if [ -f "$TEMP_DIR/dashboard_templates.csv" ]; then
    log "Importing dashboard templates..."
    docker exec -i "$DB_CONTAINER" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c \
        "TRUNCATE dashboard_templates CASCADE;"
    docker exec -i "$DB_CONTAINER" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c \
        "\COPY dashboard_templates FROM STDIN WITH CSV HEADER" < "$TEMP_DIR/dashboard_templates.csv"
    check_success "Dashboard templates imported"
fi

# Step 8: Run migrations to ensure schema is up to date
log "Running database migrations..."
docker compose -f "$PROJECT_ROOT/docker-compose.prod.yml" run --rm backend alembic upgrade head
check_success "Migrations completed"

# Step 9: Clear caches
log "Clearing application caches..."
REDIS_CONTAINER=$(get_container_id redis)
docker exec "$REDIS_CONTAINER" redis-cli FLUSHALL
check_success "Caches cleared"

# Step 10: Start application services
log "Starting application services..."
docker compose -f "$PROJECT_ROOT/docker-compose.prod.yml" start backend frontend celery_worker celery_beat
check_success "Application services started"

# Step 11: Verify application health
log "Waiting for application to be healthy..."
sleep 10

# Check health endpoints
for service in "backend:http://localhost/api/health" "frontend:http://localhost:3000/api/health"; do
    IFS=':' read -r name url <<< "$service"
    if curl -f -s "$url" > /dev/null; then
        log "✓ $name is healthy" "$GREEN"
    else
        log "✗ $name health check failed" "$RED"
    fi
done

# Final summary
log "=========================================" "$GREEN"
log "Restore completed successfully!" "$GREEN"
log "=========================================" "$GREEN"
log "Restored from: $BACKUP_NAME"
log "Database: Restored"
log "Application Data: Restored"
log "Services: Running"
log ""
log "Please verify:" "$YELLOW"
log "1. Application functionality"
log "2. Data integrity"
log "3. User access"
log ""

# Send notification if configured
if [ -n "${SLACK_WEBHOOK_URL:-}" ]; then
    curl -X POST -H 'Content-type: application/json' \
        --data "{\"text\":\"✅ Restore completed successfully\nBackup: $BACKUP_NAME\"}" \
        "$SLACK_WEBHOOK_URL" 2>/dev/null || true
fi

exit 0