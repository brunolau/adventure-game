# ADAM: hero animation set (production, 2026-10-05)

Style A, hand-painted (design-doc/ART_DIRECTION.md). Design per `game.json characters ADAM.design`: blue work
jacket worn **open over a mustard T-shirt** (visible in every view, including the side walk), brown leather
messenger bag on his **left hip** (strap over the right shoulder), short dark hair, dark jeans, brown shoes; every
animation also exists as a **2020 face-mask variant** (`*_mask2020`) and a **December 1982 winter-coat variant**
(`*_coat1982`, section below). Masters, sources and the build script:
`art/characters/ADAM/` and `art/tools/hero_set.py` (pipeline notes: `art/characters/PIPELINE.md` section 11).

## Files

- `<name>.webp`: spritesheet, one horizontal strip of equal cells (lossless WebP, frame i at x = i * cell_w).
- `<name>.json`: `frames`, `cell` [w, h], `pivot` [x, y], `playback_fps`, `oneshot`, `stride_px_per_s`, `facing`,
  `mirror_for_left`, `variant` (`default` | `mask2020` | `coat1982`), `standing_height_px`, and per animation `cycle_seconds`,
  `mouth_sequence`, `blink_frames`, `item_anchor_last_frame` or `note`.
- `animations.json`: manifest of all 42 sheets (default, `mask2020`, `coat1982`).

## Geometry (same for every sheet)

- **Pivot = feet centre** on the walk polygon. Put the pivot on the actor's position; scale the sprite by the
  room's feet-y perspective. The standing figure is **512 px** tall (hair to soles) at scale 1.0 in every sheet,
  so switching animations never changes his size.
- Cells are **symmetric around the pivot x** (`pivot.x = cell_w / 2`), so a plain horizontal flip mirrors any
  sheet without moving him. **Left-facing = mirror of the `*_right` sheets** (`mirror_for_left: true`).
- Most pivots sit 4 px above the cell bottom. `walk_toward` and `walk_away` extend below the pivot (the near foot
  reaches lower in perspective), so always use the JSON pivot rather than the cell bottom.
- Seamless joins: frame 0 of every one-shot sheet and frames 2, 6 and 11 (`rest`) of the `talk_*` sheets are
  pixel-identical to frame 0 of the matching `idle_*` sheet (same variant; verified). Start an action from idle
  frame 0, or accept a breathing offset of at most ~1.8 px when switching mid-breath.

## Animations

| name | facing | type | frames | fps | length | cell | pivot | stride px/s | left |
|---|---|---|---|---|---|---|---|---|---|
| `idle_right` | right | loop | 32 | 8.0 | 4.00 s | 146x524 | 73,520 | - | mirror of right |
| `idle_front` | front | loop | 32 | 8.0 | 4.00 s | 188x524 | 94,520 | - | - |
| `idle_back` | back | loop | 32 | 8.0 | 4.00 s | 190x524 | 95,520 | - | - |
| `walk_right` | right | loop | 16 | 16.7 | 0.96 s | 370x521 | 185,517 | 272.3 | mirror of right |
| `walk_toward` | front | loop | 16 | 13.24 | 1.21 s | 206x531 | 103,516 | - | - |
| `walk_away` | back | loop | 16 | 10.97 | 1.46 s | 240x553 | 120,521 | - | - |
| `talk_right` | right | loop | 12 | 10.0 | 1.20 s | 146x522 | 73,518 | - | mirror of right |
| `talk_front` | front | loop | 12 | 10.0 | 1.20 s | 188x522 | 94,518 | - | - |
| `reach_low_right` | right | one-shot | 12 | 12.0 | 1.00 s | 338x522 | 169,518 | - | mirror of right |
| `reach_mid_right` | right | one-shot | 10 | 12.0 | 0.83 s | 400x523 | 200,519 | - | mirror of right |
| `reach_high_right` | right | one-shot | 10 | 12.0 | 0.83 s | 358x581 | 179,577 | - | mirror of right |
| `use_tool_right` | right | one-shot | 16 | 12.0 | 1.33 s | 318x524 | 159,520 | - | mirror of right |
| `show_item_right` | right | one-shot | 10 | 12.0 | 0.83 s | 370x523 | 185,519 | - | mirror of right |
| `inventory_combine_front` | front | one-shot | 14 | 12.0 | 1.17 s | 198x522 | 99,518 | - | - |

Each row also exists as `<name>_mask2020` with the same frames, fps, cell and pivot.

### Directions

- Right / left: `*_right` sheets, flipped for left. Toward the camera: `*_front` / `walk_toward`. Away:
  `idle_back` / `walk_away`. The handoff's 8-direction walk reuses these by the dominant direction of motion
  (diagonals take the side cycle unless the motion is mostly vertical); see ISSUES ART-ADAM-01.
- Actions are side-facing (right, mirrored for left): face the hotspot horizontally before playing them.
  `inventory_combine_front` faces the camera.

### Playback notes

- **walk_right**: play at 16.7 fps and move the actor at `stride_px_per_s x actor scale` (272 px/s at scale 1)
  so the planted foot does not slide; tune by eye per room. Leading foot alternates over the 16 frames (two steps).
- **walk_toward / walk_away**: `stride_px_per_s` is null. The video walks in place, and the measured sideways foot
  travel says nothing about speed in depth. Move along y at a per-room speed tuned by eye (start near
  0.25 x the side stride x actor scale).
- **idle_***: 4 s loop; calm breathing (shoulders and head rise ~1.8 px, legs never move) and one blink at frame
  22 (front and right; the back view only breathes). Built from the still masters, so there is no texture flicker.
- **talk_***: lip-flap loop over the mouth shapes `a, e, rest, o, ...` (`mouth_sequence`); only the mouth/jaw band
  changes, body and eyes are pixel-identical to idle. Loop it while a line plays; stop on any `rest` frame.
- **One-shots** (`reach_*`, `use_tool`, `show_item`, `inventory_combine`): play forward once, hold the last frame
  while the action resolves, then play the same frames **reversed** to return to idle. The first and last frames
  are the crisp still poses; in-betweens come from a video and are a little softer (reads as motion).
- **show_item**: `item_anchor_last_frame` = [336, 116] is the cell point on the open palm where the bottom centre
  of the selected item's icon can be drawn (approximate; mirror x for left-facing: x' = cell_w - x).
- **use_tool**: he works with a small screwdriver that appears in his hand during the motion (the tool is part
  of the sprite; the same animation serves every `use_tool` action).
- **reach_high** is not referenced by any game.json action yet (reach_mid 49x, reach_low 1x); it is delivered
  because ART_DIRECTION section 6 lists it.

### 2020 face mask (`*_mask2020`)

Use the mask variant **outdoors among people in 2020**. game.json has no per-room flag (ISSUES ART-ADAM-02);
recommended set: the 2020 exteriors S02, S03, S04, S05, S06, S07, S08, S51, S52, S55, S56. No mask in his own
garage S01, the empty workshop S09/S10 and the interiors S53/S54. Switching variant only swaps the face: every
mask sheet has the same timing and geometry as its default sheet. Talk with the mask moves the mask's lower edge
with the jaw (the mouth is hidden), and the back view shows the ear loops.

### December 1982 winter coat (`*_coat1982`, ISSUES PT-S20)

Adam wears a closed hip-length charcoal-grey wool coat with dark buttons and a mustard knitted scarf over it (the
mustard of his T-shirt), the same brown messenger bag on his left hip with the strap over the coat, the same jeans,
shoes, face and hair. Every default animation exists as `<name>_coat1982` (14 sheets, variant `coat1982`).
Rooms: `data/ambient/actors.json` `hero_coat1982_rooms` = the 1982 exteriors S57, S58, S61, S62, S64, S66 and the
issue room S65 (a short errand straight from the S62 yard); the school interiors S59, S60, S63 keep the jacket.
The same sheets dress him for winter Jasná 2035 (6 February, owner 2026-10-06): `hero_coat2035_rooms` = the
exteriors S41, S42, S45, S48, S50, the open Priehyba station hall S67 and the unheated Funitel cabin S68; the heated
interiors S43, S44, S46, S47, S49 keep the jacket.
Masters and build: `art/characters/ADAM/coat1982/`, `art/tools/hero_coat.py` (PIPELINE.md, coat section).

- **Same face, pixel for pixel:** the head of the three facing bases is the default master's (transplanted above
  the scarf), so `talk_*` and the idle blink use the default mouth and eye frames unchanged; only the scarf covers
  the neck and chin line.
- **Same geometry contract:** 512 px standing height, pivot = feet centre, cells symmetric about the pivot, left =
  mirror of `*_right`, frame 0 of each one-shot = idle frame 0. Cells differ from the default sheets (the coat is a
  different silhouette), so always read the coat sheet's own JSON.
- **Walks** are new Hailuo clips with 20 cells per cycle (the default walks have 16): `walk_right_coat1982`
  14.64 fps, 1.366 s cycle, stride
  272.3 px/s (the same ground speed as the jacket walk; the clip was played
  1.16x faster to get there, so the feet do not slide);
  `walk_toward_coat1982` 14.55 fps / 1.375 s and
  `walk_away_coat1982` 14.64 fps / 1.366 s (the side
  walk's cadence). His steps in the coat are a little longer and slower than in the jacket.
- **One-shots** (reach_low/mid/high, use_tool, show_item, inventory_combine): the default key poses re-dressed
  (NB2 edit of the same pose) and new Hailuo transitions; same frame counts and fps as the default sheets.

## Known limits (honest list)

- Video-derived frames (walks, one-shot in-betweens) re-render the painted texture every frame; at 512 px this
  reads as slight painterly boil, not flicker. Still-based sheets (idle, talk, first/last action frames) have none.
- Raised or thin fingers in video frames are softer than in the stills (`reach_high` in-betweens most of all);
  residual green fringe was removed, but a few finger-gap pixels are darker than skin at 1:1.
- Mirroring puts the bag on his right hip when he faces left (the common adventure-game convention). Turning
  between a side view and the front/back view therefore moves the bag across in one of the two directions.
- The GIF previews in `art/characters/ADAM/anim/<name>/` still need a human playback check at real speed.
