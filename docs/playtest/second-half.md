# Playtest "second half": 1995 → 1960 → 2020 Dúbravka → 1982 → 2035 Jasná → finale, epilogue, credits, postgame

Date 2026-10-05. Fresh-eyes playtest by an agent who reads Slovak. Picks up where `first-half.md` ends (the first
trip to 1960). Screenshots: `build/screens/playtest/second-half/` (numbered problem shots `01_…` – `29_…`,
after-fix checks in `verify/` and `verify_720_*`). Issues: `design-doc/ISSUES.md` **PT-S01 … PT-S28**.

## How it was played

- Debug editor runtime (`Godot_v4.7.2-stable_mono_win64_console.exe --path src/game`), natural blocking (default).
  The QA harness was used **only to get to the start**: `--replay 32` (B21 done, Adam at the Danube embankment
  S30 in 1995, the dial B22 still to set). From there everything was played by hand, through the B22 puzzle and the
  first trip to 1960, to the end of the postgame conversation with Mira. `--soft-cursor` (cursor drawn into the
  captures) and `--lines` (line ids in the log, to quote texts exactly) were the only other flags. No save files were
  written (the owner's `%APPDATA%/LastBell/saves` was not touched).
- Input: the **real OS cursor** was moved to each point (`SetCursorPos`) and the button / key / wheel messages were
  posted to the game window, so the game's own hit test and `GetGlobalMousePosition` see a real cursor; screenshots
  via PrintWindow. Another session on this machine was also driving the cursor, so every click was checked (cursor
  position before and after) and repeated on a race; hover captures were retaken when the cursor had moved.
- Main run in a **1920x1080** client; a second run at **1280x720** from C01 (2020 Dúbravka) to the first talk with
  Tóno in 1982 (journal, map, bag, markers, topic menu, era chooser).
- Before each step I wrote down what I thought the game asked, from the journal (J), hint (H), looks (right click),
  hover names, Space markers and dialogue. I did not use the walkthrough to decide what to do. Where I was stuck I
  used the in-game hints, like a player.
- Limits: **audio not heard** (no output available; the log shows the music/ambience cues switching per era, puzzle
  and finale as designed); animation timing judged from stills and short frame series only.

## Timeline (belief → action → result)

**1995 Danube embankment (S30)**

1. Journal: "nastav 3-2-6 na stojane". Belief: click the number box. Walk ~5 s from the left (long but fine).
   Puzzle modal: clear, three wheels, "Odmerať". Solved first try → B22 lines → CS03 (Ivanka 1960). **Adam stood in
   front of the box and hid the middle wheel** (01, fixed PT-S06).
2. New objective: "Na časovom uzle Dúbravskej zastávky vyber Ivanku 1960". Map → S11 stop. **Clicked the big station
   clock: Adam walked into the distance** – same as the first-half tester (PT-F10). Found the clock button in the HUD
   by hovering (tooltip "Kam sa presunieš? (T)" only after a pause). Era chooser: clear → 1960.

**1960 Ivanka pri Dunaji**

3. S31 station master Božidar: one topic → "Mladú Hruškovú? … Oto v dielni vám povie viac". Belief: find Oto's
   workshop. S32 village square: Berta, markers show the shop, hall, yard. S35 yard (storekeeper Štefan) → S36 Oto.
   **The topic panel covered both Oto and Adam** (06, fixed PT-S03); every conversation closes after one topic and has
   to be reopened (PT-S17, open).
4. Belief: show Oto the chronometer. Bag → chronometer on Oto (I01): ticket, "dierovač vám požičia Lída v sále".
   **The chronometer stayed selected afterwards** (PT-F09 / PT-S16); the selected-item chip ran into the "Podrž
   Space" hint (03 – already fixed by the first-half tester while I played, PT-F02).
5. Ticket on Štefan (I02, leather + rivets). S34 hall: Lída wants the flat fixed. Look at the clamp: "povolená skrutka"
   → hint level 1–2 confirmed "náradie z brašne" → tools on the clamp (I03) → punch. **The look says the flat lies on
   the floor, the painting shows it standing** (05, PT-S19 open). Bag: punch on leather (I04), rivets on the cuff
   (I05). S38 pump (I06) → Oto (I07, key) → door (I08) → S39 young Mira (I09): plate imprint, burnisher from Vera,
   registration form at the post office. Clear and charming chain.
6. S40 attic: wax paper (I11). S37 Vera: burnisher (I10). S39: paper on the plate (I12), burnisher on the pressed
   paper in the bag (I13) – the bag recipe was easy to guess. S33 post: clerk topic → carbon paper (I14), combine
   (I15), forms to the clerk (I16). S40: copy into the box (I17). **Mira speaks five lines in the attic but is not
   there** (08, PT-S18 open). CS04. Journal: "Vráť sa do Grobu 2020 a ukáž Mire overený odtlačok" – clear.

**2020 (Grob → Dúbravka)**

7. Era chooser at S31 → 2020 → S06 Mira: imprint (C01). New goal: photograph the school yard in Dúbravka 2020 and
   report to Tóno. S52 school front: **the notice marker overlapped the door marker** (11, fixed PT-S04). Phone on the
   building corner (D01) – the hover sentence made it obvious.
8. **Clicked the service-window exit with the phone still selected: nothing happened** (13). Right click to cancel,
   then it worked (PT-S16 open; it happened five times in this half). S56 Tóno 2020: **Adam stood in front of the
   birdhouse and the swallow** (14, fixed PT-S06); chronometer on Tóno (D02).
9. S53 → S54 cabinet: **Jana's marker sat below her laptop, a click on it did nothing** (15, fixed PT-S05); talk to Jana,
   read the 1982 log (D03) – **Adam hid the log he read** (28, fixed). Copy on the clock frame at S51 (D04) → 1982.

**1982 Dúbravka (December, snow)**

10. S57 bus stop under construction (decision 3b visible). **Adam in his autumn clothes in the snow** (16, PT-S20 open).
    S58 school: **"Štátny znak" marker in the middle of the lettering** (fixed PT-S04). S61 yard → S64 service window:
    young Tóno on his stool, Oto behind the window. Chronometer on Tóno (E01), photo of 2020 (E02): ticket for the
    depot, "Lastovička sa vracia".
11. Journal: "Vo výdajni u Marty …" – **where is the výdajňa?** The hint repeated the step I had done (PT-S26). Found it
    by exploring: the shop S62 has an exit "Výdajňa údržbového materiálu". Ticket on Marta (E03).
12. Optional Jana side quest in S60 (Q9A-C: schematic to the teacher and back) – lovely scene; **Adam's show-item
    hand lands in the girl's face** (29, PT-S24 open). **From here the journal's current main goal showed the side
    step "Voliteľne sa s Janou porozprávaj…"** under the main title until E08 (18, fixed PT-S01).
13. S63: parts on the service board (E04) – **Adam covered the board** (19, fixed). S62 Ružena: dry jar (E05), bridge into
    the jar in the bag (E06) – **"Oto skontroloval závit", Oto is not there** (fixed PT-S09). S66 Šimon: guard (E07).
    S61: jar into the niche (E08), guard around the sapling (E09) – **neither the closed niche nor the guard appeared
    until I left and came back** (fixed PT-S10). Šimon again (E10) → CS08.

**1995 → 2020 again**

14. S13 Tóno 1995: the password topic (E11) – a fine payoff. 2020 S55 yard: the linden grew, the wall stands.
    **Which item opens the niche?** I tried Tóno's note, his drawing and the phone (silent no-ops) before the service
    bag (fixed PT-S12 with a look hint). Row/column puzzle (D05), tools on the jar in the bag (D06) – **the bag then
    stayed "selected" although it had moved to the archive tab; clicks in the bag did nothing** (fixed PT-S02).
    Bridge to Tóno (D07): the emotional peak of the Dúbravka strand.
15. Grob: Ela (C02) → Roman (C03) → Ela (C04) → workshop S10: protocol into the chronometer (C05) → CS05 → 2035.

**2035 Jasná / Chopok**

16. S41 → S42 Nina (F01): a clear list of three helpers. S43 Tamara (F02), S44 Boris (F03), Jana's exhibit (Q9F –
    Adam stood in front of it, fixed), S46 Sára (F04). Ticket at the gate (J02) → CS09.
17. S67 Priehyba → Funitel (J03). S68: journal "dokonči jazdu". **I clicked the door: "Vystúpim, až keď prídeme hore"**
    – the real target is the station in the window, found by hovering (fixed PT-S07). **The opposite cabin floated
    above the rope** (fixed PT-S13).
18. S47 Rotunda: phone on the normalisation panel (F05). S48 pavilion: reader on the terminal (F06), S45 Vrbické pleso:
    chronometer on the passive stand (F07), terminal again (F08). S50 terrace: **the switch only showed its look;
    the connector is the first step** (fixed text PT-S07). Bridge (J05), switch (F09), terminal (F10).
19. S49 chamber: Viktor (topic), Lea's message (F11) → CS06 (beautiful frame). Four ports in order (F12-F15; the
    journal line "Do portov Pôvod, Hlas, Súhlas a Návrat vlož dôkazy, ktoré k nim patria" + the item names make it
    clear). Restore panel: matching puzzle 1960 / 1995 / 2020 / 2035 – first try (F16). Confirm (F17).

**Finale, epilogue, credits, postgame**

20. CS07 (ports, Viktor writing, Mira at the window) – **the port symbols in the painting are ○ ✕ □ △, the room has
    ○ + □ △** (26, PT-S21 open). Toasts stacked over the last line (25, PT-S22). Epilogue album shot for the Jana side
    quest; credits ("Ďakujeme za hranie", then the photo / sound licences, a long scroll; the X closes it).
21. Postgame: "Príbeh sa skončil … Pokračovať vo voľnom hraní". S06 restored family photo, Mira's new topic "Po
    návrate" ("Preto mám veľkú kanvicu" – a perfect last line). Journal: all main quests "Hotová", Album with
    "Znova prehrať záver" and the scene list (**action labels as scene names**, fixed PT-S08).

**1280x720 run** (C01 → 1982 Tóno): journal, map, bag, era chooser, markers, topic menu and subtitles all readable,
nothing overlaps; the narrow HUD hides the key hint; the topic panel moves left when the speakers are on the right
(verify_720_S56_topic_left_adam_right.png). The S54 laptop marker, S52 notice and S58 emblem fixes were checked here.

## Problems found

**41 problems: 23 fixed by me, 1 already fixed by the first-half tester while I played (PT-F02), 17 open.**
Not counted: one smeared duck frame in S30 (02_S30_duck_glitch.png), seen once in a PrintWindow capture, sheet
checked and fine, not reproduced.

| # | where | problem | status |
|---|---|---|---|
| 1 | Journal / pause | current main goal showed the latest *side* objective (Q9C) | fixed PT-S01 (code) |
| 2 | Bag / HUD | archived item stays selected; bag clicks do nothing | fixed PT-S02 (code) |
| 3 | Topic menu | panel covers NPC and Adam right of centre (S03, S33, S36, S44, S56) | fixed PT-S03 (code; was PT-F11) |
| 4 | S52 | notice marker overlaps the door exit marker | fixed PT-S04 (data) |
| 5 | S58 | "Štátny znak" marker in the lettering | fixed PT-S04 (data) |
| 6 | S54 | Jana's marker outside her clickable rect | fixed PT-S05 (code) |
| 7–13 | S30, S44, S49, S54, S56, S61, S63 | Adam hides the object he uses / talks about | fixed PT-S06 (data, 7 rooms) |
| 14 | S68 | locked-door look does not point at the real "finish the ride" target | fixed PT-S07 (text) |
| 15 | S50 | switch look does not mention the connector that comes first | fixed PT-S07 (text) |
| 16 | Album | scene buttons named by spoken lines | fixed PT-S08 (ui) |
| 17 | E06 | line names Oto, who is absent | fixed PT-S09 (text) |
| 18 | S61 | E08 / E09 changes invisible until re-entry | fixed PT-S10 (data) |
| 19 | Gestures | side gestures reach away from targets above Adam | fixed PT-S11 (code) |
| 20 | S55 | nothing says the niche needs the tools | fixed PT-S12 (text) |
| 21 | S68 | opposite cabin floats above the rope | fixed PT-S13 (ambient data) |
| 22 | Journal | "Nesplnená" for a quest not started | fixed PT-S14 (ui) |
| 23 | Map | era tabs not chronological | fixed PT-S15 (code) |
| 24 | HUD | selected-item chip runs into the Space hint | already fixed (PT-F02) |
| 25 | Selection | item stays selected after use, exit clicks silently ignored (5×) | open PT-S16 (Core) |
| 26 | Dialogue | menu closes after every topic | open PT-S17 |
| 27 | S40 | Mira talks in the attic but is not there | open PT-S18 (game.json) |
| 28 | S34 | "položená kulisa" vs standing flat in the painting | open PT-S19 |
| 29 | 1982 | Adam in autumn clothes in the snow | open PT-S20 (art) |
| 30 | CS07 | ✕ instead of + on the ports | open PT-S21 (art) |
| 31 | Toasts | over modals / stacked over the last line | open PT-S22 (UI) |
| 32 | Hover label | over the hint modal and the open bag | open PT-S23 (UI) |
| 33 | S60 | show-item hand in Jana's face | open PT-S24 |
| 34 | Names | "Anton Farkaš" in hovers, "Tóno" in every line | open PT-S25 |
| 35 | Hints / objective | per quest, not per step; Marta's výdajňa never located | open PT-S26 |
| 36 | S43 | English "RECEPTION" lettering | open PT-S27 (art) |
| 37–39 | S35, S51, S53/S54 | spawn against a window; exit marker on Adam's legs; no mask indoors | open PT-S28 (minor) |
| 40 | S11 node | painted stop clock is not the time node | open (PT-F10, confirmed) |
| 41 | Bag | long names cut ("Prenosný chronometer…") | open (PT-F12, confirmed) |

## What I changed (presentation / text / data only; no story, rule or puzzle change)

- Code (`src/game/scripts`): `UI/Journal/JournalScreen.cs` (main-quest objective, album scene titles),
  `UI/Menus/PauseScreen.cs`, `UI/Hud/HudView.cs` (archived selection), `UI/Dialogue/TopicMenuView.cs` (panel side),
  `World/HotspotLabelLayer.cs` (NPC marker in rect), `Living/Actors/SpriteActorVisual.cs` (gesture side),
  `UI/Map/MapScreen.cs` (tab order).
- Blocking data (`src/game/data/blocking/`): S30, S44, S49, S54, S56, S61 (use points + two state patches), S63 use /
  talk points; S52, S58 rects; `ambient/S68.json` cabin path. `tools/check_blocking.py`: 68 rooms, 0 errors,
  8 warnings (the known M3-02 ones).
- Text: `src/game/localization/overrides/sk_overrides.csv` via `tools/check_rewrite.py` (0 errors; 1 acknowledged
  warning "drop: Oto"), then `tools/extract_strings.py`: `exit.S68.to_S47.locked`, `conn.S68.S47.locked`,
  `look.S50.switch`, `action.E06.001`, `look.S55.cache`. `ui.csv`: `ui.journal.state_open`, `ui.journal.scene_cs01…09`.
  Translations re-imported.
- `design-doc/ISSUES.md`: PT-S01 … PT-S28; PT-F11 marked fixed.
- No paid generation (USD 0; nothing added to `art/spend-log.csv`). No owner reference images used.

Tests after the changes: `dotnet test src/LastBell.sln` 294 passed / 3 skipped / 0 failed; `tools/check_strings.py` OK;
`tools/check_blocking.py` 0 errors; `tools/check_rewrite.py --self-test` OK and both rewrite files OK;
`--acceptance m1` 24 PASS / 0 FAIL (1280x720, time-scale 4) on the final build; `--acceptance m2` 41 PASS /
0 failures (1280x720, time-scale 3) on the final build (run twice, both green).

## What remains (most important first)

1. **Selection after use (PT-S16 / PT-F09)** – the single most confusing thing in the whole second half: exits do
   nothing while an item is still on the cursor, with no feedback. Needs a Core / design decision.
2. **Mira off-screen in S40 (PT-S18)** and the **CS07 port symbols (PT-S21)** – visible continuity errors at story
   moments.
3. **Adam's clothes in the 1982 snow (PT-S20)** – every 1982 room.
4. **Topic menu closing after each topic (PT-S17)** and **toasts / hover labels over GUI (PT-S22, PT-S23)**.
5. **Hints per quest (PT-S26)** and the unlocated výdajňa; the painted node clock (PT-F10).

## Verdict

**Clarity: good.** The journal objective almost always told me the next step, the item names in the hover sentence
confirm a right guess, and the Space markers make pixel hunting a non-issue – I never searched for a hotspot. I got
genuinely stuck three times: the node clock in S11 (HUD button), Marta's depot in 1982 (exploration), and the niche
in 2020 (which item); a fourth time the game only *looked* stuck because an item was still selected. The journal
glitch after the Jana side quest (now fixed) would have confused anyone who did the optional scene.

**Fun: yes, the second half is the better half.** The 1960 Ivanka chain is a cosy, well-motivated sequence of small
crafts (cuff, punch, rivets, imprint, carbon copy, stamp); the Dúbravka strand across 1982 / 1995 / 2020 – the jar in
the wall, the password, the linden that grew because of a little fence, "Nečakal som. Žil som." – is the emotional
heart and pays off beautifully; Jasná 2035 adds a different landscape and a real cable-car journey; the finale's four
witnesses tie the whole game together and the matching puzzle is satisfying rather than hard. Texts read naturally;
Adam's dry humour works ("Preto funguje.", "Rydlo, ktorým sa nemá ryť"), I found one factual slip (Oto in E06,
fixed) and no broken Slovak. Weak spots are presentation: staging where Adam covers the object (now fixed in
seven rooms), and a few texts that pointed at the wrong click (fixed). Pace: about three hours of my play for this
half including note-taking; a player would need perhaps 2–3 hours, with little dead walking thanks to double click
and map travel.
