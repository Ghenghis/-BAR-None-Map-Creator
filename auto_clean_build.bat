@echo off
REM === BAR Map Creator: Automated Clean & Build Script ===

REM Step 0: Clean up old builds and environments
echo Cleaning previous builds and environments...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist __pycache__ rmdir /s /q __pycache__
if exist clean_build_env rmdir /s /q clean_build_env
del /q *.spec 2>nul

REM Step 1: Create a new virtual environment
echo Creating clean virtual environment...
python -m venv clean_build_env

REM Step 2: Activate the virtual environment
call clean_build_env\Scripts\activate

REM Step 3: Upgrade pip
python -m pip install --upgrade pip

REM Step 4: Install required dependencies
echo Installing dependencies...
pip install numpy pillow scipy openai python-dotenv speechrecognition pyaudio pyinstaller

REM Step 5: Build the EXE
echo Building the standalone EXE...
pyinstaller --noconfirm --onefile --windowed --name "BAR-Map-Creator.exe" map_creator_app.py

REM Step 6: Move the EXE to project root
if exist dist\BAR-Map-Creator.exe move /Y dist\BAR-Map-Creator.exe .

REM Step 7: Deactivate the virtual environment
deactivate

echo.
echo Build complete! Your EXE is ready in the project folder.
pause
