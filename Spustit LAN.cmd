@echo off
setlocal
cd /d "%~dp0"
if exist "..\..\work\venv\Scripts\python.exe" (
  "..\..\work\venv\Scripts\python.exe" -m lan.server --state "..\..\work\live" --open
) else (
  if not exist ".venv\Scripts\python.exe" py -3 -m venv .venv
  if not exist ".venv\Scripts\python.exe" goto fail
  ".venv\Scripts\python.exe" -m pip install -r requirements.txt
  if errorlevel 1 goto fail
  ".venv\Scripts\python.exe" -m lan.server --open
)
if errorlevel 1 goto fail
exit /b
:fail
echo Spusteni selhalo. Zkontrolujte Python a cislo portu podle README.
pause
