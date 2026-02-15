@echo off
REM PRESTYJ Lead Scraper — One-Click Setup (Windows)

echo =========================================
echo   PRESTYJ Lead Scraper — Setup
echo =========================================
echo.

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed.
    echo Download it from https://www.python.org/downloads/
    echo IMPORTANT: Check the "Add Python to PATH" box during installation.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version') do echo Python found: %%i
echo.

REM Create virtual environment
echo Creating virtual environment...
python -m venv venv
echo Done.
echo.

REM Activate and install
echo Installing requirements...
call venv\Scripts\activate.bat
pip install -r requirements.txt --quiet
echo Done.
echo.

REM Copy .env if needed
if not exist .env (
    copy .env.example .env >nul
    echo Created .env file from template.
) else (
    echo .env file already exists — skipping.
)

echo.
echo =========================================
echo   Setup complete!
echo =========================================
echo.
echo Next steps:
echo   1. Open the .env file and paste your Google Places API key
echo   2. Run the app:
echo.
echo      venv\Scripts\activate.bat
echo      streamlit run app.py
echo.
echo Your browser will open automatically.
echo.
pause
