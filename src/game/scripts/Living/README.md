# Living world (`scripts/Living/**`, `data/ambient/**`, `assets/ambient/**`)

Makes the rooms move: sprite-sheet actors and data-driven ambient layers. Visual only; nothing here
reads or changes rules beyond `GameState.IsDone` for optional layer conditions.

`LivingRoot` (instanced by Main under `LivingHost`) registers `SpriteActorVisualFactory` with
`ActorVisualRegistry` (priority 100) and fills every room's `AmbientHost` on `WorldHooks.RoomBuilt`.
Debug args after `--`: `--reduced-motion`, `--no-ambient`, `--ambient-report` (prints the layers of each room).

## Actor sprites (`Actors/`)

- `ActorAnimationSet` reads `assets/actors/<ID>/animations.json` (hero format: one sheet per animation,
  `*_mask2020` and `*_coat1982` variants; a variant set loads the variant's sheets and the default sheet only of a
  clip the variant lacks) or `actor.json` (NPC format: named sheets, frame-name sequences, variants).
- `SpriteActorVisual` (origin = feet = sheet pivot):
  - walk cycle from the movement vector: side cycle (mirrored for left) unless the motion is mostly vertical
    (|dy| > 0.76 to enter, < 0.66 to leave), then `walk_toward` / `walk_away`;
  - ground speed: side = `stride_px_per_s` (the Actor multiplies by the perspective scale); on diagonals the
    speed is raised so the horizontal part equals the stride (max +15 %) and the playback rate follows the
    horizontal travel, so planted feet do not slide; toward/away = `depth_speed_factor` x stride;
  - idle: the facing's loop; the hero's built-in blink is kept in 70 % of the 4 s loops (random blinking);
    single-frame NPC idles blink at the `every_s` interval (15 % double blinks) and breathe procedurally
    (0.5 % vertical scale); video idles play `idle_fidget` now and then at a loop boundary;
  - talk loop while the presenter says the line is being revealed; stops on a rest mouth frame; talk time
    that arrives during a one-shot action is played after it; the back view turns side-on to talk;
  - conversation (`IActorVisual.SetEngaged`, set by `DialoguePresenter` for the NPC of the topic menu, the
    speaker of a line, the NPC an action's lines are aimed at, until the conversation ends + 0.35 s): an NPC
    whose manifest has an `idle_engaged` clip stands in it instead of an activity idle and plays no fidget
    (ZUZANA's hopscotch, owner 2026-10-07); `--clips` logs each NPC's clip per harness screenshot frame;
  - one-shots from `actions[].animation` (`reach_low|mid|high`, `use_tool`, `show_item`, `inventory_combine`,
    NPC `gesture`): forward, hold (`action_hold_s`, overrides per animation), reversed back; walking cancels;
  - every clip switch cross-fades for 80 ms.
- Window busts (placements with `sill_y`) report `CastsShadow = false`, so the world's shadow layer draws no
  feet ellipse on the wall below the sill (ISSUES LIVING-01 / INT-02).
- `ActorStaging` reads `data/ambient/actors.json`: `hero_mask2020_rooms` (ISSUES ART-ADAM-02) and
  `hero_coat1982_rooms` (winter coat in the December 1982 exteriors, ISSUES PT-S20) and `hero_coat2035_rooms` (the
  same coat in winter Jasná 2035, DECISIONS "Jasná 2035 is in winter"; `ActorStaging.HeroVariant`
  picks the hero variant of a room for the factory and the preloader), per-room NPC
  `placements` (`variant`, `sill_y` for window busts, `scale`, `offset_x`, `facing`), walk/hold tuning.

## Ambient layers (`Ambient/`)

`data/ambient/<room>.json` = `{ "room", "notes", "layers": [ ... ] }`, built in file order. Every layer is one
Node2D at the room origin that draws in canvas px (1920x1080), so one shader can clip or mask it.

Common fields: `id`, `type`, `plane` (`back` = behind actors, default; `front` = above the foreground mask;
`actors` = y-sorted with the hero at `sort_y`), `alpha`, `modulate`, `z`, `blend` (`mix`/`add`), `clip`
[x,y,w,h], `mask` (alpha texture; `mask_rect` from the manifest), `mask_invert`, `speed_scale`, `prewarm_s`,
`reduced_motion` (`freeze` | `hide` | `slow`), `era`, `if_done` / `unless_done` (action ids), `disabled`.

| type | what | main fields |
|---|---|---|
| `sway` | wind on a cut-out of the painting (tree crowns, grass, vines, hanging baskets, notes) | `texture`, `anchor` (0 top..1 bottom, still line), `hang`, `amp_px`, `freq`, `wavelength_px`, `flutter_px`, `gust` |
| `water` | ripples + moving glints on a cut-out of the water | `texture`, `amp_px`, `speed`, `glint`, `glint_color` |
| `particles` | presets `leaves`, `dust`, `snow`, `rain`, `steam` | `emit_rect` / `emit_points`, `rate` or `count`, `size`, `speed_x/y`, `wind`, `land_y`, `rest_s`, `textures`, `colors`; breath: `pulse_s` + `pulse_on_s` (puffs), `follow` `hero` / `npc:<hotspot id>` (emit at that actor's mouth: `follow_offset` [x, y] in figure heights, x toward the side it faces, `follow_push`, scaled by its perspective) |
| `tween_path` | something crossing now and then: birds (flocks), cars, a cat, shadows behind curtains | `sheet`/`texture`, `frames` (list or name prefix), `fps`, `path`, `speed_px_s`/`duration_s`, `every_s`, `start_s`, `direction`, `faces`, `scale` [start,end], `flock`, `bob_px`, `fade_px` |
| `critters` | ground birds that peck/look/walk, flee from the hero and fly back | `sheet` (frames stand, peck, look, walk, fly_0..3), `count`, `ground` [[x,y],[x,y]], `scale`, `flee_radius`, `return_s`, `exit` |
| `flicker` | light: `fluorescent`, `pulse`, `blink`, `noise`, `sweep` | `rect` or `pos`+`size`, `texture` (default `builtin:glow` / `builtin:softrect`), `color`, `min`, `max`, `period_s`, `duty`, `every_s` |
| `clouds` | painted clouds drifting with parallax, wrapping | `textures`, `band`, `count`, `speed_px_s`, `scale`, `x_span` (+ a sky `mask`) |
| `rotor` | clock hand (tick with overshoot, or sweep) | `pivot`, `length`, `tail`, `width`, `color`, `mode`, `period_s` |
| `sprite_loop` / `cutout` | frames at a fixed place / a static piece (occluder, patch) | `sheet`/`texture`, `pos`, `scale`, `fps`, `frames`, `ping_pong`, `pause_s` |

Textures: paths under `assets/ambient/` (`common/…` shared sprites, `<room>/…` cut-outs and masks; a sheet is
`name.webp` + `name.json` like the actor sheets) or `builtin:dot|glow|puff|streak|softrect|silhouette|white`.
Cut-outs without `pos` take their position from `assets/ambient/manifest.json`.

Reduced motion (`PresentationSettings.ReducedMotion`, polled every frame): sway, particles, clouds, loops and
critters freeze (shader time stops), flickers hold their mean brightness, things crossing the screen hide.

## Art

- Cut-outs, masks and patches are cut from the painted backgrounds for free by `art/tools/ambient_cut.py`
  from `art/ambient/cuts.json`; `--check` reports rooms whose background was repainted since (re-run with
  `--only <room>`; positions update through the manifest).
- Shared sprites (leaves, pigeon, two cars, cat walk loop, clouds, ducks) were generated in style A by
  `art/tools/ambient_art.py` (nano-banana-pro, Hailuo-02 for the cat walk), chroma-keyed locally; sources
  and spend in `art/ambient/` and `art/spend-log.csv` (scope `ambient/`).
