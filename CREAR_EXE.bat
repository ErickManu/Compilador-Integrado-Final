@echo off
setlocal
cd /d "%~dp0"
set "PYTHON=py -3"
py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
if errorlevel 1 (
    set "PYTHON=python"
    python -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
    if errorlevel 1 goto missing_python
)
%PYTHON% -m PyInstaller --version >nul 2>&1
if errorlevel 1 goto missing_pyinstaller
echo Ejecutando pruebas...
%PYTHON% -m unittest discover -s tests -v
if errorlevel 1 goto failed
echo Creando ejecutable Windows...
%PYTHON% -m PyInstaller --noconfirm Compilador_Integrado.spec
if errorlevel 1 goto failed
echo Verificando el ejecutable y sus recursos...
powershell -NoProfile -Command "$p = Start-Process -FilePath (Join-Path $PWD 'dist\Compilador_Integrado.exe') -ArgumentList '--self-test --report build\smoke-exe.json' -WindowStyle Hidden -PassThru; if (-not $p.WaitForExit(60000)) { $p.Kill(); exit 1 }; exit $p.ExitCode"
if errorlevel 1 goto failed
%PYTHON% -c "import json; from pathlib import Path; r=json.loads(Path('build/smoke-exe.json').read_text(encoding='utf-8')); print(json.dumps(r, ensure_ascii=True, indent=2)); raise SystemExit(0 if r['ok'] and r['frozen'] else 1)"
if errorlevel 1 goto failed
echo Listo: dist\Compilador_Integrado.exe
exit /b 0
:missing_python
echo ERROR: se necesita Python 3.10 o posterior con Tkinter.
exit /b 1
:missing_pyinstaller
echo ERROR: falta PyInstaller en el Python seleccionado.
echo Instala con: %PYTHON% -m pip install pyinstaller
exit /b 1
:failed
echo ERROR: no se pudo completar la creacion o verificacion. Revisa la salida anterior.
exit /b 1
