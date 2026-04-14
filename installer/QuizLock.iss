#ifndef MyAppVersion
  #define MyAppVersion "1.0.0"
#endif

[Setup]
AppId={{F8F966B8-3D39-41D8-99A9-671AE0A47A34}
AppName=QuizLock
AppVersion={#MyAppVersion}
AppPublisher=QuizLock Team
DefaultDirName={autopf}\QuizLock
DefaultGroupName=QuizLock
LicenseFile=..\LICENSE
InfoBeforeFile=DISCLAIMER.txt
DisableDirPage=no
DisableProgramGroupPage=yes
OutputDir=..\dist
OutputBaseFilename=QuizLock-Setup-{#MyAppVersion}
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional icons:"; Flags: unchecked

[Files]
Source: "..\dist\QuizLock.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\QuizLock"; Filename: "{app}\QuizLock.exe"
Name: "{autodesktop}\QuizLock"; Filename: "{app}\QuizLock.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\QuizLock.exe"; Description: "Launch QuizLock"; Flags: nowait postinstall skipifsilent
