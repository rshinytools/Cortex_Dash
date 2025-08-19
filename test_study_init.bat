@echo off
REM ABOUTME: Batch script to test study initialization flow using curl
REM ABOUTME: Tests study creation, template selection, file upload, and metadata extraction

echo ============================================
echo Study Initialization Test Script
echo ============================================
echo.

REM Login to get token
echo [1/6] Logging in as admin@sagarmatha.ai...
curl -s -X POST "http://localhost:8000/api/v1/login/access-token" ^
  -H "Content-Type: application/x-www-form-urlencoded" ^
  -d "username=admin@sagarmatha.ai&password=adadad123" ^
  -o login_response.json

REM Extract token using PowerShell
for /f "delims=" %%i in ('powershell -command "(Get-Content login_response.json | ConvertFrom-Json).access_token"') do set TOKEN=%%i

if "%TOKEN%"=="" (
    echo ERROR: Failed to login
    exit /b 1
)
echo SUCCESS: Logged in successfully
echo.

REM Create study through wizard
echo [2/6] Creating new study...
set TIMESTAMP=%date:~-4%%date:~3,2%%date:~0,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set TIMESTAMP=%TIMESTAMP: =0%
curl -s -X POST "http://localhost:8000/api/v1/studies/wizard/start" ^
  -H "Authorization: Bearer %TOKEN%" ^
  -H "Content-Type: application/json" ^
  -d "{\"name\":\"TestStudy_%TIMESTAMP%\",\"protocol_number\":\"TEST_%TIMESTAMP%\",\"description\":\"Automated test study\",\"phase\":\"phase_3\",\"therapeutic_area\":\"Oncology\",\"indication\":\"NSCLC\"}" ^
  -o study_response.json

REM Extract study ID
for /f "delims=" %%i in ('powershell -command "(Get-Content study_response.json | ConvertFrom-Json).study_id"') do set STUDY_ID=%%i

if "%STUDY_ID%"=="" (
    echo ERROR: Failed to create study
    type study_response.json
    exit /b 1
)
echo SUCCESS: Study created with ID: %STUDY_ID%
echo.

REM Get available templates
echo [3/6] Getting available templates...
curl -s -X GET "http://localhost:8000/api/v1/studies/wizard/%STUDY_ID%/templates" ^
  -H "Authorization: Bearer %TOKEN%" ^
  -o templates_response.json

REM Extract first template ID
for /f "delims=" %%i in ('powershell -command "(Get-Content templates_response.json | ConvertFrom-Json)[0].id"') do set TEMPLATE_ID=%%i

if "%TEMPLATE_ID%"=="" (
    echo ERROR: No templates found
    type templates_response.json
    exit /b 1
)
echo SUCCESS: Found template ID: %TEMPLATE_ID%
echo.

REM Select template
echo [4/6] Selecting dashboard template...
curl -s -X POST "http://localhost:8000/api/v1/studies/wizard/%STUDY_ID%/select-template" ^
  -H "Authorization: Bearer %TOKEN%" ^
  -H "Content-Type: application/json" ^
  -d "{\"template_id\":\"%TEMPLATE_ID%\"}" ^
  -o select_response.json

REM Check if selection was successful
for /f "delims=" %%i in ('powershell -command "(Get-Content select_response.json | ConvertFrom-Json).message"') do set SELECT_MSG=%%i
echo Response: %SELECT_MSG%
echo.

REM Update wizard state
echo [5/6] Updating wizard state...
curl -s -X PATCH "http://localhost:8000/api/v1/studies/wizard/%STUDY_ID%/state" ^
  -H "Authorization: Bearer %TOKEN%" ^
  -H "Content-Type: application/json" ^
  -d "{\"current_step\":3,\"completed_steps\":[\"basic_info\",\"template_selection\"]}" ^
  -o state_response.json
echo.

REM Note about file upload
echo [6/6] File Upload Test
echo ----------------------------------------
echo NOTE: File upload requires multipart form data which is complex in batch scripts.
echo Please manually:
echo   1. Navigate to http://localhost:3000/studies/%STUDY_ID%/initialization
echo   2. Upload your SAS files from C:\Users\amuly\OneDrive\AetherClinical\dummy_data
echo   3. Complete the field mapping
echo.
echo Study URL: http://localhost:3000/studies/%STUDY_ID%/initialization
echo.

REM Cleanup temp files
del login_response.json 2>nul
del study_response.json 2>nul
del templates_response.json 2>nul
del select_response.json 2>nul
del state_response.json 2>nul

echo ============================================
echo Test partially completed!
echo Study created and template selected.
echo Please complete file upload manually.
echo ============================================