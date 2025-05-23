@echo on
REM === BAR Map Creator: Debug Clean & Build Script ===

REM Step 0: Ensure Python is available
where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH.
    echo [ERROR] Python is not installed or not in PATH. > build_log.txt 2>&1
    echo Please install Python 3.8+ and try again.
    echo Please install Python 3.8+ and try again. >> build_log.txt 2>&1
    pause
    exit /b 1
)

REM Step 1: Clean up old builds and environments
echo Cleaning previous builds and environments...
echo Cleaning previous builds and environments... >> build_log.txt 2>&1
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist __pycache__ rmdir /s /q __pycache__
if exist clean_build_env rmdir /s /q clean_build_env
REM del /q *.spec 2>nul  <- Keep the spec file now

REM Step 2: Create a new virtual environment if needed
echo Creating clean virtual environment...
echo Creating clean virtual environment... >> build_log.txt 2>&1
python -m venv clean_build_env >> build_log.txt 2>&1
if not exist clean_build_env\Scripts\activate.bat (
    echo [ERROR] Failed to create virtual environment.
    echo [ERROR] Failed to create virtual environment. >> build_log.txt 2>&1
    echo Please check Python installation and try again.
    echo Please check Python installation and try again. >> build_log.txt 2>&1
    pause
    exit /b 1
)

REM Step 3: Activate the virtual environment
call clean_build_env\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment.
    echo [ERROR] Failed to activate virtual environment. >> build_log.txt 2>&1
    pause
    exit /b 1
)

REM Step 4: Upgrade pip
echo Upgrading pip...
echo Upgrading pip... >> build_log.txt 2>&1
python -m pip install --upgrade pip >> build_log.txt 2>&1
if errorlevel 1 (
    echo [ERROR] Failed to upgrade pip.
    echo [ERROR] Failed to upgrade pip. >> build_log.txt 2>&1
    pause
    exit /b 1
)

REM Step 5: Install required dependencies
echo Installing dependencies...
echo Installing dependencies... >> build_log.txt 2>&1
pip install -r requirements.txt >> build_log.txt 2>&1
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies.
    echo [ERROR] Failed to install dependencies. >> build_log.txt 2>&1
    pause
    exit /b 1
)

REM Step 6: Build the EXE using spec file (log output)
echo Building the standalone EXE using spec file...
echo Building the standalone EXE using spec file... >> build_log.txt 2>&1
pyinstaller --noconfirm BAR-Map-Creator.exe.spec >> build_log.txt 2>&1
if errorlevel 1 (
    echo [ERROR] PyInstaller build failed.
    echo [ERROR] PyInstaller build failed. >> build_log.txt 2>&1
    pause
    exit /b 1
)

REM Step 7: Move the EXE to project root
if exist dist\BAR-Map-Creator.exe move /Y dist\BAR-Map-Creator.exe .

REM Step 8: Deactivate the virtual environment
deactivate

echo.
echo Build complete! Your EXE is ready in the project folder.
echo Build complete! Your EXE is ready in the project folder. >> build_log.txt 2>&1
echo Check build_log.txt for details if there was a problem.
echo Check build_log.txt for details if there was a problem. >> build_log.txt 2>&1
pause
