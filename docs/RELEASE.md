# Posledný zvonec - release notes for the product owner

Version: **0.3.0**, built 2026-10-10 for Windows, Linux, macOS and Android (the main menu and the exe say the same
number). **Not published yet:** the GitHub release page still offers `v0.2.0` (2026-10-08, Windows, Linux, macOS);
0.3.0 waits for your word (0.2.1 of 2026-10-09 was built and never published). Before that: 0.1.0 of 2026-10-07,
published on 2026-10-08 as `v0.1.0`.
Languages: Slovak and English, texts and voices (Android: both text languages, English voices only). Test record
behind this page: `docs/MILESTONE5.md` (sections "Version 0.3.0", "Version 0.2.1", "Version 0.2.0", "Owner feedback of
2026-10-07 evening", "Round 2 applied", "Content v2 applied", "Second verification and release pass" and "Verification
and release pass").

## In short

- **New in 0.3.0 (2026-10-10):**
  - **English dub** (your note: "now make english dubbing"). Everything that is spoken in Slovak is now spoken in
    English too: 2,217 dialogue lines, Adam's look texts and the Standard / Hard versions (2,622 recordings, 3 h
    15 min). Every character keeps the voice it has in Slovak, speaking British English. With English texts the game
    plays the English voices, with Slovak texts the Slovak ones. Settings → Zvuk has a new row *Jazyk dabingu* (Ako
    texty / Slovenčina / English), so English subtitles with the original Slovak voices are one click away. **Nobody
    has listened to the English dub yet.** The checks were automatic; 57 recordings are marked for a listen. Listening
    page: `docs/voice/en.html` (open it from the repository folder); record: `docs/voice/ENGLISH.md`.
  - **Android has only the English dub** (your note: "for the android version include only english dubbing"). The
    phone plays English voices with Slovak or English subtitles; *Hovorené dialógy* still switches them off.
  - **Android: the exit arrows stand above the buttons** (your note: "ensure the location navigation buttons dont
    collide the the control buttons … they need to be raised a bit up"). The arrow badges the Eye shows sat on or
    behind the row of buttons at the bottom, and two exits (the Grasshopper playground → the lane, LEAL Court →
    Sokolikova) lay completely under the buttons and could not be tapped at all. The badges are now above the row,
    and a tap on a badge goes through its exit. Nothing of this changes the PC version.
  - Android, small: a first-start tip no longer covers a slot of the open inventory.
- **New in 0.2.1 (2026-10-09):**
  - **English names for the characters, on every platform** (your notes: "Bodka => Dotty ... and come up with
    English sounding names", "for all platforms of course"): Adam and Mira Perry, Tony, Otto, Jane, Leah and Victor
    Korman, Dotty the dog, Barnaby the pigeon, Blinky the robot and the rest. Only Dotty is your own choice; the
    others are proposals you have not seen yet (full table: `docs/translation/README.md`, "English names of people";
    any name is one line to change). 896 of the 5,255 English texts changed. Slovak texts and the Slovak voices are
    unchanged, so with English subtitles the voice says *Tóno* and the subtitle says *Tony*.
  - **Android: lists scroll with a finger** (your first report from the phone: "none of the things that are meant to
    be scrollable is actually scrollable"). A finger that slides over a list scrolls it, also when it went down on a
    button; a short touch is still a tap. Volume sliders no longer jump when a finger passes over them. The settings
    have their tabs in a column on phones, so four rows fit instead of two. Nothing of this changes the PC version.
  - **Android build** (new since 0.2.0, see "Linux, macOS, Android, iOS" below): an APK for phones and a Google Play
    bundle, with touch controls.
- **New in 0.2.0 (2026-10-08):**
  - **Standard and Hard give less away** (your note: "the game is still hinting way too much… I don't want
    'metronóm má Emil'"; approved: "yup, good adjustments"). On these two difficulties 163 lines, goals and journal
    entries have a second version that says what is needed, not who has it or where to go. The answer is still
    findable in the world. Easy keeps the explicit texts. 32 of the changed lines are spoken and were re-recorded.
  - **English.** All 5,255 texts are translated (Settings, tab "Text a titulky": *Jazyk*). A first start follows the
    system language: Slovak or Czech gets Slovak, everything else English. A profile that already played 0.1.0 keeps
    its language. The voices stay Slovak with English subtitles. The window title follows the language (*The Last
    Bell*). Place names follow your rule: Dubravka, Ruzinov, Petrzalka, Jasna; the Old Town, the Old Bridge, Kamenne
    Square, Lake Vrbicke, the Grasshopper playground, LEAL Court, Light photo studio. Painted signs stay Slovak. The
    English was translated and checked without a human proofreader (`docs/translation/review.html` shows every text
    in both languages).
  - **Adam's look texts are voiced**: everything he says when you look at a room, a thing, an item or a locked exit
    (567 texts, 390 recordings), on top of the 2,217 dialogue lines. The setting "Hovorené dialógy" switches all of
    it.
  - **Linux and macOS preview builds** next to the Windows one. Linux was started in an Ubuntu 24.04 container
    without a screen; macOS was checked by its structure only, because there is no Mac here.
  - Tóno is "Tóno" in hover labels and topic headers, and the first workshop goal no longer uses unexplained terms.
- **Your notes of 2026-10-07 evening are in:**
  - **S07** (bus stop, 2020): the way to Potraviny cez okienko now points **down**, and behind the stop the painting
    shows small family houses of the suburb instead of open fields.
  - **S18 / S62** (kiosk street 1995 / shop street 1982): the stop is on the **left**, the school yard on the
    **right**.
  - **S69 is „Pri LEALe“ everywhere** (room name, map, exit labels, journal, hints and every line; „k LEALu“, „od
    LEALu“). The four spoken lines that say the name were re-recorded.
  - **S21** (Kamenné námestie): the other exits stay; Petržalský podchod is now in the **lower right corner, pointing
    right**.
  - **Narrator**: a **female voice** (Callirrhoe) with a warmer, more interested delivery reads the two narrator lines
    (the 1962 cutscenes CS04 and CS07). Fero's dialect is unchanged.
  - S51, S17, S28 and S02 stay as they were (your "ok").
- **Round 2 is in** (you approved it on 2026-10-07: "i guess ok"): Adam no longer names people, places or things
  before the game has shown or told them (Juro, Pali, Oto, Dezider, Alena, Nina, the return bridge and the rest; the
  audit of every text in every legal order now finds **0 problems**). **Difficulty**: at New Game you choose Ľahká,
  Štandardná (recommended) or Ťažká, and you can change it in Settings, tab "Hra". Easy gives the exact step as
  before; Standard gives a nudge in Adam's voice and where to look, never the solution; Hard gives only the nudge,
  after three minutes without progress, and no puzzle help. 268 hint texts were written for this.
- The two cosmetic fixes you were promised: little Zuzana in the Ivanka park stands still while she talks to Adam
  (and while he talks) and goes back to her hopscotch when the conversation ends; S69 Pri LEALe is now
  in the same sunset light as the kiosk street S18 next to it (the painting relit, nothing moved).
- The whole game is playable from a new game to the end credits and the postgame, on Windows 10/11 (64-bit).
- **Content v2 is in** (you approved it on 2026-10-06: "ok, they are good"): Zuzana at seven in the Ivanka park with
  her side quest (the class bell, 4 steps), Zuzana at forty and Kubo in the new room S69 Pri LEALe (reached
  from the kiosk street S18) with the side quest of Kubo's bike bell (3 steps), the rhythm drawing of the main story
  now on the yard wall, two new epilogue pictures, and every new conversation and topic of 1995, 1962, 1982 and 2035.
- Every automated check passes on the final code (re-run on 2026-10-07 evening after your notes: tests, text checks,
  knowledge audit with 0 problems, blocking, acceptance and the save/load and keyboard-only routes; the full set of
  four routes last ran in the morning with round 2). All 134 story
  and side actions were played by real input events in four different orders: one saved and reloaded after every action, one showed every line, one skipped every
  cutscene, and one used **only the keyboard** for the whole game. The 2020 prologue was also played from the main
  menu with real Windows key presses only, with a save and a load on the way.
- **All 30 handoff acceptance tests pass**, AT19 (keyboard only) included.
- Open before a public release: your answer on the art licence (DECISIONS item 9) and the few points in
  docs/DECISIONS.md "Status 2026-10-06". None of them blocks play.
- Paid generation so far: **USD 250.11** (8228 log rows, art/spend-log.csv, read 2026-10-07 20:25). Your evening notes
  cost USD 0.31 (the S07 painting edit USD 0.15, the GPT check of the renamed texts USD 0.06, the new voice takes and
  their checks USD 0.10); this verification added nothing.

## How to install and play (Windows)

1. Take the zip `build/m5/ship/PoslednyZvonec-0.3.0-windows-x64.zip` (487.2 MB; the GitHub release page still has
   0.2.0). Unpacked, it is the folder `PoslednyZvonec/` (639.7 MB). It holds three things that must stay
   together: `LastBell.exe` (109.5 MB), `LastBell.pck` (448.7 MB, of it 127.9 MB Slovak and 127.2 MB English voice
   clips) and `data_LastBell_windows_x86_64/` (81.5 MB, the C# code and the .NET runtime).
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
  Pri LEALe 1995), **5 puzzles**, **9 cutscenes**, an epilogue
  whose pictures follow the side quests you did, end credits, and a postgame with the album (replay the ending and
  the cutscenes).
- 5,255 player texts in Slovak and English: 2,239 spoken lines, 2,246 world texts and 770 UI texts (163 of them the
  less revealing Standard / Hard versions), written in the Polda tone you chose and approved era by era
  (docs/writing/approval/). The puzzles and solutions did not change; the one main step
  that moved is the rhythm drawing (B19), now on the wall of the yard Pri LEALe.
- Original music: one theme per period plus menu, puzzle, tension and epilogue (9 tracks). About 105 sound effects
  and ambience loops. Subtitles for everything. Spoken lines: 2,639 Slovak voice clips in `src/game/assets/voice/`
  (2,217 dialogue lines, 390 look texts, 32 Standard / Hard versions; the narrator is the female voice Callirrhoe
  since 2026-10-07, docs/voice/FULL.md) and, since 0.3.0, 2,622 English ones in `src/game/assets/voice_en/` for the
  same lines (docs/voice/ENGLISH.md).
- Three difficulty levels (Easy / Standard / Hard, saved with each save file): they change the hints and, since
  0.2.0, how much the texts give away,
  journal with goals and hints per step, a map with fast travel, an era chooser, 8 save slots plus an
  autosave, and settings: volumes, text speed, subtitle size and background, fullscreen/window, HUD scale, walk speed
  100/125/150 %, reduced motion, key rebinding.

## System requirements (Windows)

| | minimum (estimated) | tested |
|---|---|---|
| OS | Windows 10 or 11, 64-bit | Windows 11 Pro 26200 |
| graphics | OpenGL 3.3 GPU (Godot "Compatibility" renderer), 1 GB VRAM | AMD Radeon RX 7600 |
| memory | 4 GB RAM (the game uses about 1.2 GB) | desktop with Ryzen 9 7900X |
| disk | 640 MB free, plus the 487 MB download | - |
| screen | 1280x720 or larger (16:9; other shapes get bars) | 1280x720 and 1920x1080 windows |

Measured on the test PC: main menu 0.8 s after start, a room change takes about 0.7 s (fade included), 406-446 MB
of texture memory. Only one PC was tested, so the minimum column is an estimate. Laptops with integrated graphics
were not tried.

## Known issues

None of these stops a playthrough. Ids are in `design-doc/ISSUES.md`. Everything the two playtests and milestone 5
found is fixed (selection after use, hints per step, the painted time-node clock, conversations that stay open,
Esc = one line, Mira in the attic, the CS07 symbols, Adam's winter coat, RECEPCIA, toasts and hover label over
screens, the S05 door, staging in front of props, the version number), except:

- (fixed 2026-10-08) Tóno is now "Tóno" in hover labels and topic headers too.
- (fixed 2026-10-08) The first workshop goal no longer names the cradle before it is explained.
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

### Linux, macOS, Android, iOS
Details and the test record of each port: docs/PORTS.md.
- **Linux x86_64 (preview):** `build/ports/PoslednyZvonec-0.3.0-linux-x86_64.tar.gz` (476.2 MB). 0.2.0 is on the
  release page; 0.3.0 was started without a screen in an Ubuntu 24.04 container. Nobody has played either on a Linux
  desktop yet.
- **macOS, Apple Silicon and Intel (preview):** `build/ports/PoslednyZvonec-0.3.0-macos.zip` (543.6 MB). Not
  notarised and never started on a real Mac: the player opens it with right-click, Open. For a normal install it
  needs an Apple Developer account (USD 99/year), a Developer ID certificate, signing and notarization, and a Mac to
  test on.
- **Android (not released):** `build/ports/PoslednyZvonec-0.3.0.apk` (584.9 MB, arm64, Android 7.0 or newer, no
  permissions) and a Google Play bundle (521.2 MB). It installs over 0.2.0 or 0.2.1 and keeps the saves. English
  voices only (the Slovak recordings are left out of the Android build). Touch controls: tap acts, hold looks, a
  slide scrolls lists, the Eye button shows the markers (the exit arrows stand above the buttons), system Back is
  Esc, autosave when the app leaves the screen. You tried the earlier builds on your phone (2026-10-09: lists did not
  scroll, fixed in 0.2.1; 2026-10-10: the exit arrows collided with the buttons, fixed in 0.3.0). 0.3.0 was played
  only in an Android 16 emulator (touch smoke test 13 of 13); **it has not been on a real phone yet**. Not on the
  GitHub release page: it waits for your test and for your approval of 11 Slovak touch texts
  (`docs/writing/out_v6/ui_touch.csv`). Google Play needs a developer account (USD 25, once). C# on Android is
  experimental in Godot 4.7.
- **iOS:** needs a Mac with Xcode, an Apple Developer team id and provisioning profiles. C# on iOS is
  experimental (NativeAOT), so check that it works.

### Voice acting
- Already in the engine: when `assets/voice/<line_id>.ogg` exists, it plays on the Voice bus, the music ducks,
  and the clip stops when the line is skipped. Voice clips are installed for every spoken line (voice recast, commit
  6b6d141; the narrator recast to a female voice and the „Pri LEALe“ lines re-recorded on 2026-10-07, docs/voice/FULL.md).
- The voices are synthetic (Gemini TTS through fal.ai, each take checked by speech-to-text). Since 0.2.0 the look
  texts and the Standard / Hard versions are voiced too. 33 look takes are flagged for a listen (docs/voice/).
- **English voices since 0.3.0** (docs/voice/ENGLISH.md): the same synthetic voices speaking British English, one
  recording per Slovak one; 57 takes are flagged for a listen, and the pronunciation of the Slovak place names
  (Dubravka, Cierna Voda, Vrbicke …) needs an ear.
- Open: human voice actors if you want them (about 50 characters, several at two or three ages), lip flap timed to
  the clip (LIVING-03) and loudness mastering like the music (-16 LUFS).

## Paid generation (art/spend-log.csv)

Read 2026-10-10 05:00: **USD 263.48**. On 2026-10-10: the English dub USD 9.97 (2,622 voice takes, 141 retakes and
a transcript of each: USD 9.96; an accent check of 23 pilot takes by an audio model: USD 0.01). The Android fixes,
the builds and this verification cost nothing.

Read 2026-10-08 22:40: **USD 253.51** (9294 rows). On 2026-10-08: USD 3.29 (the voices of the look texts USD 1.97,
the GPT check of the Standard / Hard texts USD 1.09, their 32 voice takes and the Dezider auditions the rest). The
English translation, its LanguageTool check, the ports and this verification cost nothing.

Read 2026-10-07 20:25: **USD 250.11** (8228 rows). Since the morning read: the S07 painting edit (suburb houses)
USD 0.15, the GPT check of the „Pri LEALe“ texts USD 0.06, the narrator auditions and the re-recorded lines with their
speech-to-text checks USD 0.10. The exits and this verification and release pass cost nothing.

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
