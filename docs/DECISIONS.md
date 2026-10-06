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
   region, another region is reached only through its hub (bus stop, tram stop, cable car station). Changes per era:
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

**Status 2026-10-06 (item 7): implemented** (ISSUES TRAVEL-01): Core overlay loader + region rule
(`ContentOverlayTests`), `WorldStage` ride (first-ride lines, transport card, `travel_bus` sound), `MapScreen`
regions-first, acceptance m2 TR01-TR03 and AT12 through the region view. Screenshots: build/screens/travel/.

**Status 2026-10-06 (item 6): implemented** (ISSUES INT-09): `InteractionController` (drawer close on a scene press,
valid-only hover and Tab), `HotspotLabelLayer` (valid-only markers); acceptance m1 `RunSelectionControlChecks`, m2 AT06.
Screenshots: build/screens/selection/.

**Status 2026-10-05: implemented** (ISSUES INT-08): walk speed x1.25 (Settings: walk speed 100/125/150 %), double click / double tap / double Enter / Shift+Enter skip, hover label at the cursor, painted contextual cursor set (art/ui/cursors, USD 0.12), Space hold-to-show markers (two-finger hold on touch, HUD eye press-and-hold). Screenshots: build/screens/controls/.

---

## Status 2026-10-05 (milestone 5): what still waits for you

The game is complete and tested (docs/MILESTONE5.md; owner summary and download in docs/RELEASE.md). Items 1-8 and
the control changes are answered and built. **Items 9-24 above have no answer yet.** Below is what we did meanwhile,
plus new questions from the playtests, the location feedback and the text rewrite. Same answer format as above
("9 ok, 13 ok, N1 a ..."). **Bold** = our recommendation.

### Needed before a public release
- **9. Art licence:** still open. The credits list every source, but nothing yet says the game's art is
  CC BY-SA 4.0, and the two carl_eric photos (CC BY-NC-SA 2.0, rooms S17, S18, S55, S61, S62, S65, S66 and frames
  CS02_2, CS08_1, CS08_2) make those parts non-commercial. **Confirm a**; we then add the licence line from
  RELEASE.md to the credits and the download page.
- **10. QA harness in release builds:** built as option **c** (debug and QA builds only; the release exe ignores
  `--` arguments, verified again in milestone 5). The QA export `build.bat debug` keeps exports testable.
  Please confirm c instead of b.
- **N1. Version number:** the menu shows "Verzia 2.0.0" (story data version), the exe says 0.1.0.0 (ISSUES M5-03).
  **Show the release number (0.1.0, or 1.0.0 for the first public release) in the menu.**
- **N2. Item stays selected after a successful use** (PT-F09 / PT-S16; the most confusing thing in both playtests;
  exit clicks do nothing while an item is selected). a) clear the selection after a committed item action;
  b) let an exit click drop the selection and walk; c) keep. **a + b** (a small Core rule change, tested by the
  existing acceptance runs).
- **N3. Hints per step, not per quest** (PT-F08 / PT-S26): **skip hint lines whose step is already done** (Core
  hint selection; no text change).
- **N4. Signing and ids:** a Windows code-signing certificate (removes the SmartScreen warning; optional for a free
  game), the final bundle / package id (placeholder `eu.lastbell.poslednyzvonec`), and for the ports an Apple
  Developer account (USD 99/year) and an Android release keystore (docs/BUILD.md).

### Places (owner location feedback 2026-10-05, still open)
- **N5. Entry hall of ZŠ Sokolíkova (S13 1995, S53 2020, S59 1982):** you said the real hall looked different from the
  type references, "details pending". The rooms are painted from type references until you describe it (layout,
  where the stairs / porter's window / doors are, floor and wall colours, what hung on the walls). Cost to repaint
  the L_HALL family afterwards: about USD 0.45-0.90.
- **N6. The imgur photos** (`imgur_wrRxN8x` S07, `imgur_2tyAMxf` S08, `imgur_d7UwYm6` S41): are they your own photos?
  If yes (and you allow it), we may use them as real image inputs and credit you. If not (Street View), they stay
  look-only, as now. Two of them are Street View screenshots and can never be inputs.
- **N7. S57 data:** decision 3b (bus, tram line under construction) is in the game as a presentation override;
  game.json `art_brief` / `ambience` of S57 still say tram (handoff owner, ART-DUBEXT-01).

### Texts (docs/writing/SAMPLES.md "Open points for you")
- **N8. Renames made in the rewrite, please confirm:** "Juro Kazeta" (was Juraj Malík zvaný Juro Kazeta),
  "Paliho opravovňa" (was Palova), item names "Textilný izolačný návlek", "Adaptér s konektorom bez izolácie",
  "Mapa uzlov bez fólie", "Priehľadná fólia K-17", "Úplná mapa meracích uzlov", and "Drevená lastovička" (S64,
  the 1982 swallow is Tóno's wooden model). **ok**.
- **N9. Tóno's name:** hover labels and topic headers say "Anton Farkaš", every line says Tóno (PT-S25).
  **"Tóno (Anton Farkaš)"** on first meeting, then "Tóno".
- **N10. Smaller text questions:** Lea's speaker label (keep "Lea Kormanová (správa z roku 2032)" or **"Lea
  Kormanová (2032)"**); should the F08 goal name the bridge too (**yes**, it is the only step players miss); two
  things called "servisná doska" (S63 workbench and the wall board; **rename the workbench "pracovný stôl"**); the
  map label "Okno školníckej dielne v roku 1982" differs from its room name (**make it equal**); the action label
  "Dotiahnuť bezpečne položenú kulisu" vs the standing flat in S34 (PT-S19, **reword label + look**).

### Story data and art fixes found in the playtests (handoff owner / small paid edits)
- **N11.** Mira speaks five lines in the S40 attic but is not in the room (PT-S18): **add MIRA60 to S40 after I09**
  (game.json) or mark the lines as off-screen voice.
- **N12.** Paid art fixes, about USD 1.5-2.5 in total: CS07 port frame shows ✕ instead of + (PT-S21, USD 0.15);
  Adam's winter coat for the 1982 rooms (PT-S20, USD 1-2); "RECEPTION" lettering in S43 (PT-S27, USD 0.15).
  **Do all three.**
- **N13.** Design: the conversation closes after every topic (PT-S17; **return to the topic list until "Ukončiť
  rozhovor"**); Esc skips the whole intro (PT-F13; **first Esc = this line, second = all**); the painted stop clock
  in S11/S51/S57 is not the time node (PT-F10; **one-time notice that the clock button / T opens the era chooser**).

### Items 11-24
Unchanged since the list above. Item 13 is mostly done: the S04 basket (crate empty after G03) and the S06 photo
(faded after G11, half after C04, restored after F17) have their after states; only the S09 case stays closed
(the chronometer is inside, so nothing visible changes). Items 14-24 are cosmetic and can be answered any time.

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
