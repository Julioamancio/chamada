@echo off
REM Build Windows executable with PyInstaller (one-folder)
set NAME=ChamadaEscolar

py -3 -m pip install --upgrade pip
py -3 -m pip install -r requirements.txt pyinstaller

REM Include the webapp package templates/static automatically
py -3 -m PyInstaller ^
  --noconfirm ^
  --name %NAME% ^
  --windowed ^
  --add-data "webapp;webapp" ^
  run_server.py

echo.
echo Build finalizado. Execute dist\%NAME%\%NAME%.exe
echo Para criar instalador, use Inno Setup ou WiX com a pasta dist\%NAME%.
