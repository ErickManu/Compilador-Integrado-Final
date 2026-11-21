@echo off
cd /d "%~dp0"
py main.py
if errorlevel 1 (
  echo Si no tienes el comando py, prueba: python main.py
  pause
)
