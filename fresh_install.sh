#!/bin/bash
# ABOUTME: Complete fresh installation script for Cortex Dashboard
# ABOUTME: Removes all old containers, volumes, and creates a fresh installation

set -e

echo "============================================="
echo "   Cortex Dashboard - Fresh Installation"
echo "============================================="
echo ""

# Function to check if Docker is running
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        echo "Docker is not running. Please start Docker Desktop and try again."
        exit 1
    fi
}

# Function to clean up existing installation
cleanup_existing() {
    echo "Step 1: Cleaning up existing installation..."
    echo "----------------------------------------"
    
    # Stop all containers
    echo "Stopping existing containers..."
    docker compose -f docker-compose.local-prod.yml down 2>/dev/null || true
    
    # Remove specific containers if they exist
    echo "Removing old containers..."
    docker rm -f cortex_dash-backend-1 2>/dev/null || true
    docker rm -f cortex_dash-frontend-1 2>/dev/null || true
    docker rm -f cortex_dash-db-1 2>/dev/null || true
    docker rm -f cortex_dash-redis-1 2>/dev/null || true
    docker rm -f cortex_dash-celery-worker-1 2>/dev/null || true
    docker rm -f cortex_dash-prestart-1 2>/dev/null || true
    
    # Remove volumes
    echo "Removing old volumes..."
    docker volume rm cortex_dash_postgres_data 2>/dev/null || true
    docker volume rm cortexdash_postgres_data 2>/dev/null || true
    
    # Remove old images
    echo "Removing old images..."
    docker rmi cortex-backend:prod 2>/dev/null || true
    docker rmi cortex-backend:dev 2>/dev/null || true
    docker rmi cortex-frontend:prod 2>/dev/null || true
    
    echo "Cleanup complete!"
    echo ""
}

# Function to build fresh images
build_fresh() {
    echo "Step 2: Building fresh Docker images..."
    echo "----------------------------------------"
    
    # Build backend
    echo "Building backend image..."
    docker build -t cortex-backend:prod -f backend/Dockerfile backend/
    
    # Build frontend
    echo "Building frontend image..."
    docker build -t cortex-frontend:prod -f frontend/Dockerfile frontend/ --target runner \
        --build-arg NODE_ENV=production \
        --build-arg NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1 \
        --build-arg NEXTAUTH_URL=http://localhost:3000 \
        --build-arg NEXTAUTH_SECRET=your-secret-key-here-change-in-production
    
    echo "Build complete!"
    echo ""
}

# Function to start services
start_services() {
    echo "Step 3: Starting services..."
    echo "----------------------------------------"
    
    # Start database and redis first
    echo "Starting database and cache services..."
    docker compose -f docker-compose.local-prod.yml up -d postgres redis
    
    # Wait for PostgreSQL to be ready
    echo "Waiting for PostgreSQL to be ready..."
    sleep 10
    
    # Start backend (which will auto-initialize)
    echo "Starting backend service (with auto-initialization)..."
    docker compose -f docker-compose.local-prod.yml up -d backend
    
    # Wait for backend to be ready
    echo "Waiting for backend to initialize..."
    sleep 15
    
    # Start remaining services
    echo "Starting frontend and worker services..."
    docker compose -f docker-compose.local-prod.yml up -d frontend celery-worker
    
    echo "All services started!"
    echo ""
}

# Function to verify installation
verify_installation() {
    echo "Step 4: Verifying installation..."
    echo "----------------------------------------"
    
    # Check if services are running
    echo "Checking service status..."
    docker compose -f docker-compose.local-prod.yml ps
    
    # Check database
    echo ""
    echo "Checking database initialization..."
    docker compose -f docker-compose.local-prod.yml exec postgres psql -U postgres -d clinical_dashboard -c "SELECT COUNT(*) as tables FROM information_schema.tables WHERE table_schema = 'public';" 2>/dev/null || echo "Database check failed"
    
    # Check organization
    echo ""
    echo "Checking organization setup..."
    docker compose -f docker-compose.local-prod.yml exec postgres psql -U postgres -d clinical_dashboard -c "SELECT name FROM organization;" 2>/dev/null || echo "Organization check failed"
    
    # Check admin user
    echo ""
    echo "Checking admin user setup..."
    docker compose -f docker-compose.local-prod.yml exec postgres psql -U postgres -d clinical_dashboard -c "SELECT email, org_id IS NOT NULL as has_org FROM \"user\" WHERE email = 'admin@sagarmatha.ai';" 2>/dev/null || echo "Admin user check failed"
    
    echo ""
    echo "Verification complete!"
    echo ""
}

# Main execution
main() {
    echo "This will completely remove and reinstall Cortex Dashboard."
    echo "WARNING: All existing data will be lost!"
    echo ""
    read -p "Do you want to continue? (yes/no): " confirm
    
    if [ "$confirm" != "yes" ]; then
        echo "Installation cancelled."
        exit 0
    fi
    
    echo ""
    
    # Check Docker
    check_docker
    
    # Run installation steps
    cleanup_existing
    build_fresh
    start_services
    verify_installation
    
    echo "============================================="
    echo "   Installation Complete!"
    echo "============================================="
    echo ""
    echo "Access the application at:"
    echo "  - Frontend: http://localhost:3000"
    echo "  - Backend API: http://localhost:8000"
    echo "  - API Docs: http://localhost:8000/docs"
    echo ""
    echo "Login credentials:"
    echo "  - Email: admin@sagarmatha.ai"
    echo "  - Password: adadad123"
    echo ""
    echo "To view logs:"
    echo "  docker compose -f docker-compose.local-prod.yml logs -f"
    echo ""
}

# Run main function
main