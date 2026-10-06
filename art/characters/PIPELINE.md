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

## 10. Prologue NPC run (2026-10-05): ELA, DANA, MIRA20, ROMAN, LENKA, JOZEF

Budget USD 10 (shared with the prologue item icons), spent **USD 4.39** (37 calls; characters 4.11, icons 0.28).
NPC scripts: `art/tools/npcs.py` (paid: `sheet`, `pose blink|talk|talk_oh|gesture`, `video`; task budget guard
over a prefix list + start time), `mask_talk.py`, `glass.py`, `export_actors.py` (all free, local).

- **House view for NPCs: three-quarter facing right**, Pro 2K with ADAM's keyed 3/4 sprite as cast anchor
  (`npcs.py sheet <ID>`): five of five sheets usable on the first try (ELA reuses the prototype cast sheet).
  Ages, clothes and props follow `characters[].design`; briefs, gestures and idle prompts are in `characters.json`.
- **Face masks (2020) break NB2 talk edits.** Asked to "speak behind the mask", NB2 pulled the mask under the chin
  or painted an open mouth through it on all five masked NPCs. Talk frames for masked characters are therefore
  made locally: `mask_talk.py` finds the light-blue mask and stretches its lower half around a jaw hinge
  (0 at the ear, full at the chin; `--drop 0.14 --fold` and `--drop 0.07`). Eyes and brows stay the base's, so
  alternating talk frames do not flicker the expression. NB2 blinks with a mask are fine.
- **Unmasked talk (MIRA20):** NB2 talk frames also widen the eyes; only a mouth band (0.163-0.225 of the figure
  height) is transplanted so the expression stays stable.
- **Gestures (NB2 2K):** 5/6 first try; ROMAN duplicated his parcel until the prompt said which hand keeps it and
  that there is exactly one.
- **Hailuo idle loops (768p, 6 s, start = end):** MIRA20 (listening on the phone, slow blink, nod) excellent;
  DANA good (hands move to clasped and back); ELA twice turned toward profile and bowed over her clipboard
  mid-clip despite "does not look down" in the second prompt. Shipped ELA idle = ping-pong of the calm first
  2.3 s (head turns toward the road and back); the first clip ships as an optional `idle_checklist` fidget.
  36 frames per idle (6-8 fps). Video cells are softer than the edit stills; switch to talk at a loop boundary.
- **Behind glass:** `glass.py` cuts a bust at the window-sill line (pivot = centre of the cut edge) and bakes a
  pale veil + one soft reflection streak; in a mock window it reads as "behind the pane" while the face stays
  readable (MIRA20 default in S06; optional for DANA in S04; ISSUES ART-NPC-02).
- **Spend log race:** with ~24 calls submitted at once one `log_spend` append was lost (re-logged by hand).
  `fal_api.log_spend` has no file lock; keep parallel batches small or add a lock before the next big batch.
- **Icons:** all eight prologue icons in ONE NB2 2K 4x2 grid on a flat green canvas (ADAM's bag crop as the
  second reference) give matching camera, light and outline; NB2 invents readable text when asked for
  "suggestions of words" and wrote "ENGRAVED RIM" on the chronometer, fixed with one single-icon retake (style
  reference = the grid without the failed cell) and one focused edit. Glass keys to opaque grey glass, which
  reads well. Tools: `art/tools/items.py`, masters in `art/items/`.

## 11. Hero production set (2026-10-05): ADAM

Budget USD 10, spent **USD 7.71** (40 calls, spend-log scope `characters/ADAM/prod/`). Shipped:
`src/game/assets/actors/ADAM/` (28 lossless WebP sheets + JSON + `animations.json` + README with fps, pivots,
strides and playback rules). Masters: `art/characters/ADAM/anim/<name>/` (sheet PNG + JSON, GIF preview on a game
background, contact sheet, `*_review.jpg` with pivot / standing-height guide lines), full-resolution keyed masters
in `masters/`, every paid output with its sidecar in `prod/`. Local build: `art/tools/hero_set.py`
(`prep`, `canvases`, `walk`, `idle`, `talk`, `oneshot [--mask]`, `walkmask`, `export`).

- **Design fix.** The prototype profile hid the mustard T-shirt (strap and closed-looking jacket: it read as a blue
  shirt). Pro edit of the old profile with the 3/4 sheet as clothes reference turned him to 3/4 (40 deg); NB2 with
  two references copied the second reference. What worked: **one-image NB2 2K edit of the old profile**
  (`pose open_jacket_solo`): same face, near profile, jacket hanging open, broad mustard band neckline-to-belt.
  Front/back views are the approved prototype turnaround, **mirrored** so the bag hangs on his left hip as the
  brief says (the turnaround had drawn it on the right hip). Lesson: NB2 sticks to the first image; give it one.
- **One canvas per facing** (1792x2400, figure 1700 px, feet line 2256): every face and pose edit is made on it, so
  edits align; key poses are aligned by the feet (phase correlation of the lowest band; for the crouch, by the
  boots' colour box, because the reaching hand sits in that band). NB2 re-framed the reach_low crouch 1.6x larger
  (measured head and boots) and it was scaled back about the feet.
- **Pose-edit guard.** The style line's "dappled shadows" put sun spots on the jacket and lightened the hair
  (use_tool, reach_high first tries); every `chars.py pose` prompt now carries `POSE_GUARD`.
- **Walks (Hailuo Pro, start = end):** all three usable first time; 16 frames per cycle. Scale comes from the
  standing first video frame (`build_loop --ref_height`), so walk and idle share 512 px. toward/away keep the
  video's vertical positions (`fixed_baseline`): aligning each frame's lowest pixel made the body bob ~20 px,
  because the near foot reaches below the standing feet line in perspective.
- **Idle and talk need no video.** Idle = still master + procedural breathing warp (rows above the hips lift
  0.35 % of the height, smooth falloff to the hips; untouched rows stay bit-identical) + one NB2 blink frame.
  Talk = mouth/jaw band (0.098-0.178 of the height, soft edges) of three NB2 mouth edits; NB2 also raised the
  brows on 'ah'/'oh', which the band excludes. Masked talk = local jaw warp of the mask (no mouth edits).
- **One-shots (Hailuo Pro, start = idle still, end = key pose):** Hailuo moves quickly, then drifts slowly into the
  end frame (reach_low turns from profile to 3/4 over 3 s). Frames are therefore sampled at **equal pose progress**
  p = d0 / (d0 + d1) (`progress_picks`), not equal time; first and last cells are the crisp stills. Prompts must
  not name props: "a high shelf" produced a ghost shelf touching the hand (retake without it).
- **Green fringe on video frames:** 4:2:0 chroma turns thin fingers yellow-green after the plain despill.
  `frames.edge_despill` (on by default for video keys, green key only) caps G near the matte edge for green-top or
  olive pixels; skin and the mustard shirt are outside that rule. `reach_high` in-betweens additionally get a
  skin-tone pull above the head line, where only the hand can be.
- **2020 mask on frames that were not edited:** a mask-only layer (light-blue fabric pieces with attached ear
  loops; skin highlights, eye whites and collar specks are dropped by component filtering) is tracked onto every
  cell by weighted SSD over rotation and scale, following one head centre from cell to cell. Works for all walks
  and five one-shots; for the crouch (head pitched toward the floor) tracking failed, so NB2 painted the mask onto
  those three source video frames (USD 0.24) and only the mask pixels were transplanted.
- **Checks run:** default and mask variants start pixel-identical to idle frame 0; idle and talk bodies are
  bit-identical below the head (legs never move); WebP decodes identical to the PNG masters; Godot 4.7.2 imports
  all 28 sheets headless without errors.
- **walk_left = mirror** (decided after looking at mirrored frames next to the front view; a generated walk_left
  alone would make the bag jump at every stop because idle and actions are mirrored anyway).
- **Not produced:** startled, listen, travel (ISSUES ART-ADAM-01), diagonal walk sheets (reuse rule).

| spend | USD |
|---|---|
| base fix: Pro 3/4 (kept as design and cast reference), 2 failed NB2 profile tries, final NB2 profile | 0.51 |
| walks right / toward / away (Hailuo Pro) | 1.44 |
| face edits side + front (blink, 3 mouths, mask) + back mask (NB2 1K) | 0.88 |
| key poses (NB2 2K) incl. retakes use_tool, reach_high | 0.96 |
| transitions x 6 (Hailuo Pro) + reach_high retake | 3.36 |
| mask edits on 4 key poses + 3 crouch video frames (NB2 1K) | 0.56 |
| **total** | **7.71** |

## 12. 2035 NPC batch (2026-10-05): NINA, TAMARA, BORIS, SARA, ROBOT, VIKTOR, IVAN, TURISTA

Budget USD 15, spent **USD 9.20** (53 calls, spend-log scope `characters/<ID>/`). Tool: `art/tools/npc_prod.py`
(paid `sheet`, `pose`, `video`; free `prep`, `stills`, `idle`, `calm`, `cut`, `export`, `review`). Shipped:
`src/game/assets/actors/<ID>/` (actor.json + lossy-RGB/lossless-alpha WebP grids of at most 4096 px with
`columns`/`rows`, imported by Godot 4.7.2 headless). Masters: `art/characters/<ID>/` (`npc_set/`, `idle_calm/`,
`idle_hailuo/`, `table/` or `counter/`, `face_zoom.jpg`, `idle_strip.jpg`, `idle_face_strip.jpg`). In-engine
check: `build/screens/npc2035/<room>_0n.png` (S41-S68 on the dev blockout; idles animate, grid cells correct).

- **Base sheets** (Pro 2K, ADAM's keyed 3/4 sprite as cast anchor): 8/8 usable first time; ages, alpine-summer
  2035 clothes and props as briefed, no logos. The ROBOT came out facing left and was mirrored (raw kept as
  `sheet_npc_3q_raw_faces_left.png`). A brief with `"pronoun": "it"` gets machine prompts (no human proportion
  rules; face edits address light eyes and a light-dot mouth).
- **Face bands found from the edits:** eyes = peak of the blink edit's changed rows 3-14 % below the figure top,
  mouth = peak of the talk edit's changes 3-10 % of the height below the eyes. Centroids failed: NB2 also
  re-renders collars and hair, and the first build put the mouth band on the neck (TAMARA, IVAN, TURISTA showed
  closed mouths). NB2 changes 7-10 % of the pixels outside the face at mean 7-9/255, so whole-frame swaps would
  flicker; outside the bands the frames are pixel-identical (`stills` prints the changed row spans).
- **NB2 defects caught by looking:** VIKTOR's 'oh' grew a full grey beard (retake with "keep the very short dark
  stubble"); TAMARA's gesture raised the far arm but left the hanging hand (three hands); SARA's open-palm gesture
  added a third hand because both hands held props. Rule: a gesture must use a free hand or the hand that holds
  the prop, say which hand stays where, and say "exactly two arms and two hands".
- **Gesture frames** keep every pixel the edit did not change (pixel-diff patch over the base, legs IoU >= 0.988).
- **Machines:** NB2 re-renders the whole robot shell on a face edit (diff > 40 on most rows), so blink and mouth
  frames take only the inside of the dark glass face panel (convex hull of the largest dark region, rim kept),
  split between eyes and mouth by the two largest glowing blobs. The ROBOT sprite is its real size: 85 cm shell +
  wheels = 249 px at the 512 px = 175 cm adult scale, 344 px with the antenna (`height_px` 344).
- **Video idles (Hailuo-02 Pro 1080p, 6 s, start = end):** feet planted (leg band <= 2.2/255 vs frame 0) and loop
  closure 0.001-0.006 on all kept clips. Every human glanced or bowed down for 2-3 s mid-clip although the prompt
  forbids it, which looks mechanical when looped every 6 s. Shipped therefore (TAMARA, BORIS, SARA, VIKTOR, IVAN,
  TURISTA): `idle` = `calm` = ping-pong of the frames within 4/255 (head band) of frame 0 on both sides of the
  loop point, every 3rd frame at 8 fps (2.25-4.75 s), rotated to start on source frame 0, plus one blink cell (the
  still blink transplanted onto the frame-0 cell, listed in `blink_frames`, shown in ~70 % of loops by the
  engine); `idle_fidget` = the whole clip (cell 0 = the same frame), played every 10-20 s. NINA and ROBOT ship the
  whole clip as `idle` (no glance down; both blink in it).
- **A magenta canvas makes Hailuo spin the figure:** NINA (green coat, magenta key) turned a full 360 degrees in
  two Pro clips despite "does not turn around, does not rotate" (ELA in section 10 also turned toward profile on
  magenta; none of the seven green-canvas clips turned). On a flat **blue** canvas the same prompt held the pose.
  Use blue video canvases for green-wearing characters (`npc_prod.py video ... --image <blue canvas> --bg blue`;
  blue keys cleanly against dark green). `frames.key_kind` read video blue (2, 1, 249) as magenta (R > G) and
  keyed nothing; fixed with a margin (magenta needs min(R, B) > G + 64).
- **Staging variants** (free cuts, pivot = centre of the cut edge, `pivot_is_sill_line`): SARA `counter` (42 % of
  the figure above a ~97 cm counter), TAMARA / BORIS / VIKTOR `table` (55 %, ~76-80 cm table), for the still
  set, idle and idle_fidget; default stays the full figure (rooms not painted yet, ISSUES ART-2035-01).

| spend | USD |
|---|---|
| 8 base sheets (Pro 2K) | 1.20 |
| 24 face edits (NB2 1K) + VIKTOR 'oh' retake | 2.00 |
| 8 gestures (NB2 2K) + TAMARA, SARA retakes | 1.20 |
| 8 video idles (Hailuo Pro) + 2 NINA retakes (magenta, then blue) | 4.80 |
| **total** | **9.20** |

## Ageing cast run (2026-10-05): TONO82 / TONO / TONO20, JANA82 / JANA95 / JANA20 / JANA35, MIRA60 / MIRA95, OTO / OTO82

Budget USD 22, spent **USD 14.55** (91 calls, spend-log prefixes `characters/likeness/` and `characters/<ID>/` from
2026-10-05T04:34). Scripts: `art/tools/ageing_cast.py` (paid: `lineup`, `split`, `base`, `edit`, `plate`, `video`,
`briefs`; task guard over the spend log) and `art/tools/ageing_build.py` (free: `faces`, `canvas`, `headwarp`, `build`,
`export`, `likeness`). Briefs: `art/characters/characters.json` (with `likeness_group` / `likeness_core`).

- **Likeness first.** One Pro 2K 16:9 age-progression sheet per person (`art/characters/likeness/<PERSON>/lineup.png`,
  all ages side by side in the house 3/4 view, same scale); each per-age base is a Pro 2K 3:4 sheet with the lineup
  figure of that age as the FIRST (identity) reference and a cast anchor as the second (ADAM for Tóno and Oto, DANA for
  Jana, the approved MIRA20 sheet for Mira). Final check: `likeness/<PERSON>/<PERSON>_likeness_final.jpg` (shipped
  stills at their real relative size + enlarged heads).
- **Style drift.** The first Jana lineup came out as a flat, outlined mobile-game look and every base inherited it
  (rejected, `rejected/`); with DANA as the cast anchor and an explicit "painterly, natural-sized eyes, no ink outlines"
  line (`PAINTERLY`) it matches the cast. Mira at 20 came out matronly; "petite, slim, not stout" fixed it.
- **Seated figures.** Pro and NB2 paint a seated man with a head 1/7 of the *seated* height (three tries, same pose:
  the fixed seed reproduces the composition), which in the game makes him either a giant or a pin-head. Fix: NB2 seat
  edit of the standing likeness figure, then a local head warp (x1.3 about the chin, identity below the collar line)
  applied identically to the base and every edit (`ageing_build.py headwarp`), scaled so the head matches TONO20.
  Seats are part of the sprite (chair / stool + satchel).
- **Face frames** (NB2 1K): eye / mouth boxes are found from *blurred* differences (the 1K edits are softer and a pixel
  off at every edge, so plain differences light up the whole outline); only changed pixels inside the boxes are
  transplanted. Body pixel-identical to idle in the PNG masters and in the shipped sheets (still sheets are lossless
  WebP: lossy q92 differed by up to 15 levels between cells, a visible shimmer when talk frames alternate).
- **Idle loops**: Hailuo-02 **Pro** 1080p, 6 s, start = end, 48 frames at 8 fps; video px are mapped back through the
  canvas transform (no per-frame recentring), then a global shift + per-channel gain so frame 0 meets the still
  (feet stable within 1 px, loop closure error 2-6/255). Window busts were filmed on the upper body only (sharper
  bust). The Q9C prop variants (JANA95 multimeter, JANA35 old drawing) idle with a breathing warp + built-in blink.
- **JANA20** is a webcam portrait: keyed portrait + painted home plate (Q9C plate: labelled refurbished laptops), the
  video idle composited onto either plate, and a `laptop` variant (Pro laptop prop with a magenta screen, every frame
  perspective-warped into it; 180 px wide, about 1.7x real size so her face reads).
- **Spend log lock**: `fal_api.log_spend` now serialises appends with a lock file (`spend-log.csv.lock`).

| spend | USD |
|---|---:|
| likeness lineups (4 + Jana retake) | 0.75 |
| base sheets (11 + Jana x4 / Mira60 / Tóno x2 retakes; Tóno NB2 seat edit) | 2.82 |
| JANA20 plates + laptop | 0.42 |
| face frames + gestures (11 + Tóno redo) | 4.32 |
| Q9C variants (JANA95, JANA35: prop + gesture) | 0.48 |
| Hailuo Pro idle loops (11 + Tóno redo) | 5.76 |
| **total** (rejected work: Jana style 0.75, Tóno proportions 1.29, Mira60 0.15) | **14.55** |

## 1960 / 1982 NPC batch (2026-10-05): BOZO, BERTA, POSTA, LIDA, RUDO, SKLAD, VERA60, DOBRO, RUZENA, MARTA82, SIMON

Budget USD 18, spent **USD 11.11** (80 calls, all under `characters/<ID>/` in the spend log, cross-checked against the
sidecar JSONs). Ivanka pri Dunaji June 1960 (S31-S37) and Dúbravka December 1982 (S60-S66). Paid calls: `npcs.py`
(new: `pose ... seated`, `fix --instruction`, `pose --model pro`, a light guard on gesture / seated edits against the
style line's "dappled shadows"). Local build: **`art/tools/npc_build.py`** (`base`, `canvas`, `bands`, `stills`, `idle`,
`bust`, `export`, `review`; per-character settings in `art/characters/<ID>/build.json`, review sheets in
`art/characters/<ID>/review/`). Exported to `src/game/assets/actors/<ID>/` in the NPC format (actor.json + sheets),
every WebP a grid of at most 4096 px (`columns` / `rows` in the sheet JSON, read by the grid-aware `SpriteSheet`).

- **Base sheets**: Pro 2K with ADAM's 3/4 sprite as cast anchor, 11 of 11 on model first try (ages and era clothes
  right). Local design fixes, no paid retake: SKLAD's "blue" work clothes came out lilac-grey (hue rotated to workwear
  blue); BOZO's timetable carried invented Latin letters (paper interior re-filled); RUZENA's boots looked like modern
  sheepskin boots (one NB2 1K boots edit, feet band taken wholesale below 82 % of the height). RUDO's costume was only
  mildly oversized: an NB2 "make it too big" edit drew four arms (rejected); the second (arms down, sleeves over the
  hands) is the base. SIMON (green coat) uses the magenta key.
- **Seated VERA60**: NB2 seat edit duplicated the drawing board and added sun spots (rejected); Pro edit of the
  standing sheet is clean (one board on her lap, case on the bench). The bench is part of every frame. Pro kept the
  head size but lengthened the seated body (seated = 0.93 of standing height); the sprite is scaled to 0.86 of 512 px
  as a compromise (head ~8 % smaller than her standing sheet), `actor.json height_px` = 440 so labels sit above her head.
- **Face frames**: NB2 1K blink / 'ah' / 'oh' transplanted in tight eye and mouth bands (`build.json`). New: the edit is
  **colour-matched to the base** before the transplant (per-channel gain + offset on the head outside the band):
  NB2 1K often shifts the whole picture (BOZO's blink edit turned his navy jacket brown and warmed the skin), which
  would pop on every blink. Bodies are pixel-identical outside the bands (checked per cell). SKLAD's first 'oh' edit
  grew a beard (retake); for SKLAD and SIMON the mouth transplant is limited to a soft window around the mouth.
- **Gestures**: NB2 2K, 10/11 usable first time. MARTA82 v1 had two clipboards; both retakes move the one clipboard
  into her other hand (NB2 insisted), so her gesture swaps hands for its 1.2 s hold. BOZO's gesture re-painted the
  timetable hand with a lime smear: only the arm band (10-50 % of the height) is taken from the edit.
- **Hailuo idle loops** (768p, 6 s, start = end, 36 frames, ~6 fps): 7/11 good first time. Male figures in uniform or
  waistcoat (BOZO, POSTA) turned to the camera or to a full profile even when told not to, twice each; what worked was
  a **minimal-motion prompt** ("stands completely still ... gazing at one fixed point; only the chest rises and falls,
  one blink"). SKLAD v1 reached out sideways and DOBRO v1 bowed his head (both retaken once). Video cells are aligned
  to the still idle (Hailuo canvases centre the bounding box, the stills the torso: up to 14 px offset, now 0) so the
  switch to talk frames does not jump. MARTA82's thin pencil vanished with the 1 px matte choke: `video_choke: 0`.
- **Counters / windows**: POSTA (S33 counter), RUZENA (S62 serving window), SKLAD (S35 issue hatch) and MARTA82
  (S65 counter) get `window` / `counter` bust variants (cut at 48 % / 45 % of the height) of both the still set and
  the video idle, POSTA and RUZENA also `window_glass`; default stays the full figure (ISSUES ART-6082-02).
- **Checks**: WebP grids decode at the expected size, Godot 4.7.2 headless import OK (no errors), and every room
  (S31-S35, S37, S60, S62, S65, S66) was screenshotted in a real window with the dev blockout: all actors load, idle
  grids play the right cells (`build/screens/m2chars/`).

| spend | USD |
|---|---:|
| base sheets (11 x Pro) | 1.65 |
| design fixes: RUDO costume (2 NB2 2K, first rejected), RUZENA boots (NB2 1K) | 0.32 |
| VERA60 seat: NB2 (rejected) + Pro | 0.27 |
| face frames (33 x NB2 1K) + SKLAD 'oh' retake | 2.72 |
| gestures (11 x NB2 2K) + 2 MARTA82 retakes | 1.56 |
| Hailuo idle loops (11) + 6 retakes (BOZO x2, POSTA x2, SKLAD, DOBRO) | 4.59 |
| **total** (rejected work 2.18) | **11.11** |

## 1995 NPC batch (2026-10-05): LEA95, SONA, ZITA, EMIL, PALI, VIERA, ARCHIVAR, FOTO, TRH, MILADA, JURO, JURAJ, DEZI

Budget USD 20, spent **USD 13.16** (91 paid calls, spend-log assets `characters/<ID>/...`; rejected work USD 3.02).
Tool: `art/tools/npc_batch.py` (paid `sheet`, `faces`, `face`, `gesture`, `video` in a small thread pool with a
serialised spend log and an in-flight budget reservation; free `build`, `idle`, `busts`, `review`, `export`). Briefs
(English, June 1995, mid-90s Bratislava clothing, no logos, ages locked) in `characters.json`; all 13 speak in
conversations (ambient topics + quest lines), so all 13 have a Hailuo video idle.

- **Base sheets** (Pro 2K, ADAM's keyed 3/4 sprite as cast anchor): 13/13 usable first time. SONA (11) is painted
  with child proportions (`CHILD_RULES`) and exported at **420 px** standing height (adults 512 px; `height_px` in
  actor.json), so she stands ~0.82 of Adam. LEA95 (dark green dress) is magenta-keyed.
- **Face frames** (NB2 1K blink / 'ah' / 'oh'): eye and mouth bands are found per character from the edits
  themselves (blink diff rows = eye line, 'ah' diff rows = mouth line, searched only inside the head window) and
  transplanted with `patch_face`: colour-matched (moment matching on head pixels outside the band; a regression
  slope flattened the contrast of the softer 1K edits), base silhouette and alpha kept, band edges faded, key-coloured
  edit pixels skipped (DEZI's glasses, JURAJ's cheek showed green specks before). Bodies are bit-identical to idle
  below the head in all four face frames (checked per cell). VIERA's first blink edit was washed out with a green cast
  (retake).
- **Gestures** (NB2 2K, transplanted as changed-pixels-only so the unchanged body does not flicker): 11/13 first time.
  JURAJ v1 kept the closed sketchbook under his arm and grew a second one; JURO v1 pressed something phone-like to his
  ear. Retakes that say "the one sketchbook ... nothing is left under his arm" / "holds the headphones out" worked.
- **Hailuo idle loops** (768p, 6 s, start = end; 36 frames over 141 source frames, 6.13 fps): only 5/13 good with the
  brief's prompt ("... does not turn, does not look down"): LEA95, TRH and DEZI turned to the camera, SONA, MILADA,
  JURO and JURAJ bowed their heads, PALI and FOTO looked down sideways, ZITA's pencil vanished from behind her ear for
  ~1.5 s. One retake each with a **positive-only minimal-motion prompt** (stands completely still, keeps the same
  pose, only slow breathing and one blink, eyes stay on the right edge of the frame, the prop stays where it is) fixed
  all ten. Video canvases put the torso centre (= the still set's pivot x) on the canvas centre, so idle frame 0 and
  the still idle differ by <= 2 px in outline (matte choke). Key colour painted into enclosed gaps (MILADA's arm and
  waist) is cleared on video frames only when it is not on the outer edge (`_video_key`).
- **Staging**: every NPC rect in S14-S29 is standing size (150 x 320), so the default is the full standing figure.
  Extra free variants: ZITA `window` / `window_glass` (kiosk, cut at 50 %), TRH `counter` (behind his market table,
  58 %), MILADA `counter` (sewing table, 55 %); select them per room in `data/ambient/actors.json` (`variant`,
  `sill_y` = top edge of the painted counter / sill) once the backgrounds exist (ISSUES ART-1995-01).
- **Export**: lossless WebP still sheets, q92 WebP idle grids (18 x 2, EMIL/DEZI 12 x 3; `columns` / `rows` in each
  JSON), every sheet <= 4096 px; 12.6 MB for 13 actors. Godot 4.7.2 headless import without errors; S17, S18, S19 and
  S25 screenshotted in a real window (dev blockout): sheets load and the grid cells play (`build/screens/npc1995/`).

| spend | USD |
|---|---:|
| base sheets (13 x Pro 2K) | 1.95 |
| face frames (39 x NB2 1K) + VIERA blink retake | 3.20 |
| gestures (13 x NB2 2K) + JURO, JURAJ retakes | 1.80 |
| Hailuo idle loops (13) + 10 retakes | 6.21 |
| **total** | **13.16** |

## Guest walk-ins (2026-10-05): MIRA60, OTO82, TONO82 (ISSUES PT-S18)

Tool: `art/tools/guest_walks.py` (paid `stand`, `fix`, `face`, `video`; free `canvas`, `loop`, `stills`, `export`,
`export_standing`). Spend **USD 1.96** (spend-log scope `characters/<ID>/guest_`). Masters: `art/characters/<ID>/guest/`.

- **Walks (Hailuo-02 Pro, start = end, three-quarter view, "walks in place"):** all three usable first time; 12-cell
  loops scaled from the standing first frame to the shipped figure height (MIRA60 / OTO82 512 px, TONO82 445 px =
  152 cm), cycles 1.08-1.25 s, loop error 0.003-0.005. Shipped as `walk_sheet.webp` + `walk_right` animation in each
  actor.json (OTO82 as a 6 x 2 grid, <= 4096 px); mirrored for left like every NPC clip.
- **TONO82 standing:** the shipped set is seated (S64). NB2 2K "stand up" edit of the base sheet kept the face but left
  the briefcase and a faint ghost leg; a second NB2 clean-up edit changed nothing (NB2 sticks to the first image,
  as in section 11) and its first download broke after billing (both billed). The left-overs were cut locally
  (`clean_tono_stand`: hand boxes + largest component). Two NB2 1K mouth edits ('ah', 'oh') transplanted as a soft
  mouth ellipse only (`mouth_patch`), so the body never flickers. Variant `guest_standing` (height_px 444.7).
- Looked at: the sheets on grey, and in engine (build/screens/fixes/staging/S40_I17_*, S61_E08_*).

## Hero winter coat for December 1982 (2026-10-05): ADAM `coat1982` (ISSUES PT-S20)

Spend **USD 6.60** (24 calls, spend-log prefix `characters/ADAM/coat1982/`; task budget USD 8 shared with the CS07
ports, the TOOLS icon and the S43 lettering). Tool: `art/tools/hero_coat.py` (paid `edit`, `video`; free `masters`,
`build`, `export`, `review`); the set lives in `art/characters/ADAM/coat1982/` with the layout of `ADAM/`, so the
`hero_set.py` stages run on it unchanged (`char = "ADAM/coat1982"`). Shipped: 14 `*_coat1982` sheets next to the
default ones in `src/game/assets/actors/ADAM/` (README there), selected per room by `hero_coat1982_rooms`.

- **Re-dress, do not re-pose.** One NB2 2K edit per facing base (side, front, back) and per default key pose
  (reach_low/mid/high, use_tool, show_item, inventory_combine), all with the same text: closed hip-length charcoal
  wool coat with dark buttons, mustard knitted scarf (the T-shirt's colour), bag strap over the coat, no hat, no
  gloves, "do not move, turn or rescale him". The coat came out the same in 8 of 9 edits; NB2 drew the front view
  6.7 % larger (scaled back about the feet, `rescale_about_feet`) and once a second small head above it (dropped as
  a stray component, `main_figure`); inventory_combine v1 had long scarf ends that read as fiddling with the scarf
  (retake `_b` with "ends tucked in, nothing hangs in front of his hands"); reach_low painted the coat ~24 % lighter
  (per-channel gain on the coat pixels, `match_coat_tone`).
- **Face pixel-identical to the jacket set.** The default head is transplanted onto each coat base: everything
  inside the head box the edit painted as face / hair, but not where it painted scarf (closed + hole-filled mustard
  mask, so the dark knit ribs count), wool or where the default shows its jacket collar, and not where the edit is
  opaque and the default is not (the scarf behind the neck). The default blink and mouth frames are then blended
  with the same weight, so `talk_*` and the idle blink need no new edits. Lesson: a plain row cut at the chin line
  pasted the default neck over the scarf, and an unopened colour mask grabbed the olive face outline.
- **Walks (Hailuo-02 Pro, start = end, the jacket prompts with the jacket wording replaced):** the side walk is
  fine but slower than the jacket clip (cycle 38 video frames against 23), so its cycle window was moved and the
  sheet plays 1.16x faster in the engine to keep the 272 px/s ground speed (no sliding: stride and fps scale
  together). Toward and away v1 walked stop-and-go (leg-motion minima 1-3 against 11-19 for the jacket clips, both
  feet planted ~0.4 s at every step); the retakes `_b` with "brisk, steady, continuous ... no pause between the
  steps" walk continuously (away plays at the side walk's cadence). 20 cells per cycle.
- **One-shots:** start = coat base, end = coat key pose aligned to the coat base by the feet; all six usable first
  time; frames sampled at equal pose progress as before.
- **Download hiccup:** `v3b.fal.media` reads timed out repeatedly; the first `coat_side` result was lost after
  billing (USD 0.12, logged). `hero_coat.save_result` now writes the raw result JSON first and downloads with curl
  (retries), falling back to requests.
- Looked at: edit sheets, head zooms at full and game scale, every walk and one-shot strip, in-engine S57 / S59 /
  S61 / S65 idles, S57 / S61 walks and the S61 E09 reach in the coat (`build/screens/fixes/art/`).

| spend | USD |
|---|---:|
| 9 coat edits (NB2 2K) + inventory_combine retake + 1 lost download | 1.32 |
| 9 Hailuo Pro clips (3 walks, 6 transitions) | 4.32 |
| 2 walk retakes (toward, away) | 0.96 |
| **total** | **6.60** |

## Zuzana, 7, Ivanka pri Dunaji June 1962 (2026-10-06): ZUZANA (S37)

Budget USD 6, spent **USD 2.94** (17 calls, spend-log scope `characters/ZUZANA/`; rejected or unused work USD 0.93). Tools:
`art/tools/zuzana_set.py` (paid: `sheet`, `faces`, `crouch`, `crouch_faces`, `video --kind idle|hop|draw`) and
`art/tools/zuzana_build.py` (free: `build`, `idle`, `hop`, `crouch_prep`, `crouch_build`, `draw`, `export`,
`preview`), both on top of `npc_batch.py`. Shipped: `src/game/assets/actors/ZUZANA/` (5 sheets, actor.json with the
variants `playing` (default), `full`, `drawing`, README). Masters and review sheets: `art/characters/ZUZANA/`.

- **Likeness.** The face and hair come from a family photo supplied by the owner. The photo stays in the git-ignored
  `art/source/owner_refs/`; it is sent to Nano Banana Pro only as an in-memory data URI (no fal storage upload, no
  copy next to the masters), the likeness note of the prompt is kept next to the photo, and sidecars carry a
  placeholder instead of the photo's path or description. Base sheet: Pro 2K with ADAM's cast anchor first and the
  photo last. Three takes: A (cast anchor + photo) chosen; B (+ SONA as a child reference) nearly identical (same
  seed); C (an extra "older, slimmer" note, new seed) came out with a bigger head and a younger face (rejected).
- **Age and height.** Head ~1/5.3 of the height, which matches the cast's head exaggeration for a seven-year-old
  (adults 1/6.5 painted vs ~1/7.5 real; SONA 1/6.2 at 11). Shipped standing height **350 px** (adults 512 px =
  1.70-1.75 m, so ~118-120 cm, a typical seven-year-old; 0.68 of Adam, SONA 420 px). The suggested ~320 px would be
  ~110 cm, a four- or five-year-old next to SONA. Crouched set: 204 px at the same head size (scale from the width of
  the hair bob; a row-width scan merged head and shoulders in the crouch and gave a wrong 2.07x).
- **Crouch.** Pro returned the standing sheet unchanged for "she now crouches ..." (rejected); NB2 2K with "Change the
  pose ... She is no longer standing" crouched her correctly (redrawn 1.49x larger, scaled back by the head).
- **Hopscotch loop (Hailuo-02 Pro, start = end = the standing base, 70 cells at 11.9 fps):** take 1 ("hops on one
  foot ... jumps landing with both feet apart") gave high tuck jumps with the legs folded under the skirt
  (rejected). Take 2 with "small, low, light hops ... feet rise only a little ... knees bend only a little ... arms
  slightly out to the sides" hops on one foot with the other lifted behind, two rounds and a pause. Built with a
  fixed feet line (the standing first frame), so the hops rise above the pivot instead of being flattened.
- **Drawing loop (Hailuo standard):** the key colour drifted to a mint green after 0.15 s (keyed per frame from the
  border median, no problem) and small chalk strokes appeared on the ground (removed by the island filter; they
  would reset at the loop point).
- **Checks:** video cell 0 of idle / play / draw within 1 px of the still idle of its set; still bodies pixel-identical
  outside the face bands; every WebP <= 4096 px; Godot 4.7.2 headless import without errors; actor.json staging
  names resolve with `tools/check_blocking.resolve_staging`. Not yet seen in a real room window (she is not in
  `game.json` / `data/blocking/S37.json` yet); mock-ups at the S37 perspective in `ZUZANA/review/S37_mock_*.jpg`,
  animated in `build/screens/zuzana/S37_playing.gif`.

| spend | USD |
|---|---:|
| base sheets (Pro 2K: takes A, B, C) | 0.45 |
| face frames (3 x NB2 1K) + pointing gesture (NB2 2K) | 0.36 |
| crouch: Pro (unchanged, rejected) + NB2 2K | 0.27 |
| crouch face frames (3 x NB2 1K) + crouch pointing (NB2 2K) | 0.36 |
| hopscotch loop (Hailuo Pro, 2 takes) | 0.96 |
| standing idle + drawing loop (Hailuo standard) | 0.54 |
| **total** | **2.94** |

## Winter variants for Jasná 2035 (2026-10-06): NINA, IVAN, TURISTA (DECISIONS "Jasná 2035 is in winter")

Spend **USD 2.16** (9 calls, spend-log prefix `characters/<ID>/winter/`; the task's three cabin clean plates, USD 0.36,
are under `ambient/jasna_winter/`). Tool: `art/tools/npc_winter.py` (paid `redress`, `gesture`, `video`; free `build`,
`idle`, `calm`, `export`, `review`); masters in `art/characters/<ID>/winter/` (same layout as the default set, so
`npc_prod.py idle` / `calm` run on it unchanged). Shipped as the actor.json variant `winter` (`npc_winter`,
`idle_winter`, `idle_fidget_winter` sheets beside the default ones), staged in the natural blocking
(`npcs.<id>.variant = "winter"` in S42, S67, S68). ROBOT already had its `snow` variant (S41 painting).

- **Re-dress, do not re-pose:** one NB2 2K edit of the accepted base sheet per character ("same person, pose, size;
  change ONLY the clothes for a freezing February day"): NINA closed knee-length bottle-green wool coat, charcoal
  scarf, black gloves, black winter boots (no hat, so she stays recognisable next to EPILOGUE_8); IVAN padded
  slate-blue parka with the same orange shoulder panels, cabin patch and radio, grey beanie, work gloves; TURISTA
  padded brick-red ski jacket, dark-blue bobble beanie instead of the bucket sun hat, grey ski trousers, gloves, the
  same daypack and camera. 3/3 usable first time; body shift 0-3 px, feet within 1 px.
- **Default face pixels:** the face (skin of both figures in the head rows, closed over eyes and brows that touch the
  hair, holes filled) is taken from the default base, so the default blink and mouth edits are blended in with the
  same weight: no new face edits, and the face frames differ from the idle only inside the eye / mouth bands
  (checked per cell). A first mask without the closing missed NINA's near eye (half blink); fixed.
- **Gesture:** NB2 2K edit of the winter base with the brief's gesture (the clothes stay), patched over the base.
- **Video idles:** Hailuo-02 Pro from the winter canvas (NINA on blue, PIPELINE section 12); feet planted (leg band
  <= 2.6/255), loop closure 0.002-0.007. NINA ships the whole clip as idle (no glance down); IVAN and TURISTA bowed
  their heads mid-clip like their summer clips, so they ship the calm ping-pong (`calm`, TURISTA threshold 5) plus the
  whole clip as `idle_fidget`.
- Looked at: `art/characters/<ID>/winter/review.jpg` (default | winter stills, face zoom), the idle strips, and in
  engine `build/screens/jasna_winter/<room>/winter_life_*`.

| spend | USD |
|---|---:|
| 3 re-dress edits (NB2 2K) | 0.36 |
| 3 gestures (NB2 2K) | 0.36 |
| 3 Hailuo Pro idle loops | 1.44 |
| **total** | **2.16** |

## Zuzana at 40 and Kubo, Sokolíkovský dvor 15 June 1995 (2026-10-06, evening): ZUZANA95, KUBO (S69)

Content v2 art run (task budget USD 12 for S69, both actors, icons, state layers and the two epilogue stills; this
part **USD 1.95**, 15 calls, spend-log prefixes `characters/ZUZANA95/`, `characters/KUBO/`; guard
`art/tools/content_v2_budget.py`). Tool: `art/tools/zuzana95_set.py` (paid `sheet`, `faces`, `face`, `gesture`,
`video`, free `choose`) on top of `npc_batch.py` (free `build`, `idle`, `export` unchanged). Briefs in
`characters.json` (no profession, no ring, jewellery, watch, glasses or bag; Kubo is a neighbour's child). Shipped:
`src/game/assets/actors/ZUZANA95/` (512 px, adult) and `src/game/assets/actors/KUBO/` (350 px, like ZUZANA at 7),
each npc still set idle / blink / talk_a / talk_b / gesture + a 36-cell Hailuo idle; staged standing in S69
(`art/masters/bg_natural/S69.md`), so no seated set.

- **Likeness (ZUZANA95).** Pro 2K edit with ADAM's 3/4 cast anchor first, the approved 7-year-old ZUZANA sheet
  second as the identity reference ("the same person 33 years later": face shape, eyes, brows, nose, mouth, hair
  colour and parting), and the family photo supplied by the owner last, handled exactly as for the child (private,
  git-ignored, in-memory data URI only; its likeness note for this sheet is kept next to the photo, sidecars carry a
  placeholder). Take A (seed 1955) **chosen**: clearly the girl grown up (round face, the same eyes and mouth, the
  parted bob), a warm small smile, early-1990s navy blouse with the small round white collar, beige skirt, sandals,
  one chalk stick. Take B (seed 4015) **rejected** (`rejected/`): a longer, older-looking face that reads 50 rather
  than 40 and loses the child's roundness.
- **Kubo.** Pro 2K with the cast anchor and the ZUZANA (7) sheet for child-of-seven proportions only: first take
  usable (red T-shirt with one white band, navy shorts, white socks, plain blue canvas shoes, a graze on the knee).
- **Faces / gestures (NB2).** 6/6 face frames usable first time, transplanted in the eye / mouth bands (bodies
  bit-identical). ZUZANA95 gesture take 1 **rejected** (`rejected/`): the pointing hand also held a second chalk
  stick (two chalks); the brief now points with the empty far hand while the near hand keeps the one chalk; the
  retake's first download broke after billing (USD 0.12 lost, logged), the next retake (`_r3`) is the shipped gesture.
  Kubo's tap-the-bell gesture first time.
- **Idles (Hailuo-02 768p, 6 s, start = end).** Both calm on the first take with the minimal-motion prompts (feet
  planted, one blink, no turn, no bow): shipped whole as `idle`.
- **Download hiccups:** fal media reads stalled twice in this run; `content_v2_budget.py` now routes every save of
  the run through `hero_coat.save_result` / `robust_download` (raw result JSON first, curl with retries).
- Looked at: `ZUZANA95/review/faces.jpg`, `idle_strip.jpg`, the head lineup child | take A | take B, `KUBO/review/*`,
  and in engine (`build/screens/content_v2/S69/`).

| spend | USD |
|---|---:|
| base sheets: ZUZANA95 takes A + B, KUBO (Pro 2K) | 0.45 |
| face frames 6 x NB2 1K | 0.48 |
| gestures 2 x NB2 2K + 2 ZUZANA95 retakes (one lost in the download) | 0.48 |
| idle videos 2 x Hailuo 768p | 0.54 |
| **total** | **1.95** |
