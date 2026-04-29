@echo off
setlocal
REM Forward `python` to the repo's virtualenv python for this directory.
REM This lets you run: `python manage.py runserver` without activating venv.

set "VENV_PY=%~dp0.venv\Scripts\python.exe"
if not exist "%VENV_PY%" (
  echo Virtualenv python not found: "%VENV_PY%"
  exit /b 1
)

"%VENV_PY%" %*

