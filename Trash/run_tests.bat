@echo off
REM ABOUTME: Comprehensive test runner for all implemented phases
REM ABOUTME: Tests RBAC, Data Sources, Integrations, and Advanced Features

echo ============================================================
echo    CORTEX CLINICAL DASHBOARD - COMPREHENSIVE TEST SUITE
echo    Testing Phases 5-8 Implementation
echo ============================================================
echo.

REM Detect Python command
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    py --version >nul 2>&1
    if %ERRORLEVEL% NEQ 0 (
        echo ERROR: Python not found. Please install Python 3.10+
        pause
        exit /b 1
    )
    set PYTHON_CMD=py
) else (
    set PYTHON_CMD=python
)

echo Using Python: %PYTHON_CMD%
%PYTHON_CMD% --version
echo.

REM Initialize counters
set /a total_tests=0
set /a passed_tests=0
set /a failed_tests=0

echo ============================================================
echo    PHASE 5: RBAC SYSTEM
echo ============================================================
echo Testing Role-Based Access Control implementation...
echo.
%PYTHON_CMD% tests\test_rbac_simple.py
if %ERRORLEVEL% EQU 0 (
    set /a passed_tests+=1
    echo.
    echo [PASS] Phase 5: RBAC System
) else (
    set /a failed_tests+=1
    echo.
    echo [FAIL] Phase 5: RBAC System
)
set /a total_tests+=1
echo.

echo ============================================================
echo    PHASE 6: DATA SOURCE FRAMEWORK
echo ============================================================
echo Testing Data Upload, Parquet Conversion, and Widget Mapping...
echo.
%PYTHON_CMD% tests\test_data_source_framework.py
if %ERRORLEVEL% EQU 0 (
    set /a passed_tests+=1
    echo.
    echo [PASS] Phase 6: Data Source Framework
) else (
    set /a failed_tests+=1
    echo.
    echo [FAIL] Phase 6: Data Source Framework
)
set /a total_tests+=1
echo.

echo ============================================================
echo    PHASE 7: API INTEGRATIONS
echo ============================================================
echo Testing Medidata Rave, Veeva Vault, and REDCap integrations...
echo.
%PYTHON_CMD% tests\test_api_integrations.py
if %ERRORLEVEL% EQU 0 (
    set /a passed_tests+=1
    echo.
    echo [PASS] Phase 7: API Integrations
) else (
    set /a failed_tests+=1
    echo.
    echo [FAIL] Phase 7: API Integrations
)
set /a total_tests+=1
echo.

echo ============================================================
echo    PHASE 8: ADVANCED FEATURES
echo ============================================================
echo Testing WebSocket, Filtering, Export, Audit, and Notifications...
echo.
%PYTHON_CMD% tests\test_advanced_features.py
if %ERRORLEVEL% EQU 0 (
    set /a passed_tests+=1
    echo.
    echo [PASS] Phase 8: Advanced Features
) else (
    set /a failed_tests+=1
    echo.
    echo [FAIL] Phase 8: Advanced Features
)
set /a total_tests+=1
echo.

echo ============================================================
echo    TEST SUMMARY
echo ============================================================
echo.
echo Total Test Suites: %total_tests%
echo Passed: %passed_tests%
echo Failed: %failed_tests%
echo.

if %failed_tests% EQU 0 (
    echo SUCCESS: All tests passed!
    echo.
    echo ============================================================
    echo    PLATFORM FEATURES VERIFIED
    echo ============================================================
    echo.
    echo Phase 5: RBAC System
    echo   - 36 granular permissions
    echo   - 5 default roles
    echo   - Dynamic permission management
    echo   - Frontend permission guards
    echo.
    echo Phase 6: Data Source Framework
    echo   - Automatic Parquet conversion
    echo   - File versioning system
    echo   - Simplified widget mapping
    echo   - Multi-format support (CSV, Excel, SAS, ZIP)
    echo.
    echo Phase 7: API Integrations
    echo   - Medidata Rave (OAuth 2.0)
    echo   - Veeva Vault (Session-based)
    echo   - REDCap (Token-based)
    echo   - Secure credential storage
    echo.
    echo Phase 8: Advanced Features
    echo   - Real-time WebSocket updates
    echo   - 15+ filter operators
    echo   - 5 export formats (CSV, Excel, PDF, JSON, HTML)
    echo   - Complete audit trail
    echo   - Notification system
    echo.
) else (
    echo WARNING: Some tests failed. Please review the output above.
    echo.
)

echo ============================================================
echo    NEXT STEPS
echo ============================================================
echo.
echo 1. To start the platform:
echo    - With Docker: docker compose -f docker-compose.local-prod.yml up
echo    - Without Docker: Use run_backend_dev.bat and run_frontend_dev.bat
echo.
echo 2. Access the application:
echo    - Frontend: http://localhost:3000
echo    - API Docs: http://localhost:8000/docs
echo.
echo 3. Login credentials:
echo    - Email: admin@sagarmatha.ai
echo    - Password: adadad123
echo.
pause