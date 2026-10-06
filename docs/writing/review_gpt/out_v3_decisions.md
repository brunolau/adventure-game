# out_v3: GPT check and final control (round 2, 2026-10-07)

Scope: the drafts in `docs/writing/out_v3/`: knowledge fixes (`knowledge.csv`, `knowledge_ext.json`), Standard / Hard
step hints (`hints.csv`), difficulty UI strings (`ui_difficulty.csv`). Nothing is live. The owner approves the texts
on the review page (`docs/writing/approval/changes_r2.json`, scene ids `R2-…`).

Model: `openai/gpt-6.1-sol-pro` only. Only new or changed texts were judged; unchanged lines were shown as context.
`--all-keys` was never used.

## 1. GPT runs

| run (review_gpt/…) | what was judged | keys | flags | USD |
|---|---|---|---|---|
| `knowledge_C1` … `knowledge_C4` | all 75 table / overlay texts of the knowledge drafts that differ from the live game (48 csv rows; the 3 item purposes are never shown and were read by Claude only), each in its scene (bundles regenerated from the live game: `docs/writing/context/r2_C*.md`) | 75 | 11 | 0.8610 |
| `hints_r2verify`, `ui_difficulty_r2verify` | the texts that were changed after the hint writer's own GPT pass (`hints.json`, `ui_difficulty.json`, same model) and differed from GPT's suggestion: 4 adapted hints, 1 punctuation edit, 2 adapted UI strings | 7 | 3 | 0.1438 |
| `hints_r2final`, `knowledge_final_C1/C2` | texts changed in this final control (8 nudges, 3 dialogue lines; the C1/C2 runs also re-judged the other new lines of those 4 exchanges) | 20 | 3 | 0.2346 |
| `hints_r2where` | 8 "where" hints shortened in this final control | 8 | 0 | 0.1300 |
| **this step** | | **110** | **17** | **1.3694** |

The earlier passes of this workflow (writers' runs, same model): `hints` USD 0.9373 (2026-10-07), `ui_difficulty`
USD 0.1003 (2026-10-06 23:56). Spend of the whole workflow: **USD 2.4070** (USD 2.3067 of it logged today).
Cap: USD 8 for this step, USD 10 for the workflow.

## 2. Decisions on the flags (17 + a re-read of the writers' 18)

Counts of this step: 10 accept, 3 adapt, 4 reject. Every flag is in a `*.decisions.csv` next to its run;
`gpt_review.py --check-decisions` passes for all eleven review files of out_v3.

| key | GPT | decision | final text / reason |
|---|---|---|---|
| `look.S10.chrono` | unnatural | accept | „Stolový uzol s nízkonapäťovou kolískou. …“ |
| `look.S51.clock` | grammar | accept | „… Visel tu už vtedy, keď som chodil do školy.“ |
| `topic.ELA.extra 2.002` | unnatural (twice) | adapt | „Nina? Malá už dávno nie je, má pätnásť a školu cez počítač. …“: answers Adam's „asi už nie taká malá“, keeps „Nina?“ as the introduction of the name, no repeated „učí“ |
| `action.B06.002` | unnatural („zhlasním“) | reject | the owner's own wording; the review page shows the note and the alternative „…ale ako tie hlasy zosilním?“ |
| `action.B19.objective`, `.journal` | grammar | accept | „Zapamätaj si číslice 3–2–6 a …“ (protected 3–2–6 unchanged) |
| `look.S28.mural` | unnatural | reject | the flagged first sentence is the live, approved text and echoes the hotspot name „Povolený výtvarný panel“ |
| `look.S30.dial` | length | accept | „Tri kolieska: 0–9. Štítok písala babka: „Číslice – nákres v Sokolíkovskom dvore.“ …“ (111 characters) |
| `topic.JANA95.extra 1.001` | unnatural | accept | „Vidím, že máte plné ruky práce. Čo to bude?“ |
| `action.Q8B.001`, `look.S45.bench` | calque („lobby“) | reject | „Lobby hotela Grand Jasná“ is the canonical room name (GLOSSARY, S43); same as the writers' `hint.where.Q8C` |
| `hint.where.B21` | nonsense | accept | „Pri meracom stánku na Starom moste, vedľa stojana.“ GLOSSARY S30: the table stands beside the booth. This overrules the writers' adapt in `hints.decisions.csv` |
| `ui.difficulty.easy_desc` | unnatural | accept | „… riešenie hádanky ti na požiadanie doplní.“ |
| `ui.hint.standard_end` | unnatural | accept | „… Presný krok ukáže nápoveda na ľahkej obťažnosti – prepneš na ňu v nastaveniach na karte Hra.“ |
| `hint.nudge.G10` | unnatural | adapt | „Náhradná poistka má rovnaké hodnoty ako prepálená. Patrí presne tam, odkiaľ som tú starú vybral.“ |
| `hint.nudge.Q1C` | calque („postráda“) | accept | „… Niekomu chlpatému už určite chýba.“ |

The writers' own decisions (`hints.decisions.csv` 16, `ui_difficulty.decisions.csv` 2) were read again and stand,
except `hint.where.B21` (above) and the two UI strings that the verify run improved.

## 3. Changes from the final read-through (Claude)

Dialogue (knowledge_ext.json):

- `action.B05.k03` (Pali): „Za Jurom do kazetového klubu v Ružinove. S páskami čaruje, nie nadarmo mu hovoria Juro
  Kazeta.“ This keeps the owner's phrasing („S páskami čaruje Juro Kazeta“, DECISIONS.md) and matches
  `hint.nudge.B07` („niekoho, kto s páskami vie čarovať“).
- `action.C01.k01` (Mira 2020): „A teraz vážne. Ak chceš to mazanie zastaviť, potrebuješ návratový mostík.“ The old
  wording („pustiť sa do mazania“) sounded as if Adam would be the one deleting.

Hints at Standard. Rule (DECISIONS.md "Difficulty settings"): level 1 and level 2 together must not add up to "use X
on Y". In these steps the nudge paired the item with its target, or the where text named the target object:

- Nudges rewritten (the item stays, the target is only hinted): G10, B06, B20, E04, I06, E09, Q1C, Q10D. Example: B06
  was „Nový remienok mám. Magnetofón v škole stále drží kazetu.“ and is now „Nový remienok je presne na mieru. Starý
  som vyťahoval z jedného tvrdohlavého magnetofónu.“
- Where texts reduced to the place: G10, I06, I08, I17, E09, C05, Q5C, Q11C. Example: I17 was „Na povale
  technického archívu, pri kovovej schránke.“ and is now „Na povale technického archívu.“ I06 / I08 say „Pred búdkou
  za parkom.“: check_rewrite found that „skúšobná búdka“ is not introduced before I06.
- Kept on purpose: the puzzle "where" texts explain the rule, never the answer (G11, B16, B22, D05, F16). Steps whose
  only object is the obvious one (the ports F12–F15, the terminal F08 / F10, the switch F09) keep the object as the
  place, because the player must still choose the item or the setting (MONITOR).

## 4. Read-through result

- **Language and tone.** All 11 knowledge exchanges and 5 topics were read in play order with their live lines. ty/vy
  is correct: Tóno 25 says vy, Pali ty, Karol vy, Oto 66 vy, Zuzana says vy and Adam ty to her, Tamara ty. No ironic
  one-liner endings were added. The Zuzana topic speaks only of 1962 and nothing of her later life (ZUZANA.md). Goals
  and hints are clear and contain no jokes.
- **Knowledge rule, machine check.** `tools/knowledge_audit.py` was run in memory (scratch script, nothing written)
  with knowledge.csv, the knowledge overlay entries (replacing their live ids) and all 268 hints as step-hint
  candidates. Every hint and every new line names only what is already introduced or belongs to Adam's background.
  Thirteen mentions remain that are not counted as introductions:
  - Names Adam reads off a visible sign: the map signature in B16.k01, Mira's label on the stand in look.S30.dial,
    Tamara's note on the bench in look.S45.bench, Q8B.001 and Q8B.002. The audit does not model texts on objects, so
    these were judged by hand and accepted.
  - Background or already-accepted rows: the fund in B13.x01, 3–2–6 in B19, the fence in E08.
- **Protected facts.** `check_rewrite` reports 0 errors on knowledge.csv with the overlay, on the overlay alone, and
  on hints.csv. The run on the drafts merged into the live overlay (`content_ext.py check`) is OK. The two hint
  warnings (B07: Juro and the club, introduced by the draft line B05.k03) are expected; the in-memory audit with the
  draft merged confirms they are introduced.
- **Unchanged live state.** No file under `src/game/localization/`, `sk_overrides.csv` or `src/game/data/content_ext/`
  was touched. `check_strings` and `check_rewrite --self-test` pass. `ui_difficulty.csv` holds new ui.csv keys, so
  `check_rewrite` reports them as unknown keys: this is expected until approval, and GPT reviewed them.

## 5. Open questions for the owner (also shown as notes on the review page)

1. `action.B06.002`: keep „zhlasním“ (colloquial, your wording) or the standard „…ale ako tie hlasy zosilním?“?
2. `look.S30.dial` and `look.S45.bench` add small written props: a label on the stand and a note under the bench
   sign. The painting may not show them.
3. `quest.M08.title` changes from „Ručná pumpa“ to „Dielňa v Ivanke“, because the pump is not known yet when the title
   is first shown.
4. On approval the code fallbacks in `src/game/scripts/UI/Common/DifficultyText.cs` must follow the two changed UI
   strings (`ui.difficulty.easy_desc`, `ui.hint.standard_end`). The integrator must also remove the superseded
   C1–C4 overlay entries before merging `knowledge_ext.json` (see its `about`).
5. The rule "Adam never knows what he has not learned" is recorded in DECISIONS.md but is not yet in
   `design-doc/WRITING_METHOD.md` (only the owner changes that file).
