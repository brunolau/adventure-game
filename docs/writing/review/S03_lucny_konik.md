# S03 Lúčny koník – writing review notes (2026-10-06)

Owner request 2026-10-06: S03 is the real playground "Lúčny koník" in Čierna Voda and the name is used in the game.
Method: design-doc/WRITING_METHOD.md, all four steps.

## What changed (11 keys)

| key | new text |
|---|---|
| room.S03.name | Lúčny koník – výdajné miesto |
| exit.S02.to_S03.label, exit.S04.to_S03.label, exit.S07.to_S03.label, conn.S02.S03.label | Lúčny koník – výdajné miesto (equal to the room name, glossary 3.3) |
| entry.S03.001 | Lúčny koník. Pod prístreškom, kde sa inokedy griluje, teraz Ela vybavuje telefóny aj zemiaky naraz. |
| action.G01.objective, action.G01.journal | Pomôž Mire s nákupom: zastav sa u Ely na výdajnom mieste pri Lúčnom koníku. |
| quest.M01.hint.1 | Začni u Ely na výdajnom mieste pri Lúčnom koníku. |
| ui.hint_step.G02 (ui.csv) | Na výdajnom mieste pri Lúčnom koníku sa s Elou porozprávaj o téme „Babkin nákup“. |
| ui.hint_step.C02 (ui.csv) | Na výdajnom mieste pri Lúčnom koníku sa s Elou porozprávaj o téme „Protokol k babkinej krabici“. |

Kept as they are (natural without the name): the other "na výdajnom mieste" hints (C04, Q2, Q2B), item.CHAIN, the
S55 look, every dialogue line. Topic names are unchanged.

## Steps

1. Drafts `docs/writing/out/S03_lucny_konik.csv` (C1, 9 keys) and `S03_lucny_konik_C4.csv` (2 ui keys);
   `check_rewrite.py` 0 errors, 0 warnings (the dropped word "dobrovoľnícke" is noted per row).
2. GPT (openai/gpt-6-astra-pro, instruction `docs/writing/review_gpt/S03_lucny_konik.instruction.txt`): 4 batches,
   11 keys, **0 flags** (`S03_lucny_konik.json`, `S03_lucny_konik_C4.json`), USD 0.49.
3. Final control (Claude): 0 flags to decide (decision files empty, `--check-decisions` passes). Read in story order
   (headless line dump): Adam arrives from the street, says the entry line, Ela's topic follows; the place name and its
   declension (pri Lúčnom koníku) are right, the old phones-and-potatoes joke is kept, the grill remark matches the
   painted shelter and does not joke about covid.
4. Merged into `src/game/localization/overrides/sk_overrides.csv` (via `--overrides-out`) and ui.csv;
   `extract_strings.py`, `check_strings.py` OK, `check_rewrite.py --self-test` OK, dotnet test green, `--acceptance m2`
   0 failures.

Glossary: "Lúčny koník" added to GLOSSARY.md (3.1 forms, 3.2 named places, 3.3 room S03 renamed) and
glossary.json `places` (`Lúčn\w* koník\w*`), so the checker now protects the name in goals, hints and labels.

Open questions for the owner: none.
