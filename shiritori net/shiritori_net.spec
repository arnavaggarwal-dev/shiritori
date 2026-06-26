# -*- mode: python ; coding: utf-8 -*-
import sys
import importlib.util

_icon = ['favicon.ico'] if sys.platform == 'win32' else []
_ctk_path = importlib.util.find_spec('customtkinter').submodule_search_locations[0]

a = Analysis(
    ['shiritori_net.py'],
    pathex=[],
    binaries=[],
    datas=[('words_dictionary.json', '.'), (_ctk_path, 'customtkinter')],
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
    name='shiritori_net',
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
    icon=_icon,
)
