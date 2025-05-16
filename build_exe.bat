@echo off
REM Build BAR Map Creator as a standalone Windows executable using PyInstaller
REM You must have pyinstaller installed: pip install pyinstaller
REM Run this script from the project directory

set MAIN_SCRIPT=map_creator_app.py
set EXENAME=BAR-Map-Creator.exe
set ICON=icon.ico

REM Optional: If you have an icon file, place it in the project folder and uncomment the --icon line

pyinstaller --noconfirm --onefile --windowed --name "%EXENAME%" %MAIN_SCRIPT% 
REM To add an icon, use:
REM pyinstaller --noconfirm --onefile --windowed --icon %ICON% --name "%EXENAME%" %MAIN_SCRIPT%

REM Move the exe to the project root for convenience
if exist dist\%EXENAME% move /Y dist\%EXENAME% .

pause