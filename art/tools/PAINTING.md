# Painting room backgrounds (style A) - recipe

Proven on the pilot rooms S01 (interior garage) and S05 (exterior garden gate), 2026-10-05; logs in
`art/masters/bg/S01.md` and `art/masters/bg/S05.md`. Binding rules: `design-doc/ART_DIRECTION.md` (style A only,
real places, rects binding, nudges <= 40 px), `design-doc/ARCHITECTURE.md` (English-only code and docs).

Tools (all in `art/tools/`, run with `PYTHONIOENCODING=utf-8 python -X utf8 ...` from the repo root):

| tool | what | cost |
|---|---|---|
| `paint_room.py prompt <room>` | assembles the prompt, renders the sketch to `art/layout/<room>_sketch.png`, lists the images | free |
| `paint_room.py paint <room> --scope bg/<task>/ --budget <usd> [--seed N]` | one generation -> `art/masters/bg/<room>_v<N>.png` + `.json` sidecar (prompt, images, seed, price), then the review overlay | USD 0.15 |
| `review_room.py <room> <N>` | `art/review/<room>_v<N>_overlay.png` (rects, NPC zones, exits, walk band, anchors, nudges) + `_crops.png` (every rect x2) | free |
| `review_room.py <room> <N> --grid x0 y0 x1 y1` | x2 crop with a 20 px grid in game coordinates, to measure where a prop really is | free |
| `refit_room.py fit <room> <N> --box "<id>=x0,y0,x1,y1" ...` | best uniform scale + offset that moves the measured props into their rects | free |
| `refit_room.py extend <room> <N> --scale s --offset tx ty --keep ... --note "..."` | scales the master, outpaints the uncovered margins, composites the original back | USD 0.15 |
| `refit_room.py fix <room> <N> --box x y w h --instruction "..."` | local edit; only the box is taken from the model's output | USD 0.15 |
| `paint_room.py export <room> <N>` | master -> `src/game/assets/bg/<room>.webp`, 1920x1080, WebP q90 | free |
| `bg_helpers.py prezoom-paint <room> --plan s tx ty ...` | paint with a pre-zoomed sketch for a planned refit (see "Batch prologue2020") | USD 0.15 |
| `bg_helpers.py trim / remap / recomposite ...` | grey out the bottom before an extend / push a kerb out of the walk band / re-composite a paid fix with a bigger box | free |

Model: `fal-ai/nano-banana-pro/edit`, 16:9, 2K, png, one image per call. It returns 2752x1536; the game frame is
1920x1080, so every tool maps with the same cover-fit (`paint_room.fit_to_frame`: scale to 1935x1080, crop 7 px left,
8 px right). Each paid call goes through `fal_api.run`, which refuses to exceed `--budget` for the `--scope` prefix and
appends a row to `art/spend-log.csv`. Use a scope per task (`bg/batch2/`, ...), not the bare `bg/`.

## Step by step

1. **Read the room.** `design-doc/game.json` room (art_brief, hotspots, exits, walk_polygon, camera_family),
   `design-doc/LOCATIONS_REGISTER.csv` row (real place, photos, fiction notes, notes), the photos in
   `art/source/rooms/<room>/` (LOOK at them), the layout guide `art/layout/<room>.png`, and
   `game.json landmark_layouts[camera_family]` if the room has a camera family.
2. **Design a physically consistent camera for the rects.** All rooms share a template blocking (ISSUES.md
   ART-BLOCK-01): prop rects 120x100 at x 120/425/730/1035, y 150-250; NPC rect 385,450,150,320; walk band
   y 790-1015. A prop rect is ~0.4 hero heights tall and sits far above the hero's head, so:
   - *Interior:* the props stand on a high shelf / hang on the upper wall right behind the walk band; the wall meets
     the floor at y ~780 (S01).
   - *Exterior:* the frontage stands on a ~1 m raised plot behind a low retaining wall (steps up to gates), so table
     tops, door handles and fence tops are at y 150-250; the walk band is the pavement in front (S05).
   - Never draw small floor-standing props high in a flat eye-level scene: the model "corrects" it (S05 v2).
3. **Write the sketch** `art/prompts/<room>.sketch.json`: flat colour blocks in game coordinates (format in the
   `paint_room.py` docstring). Big regions first (sky, walls, floor), then furniture, then each hotspot prop drawn as a
   simple silhouette that fills its rect, with its own colour (olive bag, grey cabinet, cream pot...). The walk band is
   one plain floor colour (no lines across it except paving joints); kerbs/edges go above y 790. NPC zones get plain
   background only. No text, no outlines around props. Render and check it:
   `paint_room.py prompt <room>` then `review_room.py <room> art/layout/<room>_sketch.png` - every prop block must sit in
   its rect in the overlay.
4. **Write the prompt** `art/prompts/<room>.txt` from the template below (English; translate the Slovak brief).
5. **Paint** (`paint_room.py paint`) and LOOK at the master, the overlay and the crops. Judge with the checklist below.
6. **Repair instead of re-rolling** (max 4 paid calls per room, all counted):
   - every prop is off by a similar scale/shift (typical: the scene came out ~1.2x larger, props too low) ->
     measure the props (`review_room.py --grid`), `refit_room.py fit`, then `refit_room.py extend` with `--keep`
     ending on a strong horizontal edge (a kerb, a skirting line). If the seam shows, re-composite the same raw output
     for free with another `--keep` (`--from-raw art/masters/bg/_<asset>_raw.png`).
   - one prop is the wrong size or slightly off -> `refit_room.py fix` with a box around it (and around whatever it
     leaves behind), then a nudge.
   - the composition is wrong (walls, floor line, camera) -> change the sketch and the prompt, paint again.
   - remaining offsets <= 40 px -> `src/game/data/art_overrides.json` (below).
7. **Export** `paint_room.py export <room> <N>`, write `art/masters/bg/<room>.md` (attempts table: version, kind,
   seed, result, verdict; review of the final; continuity notes for rooms of the same property or family).

## Prompt template (`art/prompts/<room>.txt`)

`paint_room.py` adds the image-role preamble, the "paint over the sketch, no frames/boxes" warning and the canonical
style-A sentence (read verbatim from ART_DIRECTION.md). Placeholders are expanded from game.json - never type
coordinates of rects yourself. Every hotspot id must appear in a `{rect:...}` (NPCs via `{npc_zones}`), else the tool
refuses.

```
# <room> <name> (<era>) - prompt body for art/tools/paint_room.py
#refs: art/source/rooms/<room>/<photo1>.jpg ; art/source/rooms/<room>/<photo2>.jpg
#style: art/backgrounds/<entrance|sokolikova-street|...>.png
Place: <real place and area from the register>. Images 2-<n> are <what each photo shows>. Paint <what is real /
what is invented> from these real house types, walls and materials - not a copy of one particular private house.

Brief: <art_brief in English>. <season, year, time of day, weather, light>. <era details the brief or story asks for>.

Camera: <height and angle, consistent with step 2>. Keep this exact geometry from the sketch: <the main lines with y>.

What the sketch blocks are: <every non-hotspot block, left to right, in plain words>.

Interactive props - each painted clearly inside its block, the same size as its block, easy to recognise at a glance:
1. {rect:<hotspot id>}: <the prop, the part that must be inside the rect>.
2. ...

Walkable floor: {walk} is <surface> - one continuous flat surface with no kerb, step, edge or change of material
inside it, and nothing standing on it: <list>. Only light, shadows and <small details>. <exits: {exit:<id>} ...>.
{npc_zones}
{anchors}

Fiction rules: <register fiction_notes>. No house numbers, no names, no shop signs, no logos, no people, no animals.
Any paper shows only illegible scribbles, no digits.
```

Style reference: pick the approved background closest in kind (exterior street: `sokolikova-street.png`, school
exteriors: `entrance.png` / `side-path.png`, greenery: `sokolikova-yard.png`). No interior reference exists yet; once
S01 is accepted it can serve as one for interiors.

## What worked and what failed (pilot evidence)

| finding | evidence |
|---|---|
| Sending the labelled layout guide makes the model **draw its boxes and green lines** and place props where they naturally stand. Do not send it; use it for designing the sketch and for review. | S01 v1, S05 v1 |
| A flat-colour **sketch as image 1** fixes the composition: S01 props within ~20 px, floor line exact. | S01 v2 |
| The sketch is only followed if it is **physically plausible**. With floor-standing props high in an eye-level view the model re-composed the scene at its own scale (props 300-500 px too low), twice, even with a raised plot. | S05 v2, v3 |
| More prompt words do not fix placement; a repaint can get worse. | S01 v3 |
| **Refit** (uniform scale + outpaint) puts all props in their rects without repainting; the outpaint reproduced the kept area within ~5-9 grey levels, the new margins matched in style. | S05 v4 |
| A soft seam through a texture (paving) shows doubled joints; a seam along a kerb is invisible. | S05 v4 vs v5 |
| **Local fix** of one prop works and leaves the rest pixel-identical (bag a third smaller, tape measure removed), but the model does not hit an exact x position from percentages (ended 60 px right). | S01 v4 |
| Free cut-and-paste moves of a prop on a painted wall show rectangles and ghosts (wall gradients). Dropped. | S01 v5/v6 (deleted) |
| The model adds kerbs/edges into the walk band unless told "one continuous flat surface, no kerb" and given a kerb line above the band in the sketch. | S05 v2, v3 |
| Requested words are spelled right (VITAJTE); unrequested text appears too ("2020" on a note, pseudo letters on a radio dial) - ask for "illegible scribbles, no digits". | S05 v2, S01 v2 |
| Interiors in sketch mode come out with slightly cleaner, inkier lines than the painterly references; a "Rendering: painterly, no ink outlines" line did not change it. Exteriors matched the references well. | S01 v2/v3, S05 v3 |
| Cost: USD 0.15 per call; the two pilot rooms took 8 calls = USD 1.20. Budget ~USD 0.60 per room. | spend-log `bg/pilot/` |

### Batch prologue2020 (S02 S03 S04 S06 S07, 2026-10-05; logs in `art/masters/bg/<room>.md`)

| finding | evidence |
|---|---|
| **Straight-on wall views are followed in one call** (S01 camera: the wall meets the floor at y ~780, props in the upper part of tall windows / on a high shelf, NPCs behind a window with the sill at y ~595-610). | S04 v1, S06 v1 |
| **Frontage sketches with the S05 camera are always re-composed** at eye level, 1.0-2x larger (x positions kept in S02, scaled 1.35x in S07, ~2x in S03), and the model drops an invented raised terrace when the photo shows flat ground. Plan the refit from the start: paint, measure (`review_room.py --grid`), `refit_room.py extend`. | S02 v1, S03 v1, S07 v1 |
| The fit tool returns the *smallest* scale that scores well; compute the largest one that still puts every prop in its rect (less outpaint, closer to the painting). A pure shift (scale 1.0) is enough when only y is off. | S02 v2 (1.0 vs 0.84), S07 v3 (0.80 vs 0.66) |
| Outpainting ~60 % of the frame (right quarter + everything below y ~590) at scale 0.8 still matched the style; seams through large concrete slabs were invisible. | S07 v3, S03 v4 |
| If the bottom of the painting (kerb, bus bay) would land above the walk band after scaling, grey it out first (`bg_helpers.py trim`) and pass `--keep` so it is not pasted back. The model may still place the new kerb too high; empty paving can then be stretched for free (`bg_helpers.py remap`, max ~1.2x reads naturally). | S07 v2-v4 |
| **Pre-zoomed sketch**: when props must keep their relative layout (three in one row at one height), draw the sketch at the eye-level scale the model prefers and plan the refit (`bg_helpers.py prezoom-paint --plan 0.8 -40 -180`, then `extend` with the same transform). The model followed it to within ~30 px. | S03 v2, v4 |
| A **floor** item cannot share the top hotspot row with table tops in an eye-level view; the model moved the floor tape onto a wall. Re-block or rename such hotspots (ISSUES.md ART-BLOCK-02). | S03 v2 |
| `refit_room.py fix`: make the box exceed the object by more than the feather (~34 game px on each side); a tight box leaves a half-transparent ghost. The raw output can be re-composited for free with a bigger box (`bg_helpers.py recomposite`). | S02 v3 -> v4 |
| Unrequested readable text still appears on product boxes ("disposable masks" in English) and as pseudo-Cyrillic headings; one local fix removed all of it. | S03 v2 -> v3 |
| Using the accepted S05 background as the style image keeps light and palette coherent across a family of rooms; for a room of the same property pass it as a *reference* image (not as the style image, which the preamble says not to copy). | S02-S07, S06 |
| Cost: 11 calls = USD 1.65 for five rooms (1-4 calls per room; wall views 1, frontages 2-4). | spend-log `bg/prologue2020/` |

### Batch S08-S11 (2026-10-05; logs in `art/masters/bg/S08.md` ... `S11.md`)

| finding | evidence |
|---|---|
| **Raised bank exterior** (props on the crest of a ~1.7 m embankment, path at its foot, horizon ~y 100 so sky and landscape stay visible) and a **side-on view across a double track** (template prop row = far platform, walk band = near platform) were both followed in one call, props within ~20 px, anchors exact. | S08 v1, S11 v1 |
| Interiors: the model **copies the style image's left-edge door** (S01's roller shutter appeared in S09 v2/v3 and S10 v1), and a narrow doorway strip in the sketch is widened to a real door, pushing the props 130-200 px right. Put a solid block (cupboard) at the frame edge or a realistic doorway with the shelf resting on its lintel, and use a style image without that door. | S09 v2, v3; S10 v1 -> v2 |
| A reference photo with a strong perspective (danielmee33 shed) overrides a frontal sketch (three-wall room, props 150-300 px off). An explicit paragraph "Camera: exactly as frontal as image N, ONE wall parallel to the picture, no side walls" plus percentages fixed it. | S09 v1 -> v2 |
| Too much stacked above the shelf (visible ceiling + tube + schematic) makes the model compose a taller room (shelf 150 px lower, floor at y ~960). Showing only the beam at the top edge ("ceiling NOT visible") and repeating the vertical positions in percent brought it to within ~10 px. | S10 v1 -> v2 |
| `refit_room.py fix` with a box touching the frame edge used to feather that edge too and blended the old object back in as a ghost; fixed in the tool (frame-edge sides are not feathered). Re-composite an older raw output for free with the corrected mask. | S09 v4 -> v7 |
| Free pixel retouches work for small, simple elements: mirror a clock dial to change the time (symmetric ticks), a soot smudge on a fuse, duplicating a ski along its own traced outline. Always protect thin foreground parts (strap, pole) with a mask from their dark pixels. | S11 v3, S10 v3, S09 v6 |
| Cost: 9 calls = USD 1.35 for four rooms (S08 1, S09 4, S10 2, S11 2). | spend-log `bg/batch_s08_s11/` |

## Review checklist (do it on the overlay AND the crops, at 100 %)

- [ ] Every prop inside its rect (or within a <= 40 px nudge) and recognisable at a glance in its crop.
- [ ] Walk band: open, continuous floor; no kerb, step, edge, pole, furniture, cable or rug in it; exits open.
- [ ] NPC zones: plain background, no person, figure, silhouette or coat that reads as one.
- [ ] NPC feet: an NPC stands with its feet on the rect bottom (y 770, 20 px above the walk band, ISSUES.md GAME-04),
      so the floor must reach up behind every NPC zone: interiors put the wall-floor line at y <= 760 there (not ~780
      as in S01, which has no NPC); exteriors keep the pavement up to y ~740. Otherwise store `npc_feet` (<= 40 px).
- [ ] No people (paint them out), no animals or cars unless the brief asks; no legible real brands, logos, house
      numbers, names on bells or mailboxes; paper and screens illegible.
- [ ] No guide artefacts (boxes, outlines, grid, green band, labels) and no flat sketch blocks left.
- [ ] Era, season, time and weather per brief and era (1960/1982/1995/2020/2035); covid-era details only where the
      brief or story asks (2020).
- [ ] Style A: consistent with `art/backgrounds/*.png` (painterly brushwork, warm light, harmonious palette).
- [ ] Recognisably the real place of the register row (architecture, materials, street furniture); fiction notes kept.
- [ ] Camera families: `landmark_layouts` anchors (magenta crosses in the overlay) hit the same architecture in every
      era; same-property rooms reuse the colours and details listed in the earlier room's `<room>.md`.
- [ ] Refit/fix seams invisible at 100 %.
- [ ] Hotspots with `visible_after` / `hide_after` noted for a state patch (ISSUES.md ART-VAR-01).
- [ ] Sidecar present, spend logged, `<room>.md` written, export 1920x1080 WebP.

## `src/game/data/art_overrides.json`

Schema owned by `src/game/scripts/World/ArtOverrides.cs` (visual only, every value clamped to +-40 px):

```json
{ "version": 1,
  "rooms": { "S01": { "master": "art/masters/bg/S01_v4.png",
                      "targets": { "S01.tools": { "rect_nudge": [40, 0, 30, 0], "label_offset": [40, 0],
                                                  "reason": "why" } } } } }
```

`rect_nudge` is `[dx, dy, dw, dh]` on the hover/click rect, `label_offset` moves the label; interaction points never
change. Other keys the loader knows: `actor_scale`, `walk_band`, `foreground_mask`, `npc_feet`. Extra keys (`reason`,
`master`) are ignored. `review_room.py` draws the nudged rects as dashed cyan boxes.

## Natural mode (all 68 rooms; product-owner decision 2026-10-05)

Natural re-blocking replaces the template geometry for presentation: each prop stands where it really is, the walk
polygon lies on the painted ground, NPCs are staged per `docs/DECISIONS.md` item 2. `game.json` is never edited (ids,
conditions and rules stay there; Core never reads positions). Pilot and rationale: `docs/reblock/README.md`.
**Binding owner feedback:** `art/feedback/2026-10-05_owner_feedback.md` overrides the register for S04, S05, S07,
S08, S11, S12, every ZŠ Sokolíkova room (plain yellowish walls in 1982/1995, the yard-side entrance), S17, S18, S21,
S28, S41, S43. Owner reference images in `art/source/owner_refs/` are for LOOKING only: never pass them to the
generator and never copy their framing; Google Street View screenshots are location pointers only.

### How the game applies it

A room with `src/game/data/blocking/<room>.json` uses its geometry and `assets/bg_natural/<room>.webp` when natural
blocking is on (`--blocking natural`, or project setting `last_bell/presentation/blocking="natural"`); a room
without a file keeps the template. A blocking file without its painting shows the dev blockout (never the template
painting), so a room's blocking file goes into the build together with its painting. For a natural room the
template-painting data is ignored: `art_overrides.json`, the `data/ambient/actors.json` placement,
`data/ambient/<room>.json`, the template `visual_variant_layers` overlays. Loader `src/game/scripts/World/RoomBlocking.cs`,
applied by `Room.cs`; validator `tools/check_blocking.py`.

### Per-room files (a painter writes ONLY these)

| file | what |
|---|---|
| `src/game/data/blocking/<room>.json` | the blocking (schema below) |
| `art/prompts/natural/<room>.txt`, `<room>.sketch.json` | prompt body and flat-colour layout sketch |
| `art/prompts/natural/<room>.era.txt` | era prompt when the room is derived from a family base (`derive_era.py`) |
| `art/prompts/natural/<room>.fg.json` | foreground-mask polygons (`paint_natural.py mask`) |
| `art/masters/bg_natural/<room>_v<N>.png` + `.json` | masters + sidecars (written by the tools) |
| `art/masters/bg_natural/<room>.md` | the room log: attempts, decisions, review findings, register updates |
| `src/game/assets/bg_natural/<room>.webp` | exported painting (1920x1080) |
| `src/game/assets/fg_natural/<room>.webp` | foreground mask (1920x1080 RGBA), optional |
| `src/game/assets/variants_natural/<room>_<name>.webp` | state patches and full-frame variant overlays |
| `src/game/data/blocking/ambient/<room>.json` | ambient layers for the natural painting (schema `src/game/scripts/Living/README.md`) |
| `art/ambient/natural/<room>.cuts.json` -> `src/game/assets/ambient/<room>/natural/` | sprites cut from the painting (`ambient_cut.py --natural <room>`) |
| `build/screens/m3/<room>/` | in-engine screenshots |

Never edit shared files (`project.godot`, `game.json`, `art_overrides.json`, `data/ambient/actors.json`,
`data/ambient/<room>.json`, `art/ambient/cuts.json`, `LOCATIONS_REGISTER.csv`, `data/audio/*.json`). Register
changes go into the room log under "Register updates for the integrator".

### Blocking schema (`src/game/data/blocking/<room>.json`)

```jsonc
{ "version": 1, "room": "S13",
  "note": "camera height, horizon y, foot line y, px per metre; where each prop really is",
  "background": "bg_natural/S13.webp",                  // optional, this is the default
  "walk_polygon": [[x, y], ...], "walk_band": [top, bottom], "actor_scale": [scale_at_top, scale_at_bottom],
  "spawn": [x, y],
  "anchors": { "terrazzo_line": [960, 890] },           // camera families only: identical in every era of the family
  "hotspots": { "S13.book": { "rect": [x, y, w, h], "interaction_point": [x, y], "label_anchor": [x, y], "reason": "..." } },
  "exits":    { "S13.to_S12": { "rect": [...], "interaction_point": [...], "label_anchor": [...], "reason": "..." } },
  "npcs": { "S13.TONO": {
      "variant": "seated",          // standing | seated | behind_counter | window_bust | window_bust_glass | any actor.json variant
      "feet": [x, y],               // feet centre (bust: where the figure would stand)
      "scale": 0.62,                // absolute; omit = room perspective at the feet
      "sill_y": 640,                // REQUIRED for bust variants: canvas y of the painted counter / sill / table top (cut line)
      "offset_x": 0, "facing": "left|right",   // optional
      "z": "auto|back|front",       // auto = y-sorted with the hero; back = always behind hero + occluders; front = always in front
      "reason": "DECISIONS item 2: sits at the visitor log" } },
  "occluders": [ { "id": "desk", "polygon": [[x, y], ...], "baseline": 760, "texture": null } ],
      // a piece of the painting (texture null) or of a full-frame image, y-sorted at `baseline`:
      // actors whose feet are above it are hidden behind it, actors below it walk in front of it
  "foreground_mask": "fg_natural/S13.webp",             // optional, this is the default; drawn above every actor
  "state_patches": [ { "texture": "variants_natural/S13_book_open.webp", "pos": [x, y], "after": ["T03"], "until": [] } ],
  "variant_layers": {                                   // natural replacement of each game.json visual_variant_layers asset of the room
      "variants/S17_healthy_linden.webp": "variants_natural/S17_healthy_linden.webp",           // full frame
      "variants/S55_linden_and_wall.webp": { "texture": "variants_natural/S55_linden.webp", "pos": [x, y] },  // patch
      "variants/S06_family_restored.webp": null },     // null = the natural painting needs no overlay (say why)
  "ambient": "res://data/blocking/ambient/S13.json",    // optional, this is the default
  "audio": { "ambience": [ { "sound": "<ambience.json library id>", "db": -6, "every": [20, 40], "x": [200, 1700] } ],
             "ambience_mode": "replace|add", "music": "<music.json cue or asset>" },   // optional (e.g. S57 bus)
  "waive": { "ambient": "reason" } }                    // only for --strict items that truly do not apply
```

(No comments in the real file: it is plain JSON.) Staging resolution (C# `ActorAnimationSet.TryResolveStaging` =
Python `check_blocking.resolve_staging`): `standing` -> the `full` variant or the default sheets of a standing figure;
`seated` -> a `seated` variant or the default sheets of a figure whose `posture` is seated (TONO, TONO82, VERA60);
`behind_counter` -> `counter`, else `table`; `window_bust` -> `window`; `window_bust_glass` -> `window_glass`;
anything else must be a variant name in `src/game/assets/actors/<ID>/actor.json` (e.g. JANA20 `laptop`). Bust variants
are cut at a sill line: the painted counter/sill top must be at `sill_y` across the figure. The check warns when the
staging differs from DECISIONS item 2.

### Commands

All from the repo root with `PYTHONIOENCODING=utf-8 python -X utf8`. Budget scope per room: `bg_natural/<room>/`
(the default of every paid command). Godot: `.tools/godot/Godot_v4.7.2-stable_mono_win64/Godot_v4.7.2-stable_mono_win64_console.exe`.

| command | what | cost |
|---|---|---|
| `art/tools/paint_natural.py init <room>` | drafts of the blocking, prompt and starter sketch (only files that do not exist yet) | free |
| `art/tools/paint_natural.py sketch <room> [--force]` | (re)derive the starter sketch from the blocking + render + sketch review | free |
| `tools/check_blocking.py <room> [--strict]` | validate (also `paint_natural.py check <room>`) | free |
| `art/tools/paint_natural.py prompt <room>` | assembled prompt, sketch render, sketch overlay | free |
| `art/tools/paint_natural.py run <room> --budget 0.45` | ONE paid attempt: check -> sketch -> paint -> review overlay -> export + master + sidecar. Refuses with blocking errors, TODOs, or after 3 paid paint/derive attempts | USD 0.15 |
| `art/tools/paint_natural.py review <room> <N> [--grid x0 y0 x1 y1]` | natural overlay (rects, NPC figures as drawn, sill lines, occluders, hero scale ruler, anchors) + crops / measuring grid | free |
| `art/tools/paint_natural.py export <room> <N>` | master vN -> `bg_natural/<room>.webp` | free |
| `art/tools/paint_natural.py refit fit\|extend\|fix <room> <N> ...` | `refit_room.py` on the natural masters (scope defaults to the room) | fit free, extend/fix USD 0.15 |
| `art/tools/paint_natural.py mask <room> [--preview-only]` | `fg_natural/<room>.webp` from `art/prompts/natural/<room>.fg.json` (the first run writes a template) + `art/review/natural/<room>_fg_preview.png` | free |
| `art/tools/paint_natural.py patch <room> <name> --from <N> --box x y w h [--full]` | cut `variants_natural/<room>_<name>.webp` from master vN (typically a `refit fix` version that shows the changed state; outside its box it is pixel-identical), preview + JSON snippet to paste | free |
| `art/tools/ambient_cut.py --natural <room> [--preview]` | ambient sprites from `art/ambient/natural/<room>.cuts.json` | free |
| `art/tools/derive_era.py init\|prompt\|run\|review <BASE> <TARGET> --from <N>` | derive another era of a camera family from an accepted base (below) | run USD 0.15 |
| `art/tools/paint_natural.py screens <room> [--replay N] [--act ID ...] [--tag after_G04] [--frames 6]` | Godot import (serialised by `build/.godot_import.lock`), then `<tag>_labels.png`, `<tag>_clean.png`, `<tag>_motion_NN.png` in `build/screens/m3/<room>/`; needs a real window | free |

### Per-room checklist (follow it in this order)

a. **Design the blocking from the real photos and the brief** (register row + `art/source/rooms/<room>/`, owner
   feedback, `game.json` art_brief). Start with `paint_natural.py init <room>`, then redesign EVERY value and write
   the camera in `note` (height, horizon y, foot line y, px per metre):
   - each hotspot rect on the object where it naturally is (floor props on the floor, wall props on the wall);
     rects >= 44x44, better >= 60 for touch; label anchor just above or beside the object;
   - each NPC staged per DECISIONS item 2 (`variant`, `feet`, `sill_y` for busts, `z`), with a walkable approach
     point beside it;
   - the walk polygon on the real ground only (pavement, floor, path): one connected simple polygon, bottom at y
     ~1015 (the HUD covers the rest); every interaction point and the spawn inside it;
   - exits at real doors, gates, path ends and frame edges, interaction points inside the polygon;
   - `walk_band` / `actor_scale` from the camera: the hero (512 px at scale 1) is about 1.7 m tall at the feet line;
     check the ruler in the review overlay; typical back 0.45-0.6, front 0.9-1.0;
   - camera families (`location_families`): design the base era first, then derive the others (below) with
     identical `anchors`, `walk_band` and `actor_scale`.
   Then write the sketch (`<room>.sketch.json`: walls, horizon and furniture of the real place; each prop as its own
   block at its rect; counters and sills at `sill_y`) and the prompt (`<room>.txt`, English, placeholders `{rect:ID}`
   `{exit:ID}` `{walk}` `{npc_zones}` `{anchors}`; image inputs only freely licensed photos, OSM reconstructions,
   our sketches and approved paintings). No TODO may remain.
b. **`python tools/check_blocking.py <room>`**: 0 errors; read every warning and fix it or explain it in the log.
c. **Paint**: `paint_natural.py run <room> --budget <room budget>`. Max 3 attempts, usually 1-2. Before another
   attempt, change the sketch or prompt for a reason you write in the log.
d. **Review**: LOOK at the master, `art/review/natural/<room>_v<N>_overlay.png` and `_crops.png` at 100 %. Every prop
   inside its rect, nothing painted in NPC zones, walk area clear and flat, sills at `sill_y`, no text, logos or
   brands, no people, the real place recognisable. Fix by moving rects to the painting (preferred, free; re-run the
   check) or with `refit fix` for a local repair; re-export the accepted version.
e. **Foreground mask / occluders** when actors walk behind something: `occluders` for objects actors walk both
   behind and in front of (desk, counter, bench, pillar), the mask (`mask <room>`) only for things that are always
   in front (a front railing, a lamp post at the bottom edge). LOOK at the preview.
f. **State art** for this room: every `game.json` `visual_variant_layers` asset of the room needs a `variant_layers`
   entry; every hotspot with `visible_after` / `hide_after` and every action that visibly changes a prop needs a
   `state_patches` entry (`refit fix` the changed state on the accepted master, then `patch ... --from <fix version>`).
   `check_blocking.py <room> --strict` lists what is missing.
g. **Ambient** `data/blocking/ambient/<room>.json` with >= 3 layers (ART_DIRECTION section 5; schema
   `src/game/scripts/Living/README.md`): sway / flicker / water cut from the natural painting with
   `ambient_cut.py --natural <room>` (sprites in `assets/ambient/<room>/natural/`), plus particles, critters, tween
   paths, clouds from `assets/ambient/common/`. Never reference the template cut-outs `assets/ambient/<room>/*.webp`
   (they belong to `bg/<room>.webp`). Audio override in the blocking's `audio` only where the brief or a decision
   asks for it (S57 bus).
h. **In-engine screenshots**: `paint_natural.py screens <room>` (plus `--act` / `--replay` and `--tag` for every state
   with patches or overlays). LOOK at the labels, the staging (feet on the floor, busts on their sill, scale), the
   hero in front of / behind occluders, and the motion frames (every ambient layer moves). Fix and repeat.
i. **Log** `art/masters/bg_natural/<room>.md`: real place and photos used, camera, blocking decisions, attempts with
   seeds and cost, review findings, fixes, open issues, screenshots, and "Register updates for the integrator"
   (status, new source photos, notes). Final gate: `check_blocking.py <room> --strict` with 0 errors.

### Camera families: `derive_era.py`

1. Paint and accept the base era (e.g. S11 1995 for L_STOP) with the checklist above.
2. `derive_era.py init S11 S51` drafts `blocking/S51.json` from the base (same walk polygon, band, scale, spawn,
   anchors; matching hotspots and exits copied - verify each one) and `art/prompts/natural/S51.era.txt` (with the
   `location_families` era text to translate). Finish both; `check_blocking.py S51`.
3. `derive_era.py prompt S11 S51 --from <base version>` (free): prompt and a pre-review of the target rects on the
   base painting (`art/review/natural/S51_from_S11_v<N>_prereview.png`).
4. `derive_era.py run S11 S51 --from <N> --budget <usd>`: one Nano Banana Pro edit of the base master (image 1) with a
   boxes guide (image 2). It measures the camera (global shift, compensated up to 48 master px; local shift at every
   anchor and exit, tolerance 8 px) and writes `art/masters/bg_natural/S51_v<N>.png` + sidecar (kind "derive"),
   `art/review/natural/S51_v<N>_derive.png` (base | derived; base edges in cyan over the derived painting; anchors
   with their measured shifts; target rects) plus the normal overlay, and exports. "CAMERA DRIFT" = do not accept.
5. Continue the checklist from (d) for the target room.

Tool test 2026-10-05 (S05 autumn 2020 -> "June 1995", `--test`, USD 0.15, `art/review/natural/derive_test/`):
global shift 0, every exit 0 px, NCC 0.93-0.96; the season, vine and gate note changed as asked, but the model also
added two trees behind the workshop. Check the "nothing else changes" part on the derive review.
