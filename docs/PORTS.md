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
| Android | yes: release APK (arm64-v8a), Google Play bundle, debug APK (x86_64) | debug APK played on a headless Android 16 emulator: smoke test 10 of 10 (title screen, new game, touch controls, autosave); release APK and bundle checked statically only; **no real device yet** | `PoslednyZvonec-0.2.0.apk`, 584.3 MB; `PoslednyZvonec-0.2.0.aab`, 520.6 MB |
| iOS | preset | not possible on Windows | — |

## Running the desktop ports

- **Linux:** unpack, then `./LastBell.x86_64`. Needs a 64-bit glibc distribution with Vulkan or OpenGL 3.3 drivers.
  The build uses invariant globalisation, so no libicu is needed.
- **macOS:** unzip and move *Posledný zvonec.app* to Applications. The app is not notarised, so the first start needs
  right-click → **Open** → **Open** (or System Settings → Privacy & Security → **Open Anyway**). If macOS says the app
  is damaged, run `xattr -cr "/Applications/Posledný zvonec.app"` once.

## Android (2026-10-08)

Package `eu.inviton.lastbell`, version 0.2.0 (code 2), landscape, immersive (no system bars), no permissions, minimum
Android 7.0 (API 24), target API 36. C# runs on the .NET 9 Mono runtime inside the APK (Godot 4.7.2, experimental).

### Artifacts

| File | What | Size |
|---|---|---|
| `build/ports/PoslednyZvonec-0.2.0.apk` | release APK for sideloading and GitHub: arm64-v8a, signed with the local release key | 584.3 MB |
| `build/ports/PoslednyZvonec-0.2.0.aab` | Google Play bundle (Gradle build), signed with the same key: base module 29 MB, the game data (488 MB) in an install-time asset pack | 520.6 MB |
| `build/ports/android_qa/LastBell-qa-x86_64.apk` | debug APK for the emulator: x86_64, debug key, QA harness arguments honoured | 586.7 MB |

Install the APK on a phone: copy it over and open it (Android asks once to allow installs from that app), or
`adb install -r build/ports/PoslednyZvonec-0.2.0.apk`. The game needs about 1.2 GB free for the install.

### Build

```
python tools/build_ports.py android-qa      debug APK, x86_64 (emulator)
python tools/build_ports.py android         release APK, arm64-v8a
python tools/build_ports.py android-aab     Google Play bundle (first run downloads Gradle 8.11.1 and the Android
                                            Gradle plugin 8.6.1 into .tools/gradle, about 10 minutes)
python tools/build_ports.py texture-report  texture memory of the desktop and the mobile import
```

What the script does for the Android targets:

- **Staging copy.** `build/ports/_stage/src` is a copy of `src/` in which the painted textures (actor sheets,
  backgrounds, cutscenes, ambient cut-outs, foreground masks, variant layers: 668 files) are imported as Basis
  Universal (UASTC level 2, RDO 0.75) instead of Lossy WebP. The first import takes about 6 minutes; later runs only
  import what changed. `src/game` and its imports are never touched. Godot does not notice changed import parameters
  by itself (it trusts its file cache), so the script deletes the stale imported file and its `.md5` when a texture
  of the mobile set is still the desktop import. `--keep-stage` exports the copy as it is (for trying a change there).
- **Toolchain.** JDK and SDK are taken from `.tools/android` first (table below). Godot reads both paths only from its
  editor settings, and every Godot editor process rewrites that file on exit, so the Android exports run with
  `APPDATA=.tools/android/godot_appdata`: a private Godot configuration with `export/android/java_sdk_path`,
  `android_sdk_path` and the debug keystore, plus a directory junction to the installed export templates. The user's
  own Godot editor settings (which point at `C:\Program Files\Java\jdk-17` and `%LOCALAPPDATA%\Android\Sdk`) are not
  changed. The exports also use their own adb server port (5041). The junction
  `.tools/android/godot_appdata/Godot/export_templates/4.7.2.stable.mono` points at the real templates folder in
  `%APPDATA%`: remove it with `rmdir`, never with a recursive delete that follows links.
- **Signing.** `python tools/build_ports.py keystores` creates `.tools/android/lastbell-debug.keystore` and
  `lastbell-release.keystore` once; the generated release password is in `.tools/android/keystore.json`. Both stay
  out of git (`.tools/` is ignored). **Keep a copy of the release keystore and of keystore.json somewhere safe:** an
  app on Google Play can only be updated with the same key (or after an upload-key reset by Google). The passwords
  reach Godot and keytool through environment variables, never through a command line or `export_presets.cfg`.
- **Locks and build servers.** Godot runs on the staging copy use `build/locks/godot_stage.lock`, not the agents'
  lock of `src/game`, and run at below-normal priority. The C# build of an export uses no compiler server, no MSBuild
  node reuse and no Gradle daemon: Godot's console wrapper waits for every child process, and those servers stay
  alive for 10 minutes to 3 hours.

### Toolchain in `.tools/android` (free, nothing installed system-wide)

| Tool | Version | Where |
|---|---|---|
| OpenJDK | Eclipse Temurin 17.0.20.1+1 (`OpenJDK17U-jdk_x64_windows_hotspot_17.0.20.1_1.zip`, sha256 `e53a79c3…affc7cb0`) | `.tools/android/jdk-17` |
| Android SDK command-line tools | 23.0 (`commandlinetools-win-16111833_latest.zip`, sha1 `57d04f2d…a63e9d`) | `.tools/android/sdk/cmdline-tools/latest` |
| platform-tools (adb) | 37.0.1 | `.tools/android/sdk/platform-tools` |
| build-tools (aapt2, apksigner, zipalign) | 36.1.0 (what Godot 4.7.2 asks for) | `.tools/android/sdk/build-tools/36.1.0` |
| platform | android-36, revision 2 | `.tools/android/sdk/platforms/android-36` |
| emulator | 37.2.12 (build 16428233) | `.tools/android/sdk/emulator` |
| emulator system image | `system-images;android-36;default;x86_64` revision 2 (Android 16, AOSP, no Google services) | `.tools/android/sdk/system-images` |
| Gradle / Android Gradle plugin | 8.11.1 / 8.6.1 (from Godot's build template, AAB only) | `.tools/gradle` |
| NDK | not needed (the template ships prebuilt libraries) | — |
| .NET SDK | 9.0.301 (already on the machine; 10.0.300 too) | system |
| Godot export templates | 4.7.2.stable.mono (already installed) | `%APPDATA%\Godot\export_templates` |

Set up again on another Windows machine (about 3.7 GB download and disk):

```
unzip the Temurin 17 JDK                 -> .tools/android/jdk-17
unzip commandlinetools-win-*_latest.zip  -> .tools/android/sdk/cmdline-tools/latest
set JAVA_HOME=<repo>\.tools\android\jdk-17
.tools\android\sdk\cmdline-tools\latest\bin\sdkmanager --sdk_root=<repo>\.tools\android\sdk --licenses
... sdkmanager --sdk_root=... platform-tools build-tools/36.1.0 platforms/android-36
... sdkmanager --sdk_root=... emulator system-images/android-36/default/x86_64      (only for the emulator test)
python tools/build_ports.py keystores
python tools/android_qa.py create                                                   (the test AVD)
```

On this machine the licence files were copied from the Android SDK the owner had already installed
(`%LOCALAPPDATA%\Android\Sdk\licenses`).

### Texture memory (ISSUES BUILD-06)

`python tools/build_ports.py texture-report` (every texture under `assets/` decoded at once; the game never does
that, the numbers compare the two imports):

| Folder | Desktop import (Lossy WebP / lossless, RGBA8 in memory) | Mobile import (Basis Universal, ASTC 4x4 / ETC2 in memory) |
|---|---|---|
| assets/actors | 1731 MB | 436 MB |
| assets/bg_natural | 429 MB | 143 MB |
| assets/cutscenes | 205 MB | 68 MB |
| assets/ambient | 162 MB | 41 MB |
| assets/fg_natural + variants_natural | 45 MB | 11 MB |
| everything else (UI, items, template paintings; same import) | 111 MB | 111 MB |
| **all** | **2684 MB** | **811 MB** |

Measured in the running game (`--perf 20`, a tour of 20 rooms, texture memory reported by the engine; the desktop GPU
transcodes Basis to BC formats at the same 1 byte per pixel as ASTC 4x4): **523 MB with the desktop import** (350 MB
right after the start), **151 MB with the mobile import** (102 MB after the start); the private memory of the process
is 1275 MB against 675 MB.

Cost: the block-compressed files do not shrink as well as WebP. The imported textures are 305 MB on disk instead of
131 MB (actors 151 instead of 75 MB, backgrounds 86 instead of 17 MB, cutscenes 43 instead of 8 MB), which is why the
APK is 584 MB while the same build with the desktop textures is 412 MB.

### Tested (2026-10-08)

- **Emulator, no window:** Android 16 (API 36) x86_64, AVD `lastbell_qa` (Pixel 7 profile, 1080x2400, 420 dpi, 4 GB
  RAM), hardware acceleration through the Windows Hypervisor Platform (WHPX was already enabled, no admin rights
  needed), `-no-window -no-audio -no-boot-anim -gpu host`. The emulator's software GPU cannot run the game: its GLES
  allows 261 fragment uniform vectors and Godot's canvas shader does not link (grey screen); `-gpu host` renders with
  the PC's GPU off-screen.
- `python tools/android_qa.py smoke`: **10 of 10 checks pass** with real Android touch and key events
  (`adb shell input`): the debug APK starts and draws the title screen (first frame 8.4 to 10.3 s after the engine
  start), Back on the title asks whether to quit, New game with the difficulty step builds room S01, a finger sliding
  over the picture shows the names and takes nothing, a tap takes the tool bag (autosave: TOOLS, G01 done), the Eye
  button shows the markers, a long press looks, the inventory opens, a long press on an item looks at it, a tap takes
  it in hand and closes the inventory, a long press on the floor cancels it, Back opens and closes the pause menu, a
  double tap goes through the exit to S02 without the walk, Home writes the autosave and coming back shows the pause
  menu, no crash in logcat. Screenshots: `build/screens/android/smoke_01 … smoke_15.png`.
- **Aspect ratios and cutout:** 20:9 phone (2400x1080): the 16:9 picture with 240 px black bars left and right, the
  camera cutout lies inside a bar (`10_menu_immersive.png`, `smoke_*.png`). 4:3 tablet (2048x1536, emulated with
  `android_qa.py size`): bars above and below, nothing stretched, and the HUD moved 109 canvas px in from the left
  edge by the display's safe area (`40_tablet_4x3_menu.png`, `42_tablet_s01.png`).
- **Desktop, touch mode:** `<godot> --headless --path src/game -- --touch --acceptance touch`: **16 of 16 checks**
  (`Diagnostics/TouchAcceptance.cs`: label at the finger, slide, tap, long press, inventory, item in hand, HUD button
  size 9.0 mm, eye latch, Back with a doubled request, background and return, double tap) with injected
  `InputEventScreenTouch` / `InputEventScreenDrag` events. Screenshots of the gestures and of the screens at the
  phone's 200 % from hidden-window runs (`tools/qa_godot.py … -- --touch`): `build/screens/android/desktop_touch/`.
- **Desktop unchanged:** `dotnet test` 506 passed, `check_strings.py` OK, `--acceptance m1` 34 PASS, `m2` 46 PASS
  (with `--time-scale 3`, as the release verification runs it; without it AT29 waits 30 s for 34 s of lines),
  `travel` 4 PASS after the touch changes (logs `build/ports/logs/acceptance_*.txt`).
- **Not tested:** a real phone or tablet. The release APK is arm64-v8a and the emulator is x86_64, so the release APK
  itself was only checked statically (`build_ports.py verify`: ABI, package, signature with the release key, C#
  assemblies inside); it is the same project and code as the debug APK that was played. Performance, battery use,
  audio latency and real GPU memory are unknown until someone plays it on a device.

### Known limits

- **Not on a real device yet** (ANDROID-03, see above). C# on Android is marked experimental by Godot.
- **Size:** 584 MB APK (ISSUES ANDROID-04). The APK works for sideloading. For Google Play the bundle already has the
  game data in an install-time asset pack and a base module of 29 MB, so the old worry (a 290 MB PCK against a base
  limit of 150 MB) does not apply; Play's published limits are 200 MB for the base module and 1.5 GB for an asset
  pack (check the current table in the Play Console help). Whether Play accepts the bundle is only known after an
  upload to the internal test track.
- **HUD inside the picture (ANDROID-05).** On a 20:9 phone the buttons lie over the bottom corners of the painting while the bars
  beside it stay empty. Moving them into the bars needs the stretch aspect `expand` and a pass over every screen.
- **Small screens (ANDROID-06):** a phone runs the UI at 200 %, which is a logical screen of 960x540. Every screen fits (panels
  that cannot scroll are scaled down as a whole: the difficulty step, the map, puzzles), but the map and the settings
  tabs show little at once, and puzzle controls end up smaller than 9 mm.
- **Tablets with Android 16 or newer (ANDROID-07)** ignore the landscape lock of an app that targets API 36: held upright, the
  game is a letterboxed strip. A manifest property can opt out until API 37 (needs the Gradle build).
- **Texts that name the mouse (ANDROID-08):** hint and dialogue lines written for the PC ("klikni", "pravým tlačidlom") are shown
  as they are; only the tutorial, the help and the inventory hints have touch wording.
- **No haptics** (it would need the VIBRATE permission) and no gamepad mapping.

### What the owner needs for Google Play

1. A **Google Play developer account**: one-off USD 25 at <https://play.google.com/console/signup> (Google account,
   identity check; personal accounts opened after November 2023 must run a closed test with 12 testers for 14 days
   before they may publish to production).
2. Nothing else to buy. From the repository: the AAB above, the release keystore + password file (keep them safe),
   then in the Play Console: app name, short and full description, icon 512x512 and feature graphic 1024x500,
   at least two phone screenshots, the content rating questionnaire, the data safety form (the game collects no data
   and has no network permission) and a privacy policy URL.
3. Until then the APK can be shared directly (GitHub release, a link): Android asks the user to allow the install.

## Touch controls (phones and tablets)

Presentation only: Core is untouched, and a desktop build never turns the touch mode on (`Runtime/TouchMode.cs`: the
feature tag `mobile`), so the PC controls are exactly as before. On a PC with a touch screen the older gestures stay
(tap = left click, long press = right click).

| Gesture | What it does | PC counterpart |
|---|---|---|
| finger down on the picture | the name of the place under the finger, drawn about 8 mm above it; with an item in hand the action sentence, and only over a place where the item can be used | hover label |
| lift without sliding (tap) | the one action of that place: walk, take, use, talk, exit. The label stays 1.6 s | left click |
| slide, then lift | the names follow the finger; lifting does nothing | moving the mouse |
| hold 0.5 s | look; on empty floor the inventory; with an item in hand: cancel it | right click |
| second tap on the same place within 0.35 s | skip the walk | double click |
| Eye button | markers on every place for 6 s (a second tap hides them); with an item in hand only where it can be used | hold Space |
| two fingers held | markers while they are held | hold Space |
| tap during a line | next line | click / Enter |
| system Back | Esc: skip a line, close a screen, cancel the item, pause; on the title screen: quit? | Esc |
| inventory: tap an item | takes it in hand and closes the inventory (the HUD shows it with a cancel cross); open the inventory again and tap a second item to combine | click the item, click outside |
| inventory: hold an item | look at it (also the "Prezrieť" button of the card) | right click |

**Why a tap acts at once** (and not "first tap shows the label, second tap acts"): the game has one action per place
and no verb to choose, nothing a tap does can be lost, and a second tap on the same place is already the double tap
that skips the walk; two taps for everything would double the taps of the whole game. The label is not lost: it shows
while the finger is down, before anything happens, and a finger that slides off cancels. So "look first, then act" is
one gesture: touch, read, lift.

Also in touch mode:

- **HUD:** buttons of 74 logical px with their name under the glyph (no tooltips without a hover), no wooden band,
  no key hint. A first start picks the HUD scale and the subtitle size from the physical screen (`TouchMode.DeviceDefaults`,
  screen dpi): a 6.3 inch phone gets 200 % (buttons 9.0 mm) and 42 px subtitles (2.6 mm), an 8 inch tablet 150 %, a
  10 inch tablet 100 to 125 %. Both stay adjustable in the settings.
- **Screens:** the title screen has two columns, the inventory a wide card above one row of slots, tips wrap; panels
  that would not fit are scaled down (`ModalScreen`).
- **Safe area:** HUD, screens and subtitles keep inside the display's safe area (`TouchMode.SafeInsets`); the painting
  uses the whole picture. On phones wider than 16:9 the cutout is in the black bar and the inset is zero.
- **Aspect ratios:** stretch aspect `keep`: bars left and right on phones, above and below on 4:3 tablets.
- **Background:** when the app leaves the screen the game is autosaved at once; when it returns from the scene the
  pause menu is open (`UI/Common/MobileLifecycle.cs`). The window mode setting is ignored (it would end the immersive mode).
- **Texts:** `ui.tutorial.touch_tap / touch_hold / touch_eye` from ui.csv; 11 further rows (the control list and two
  inventory hints) have Slovak and English fallbacks in code and wait in `docs/writing/out_v6/ui_touch.csv`.

QA on the desktop: `python tools/qa_godot.py --path <project> --resolution 2400x1080 -- --touch …` emulates a
6.3 inch phone (`--touch-mm 0.118` a 10.5 inch tablet, `--safe-area l,t,r,b` a cutout); touch events:
`--input tap:x,y | longpress:x,y | doubletap:x,y | slide:x1,y1,x2,y2 | touchdown:x,y | touchup:x,y | twotap:x,y`,
phone events: `--input app:pause | app:resume | app:back`.

## Still to do

1. **Android on a real phone and tablet:** install the APK, play the prologue, watch memory, speed, sound and
   battery (ISSUES ANDROID-03). Then the open points of "Known limits" above (HUD into the black bars, the map
   and the settings on small screens, touch wording of PC texts; ISSUES ANDROID-04 to ANDROID-08).
2. **Google Play:** needs the owner's developer account (USD 25, once); then upload the bundle to the internal
   test track and see whether Play takes it as it is (ISSUES ANDROID-09).
3. **iOS:** the touch controls are the same code as on Android (feature tag `mobile`). C# on iOS is compiled ahead of
   time, which needs a Mac with Xcode. Needed from the owner: a Mac with Xcode,
   and the Apple Developer Program (USD 99 per year) for TestFlight / App Store or for installing on a device for
   longer than 7 days. A free Apple ID can install a build on your own device for 7 days.
4. **macOS notarisation** (no Gatekeeper warning) also needs the Apple Developer Program.
