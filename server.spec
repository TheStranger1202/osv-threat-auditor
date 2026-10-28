# -*- mode: python ; coding: utf-8 -*-

datas = [
    ('data/osv_ecosystems.json', 'data'),
    ('src/web/templates', 'templates'),
    ('src/web/templates', 'src/web/templates'),
]

a = Analysis(
    ['src/web/app.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'jinja2',
        'werkzeug',
        'requests',
        'urllib3',
        'packaging',
        'packaging.version',
        'packaging.specifiers',
        'charset_normalizer',
    ],
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
    a.zipfiles,
    a.datas,
    [],
    name='OSV_Threat_Auditor_Server',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
