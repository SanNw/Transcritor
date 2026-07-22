; Script do Inno Setup para gerar o instalador Windows (.exe) do Transcritor.
;
; Pré-requisito: o binário backend\dist\transcritor.exe já compilado via
; PyInstaller (veja packaging/windows/build-windows.ps1).
;
; Para compilar este instalador:
;   1. Instale o Inno Setup (https://jrsoftware.org/isinfo.php)
;   2. Abra este arquivo no Inno Setup Compiler e clique em "Compile",
;      ou rode: ISCC.exe packaging\windows\transcritor.iss

#define MyAppName "Transcritor"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Transcritor"
#define MyAppExeName "transcritor.exe"

[Setup]
AppId={{B7B3B6C0-7A3E-4B7E-9C6E-3B6B7C1A6F2A}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=..\..\dist-packages
OutputBaseFilename=Transcritor-{#MyAppVersion}-setup
SetupIconFile=..\icons\transcritor.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#MyAppExeName}
InfoBeforeFile=before-install.txt

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\..\backend\dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent
