@echo off
rem Posledny zvonec (LastBell): build, import and play the Godot project.
rem Double-click to play. Extra arguments are passed to Godot, e.g.  play.bat -- --room S05
setlocal
set "ROOT=%~dp0"
set "GODOT_DIR=%ROOT%.tools\godot\Godot_v4.7.2-stable_mono_win64"
set "GODOT=%GODOT_DIR%\Godot_v4.7.2-stable_mono_win64.exe"
set "GODOT_CONSOLE=%GODOT_DIR%\Godot_v4.7.2-stable_mono_win64_console.exe"
set "PROJECT=%ROOT%src\game"

if not exist "%GODOT%" (
  echo Godot 4.7.2 .NET was not found at:
  echo   %GODOT%
  echo Download Godot_v4.7.2-stable_mono_win64.zip from godotengine.org and unpack it to .tools\godot\
  pause
  exit /b 1
)
where dotnet >nul 2>nul
if errorlevel 1 (
  echo The .NET SDK 8 or newer is required: https://dotnet.microsoft.com/download
  pause
  exit /b 1
)

echo Building the game code...
dotnet build "%PROJECT%\LastBell.csproj" -c Debug -nologo -v q
if errorlevel 1 (
  echo Build failed.
  pause
  exit /b 1
)

echo Importing assets...
"%GODOT_CONSOLE%" --headless --path "%PROJECT%" --import >nul 2>&1

start "" "%GODOT%" --path "%PROJECT%" %*
endlocal
