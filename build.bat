@echo off
REM Build Desktop Translator executable using PyInstaller
REM Ensure dependencies are installed: pip install -r requirements.txt pyinstaller

if not exist "icons/translate.ico" (
    echo Warning: icon file icons/translate.ico not found, building without icon.
    pyinstaller --onefile --windowed --name DesktopTranslator main.py
) else (
    pyinstaller --onefile --windowed --icon=icons/translate.ico --name DesktopTranslator main.py
)

echo Build complete. Executable is in dist/DesktopTranslator.exe
pause