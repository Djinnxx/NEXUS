@echo off
echo =============================================
echo   NEXUS OSINT - Build EXE
echo =============================================
echo.
echo Installing PyInstaller...
pip install pyinstaller
echo.
echo Building executable...
pyinstaller --onefile --windowed ^
    --name "NEXUS_OSINT" ^
    --add-data "config;config" ^
    --hidden-import "PyQt6.sip" ^
    --hidden-import "dns.resolver" ^
    --hidden-import "dns.rdatatype" ^
    main.py
echo.
echo Build complete! Check the /dist folder.
pause
