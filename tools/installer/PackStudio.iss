[Setup]
AppId={{B77CC148-A711-40FF-A23A-E010019E22D5}
AppName=PackStudio
AppVersion={#ReleaseVersion}
AppPublisher=PackStudio
DefaultDirName={autopf}\PackStudio
DisableWelcomePage=no
DisableDirPage=no
DisableProgramGroupPage=yes
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
WizardStyle=modern dynamic
UninstallDisplayIcon={app}\PackStudio.exe
VersionInfoVersion={#ReleaseVersion}
OutputBaseFilename=PackStudio-Setup-x64
Compression=lzma2
SolidCompression=yes

[Types]
Name: "full"; Description: "Desktop and CLI"
Name: "desktop"; Description: "Desktop only"
Name: "custom"; Description: "Custom installation"; Flags: iscustom

[Components]
Name: "desktop"; Description: "PackStudio Desktop"; Types: full desktop custom; Flags: fixed
Name: "cli"; Description: "PackStudio CLI"; Types: full

[Files]
Source: "{#DesktopPublish}\*"; DestDir: "{app}"; Excludes: "*.pdb"; Components: desktop; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#CliPublish}\*"; DestDir: "{app}\cli"; Excludes: "\runtime_data\*,*.pdb"; Components: cli; Flags: ignoreversion recursesubdirs

[Icons]
Name: "{autoprograms}\PackStudio"; Filename: "{app}\PackStudio.exe"; WorkingDir: "{app}"

[Registry]
Root: HKLM; Subkey: "Software\Microsoft\Windows\CurrentVersion\App Paths\PackStudio.exe"; ValueType: string; ValueData: "{app}\PackStudio.exe"; Flags: uninsdeletekey

[Run]
Filename: "{app}\PackStudio.exe"; Description: "Launch PackStudio"; WorkingDir: "{app}"; Flags: nowait postinstall skipifsilent
