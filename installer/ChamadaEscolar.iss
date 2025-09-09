; Inno Setup Script for Chamada Escolar
#define MyAppName "Chamada Escolar"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Sua Escola"
#define MyAppExeName "ChamadaEscolar.exe"

[Setup]
AppId={{FBCBEE11-6A6F-44C4-A96B-CHAMADAESCOLAR}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={pf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir=installer\out
OutputBaseFilename=ChamadaEscolar-Setup
Compression=lzma
SolidCompression=yes
PrivilegesRequired=admin

[Languages]
Name: "portuguese"; MessagesFile: "compiler:Languages\Portuguese.isl"

[Files]
; Copia a pasta gerada pelo PyInstaller (one-folder)
Source: "dist\ChamadaEscolar\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na Área de Trabalho"; GroupDescription: "Atalhos:"; Flags: unchecked

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Iniciar {#MyAppName}"; Flags: nowait postinstall skipifsilent

