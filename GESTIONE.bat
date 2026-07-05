@echo off
cd /d "%~dp0"
color 0D
title GESTIONE COLF

echo.
echo  ==========================================
echo     GESTIONE COLF v2.0
echo     Gestione Collaboratori Familiari
echo  ==========================================
echo.

color 0B
:: --- Ambiente ---
echo [AMBIENTE]
py -3.14 --version >nul 2>&1
if errorlevel 1 (
    echo [..] Python 3.14 non trovato. Download in corso...
    curl -sL -o "%TEMP%\python-3.14.6-amd64.exe" "https://www.python.org/ftp/python/3.14.6/python-3.14.6-amd64.exe"
    if errorlevel 1 (
        echo [ERR] Download Python fallito.
        echo       Scarica manualmente da: https://www.python.org/downloads/release/python-3146/
        pause
        exit /b
    )
    echo [..] Installazione Python 3.14...
    start /wait "" "%TEMP%\python-3.14.6-amd64.exe" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0 Include_doc=0 Include_debug=0 Include_symbols=0 Include_tools=0
    if errorlevel 1 (
        echo [ERR] Installazione Python fallita.
        pause
        exit /b
    )
    del "%TEMP%\python-3.14.6-amd64.exe"
    echo [..] Verifica nuova installazione...
    py -3.14 --version >nul 2>&1
    if errorlevel 1 (
        echo [ERR] Python 3.14 installato ma non rilevato dal launcher.
        echo       Riavvia il terminale.
        pause
        exit /b
    )
)
for /f "tokens=*" %%i in ('py -3.14 --version 2^>^&1') do set "PY_VER=%%i"
echo  ^|  %PY_VER%
echo.

color 09
:: --- Ambiente virtuale ---
:venv
if not exist ".venv\Scripts\python.exe" goto venv_recreate
echo [..] Verifica ambiente virtuale...
.venv\Scripts\python.exe --version >nul 2>&1
if not errorlevel 1 (
    echo  ^|  Ambiente virtuale pronto
    goto venv_done
)
:venv_recreate
echo [..] Ricreazione ambiente virtuale (obsoleto o danneggiato)...
rd /s /q ".venv" 2>nul
py -3.14 -m venv .venv
if errorlevel 1 (
    echo [ERR] Creazione ambiente virtuale fallita.
    pause
    exit /b
)
echo  ^|  Ambiente virtuale ricreato
:venv_done
echo.

:: --- Pip ---
:pip
echo [..] Aggiornamento pip...
.venv\Scripts\python.exe -m pip install --upgrade pip --quiet
if errorlevel 1 (
    echo [WARN] Aggiornamento pip fallito, continuo...
)
echo  ^|  pip aggiornato
echo.

color 0A
:: --- Dipendenze ---
:deps
echo [..] Installazione dipendenze...
.venv\Scripts\python.exe -m pip install -r requirements.txt --upgrade --quiet
if errorlevel 1 (
    echo [..] Riprovo installazione dipendenze...
    .venv\Scripts\python.exe -m pip install -r requirements.txt --upgrade
    if errorlevel 1 (
        echo [ERR] Installazione dipendenze fallita.
        pause
        exit /b
    )
)
echo  ^|  Dipendenze installate
echo.

color 0B
:: --- Database ---
:migrate
echo [DATABASE]
echo [..] Migrazioni database...
.venv\Scripts\python.exe manage.py migrate --noinput
if errorlevel 1 (
    echo [WARN] Migrazioni fallite, riprovo...
    .venv\Scripts\python.exe manage.py migrate --noinput
    if errorlevel 1 (
        echo [ERR] Migrazioni database fallite.
        pause
        exit /b
    )
)
echo  ^|  Database aggiornato
echo.

color 0C
:: --- Playwright Browser ---
:playwright
echo [PLAYWRIGHT]
echo [..] Verifica browser Playwright...
.venv\Scripts\python.exe -c "import playwright; print('OK')" >nul 2>&1
if not errorlevel 1 (
    echo  ^|  Browser Playwright gia' installato
    goto playwright_done
)
echo [..] Installazione browser Playwright...
.venv\Scripts\python.exe -m playwright install chromium
if errorlevel 1 (
    echo [WARN] Installazione Playwright fallita (riprova manualmente)
    echo        .venv\Scripts\python.exe -m playwright install chromium
) else (
    echo  ^|  Browser Playwright installato
)
:playwright_done
echo.

color 0D
:: --- Desktop shortcut ---
echo [DESKTOP]
set "DESKTOP=%USERPROFILE%\Desktop"
if exist "%USERPROFILE%\OneDrive\Desktop" set "DESKTOP=%USERPROFILE%\OneDrive\Desktop"
set "SHORTCUT=%DESKTOP%\GESTIONE COLF.lnk"
if not exist "%SHORTCUT%" (
    echo [..] Creazione collegamento...
    powershell -NoProfile -Command "$WS=New-Object -ComObject WScript.Shell; $S=$WS.CreateShortcut('%SHORTCUT%'); $S.TargetPath='%~dp0GESTIONE.bat'; $S.IconLocation='%~dp0static\favicon.ico,0'; $S.WindowStyle=7; $S.Save()" >nul
    echo  ^|  Collegamento creato sul desktop
) else (
    echo  ^|  Collegamento gia' presente
)
echo.

color 0E
:: --- Server check ---
echo [SERVER]
tasklist /FI "WINDOWTITLE eq GESTIONE COLF*" /NH 2>nul | findstr /C:"python.exe" >nul 2>&1
if not errorlevel 1 (
    echo  ^|  Server gia' in esecuzione su porta 8000
    echo  ^|  Apro il browser...
    start http://127.0.0.1:8000/dashboard/
    exit /b
)
color 0A
echo [..] Avvio server in corso...
start /min "GESTIONE COLF" .venv\Scripts\python.exe manage.py runserver
timeout /t 3 /nobreak >nul
echo  ^|  Server avviato su http://127.0.0.1:8000/
start http://127.0.0.1:8000/dashboard/
echo.
color 0D
echo  ==========================================
echo     GESTIONE COLF avviata con successo!
echo  ==========================================
echo.
