# Decisions for the product owner

> **Latest: milestone 5 (2026-10-05).** The game is complete. What still waits for you is in
> ["Status 2026-10-05 (milestone 5)"](#status-2026-10-05-milestone-5-what-still-waits-for-you) at the end.

Status 2026-10-05, after the issue cleanup. Everything that did not need you is fixed and marked in
`design-doc/ISSUES.md` ("Cleanup 2026-10-05"). What is left needs your call. Each item: the question,
the options, our recommendation (**bold**), and what it costs. Ids point to `design-doc/ISSUES.md`.

Answer with the item number and a letter, e.g. "1b, 2 ok, 3a". "ok" means: take the recommendation.

Background: 11 of 68 rooms are painted (S01-S11). About USD 0.15 per paid image call; a room takes 1-4 calls.

---

## A. Blocks background painting (please answer first)

These decide how the remaining 57 rooms are composed. Painting more rooms before the answer risks repaints.

### 1. Hotspot re-blocking (ART-BLOCK-01, ART-BLOCK-02, ART-STOP-01, ART-2035-02, ART-6082-01, LIVING-02)

Every room uses the same template layout: four prop boxes in one row high up at y 150-250, the NPC box at the
same spot, the floor band at the bottom. Real scenes do not look like that (a table, a door or a tape on the
floor cannot all sit in the top quarter of the screen).

- a) Keep the template. Painters keep the workaround: props on high shelves, houses on a raised plot, then refit.
- b) Re-block the boxes per room from the painted image (a change in `game.json`, done by the handoff owner;
  a pilot is running in parallel, results in `docs/reblock/` - the folder did not exist yet when this was written).
- c) Re-block only rooms where the template contradicts the brief (S03 tape, S51 clock and kerb, S41 robot,
  S37 bench, S54 laptop, NPC talk points).
- **Recommendation: b for the 57 unpainted rooms if the pilot keeps all tests green; S01-S11 stay as painted.**
- Cost/impact: b) no rules change (Core never reads screen positions), handoff edit of `game.json`; paintings
  become more natural and need fewer repair calls (saves ~USD 0.15-0.30 per room). a) no edit, compositions stay
  forced. c) half of each.

### 2. NPC staging per room: standing, seated or behind the counter

The briefs seat or hide some NPCs behind furniture; the NPC boxes are all standing-size. All sprite variants
already exist (free), only seated poses that do not exist yet would cost ~USD 0.12 each.

| room | NPC | brief | proposed staging |
|---|---|---|---|
| S03 | Ela | "sits by the side wall" | **standing** (S03 is painted that way); drop "sedí" from the brief |
| S13 | Tóno (25) | sits at the visitor log | **seated** (sprite exists); desk behind or left of him |
| S64 | Tóno (12) | low stool outside the window | **seated** (sprite exists) |
| S37 | Vera | on a park bench | **seated with bench** (sprite exists); painter leaves the bench spot free |
| S18 | Zita | in her kiosk | **behind the kiosk sill** (bust) |
| S25 | Fero | behind his market table | **behind the table** (bust) |
| S26 | Milada | at the sewing machine | **behind the table** (bust); seated would be +USD 0.12 |
| S33 / S35 / S62 / S65 | post clerk / Štefan / Ružena / Marta | counter or serving window | **behind the counter / window** (bust) |
| S43 / S44 / S49 | Tamara / Boris / Viktor | at a table | **behind the table** (bust) |
| S46 | Sára | service counter | **behind the counter** (bust) |
| S56 / S64 | Tóno (50) / Oto (66) | behind the service window | **window bust** (same sill in both rooms, one camera) |

- **Recommendation: the table above (follow the brief, use the free variants).**
- Cost/impact: free. The painter puts the counter/sill top where the bust's cut edge lands; one number per room
  in `data/ambient/actors.json`.

### 3. S57 Dúbravka stop in December 1982: tram or bus? (ART-DUBEXT-01)

The brief shows a red-cream tram, but trams reached Dúbravka only in 1984/1986. Options are being painted in
`docs/decisions/` (not yet present when this was written).

- a) Keep the tram as acknowledged fiction.
- b) Same camera, the tram line under construction (track bed, poles) and a bus at a temporary stop; bus sounds.
- c) A tram, but nothing is said about the line.
- **Recommendation: b** (true to the place, fits the "real places" rule; story unaffected, S57 is a travel node).
- Cost/impact: b) the S57 painting (~USD 0.15-0.45) plus a presentation-only ambience override (no `game.json`
  change needed; the handoff owner may update the brief). a/c) free.

### 4. Chorvátsky Grob scenes painted in Čierna Voda (register "district choice")

The handoff says Chorvátsky Grob; the old village has no freely licensed street photos, so S01-S10 were painted
in Čierna Voda, the larger part of the same municipality.

- a) Confirm Čierna Voda. b) Repaint in the old village from reconstruction (map data only).
- **Recommendation: a.** Cost: a) free; b) ~USD 6 and lower accuracy (no photos).

### 5. S04 shop based on a strip-mall wing (Centrum MONAR)

The real base of the window-sale shop is a wing of a small shopping centre (lower confidence in the register).

- a) Keep (already painted). b) Repaint as the small shop units at the Čierna Voda stop (no usable photo).
- **Recommendation: a.** Cost: a) free; b) ~USD 0.30-0.60.

### 6. Atlas pavilion placement (S48-S50)

The fictional Atlas pavilion is planned on the real gravel plateau ~50 m east of the Rotunda on Chopok.

- a) Confirm. b) Another spot (e.g. next to the Funitel station).
- **Recommendation: a** (keeps the real Rotunda in the window view of S49). Cost: free; decide before S48-S50.

### 7. JANA20 laptop size in S54 (ART-AGE-03)

Jana 2020 takes part by video call: a laptop on the bench showing her. The delivered laptop is about 1.7x real
size (180 px wide) so her face reads; earlier notes said 300 px.

- a) Keep 1.7x on the bench. b) Real size (face hard to read). c) Paint a larger screen/monitor into S54 and use
  the flat `screen` variant.
- **Recommendation: a**, and re-block S54.JANA20 onto the bench (with item 1). Cost: free; decide before S54.

### 8. TESLA and other brand lettering on period devices

The rules forbid logos (TESLA, TMR, GOPASS...). Period Czechoslovak devices (S16 cassette deck, 1982 radios)
carried "TESLA" on the front.

- a) No brands: unbranded period devices. b) Allow "TESLA" as period lettering.
- **Recommendation: a** (the brand is still in commercial use; the period look survives without the logo).
  Cost: free.

---

## B. Blocks release

### 9. Art licence CC BY-SA 4.0 for all game artwork

Backgrounds painted from CC BY-SA photos are adaptations, so the art is released under CC BY-SA 4.0
(NC-derived pieces also non-commercial).

- a) Confirm: all game art CC BY-SA 4.0, attribution in the credits (already built). b) Keep the art
  proprietary: replace every BY-SA / NC reference with CC0/CC BY photos and repaint.
- **Recommendation: a** (the game is free and non-commercial anyway). Cost: a) free (a licence note in the
  credits and the download page); b) new research + repainting most rooms.

### 10. QA harness in release builds (BUILD-03)

The test harness (`--replay`, `--room`...) also works in the exported game, so a player could skip the story
from the command line.

- a) Keep it. b) Only with an extra `--qa` flag in release builds. c) Debug builds only.
- **Recommendation: b** (exported builds stay testable). Cost: small code change.

### 11. Touch: the "use item on target" sentence (BUILD-04)

With a mouse, hovering shows "Use X on Y" before the click. A finger cannot hover.

- a) Tap does the action directly (as a click); the sentence shows as a short caption.
- b) First tap shows the sentence, second tap does it.
- **Recommendation: a** (fewer taps; wrong items still do nothing, as on desktop). Cost: small; mobile only.

### 12. Handoff housekeeping (handoff owner, all trivial)

- CORE-02: acceptance_tests.csv AT16 says "seven" cutscenes, there are nine.
- ART-NPC-03: assets.csv points at `actors/<ID>.webp`; the delivered format is `actors/<ID>/actor.json`.
- ART-NPC-01 / ART-AGE-01 / ART-6082-01: briefs that seat NPCs (see item 2).
- LIVING-02: NPC talk points straight below the NPC (worked around; fix with item 1).
- **Recommendation: approve the four text fixes.** Cost: none for us.

### 13. Missing "after" states of props (INT-04, ART-VAR-02)

Three props have no picture of their changed state yet: Dana's basket on her table (S04), the brass case
after the chronometer is taken (S09), the family photo fading in S06 between G11 and F17.

- a) Paint them (one local edit each). b) Leave as is.
- **Recommendation: a.** Cost: ~USD 0.45 in total.

---

## C. Cosmetic (any time)

### 14. Child heights (ART-1995-02, ART-AGE-05)

Children differ between batches: Soňa (11) 420 px = 0.82 of Adam, Jana (12) 440 px = 0.86, Tóno (12) about
0.85. Adults are all 512 px.

- a) One table: 11-12 years = 0.84 of Adam (430 px) for all children. b) Keep as is.
- Optional: adult women slightly shorter (0.95, ~486 px).
- **Recommendation: a; women unchanged.** Cost: free (a number per sprite).

### 15. "Tóno has the same height" in all eras (ART-AGE-05 a)

The bible asks for the same height across 1982 / 1995 / 2020, which cannot be literal for a 12-year-old.

- a) Same height for Tóno at 25 and 50, the child shorter. b) Literal.
- **Recommendation: a** (the three never stand side by side). Cost: free.

### 16. OTO82 likeness

Oto at 66 (S64) reads slimmer and has a thinner grey moustache than the brief's "neat full moustache, stocky"
and than Oto at 44 (`art/characters/likeness/OTO/OTO_likeness_final.jpg`).

- a) Accept (he is only seen as a bust behind a window). b) Retake the base and its face frames and idle.
- **Recommendation: a.** Cost: b) about USD 1-1.5.

### 17. Boris's "rukávové záložky" (ART-2035-03)

Painted as black sleeve garters above the elbows.

- a) Accept. b) Turned-back cuffs or sleeve protectors instead.
- **Recommendation: a.** Cost: b) USD 0.12 + USD 0.48 for a new idle clip.

### 18. Šimon's "metre dreva" (ART-6082-03)

Painted as a yellow wooden folding rule; the laths stay props of the S66 background.

- a) Accept. b) Laths under his arm.
- **Recommendation: a.** Cost: b) ~USD 0.39.

### 19. Item icon details (ART-ITEM-01, ART-ITEM-02)

The fuses show "2A"; the ORDER note carries Slovak handwriting; the keeper's note is read as a 3 x 4 grid;
the tree guard is one assembled guard.

- a) Accept all; make English icon variants only when an English version is planned. b) Change any of them.
- **Recommendation: a.** Cost: ~USD 0.08 per icon changed.

### 20. Cutscene painting choices (CUT-02)

Montage frames (CS04_2, EPILOGUE_9), the three-era blend CS08_1, the invented chronochamber look, smaller
Funitel cabins in CS09_2.

- a) Accept. b) Redo named frames.
- **Recommendation: a.** Cost: USD 0.15 per frame redone.

### 21. Music cues (AUDIO-03)

The data has one track per era. We added: tension music in S48/S49 until the finale and in CS06, the epilogue
theme in CS07, a puzzle theme and a menu theme (presentation only).

- a) Accept. b) Move the cues into `game.json`. c) Remove them.
- **Recommendation: a.** Cost: free.

### 22. Foreign crowd murmur (AUDIO-04)

The few crowd recordings (market, tourists, halls) are Spanish, Czech or English, mixed low.

- a) Accept for now. b) Record Slovak murmur locally (no CC0 Slovak recordings exist).
- **Recommendation: a.** Cost: b) a recording session.

### 23. Adam's "startled" pose (ART-ADAM-01)

The bible lists a startled pose; no action uses it.

- a) Skip. b) Make it.
- **Recommendation: a.** Cost: b) ~USD 0.60.

### 24. S11 tram as its own moving layer (LIVING-05)

The 1995 tram in S11 is painted into the background, so it cannot arrive or leave.

- a) Paint it as a separate layer with a clean platform plate so it can move. b) Keep it still.
- **Recommendation: a** in the next art pass. Cost: ~USD 0.30.

---

24 decisions: 8 block painting, 5 block release, 11 cosmetic.

---

## Answers from the product owner (2026-10-05)

- **1. Hotspot re-blocking: b, for ALL 68 rooms** — the 57 unpainted rooms and S01-S11 are re-blocked naturally
  and repainted (S03/S05 pilot accepted). Natural blocking becomes the default once every room has a blocking file.
- **2. NPC staging: follow the brief** — the proposed staging table above is accepted.
- **3. S57: b** — bus at the Dúbravka stop in December 1982 with the tram line under construction; bus ambience
  (presentation-only override, game.json untouched).
- **4-8: recommendations accepted** — Čierna Voda for the Chorvátsky Grob scenes, S04 strip-mall base kept,
  Atlas pavilion on the plateau east of the Rotunda, JANA20 laptop as recommended, no TESLA lettering.

## Control changes from the product owner (2026-10-05) — override CODING_AGENT_START.txt where they differ

1. **Walking is a bit faster** (natural, not rushed); the walk animation playback follows the speed so feet do not slide.
2. **Double-click skips the walk:** double-click on a hotspot, NPC, exit or floor puts the hero at the destination
   at once and continues exactly as if the walk had ended (conditions re-checked on arrival, as before).
3. **Hover label at the cursor, not in the bottom HUD:** the contextual action name appears next to the (big) cursor
   in large outlined text, like the Polda games (reference: `art/source/owner_refs/ui_rG0q3FH.png`, local only).
   The selected-item rule stays: an item-use label appears only when the combination is executable.
4. **Custom, bigger cursor**, painted in style A, contextual by target kind (default/walk, use/take, talk, exit with
   direction, item selected), scaled with resolution.
5. **Space is hold-to-show, not a toggle:** while Space is held, small round markers appear on all visible
   interactive hotspots (including atmospheric ones) — markers only, no text labels; releasing Space hides them
   (reference: `art/source/owner_refs/ui_cOw4kTJ.png`, local only). Touch: two-finger hold shows them.
6. **Using items from the bag (owner, 2026-10-06: "you misread my instruction about using stuff from inventory"):**
   when the player picks an item in the open bag (e.g. "Servisná brašna") and right-clicks anywhere outside the bag
   panel, the panel closes and the item stays selected for use in the scene; a further right click (panel closed)
   cancels the selection as before. A left click into the scene outside the panel also closes it and resolves normally
   (a valid target uses the item; an invalid one stays a complete no-op that keeps the selection, no refusal line).
   A right click inside the panel keeps its behaviour (look at the item). **With an item selected only valid
   combinations come up:** the hover label appears only over a target where Core says the item rule is executable
   (any other hotspot, NPC or exit shows no label, the cursor stays the item cursor), Space / two-finger hold shows
   markers only on those targets, and Tab cycles only them. Without a selection every visible target hovers, gets a
   marker and a Tab stop as before (owner's example: 6 objects on screen, no selection: all 6; item selected: only
   the valid combination). Overrides the handoff's AT06 wording "the object name stays" for invalid pairs.
7. **Far places are reached through their transport hub; the map shows regions (owner, 2026-10-06:** "Dúbravka
   reachable by bus from the Čierna Voda bus stop", "map regions"**).** Applied as a travel overlay
   (`src/game/data/content_ext/travel_ext.json`, game.json untouched; Core README section 13, ISSUES TRAVEL-01).
   The map shows the regions of an era first, then the rooms of the chosen region; fast travel is free inside a
   region, another region is reached only through its hub (bus stop, tram stop, cable car station).
   **Owner override 2026-10-06 (item 8): the regions-first view and the hub-only fast-travel rule are replaced** by one
   screen with every region and a direct one-click fast travel to any visited room; the hubs stay where the physical
   rides (bus, tram, cable car) enter a region, and a first visit is still made physically. Changes per era:
   - **2020:** the car transition S02 (Ulica medzi plotmi) <-> S51 (Dúbravská zastávka 2020) is removed (exits
     S02.to_S51 and S51.to_S02, connection S02-S51). New bus S07 (Čierna Voda pri výveske, the real bus stop) <->
     S51, travel `bus`: exit "Autobus do Dúbravky" at the kerb by the bus-stop sign, back "Autobus do Čiernej Vody"
     at the platform end; first ride each way plays Adam's lines from the C1 draft in the stop he leaves, then a
     fade, the destination card ("Dúbravka" / "Autobusom · Dúbravská zastávka v roku 2020") and the bus sound
     (reduced motion: the same fade and card, shorter). Regions: Chorvátsky Grob (S01-S10; Čierna Voda is part of
     the municipality, hub S07) and Dúbravka (S51-S56, hub S51). The walk S03 <-> S07 stays (inside the region).
     Hint `quest.M11A.hint.1` names the bus (sk_overrides, from the C1 draft).
   - **1995:** no change: every cross-region link already joins two hubs (Dúbravka S11 tram stop <-> Karlova Ves
     S19 platform <-> Staré Mesto S21 Kamenné námestie <-> Ružinov S25 / Petržalka S28). Regions = the districts,
     hubs S11, S19, S21, S25, S28.
   - **1960:** one region (Ivanka pri Dunaji, hub S31 railway stop). **1982:** one region (Dúbravka, hub S57).
   - **2035:** no link change (cable car S41 -> S67 Priehyba -> S68 Funitel -> S47 Chopok). Regions: Jasná (S41-S46:
     Biela Púť, Grand Jasná, Vrbické pleso are one walkable area, hub S41 lower station), Priehyba, Funitel, Chopok.
   - Walkthrough: `walkthrough.json` still says S02 -> S51 (steps 52, 67, 70); Core tests and the Godot replayer
     recompute such a hop under the overlay (S02 -> S03 -> S07 -> bus S51). Revert: empty `travel_ext.json`.
8. **Direct fast travel to every discovered place (owner 2026-10-06:** "make it possible to travel directly to any
   discovered location, not via 2 steps"**).** Overrides the hub rule and the regions-first map of item 7.
   - Rule (Core `Navigation.CanFastTravel`, `ViewBuilder.Map`): from the map, ONE click on any visited room of the
     current era travels there, in any region, with no stop at the region's hub. Unchanged: same era only, visited
     only (the first trip into a place, e.g. the bus S07 -> Dúbravka, is still made physically), and the room must be
     reachable over open connections (a `requires_done` gate on every route keeps it unavailable, AT12).
     `Navigation.IsRegionTarget` is gone; the load-time region rule (a cross-region connection joins two hubs) stays.
   - Map (`UI/Map/MapScreen.cs`): one screen per era with every region as a section (name, "Tu si" or the transport
     into it, "Miesta: x z y") and its discovered rooms as nodes (undiscovered rooms are not drawn; a region with no
     visited room is one grey "Neznáma oblasť" card); small regions sit side by side, so 1995 (5 regions) fits one
     1920x1080 screen. The "Späť na oblasti" step is gone.
   - Transport card: a fast travel that leaves the region shows the card of the first link out of it ("Autobusom",
     "Električkou", "Kabínkovou lanovkou" + destination; the 1995 map-transition links count as tram / bus, the
     Funitel as the cable car) instead of a plain fade (`WorldStage.FastTravelCardStyle`). Story cable rides keep their
     own staging.
   - Checks: Core `ContentOverlayTests.Fast_travel_reaches_every_visited_room_of_the_era_in_one_step_in_any_region`;
     acceptance `TR03_map_one_screen_one_click_to_any_visited_room` (replaces `TR03_map_regions_first_hub_only_fast_travel`),
     AT12 and the keyboard tour without the region step. Screenshots: build/screens/nav_ui/.
9. **Exits sit where the painted way leads, on the side of travel; no two places side by side on one edge (owner
   2026-10-06:** "the location navigations are often a bit illogically placed [2 different location navigations very
   close to each other on the same direction while no on the other exit of the screen] … revise the location chain so
   that the direction make more sense"**).** Full audit, rules and per-room changes: docs/navigation/EXITS.md (table
   generated by `tools/exit_audit.py`); ISSUES NAV-EXITS-01.
   - Rules: an exit is on a painted way (door, gate, path, road edge, stairs, vehicle); its side (left / right edge, up =
     into the picture, down = towards the viewer) matches the direction of travel and may be named in the blocking
     (`"side"`); two places never share one edge side by side (separate them by kind or change the chain); leaving out of
     the right edge arrives at the target's left edge (doors exempt); the real bearing is advisory.
   - Chain (2020 Chorvátsky Grob, `travel_ext.json`): street S02 → park S03 → shop S04 → bus stop S07 (the S03 ↔ S07 map
     transition is replaced by the walk S04 ↔ S07); the pond S08 is reached from the park S03 beside it (S03 ↔ S08)
     instead of from the bus stop 1.3 km away. Region and hub unchanged.
   - Layout: S02 park on the right; S03 pond right / shop towards the viewer / street left; S04 park right, bus stop left
     (the camera faces south); S07 the far platform leads to the shop; S18 and S62 (one picture, 1995 / 1982) school side
     left, stop right (continuity with the yard S17); the stop ramps S11 / S51 / S57 lead down; S21, S42, S52, S19, S25
     name their doors and depth paths `up` so they no longer read as edge exits beside the real ones; S42 → S41 and
     S61 → S64 towards the viewer.
   - Arrival: through an exit Adam appears at the new room's matching return exit (edge or door) and walks a step in during
     the fade-in (`World/ExitSides.cs`, `Room.HeroSpawn` / `FinishArrival`, `WorldStage` passes the room left through an
     exit; map fast travel, portals and special transitions use the spawn). Cursor arrow and Space badge follow the side.
   - Checks: `tools/check_blocking.py` warns about exits crowding one edge and about edge-to-same-edge returns, validates
     `side` / `arrival`; `tools/exit_audit.py --check`. Screens: build/screens/exits/. No paint edit was needed (USD 0).
   - Text keys of the new exits (`exit.S04.to_S07`, `exit.S07.to_S04`, `exit.S03.to_S08`, `exit.S08.to_S03`,
     `conn.S04.S07`, `conn.S03.S08`) come from `python tools/extract_strings.py` (text owner).
10. **The inventory is "Inventár", not "Brašna" (owner 2026-10-06:** "dont have brasna inside brasna, perhaps call it
    just inventar"**).** The panel title, the HUD button tooltip, the help / tutorial lines, the empty-panel text, the
    "pribudlo / ubudlo" notices and the ui.csv hint steps that meant the panel ("V brašni spoj …" -> "V inventári
    spoj …", D06 "V inventári použi servisnú brašnu …", C05 "… musí byť v inventári") say "inventár"; the item
    "Servisná brašna" keeps its name. 20 rows of `localization/ui.csv` (sk), nothing else. World / dialogue lines in
    Adam's voice that mention his bag stay as written (text owners).
11. **No permanent outline on valid targets of a selected item (owner 2026-10-06:** "if object combination matches,
    now also rectangular border is added to viable target... only on hover or space press it should indicate"**).**
    `HotspotLabelLayer` no longer draws the rect outline around every target where the selected item has a use. The
    valid targets show only (a) on hover: the item-action label at the cursor, (b) while Space is held: the round
    markers on the valid targets only. Everything else of item 6 stays (valid-only hover label, markers and Tab stops;
    the Tab focus outline is the keyboard focus, not an item hint). Checks: m2 `AT06_labels_with_item_only_valid_targets_marked_no_outline`
    (was `..._outlined`), travel set `NAV04_inventar_title_and_no_item_outline`.
    QA side note: in a hidden windowed QA run (tools/qa_godot.py, no `--warp-mouse`) the world input, hover label and
    soft cursor now use the position of the last mouse event (`QaWindow.UseEventPointer`; players' runs never), so
    raw world clicks land and the hover label shows in evidence frames (TR02 no longer falls back to Tab + Enter).

**Status 2026-10-06 (item 7): implemented** (ISSUES TRAVEL-01): Core overlay loader + region rule
(`ContentOverlayTests`), `WorldStage` ride (first-ride lines, transport card, `travel_bus` sound), `MapScreen`
regions-first, acceptance m2 TR01-TR03 and AT12 through the region view. Screenshots: build/screens/travel/.

**Status 2026-10-06 (items 8, 10, 11): implemented** (ISSUES TRAVEL-02, UI-INV-01, INT-10): one-click fast travel to
every visited room with the transport card, the one-screen map, "Inventár", no item outline. Core tests, check_strings
(ui rows), acceptance m1 34/34, m2 46/46 (run with its own APPDATA: a parallel m2 of another agent shares the
`m2_accept_cs` save slot and broke AT16 twice), travel TR01-TR03 + NAV04 (headless and hidden window), `--play-all`
routes A, C7, K headless exit 0 (K: 0 blockers); screenshots build/screens/nav_ui/. Open at that time, not from this pass:
`ContentOverlayTests.Every_overlay_text_has_its_key_in_the_tables` / check_strings wait for the world.csv rows of item 9's new exits.

**Status 2026-10-06 (item 6): implemented** (ISSUES INT-09): `InteractionController` (drawer close on a scene press,
valid-only hover and Tab), `HotspotLabelLayer` (valid-only markers); acceptance m1 `RunSelectionControlChecks`, m2 AT06.
Screenshots: build/screens/selection/.

**Status 2026-10-05: implemented** (ISSUES INT-08): walk speed x1.25 (Settings: walk speed 100/125/150 %), double click / double tap / double Enter / Shift+Enter skip, hover label at the cursor, painted contextual cursor set (art/ui/cursors, USD 0.12), Space hold-to-show markers (two-finger hold on touch, HUD eye press-and-hold). Screenshots: build/screens/controls/.

---

## Status 2026-10-06 (verification and release pass): what still waits for you

The game is complete, tested and rebuilt (docs/MILESTONE5.md; owner summary and download in docs/RELEASE.md). All 30
handoff acceptance tests pass, AT19 (the whole game with the keyboard only) included. Answered or done since the last
status, so no longer asked: items 1-8, the control changes, N2 a (the selection clears after a successful use), N3
(hints follow the step), N6 (imgur permission, applied as recorded in art/feedback), N11 (Mira walks into the attic),
N12 (CS07 symbols, Adam's winter coat, RECEPCIA), N13 (conversations stay open, Esc once = one line, the painted
stop clock is the time node), the S34 part of N10, and the Jasná-in-winter and Ivanka-1962 decisions.
**Only the items below still need you.** Same answer format as before ("9 ok, N1 1.0.0, N9 ok ..."). **Bold** = our
recommendation.

### Needed before a public release
- **9. Art licence:** the credits list every source, but nothing yet says the game's art is CC BY-SA 4.0, and the two
  carl_eric photos (CC BY-NC-SA 2.0; rooms S17, S18, S55, S61, S62, S65, S66, S69 and frames CS02_2, CS08_1, CS08_2, EPILOGUE_11) make
  those parts non-commercial. **Confirm a**; we then add the licence line from RELEASE.md to the credits and the
  download page.
- **10. QA harness in release builds:** built as option **c** (debug and QA builds only; the release exe ignores
  `--` arguments, verified again on the 2026-10-06 build). Please confirm c.
- **N1. Release number:** the menu and the exe now both say 0.1.0 (one source, project.godot). **Keep 0.1.0** for
  test builds and call the first public release **1.0.0**, or tell us another number.
- **N2 b. Exit click while an item is deliberately kept selected:** today it does nothing (the handoff's no-op
  rule for invalid item uses). b) drop the selection and walk; c) keep. **b** (a small Core rule change).
- **N4. Signing and ids:** a Windows code-signing certificate (removes the SmartScreen warning; optional for a free
  game), the final bundle / package id (placeholder `eu.lastbell.poslednyzvonec`), and for the ports an Apple
  Developer account (USD 99/year) and an Android release keystore (docs/BUILD.md).

### Places (owner location feedback, still open)
- **N5. Entry hall of ZŠ Sokolíkova (S13 1995, S53 2020, S59 1982):** painted from type references until you
  describe the real hall (layout, stairs, porter's window, doors, floor and wall colours). Repaint of the L_HALL
  family afterwards: about USD 0.45-0.90.
- **N7. S57 data:** decision 3b (bus, tram line under construction) is in the game as a presentation override;
  game.json `art_brief` / `ambience` of S57 still say tram (handoff owner, ART-DUBEXT-01). The same applies to the
  displayed dates of the two later decisions (game.json still says 2035-06-06 and 1960; ISSUES ART-JASNA-WINTER,
  TEXT-IVANKA-1962): update game.json when convenient, nothing in play depends on it.

### Texts
- **N8. Renames made in the rewrite, please confirm:** "Juro Kazeta", "Paliho opravovňa", the item names
  "Textilný izolačný návlek", "Adaptér s konektorom bez izolácie", "Mapa uzlov bez fólie", "Priehľadná fólia K-17",
  "Úplná mapa meracích uzlov", and "Drevená lastovička" (S64). **ok**.
- **N9. Tóno's name** (PT-S25): hover labels and topic headers say "Anton Farkaš", every line says Tóno.
  **"Tóno (Anton Farkaš)"** on first meeting, then "Tóno".
- **N10. Smaller text questions:** Lea's speaker label (keep "Lea Kormanová (správa z roku 2032)" or **"Lea
  Kormanová (2032)"**); should the F08 goal name the bridge too (**yes**, it is the step players miss); two things
  called "Servisná doska" (S63 workbench and the wall board; **rename the workbench "Pracovný stôl"**); the map
  label "Okno školníckej dielne v roku 1982" differs from its room name (**make it equal**).
- **N14. First goal in the workshop** (PT-F14): "Oprav kolísku stolového uzla ZVON" appears before anything explains
  "kolíska"; the objective is strict game.json text. **Add one S10 first-entry line that points at the cradle**
  (text overlay, no story change).

### Items 11-24
Unchanged and cosmetic; they can be answered any time. Item 13 is done except the S09 case (it stays closed; the
chronometer is inside, so nothing visible changes).

## Orchestrator decisions after the playtests (2026-10-05) — reversible, within the owner's rules

- **Selection clears after a successful item use** (standard adventure behaviour; the handoff's no-op rule for
  *invalid* item clicks stays). The open question of exits clicked with an item selected is asked separately.
- **Hints follow the step, not only the quest:** hint 1/2/3 refer to the next undone action of the quest.
- **Conversations stay open** after a topic until the player closes them or no topics are left.
- **The painted S11 clock is the time node** (clicking it opens the era chooser, like the bottom-bar clock).
- **Guest speakers walk in briefly** as the actions' staging rules describe (e.g. Mira 60 in the S40 attic).
- **Adam wears a winter coat outdoors in December 1982**; CS07 port symbols repainted to match the room.
- **Toasts wait until lines end and never cover open screens; the hover label hides over UI panels.**
- **Esc skips the current line; Esc twice quickly skips the whole sequence.** Menu shows the game version 0.1.0
  (content data version stays internal).

## Jasná 2035 is in winter (owner 2026-10-06)

Owner: "for Jasna I'd prefer winter settings ... so redraw your art that jasna is in winter". Binding for every Jasná
2035 image (rooms S41-S50, S67, S68 and the cutscene / epilogue frames set there):

- **Winter, clear and cold:** deep snow on roofs, slopes and the forest, groomed ski pistes with small distant skiers,
  snow banks beside the cleared paths, Vrbické pleso frozen under snow (swept black ice in the middle), clear cold
  light (or light snowfall), icicles, breath steam; the cable cars run (cabins on the ropes).
- **Displayed date: 6 February 2035** (presentation override of `era.2035.date` in `src/game/localization/ui.csv`;
  `game.json` `eras[].date` stays 2035-06-06 for the handoff owner, ISSUES ART-JASNA-WINTER).
- **Same cameras and blocking:** every room is an edit of its accepted summer painting (`art/tools/winter_jasna.py`),
  so hotspot rects, walk polygons, NPC staging, anchors and state patches stay valid; interiors keep their pixels
  outside the windows and the added winter details. Summer masters stay in `art/` only (`*_summer.webp`).
- S41 is painted separately from the owner's new references.
- **People dress for winter.** Adam wears his winter coat and mustard scarf (the `*_coat1982` sheets) in the Jasná
  exteriors S41, S42, S45, S48, S50, the open Priehyba station hall S67 and the unheated Funitel cabin S68
  (`data/ambient/actors.json` `hero_coat2035_rooms`, `ActorStaging.HeroWearsCoat`); the heated interiors keep the
  jacket, as in 1982. The CS09 frames already show him in the coat. Outdoor NPCs get an actor.json variant `winter`
  staged in the natural blocking (`art/tools/npc_winter.py`: re-dressed, same pose and default face pixels, so the
  default blink and mouth frames apply): NINA (S42, closed coat, scarf, gloves, boots), IVAN (S67, padded parka,
  beanie, gloves), TURISTA (S68, padded ski jacket and bobble beanie instead of the bucket sun hat). ROBOT (S41)
  has its `snow` variant from the S41 painting. Indoor NPCs keep their clothes.
- **Winter life** (`art/tools/winter_ambient.py`, `w_*` layers in `data/blocking/ambient/<room>.json`): the cable cars
  run (the painted cabins of S42, S48 and S50 lifted off clean plates and riding their ropes), small skiers slide
  down the pistes and a snowcat grooms the slopes far away, snow blows off roofs and ridges, light snowfall varies per
  room (clear with diamond dust in S42 / S45, flurries in S48 / S50 and outside the interior windows), Adam's and
  the outdoor NPCs' breath steams in pulses (`ParticleLayer` `follow: "hero"` / `"npc:<id>"`, `pulse_s`). Reduced
  motion: crossing things hide, cabins freeze, breath hides.
- **Texts:** only "Hladina plesa" became "Zamrznuté pleso" (`docs/writing/out/jasna_winter.csv` -> sk_overrides.csv);
  no other Jasná text names summer. The later 2035 writing pass (C4) may add winter touches.

## Ivanka is shown as June 1962 (owner 2026-10-06)

Owner: "move Ivanka to the year 1962" (so that the new Ivanka character Zuzana, born 1955, is 7 when Adam meets her in the
manor park; docs/story/ZUZANA.md). Binding for everything the player sees of the Ivanka chapter (rooms S31-S40):

- **Displayed date: 6 June 1962** (`era.1960.date` = "6. júna 1962", new `era.<year>.year` keys in ui.csv with
  `era.1960.year` = 1962). Only the presentation changes: the era id stays **1960** everywhere inside (game.json
  `eras[].year`, rooms, conditions, saves, the P04 solution value, ids MIRA60 / VERA60, `music/1960.ogg`), ISSUES
  TEXT-IVANKA-1962.
- Every visible era year goes through `TextKeys.YearOf` / `TextService.EraYear` (era card, journal time map and person
  labels, map tabs, era chooser, save slots); texts say 1962 (36 rewritten keys, `docs/writing/out/ivanka1962.csv`).
- **Ages in June 1962:** Mira 22, Vera 24, Oto 46 (66 in 1982, so "zostarol o dvadsať rokov"); other Ivanka people +2
  where a text states an age. Birth years and the other eras do not change (Mira is still 55 in 1995 and 80 in 2020).
- **Spans:** Mira is 13 years younger than Adam; the box held 58 years until 2020 ("skoro šesťdesiat rokov"); the
  registered paper must last 73 years until 2035 ("o sedemdesiattri rokov").
- **Painted dates** follow: the form icons REGFORM / REGDOUBLE / REGISTERED (6. 6. 1962), the S33 wall calendar, the
  CS03_1 chronometer wheels and the EPILOGUE_6 calendar show 1962.
- Writers: GLOSSARY.md section 6.3 and glossary.json carry the 1962 facts (`check_rewrite.py` enforces them).

## Owner answers (2026-10-06, afternoon)

- **Version** stays **0.1.0** for now.
- **School entry hall (S13/S53/S59)**: the type-reference look is fine; **remove the caretaker's desk** in all eras.
- **S03 Lúčny koník**: add a generic wooden grasshopper (clearly not the real sculpture) — approved.
- **Podlubie (S17/S55/S61)**: it only leads to the school's small inner yard → **no-go** (not walkable, no exit).
  The way to the panel blocks (S18 / S62) is **to the right of the school**.
- **S30**: match cutscene frame CS03_1 to the Starý most view and rename the room to
  „Merací stánok na Starom moste“ — approved.
- **Zuzana**: appears only in 1962 (and possibly 1995 Dúbravka, details pending with the owner); no appearance or
  reference to her later life in 2020 or 2035; the MIRA20 topic about her later life is dropped from the design.

## Difficulty settings (owner request 2026-10-06, queued after the Content v2 apply)

The current hints end in a step-by-step solution. Owner: standard difficulty (default) must give "some sort of
hint, but not a full walkthrough". Plan (orchestrator proposal, owner may adjust):
- **Ľahká (Easy):** today's 3 hint levels incl. the exact step; puzzle hint can fill in the answer.
- **Štandardná (Standard, default):** 2 levels, never the solution — (1) a nudge in Adam's voice (what is missing / who
  might know), (2) where to look (place or person), without naming the item combination or action; puzzle hints
  explain the rule, never fill in.
- **Ťažká (Hard):** only the level-1 nudge, available after a few minutes without progress; no puzzle help.
- Chosen at New Game, changeable in Settings; journal goals stay as they are; Space markers on all levels.
- New per-step nudge / place texts via the writing method and the owner's approval page before they go live.
- Implemented 2026-10-06 (engine + UI, Core `Rules/Hints.cs`, README § 8): Hard's nudge after 180 s without a new done
  action (play time; resets on load), Hard gives no help on a puzzle step, the difficulty is saved per save file (old saves
  = Standard). Until the texts are approved Standard shows the Easy level-1 / level-2 texts as fallbacks; the keys to
  write are `hint.nudge.<step>` / `hint.where.<step>` (docs/writing/out_v3/hint_steps_todo.csv), the UI strings are drafts
  in docs/writing/out_v3/ui_difficulty.csv.

## Adam never knows what he has not learned (owner 2026-10-06)

Example: in B06 Adam said „To je robota pre Jura z kazetového klubu v Ružinove.“ before anyone mentioned Juro. Fix
(queued after the Content v2 apply): Pali mentions Juro in B05 („S páskami čaruje Juro Kazeta v klube v Ružinove.“);
B06.002 becomes „…Kazetu by to chcelo opraviť, ale ako ju zhlasním?“ + „Pali spomínal Jura z kazetového klubu
v Ružinove. Ten by to mohol vedieť.“ General rule for WRITING_METHOD.md: every person, place or item Adam names must
have been introduced to the player earlier in every legal order of play; a knowledge-state audit runs over all eras.

## Round 2 approved and applied (owner 2026-10-07)

On his approval page (`docs/writing/approval/changes_r2.json`, scenes `R2-…`) the owner answered "i guess ok" with no
card marked: every round-2 text is approved as drafted. Applied on 2026-10-07 (docs/MILESTONE5.md "Round 2 applied"):
the knowledge fixes (`docs/writing/out_v3/knowledge.csv` -> sk_overrides.csv / ui.csv, `knowledge_ext.json` ->
dialogue_ext.json, the superseded C1-C4 entries of the same 13 ids removed first), the 268 Standard / Hard step hints
(`hints.csv` -> ui.csv `hint.nudge.*` / `hint.where.*`; B07's hint together with the B05 / B06 Juro fix) and the 24
difficulty UI strings (`ui_difficulty.csv` -> ui.csv; the code fallbacks follow them). The open questions of
`docs/writing/review_gpt/out_v3_decisions.md` § 5 are taken as answered by the approval: B06.002 keeps „zhlasním“, the
written props on the S30 stand and under the S45 bench sign stay, M08's title is „Dielňa v Ivanke“. The rule "Adam
never knows what he has not learned" is still to be added to design-doc/WRITING_METHOD.md by the owner (only he
changes that file). The two promised cosmetic fixes went in at the same time: little Zuzana (S37) stands still while
anyone talks to her and hops again when the conversation ends; S69 is relit to the S18 sunset (USD 0.15).

### Owner answers 2026-10-08

- **N9 / PT-S25 Tóno's label:** hover labels and topic headers say **Tóno** in every era (char.TONO*.name and the
  three hotspot names, sk_overrides.csv).
- **N2 b, exit click with an item selected:** stays as it is (nothing happens).
- **N14 / PT-F14 first workshop goal:** reworded so it no longer names *kolíska* / *stolový uzol* before the S10 look
  explains them: quest.M02.goal „Zisti, prečo sa odpojený ZVON v záhradnej dielni ozýva, a rozchoď ho.“, G07
  objective/journal „…servisnú časť prístroja ZVON.“
- **Publishing:** GitHub Releases for now; release the current build as v0.1.0.
- **Known flaws** (S69 people in daylight colours, non-Slovak crowd murmur, far exit labels): accepted for now.
- **Next:** ports to macOS, Linux, Android and iOS (one agent); English translation drafted by Claude and checked by
  Claude without fal.ai (another agent), text in art "variablized" where sensible.

### Guidance by difficulty (owner 2026-10-08)

- Owner: "the game is still hinting way too much in the texts and dialogues [middle difficulty]… I don't want
  'metronóm má Emil' and stuff like that". Decision: Standard and Hard show less revealing `.std` versions of
  dialogue lines, goals and journal entries (design-doc/WRITING_METHOD.md "Guidance by difficulty"); Easy keeps the
  explicit texts. First pass: 163 variants over all eras (docs/writing/guidance/), waiting for the owner's approval.
  **Approved 2026-10-08** ("yup, good adjustments"): the 163 variants are live
  (`src/game/localization/overrides/guidance_std.csv`), 32 of them with their own voice take.

### English and version 0.2.0 (owner 2026-10-08)

- **English** needs no owner approval for now ("make the translations using your model so we don't use confirmation
  for now"): translated and checked by Claude, LanguageTool en-GB on this computer, no fal.ai
  (docs/translation/README.md). Voices stay Slovak with English subtitles; painted signs stay Slovak.
- **English place names** ("translate the location names too … some like Ružinov turn into Ruzinov … for others like
  Lúčny koník find a proper English name"; the list was shown and approved: "all good, go ahead"): real geographic
  names lose their diacritics (Dubravka, Ruzinov, Petrzalka, Jasna, Cierna Voda, Chorvatsky Grob, Biela Put,
  Sokolikova, Mileticova); names with a meaning are English (the Old Town, the Old Bridge, Kamenne Square, Lake
  Vrbicke, the Grasshopper playground, LEAL Court, Light photo studio). People's names keep their Slovak spelling
  (`tools/en_place_names.py`).
- **Version 0.2.0** on GitHub Releases for Windows, Linux and macOS (approved with the same answer): English, the
  Standard / Hard texts and the voiced look texts.
- **Dezider's voice** stays as it is (owner: "whatever… it does not matter"). No ethnic caricature voice and no clone
  of a real person's voice without consent.
- **Android** build and touch controls: a separate agent, after the 0.2.0 desktop release.

### English names of the characters (owner 2026-10-09)

- **Request:** "in english - also change the character names .. Bodka => Dotty ... and come up with English sounding
  names". Only **Bodka → Dotty** is the owner's own choice; every other name was chosen by Claude and has **not been
  shown to the owner yet** (English needs no approval for now, see above).
- **Rule:** the natural English form of a first name where there is one (Tóno → Tony, Jana → Jane, Fero → Frank,
  Viera → Faith); a name that already reads as English stays (Adam, Mira, Nina, Vera, Boris …); surnames by meaning
  where that gives a common English surname (Hruška → Perry, Kováč → Smith, Mlynár → Miller), else by sound; Béla →
  Barnaby, Očko → Blinky; no two characters share a first name; no diacritics. This replaces "People's names keep
  their Slovak spelling" of 2026-10-08. Full table: docs/translation/README.md "English names of people";
  `tools/en_person_names.py`.
- **Scope:** English texts only (896 of 5,255). Slovak texts and the Slovak voices are unchanged, so with English
  subtitles the voice says *Tóno* and the subtitle *Tony*. Real people (credits, photo sources), brands and place
  names are not renamed. Zuzana is *Susanna* (*Susie* where the Slovak says Zuzka); nothing else about her changed.
- **All platforms** (owner, same morning: "those english sounding names are for all platforms of cours"): the names
  are in the one English text table every platform ships, so Windows, Linux, macOS and Android all get them with
  version 0.2.1. 0.2.0 on GitHub still has the Slovak names in English.
- **Open for the owner:** the names themselves (any of them can be changed in one line of the tool), in particular
  Mira and the other names left as they are, *Aloysius* for Alojz, *Jerry Cassette* for Juro Kazeta, and the family
  name *Perry*.

### Android: first test on a phone, version 0.2.1 (owner 2026-10-09)

- **Report:** "first issue i see is that that none of the things that are meant to be scrollable is actually scrollable
  [android]". Reproduced on the emulator and fixed (design-doc/ISSUES.md ANDROID-12; docs/PORTS.md "Touch controls"):
  a sliding finger scrolls a list wherever it went down, a tap is still a tap. Sliders follow a slide along them and
  no longer jump when a finger passes over them.
- **Decided by Claude along the way** (touch mode only, the PC is unchanged): the settings tabs stand in a column on
  phones (ANDROID-13); no hover highlight on touch screens; the version is **0.2.1** (Android version code 3), so the
  owner can tell the new APK from the one already on the phone.
- **APK size** (owner: "is it normal for game on android to have 0.5gb?"): answered, no change. The pictures are
  stored in the GPU's own format, which costs disk space and saves memory (ISSUES ANDROID-04); the choice waits for
  the test on a real phone.
- **Still waiting for the owner:** the 11 Slovak touch texts (docs/writing/out_v6/ui_touch.csv), the test of 0.2.1 on
  the phone, and whether 0.2.1 is published on GitHub.
