# -*- mode: python -*-

block_cipher = None


a = Analysis(['GSL_GUI.py'],
             pathex=['E:\\Workspace\\PyCharm\\ECMap'],
             binaries=[],
             datas=[],
             hiddenimports=['tkinder'],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
a.datas += [('bg_GUI.png','.\\bg_GUI.png','DATA')]
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='GSL_GUI',
          debug=False,
          strip=False,
          upx=True,
          console=True )
