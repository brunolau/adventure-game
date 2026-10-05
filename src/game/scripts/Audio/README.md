# Audio (`scripts/Audio`, `assets/music|ambience|sfx|voice`, `data/audio`)

`AudioService` (node `/root/Main/AudioService`, created by `Main`) owns every sound of the game. It is
presentation only: it listens to `GameRuntime` / `WorldHooks` / `DialoguePresenter` events and never
changes game state. It replaced the world runtime's `Presentation/MusicPlayer` (removed in the issue cleanup, ISSUES AUDIO-01).

## Buses

`default_bus_layout.tres`: Master → Music, Ambience, SFX, Voice. The settings screen
(`UI/Settings/UiSettings.Apply`) sets their volumes and the unfocused mute; the service only routes
its players to the buses (`AudioService.BusOrMaster`).

## Parts

| class | what |
|---|---|
| `AudioService` | wiring, music/ambience choice, game/UI event sounds, voice, `--audio-report` |
| `MusicDirector` | two decks, equal-power crossfade (2 s, `music.json crossfade_seconds`), loop points, resume of a track faded out < 2 min ago (era theme → puzzle cue → back), duck while a voice line plays |
| `AmbiencePlayer` | per-room layers: bed loops + random one-shot spots (stereo position from the canvas x, `AudioStreamPlayer2D`), `after` / `until` action conditions, 1.2 s crossfade between rooms, level offsets for overlays (pause/journal/map −8 dB, puzzle −6 dB) and silence under the main menu / ending |
| `SfxPlayer` | sound ids from `sfx.json`: random take (no immediate repeat), pitch jitter, per-id cooldown, pool of 10 players |
| `AudioCatalog`, `AudioStreams` | data loading, stream cache, loop flags |

## What plays when

Music priority (first match): ending / credits screen → `epilogue`; main menu open → `menu`;
`AudioService.ForcedMusic` (for other agents); Core mode `Puzzle` → `puzzle`; a cutscene listed in
`music.json cutscenes` (CS06 → tension, CS07 → epilogue); a room override in `music.json rooms`
(S48/S49 → tension until F17); else `rooms[].music` of the displayed room (game.json, canonical).
Music files: `assets/music/{1960,1982,1995,2020,2035,menu,puzzle,tension,epilogue}.ogg`; each plays
once from 0 (intro) and then loops `loop_start` → end (baked one-beat crossfade, `music.json`).

Ambience: `data/audio/ambience.json` `rooms.<id>.layers` (every room S01–S68 has 2–5 layers built
from `rooms[].ambience`), library files in `assets/ambience/beds|spots/`.

Sound ids (`data/audio/sfx.json`): the four `actions[].sfx` ids (`item_soft`, `paper`, `tool_click`,
`soft_success`) play when the action commits; events (name = id): `ui_click`, `ui_hover`, `ui_toggle`,
`ui_slider` (every `BaseButton` / `Slider` in the tree is hooked through `SceneTree.NodeAdded`, no
UI code changed), `item_select`, `item_deselect`, `item_added`, `new_goal` (action with an objective),
`inventory_open/close`, `journal_open/close`, `map_open/close`, `pause_open/close`, `puzzle_open`,
`puzzle_success`, `puzzle_fail` (`GameRuntime.PuzzleSubmitted`), `era_transition` (`EraChanged`),
`cutscene_start` (mode `Cutscene`), `saved`.

Voice (reserved): when a line is shown and `res://assets/voice/<line_id>.ogg` exists it plays on the
Voice bus (music ducks −5 dB) and stops when the line changes or is skipped. No voice files yet.

## API for other code

```csharp
AudioService.PlaySfx("tool_click");          // a sound id
AudioService.PlayEvent("puzzle_success");    // an event name (sfx.json events)
AudioService.Instance!.ForcedMusic = "tension"; // cue name or "music/x.ogg"; null = automatic
```

## QA

`<console exe> --headless --path src/game -- --audio-report --quit-after 2` prints every room's music
and ambience layers (`AUDIO REPORT room S01 era 2020 music music/2020.ogg | ambience clock_wall, ...`),
checks that every referenced file loads and ends with `AUDIO REPORT OK` or `FAIL <n> missing`.
Harness runs (any user args) also log `AUDIO music -> ...` / `AUDIO ambience -> ...` changes.

## Rebuilding the assets

`art/tools/music.py` (fal.ai generation, logged spend), `art/tools/audio_master.py music` (loops,
loudness, `music.json`), `art/tools/freesound.py` (CC0 search / download with licence check),
`art/tools/audio_build.py` (ambience library, room layers, sfx, `art/source/AUDIO_CREDITS.md`).
