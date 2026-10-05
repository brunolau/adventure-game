# Natural re-blocking - decision brief (2026-10-05)

**Decision for the product owner:** may rooms be re-blocked naturally (props where they really are, the walk band on
the real ground), or do all 68 rooms keep the handoff's template blocking?

**Status:** built and tested on S03 and S05. **Off by default.** Nothing in `game.json`, Core, saves or rules changes.

## The problem

Every room in `game.json` uses the same template coordinates (ISSUES.md ART-BLOCK-01):

- prop rects 120x100 at x 120/425/730/1035, y 150-250, in one row along the top quarter of the screen;
- NPC rect 385,450,150,320;
- a walk band at y 790-1015;
- exits at y 975.

To make a painting fit these rects, the background has to put every prop high up: on a raised plot, a high shelf or
a wall. The camera ends up looking at the top of the scene, and the lower 60 % of the picture is empty floor:

- S03: the distribution tables are squeezed against the top edge, the roof is cut off, and the "tape on the floor"
  had to be painted on a low back wall the real shelter does not have.
- S05: the frontage stands on an invented 1 m raised plot with steps. The doormat hangs on the fence and the table
  stands on a landing. The real Pezinská street is flat.
- Floor-standing props drawn high in an eye-level view make the model re-compose the scene, so frontages needed 2-4
  paid calls each plus refits (PAINTING.md).

## Comparison (in-game, Space labels on)

![S03](S03_compare.png)

![S05](S05_compare.png)

**Verdict:** the natural versions are clearly better pictures and better game screens:

- the whole place reads at a glance: the full shelter with roof and chimney, the full frontage with the house;
- each prop stands where a player expects it: the table beside the gate, the mat in front of the gate, the tapes on
  the floor in front of the queue table;
- the labels sit next to the objects they name;
- Ela stands at the side wall of the shelter, as the brief asks, instead of on the open forecourt far from her table;
- the hero walks on the ground that is painted under him.

Both rooms were followed by the model in **one paid call each** (template S03/S05: 4 calls each plus refits). The
painted props landed inside the natural rects. Only S03's tape needed its rect moved 50 px to match the painting.

**What gets worse, honestly:**

- Characters at the back are smaller: scale 0.43-0.52 at the back edge instead of 0.80 (Ela is ~245 px tall at the
  shelter).
- Props are smaller on screen (S03 thermos rect 110x95). All rects are still at least 44x44.
- Two hotspots (S03 tape, S05 doormat) now lie on the floor at the back edge of the walk band. A click there looks
  at the prop instead of walking.
- The deeper band means a little more walking.
- S05's workshop door is split: the upper part is the `shed_door` hotspot and the lower part with the threshold is
  the exit to S09. Both labels show, one above the door and one below it.

## What was built

| piece | where | what |
|---|---|---|
| blocking files | `src/game/data/blocking/<room>.json` (S03, S05) | per hotspot `rect`, `interaction_point`, `label_anchor`; per NPC `feet`, `scale`; `walk_polygon`, `walk_band`, `actor_scale`, `spawn`; exits' `rect` / `interaction_point` / `label_anchor`; `background`; `state_patches`; optional `ambient`, `foreground_mask`. Ids must exist in game.json; conditions stay there. |
| loader | `src/game/scripts/World/RoomBlocking.cs` | reads the file only when enabled; cached per room |
| application | `src/game/scripts/World/Room.cs` | walk area, perspective, background, targets (hit rects, walk targets, labels), hero spawn, NPC feet and scale, ambient data path. For a re-blocked room the template's `art_overrides.json` entry is ignored, because its nudges and patches belong to the old painting. |
| small hooks | `Actor.ScaleOverride`, `AmbientHost.DataPathOverride`, `PresentationSettings.NaturalBlocking` | additive |
| switch | `src/game/project.godot` `[last_bell] presentation/blocking="template"`; QA flag `--blocking natural\|template` (DebugHarness) | default template |
| validator | `tools/check_blocking.py` | see below |
| paint tool | `art/tools/paint_natural.py` | paint_room.py / review_room.py with the natural geometry and separate folders (prompts/layout/masters/review `natural`, export `assets/bg_natural/`) |
| paintings | `src/game/assets/bg_natural/S03.webp`, `S05.webp`; masters + logs in `art/masters/bg_natural/` | the template `bg/S03.webp`, `bg/S05.webp` are untouched |
| state patches | `src/game/assets/variants_natural/` (`art/tools/natural_patches.py`, free) | S05 groceries on the table (G04) and the unlocked workshop door (G06) |
| ambient | `src/game/data/blocking/ambient/S03.json`, `S05.json` | data-only layers re-placed for the new paintings: leaves, pigeons, birds, a cat on the fence, a curtain shadow. No sway layers yet. |
| comparisons | `docs/reblock/<room>_compare.png` (`tools/reblock_compare.py`) | |

### Validator `tools/check_blocking.py`

It checks the *effective* geometry: game.json merged with the blocking file, by the same rule Room.cs uses.

- **Errors:**
  - unknown ids;
  - a rect smaller than 44x44, or less than 44x44 of it on screen;
  - a walk polygon that intersects itself or leaves the screen;
  - interaction points (hotspots and exits) or the spawn outside the walk polygon. The polygon is one connected
    area, so a point inside it is reachable from the spawn;
  - label anchors off screen;
  - NPC feet more than 12 px off the walkable floor;
  - a rect fully hidden behind earlier targets in the game's hit order (NPCs, then props with later entries on top,
    then exits);
  - a missing state-patch texture.
- **Warnings:**
  - overlapping or clamped labels;
  - a label far from its rect;
  - an exit rect far from its walk target;
  - no walkable approach point beside an NPC;
  - an NPC scale that does not match the room's perspective;
  - a rect that is mostly hidden;
  - a missing painting.

Run it with `python tools/check_blocking.py`, or with `--template` to check the game.json geometry. S03 and S05:
0 errors, 0 warnings. The template check fails 49 of 68 rooms on one known issue: NPC feet stand 20 px behind the walk
band (ISSUES GAME-04).

## Tested

| check | result |
|---|---|
| `dotnet test src/LastBell.sln` | 293 passed, 3 skipped, 0 failed |
| `tools/check_strings.py` | OK |
| `--acceptance m1`, `--acceptance m2` (default, template) | exit 0, no FAIL |
| `--blocking natural --fast-text --real --play 11` (whole prologue G01-G11 by real clicks through natural S03 and S05) | passed 2 of 3 runs; the first run stopped once on a travel retry in S04, a room that is not re-blocked, and both reruns passed. Evidence: `build/screens/reblock/play/*.jpg` (Adam beside Ela at the side wall, the bag on the S05 table, the door unlocked) |
| `--blocking natural --acceptance` (m1 + m2, incl. AT20 "every target clickable" and AT05 labels in all 68 rooms) | exit 0, 60 PASS, 0 FAIL |

## Cost and time to apply to all 68 rooms

| work | rooms | paid | agent time |
|---|---|---|---|
| design the blocking from the register photos and brief, plus the sketch and prompt | 68 | - | ~20-30 min per room |
| repaint the rooms already painted on the template | 11 (S01-S11) | 1-3 calls each = USD 1.65-5.00 | ~15 min per room (review, export) |
| paint the rooms not yet painted (S12-S68), directly on the natural blocking | 57 | 1-3 calls each = USD 8.55-25.65. Template recipe budget: ~USD 0.60 per room = USD 34, so natural is likely **cheaper** | same as the template recipe |
| re-place the data-only ambient layers, re-cut the sway textures (`ambient_cut.py`, free) | 11 already animated | - | ~10 min per room |
| redo state patches (S01 bag, S05 x2 done), window-bust sill heights (`data/ambient/actors.json`: S04 DANA `sill_y` 595, S06 MIRA20 `sill_y` 582) and the S06 photo crop used by the cutscene shots (`art/tools/cutscene_shots.py`) | S01, S04, S06 | - (one paid call if a cutscene still has to be re-made) | ~1 h |
| camera families: one shared natural blocking per family (`landmark_layouts` L_STOP, L_SCHOOL_FRONT, L_HALL, L_CLASS, L_CABINET, L_YARD, L_WINDOW), designed together so the anchors stay pixel-identical across eras. This also resolves ART-STOP-01. | ~25 rooms in 7 families | - | +1 h per family |
| QA: `check_blocking.py`, comparison shots, `--play-all --real --blocking natural` | all | - | ~2 h per batch |

**Extra money for the switch:** about USD 2-5, for repainting S01-S11. For the remaining 57 rooms the natural
blocking should cost less than the template recipe, because physically plausible sketches are followed in one call.
**Extra time:** about 30-40 agent-hours, about the same as painting on the template plus refits, and it can be done
in parallel batches of 5-10 rooms.

## Risks

1. **The handoff says the coordinates are binding.** Every room's `blocking_note` says "Súradnice sú záväzný herný
   blocking", and ART_DIRECTION section 4 says the same. Approving natural blocking overrides that for presentation.
   game.json stays the logic source. Core never reads positions, and every rule still re-resolves through Core on
   arrival.
2. **Two sources of geometry.** For re-blocked rooms the coordinates in game.json become stale. If the handoff owner
   later changes game.json rects, nothing breaks, but the change has no effect while a blocking file exists.
   Mitigation: `check_blocking.py` in the build. Better: fold the blocking files back into game.json once approved
   (proposed handoff fix for ART-BLOCK-01).
3. **Mixed state while migrating.** Template and natural rooms have different character scales (back of the band
   0.8 vs ~0.45). The switch is global, and a room without a blocking file keeps the template. Switch the prologue
   rooms S01-S11 together.
4. **Rooms with a blocking file but no `bg_natural` painting** show the dev blockout, not the template painting,
   because the old painting would not match the new rects. Rule: paint before you add a blocking file to the build.
5. **Smaller back-of-band characters and props.** Watch NPC readability and touch targets on the mobile ports. The
   44 px minimum is enforced, but 60+ px is kinder for touch.
6. **Floor hotspots inside the walk band** (S03 tape, S05 mat) catch floor clicks. This is standard in adventure
   games, but it is new for this project.
7. **The bottom HUD bar** covers y ~1000-1080 in both modes. The natural walk bands end at y 1015, like the template.
8. **Ambient:** the natural S03 and S05 have data-only layers (particles, critters, tween paths), but not yet the
   wind-sway layers of the vine and trees.
9. **ISSUES ART-NPC-01** (the brief says Ela sits, the sprite stands) is unchanged. The natural blocking places her
   at the side wall as the brief asks, standing.

## How to enable

- **Try it** (QA, no setting changes):

  ```
  <console exe> --path src/game --resolution 1920x1080 -- --blocking natural --room S05 --labels
  ```

  Or play the whole prologue through real clicks:

  ```
  <console exe> --path src/game --time-scale 4 -- --blocking natural --fast-text --real --play 11
  ```

- **Turn it on for players:** in `src/game/project.godot` set `[last_bell] presentation/blocking="natural"`. Only
  rooms that have a `data/blocking/<room>.json` change.
- **Add a room:** the complete per-room checklist, schema and commands are in `art/tools/PAINTING.md` "Natural mode"
  (per-NPC staging, occluders, foreground mask, state overlays, ambient, audio, `derive_era.py` for camera families). Short form:
  1. Write `src/game/data/blocking/<room>.json`.
  2. Write `art/prompts/natural/<room>.txt` and `art/prompts/natural/<room>.sketch.json`.
  3. Run `art/tools/paint_natural.py prompt` and then `paint ... --scope bg_natural/ --budget <usd>`.
  4. Review the painting, then run `export`.
  5. Re-fit the rects to the painting if needed.
  6. Run `python tools/check_blocking.py`.
  7. Take comparison shots with `tools/reblock_compare.py`.
- **Turn it off:** set `"template"` (the default) or pass `--blocking template`. Nothing else changes.

## Spend

2 paid calls, USD 0.30 (`bg_natural/S05_v1`, `bg_natural/S03_v1` in `art/spend-log.csv`), of a USD 4 budget.
