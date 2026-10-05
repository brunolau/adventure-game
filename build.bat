@echo off
rem Posledny zvonec (LastBell): export the Windows build to build\windows\ (see docs\BUILD.md).
rem   build.bat            release export (LastBell.exe + LastBell.pck + data_LastBell_windows_x86_64\)
rem   build.bat debug      debug export (prints errors to LastBell.console.exe)
rem Needs: Godot 4.7.2 .NET in .tools\godot\, .NET SDK 8+, export templates 4.7.2.stable.mono in
rem %APPDATA%\Godot\export_templates\ (or GODOT_TEMPLATES pointing to an unpacked templates folder).
setlocal
set "ROOT=%~dp0"
set "GODOT_DIR=%ROOT%.tools\godot\Godot_v4.7.2-stable_mono_win64"
set "GODOT_CONSOLE=%GODOT_DIR%\Godot_v4.7.2-stable_mono_win64_console.exe"
set "PROJECT=%ROOT%src\game"
set "OUT=%ROOT%build\windows"
set "MODE=--export-release"
if /i "%~1"=="debug" set "MODE=--export-debug"

if not exist "%GODOT_CONSOLE%" (
  echo Godot 4.7.2 .NET was not found at:
  echo   %GODOT_CONSOLE%
  echo Download Godot_v4.7.2-stable_mono_win64.zip from godotengine.org and unpack it to .tools\godot\
  exit /b 1
)
where dotnet >nul 2>nul
if errorlevel 1 (
  echo The .NET SDK 8 or newer is required: https://dotnet.microsoft.com/download
  exit /b 1
)
set "TEMPLATES=%APPDATA%\Godot\export_templates\4.7.2.stable.mono"
if defined GODOT_TEMPLATES set "TEMPLATES=%GODOT_TEMPLATES%"
if not exist "%TEMPLATES%\windows_release_x86_64.exe" (
  echo Export templates 4.7.2.stable.mono not found in:
  echo   %TEMPLATES%
  echo Download Godot_v4.7.2-stable_mono_export_templates.tpz from
  echo   https://github.com/godotengine/godot/releases/tag/4.7.2-stable
  echo and unpack its templates\ folder to %APPDATA%\Godot\export_templates\4.7.2.stable.mono\  ^(docs\BUILD.md^)
  exit /b 1
)
if defined GODOT_TEMPLATES if /i not "%TEMPLATES%"=="%APPDATA%\Godot\export_templates\4.7.2.stable.mono" (
  if not exist "%APPDATA%\Godot\export_templates\4.7.2.stable.mono\windows_release_x86_64.exe" (
    echo Linking the templates folder into %APPDATA%\Godot\export_templates\4.7.2.stable.mono
    if not exist "%APPDATA%\Godot\export_templates" mkdir "%APPDATA%\Godot\export_templates"
    mklink /J "%APPDATA%\Godot\export_templates\4.7.2.stable.mono" "%TEMPLATES%" >nul
  )
)

echo Building the game code...
dotnet build "%PROJECT%\LastBell.csproj" -c Debug -nologo -v q
if errorlevel 1 (
  echo C# build failed.
  exit /b 1
)

echo Importing assets...
"%GODOT_CONSOLE%" --headless --path "%PROJECT%" --import
if errorlevel 1 (
  echo Import failed.
  exit /b 1
)

if exist "%OUT%" rmdir /s /q "%OUT%"
mkdir "%OUT%"
echo Exporting "Windows Desktop" (%MODE%) to %OUT% ...
"%GODOT_CONSOLE%" --headless --path "%PROJECT%" %MODE% "Windows Desktop" "%OUT%\LastBell.exe"
if errorlevel 1 (
  echo Export failed.
  exit /b 1
)
if not exist "%OUT%\LastBell.exe" (
  echo Export produced no LastBell.exe.
  exit /b 1
)
echo.
echo Done: %OUT%\LastBell.exe
endlocal
