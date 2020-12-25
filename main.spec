# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['main.py'],
             pathex=['/Users/dkanefsk/Desktop/_Python_app/Get_Total_Duration'],
             binaries=[('ffprobe', '.')],
             datas=[],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

a.datas += [('./images/info_black.png', './images/info_black.png', 'DATA'),('./images/info_blue.png', './images/info_blue.png', 'DATA') ]
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
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
