@echo off
REM ABOUTME: Restart script to cleanly restart all Cortex Dashboard services
REM ABOUTME: Preserves data while restarting all containers and services

echo ============================================================
echo    CORTEX CLINICAL DASHBOARD - RESTART SERVICES
echo ============================================================
echo.

REM Check if Docker is running
docker info >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Docker is not running. Please start Docker Desktop and try again.
    pause
    exit /b 1
)

echo Restarting Cortex Dashboard services...
echo.

echo Step 1: Stopping all services...
echo ----------------------------------------
docker compose -f docker-compose.local-prod.yml stop
echo Services stopped.
echo.

echo Step 2: Clearing temporary files...
echo ----------------------------------------
REM Clear Python cache
if exist backend\__pycache__ rmdir /s /q backend\__pycache__ 2>nul
if exist backend\app\__pycache__ rmdir /s /q backend\app\__pycache__ 2>nul

REM Clear Next.js cache
if exist frontend\.next rmdir /s /q frontend\.next 2>nul

echo Temporary files cleared.
echo.

echo Step 3: Starting services in order...
echo ----------------------------------------

REM Start database first
echo Starting PostgreSQL...
docker compose -f docker-compose.local-prod.yml start postgres
timeout /t 5 /nobreak >nul

echo Starting Redis...
docker compose -f docker-compose.local-prod.yml start redis
timeout /t 3 /nobreak >nul

echo Starting Backend...
docker compose -f docker-compose.local-prod.yml start backend
timeout /t 10 /nobreak >nul

echo Starting Frontend...
docker compose -f docker-compose.local-prod.yml start frontend

echo Starting Celery Worker...
docker compose -f docker-compose.local-prod.yml start celery-worker

echo.
echo Step 4: Verifying services...
echo ----------------------------------------
docker compose -f docker-compose.local-prod.yml ps

echo.
echo ============================================================
echo    RESTART COMPLETE!
echo ============================================================
echo.
echo Services are available at:
echo   - Frontend: http://localhost:3000
echo   - Backend API: http://localhost:8000
echo   - API Docs: http://localhost:8000/docs
echo.
echo To view logs: docker compose -f docker-compose.local-prod.yml logs -f
echo.
pause