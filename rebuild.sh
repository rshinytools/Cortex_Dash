#!/bin/bash
# ABOUTME: Quick rebuild script for code changes (Linux/Mac)
# ABOUTME: Rebuilds and restarts containers without removing data

echo "============================================="
echo "   Rebuilding Cortex Dashboard"
echo "============================================="
echo ""

# Check which service to rebuild
SERVICE=$1
if [ -z "$SERVICE" ]; then
    echo "Rebuilding all services..."
    SERVICE=""
else
    echo "Rebuilding $SERVICE service..."
fi

echo ""

# Stop the containers
echo "Stopping containers..."
docker compose -f docker-compose.local-prod.yml stop $SERVICE

# Rebuild the images
echo "Building images..."
if [ -z "$SERVICE" ]; then
    docker compose -f docker-compose.local-prod.yml build
else
    docker compose -f docker-compose.local-prod.yml build $SERVICE
fi

# Start the containers
echo "Starting containers..."
docker compose -f docker-compose.local-prod.yml up -d $SERVICE

echo ""
echo "============================================="
echo "   Rebuild Complete!"
echo "============================================="
echo ""

# Show container status
docker compose -f docker-compose.local-prod.yml ps

echo ""
echo "Usage:"
echo "  ./rebuild.sh          - Rebuild all services"
echo "  ./rebuild.sh backend  - Rebuild only backend"
echo "  ./rebuild.sh frontend - Rebuild only frontend"
echo ""
echo "To view logs:"
echo "  docker compose -f docker-compose.local-prod.yml logs -f $SERVICE"
echo ""