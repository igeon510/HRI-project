# -*- mode: python ; coding: utf-8 -*-

import os 

a = Analysis(
    ['pakapaka_type1.py'],
    pathex=[os.getcwd()],
    binaries=[],
    datas=[('pose_landmarker_lite.task','.'),
            ('sound','sound')],
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
    [],
    exclude_binaries=True,
    name='PakapakaType1',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='PakapakaType1',
)
app = BUNDLE(
    coll,
    name='PakapakaType1.app',
    bundle_identifier='com.igeon.pakapaka',
    info_plist={
        'CFBundleExecutable': 'PakapakaType1',
        'CFBundleDisplayName': 'PakapakaType1',
        'NSCameraUsageDescription': 'Camera access is required for posture detection.',
    }
)
