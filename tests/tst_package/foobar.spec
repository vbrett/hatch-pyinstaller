foo_a = Analysis(
    ['src/tst_package/foo.py'],
    pathex=[],
    binaries=[],
    datas=[('data/Designer.png', '.')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
foo_pyz = PYZ(foo_a.pure)
foo_exe = EXE(
    foo_pyz,
    foo_a.scripts,
    [],
    exclude_binaries=True,
    name='foo',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)


bar_a = Analysis(
    ['src\\tst_package\\bar.py'],
    pathex=[],
    binaries=[],
    datas=[('data/Designer.png', '.')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
bar_pyz = PYZ(bar_a.pure)
bar_exe = EXE(
    bar_pyz,
    bar_a.scripts,
    [],
    exclude_binaries=True,
    name='bar',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    foo_exe,
    foo_a.binaries,
    foo_a.datas,
    bar_exe,
    bar_a.binaries,
    bar_a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='foobar',
)
