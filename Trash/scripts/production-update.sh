#!/bin/bash

# ABOUTME: Production update script for zero-downtime deployments
# ABOUTME: Updates the application with minimal disruption to users

set -e

echo "🚀 Starting production update..."

# 1. Build new images without stopping the old ones
echo "📦 Building new images..."
docker-compose -f docker-compose.prod.yml build

# 2. Update backend with rolling restart
echo "🔄 Updating backend service..."
docker-compose -f docker-compose.prod.yml up -d --no-deps --scale backend=2 backend
sleep 10  # Wait for new container to be healthy
docker-compose -f docker-compose.prod.yml up -d --no-deps --scale backend=1 backend

# 3. Update frontend with rolling restart
echo "🔄 Updating frontend service..."
docker-compose -f docker-compose.prod.yml up -d --no-deps --scale frontend=2 frontend
sleep 10  # Wait for new container to be healthy
docker-compose -f docker-compose.prod.yml up -d --no-deps --scale frontend=1 frontend

# 4. Update other services if needed
echo "🔄 Updating other services..."
docker-compose -f docker-compose.prod.yml up -d --no-deps redis nginx

# 5. Run any new seeds or migrations
echo "🌱 Running database updates..."
docker exec $(docker ps -qf "name=backend") python -m alembic upgrade head
docker exec $(docker ps -qf "name=backend") python app/initial_data.py
docker exec $(docker ps -qf "name=backend") python -m app.db.seed_metrics_card_widget || true

# 6. Clean up old images
echo "🧹 Cleaning up..."
docker image prune -f

echo "✅ Production update complete!"
echo "📊 Check application health at: http://localhost/api/health"