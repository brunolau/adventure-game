# LastBell character art and animation pipeline (prototype on ADAM)

Prototype run 2026-10-05. Budget USD 6.00, spent **USD 4.10** (20 paid fal.ai calls, all in `art/spend-log.csv`
under `characters/`). Style A only (ART_DIRECTION.md section 1). Scripts: `art/tools/fal_api.py` (shared client,
budget guard, spend log), `art/tools/chars.py` (paid generation), `art/tools/frames.py` (free local processing).
Outputs: `art/characters/ADAM/` (plus one cast-consistency test in `art/characters/ELA/`).

## 1. Verdict in short

| part | approach | quality |
|---|---|---|
| model sheets | Nano Banana Pro edit, 2K, flat chroma key, background painting as style reference (first sheet only) | **production quality**: painterly, matches the backgrounds, perfect key |
| derived views | identity reference only (turnaround, profile) | consistent face, clothes, bag and proportions across views |
| face frames (blink, mouth shapes, 2020 face mask) | Nano Banana 2 edit (1K is enough) + local head-band transplant | **production quality**, body pixel-identical, so no flicker |
| body key poses (reach, gesture, use_tool) | Nano Banana 2 edit, 2K | very good, body/legs/bag unchanged, only the arm moves |
| in-betweens of a pose | Hailuo-02 first/last-frame video, start = idle sheet, end = key pose | smooth, natural easing, feet planted; slow, so resampled |
| walk cycles | Hailuo-02 (Pro 1080p preferred) image-to-video, "walks in place", start = end frame | **good**: real walk cycles, static camera, clean loops; softer than the stills, slight per-frame texture boil |
| background removal | local chroma key (free) | no paid removal needed |

All four tested video models kept the man walking in place on the flat green with a static camera on the first
try. The edit-based NPC path is the cheapest and the most consistent; video is worth paying for where motion has to
be fluid (hero walks, hero actions, optional NPC idle loops).

## 2. Models and prices researched (fal.ai model pages, 2026-10-05)

| model (endpoint) | price | used for | result in this test |
|---|---|---|---|
| `fal-ai/nano-banana-pro/edit` | $0.15 / image (1K-2K), $0.30 (4K) | base sheets | best style match; ignores "true profile" (gives 3/4) |
| `fal-ai/nano-banana-2/edit` | $0.08 (1K), $0.12 (2K), $0.06 (0.5K), $0.16 (4K) | views, poses, face frames | nearly Pro quality for edits, follows pose instructions better; **drifts to a flat cartoon look when it invents a new character** (see ELA) |
| `fal-ai/minimax/hailuo-02/standard/image-to-video` | $0.045 / s (768p), 6 s = $0.27 | walk, idle, reach | **best motion and loop closure**, end frame supported; 768p is soft |
| `fal-ai/minimax/hailuo-02/pro/image-to-video` | $0.08 / s (1080p), 6 s = $0.48 | walk | same motion quality, visibly sharper (Laplacian 10.0 vs 7.3; still sheet 14.4) |
| `fal-ai/kling-video/v2.5-turbo/pro/image-to-video` | $0.35 / 5 s, +$0.07 / s | walk | sharpest (1440 px), but magenta colour corruption on the occluded leg/shoe, invented a wristwatch, shuffling steps: rejected |
| `fal-ai/bytedance/seedance/v1/pro/fast/image-to-video` | ~$0.061 / 5 s 480p, ~$0.137 / 5 s 720p (1M tokens = $1) | walk, idle | cheap, but torso turns toward camera mid-walk, colour/contrast drift from frame 6 on in the idle, no end-frame input: rejected |
| `fal-ai/wan/v2.2-a14b/image-to-video` | $0.04 / $0.06 / $0.08 per s (480/580/720p, 16 fps) | walk | small shuffling steps, 16 fps; rejected |
| `fal-ai/veo3.1/fast/image-to-video` | $0.10 / s (720p/1080p, no audio) | not tested | too expensive for sprites |
| `fal-ai/ltx-2/image-to-video/fast` | $0.04 / s at 1080p, 6-20 s | not tested | candidate for long cheap ambient loops |
| `fal-ai/bria/background/remove` | $0.018 / image | not used | local chroma key is free and cleaner |
| `fal-ai/birefnet/v2` | per compute second (no fixed price shown) | not used | same |

Prices in `art/spend-log.csv` are the documented ones above. The account's billing API was not queried.

## 3. Recommended pipeline

Run from `art/tools`. Every paid command takes `--budget` (USD cap for the `characters/` scope of the spend log)
and refuses to submit beyond it.

1. **Brief.** Add the character to `art/characters/characters.json` (English description derived from
   `game.json characters[].design`; age locked). Characters wearing green (ELA, LEA95, NINA, SIMON) get
   `--key magenta` everywhere; everyone else uses `#00FF00`.
2. **Base sheet** (Pro, 2K, 3:4, ~$0.15, budget 1.5 attempts):
   - hero / first character: `chars.py view ADAM side_right` (sends `art/backgrounds/tram-stop.png` as style ref);
   - every NPC: `chars.py view <ID> side_right --cast-ref ../characters/ADAM/keyed/side_right_3q.png [--key magenta]`.
     The approved ADAM sprite is the cast style anchor and replaces the background painting. Without it NB2
     painted ELA as a big-headed, heavily outlined mobile-game figure that does not fit the cast.
3. **Derived views** (only identity reference, never together with the background painting, which leaked the
   tram stop into the key background on the first turnaround test): `view <ID> turnaround --ref <base sheet>`
   (Pro, 16:9, front | side | back in one image = consistent scale), `frames.py split` cuts it into views.
   For a true profile (hero walk) use NB2: `view ADAM profile --model nb2 --ref <turnaround>`.
4. **Key** (free): `frames.py key` / `split`. Edge colours are un-mixed from the key colour, so there is no fringe.
5. **Face frames** (NB2 1K, $0.08 each): `chars.py pose <ID> blink|talk|talk_oh|mask2020 --base <sheet> --res 1K`,
   then `frames.py stills` (or `patch`) transplants only the changed head band onto the base. NB2 changed 1.0-1.4 %
   of the pixels outside the head (mean abs diff ~4/255), which would flicker if frames were swapped whole; the
   transplant makes the body pixel-identical.
6. **Body key poses** (NB2 2K, $0.12 each): `chars.py pose <ID> reach_mid --base <sheet>`. Add new pose prompts to
   `POSE_PROMPTS` for reach_low/high, use_tool, show_item, inventory_combine, NPC gestures.
7. **Motion** (Hailuo-02):
   - canvases: `frames.py canvas <keyed view> video_in.png --size 1080x1080` (figure 80 % of the height, feet at
     90 %); for pose transitions build start and end with `--anchor <base sheet>` so the body does not jump;
   - walk loop: `chars.py video <ID> --image video_in.png --engine hailuo_pro --motion walk|walk_toward|walk_away --tail`;
   - pose transition: `chars.py video <ID> --image start.png --end keypose.png --engine hailuo --motion reach`;
   - idle loop (optional for NPCs): `--motion idle --tail` from the 3/4 sheet.
8. **Frames** (free): `frames.py extract video.mp4 <dir>` then
   - loops: `frames.py loop <dir> <out> --name walk_right --fps 24 --frames 12` (finds the most self-similar full
     cycle after the first 0.6 s, aligns every frame to the feet baseline and the torso centre, scales to 512 px,
     erodes the matte 1 px against video chroma bleed, writes PNG frames, spritesheet + JSON, GIF preview on a
     real background, contact sheet);
   - one-shots: `--range 2,78 --oneshot --playback-fps 12` (skip the sharp first still frame, cut where the motion
     settles; play reversed to return to idle);
   - whole start=end clips (idle): `--range 0,141 --frames 24 --no-recenter`.
9. **Variants**: the 2020 face mask is one NB2 head edit per facing, transplanted onto every frame with
   `frames.py overlay` + `frames.py sheet`. Tested on both Hailuo walks: the mask sits correctly on all 12 frames.

## 4. Quality notes

- **Consistency.** Within ADAM the identity held across Pro, NB2, four edits and six videos: same face, hair,
  jacket, mustard T-shirt, bag, boots. Videos re-render the face slightly every frame (chin and nose shape vary a
  little); at 512 px this reads as painterly life, not as a different person. Across characters the cast anchor
  is required (section 3.2).
- **View control.** Pro returns a 3/4 view even when asked for an exact profile (twice); NB2 produced a near
  profile. 3/4 is acceptable for NPCs; the hero walk was made from the NB2 profile.
- **Flicker.** Edit-based frames: none after the head-band transplant. Video frames: subtle texture boil (painted
  detail re-generated per frame) and small torso rotation within the cycle; Hailuo standard is soft (source
  figure ~600 px), Hailuo Pro better (~840 px). Kling would be sharpest but corrupts colours. I judged motion
  from frame strips and contact sheets; **the GIF previews still need a human playback check.**
- **Keying edges.** Stills: no green in the figure, clean hair, fingers and laces at 100 %; un-mixing removed the
  olive outline the first version had. Video: 4:2:0 chroma bleed left thin yellow-green slivers on hands; the
  1 px matte choke removes almost all of it, and tiny slivers remain only in enclosed gaps (bag/jacket), invisible
  at 1x. Interior protection keeps occluded limbs opaque even where a model paints green bounce light on them.
  Magenta key on ELA: the green vest is fully preserved.
- **Loops.** With start = end frame Hailuo loops close cleanly (loop error 0.003-0.008); the cycle finder picked
  full two-step cycles in all directions (checked: leading foot alternates and returns).
- **Measured cycles** (12 frames, 512 px): walk_right Hailuo Pro 1.08 s cycle, 11.1 fps, stride ~410 px/s at
  512 px figure height; Hailuo std 1.25 s, 9.6 fps, ~274 px/s; walk_toward 0.83 s; walk_away 1.46 s. The engine
  should play a cycle at its `playback_fps` and move the actor at `stride_px_per_s x (actor scale)` to avoid foot
  sliding (values in each `*_sheet.json`; tune by eye). Feet-baseline jitter is the natural bob (height range
  500-526 px).

## 5. Engine integration notes

- Every `*_sheet.json` has `cell`, `pivot` (feet centre, 4 px above the cell bottom), `playback_fps`,
  `stride_px_per_s`, `oneshot`. Pivot = the actor's feet position on the walk polygon; scale by feet y.
- walk_left = mirrored walk_right (the bag then hangs on the other hip; accepted in most adventure games; if
  not acceptable, generate a left profile and one more walk video, ~$0.60).
- Diagonal walking reuses side or toward/away cycles depending on the dominant direction.
- Ship as WebP spritesheets (assets.csv `actors/<ID>.webp`) converted from the PNG sheets; masters stay PNG.

## 6. Cost estimates (documented prices, including retakes)

**NPC** (49 characters, each appears in one room, so one facing + mirror):

| item | model | USD |
|---|---|---|
| base sheet with cast anchor, ~1.5 attempts | Pro 2K | 0.23 |
| blink | NB2 1K | 0.08 |
| talk, two mouth shapes | NB2 1K | 0.16 |
| gesture key pose | NB2 2K | 0.12 |
| retakes on edits (~25 %) | | 0.09 |
| **tier A: edit-only** (idle life = engine breathing shader + blink) | | **~0.70** |
| idle loop video (optional) | Hailuo 768p 6 s | +0.27 |
| gesture in-betweens video (optional) | Hailuo 768p 6 s | +0.27 |
| **tier B: with video idle and gesture** | | **~1.30** |

Special cases are cheaper (JANA20 is a laptop video portrait, MIRA20 is behind a closed window: bust only) or
need one extra prompt (ROBOT, LENKA's dog).

**Hero ADAM** (full set from section 6 of ART_DIRECTION):

| item | USD |
|---|---|
| sheets: side, turnaround, profile (done) | 0.42 |
| walk right (left mirrored), toward, away: 3 x Hailuo Pro | 1.44 |
| reach_low / mid / high: 3 key poses (NB2 2K) + 3 transitions (Hailuo 768p) | 1.17 |
| use_tool, show_item, inventory_combine: 3 key poses + 3 transitions | 1.17 |
| talk (2 mouth shapes) and blink, side and front facing (NB2 1K) | 0.48 |
| idle loops side and front (Hailuo 768p) | 0.54 |
| 2020 face mask, side and front (NB2 2K), overlaid locally on all frames | 0.24 |
| retakes (~40 %) | 2.18 |
| **hero total** | **~7.60** |

About $2.15 of this is already covered by prototype outputs that can be kept if approved (sheets $0.42,
walk_right Pro $0.48, toward/away $0.54, reach_mid $0.39, side talk + blink $0.20, side mask $0.12).

**All 50 characters:** hero ~$7.60 + 49 NPCs x $0.70 = **~$42 (tier A)**; with tier B **~$71**. Recommended budget:
**~$53** for tier A for everyone plus tier B for the ~10 most visible NPCs ($42 + 10 x $0.60 = $48, +10 %), or
**$80** to give every NPC a video idle and gesture, both including ~10 % contingency for re-prompting. Ambient passers-by (ART_DIRECTION 5) are
not included.

## 7. Prototype spend (USD 4.10)

| asset | model | USD | kept? |
|---|---|---|---|
| sheet_side_right (3/4 side) | nano-banana-pro/edit | 0.150 | yes |
| sheet_turnaround, first try | nano-banana-pro/edit | 0.150 | no: background leaked; file `rejected_turnaround_styleleak.png` (logged as `sheet_turnaround`) |
| sheet_turnaround | nano-banana-pro/edit | 0.150 | yes (front, back) |
| sheet_profile_nb2 | nano-banana-2/edit 2K | 0.120 | yes (walk base) |
| pose_talk, pose_reach_mid, pose_mask2020 | nano-banana-2/edit 2K | 0.360 | yes |
| pose_blink_nb2_1k | nano-banana-2/edit 1K | 0.080 | yes |
| walk_right: Kling / Seedance / Wan / Hailuo / Hailuo Pro | video | 0.350 / 0.137 / 0.405 / 0.270 / 0.480 | Hailuo Pro (+ std as fallback) |
| walk_toward, walk_away, reach_mid, idle | hailuo-02 standard | 1.080 | yes |
| idle | seedance 720p | 0.137 | no (colour drift) |
| ELA sheet: NB2 1K vs Pro with cast anchor | nano-banana-2 / pro | 0.080 / 0.150 | cast-anchor version is the reference result |

## 8. Files

- `ADAM/sheet_*.png`, `pose_*.png` (+ `.json` sidecars: model, prompt, references, seed, price): 2K masters.
- `ADAM/keyed/`: transparent full-resolution views and poses (`side_right_3q`, `profile_nb2`, `turn_front`,
  `turn_side_right`, `turn_back`, `talk`, `blink`, `reach_mid`, `mask2020`).
- `ADAM/npc_set/side_*`: edit-based set idle / blink / talk / reach_mid / mask2020 on one pivot, GIF preview.
- `ADAM/walk_hailuo_pro/`, `walk_hailuo/`, `walk_toward_hailuo/`, `walk_away_hailuo/`: 12-frame loops (frames,
  `*_sheet.png` + `.json`, `*_preview.gif`, `*_contact.jpg`); `walk_hailuo*_mask2020/`: masked variants.
- `ADAM/reach_mid_hailuo/` (8-frame one-shot), `ADAM/idle_hailuo/` (24-frame idle).
- `ADAM/walk_kling/`, `walk_seedance/`, `walk_wan/`: rejected comparison loops (kept for reference).
- `ADAM/video_*.mp4` (+ `.json`) and `video_in_*.png` (video inputs). Raw extracted video frames are not kept;
  `frames.py extract` regenerates them.
- `ELA/`: cast-consistency and magenta-key test.

## 9. Open points

- Human playback check of the GIFs (motion judged from strips only).
- Approve 3/4 vs profile as the house view for NPCs; the hero walk uses a near profile.
- Regenerate walk_toward / walk_away with Hailuo Pro for sharpness (they are 768p now).
- Front-facing talk/blink for the hero, and the remaining hero actions, are not generated yet.
- `restyle.py` still has its own key lookup and synchronous calls; it could use `fal_api.py`.
