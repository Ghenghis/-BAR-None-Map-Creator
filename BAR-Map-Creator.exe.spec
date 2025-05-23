# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['map_creator_app.py'],
    pathex=[],
    binaries=[
        # Example: If PortAudio DLL is named portaudio_x64.dll and is in the project root
        # or a known path that can be added here:
        # ('portaudio_x64.dll', '.') 
        # TODO: Developer needs to locate the correct PortAudio DLL for pyaudio 
        # and add it here, e.g., ('path/to/portaudio_x64.dll', '.')
    ],
    datas=[
        # ('icon.ico', '.'), # TODO: Developer should add if icon.ico exists in project root.
        ('assets/icons', 'assets/icons') # Added for button icons
    ],
    hiddenimports=[
        'speech_recognition.recognizers.google',
        'pydub.utils', # pydub.utils.get_player_name is often needed
        'scipy.special._cdflib',
        'scipy._lib.messagestream', # Common scipy hidden import
        'pkg_resources.py2_warn',
        'python-dotenv', # Explicitly include if not picked up
        'openai', # Ensure base openai is included
        'tkinter.filedialog', # Sometimes needed explicitly
        'tkinter.messagebox',  # Sometimes needed explicitly
        'appdirs', # Added for user-specific log directory
        'ttkthemes', # Added for themed Tk widgets
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tests'], # Added 'tests' directory to excludes
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
    name='BAR-Map-Creator.exe',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False, # Set to True for debugging if needed
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon='icon.ico' # TODO: Uncomment and set if icon.ico is added to datas and exists
)
