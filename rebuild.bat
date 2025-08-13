@echo off
REM ABOUTME: Quick rebuild script for code changes (Windows)
REM ABOUTME: Rebuilds and restarts containers without removing data

echo =============================================
echo    Rebuilding Cortex Dashboard
echo =============================================
echo.

REM Check which service to rebuild
if "%1"=="" (
    echo Rebuilding all services...
    set SERVICE=
) else (
    echo Rebuilding %1 service...
    set SERVICE=%1
)

echo.

REM Stop the containers
echo Stopping containers...
docker compose -f docker-compose.local-prod.yml stop %SERVICE%

REM Rebuild the images
echo Building images...
if "%SERVICE%"=="" (
    docker compose -f docker-compose.local-prod.yml build
) else (
    docker compose -f docker-compose.local-prod.yml build %SERVICE%
)

REM Start the containers
echo Starting containers...
docker compose -f docker-compose.local-prod.yml up -d %SERVICE%

echo.
echo =============================================
echo    Rebuild Complete!
echo =============================================
echo.

REM Show container status
docker compose -f docker-compose.local-prod.yml ps

echo.
echo Usage:
echo   rebuild.bat          - Rebuild all services
echo   rebuild.bat backend  - Rebuild only backend
echo   rebuild.bat frontend - Rebuild only frontend
echo.
echo To view logs:
echo   docker compose -f docker-compose.local-prod.yml logs -f %SERVICE%
echo.

pause