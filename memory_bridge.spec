# memory_bridge.spec
# PyInstaller spec file for Memory Bridge
# Run with:  pyinstaller memory_bridge.spec

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# ── Collect customtkinter themes & assets (required) ─────────────────────────
ctk_datas = collect_data_files("customtkinter", include_py_files=True)
tkcal_datas = collect_data_files("tkcalendar", include_py_files=True)
babel_datas = collect_data_files("babel", include_py_files=True)

# ── Hidden imports needed at runtime ─────────────────────────────────────────
hidden = (
    collect_submodules("customtkinter")
    + collect_submodules("tkcalendar")
    + collect_submodules("babel")
    + [
        "pyttsx3.drivers",
        "pyttsx3.drivers.sapi5",   # Windows TTS driver
        "plyer.platforms.win.notification",
        "sqlite3",
        "PIL._tkinter_finder",
    ]
)

a = Analysis(
    ["main.py"],
    pathex=["."],
    binaries=[],
    datas=ctk_datas + tkcal_datas + babel_datas + [
        ("pages",  "pages"),   # all page modules
        ("assets", "assets"),  # family photos, item photos
        ("theme.py",    "."),
        ("widgets.py",  "."),
        ("database.py", "."),
        ("services.py", "."),
    ],
    hiddenimports=hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["matplotlib", "numpy", "scipy", "pandas"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="MemoryBridge",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # no black console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,              # add "assets/icon.ico" here if you have one
)
