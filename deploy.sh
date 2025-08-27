#!/bin/bash
# ABOUTME: Quick deployment script for production environment
# ABOUTME: Automates the deployment process with safety checks

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}   Cortex Clinical Dashboard Deployment${NC}"
echo -e "${GREEN}================================================${NC}"

# Check if .env.prod exists
if [ ! -f .env.prod ]; then
    echo -e "${RED}Error: .env.prod file not found!${NC}"
    echo "Please copy .env.prod.template to .env.prod and configure it"
    exit 1
fi

# Load environment variables
export $(grep -v '^#' .env.prod | xargs)

# Function to check if service is healthy
check_health() {
    service=$1
    echo -n "Checking $service health..."
    
    if docker compose -f docker-compose.prod.yml ps | grep -q "$service.*healthy"; then
        echo -e " ${GREEN}✓${NC}"
        return 0
    else
        echo -e " ${RED}✗${NC}"
        return 1
    fi
}

# Parse arguments
SKIP_BUILD=false
SKIP_MIGRATE=false

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --skip-build) SKIP_BUILD=true ;;
        --skip-migrate) SKIP_MIGRATE=true ;;
        --help) 
            echo "Usage: ./deploy.sh [options]"
            echo "Options:"
            echo "  --skip-build    Skip building Docker images"
            echo "  --skip-migrate  Skip database migrations"
            echo "  --help          Show this help message"
            exit 0
            ;;
        *) echo "Unknown parameter: $1"; exit 1 ;;
    esac
    shift
done

# Step 1: Pull latest code (if in git repo)
if [ -d .git ]; then
    echo -e "${YELLOW}Pulling latest code...${NC}"
    git pull origin main || true
fi

# Step 2: Build images
if [ "$SKIP_BUILD" = false ]; then
    echo -e "${YELLOW}Building Docker images...${NC}"
    docker compose -f docker-compose.prod.yml build
else
    echo -e "${YELLOW}Skipping build (--skip-build flag set)${NC}"
fi

# Step 3: Start core services
echo -e "${YELLOW}Starting core services...${NC}"
docker compose -f docker-compose.prod.yml up -d postgres redis

# Wait for services to be healthy
sleep 5
check_health "postgres"
check_health "redis"

# Step 4: Run migrations
if [ "$SKIP_MIGRATE" = false ]; then
    echo -e "${YELLOW}Running database migrations...${NC}"
    docker compose -f docker-compose.prod.yml run --rm backend alembic upgrade head
else
    echo -e "${YELLOW}Skipping migrations (--skip-migrate flag set)${NC}"
fi

# Step 5: Start all services
echo -e "${YELLOW}Starting all services...${NC}"
docker compose -f docker-compose.prod.yml up -d

# Step 6: Wait for services to be ready
echo -e "${YELLOW}Waiting for services to be ready...${NC}"
sleep 10

# Step 7: Health checks
echo -e "${YELLOW}Running health checks...${NC}"
services=("postgres" "redis" "backend" "frontend")
all_healthy=true

for service in "${services[@]}"; do
    if ! check_health "$service"; then
        all_healthy=false
    fi
done

# Step 8: Display status
echo ""
echo -e "${GREEN}================================================${NC}"
if [ "$all_healthy" = true ]; then
    echo -e "${GREEN}✓ Deployment completed successfully!${NC}"
    echo ""
    echo "Your application is available at:"
    echo -e "${GREEN}https://${DOMAIN_NAME:-dashboard.sagarmatha.ai}${NC}"
    echo ""
    echo "Admin login:"
    echo "Email: ${FIRST_SUPERUSER:-admin@sagarmatha.ai}"
    echo "Password: (as configured in .env.prod)"
else
    echo -e "${RED}⚠ Some services are not healthy${NC}"
    echo "Check logs with: docker compose -f docker-compose.prod.yml logs"
fi
echo -e "${GREEN}================================================${NC}"

# Show running containers
echo ""
echo "Running containers:"
docker compose -f docker-compose.prod.yml ps

# Useful commands reminder
echo ""
echo "Useful commands:"
echo "  View logs:    docker compose -f docker-compose.prod.yml logs -f [service]"
echo "  Stop all:     docker compose -f docker-compose.prod.yml down"
echo "  Restart:      docker compose -f docker-compose.prod.yml restart [service]"
echo "  Backup DB:    docker compose -f docker-compose.prod.yml exec backup /backup.sh"