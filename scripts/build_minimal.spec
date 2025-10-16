# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(['main.py'],
             pathex=['.'],
             binaries=[],
             datas=[],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=['*'],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

# 清空所有依赖，让exe最小化
a.binaries = []
a.datas = []
a.pure = []

pyz = PYZ([], cipher=block_cipher)

exe = EXE(pyz,
          ['main.py'],
          [],
          name='ForumAssist',
          debug=False,
          bootloader_ignore_signals=False,
          strip=True,
          upx=True,
          console=False,
          icon='assets/icon.ico')