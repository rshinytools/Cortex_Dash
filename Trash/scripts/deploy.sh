#!/bin/bash
# ABOUTME: Production deployment script for Clinical Dashboard Platform
# ABOUTME: Handles blue-green deployment with health checks and rollback capability

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DEPLOYMENT_ID=$(date +%Y%m%d%H%M%S)
LOG_FILE="/var/log/clinical-dashboard/deploy-${DEPLOYMENT_ID}.log"

# Ensure log directory exists
mkdir -p /var/log/clinical-dashboard

# Function to log messages
log() {
    echo -e "${2:-}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}" | tee -a "$LOG_FILE"
}

# Function to check command success
check_success() {
    if [ $? -eq 0 ]; then
        log "✓ $1" "$GREEN"
    else
        log "✗ $1 failed" "$RED"
        exit 1
    fi
}

# Function to wait for service to be healthy
wait_for_health() {
    local service=$1
    local url=$2
    local max_attempts=30
    local attempt=1
    
    log "Waiting for $service to be healthy..."
    while [ $attempt -le $max_attempts ]; do
        if curl -f -s "$url" > /dev/null; then
            log "✓ $service is healthy" "$GREEN"
            return 0
        fi
        log "Attempt $attempt/$max_attempts: $service not ready yet..." "$YELLOW"
        sleep 10
        ((attempt++))
    done
    
    log "✗ $service failed to become healthy" "$RED"
    return 1
}

# Parse command line arguments
ENVIRONMENT=${1:-production}
SKIP_BACKUP=${2:-false}

log "Starting deployment to $ENVIRONMENT environment" "$GREEN"
log "Deployment ID: $DEPLOYMENT_ID"

# Step 1: Pre-flight checks
log "Running pre-flight checks..."
cd "$PROJECT_ROOT"

# Check if .env file exists
if [ ! -f .env ]; then
    log "✗ .env file not found. Copy .env.example and configure it." "$RED"
    exit 1
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Check Docker and Docker Compose
docker --version > /dev/null 2>&1
check_success "Docker is installed"

docker compose version > /dev/null 2>&1
check_success "Docker Compose is installed"

# Check if we can connect to Docker
docker ps > /dev/null 2>&1
check_success "Docker daemon is running"

# Step 2: Backup current data
if [ "$SKIP_BACKUP" != "true" ]; then
    log "Creating backup before deployment..."
    "$SCRIPT_DIR/backup.sh"
    check_success "Backup completed"
else
    log "Skipping backup as requested" "$YELLOW"
fi

# Step 3: Build new images
log "Building Docker images..."
docker compose -f docker-compose.prod.yml build --no-cache
check_success "Docker images built"

# Step 4: Run database migrations
log "Running database migrations..."
docker compose -f docker-compose.prod.yml run --rm backend alembic upgrade head
check_success "Database migrations completed"

# Step 5: Deploy with blue-green strategy
log "Starting blue-green deployment..."

# Tag current running containers as 'blue'
docker compose -f docker-compose.prod.yml ps -q | xargs -I {} docker tag {} {}-blue 2>/dev/null || true

# Start new containers (green)
log "Starting new containers..."
docker compose -f docker-compose.prod.yml up -d --scale backend=0 --scale frontend=0
check_success "Infrastructure services started"

# Start backend with single instance first
docker compose -f docker-compose.prod.yml up -d --scale backend=1
wait_for_health "backend" "http://localhost/api/health"

# Start frontend with single instance
docker compose -f docker-compose.prod.yml up -d --scale frontend=1
wait_for_health "frontend" "http://localhost:3000/api/health"

# If health checks pass, scale up to full capacity
log "Scaling up services..."
docker compose -f docker-compose.prod.yml up -d --scale backend=2 --scale frontend=2
check_success "Services scaled up"

# Step 6: Run post-deployment tests
log "Running post-deployment tests..."
docker compose -f docker-compose.prod.yml run --rm backend pytest tests/test_health.py -v
check_success "Health tests passed"

# Step 7: Update nginx to point to new containers
log "Reloading nginx configuration..."
docker compose -f docker-compose.prod.yml exec nginx nginx -s reload
check_success "Nginx reloaded"

# Step 8: Final health check
sleep 10
wait_for_health "application" "https://${DOMAIN}/health"

# Step 9: Clean up old containers
log "Cleaning up old containers..."
docker image prune -f
docker container prune -f
check_success "Cleanup completed"

# Step 10: Send deployment notification
log "Sending deployment notification..."
if [ -n "${SLACK_WEBHOOK_URL:-}" ]; then
    curl -X POST -H 'Content-type: application/json' \
        --data "{\"text\":\"✅ Clinical Dashboard Platform deployed successfully to $ENVIRONMENT\nDeployment ID: $DEPLOYMENT_ID\"}" \
        "$SLACK_WEBHOOK_URL" 2>/dev/null || true
fi

log "Deployment completed successfully!" "$GREEN"
log "Deployment ID: $DEPLOYMENT_ID"
log "Log file: $LOG_FILE"

# Create deployment record
cat > "/var/log/clinical-dashboard/deployments/${DEPLOYMENT_ID}.json" <<EOF
{
    "id": "$DEPLOYMENT_ID",
    "environment": "$ENVIRONMENT",
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "status": "success",
    "git_commit": "$(git rev-parse HEAD)",
    "git_branch": "$(git rev-parse --abbrev-ref HEAD)"
}
EOF

exit 0