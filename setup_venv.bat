@echo off
cd /d "%~dp0"
echo.
echo  ==========================================
echo     SETUP AMBIENTE VIRTUALE
echo  ==========================================
echo.

:: --- Crea virtualenv fuori dal progetto (NAS-safe) ---
if exist "..\.venv_gestione_colf\Scripts\python.exe" (
    echo [OK] Ambiente virtuale gia' presente
    goto :install_deps
)

echo [..] Creazione ambiente virtuale...
py -3.14 -m venv ..\.venv_gestione_colf
if errorlevel 1 (
    echo [ERR] Creazione ambiente virtuale fallita.
    pause
    exit /b 1
)
echo [OK] Ambiente virtuale creato

:install_deps
echo [..] Installazione dipendenze...
..\.venv_gestione_colf\Scripts\python.exe -m pip install --upgrade pip --quiet
..\.venv_gestione_colf\Scripts\python.exe -m pip install -r requirements.txt --upgrade
if errorlevel 1 (
    echo [ERR] Installazione dipendenze fallita.
    pause
    exit /b 1
)
echo [OK] Dipendenze installate
echo.
echo  ==========================================
echo     SETUP COMPLETATO
echo  ==========================================
echo.
pause
