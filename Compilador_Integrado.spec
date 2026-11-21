# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

project = Path(SPECPATH)
flex_binary = project / 'flex' / 'mini_lexer.exe'

a = Analysis(
    [str(project / 'main.py')],
    pathex=[str(project)],
    binaries=[(str(flex_binary), 'flex')] if flex_binary.is_file() else [],
    datas=[(str(project / 'ejemplos' / '*.java'), 'ejemplos')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Compilador_Integrado',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
