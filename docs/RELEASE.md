# Posledný zvonec - release notes for the product owner

Version: Windows build of 2026-10-05 (exe version 0.1.0.0; the main menu shows the data version "2.0.0", see Known
issues). Language: Slovak only. Test record behind this page: `docs/MILESTONE5.md`.

## In short

- The whole game is playable from a new game to the end credits and the postgame, on Windows 10/11 (64-bit).
- Every automated check passes. All 127 story and side actions were played through by real input events in three
  different orders. One of the orders saved and reloaded after every action. The exported release exe was played
  by hand through the 2020 prologue to the arrival in 1995, with a save/load round trip on the way.
- 29 of the 30 handoff acceptance tests pass. AT19 is the exception: a playthrough of the whole game with only the
  keyboard was not done, only spot checks.
- Open before a public release: your answer on the art licence (DECISIONS item 9) and the licence note that goes
  with it, the version number shown in the menu, and the known issues below. None of them blocks play.
- Paid generation so far: **USD 102.42** (683 fal.ai calls). This pass added nothing.

## How to install and play (Windows)

1. Take the zip `build/m5/ship/PoslednyZvonec-0.1.0-windows-x64.zip` (244.5 MB). Unpacked, it is the folder
   `PoslednyZvonec/` (366.8 MB). It holds three things that must stay together: `LastBell.exe` (109.5 MB),
   `LastBell.pck` (176.2 MB) and `data_LastBell_windows_x86_64/` (81.0 MB, the C# code and the .NET runtime).
   The same files are in `build/windows/`. That folder also holds 34 MB of old locked DLL copies
   (`*.dll~RF*.TMP`), left there by an older game window that is still open, so do not zip that folder.
2. Unpack it anywhere, for example in Documents, and double-click `LastBell.exe`. There is no installer.
3. The exe is not code-signed, so Windows SmartScreen says "Windows protected your PC". Click "More info", then
   "Run anyway". Only the first start asks.
4. Saves and settings go to `%APPDATA%\LastBell\` (`saves\slot1-8.json`, `autosave.json`, `settings.cfg`). To
   uninstall, delete the game folder and that folder.

From the repository you can also start the game with `play.bat` (the editor runtime). `build.bat` rebuilds the
release in about 30 s plus the asset import (docs/BUILD.md).

### Controls

| input | what it does |
|---|---|
| left click | walk / use / talk / take; a click on an exit walks there |
| double click | skip the walk: Adam is at the target at once |
| right click | look at the thing; on empty floor: open the bag; with an item selected: drop the selection |
| hold Space (or hold the eye button) | round markers on everything you can click |
| item in the bag -> click a target | use the item; the sentence next to the cursor ("Vyzdvihnúť Mirin nákup") appears only when the combination works |
| I / J / M / H / T | bag / journal / map / hint / era chooser (at the time nodes, also the clock button in the HUD) |
| Esc | cancel the selection, otherwise pause (save, load, settings, help); skips cutscenes and queued lines |
| Tab, Enter, Backspace | keyboard play: next target, use it, look at it |
| F5 / F9 | quick save / quick load |

Touch input is built in for the mobile ports: tap, long press = right click, two-finger hold = markers.

## What is in the game

- **68 rooms** in five periods: 2020 Chorvátsky Grob / Čierna Voda (the prologue), 1995 Bratislava (Dúbravka,
  Karlova Ves, Staré Mesto, Ružinov, Petržalka), 1960 Ivanka pri Dunaji, 1982 Dúbravka and 2035 Jasná / Chopok.
  Every room is painted in style A from its real place, has 3-24 ambient animations, and uses the natural layout
  (decision 1b).
- **94 main and 33 side actions** in 27 quests, **9 side quests**, **5 puzzles**, **9 cutscenes**, an epilogue
  whose pictures follow the side quests you did, end credits, and a postgame with the album (replay the ending and
  the cutscenes).
- About 2 950 player texts: 756 dialogue lines, the world texts and the UI. All were rewritten in plain Slovak
  (docs/writing/SAMPLES.md). The story, puzzles and solutions did not change.
- Original music: one theme per period plus menu, puzzle, tension and epilogue (9 tracks). About 105 sound effects
  and ambience loops. Subtitles for everything. **No voice acting yet.**
- Journal with goals and three hint levels per quest, a map with fast travel, an era chooser, 8 save slots plus an
  autosave, and settings: volumes, text speed, subtitle size and background, fullscreen/window, HUD scale, walk speed
  100/125/150 %, reduced motion, key rebinding.

## System requirements (Windows)

| | minimum (estimated) | tested |
|---|---|---|
| OS | Windows 10 or 11, 64-bit | Windows 11 Pro 26200 |
| graphics | OpenGL 3.3 GPU (Godot "Compatibility" renderer), 1 GB VRAM | AMD Radeon RX 7600 |
| memory | 4 GB RAM (the game uses about 1.2 GB) | desktop with Ryzen 9 7900X |
| disk | 400 MB free, plus the 245 MB download | - |
| screen | 1280x720 or larger (16:9; other shapes get bars) | 1280x720 and 1920x1080 windows |

Measured on the test PC: main menu 0.8 s after start, a room change takes about 0.7 s (fade included), 406-446 MB
of texture memory. Only one PC was tested, so the minimum column is an estimate. Laptops with integrated graphics
were not tried.

## Known issues

None of these stops a playthrough. Ids are in `design-doc/ISSUES.md`.

Most noticeable:
1. **An item stays selected after a successful use** (PT-F09 / PT-S16). While it is selected, a click on an exit
   does nothing and gives no feedback. Workaround: right click (or the x on the HUD chip) to drop it. This is a
   rule and design change in Core and needs your OK.
2. **Hints follow the quest, not the step** (PT-F08 / PT-S26). Hint 1 can repeat a step you already did. Read hint
   2 and 3.
3. **The time node in S11 / S51 / S57** is the clock button in the HUD (or T). The painted stop clock does nothing
   (PT-F10).
4. **Continuity at story moments:** Mira speaks in the S40 attic without being there (PT-S18). The CS07 picture
   shows ✕ where the room has + (PT-S21). Adam wears autumn clothes in the snowy December 1982 (PT-S20).
5. **Conversations close after each topic.** Click the person again for the next topic (PT-S17).

Smaller issues:
- Toasts and the hover label can sit over open windows. "New item / new goal" toasts appear before the lines that
  explain them (PT-S22, PT-S23, M5-05).
- In S05, after unlocking, the upper part of the workshop door still gives the lock look. The lower part walks in
  (M5-02).
- Adam sometimes stands in front of what he uses: the S05 table, the S09 case, the S10 cradle, Jana's face in S60
  (M5-04, PT-S24). The service-bag icon is brown leather, while the painted bag is green canvas.
- Long item names are cut in the bag ("Prenosný chronometer…", PT-F12). Esc skips the whole intro monologue
  (PT-F13). Tóno is "Anton Farkaš" in hover labels (PT-S25). The S43 lobby has English "RECEPTION" lettering
  (PT-S27). A few spawn and marker spots are tight (PT-S28, M3-02).
- The S11 tram is part of the painting and never leaves (LIVING-05). Crowd murmur in a few rooms is not Slovak
  (AUDIO-04).
- The menu says "Verzia 2.0.0", which is the story data version, while the exe says 0.1.0 (M5-03). Pick one
  release number.
- The credits list every photo, sound, font and the engine. They do not yet say under which licence the game's
  own art is released (waits for decision 9, see below).

## Credits and licences (summary)

All of this is shown in the game under **Autori** (main menu), generated from `art/source/CREDITS*.md` and
`art/source/AUDIO_CREDITS.md` by `tools/build_credits.py`.

- **Game art** (backgrounds, characters, items, cutscenes, UI, icon): painted with AI image tools (fal.ai
  nano-banana-pro / nano-banana-2, animations with Hailuo, Kling, Wan and Seedance image-to-video). The inputs
  were freely licensed photos, OpenStreetMap reconstructions and our own sketches. Planned licence: **CC BY-SA
  4.0** (the paintings adapt CC BY-SA photos). This waits for your confirmation (DECISIONS item 9).
- **Photo sources: 134 entries.** CC BY-SA 4.0: 54. CC BY-SA 3.0 / 3.0 de / 2.5 / 2.0: 22 / 1 / 1 / 11. CC BY
  4.0 / 3.0 / 2.0: 3 / 9 / 15. Public domain: 14. CC0: 1. OpenStreetMap (ODbL): 1. Each one is credited by
  author, title, licence and link.
- **Non-commercial (NC) sources, flagged:** two Flickr photos by carl_eric ("Block" and "Yard", Sokolíkova 2012,
  **CC BY-NC-SA 2.0**). They are image inputs of rooms S17, S18, S55, S61, S62, S65 and S66 and of the cutscene
  frames CS02_2, CS08_1 and CS08_2. A style painting made from "Yard" is also the style image of S17, S18, S55, S61
  and S66. The register marks each of these rows. As long as these stay in, **the game must stay
  non-commercial**. For a commercial release, those rooms need new free photos and repainting.
- **Your reference photos** (`art/source/owner_refs/`: press photos and Street View screenshots) were only looked
  at. They were never given to a generator, are not in the repository history or the build, and are not credited
  as sources.
- **Music:** 9 original tracks made for this game with Google Lyria 3 Pro via fal.ai. They carry Google's
  inaudible SynthID watermark, and the provider's terms give us the rights to the output. No existing tune or
  artist was requested.
- **Sound effects and ambience:** 106 sounds, all **CC0** (Kenney.nl Interface Sounds, UI Audio, RPG Audio and
  Music Jingles, plus Freesound authors listed one by one).
- **Fonts:** Alegreya and Alegreya Sans (SIL Open Font License 1.1; the licence texts ship with the fonts).
- **Engine:** Godot Engine 4.7.2 (MIT). The bundled .NET runtime is MIT licensed too.

Text to add to the download page and credits once item 9 is confirmed: *"Herná grafika: CC BY-SA 4.0. Časti
odvodené od fotografií s licenciou CC BY-NC-SA 2.0 (izby S17, S18, S55, S61, S62, S65, S66 a zábery CS02_2,
CS08_1, CS08_2) len na nekomerčné použitie. Zdroje a autori sú v hre v časti Autori."*

## What is left

### macOS, Android, iOS
All three have a ready export preset, icons and touch input. None is built or tested yet (details in
docs/BUILD.md).
- **macOS:** needs an Apple Developer account (USD 99/year) and a Developer ID certificate, then signing with the
  hardened runtime and notarization. A Mac is needed to test. The C# entitlements are already set.
- **Android:** a debug APK exported once but never ran on a device, because no arm64 phone was available. Next
  steps: create the release keystore (keep it safe), test on a real phone (start-up, touch, saves), build an
  `.aab` for Google Play, and lower memory use (hero sheets are about 230 MB decoded, BUILD-06; ambience at
  mobile quality, AUDIO-07). C# on Android is experimental in Godot 4.7 and needs net9.0, which is already handled.
- **iOS:** needs a Mac with Xcode, an Apple Developer team id and provisioning profiles. C# on iOS is
  experimental (NativeAOT), so check that it works.
- Touch design still needed for all mobile ports: a finger cannot hover, so the "use X on Y" sentence needs a tap
  equivalent (DECISIONS item 11). The HUD buttons also need a check on small phones.

### Voice acting
- Already in the engine: when `assets/voice/<line_id>.ogg` exists, it plays on the Voice bus, the music ducks,
  and the clip stops when the line is skipped. No voice files exist yet.
- Needed: casting and recording, or a decision on synthetic voices, for 756 dialogue lines across about 50
  characters. Many characters appear at two or three ages (Mira, Tóno, Jana, Oto). A script per character can be
  exported from `src/game/localization/dialogue.csv` by line id.
- Then: lip flap timed to the clip (LIVING-03), line duration taken from the audio, and loudness mastering like
  the music (-16 LUFS).

## Paid generation (art/spend-log.csv)

| what | calls | USD |
|---|---:|---:|
| images (nano-banana-pro 43.50, nano-banana-2 26.96) | | 70.46 |
| animations, image-to-video (Hailuo pro 15.84, standard 13.50, Wan 0.41, Kling 0.35, Seedance 0.27) | | 30.37 |
| music (Lyria 3 Pro 1.44, MiniMax test 0.15) | | 1.59 |
| **total** | **683** | **102.42** |

Spend by day: 2026-10-04 USD 2.10 (style tests), 2026-10-05 USD 100.32. Milestone 5 cost nothing.

## What waits for you

See `docs/DECISIONS.md`, section "Status 2026-10-05 (milestone 5)".
