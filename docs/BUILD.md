# Building Posledný zvonec (LastBell)

Status 2026-10-05: **Windows x86_64 is built and tested** (the exported exe, not the editor).
macOS, Android (arm64) and iOS have prepared export presets but are **not built**. See the per-platform
sections below for what each one still needs.

| platform | preset (`src/game/export_presets.cfg`) | status |
|---|---|---|
| Windows x86_64 | `Windows Desktop` (release) / `Windows Desktop (QA)` | built by `build.bat` / `build.bat debug`; release PCK 176 MB; prologue G01-G11 by real input on the release PCK, 67-room perf tour, 0 missing-asset warnings |
| macOS universal | `macOS (not built)` | preset only; needs signing + notarization for distribution (Mac or rcodesign) |
| Android arm64 | `Android arm64 (not built)` | a debug APK exported once (176 MB, debug-signed, before the size work) but **never run on a device**; C# on Android is experimental (net9.0) |
| iOS arm64 | `iOS (not built)` | preset only; needs a Mac with Xcode (C# on iOS is experimental, NativeAOT) |

Milestone 5 (2026-10-05, docs/MILESTONE5.md): `build.bat` re-run on the final code (exe 109.5 MB, PCK 176.2 MB, data 81.0 MB);
the release exe was played by real input from a new game through the prologue with a save/load round trip, and refused
the harness flags. The clean distributable (without the `*.dll~RF*.TMP` leftovers of a still-running old window) is
`build/m5/ship/PoslednyZvonec/` and `build/m5/ship/PoslednyZvonec-0.1.0-windows-x64.zip` (244.5 MB).

## Windows (build now)

Requirements (same as `play.bat`, plus Python 3 for `tools/release_assets.py`):

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
4. Python 3 on `PATH` (`python`).

Build:

```
build.bat            release export  -> build/windows/        (preset "Windows Desktop")
build.bat debug      QA export       -> build/windows_debug/  (preset "Windows Desktop (QA)", adds LastBell.console.exe)
```

`build.bat` builds the C# code, applies the texture import policy (`tools/release_assets.py imports`), checks the
release filters (`tools/release_assets.py filter --check`), imports the assets, deletes and re-creates the output
folder, then runs `<console exe> --headless --path src/game --export-release "Windows Desktop" build/windows/LastBell.exe`
and writes the PCK contents by folder to `build/pck_contents_release.txt` (`_debug` for the QA build).
It takes about 30 s on the dev machine.

Two things `build.bat` handles on this machine:
- If a `LastBell.exe` from the output folder is still running, Windows keeps its files locked (`*.dll~RF….TMP`
  leftovers in `data_LastBell_windows_x86_64/`). `build.bat` warns; close the game before building for a clean folder.
- Godot writes the icon and version info into the exe after copying the template. That step sometimes fails with
  `ERR_CANT_OPEN` (`template_modifier.cpp`) on a freshly copied exe; the exe is then the bare template (no icon).
  `build.bat` compares the exe size with the template and exports once more (that always worked); it fails if the
  icon is still missing.

Artifacts (`build/` is git-ignored):

| file | size | what |
|---|---|---|
| `build/windows/LastBell.exe` | 109.5 MB | Godot release runtime with the painted icon and version info (Posledný zvonec 0.1.0.0) |
| `build/windows/LastBell.pck` | 176.2 MB | the game resources (was 448.0 MB, see "Release size") |
| `build/windows/data_LastBell_windows_x86_64/` | 78 MB | the C# assemblies (LastBell.dll, LastBell.Core.dll) and the bundled .NET runtime |
| the three zipped (deflate) | 244 MB | what a player downloads (before: about 514 MB) |

Ship the three together (zip the folder). There is no installer and no code signing yet, so Windows
SmartScreen warns on first start ("unknown publisher"). A code-signing certificate (`codesign/*` in the
preset, signtool) would remove the warning.

What the export contains: `export_filter = all_resources`, plus `include_filter = "*.json,
localization/*.translation, assets/ui/fonts/*.txt"` (the fonts' OFL licence texts travel with the fonts). The
`*.json` filter is required. The game reads these non-resource files through `FileAccess`: `res://data/game.json`,
`data/art_overrides.json`, `data/blocking/**/*.json`, `data/audio/*.json`, `data/ambient/actors.json`, the
actor/ambient sheet sidecars `assets/**/*.json`, `assets/ui/credits.json`, `assets/ui/puzzle_glyphs.json` and the
ambient manifests. The localization CSVs are imported into `localization/*.sk.translation`, which project.godot
loads. `*.md` files are excluded. If you add a new non-resource file type that is read through `FileAccess`
(e.g. `.txt`, `.csv` read by hand), add it to `INCLUDE` in `tools/release_assets.py` and run
`python tools/release_assets.py filter` (it rewrites the filters of **every** preset).

## Release size (2026-10-05)

The PCK had grown to 448 MB: Godot imported every texture "lossless" (it re-encodes the lossy WebP paintings as
lossless images, about 5x their file size; `.godot/imported` was 428 MB) and both the template and the natural
paintings shipped. Two changes, both in `tools/release_assets.py` (run by `build.bat`):

1. **Texture compression** (`imports`): Godot's *Lossy* import (WebP inside the `.ctex`, quality 0.90; decoded to
   RGBA8 on load, no mipmaps) for the large painted images: `assets/bg_natural`, `assets/bg`, `assets/bg_options`,
   `assets/cutscenes`, `assets/actors` (298 textures). Everything else stays lossless: UI, cursors, icons, fonts,
   item icons (drawn 1:1 at small sizes) and the painting-matched overlays (`assets/ambient` cut-outs and masks,
   `variants*`, `fg*`), which sit pixel-exactly on the painting and must not get their own compression noise.
   VRAM compression (S3TC/BPTC) was not used: BC1/BC3 bands on the soft painted gradients, BC7 is 1 byte per pixel
   (about 2 MB per background, larger than the lossy WebP on disk), and the PCK is not compressed further.
   New textures get Godot's lossless default until `build.bat` (or `python tools/release_assets.py imports`) runs.
2. **Release export filter** (`filter`): the release presets (Windows, macOS, Android, iOS) do not ship what only
   the template mode, the QA harness or art reviews use. Natural blocking is the default and every room has
   `data/blocking/<room>.json`, so these are unused in a release: `assets/bg/*`, `assets/variants/*`, `assets/fg/*`
   (template paintings, overlays, masks), the 37 ambient cut-outs of the template paintings
   (`assets/ambient/<room>/<file>`, not `natural/`), `data/ambient/S*.json` (their layers), `assets/bg_options/*`
   (the S57 painting options for the owner decision) and `data/debug/*` (the QA walkthrough). The QA preset
   `Windows Desktop (QA)` keeps everything, so `--blocking template` still works there and in the editor.
   `filter --check` fails when the presets are out of date or when natural-mode data (`data/blocking/**`,
   `data/audio`, sheet and manifest JSON) names an excluded file. The main menu backdrop now uses the natural S01
   painting (it used the template `bg/S01.webp`).

| | before | after |
|---|---|---|
| `LastBell.pck` | 448.0 MB (2392 files) | 176.2 MB (2335 files) |
| actors / bg_natural / cutscenes / bg (template) | 215.5 / 85.2 / 39.8 / 15.2 MB | 63.9 / 15.9 / 6.9 / 0 MB |
| audio (ambience, music, sfx; unchanged, already Vorbis 112-160 kbps) | 60.5 MB | 60.5 MB |
| ambient cut-outs (lossless; grew with new natural living layers) | 15.0 MB | 15.4 MB |
| release zip (exe + pck + data) | about 514 MB | 244 MB |

`python tools/release_assets.py pck build/windows/LastBell.pck --release` lists a PCK by folder and fails if an
excluded file is inside.

Quality check (1920x1080 screenshots of the same QA scenes before and after, `--no-ambient`, 11 rooms and 2
cutscene beats; `build/screens/release/`): rooms 44.6-46.8 dB PSNR against the lossless import (mean pixel
difference below 1 of 255, 99.9 % of the pixels within 8 of 255, at most 7 pixels per frame up to 29); the cutscene beats differ only by the camera pan's
sub-pixel timing (the difference image shows outlines, not blocks). Zoomed crops of Adam, Dana, the S04 sign and
the flat S60 ceiling/wall show no blocking, ringing or banding.

## Performance (2026-10-05, Ryzen 9 7900X, Radeon RX 7600, 1920x1080 window)

Measured with the QA exe running the release PCK (`--perf`, src/game/README.md; the release exe takes no
harness arguments):

| | before (448 MB PCK, old code) | after |
|---|---|---|
| start to the first frame (main menu), release exe | not measured in release; QA exe 826-848 ms | 834-835 ms after engine start (window after 0.46 s) |
| first room (S01) build in the harness start | 352 ms | 388 ms (hero sheets; while the menu shows, `Main` now preloads the start room) |
| room transition, 20 rooms (fade out + build + fade in) | median 703 ms, max 889 ms | median 703 ms, max 718 ms |
| room build (synchronous, screen black) | median 37 ms, max 305 ms | median 20 ms, max 70 ms |
| longest frame while in a room (background loading) | - | median 7.1 ms, max 12.7 ms |
| texture memory after 20 rooms | 639 MB (187 MB at start) | 446 MB (350 MB at start incl. preloads) |
| process working set / private after 20 rooms | 336 / 1230 MB | 320 / 1179 MB |
| texture memory after 67 rooms (all eras) | (grows: about +23 MB per room) | 406 MB |

What changed:
- **Neighbour preloading** (`World/RoomPreloader.cs`): after every room build the paintings, foreground masks,
  occluder textures and, through `RoomPreloader.PathProviders` (the living world), the hero sheets of the next
  room's variant and every NPC sheet of the rooms behind the exits are loaded on Godot's loader threads (at most 6
  rooms). While a cutscene or an action's lines keep the old room on screen, the next room is preloaded; the main
  menu preloads the start room. Without it (`--no-preload`) the same tour has builds up to 366 ms and transitions up
  to 945 ms. Non-neighbour jumps (portals, fast travel, dev jumps) still build synchronously behind the fade (up to
  about 160 ms).
- **Bounded sprite caches** (`Runtime/RoomScopedCache.cs`): the sprite-sheet, actor-set and ambient-sprite caches
  kept every visited room's textures for the whole session (all actor sheets decoded are 1.39 GB). Entries now drop
  when no room build used them for 2 rooms; the hero's sheets stay.
- **Line timing after a load** (`Presentation/DialoguePresenter.cs`): the frame after a load (the room is built
  inside it) no longer counts as reading time, so the line on screen when the game was saved is not skipped.
- Mobile note: the hero sheets alone are about 230 MB decoded (two variants of 14 sheets of 3040x1048). Fine on
  desktop; for phones consider Basis Universal or smaller hero sheets (ISSUES BUILD-06).

## Testing the exported build

The release exe ignores the QA harness (ISSUES BUILD-03): everything after `--` is dropped and the log says
`LastBell: release build, N QA argument(s) after "--" ignored`. Engine options still work:

```
build\windows\LastBell.exe --resolution 1920x1080 --log-file C:\abs\path\run.log
```

Test the exported game with the QA build (`build.bat debug`, debug template, same code, all assets plus the QA
walkthrough). To test exactly the release content, copy `build\windows_debug` somewhere and replace its
`LastBell.pck` with `build\windows\LastBell.pck` (the templates do not support `--main-pack`; the release PCK has no
`data/debug/walkthrough.json`, so use `--act` instead of `--play`):

```
build\windows_debug\LastBell.console.exe --resolution 1920x1080 -- --lines --wait 2500 --screenshot C:\abs\path\S01.png
build\windows_debug\LastBell.console.exe --resolution 1920x1080 -- --replay 11 --skip-lines --screenshot C:\abs\path\S11.png
build\windows_debug\LastBell.console.exe --headless -- --replay 94 --quit-after 1
<copy>\LastBell.console.exe --resolution 1920x1080 --time-scale 3 -- --real --act G01 ... --act G11 --fast-text --shots C:\abs\dir --screenshot C:\abs\path\S11.png
<copy>\LastBell.console.exe --resolution 1920x1080 -- --perf 20
```

Use absolute screenshot paths. In an exported build, relative paths are resolved from the exe folder,
not from the repository. Results of the 2026-10-05 release-engineering run are in `build/screens/release/`
(before/after screenshots and crops, the prologue shots `prologue/`, perf logs). The prologue G01-G11 + P01 + CS01
ran by real input events on the release PCK to S11/1995 with PHONE, TOOLS, SHEDKEY, CHRONO; neither that run nor the
67-room tour logged a missing texture or any warning. The release exe given `-- --room S44 --screenshot … --quit-after 1`
logged the "ignored" line, kept running as a normal game and wrote no screenshot (the desktop was locked during
this run, so the main menu itself was checked in the QA build: `menu_release_pck.png`).

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

1. `dotnet build src/LastBell.sln` and `dotnet test src/LastBell.sln` are green; `python tools/check_strings.py` is OK;
   `--acceptance m1` and `m2` pass (src/game/README.md).
2. `python art/tools/regrid_sheets.py --check` reports 0 textures over 4096 px.
3. `python tools/release_assets.py check` is OK (texture import policy applied, release filters up to date and not
   excluding anything natural-mode data uses). `build.bat` runs it.
4. `build.bat` and `build.bat debug`; the release PCK is about 176 MB (`build/pck_contents_release.txt`).
5. Run the QA exe with the release PCK through the prologue (`--real --act G01 … --act G11`) and `--perf 20`
   ("Testing the exported build"); the log has no "not found" warning. Start the release exe once and look at
   the main menu.
6. Credits screen lists all CC BY / BY-SA / BY-NC sources (`art/source/CREDITS.md`).
