@echo off
REM Local testing script for My Meal Planner (Windows)
REM This script sets up and runs the backend server locally

echo 🚀 Starting My Meal Planner Backend (Local)
echo ============================================

REM Check if virtual environment exists
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo 📥 Installing dependencies...
pip install -q --upgrade pip
pip install -q -r mymealplanner\requirements.txt

REM Check for required environment variables
if "%GOOGLE_CLOUD_PROJECT%"=="" (
    echo.
    echo ⚠️  WARNING: GOOGLE_CLOUD_PROJECT not set!
    echo    Please set it with: set GOOGLE_CLOUD_PROJECT=your-project-id
    echo.
    set /p project_id="Enter your Google Cloud Project ID: "
    set GOOGLE_CLOUD_PROJECT=%project_id%
)

if "%GOOGLE_CLOUD_LOCATION%"=="" (
    set GOOGLE_CLOUD_LOCATION=us-central1
    echo 📍 Using default location: us-central1
)

echo.
echo ✅ Starting server on http://localhost:8080
echo    Frontend: Open index.html in your browser
echo    Press Ctrl+C to stop
echo.

REM Run the server
python main.py

