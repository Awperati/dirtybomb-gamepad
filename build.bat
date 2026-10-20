@echo off
rem Builds dist\DirtyBombGamepad.exe (one file, no console). Needs Python 3.10+.
cd /d "%~dp0"
if not exist .venv py -3.10 -m venv .venv
.venv\Scripts\python.exe -m pip install -q --disable-pip-version-check pysdl2 pysdl2-dll pyinstaller
.venv\Scripts\python.exe -m unittest discover -s tests -t . || exit /b 1
.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --onefile --windowed --name DirtyBombGamepad ^
  --icon icon.ico --add-data "icon.ico;." --collect-all sdl2dll main.py
