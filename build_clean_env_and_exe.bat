@echo off
REM === BAR Map Creator: Clean Build Script ===
REM This script creates a clean virtual environment, installs only required dependencies,
REM and builds a standalone EXE using PyInstaller (no Qt bindings).

REM Step 1: Create virtual environment
python -m venv clean_build_env

REM Step 2: Activate virtual environment
call clean_build_env\Scripts\activate

REM Step 3: Upgrade pip
python -m pip install --upgrade pip

REM Step 4: Install only required dependencies
pip install numpy pillow scipy openai python-dotenv speechrecognition pyaudio pyinstaller

REM Step 5: Build the EXE
pyinstaller --noconfirm --onefile --windowed --name "BAR-Map-Creator.exe" map_creator_app.py

REM Step 6: Copy the EXE to project root
if exist dist\BAR-Map-Creator.exe move /Y dist\BAR-Map-Creator.exe .

REM Step 7: Deactivate virtual environment
deactivate

echo.
echo Build complete! Your EXE is ready in the project folder.
pause
