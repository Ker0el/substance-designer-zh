; 星空汉化 · Substance 3D Designer 中文插件 安装脚本
; 构建：先运行根目录 build.bat 生成 dist\xingkong_zh，再运行本目录 build.bat
; 直接编译：ISCC.exe build.iss（可用 ISCC 环境变量指定编译器路径）
#define MyAppName "星空汉化 · SD 中文插件"
#define MyAppVersion "0.1.2"
#define MyPublisher "星空汉化"
#define MyUrl "https://space.bilibili.com/177308205"
#define SrcDir AddBackslash(SourcePath) + "..\dist\xingkong_zh"
#define ProjectDir AddBackslash(SourcePath) + ".."
#define PluginDirName "xingkong_zh"

[Setup]
AppId={{A24CD4F8-E3D9-428B-9C94-AE0EEFB29DBD}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyPublisher}
AppPublisherURL={#MyUrl}
AppSupportURL={#MyUrl}
AppUpdatesURL={#MyUrl}
VersionInfoVersion=0.1.2.0
VersionInfoCompany={#MyPublisher}
VersionInfoDescription={#MyAppName}
VersionInfoProductName={#MyAppName}
VersionInfoProductVersion=0.1.2.0
DefaultDirName={userdocs}\Adobe\Adobe Substance 3D Designer\python\sduserplugins\{#PluginDirName}
; 用户浏览选择目录时，不要把 DefaultDirName 的最后一段拼上去
AppendDefaultDirName=no
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
DisableDirPage=no
AlwaysShowDirOnReadyPage=yes
DirExistsWarning=no
DisableWelcomePage=yes
UsePreviousAppDir=no
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
InfoBeforeFile={#ProjectDir}\installer\安装说明.txt
OutputDir={#ProjectDir}\dist
OutputBaseFilename=星空汉化_SD插件_v{#MyAppVersion}_安装包
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern dynamic
CloseApplications=no
RestartApplications=no
UninstallDisplayName={#MyAppName}
Uninstallable=yes
CreateUninstallRegKey=yes
AllowNoIcons=yes
ShowLanguageDialog=no
SetupLogging=yes

[Languages]
; 自定义中文文案，不用 Inno 自带语言文件
Name: "chinesesimplified"; MessagesFile: "Chinese_Star.isl"

[Files]
; 插件本体：Python 入口、原生引擎、词库、说明
Source: "{#SrcDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[InstallDelete]
; 清掉旧版本生成的 Python 缓存，避免加载到过期字节码
Type: filesandordirs; Name: "{app}\__pycache__"
Type: filesandordirs; Name: "{app}\xingkong_zh\__pycache__"

[UninstallDelete]
; 只清理本插件运行时生成的缓存；其他用户文件不动
Type: filesandordirs; Name: "{app}\__pycache__"
Type: filesandordirs; Name: "{app}\xingkong_zh\__pycache__"

[Run]
Filename: "{app}"; Description: "打开插件目录"; Flags: postinstall shellexec nowait skipifsilent unchecked

[Code]
var
  DesignerFound: Boolean;

const
  PluginDll = 'native\xingkong_zh_qt6.dll';

function IsFileLocked(const FileName: String): Boolean;
var
  Stream: TFileStream;
begin
  Result := False;
  if not FileExists(FileName) then
    Exit;
  try
    Stream := TFileStream.Create(FileName, fmOpenReadWrite or fmShareExclusive);
    Stream.Free;
  except
    Result := True;
  end;
end;

function ScanUninstall(RootKey: Integer; const Base: String): Boolean;
var
  Names: TArrayOfString;
  I: Integer;
  DisplayName: String;
begin
  Result := False;
  if not RegGetSubkeyNames(RootKey, Base, Names) then
    Exit;
  for I := 0 to GetArrayLength(Names) - 1 do
  begin
    if RegQueryStringValue(RootKey, Base + '\' + Names[I], 'DisplayName', DisplayName) then
    begin
      if (Pos('Substance 3D Designer', DisplayName) > 0) or
         (Pos('Substance Designer', DisplayName) > 0) then
      begin
        Result := True;
        Exit;
      end;
    end;
  end;
end;

function DetectDesigner: Boolean;
var
  Base: String;
begin
  Base := 'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall';
  Result :=
    FileExists(ExpandConstant('{autopf}\Adobe\Adobe Substance 3D Designer\Designer.exe')) or
    ScanUninstall(HKLM, Base) or
    ScanUninstall(HKLM32, Base) or
    ScanUninstall(HKLM64, Base) or
    ScanUninstall(HKCU, Base);
  Log('Substance 3D Designer detected: ' + IntToStr(Ord(Result)));
end;

function IsDesignerLockingPlugin: Boolean;
begin
  Result := IsFileLocked(AddBackslash(WizardDirValue) + PluginDll);
  if Result then
    Log('Plugin DLL is locked (Designer is probably running): ' + WizardDirValue);
end;

function InitializeSetup: Boolean;
begin
  Result := True;
  DesignerFound := DetectDesigner;
end;

function NextButtonClick(CurPageID: Integer): Boolean;
var
  Msg: String;
begin
  Result := True;

  if CurPageID = wpSelectDir then
  begin
    if WizardSilent then
      Exit;

    if not DesignerFound then
    begin
      Msg := '没有检测到 Substance 3D Designer。' + #13#10#13#10 +
             '如果 Designer 是便携版或安装在非默认位置，可以继续安装；' +
             '否则请先安装 Designer。' + #13#10#13#10 +
             '仍要继续吗？';
      if MsgBox(Msg, mbConfirmation, MB_YESNO) = IDNO then
      begin
        Result := False;
        Exit;
      end;
    end;

    if CompareText(ExtractFileName(WizardDirValue), '{#PluginDirName}') <> 0 then
    begin
      Msg := '安装目录必须以 {#PluginDirName} 结尾。' + #13#10#13#10 +
             '请使用默认目录：' + #13#10 +
             ExpandConstant('{userdocs}\Adobe\Adobe Substance 3D Designer\python\sduserplugins\{#PluginDirName}');
      MsgBox(Msg, mbError, MB_OK);
      Result := False;
      Exit;
    end;

    if IsDesignerLockingPlugin then
    begin
      Msg := 'Substance 3D Designer 正在运行，插件文件被占用。' + #13#10#13#10 +
             '请先完全退出 Designer，再点击下一步。';
      MsgBox(Msg, mbError, MB_OK);
      Result := False;
    end;
  end
  else if CurPageID = wpReady then
  begin
    if not WizardSilent and IsDesignerLockingPlugin then
    begin
      Msg := 'Substance 3D Designer 正在运行，插件文件被占用。' + #13#10#13#10 +
             '请先完全退出 Designer，再点击安装。';
      MsgBox(Msg, mbError, MB_OK);
      Result := False;
    end;
  end;
end;

procedure CancelButtonClick(CurPageID: Integer; var Cancel, Confirm: Boolean);
begin
  { 安装开始前点取消/关闭窗口直接退出，不再弹一次“确定退出吗” }
  if CurPageID < wpInstalling then
    Confirm := False;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssInstall then
    Log('Installing xingkong_zh to: ' + ExpandConstant('{app}'));
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usPostUninstall then
    Log('xingkong_zh uninstalled; Designer itself was not modified.');
end;
