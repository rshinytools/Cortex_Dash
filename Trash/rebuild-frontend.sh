#!/bin/bash
# ABOUTME: Force rebuild frontend with no cache
# ABOUTME: Clears all Next.js cache and Docker cache

echo "🧹 Cleaning all caches..."

# Clear Next.js cache
echo "Removing Next.js cache..."
rm -rf frontend/.next
rm -rf frontend/node_modules/.cache
rm -rf frontend/.turbo
rm -rf frontend/.vercel

# Clear any build artifacts
echo "Removing build artifacts..."
cd frontend
npm cache clean --force 2>/dev/null || true
cd ..

# Stop and remove frontend container
echo "Stopping frontend container..."
docker compose -f docker-compose.local-prod.yml stop frontend
docker compose -f docker-compose.local-prod.yml rm -f frontend

# Remove the frontend image to force rebuild
echo "Removing frontend image..."
docker rmi cortex_dash-frontend:latest 2>/dev/null || true
docker rmi $(docker images -f "dangling=true" -q) 2>/dev/null || true

# Build frontend locally first
echo "📦 Building frontend locally..."
cd frontend
rm -rf .next
npm run build
cd ..

# Rebuild Docker container with no cache
echo "🐳 Building Docker container with no cache..."
docker compose -f docker-compose.local-prod.yml build frontend --no-cache

# Start the frontend
echo "🚀 Starting frontend..."
docker compose -f docker-compose.local-prod.yml up -d frontend

echo "✅ Frontend rebuilt with no cache!"
echo "Please wait a few seconds for the container to start..."
sleep 5
echo "Frontend should now be available at http://localhost:3000"