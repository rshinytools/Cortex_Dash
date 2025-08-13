@echo off
REM ABOUTME: Quick restart script without rebuilding (Windows)
REM ABOUTME: Just restarts containers with existing images

echo =============================================
echo    Restarting Cortex Dashboard
echo =============================================
echo.

REM Check which service to restart
if "%1"=="" (
    echo Restarting all services...
    set SERVICE=
) else (
    echo Restarting %1 service...
    set SERVICE=%1
)

echo.

REM Restart the containers
echo Restarting containers...
docker compose -f docker-compose.local-prod.yml restart %SERVICE%

echo.
echo =============================================
echo    Restart Complete!
echo =============================================
echo.

REM Show container status
docker compose -f docker-compose.local-prod.yml ps

echo.
echo Usage:
echo   restart.bat          - Restart all services
echo   restart.bat backend  - Restart only backend
echo   restart.bat frontend - Restart only frontend
echo.

pause