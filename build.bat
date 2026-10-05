@echo off
rem Posledny zvonec (LastBell): export the Windows build (see docs\BUILD.md).
rem   build.bat            release export to build\windows\ (LastBell.exe + LastBell.pck + data_LastBell_windows_x86_64\);
rem                        without the template paintings and QA data; QA harness options are ignored (ISSUES BUILD-03)
rem   build.bat debug      QA export to build\windows_debug\ (preset "Windows Desktop (QA)": everything, harness on,
rem                        plus LastBell.console.exe that prints the log)
rem Needs: Godot 4.7.2 .NET in .tools\godot\, .NET SDK 8+, Python 3, export templates 4.7.2.stable.mono in
rem %APPDATA%\Godot\export_templates\ (or GODOT_TEMPLATES pointing to an unpacked templates folder).
setlocal
set "ROOT=%~dp0"
set "GODOT_DIR=%ROOT%.tools\godot\Godot_v4.7.2-stable_mono_win64"
set "GODOT_CONSOLE=%GODOT_DIR%\Godot_v4.7.2-stable_mono_win64_console.exe"
set "PROJECT=%ROOT%src\game"
set "OUT=%ROOT%build\windows"
set "MODE=--export-release"
set "PRESET=Windows Desktop"
set "TAG=release"
if /i "%~1"=="debug" (
  set "MODE=--export-debug"
  set "PRESET=Windows Desktop (QA)"
  set "OUT=%ROOT%build\windows_debug"
  set "TAG=debug"
)

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
where python >nul 2>nul
if errorlevel 1 (
  echo Python 3 is required for tools\release_assets.py: https://www.python.org/downloads/
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

echo Applying the texture import policy and checking the release filters...
set "PYTHONIOENCODING=utf-8"
python -X utf8 "%ROOT%tools\release_assets.py" imports
if errorlevel 1 (
  echo tools\release_assets.py imports failed.
  exit /b 1
)
python -X utf8 "%ROOT%tools\release_assets.py" filter --check
if errorlevel 1 (
  echo The release export filters are out of date or exclude a file the game uses.
  echo Run: python tools\release_assets.py filter
  exit /b 1
)

echo Importing assets...
"%GODOT_CONSOLE%" --headless --path "%PROJECT%" --import
if errorlevel 1 (
  echo Import failed.
  exit /b 1
)

tasklist /fi "imagename eq LastBell.exe" 2>nul | find /i "LastBell.exe" >nul
if not errorlevel 1 echo Warning: LastBell.exe is running. Its locked files stay behind in %OUT% ^(close the game first^).
if exist "%OUT%" rmdir /s /q "%OUT%"
if not exist "%OUT%" mkdir "%OUT%"
echo Exporting "%PRESET%" (%MODE%) to %OUT% ...
"%GODOT_CONSOLE%" --headless --path "%PROJECT%" %MODE% "%PRESET%" "%OUT%\LastBell.exe"
if errorlevel 1 (
  echo Export failed.
  exit /b 1
)
if not exist "%OUT%\LastBell.exe" (
  echo Export produced no LastBell.exe.
  exit /b 1
)
rem The exe must differ from the raw template: Godot writes the icon and version info into it afterwards. That step
rem sometimes fails with ERR_CANT_OPEN on a freshly copied exe (seen when the folder was just emptied); once more helps.
set "KIND=release"
if /i "%TAG%"=="debug" set "KIND=debug"
for %%F in ("%TEMPLATES%\windows_%KIND%_x86_64.exe") do set "TPL_SIZE=%%~zF"
for %%F in ("%OUT%\LastBell.exe") do set "EXE_SIZE=%%~zF"
if "%EXE_SIZE%"=="%TPL_SIZE%" (
  echo The icon/version step did not apply; exporting once more...
  "%GODOT_CONSOLE%" --headless --path "%PROJECT%" %MODE% "%PRESET%" "%OUT%\LastBell.exe"
)
for %%F in ("%OUT%\LastBell.exe") do set "EXE_SIZE=%%~zF"
if "%EXE_SIZE%"=="%TPL_SIZE%" (
  echo Export failed: LastBell.exe has no icon/version info ^(template_modifier^).
  exit /b 1
)
python -X utf8 "%ROOT%tools\release_assets.py" pck "%OUT%\LastBell.pck" > "%ROOT%build\pck_contents_%TAG%.txt"
for %%F in ("%OUT%\LastBell.pck") do echo PCK: %%~zF bytes, contents by folder in build\pck_contents_%TAG%.txt
echo.
echo Done: %OUT%\LastBell.exe
endlocal
