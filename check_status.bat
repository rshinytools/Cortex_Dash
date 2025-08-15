@echo off
REM ABOUTME: System status check script for Cortex Clinical Dashboard
REM ABOUTME: Verifies all components and features are properly configured

echo ============================================================
echo    CORTEX CLINICAL DASHBOARD - SYSTEM STATUS CHECK
echo ============================================================
echo.

echo Checking Docker Services...
echo ----------------------------------------
docker info >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [FAIL] Docker is not running
    echo.
    goto :check_local
) else (
    echo [OK] Docker is running
)

REM Check containers
echo.
echo Container Status:
docker compose -f docker-compose.local-prod.yml ps 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo No containers found. Run fresh_install.bat to set up.
    goto :check_local
)

REM Check database
echo.
echo Database Status:
docker compose -f docker-compose.local-prod.yml exec postgres psql -U postgres -d clinical_dashboard -c "SELECT version();" 2>nul
if %ERRORLEVEL% EQU 0 (
    echo [OK] PostgreSQL is running
    
    REM Check tables
    echo.
    echo Database Tables:
    docker compose -f docker-compose.local-prod.yml exec postgres psql -U postgres -d clinical_dashboard -c "SELECT COUNT(*) as table_count FROM information_schema.tables WHERE table_schema = 'public';" 2>nul
    
    REM Check RBAC
    echo.
    echo RBAC Configuration:
    docker compose -f docker-compose.local-prod.yml exec postgres psql -U postgres -d clinical_dashboard -c "SELECT COUNT(*) as permission_count FROM permissions;" 2>nul
    docker compose -f docker-compose.local-prod.yml exec postgres psql -U postgres -d clinical_dashboard -c "SELECT COUNT(*) as role_count FROM roles;" 2>nul
    
    REM Check admin user
    echo.
    echo Admin User:
    docker compose -f docker-compose.local-prod.yml exec postgres psql -U postgres -d clinical_dashboard -c "SELECT email, is_active FROM \"user\" WHERE email = 'admin@sagarmatha.ai';" 2>nul
) else (
    echo [FAIL] PostgreSQL connection failed
)

:check_local
echo.
echo ============================================================
echo    FEATURE IMPLEMENTATION STATUS
echo ============================================================
echo.

echo Phase 5: RBAC System
echo ----------------------------------------
if exist backend\app\models\rbac.py (
    echo [OK] RBAC models found
) else (
    echo [MISSING] RBAC models
)
if exist backend\app\services\rbac\permission_service.py (
    echo [OK] Permission service found
) else (
    echo [MISSING] Permission service
)
if exist frontend\src\components\guards\PermissionGuard.tsx (
    echo [OK] Frontend permission guards found
) else (
    echo [MISSING] Frontend permission guards
)

echo.
echo Phase 6: Data Source Framework
echo ----------------------------------------
if exist backend\app\services\data\upload_service.py (
    echo [OK] Upload service with Parquet conversion found
) else (
    echo [MISSING] Upload service
)
if exist backend\app\services\data\versioning_service.py (
    echo [OK] Versioning service found
) else (
    echo [MISSING] Versioning service
)
if exist frontend\src\components\data\DataUploadDialog.tsx (
    echo [OK] Data upload UI found
) else (
    echo [MISSING] Data upload UI
)

echo.
echo Phase 7: API Integrations
echo ----------------------------------------
if exist backend\app\services\integrations\medidata_rave.py (
    echo [OK] Medidata Rave integration found
) else (
    echo [MISSING] Medidata Rave integration
)
if exist backend\app\services\integrations\veeva_vault.py (
    echo [OK] Veeva Vault integration found
) else (
    echo [MISSING] Veeva Vault integration
)
if exist backend\app\services\integrations\redcap.py (
    echo [OK] REDCap integration found
) else (
    echo [MISSING] REDCap integration
)

echo.
echo Phase 8: Advanced Features
echo ----------------------------------------
if exist backend\app\services\realtime\websocket_manager.py (
    echo [OK] WebSocket manager found
) else (
    echo [MISSING] WebSocket manager
)
if exist backend\app\services\filtering\filter_service.py (
    echo [OK] Advanced filtering found
) else (
    echo [MISSING] Advanced filtering
)
if exist backend\app\services\export\export_service.py (
    echo [OK] Export service found
) else (
    echo [MISSING] Export service
)
if exist backend\app\services\audit\audit_service.py (
    echo [OK] Audit service found
) else (
    echo [MISSING] Audit service
)
if exist backend\app\services\notifications\notification_service.py (
    echo [OK] Notification service found
) else (
    echo [MISSING] Notification service
)

echo.
echo ============================================================
echo    SERVICE ENDPOINTS
echo ============================================================
echo.

REM Check if services are accessible
echo Checking service availability...
echo.

curl -s http://localhost:8000/health >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [OK] Backend API: http://localhost:8000
    echo     API Docs: http://localhost:8000/docs
) else (
    echo [OFFLINE] Backend API not accessible
)

curl -s http://localhost:3000 >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [OK] Frontend: http://localhost:3000
) else (
    echo [OFFLINE] Frontend not accessible
)

echo.
echo ============================================================
echo    QUICK ACTIONS
echo ============================================================
echo.
echo 1. Fresh Install:     fresh_install.bat
echo 2. Restart Services:  restart_fresh.bat
echo 3. Rebuild Platform:  rebuild_platform.bat
echo 4. Dev Setup:         dev_setup.bat
echo 5. Run Tests:         run_tests.bat
echo.
echo Default Credentials:
echo   Email: admin@sagarmatha.ai
echo   Password: adadad123
echo.
pause