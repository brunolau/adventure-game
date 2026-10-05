# Building Posledný zvonec (LastBell)

Status 2026-10-05: **Windows x86_64 is built and tested** (the exported exe, not the editor).
macOS, Android (arm64) and iOS have prepared export presets but are **not built**. See the per-platform
sections below for what each one still needs.

| platform | preset (`src/game/export_presets.cfg`) | status |
|---|---|---|
| Windows x86_64 | `Windows Desktop` | built by `build.bat`; exported exe ran S01, `--replay 11` (S11/1995), headless `--replay 94` |
| macOS universal | `macOS (not built)` | preset only; needs signing + notarization for distribution (Mac or rcodesign) |
| Android arm64 | `Android arm64 (not built)` | a debug APK exported once (176 MB, debug-signed) but **never run on a device**; C# on Android is experimental (net9.0) |
| iOS arm64 | `iOS (not built)` | preset only; needs a Mac with Xcode (C# on iOS is experimental, NativeAOT) |

## Windows (build now)

Requirements (same as `play.bat`):

1. Godot 4.7.2 .NET (mono) in `.tools/godot/Godot_v4.7.2-stable_mono_win64/` (git-ignored).
2. .NET SDK 8 or newer (`dotnet --list-sdks`; 9 and 10 are installed on the dev machine).
3. Godot **4.7.2 .NET export templates**:
   `Godot_v4.7.2-stable_mono_export_templates.tpz` (1.2 GB) from
   <https://github.com/godotengine/godot/releases/tag/4.7.2-stable>
   (SHA-512 `bb5c41d7…ff0bd5a`, listed in the release's `SHA512-SUMS.txt`). The `.tpz` is a zip: unpack its
   `templates/` folder **as** `%APPDATA%\Godot\export_templates\4.7.2.stable.mono\` (the folder must
   contain `version.txt` = `4.7.2.stable.mono` and `windows_release_x86_64.exe`). The non-mono
   `4.7.2.stable` templates do not work for a C# project.
   Self-contained alternative: unpack the templates anywhere and set `GODOT_TEMPLATES=<that folder>`.
   `build.bat` then links it into `%APPDATA%` with a directory junction (Godot only looks there).

Build:

```
build.bat            release export
build.bat debug      debug export (adds LastBell.console.exe that prints the log)
```

`build.bat` builds the C# code, imports the assets, deletes and re-creates `build/windows/`, then runs
`<console exe> --headless --path src/game --export-release "Windows Desktop" build/windows/LastBell.exe`.
It takes about 20 s on the dev machine.

Artifacts (`build/` is git-ignored), about 250 MB in total:

| file | what |
|---|---|
| `build/windows/LastBell.exe` | Godot runtime with the painted icon and version info (Posledný zvonec 0.1.0.0) |
| `build/windows/LastBell.pck` | all game resources (~70 MB) |
| `build/windows/data_LastBell_windows_x86_64/` | the C# assemblies (LastBell.dll, LastBell.Core.dll) and the bundled .NET runtime |

Ship the three together (zip the folder). There is no installer and no code signing yet, so Windows
SmartScreen warns on first start ("unknown publisher"). A code-signing certificate (`codesign/*` in the
preset, signtool) would remove the warning.

What the export contains: `export_filter = all_resources`, plus `include_filter = "*.json,
localization/*.translation"`. The `*.json` filter is required. The game reads these non-resource files
through `FileAccess`: `res://data/game.json`, `data/art_overrides.json`, `data/ambient/*.json`,
`data/debug/walkthrough.json` (QA), the actor/ambient sheet sidecars `assets/**/*.json`,
`assets/ui/credits.json`, `assets/ui/puzzle_glyphs.json` and `assets/ambient/manifest.json`. The localization
CSVs are imported into `localization/*.sk.translation`, which project.godot loads. `*.md` files are excluded.
If you add a new non-resource file type that is read through `FileAccess` (e.g. `.txt`, `.csv` read
by hand), add it to `include_filter` in **every** preset.

### Testing the exported build

The QA harness (src/game/README.md) also works in the exported exe. It only activates when user arguments follow `--`.
A release exe has no console, so write the log to a file:

```
build\windows\LastBell.exe --resolution 1920x1080 --log-file build\screens\export\run.log -- --lines --wait 2500 --screenshot C:\abs\path\S01.png
build\windows\LastBell.exe --resolution 1920x1080 --log-file run.log -- --replay 11 --skip-lines --screenshot C:\abs\path\S11.png
build\windows\LastBell.exe --headless --log-file run94.log -- --replay 94 --quit-after 1
```

Use absolute screenshot paths. In an exported build, relative paths are resolved from the exe folder,
not from the repository. Results of the 2026-10-05 run are in `build/screens/export/`:
`exported_S01_start.png`, `exported_replay11_S11.png`, walk-cycle and Ela idle frames (`walk_0*.png`,
`ela_0*.png`, `contact_grid_check.png`) and the logs. All steps OK, exit code 0.

## App icon

Painted style-A icon: a brass school bell in front of a brass ring engraved with the four symbols from the
title-screen brief, with a winter-dusk/summer-sky split showing passing time over Dúbravka panel blocks.
Master: `art/ui/icon/icon_master_v1.png` (nano-banana-pro, USD 0.15, logged in `art/spend-log.csv`).
`python art/tools/app_icon.py export art/ui/icon/icon_master_v1.png` writes:

- `src/game/icon.png` (1024, `application/config/icon`, macOS app icon)
- `src/game/icon.ico` (16-256, Windows exe + window icon, `config/windows_native_icon`)
- `src/game/assets/ui/icon/icon_<16..1024>.png` (Android 192 launcher, iOS 1024, store art)
- `src/game/assets/ui/icon/icon_android_{fg,bg}_432.png` (Android adaptive icon layers)

## Mobile readiness (done now)

- **Textures ≤ 4096 px.** Many mobile GPUs cannot sample larger textures. Eighteen actor sheets were single-row
  strips of 4672-8064 px. `art/tools/regrid_sheets.py` re-packed them into row-major grids (2 rows, at most
  4032 px wide) from the lossless pipeline sources, and wrote `columns`/`rows` into each sheet JSON. Hero
  sheets are bit-exact (lossless); NPC sheets are re-encoded like `export_actors.py` (q92 RGB, lossless
  alpha). The loader (`SpriteSheet.Region` / `GridRegion` in `scripts/Living/Actors/ActorAnimationSet.cs`,
  and `SpriteSource` for ambient sheets) reads frame *i* at column `i % columns`, row `i / columns`.
  `columns` comes from the JSON, else from texture width / cell width, so old single-row strips still work.
  Check before every mobile build: `python art/tools/regrid_sheets.py --check` (exit 1 if any texture
  under `src/game/assets` exceeds 4096 px). Run it without `--check` to fix them.
- **Touch input** (`scripts/PlayerInput/TouchGestures.cs`, wired into `InputRouter`): **tap = left click**,
  **long press (0.5 s) = right click** (look / open the bag), **two-finger tap = Space** (labels; it also
  advances a line). Godot's default `emulate_mouse_from_touch` stays on, so HUD and GUI buttons get taps first.
  Only the emulated pointer events that reach the world are turned into gestures, on release (a drag
  moves the hover and does nothing on release). Verified with real `InputEventScreenTouch` events:
  `-- --input longpress:1500,950` opens the bag, `tap:180,200` takes the service bag (G01),
  `twotap:960,900` toggles labels. The mouse acceptance run still passes 19/19.
- Renderer: GL Compatibility on desktop and mobile (`rendering_method.mobile`), `import_etc2_astc=true`.

## macOS (later; needs a Mac to sign and test)

- Preset `macOS (not built)`: universal binary, bundle id `eu.lastbell.poslednyzvonec` (placeholder,
  decide the final reverse-DNS id once), icon `res://icon.png`, min macOS 10.15 / 11 (arm64).
  The templates are already installed (`macos.zip` in the mono templates).
- Godot can export the `.zip`/`.app` on Windows, but such an app is unsigned and Gatekeeper blocks it.
  For distribution you need an **Apple Developer account** (USD 99/year), a *Developer ID Application*
  certificate, code signing with the hardened runtime, and **notarization**. The simplest way is a Mac
  with Xcode command-line tools: in the preset choose Code Signing = "Xcode codesign" and Notarization =
  "Xcode notarytool" (the preset ships with both disabled). Godot can also sign and notarize from Windows with
  `rcodesign`, but testing still needs a Mac.
- C# entitlements: `allow_jit_code_execution`, `allow_unsigned_executable_memory` and
  `disable_library_validation` are already on in the preset. The .NET runtime needs them under the
  hardened runtime.
- Saves go to `~/Library/Application Support/LastBell/saves` (`user://`, custom user dir).

## Android arm64 (later)

- Preset `Android arm64 (not built)`: arm64-v8a only, package `eu.lastbell.poslednyzvonec` (placeholder),
  immersive mode, adaptive icon layers, ETC2/ASTC textures, no permissions.
- Needs: Android SDK (platform-tools, build-tools, a platform; on the dev machine it is at
  `%LOCALAPPDATA%\Android\Sdk`), **JDK 17** (`C:\Program Files\Java\jdk-17`), both set in the Godot editor
  settings (`export/android/android_sdk_path`, `java_sdk_path`). Debug exports use the editor's debug keystore.
  A **release keystore** must be created once and kept safe (it cannot be replaced after a Play Store upload):
  `keytool -genkeypair -v -keystore lastbell-release.keystore -alias lastbell -keyalg RSA -keysize 2048 -validity 10000`.
  Then set `keystore/release`, `keystore/release_user` and `keystore/release_password` in the preset, or
  pass them via the environment (`GODOT_ANDROID_KEYSTORE_RELEASE_PATH/USER/PASSWORD`). Never commit the keystore or the password.
- **C# on Android is experimental in Godot 4.7.** The export template requires **`net9.0`**. A first export
  attempt on 2026-10-05 stopped with "C# project targets 'net8.0' but the export template only supports
  'net9.0'". `src/game/LastBell.csproj` now switches to net9.0 only when `GodotTargetPlatform == android`.
  Desktop stays on net8.0. LastBell.Core (net8.0) can be referenced from net9.0. With that change a debug
  export succeeded (`--export-debug "Android arm64 (not built)" build/android/LastBell-debug.apk`, 176 MB,
  `lib/arm64-v8a/libgodot_android.so` + Mono runtime, signed with the editor debug keystore). It has **not been
  installed or run**: no arm64 device was connected, and the machine only has an x86_64 emulator image. Next step:
  `adb install -r build/android/LastBell-debug.apk` on a real phone, then check start-up, touch and saves. Google Play needs an `.aab`
  (`gradle_build/use_gradle_build=true`, `export_format=1`), which needs the Android build template
  (Project > Install Android Build Template).
- Known C# mobile limitations: only arm64 (and x86_64) ABIs are supported for .NET; no armeabi-v7a.
  The bundled .NET runtime makes the APK noticeably larger (not measured yet), startup is slower than
  with GDScript, and on-device debugging is limited.
- Game-side notes for touch: the 16:9 canvas (`stretch aspect=keep`) letterboxes on 19.5:9 phones.
  Hover-only information (the item action sentence while an item is selected) only shows while
  dragging a finger. Plan a touch-friendly confirmation (e.g. first tap = show the sentence, second tap = act)
  before release. HUD buttons are 64 px at 1080p, so check them on a small phone.

## iOS (later; needs a Mac with Xcode)

- Preset `iOS (not built)`: arm64, iPhone + iPad, min iOS 15, `export_project_only=true` (Godot writes
  an Xcode project; Xcode builds, signs and uploads it), icon `assets/ui/icon/icon_1024.png`,
  bundle id `eu.lastbell.poslednyzvonec` (placeholder).
- Needs a Mac with Xcode, an Apple Developer account and Team ID (`application/app_store_team_id`), and
  provisioning profiles. C# on iOS is experimental: it is compiled ahead of time with NativeAOT, which only
  runs on macOS. Reflection-heavy code can break under AOT. LastBell uses `System.Text.Json` with `JsonNode`
  (no reflection serializer), which should be AOT-safe, but this is not verified. Check whether the iOS
  template also requires net9.0. If so, extend the csproj condition to `ios`.

## Checklist before any release build

1. `dotnet build src/LastBell.sln` and `dotnet test src/LastBell.sln` are green; `python tools/check_strings.py` is OK.
2. `python art/tools/regrid_sheets.py --check` reports 0 textures over 4096 px.
3. `build.bat`, then run the exported exe to S01 and `--replay 11` (above) and look at the screenshots.
4. Credits screen lists all CC BY / BY-SA / BY-NC sources (`art/source/CREDITS.md`).
5. Optional: the QA harness is active in release builds when arguments follow `--`. Gate it on
   `OS.IsDebugBuild()` before a public release if that is unwanted (ISSUES BUILD-03).
