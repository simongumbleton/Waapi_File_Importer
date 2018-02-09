# -*- mode: python -*-

block_cipher = None


a = Analysis(['ImportNewAudioFilesAsDialogue_VR2.py'],
             pathex=['E:\\Fdrive_Backup_5thNov\\LocalWork\\Projects\\Wwise WAAPI\\Waapi_File_Importer\\wwise-pubsub-wamp'],
             binaries=[],
             datas=[],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='ImportNewAudioFilesAsDialogue_VR2',
          debug=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=True )
