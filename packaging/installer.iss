[Setup]
AppId={{1C730836-E178-4B74-94E8-70C82E320C41}
AppName=Logi Z407 Control Pro
AppVersion=0.1.0
AppPublisher=Logi Z407 Control Pro contributors
DefaultDirName={localappdata}\Programs\LogiZ407ControlPro
DefaultGroupName=Logi Z407 Control Pro
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\dist\installer
OutputBaseFilename=LogiZ407ControlPro-Setup
SetupIconFile=..\assets\app.ico
UninstallDisplayIcon={app}\LogiZ407ControlPro.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; Flags: unchecked
Name: "startup"; Description: "Start with Windows"; Flags: unchecked

[Files]
Source: "..\dist\LogiZ407ControlPro\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\README.md"; DestDir: "{app}"
Source: "..\docs\*"; DestDir: "{app}\docs"; Flags: recursesubdirs
Source: "..\THIRD_PARTY_NOTICES.md"; DestDir: "{app}"

[Icons]
Name: "{group}\Logi Z407 Control Pro"; Filename: "{app}\LogiZ407ControlPro.exe"
Name: "{autodesktop}\Logi Z407 Control Pro"; Filename: "{app}\LogiZ407ControlPro.exe"; Tasks: desktopicon
Name: "{userstartup}\Logi Z407 Control Pro"; Filename: "{app}\LogiZ407ControlPro.exe"; Tasks: startup

[Run]
Filename: "{app}\LogiZ407ControlPro.exe"; Description: "Launch Logi Z407 Control Pro"; Flags: nowait postinstall skipifsilent
