# S30 Merací stánok na Starom moste – writing review notes (2026-10-06)

Owner decision 2026-10-06 (docs/DECISIONS.md "Owner answers (2026-10-06, afternoon)"): S30 is the measuring booth on the
old Starý most (the natural painting `bg_natural/S30.webp`, log `art/masters/bg_natural/S30.md`), renamed
„Merací stánok na Starom moste“. Texts that still described an embankment shelter now name the bridge.
Method: design-doc/WRITING_METHOD.md, all four steps.

## What changed (21 keys)

| key | new text |
|---|---|
| room.S30.name | Merací stánok na Starom moste |
| exit.S28.to_S30.label, conn.S28.S30.label | Merací stánok na Starom moste (equal to the room name, glossary 3.3) |
| item.NODEMAP | Mapa vedie k Deziderovej garáži a k meraciemu bodu na Starom moste. Ktorý rok ukáže, zistím až meraním. |
| item.NODEMAP.purpose | Ukázať Deziderovi; potrebná pri meraní na Starom moste v roku 1995. |
| item.COIL | Izolovaná meracia cievka. Patrí do kruhového držiaka v meracom stánku na Starom moste. |
| item.COIL.purpose | Nasadiť do držiaka v meracom stánku na Starom moste. |
| item.METRONOME.purpose | Nezávislý rytmus na meranie na Starom moste v roku 1995. |
| action.B17.001 (Dezider) | Túto mapu sme kreslili s Mirou. Tu máš cievku k stojanu na Starom moste. Ešte potrebuješ nezávislý rytmus. |
| action.B18.objective = .journal | V stánku na Starom moste nasaď cievku do držiaka pri meracom stojane a metronóm polož na stolík. |
| action.B19.objective = .journal | Na meracom stojane v stánku na Starom moste nastav 3–2–6. |
| action.B20.journal | Deziderova cievka sedí v držiaku na Starom moste. |
| action.B21.journal | Emilov metronóm tiká na stolíku pri meracom stánku. (the round table stands at the railing beside the booth) |
| quest.M07.goal | Nájdi meraním na Starom moste časové okno do Ivanky 1962. |
| quest.M07.hint.3 | … → cievka na držiak na Starom moste → … (194 characters; the rest unchanged) |
| puzzle.P03.title | Kalibrácia na Starom moste |
| ui.hint_step.B20 (ui.csv) | Deziderovu meraciu cievku použi na držiak v meracom stánku na Starom moste. |
| ui.hint_step.B21 (ui.csv) | Emilov metronóm polož na stolík s rytmickou značkou pri meracom stánku na Starom moste. |
| ui.hint_step.B22 (ui.csv) | Keď máš zachránenú kazetu aj úplnú mapu, nastav na meracom stojane v stánku na Starom moste 3–2–6. |

Kept as they are (true on the bridge as well): `entry.S30.001` and the S30 looks (Dunaj, Loď, Zábradlie, the coil
holder, the table, the three wheels), `action.B16.001` ("k meraciemu stojanu pri Dunaji"), `quest.M07.title` „Rytmus na
Dunaji“, the CS03 lines. The other "prístrešok" texts (`entry.S03.001` Lúčny koník, `action.C03.001` Z-17) are other
places and stay.

## Steps

1. Drafts `docs/writing/out/S30_starymost.csv` (C2, 18 keys) and `S30_starymost_C4.csv` (3 ui keys);
   `check_rewrite.py` 0 errors, 0 warnings (the dropped words *nábrežný / nábreží / prístrešok* are noted per row; two
   texts shortened to stay under the soft limits).
2. GPT (openai/gpt-6-astra-pro, instruction `docs/writing/review_gpt/S30_starymost.instruction.txt`): the standard C2
   bundle has no blocks for the items section, so a focused bundle `docs/writing/context/S30_starymost.md` was assembled
   from the C2 / C4 blocks that hold a changed key (B16-B22, S28, S30, M07, P03, the three items, the M07 step hints),
   with every text replaced by the current table text and the S30 picture described from the new painting. One merged
   batch, 21 keys (input `docs/writing/review_gpt/S30_starymost.input.csv`), **2 flags**, USD 0.35
   (`S30_starymost.json`).
3. Final control (Claude, `S30_starymost.decisions.csv`, `--check-decisions` passes):
   - `item.METRONOME.purpose` **accepted**: purpose takes *na* in Slovak (*na meranie*, like the topic „Metronóm na
     meranie“); *pre meranie* was a calque.
   - `quest.M07.goal` **rejected** ("do Ivanky v roku 1962"): *Ivanka 1962* is the era name the game uses for the time
     window everywhere (era chooser, B22 objective, journal scene); this pass only replaces the embankment.
   Read-through in story order (headless line dump `--play 33 --lines`): Dezider's B17 line, the arrival in S30 and
   B20-B22 read naturally; the goal card, journal and hints name the same place as the room label and the map.
4. Merged into `src/game/localization/overrides/sk_overrides.csv` (via `--overrides-out`, only these rows changed) and
   ui.csv; `extract_strings.py`, `check_strings.py` OK, `check_rewrite.py --self-test` OK, Godot import.

Glossary: GLOSSARY.md 3.1 (Starý most: na Starom moste / na Starý most / zo Starého mosta), 3.2 (merací stánok na Starom
moste replaces nábrežný merací prístrešok), 3.3 (S30 renamed), 6.1 (P03 Kalibrácia na Starom moste); glossary.json
`places` "Starý most" (`\bStar(ý|ého|ému|om|ým) most(a|e|u|om)?\b`), so goals, hints and labels keep the name;
VOICES.md Dezider (role line and example).

Open questions for the owner: none.
