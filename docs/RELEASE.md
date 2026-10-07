# Posledný zvonec - release notes for the product owner

Version: Windows build of 2026-10-07 08:17 (rebuilt with the approved round 2: the knowledge fixes, the difficulty
settings with their written hints, Zuzana standing still in conversations and S69 at sunset; it also carries the
committed changes since the last build: the voice clips, the exits by real geography and the difficulty engine;
before that, 2026-10-06 23:14 with content v2), version 0.1.0 (the main menu and the exe say the same number). Language: Slovak only. Test record behind this page: `docs/MILESTONE5.md` (sections
"Round 2 applied", "Content v2 applied", "Second verification and release pass" and "Verification and release pass").

## In short

- **Round 2 is in** (you approved it on 2026-10-07: "i guess ok"): Adam no longer names people, places or things
  before the game has shown or told them (Juro, Pali, Oto, Dezider, Alena, Nina, the return bridge and the rest; the
  audit of every text in every legal order now finds **0 problems**). **Difficulty**: at New Game you choose Ľahká,
  Štandardná (recommended) or Ťažká, and you can change it in Settings, tab "Hra". Easy gives the exact step as
  before; Standard gives a nudge in Adam's voice and where to look, never the solution; Hard gives only the nudge,
  after three minutes without progress, and no puzzle help. 268 hint texts were written for this.
- The two cosmetic fixes you were promised: little Zuzana in the Ivanka park stands still while she talks to Adam
  (and while he talks) and goes back to her hopscotch when the conversation ends; the Sokolíkovský dvor S69 is now
  in the same sunset light as the kiosk street S18 next to it (the painting relit, nothing moved).
- The whole game is playable from a new game to the end credits and the postgame, on Windows 10/11 (64-bit).
- **Content v2 is in** (you approved it on 2026-10-06: "ok, they are good"): Zuzana at seven in the Ivanka park with
  her side quest (the class bell, 4 steps), Zuzana at forty and Kubo in the new room S69 Sokolíkovský dvor (reached
  from the kiosk street S18) with the side quest of Kubo's bike bell (3 steps), the rhythm drawing of the main story
  now on the yard wall, two new epilogue pictures, and every new conversation and topic of 1995, 1962, 1982 and 2035.
- Every automated check passes on the final code (re-run in full on 2026-10-06 evening with content v2). All 134 story
  and side actions were played by real input events in four different orders: one saved and reloaded after every action, one showed every line, one skipped every
  cutscene, and one used **only the keyboard** for the whole game. The 2020 prologue was also played from the main
  menu with real Windows key presses only, with a save and a load on the way.
- **All 30 handoff acceptance tests pass**, AT19 (keyboard only) included.
- Open before a public release: your answer on the art licence (DECISIONS item 9) and the few points in
  docs/DECISIONS.md "Status 2026-10-06". None of them blocks play.
- Paid generation so far: **USD 239.75** (3112 log rows, art/spend-log.csv, read 2026-10-06 23:20). Applying content v2 and
  this verification added nothing.

## How to install and play (Windows)

1. Take the zip `build/m5/ship/PoslednyZvonec-0.1.0-windows-x64.zip` (346.8 MB). Unpacked, it is the folder
   `PoslednyZvonec/` (482.2 MB). It holds three things that must stay together: `LastBell.exe` (109.5 MB),
   `LastBell.pck` (291.3 MB, of it 98.9 MB voice clips) and `data_LastBell_windows_x86_64/` (81.4 MB, the C# code
   and the .NET runtime).
   The same files are in `build/windows/`.
2. Unpack it anywhere, for example in Documents, and double-click `LastBell.exe`. There is no installer.
3. The exe is not code-signed, so Windows SmartScreen says "Windows protected your PC". Click "More info", then
   "Run anyway". Only the first start asks.
4. Saves and settings go to `%APPDATA%\LastBell\` (`saves\slot1-8.json`, `autosave.json`, `settings.cfg`). To
   uninstall, delete the game folder and that folder.

From the repository you can also start the game with `play.bat` (the editor runtime). `build.bat` rebuilds the
release (docs/BUILD.md).

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
| Tab / Shift+Tab, Enter, Backspace | keyboard play: next / previous target, use it, look at it; in menus and screens Tab moves between the buttons and Enter presses one. The whole game can be played without a mouse |
| F5 / F9 | quick save / quick load |

Touch input is built in for the mobile ports: tap, long press = right click, two-finger hold = markers.

## What is in the game

- **69 rooms** in five periods: 2020 Chorvátsky Grob / Čierna Voda (the prologue) and Dúbravka, 1995 Bratislava
  (Dúbravka, Karlova Ves, Staré Mesto, Ružinov, Petržalka), Ivanka pri Dunaji shown as June 1962, 1982 Dúbravka in
  December snow and Jasná / Chopok in winter 2035.
  Every room is painted in style A from its real place, has 3-24 ambient animations, and uses the natural layout
  (decision 1b).
- **94 main and 40 side actions** in 29 quests, **11 side quests** (new: Q10 "the class bell" in Ivanka 1962, Q11 in
  the Sokolíkovský dvor 1995), **5 puzzles**, **9 cutscenes**, an epilogue
  whose pictures follow the side quests you did, end credits, and a postgame with the album (replay the ending and
  the cutscenes).
- About 4 790 player texts: 2 196 spoken lines, 2 113 world texts and 476 UI texts, rewritten in the Polda tone you
  chose and approved era by era (docs/writing/approval/). The puzzles and solutions did not change; the one main step
  that moved is the rhythm drawing (B19), now on the wall of the Sokolíkovský dvor.
- Original music: one theme per period plus menu, puzzle, tension and epilogue (9 tracks). About 105 sound effects
  and ambience loops. Subtitles for everything. Spoken lines: the voice clips in `src/game/assets/voice/` at build
  time (2217 clips; a separate voice task was regenerating clips while this build was made, so some lines may still
  have older takes or none).
- Three difficulty levels that change only the hints (Easy / Standard / Hard, saved with each save file),
  journal with goals and hints per step, a map with fast travel, an era chooser, 8 save slots plus an
  autosave, and settings: volumes, text speed, subtitle size and background, fullscreen/window, HUD scale, walk speed
  100/125/150 %, reduced motion, key rebinding.

## System requirements (Windows)

| | minimum (estimated) | tested |
|---|---|---|
| OS | Windows 10 or 11, 64-bit | Windows 11 Pro 26200 |
| graphics | OpenGL 3.3 GPU (Godot "Compatibility" renderer), 1 GB VRAM | AMD Radeon RX 7600 |
| memory | 4 GB RAM (the game uses about 1.2 GB) | desktop with Ryzen 9 7900X |
| disk | 400 MB free, plus the 260 MB download | - |
| screen | 1280x720 or larger (16:9; other shapes get bars) | 1280x720 and 1920x1080 windows |

Measured on the test PC: main menu 0.8 s after start, a room change takes about 0.7 s (fade included), 406-446 MB
of texture memory. Only one PC was tested, so the minimum column is an estimate. Laptops with integrated graphics
were not tried.

## Known issues

None of these stops a playthrough. Ids are in `design-doc/ISSUES.md`. Everything the two playtests and milestone 5
found is fixed (selection after use, hints per step, the painted time-node clock, conversations that stay open,
Esc = one line, Mira in the attic, the CS07 symbols, Adam's winter coat, RECEPCIA, toasts and hover label over
screens, the S05 door, staging in front of props, the version number), except:

- Tóno is "Anton Farkaš" in hover labels and topic headers, Tóno in every line (PT-S25, your choice N9).
- The first workshop goal says "kolíska stolového uzla ZVON" before anything explains it (PT-F14, N14).
- An exit click while you deliberately keep an item selected does nothing (the handoff rule; N2 b). After a
  successful use the item is no longer selected, so this is now rare.
- Keyboard play: with a full bag, reaching an item takes up to 7 key presses; the map's room cards up to 8. Tab
  goes one way, Shift+Tab the other.
- A few exit labels and walk-to points sit far from their doors (M3-02, cosmetic). The S11 tram is part of the
  painting and never leaves (LIVING-05). Crowd murmur in a few rooms is not Slovak (AUDIO-04).
- The credits list every photo, sound, font and the engine, but not yet the licence of the game's own art (waits
  for decision 9).
- The S69 painting is now at sunset, but the people in it are drawn in daylight colours (as in S18).
- Not checked by us: sound by ear (our test runs are muted), laptops with integrated graphics, other screen shapes
  than 16:9.

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
  and S66, and it is the base of the new room S69 (and the place reference of the epilogue picture EPILOGUE_11). The register marks each of these rows. As long as these stay in, **the game must stay
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
odvodené od fotografií s licenciou CC BY-NC-SA 2.0 (izby S17, S18, S55, S61, S62, S65, S66, S69 a zábery CS02_2,
CS08_1, CS08_2, EPILOGUE_11) len na nekomerčné použitie. Zdroje a autori sú v hre v časti Autori."*

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
  and the clip stops when the line is skipped. Voice clips are installed (voice recast, commit 6b6d141) and a voice
  task is still working on them; the new round-2 lines need their clips from that task.
- Needed: casting and recording, or a decision on synthetic voices, for 756 dialogue lines across about 50
  characters. Many characters appear at two or three ages (Mira, Tóno, Jana, Oto). A script per character can be
  exported from `src/game/localization/dialogue.csv` by line id.
- Then: lip flap timed to the clip (LIVING-03), line duration taken from the audio, and loudness mastering like
  the music (-16 LUFS).

## Paid generation (art/spend-log.csv)

Read 2026-10-07 08:25: **USD 249.80** (8174 rows; another task was adding voice rows while this was read). On
2026-10-07 so far: writing round 2 GPT reviews USD 2.31, the S37 exit-geometry fixes USD 0.30, **the S69 relight
USD 0.15** (the only paid call of applying round 2), voice USD 6.48. Earlier state:

**USD 239.75** (3112 log rows): 2026-10-04 USD 2.10 (style tests), 2026-10-05 USD 109.80, 2026-10-06 USD 127.85 (winter
Jasná, Ivanka 1962, the 2020 corrections, the writing and its GPT reviews for all eras, Zuzana's sprites, Kubo, the
S69 painting, the new item icons and the afternoon changes: entry hall without the desk, the S03 grasshopper, the
podlubie, S30 and CS03_1 on the Starý most, plus the evening's other work). The breakdown by model is in the log.
The verification and release passes of 2026-10-06, the content v2 one included, cost nothing.

## What waits for you

See `docs/DECISIONS.md`, section "Status 2026-10-06 (verification and release pass)".
