; Inno Setup script for 중국어 메일 번역 & 단어장
; 빌드: iscc build\installer.iss  (사전에 pyinstaller 빌드 필요)

#define MyAppName "중국어 메일 번역 & 단어장"
#define MyAppVersion "1.0"
#define MyAppPublisher "ccambin"
#define MyAppExeName "ChineseMailVocab.exe"

[Setup]
AppId={{B7E8F3A2-4C61-4E9D-9B1A-CMVOCAB10001}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\ChineseMailVocab
DefaultGroupName={#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2
SolidCompression=yes
OutputDir=..\Output
OutputBaseFilename=ChineseMailVocabSetup
ArchitecturesInstallIn64BitMode=x64compatible
DisableProgramGroupPage=yes
PrivilegesRequired=lowest

[Languages]
Name: "korean"; MessagesFile: "compiler:Languages\Korean.isl"

[Tasks]
Name: "desktopicon"; Description: "바탕화면에 바로가기 만들기"; GroupDescription: "추가 아이콘:"

[Files]
Source: "..\dist\ChineseMailVocab\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "지금 실행하기"; Flags: nowait postinstall skipifsilent
