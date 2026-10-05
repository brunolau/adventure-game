# Ambient art (living world)

Style A (ART_DIRECTION section 1), generated 2026-10-05 with `art/tools/ambient_art.py`, style reference
`src/game/assets/bg/S02.webp`. Total paid: USD 1.32 of the 10.00 budget (rows `ambient/*` in art/spend-log.csv).

| asset | model | usd | keyed parts | shipped as |
|---|---|---|---|---|
| leaves.png (16 leaves, magenta key) | nano-banana-pro/edit 1K | 0.15 | leaves_parts/ | assets/ambient/common/leaf_00..15.webp (48 px) |
| pigeon.png (8 poses, green key) | nano-banana-pro/edit 1K | 0.15 | pigeon_parts/ | common/pigeon_sheet (stand, peck, look, walk, fly_0..3) |
| car2020.png (silver-blue hatchback, unbranded) | nano-banana-pro/edit 1K | 0.15 | car2020_parts/ | common/car2020 (not used in S01-S11 yet) |
| car1995.png (boxy early-90s hatchback, unbranded) | nano-banana-pro/edit 1K | 0.15 | car1995_parts/ | common/car1995 (S11) |
| cat.png (tabby, magenta key) + cat_video.mp4 | nano-banana-pro/edit 1K + hailuo-02/standard 6 s | 0.15 + 0.27 | cat_walk/ (frames.py loop: 12 frames, 0.67 s cycle, stride 186.7 px/s at 160 px) | common/cat_walk_sheet |
| clouds.png (4 clouds) | nano-banana-pro/edit 1K | 0.15 | clouds_parts/ | common/cloud_00..03.webp |
| ducks.png (female mallards swimming) | nano-banana-pro/edit 1K | 0.15 | ducks_parts/ | common/duck_sheet |

No real people, brands, logos or plates. Everything else (tree/vine/grass cut-outs, masks, the S04 plexiglass
and S06 window-frame occluders, the S06 basket patch) is cut from the painted backgrounds by
`art/tools/ambient_cut.py` (spec `cuts.json`, previews in `preview/`). Glows, dust, steam and the
curtain silhouettes are procedural (`builtin:*` textures in the engine).
