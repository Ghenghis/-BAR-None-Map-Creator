@echo on
REM === BAR Map Creator: Debug Clean & Build Script ===

REM Step 0: Ensure Python is available
where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH. | tee build_log.txt
    echo Please install Python 3.8+ and try again. | tee -a build_log.txt
    pause
    exit /b 1
)

REM Step 1: Clean up old builds and environments
echo Cleaning previous builds and environments... | tee -a build_log.txt
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist __pycache__ rmdir /s /q __pycache__
if exist clean_build_env rmdir /s /q clean_build_env
del /q *.spec 2>nul

REM Step 2: Create a new virtual environment if needed
echo Creating clean virtual environment... | tee -a build_log.txt
python -m venv clean_build_env >> build_log.txt 2>&1
if not exist clean_build_env\Scripts\activate.bat (
    echo [ERROR] Failed to create virtual environment. | tee -a build_log.txt
    echo Please check Python installation and try again. | tee -a build_log.txt
    pause
    exit /b 1
)

REM Step 3: Activate the virtual environment
call clean_build_env\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment. | tee -a build_log.txt
    pause
    exit /b 1
)

REM Step 4: Upgrade pip
echo Upgrading pip... | tee -a build_log.txt
python -m pip install --upgrade pip >> build_log.txt 2>&1
if errorlevel 1 (
    echo [ERROR] Failed to upgrade pip. | tee -a build_log.txt
    pause
    exit /b 1
)

REM Step 5: Install required dependencies
echo Installing dependencies... | tee -a build_log.txt
pip install -r requirements.txt >> build_log.txt 2>&1
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies. | tee -a build_log.txt
    pause
    exit /b 1
)

REM Step 6: Build the EXE (log output)
echo Building the standalone EXE... | tee -a build_log.txt
pyinstaller --noconfirm --onefile --windowed --name "BAR-Map-Creator.exe" map_creator_app.py >> build_log.txt 2>&1
if errorlevel 1 (
    echo [ERROR] PyInstaller build failed. | tee -a build_log.txt
    pause
    exit /b 1
)

REM Step 7: Move the EXE to project root
if exist dist\BAR-Map-Creator.exe move /Y dist\BAR-Map-Creator.exe .

REM Step 8: Deactivate the virtual environment
deactivate

echo.
echo Build complete! Your EXE is ready in the project folder. | tee -a build_log.txt
echo Check build_log.txt for details if there was a problem. | tee -a build_log.txt
pause
