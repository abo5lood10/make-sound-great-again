; Inno Setup script: ملف تثبيت لويندوز (بدون صلاحيات مدير، يثبّت في مجلد المستخدم)
#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif
#define AppName "Make Sound Great Again"
#define AppExe "Make Sound Great Again.exe"

[Setup]
AppId={{6E0B2F57-3A55-4E0A-9B76-5D2C3A8B9C41}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=abo5lood10
DefaultDirName={localappdata}\Programs\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=..\out
OutputBaseFilename=Make-Sound-Great-Again-Setup
SetupIconFile=..\assets\icon.ico
UninstallDisplayIcon={app}\{#AppExe}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallMode=x64compatible
CloseApplications=yes

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Shortcuts:"

[Files]
Source: "..\dist\Make Sound Great Again\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExe}"; Description: "Launch {#AppName}"; Flags: nowait postinstall skipifsilent
