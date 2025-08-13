@echo off
REM ABOUTME: Development helper script with common commands (Windows)
REM ABOUTME: Provides quick access to common development tasks

echo =============================================
echo    Cortex Dashboard - Development Helper
echo =============================================
echo.

if "%1"=="" goto :menu

if "%1"=="logs" goto :logs
if "%1"=="backend-logs" goto :backend_logs
if "%1"=="frontend-logs" goto :frontend_logs
if "%1"=="db" goto :db
if "%1"=="shell" goto :shell
if "%1"=="status" goto :status
if "%1"=="stop" goto :stop
if "%1"=="start" goto :start
if "%1"=="clean" goto :clean

echo Unknown command: %1
goto :menu

:menu
echo Available commands:
echo.
echo   dev.bat logs          - Show all logs
echo   dev.bat backend-logs  - Show backend logs only
echo   dev.bat frontend-logs - Show frontend logs only
echo   dev.bat db           - Connect to PostgreSQL
echo   dev.bat shell        - Open backend shell
echo   dev.bat status       - Show container status
echo   dev.bat stop         - Stop all containers
echo   dev.bat start        - Start all containers
echo   dev.bat clean        - Clean dangling images/volumes
echo.
echo Quick rebuild commands:
echo   rebuild.bat          - Rebuild all services
echo   rebuild.bat backend  - Rebuild backend only
echo   rebuild.bat frontend - Rebuild frontend only
echo.
echo Quick restart commands:
echo   restart.bat          - Restart all services
echo   restart.bat backend  - Restart backend only
echo.
pause
goto :eof

:logs
docker compose -f docker-compose.local-prod.yml logs -f --tail=100
goto :eof

:backend_logs
docker compose -f docker-compose.local-prod.yml logs -f backend --tail=100
goto :eof

:frontend_logs
docker compose -f docker-compose.local-prod.yml logs -f frontend --tail=100
goto :eof

:db
echo Connecting to PostgreSQL...
echo Username: postgres
echo Password: changethis
echo.
docker compose -f docker-compose.local-prod.yml exec postgres psql -U postgres -d clinical_dashboard
goto :eof

:shell
echo Opening backend shell...
docker compose -f docker-compose.local-prod.yml exec backend /bin/bash
goto :eof

:status
docker compose -f docker-compose.local-prod.yml ps
echo.
echo Container health:
docker ps --filter "name=cortex_dash" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
pause
goto :eof

:stop
echo Stopping all containers...
docker compose -f docker-compose.local-prod.yml stop
goto :eof

:start
echo Starting all containers...
docker compose -f docker-compose.local-prod.yml up -d
goto :eof

:clean
echo Cleaning up Docker resources...
docker system prune -f
echo Done!
pause
goto :eof