# -*- mode: python ; coding: utf-8 -*-
import os, sys
block_cipher = None

dir_path = os.getcwd()
if sys.platform == 'darwin' or sys.platform == 'linux':
    ffprobe_location = 'ffprobe'
else:
    ffprobe_location = 'ffprobe.exe'

a = Analysis(['main.py'],
             pathex=[dir_path],
             binaries=[(ffprobe_location, '.')],
             datas=[],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

a.datas += [('./images/info_black.png', './images/info_black.png', 'DATA'), ('./images/GTD_icon.png', './images/GTD_icon.png', 'DATA')]
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

if sys.platform == 'darwin':
    exe = EXE(pyz,
            a.scripts,
            [],
            exclude_binaries=True,
            name='Total Duration',
            debug=False,
            bootloader_ignore_signals=False,
            strip=False,
            upx=True,
            console=False )
    coll = COLLECT(exe,
                a.binaries,
                a.zipfiles,
                a.datas,
                strip=False,
                upx=True,
                upx_exclude=[],
                name='Total Duration')
    app = BUNDLE(coll,
                name='Total Duration.app',
                icon='images/GTD_icon.icns',
                bundle_identifier=None,
                info_plist={
                    'NSHighResolutionCapable' : 'True'
                    }
                )

if sys.platform == 'win32' or sys.platform == 'win64' or sys.platform == 'linux':
    exe = EXE(pyz,
            a.scripts,
            a.binaries,
            a.zipfiles,
            a.datas,
            [],
            name='Total Duration',
            debug=False,
            bootloader_ignore_signals=False,
            strip=False,
            upx=True,
            upx_exclude=[],
            runtime_tmpdir=None,
            console=False,
            icon='images/GTD_icon.png')

            #TODO I changed icon to .png for linux. Is this OK for windows?