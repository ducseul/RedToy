@echo off
setlocal

REM Remove 'dist' folder if it exists
if exist dist rmdir /s /q dist

REM Remove 'output' folder if it exists
if exist output rmdir /s /q output

REM Compile Python script with Nuitka
python -m nuitka --standalone --onefile ^
    --enable-plugin=pyqt5 ^
    --output-dir=dist ^
    --windows-icon-from-ico=icon.ico ^
    --windows-console-mode=disable ^
    --company-name="Ducseul" ^
    --product-name="RedToy" ^
    --file-version=1.0.0 ^
    --product-version=1.0.0 ^
    --copyright="© 2025 DucseulInc. All rights reserved." ^
    --file-description="Redmine Toy (RedToy)" ^
    ./main.py

if not exist output mkdir output

REM Copy compiled executable
echo F | xcopy dist\main.exe output\RedToy.exe /Y

echo F | xcopy icon.ico output\icon.ico /Y

endlocal