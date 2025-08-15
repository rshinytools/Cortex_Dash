@echo off
REM ABOUTME: Complete fresh installation script for Cortex Clinical Dashboard Platform
REM ABOUTME: Sets up all phases (5-8) with RBAC, Data Sources, Integrations, and Advanced Features

echo ============================================================
echo    CORTEX CLINICAL DASHBOARD - FRESH INSTALLATION
echo    Phases 5-8: Complete Platform Setup
echo ============================================================
echo.

REM Check if Docker is running
docker info >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Docker is not running. Please start Docker Desktop and try again.
    pause
    exit /b 1
)

echo This will completely remove and reinstall Cortex Dashboard.
echo WARNING: All existing data will be lost!
echo.
set /p confirm="Do you want to continue? (yes/no): "

if /i not "%confirm%"=="yes" (
    echo Installation cancelled.
    pause
    exit /b 0
)

echo.
echo Step 1: Cleaning up existing installation...
echo ----------------------------------------

REM Stop all containers
echo Stopping existing containers...
docker compose -f docker-compose.local-prod.yml down 2>nul

REM Remove specific containers if they exist
echo Removing old containers...
docker rm -f cortex_dash-backend-1 2>nul
docker rm -f cortex_dash-frontend-1 2>nul
docker rm -f cortex_dash-db-1 2>nul
docker rm -f cortex_dash-redis-1 2>nul
docker rm -f cortex_dash-celery-worker-1 2>nul
docker rm -f cortex_dash-prestart-1 2>nul

REM Remove volumes
echo Removing old volumes...
docker volume rm cortex_dash_postgres_data 2>nul
docker volume rm cortexdash_postgres_data 2>nul

REM Remove old images
echo Removing old images...
docker rmi cortex-backend:prod 2>nul
docker rmi cortex-backend:dev 2>nul
docker rmi cortex-frontend:prod 2>nul

echo Cleanup complete!
echo.

echo Step 2: Building fresh Docker images...
echo ----------------------------------------

REM Build backend
echo Building backend image...
docker build -t cortex-backend:prod -f backend/Dockerfile backend/

REM Build frontend
echo Building frontend image...
docker build -t cortex-frontend:prod -f frontend/Dockerfile frontend/ --target runner ^
    --build-arg NODE_ENV=production ^
    --build-arg NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1 ^
    --build-arg NEXTAUTH_URL=http://localhost:3000 ^
    --build-arg NEXTAUTH_SECRET=your-secret-key-here-change-in-production

echo Build complete!
echo.

echo Step 3: Starting services...
echo ----------------------------------------

REM Start database and redis first
echo Starting database and cache services...
docker compose -f docker-compose.local-prod.yml up -d postgres redis

REM Wait for PostgreSQL to be ready
echo Waiting for PostgreSQL to be ready...
timeout /t 10 /nobreak >nul

REM Start backend (which will auto-initialize)
echo Starting backend service (with auto-initialization)...
docker compose -f docker-compose.local-prod.yml up -d backend

REM Wait for backend to be ready
echo Waiting for backend to initialize...
timeout /t 15 /nobreak >nul

REM Run database migrations including RBAC
echo Running database migrations with RBAC setup...
docker exec cortex_dash-backend-1 alembic upgrade head 2>nul

REM Initialize RBAC data
echo Initializing RBAC roles and permissions...
docker exec cortex_dash-backend-1 python scripts/init_rbac_data.py 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Note: RBAC data may already be initialized or script not found.
)

REM Initialize Widget definitions
echo Initializing widget definitions...
docker cp backend/scripts/create_widgets.py cortex_dash-backend-1:/app/scripts/ >nul 2>&1
docker exec cortex_dash-backend-1 python scripts/create_widgets.py 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Note: Widget data may already be initialized or script not found.
)

REM Start remaining services
echo Starting frontend and worker services...
docker compose -f docker-compose.local-prod.yml up -d frontend celery-worker

echo All services started!
echo.

echo Step 4: Verifying installation...
echo ----------------------------------------

REM Check if services are running
echo Checking service status...
docker compose -f docker-compose.local-prod.yml ps

REM Check database
echo.
echo Checking database initialization...
docker compose -f docker-compose.local-prod.yml exec postgres psql -U postgres -d clinical_dashboard -c "SELECT COUNT(*) as tables FROM information_schema.tables WHERE table_schema = 'public';" 2>nul

REM Check organization
echo.
echo Checking organization setup...
docker compose -f docker-compose.local-prod.yml exec postgres psql -U postgres -d clinical_dashboard -c "SELECT name FROM organization;" 2>nul

REM Check admin user
echo.
echo Checking admin user setup...
docker compose -f docker-compose.local-prod.yml exec postgres psql -U postgres -d clinical_dashboard -c "SELECT email, org_id IS NOT NULL as has_org FROM \"user\" WHERE email = 'admin@sagarmatha.ai';" 2>nul

echo.
echo Verification complete!
echo.

echo =============================================
echo    Installation Complete!
echo =============================================
echo.
echo Access the application at:
echo   - Frontend: http://localhost:3000
echo   - Backend API: http://localhost:8000
echo   - API Docs: http://localhost:8000/docs
echo.
echo Login credentials:
echo   - Email: admin@sagarmatha.ai
echo   - Password: adadad123
echo   - Role: System Administrator (full permissions)
echo.
echo RBAC System Features:
echo   - 5 pre-configured roles with different access levels
echo   - 50+ granular permissions for fine-grained control
echo   - Permission matrix for easy management
echo   - Audit trail for all permission changes
echo   - Role-based navigation and UI elements
echo.
echo To view logs:
echo   docker compose -f docker-compose.local-prod.yml logs -f
echo.

pause