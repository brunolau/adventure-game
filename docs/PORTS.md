# Ports: macOS, Linux, Android, iOS

Windows stays with `build.bat` (build/windows/). Every other platform is built by `tools/build_ports.py` into
`build/ports/<platform>/` (see the script's docstring for all targets and options). Every Godot process runs under
`tools/godot_lock.py`, because parallel agents share the project folder.

## Status (2026-10-08, version 0.2.0)

| Platform | Built | Tested | Artifact |
|---|---|---|---|
| Linux x86_64 | yes | 0.2.0: start without a screen in an Ubuntu 24.04 container (`--headless --quit-after 900`): exit 0, no error line, user folder `~/.local/share/LastBell` created. Nobody has played it on a Linux desktop | `PoslednyZvonec-0.2.0-linux-x86_64.tar.gz`, 362.2 MB |
| macOS (universal: Apple Silicon + Intel) | yes | `build_ports.py verify` only (no Mac here): bundle structure, Info.plist (eu.inviton.lastbell, 0.2.0), x86_64 + arm64 executable and .NET runtime, ad-hoc signature, icon, PCK | `PoslednyZvonec-0.2.0-macos.zip`, 429.6 MB |
| Linux arm64 | preset only | — | — |
| Android | presets (APK, AAB, x86_64 QA APK), mobile texture staging in the script | not built yet | — |
| iOS | preset | not possible on Windows | — |

## Running the desktop ports

- **Linux:** unpack, then `./LastBell.x86_64`. Needs a 64-bit glibc distribution with Vulkan or OpenGL 3.3 drivers.
  The build uses invariant globalisation, so no libicu is needed.
- **macOS:** unzip and move *Posledný zvonec.app* to Applications. The app is not notarised, so the first start needs
  right-click → **Open** → **Open** (or System Settings → Privacy & Security → **Open Anyway**). If macOS says the app
  is damaged, run `xattr -cr "/Applications/Posledný zvonec.app"` once.

## Still to do

1. **Touch controls** (Android, iOS): tap = walk/use, long-press = look, an on-screen button for the hotspot markers
   (the hold-Space equivalent), finger-sized inventory and map buttons, double-tap = skip walking, safe area, other
   aspect ratios, pause and autosave when the app goes to the background.
2. **Android build:** JDK 17 and the Android SDK into `.tools/`, local keystores (`build_ports.py keystores`, kept out
   of git), the mobile texture set (Basis Universal: about 4 times less GPU memory for the actor sheets and
   backgrounds, ISSUES BUILD-06), APK for GitHub. Google Play would need asset packs (the PCK is about 290 MB, the
   Play base limit is 150 MB).
3. **iOS:** C# on iOS is compiled ahead of time, which needs a Mac with Xcode. Needed from the owner: a Mac with Xcode,
   and the Apple Developer Program (USD 99 per year) for TestFlight / App Store or for installing on a device for
   longer than 7 days. A free Apple ID can install a build on your own device for 7 days.
4. **macOS notarisation** (no Gatekeeper warning) also needs the Apple Developer Program.
