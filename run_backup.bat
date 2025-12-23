@echo off
:: Enable UTF-8 encoding so "automação" works
chcp 65001 >nul

:: Wait 10 seconds FIRST for G: drive to "wake up" / initialize
echo Waiting for G: drive to initialize...
timeout /t 10 /nobreak >nul

:: Simply switch to G: drive
G:

:: Navigate to folder
cd "\Meu Drive\Projetos\automação-backup"

:: Activate the virtual environment
call .venv\Scripts\activate.bat

python3 main.py

:: Error handling (pause if it crashes so you can see why)
if %ERRORLEVEL% NEQ 0 (
    echo Backup failed with error code %ERRORLEVEL%
    pause
)
echo Done.
pause
