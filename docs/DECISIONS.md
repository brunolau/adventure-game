# Decisions for the product owner

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
