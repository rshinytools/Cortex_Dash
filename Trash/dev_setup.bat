@echo off
REM ABOUTME: Development setup script for local development without Docker
REM ABOUTME: Sets up Python and Node.js environments for development

echo ============================================================
echo    CORTEX DASHBOARD - DEVELOPMENT SETUP
echo    Local Development Environment (No Docker)
echo ============================================================
echo.

REM Check Python
echo Checking Python installation...
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
%PYTHON_CMD% --version

REM Check Node.js
echo Checking Node.js installation...
node --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Node.js not found. Please install Node.js 18+
    pause
    exit /b 1
)
node --version

echo.
echo Step 1: Setting up Backend...
echo ----------------------------------------
cd backend

REM Create virtual environment if it doesn't exist
if not exist venv (
    echo Creating Python virtual environment...
    %PYTHON_CMD% -m venv venv
)

REM Activate and install dependencies
echo Installing backend dependencies...
call venv\Scripts\activate.bat

%PYTHON_CMD% -m pip install --upgrade pip
pip install -r requirements.txt 2>nul

if %ERRORLEVEL% NEQ 0 (
    echo Installing core dependencies...
    pip install fastapi uvicorn sqlmodel psycopg2-binary alembic
    pip install pandas numpy pyarrow openpyxl xlsxwriter
    pip install redis celery python-multipart python-jose[cryptography]
    pip install passlib bcrypt python-dotenv email-validator
    pip install httpx aiohttp aiofiles websockets
    pip install reportlab pillow
)

REM Create .env if it doesn't exist
if not exist .env (
    echo Creating .env file...
    copy .env.example .env 2>nul || (
        echo # Development Environment > .env
        echo DATABASE_URL=postgresql://postgres:changethis@localhost/cortex_clinical >> .env
        echo SECRET_KEY=dev-secret-key-change-in-production >> .env
    )
)

deactivate
cd ..

echo.
echo Step 2: Setting up Frontend...
echo ----------------------------------------
cd frontend

REM Install dependencies
echo Installing frontend dependencies...
call npm install

REM Create .env.local if it doesn't exist
if not exist .env.local (
    echo Creating .env.local file...
    echo NEXT_PUBLIC_API_URL=http://localhost:8000 > .env.local
    echo NEXT_PUBLIC_WS_URL=ws://localhost:8000 >> .env.local
)

cd ..

echo.
echo Step 3: Creating helper scripts...
echo ----------------------------------------

REM Create run_backend_dev.bat
echo Creating run_backend_dev.bat...
(
    echo @echo off
    echo cd backend
    echo call venv\Scripts\activate
    echo echo Starting Backend Development Server...
    echo uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
) > run_backend_dev.bat

REM Create run_frontend_dev.bat
echo Creating run_frontend_dev.bat...
(
    echo @echo off
    echo cd frontend
    echo echo Starting Frontend Development Server...
    echo npm run dev
) > run_frontend_dev.bat

REM Create run_tests_dev.bat
echo Creating run_tests_dev.bat...
(
    echo @echo off
    echo cd backend
    echo call venv\Scripts\activate
    echo echo Running Platform Tests...
    echo echo.
    echo echo Phase 5: RBAC System
    echo python ../tests/test_rbac_simple.py
    echo echo.
    echo echo Phase 6: Data Source Framework
    echo python ../tests/test_data_source_framework.py
    echo echo.
    echo echo Phase 7: API Integrations
    echo python ../tests/test_api_integrations.py
    echo echo.
    echo echo Phase 8: Advanced Features
    echo python ../tests/test_advanced_features.py
    echo pause
) > run_tests_dev.bat

echo.
echo ============================================================
echo    DEVELOPMENT SETUP COMPLETE!
echo ============================================================
echo.
echo To start development:
echo   1. Backend:  run_backend_dev.bat
echo   2. Frontend: run_frontend_dev.bat
echo   3. Tests:    run_tests_dev.bat
echo.
echo Make sure you have PostgreSQL and Redis running locally!
echo.
echo Features implemented:
echo   - Phase 5: RBAC System (36 permissions, 5 roles)
echo   - Phase 6: Data Sources (Parquet conversion, versioning)
echo   - Phase 7: Integrations (Medidata, Veeva, REDCap)
echo   - Phase 8: Advanced (WebSocket, Export, Audit, Notifications)
echo.
pause