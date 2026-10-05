# Playtest "first half": new game → 2020 prologue → 1995 → first arrival in 1960

Date 2026-10-05. Fresh-eyes playtest by an agent who reads Slovak, played from the main menu (Nová hra) to the
arrival at Ivanka pri Dunaji 1960 (S31). Screenshots: `build/screens/playtest/first-half/` (numbered in play order;
`verify/` and `50x_*` are after-fix checks). Issues: `design-doc/ISSUES.md` PT-F01 … PT-F14.

## How it was played

- Editor runtime (`Godot_v4.7.2-stable_mono_win64_console.exe --path src/game`), **no harness arguments**: the real
  main menu, autosave on (the owner's saves were backed up and restored), natural blocking (default).
- 1920x1080 window for the whole run; a second run at **1280x720** for the prologue start (menu, intro, hover,
  bag, journal, pause, map).
- Input: real Windows mouse/keyboard messages to the game window (cursor moved to the point, WM_MOUSEMOVE /
  button / key messages), so Godot's normal input path, GUI first. Screenshots via PrintWindow. Limits of this
  method: the **hardware cursor is not in the screenshots**, so cursor shapes were not checked, and I could not
  **hear audio**, so audio was not checked.
- No walkthrough use: before each step I wrote down what I thought the game wanted, from the journal (J), looks
  (right click), hover names, Space markers and dialogue. Where I got stuck I used the in-game hints (H), as a
  player would.

## Timeline (what I believed the game asked → what I did → result)

**2020 prologue (Chorvátsky Grob / Čierna Voda)**

1. Menu → *Nová hra* → confirmation (overwrites autosave) → intro monologue in the garage S01. Journal: "Nákup pre
   babku – pomôž Mire s nákupom". Belief: take my tools, go to grandma. Space markers show 5 spots; looks are
   short and funny. Took the service bag (G01). Clear.
2. S02 street: Lenka (dog, side quest about the ball) and courier Roman, all topics read; mailbox/owl looks.
   Journal: "zastav sa u Ely na dobrovoľníckom výdajnom mieste". Left exit → S03. Clear.
3. S03 pavilion: Ela gives the shopping list (G02). Exit label "Čierna Voda pri výveske" vs the shop on the right:
   took the right one. Clear.
4. S04 shop window: Dana. Belief: hand her the list. Selected ORDER in the bag, hover on Dana shows the action
   sentence → GROCERIES (G03). Clear.
5. Back S03 → S02 → Mira's gate S05 (double click on exits skips the walk – very good). Belief: leave the groceries
   on the little table. Used GROCERIES on the table (G04), the bag appears on the table (state patch). Clear.
6. Side path → S06 window: Mira, three topics → SHEDKEY (G05). Clear.
7. S05: key on the workshop door (G06) – the padlock disappears. **Then I clicked the door to go in and got the
   lock look again** ("na tie dvere treba babkin kľúč"); only the threshold was the exit (PT-F05, fixed).
8. S09 hall: brass case → chronometer (G07). Journal: "Oprav kolísku stolového uzla ZVON" – I did not know what
   "kolíska" was until I looked around in S10 (PT-F14).
9. S10: entry line mentions a warning "NESYNCHRONIZOVAŤ BEZ SVEDKA", the sign on the wall says "NEPREPISOVAŤ
   ORIGINÁL" (PT-F06, fixed). Cradle look says "ak nesvieti, je to poistka". Tools on the cradle (G08) → old fuse.
   Belief: find the same fuse – the garage drawer had fuses. Walked back S09 → S05 → S02 → S01 (double clicks,
   about 15 s), drawer → FUSE (G09), back to S10, fuse in (G10).
10. Shape panel P01: the scheme look explains it (circle to circle …). Solved first try (G11) → CS01 → 1995.

**1995 (Dúbravka school, Bratislava)**

11. S11 tram stop 1995 → S12 school front: club notice (B01). Journal: show the caretaker the chronometer.
12. S13 lobby: Tóno, two topics; CHRONO on Tóno (B02). S14 club classroom: Mira 1995. **Talking to her put Adam
    behind the desk row, legs hidden, back to her** (PT-F01, fixed). B03 → LETTER. Journal: "Zachráň kazetu zo
    školského rozhlasu a zostav mapu meracích uzlov". Two goals at once, but both named.
13. S15 → S16 broadcast room: deck look → tools on the deck (B04, broken belt). Belief: someone repairs belts – the new objective names
    Pali in Karlova Ves. Tram S11 → S19 → S20 Pali; belt on Pali (B05) → new belt.
    Fast travel on the map back to S16 (map fast travel is great), belt in (B06) → TAPE_RAW, but the two voices
    interfere. Journal → Juro in Ružinov.
14. S19 → S21 Kamenné nám. → S25 Miletičova → S27 cassette club: tape on Juro (B07). He wants a connector from
    Fero and a sleeve from Milada. **Stuck for a bit at Fero**: his topics do not mention the scale; the hint (H)
    first repeated "Ukáž kazetu Jurovi" which I had already done (PT-F08); the 3rd hint is the full chain. Looking
    at the stuck scale ("klieštikmi z brašne ju vytiahnem") was the real clue – I should have looked first. Tools on
    the scale (B08) → CONNECTOR.
15. S26 Milada → BRAID (B09). Combined in the bag: connector + adapter (B10), sleeve + link (B11). The bag card said
    only "Vyber druhý predmet." which made me think selection is only for combining (PT-F07, text fixed).
16. Fast travel S16: link on the service socket (B12) → TAPE. Journal → the archive with Mira's letter.
17. S21 → S23 archive: LETTER on the archivist (B13) → NEGATIVE. S24 photo studio (B14) → CALPHOTO.
    S22 antiquary: Viera (B15) → OVERLAY. Bag: foil on the map → rotate puzzle, two turns, confirm (B16) → NODEMAP.
18. S28 underpass → S29 Dezider's garage: NODEMAP on Dezider (B17) → COIL; he sends me to Emil for a metronome.
    S19 Emil (B18): **Adam stood in front of the table and hid the metronome** (PT-F01, fixed).
19. Journal: rhythm digits in the school yard. S12 → S17 yard: rhythm panel look gives "TRI VLNY, DVA ÚDERY, ŠESŤ
    DIELIKOV = 3–2–6" (B19). Adam read it standing in front of the drawing (PT-F01, fixed).
20. S28 → S30 embankment: coil in the holder (B20), metronome on the stool (B21), dial: **the "000" looked like
    letters O** (PT-F04, fixed); set 3-2-6 → Odmerať (B22) → the cut scene with the chronometer showing 1960.
21. Journal: "Na časovom uzle Dúbravskej zastávky vyber Ivanku 1960". Fast travel S11. **I clicked the big stop
    clock – nothing (Adam walked behind the shelter)**. The era chooser is the new clock button in the HUD
    (PT-F10, open). Chooser → 1960 → S31 Ivanka pri Dunaji 1960, entry line, station master. End of this playtest.

**1280x720 run**: menu, new game, intro, hover label, bag (detail card, selection), journal, pause, map – all
readable, nothing overlaps, the HUD key hint is hidden on the narrow layout. The map captions now show the
accents (412_720_map.png).

## Problems found

20 problems: **11 fixed, 9 open** (7 logged as PT-F08 … PT-F14, 2 minor notes below). Not counted: one possible
hover-label glitch I could not confirm (see "Not checked / uncertain").

| # | where | problem | status |
|---|---|---|---|
| 1 | S14 Mira 1995 | talk point put Adam behind the desks, legs hidden, back to her | fixed (PT-F01, blocking data) |
| 2 | S19 Emil | Adam in front of the table hides the metronome | fixed (PT-F01) |
| 3 | S17 rhythm panel | Adam stands in front of the drawing he reads | fixed (PT-F01) |
| 4 | HUD | selected-item chip runs into the "Podrž Space" hint | fixed (PT-F02, code) |
| 5 | Map | region captions lose the accents (CHORVATSKY, DUBRAVKA) | fixed (PT-F03, code) |
| 6 | Digit dial | old-style 0 reads as the letter O | fixed (PT-F04, code) |
| 7 | Digit dial | háček of "Číslica" cut off | fixed (PT-F04) |
| 8 | S05 workshop | after unlocking, the door leaf is still the look-only prop | fixed (PT-F05, blocking data) |
| 9 | S05 workshop | door look stale after unlocking | fixed (PT-F05, override text) |
| 10 | S10 | entry line names a warning the room does not show | fixed (PT-F06, override text) |
| 11 | Bag | "Vyber druhý predmet." hides that a selected item is used in the scene | fixed (PT-F07, ui text) |
| 12 | Hints | hint 1 of M05 repeats a done step | open PT-F08 (Core) |
| 13 | Selection | item stays selected after a successful use | open PT-F09 (Core / design) |
| 14 | S11 node | painted clock is not the time node; chooser only in HUD | open PT-F10 |
| 15 | Topic menu | panel covers NPC/Adam right of centre | open PT-F11 (UI layout) |
| 16 | Bag | long names cut: "Prenosný chronometer…" | open PT-F12 (cosmetic) |
| 17 | Intro | Esc skips the whole intro monologue | open PT-F13 (design) |
| 18 | Prologue | "kolíska stolového uzla ZVON" unexplained when first shown | open PT-F14 (text) |
| 19 | S11 1995 | the tram is painted: it never leaves or arrives, also not after riding it | open, already ISSUES LIVING-05 |
| 20 | S09 | the brass bell on the table (title object!) is not clickable | open, minor (would need game.json) |

## What I changed (presentation / text / data only; no story, rule or solution change)

- `src/game/data/blocking/S14.json`, `S19.json`, `S17.json`: interaction points (PT-F01).
- `src/game/data/blocking/S05.json`: shed-door prop rect = padlock only, exit rect = whole door, label anchors (PT-F05).
- `src/game/scripts/UI/Hud/HudView.cs`: key hint hidden while an item is selected (PT-F02).
- `src/game/scripts/UI/Map/MapScreen.cs`: region caption without ClipText (PT-F03).
- `src/game/scripts/UI/Theme/UiTheme.cs` (`HeadingLining`), `scripts/UI/Puzzles/PuzzleControls.cs`: lining figures on
  dials, head room for the caption (PT-F04).
- `src/game/localization/overrides/sk_overrides.csv` (via `tools/check_rewrite.py`, 0 errors / 0 warnings, then
  `tools/extract_strings.py`): `entry.S10.001`, `look.S05.shed_door` (PT-F05, PT-F06).
- `src/game/localization/ui.csv`: `ui.inventory.combine_hint` (PT-F07); `.translation` re-imported.
- `design-doc/ISSUES.md`: PT-F01 … PT-F14.

Tests after the changes: `dotnet test src/LastBell.sln` 294 passed / 3 skipped / 0 failed; `tools/check_strings.py` OK;
`tools/check_blocking.py` 68 rooms, 0 errors, 8 warnings (the known M3-02 ones; S05 has 0); `tools/check_rewrite.py
--self-test` OK and the rewrite file OK; `--acceptance m1` 24 pass / 0 fail, `--acceptance m2` 0 failures (41 pass)
(both in a 1600x900 window, time-scale 3), and again on the final build: m1 24 pass / 0 fail, m2 41 pass / 0 failures.
S05 after G06 verified: the door leaf hovers as "Predsieň záhradnej dielne" (verify/S05_door_hover_crop.png).

## Not checked / uncertain

- **Audio**: not heard (no audio output available to me).
- **Cursor shapes**: the hardware cursor is not in PrintWindow captures; hover labels were checked, cursor images not.
- Once (305_B21.png) the hover label "Stolík s rytmickou značkou" stood at the top-left while the cursor was
  elsewhere, right after an item use. It may come from my input method (posted mouse messages); not reproduced,
  not logged.
- Hand-feel of walking: speed is good; double click on exits makes back-tracking quick. No feet sliding seen in
  stills (animation timing cannot be judged from screenshots).

## Verdict

**Clarity: good, with three soft spots.** The journal objective is almost always enough to know the next step,
looks carry the real clues (fuse, scale, rhythm panel), and the Space markers remove pixel hunting – I never had to
search for a hotspot. The soft spots: the hint order in M05 (hint 1 repeats a done step), the time node in S11 (the
painted clock invites a click, the real control is a HUD button), and early jargon ("kolíska stolového uzla").

**Fun: yes.** The prologue is a warm, well-paced tutorial; 1995 Bratislava is the strong part – real places that
look like themselves (Kamenné námestie, Miletičova, the Petržalka underpass, the Danube embankment with the castle
and Most SNP), a clear chain of small favours, and two pleasant puzzles. Adam's dry one-liners land most of the
time. Back-tracking is the main cost (the fuse trip in the prologue, the S16 ↔ Karlova Ves ↔ Ružinov loops), but
double click and map fast travel keep it short. The texts read well; I found one factual mismatch (S10) and no
broken Slovak in the first half.
