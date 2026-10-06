# C3 – GPT tone pass and Claude final control (2026-10-06)

Scope: the whole C3 chunk (Ivanka June 1962, Dúbravka 7 December 1982, Zuzana 1962 and side quest Q10), after the
C3 v2 writer's pass (`docs/writing/review/C3.md`, GPT runs `C3` and `C3_verify`). This pass judged **every** text of
the chunk again (new, rewritten and unchanged) with the Polda tone instruction used for C1
(`C1_tone.instruction.txt`), then Claude decided every flag, rewrote what still fell short and read the chunk in
story order. Nothing is merged into the live game. The 1962 world texts still go in only together with C2's 1995
part (see `review/C3.md`).

## Inputs and outputs

- Bundle `docs/writing/context/C3_tone.md`: the C3 bundle rebuilt with the draft world overlay applied in-process,
  without writing a live `world_ext.json`. It adds two `###` item blocks (ITEMS1/ITEMS2), so item looks were judged too.
  C1 could not judge them.
- GPT inputs: `C3_tone.input.csv`, `C3_tone.input_dialogue.json` and `C3_tone.input_epilogue.json`, built from
  `out_v2/C3.csv` and `out_v2/C3_ext.json` (same converter as the writer's `C3.input*`). The verification inputs are
  in `C3_tone_verify.input*`.
- Skipped roles: names, labels, goals, objectives, journal entries, hints, rewards, tooltips and hover sentences.
  GPT saw them as context only. Claude read them in the read-through.
- Applied to `docs/writing/out_v2/C3.csv` and `C3_ext.json`. **65 texts changed and one line moved:**
  - `C3.csv`: 34 rows added, all for existing keys whose live text changes.
  - Overlay: 30 lines and one topic label.
  - Q9B: x03 moved after x04.
- `--check-decisions` passes for both runs.

## GPT runs (openai/gpt-6-astra-pro)

| run | scope | keys | flags | accept | adapt | reject | USD |
|---|---|---|---|---|---|---|---|
| `C3_tone` | whole chunk, `--all-keys`, tone instruction, `--merge-small 30` (24 batches) | 840 | 56 | 19 | 19 | 18 | 10.61 |
| `C3_tone_verify` | every rewritten block, with `--trim-topics` and Q10A in full | 147 | 10 | 5 | 2 | 3 | 2.48 |

Total **USD 13.09** (budget 14), logged in `art/spend-log.csv`. GPT gave 0 flags on all eight Zuzana topics, the
epilogue, Q10B–Q10D and Božo.

### Rejected flags (21) and why

- **Tóno 12, ty/vy (8 flags).** Adam always says *ty* to the 12-year-old (`E01` „Ty si Tóno?“). Tóno says *ty* only in
  topics gated on E02. His ungated lines stay neutral.
- **Length on clue lines (5 flags):** I01.003, I09.001, I09.005, E02.009 and look.S39.plate. All are under 160 characters
  and on the editor's accepted list. Each suggestion cut or reworded clue wording.
- **Prepážka → priehradka (2 flags, verification run).** The room is the glossary name „Pošta s prepážkou“ (room, exits,
  map), and *prepážka* is normal Slovak for a counter. This is an owner question (below).
- **Good jokes kept:**
  - I10.004: the blunt stylus "remembers for you".
  - look.S34.ambient 2: the hat "hrá seba".
  - entry.S65.001: the paper's "ambície".
  - Q6C.002: Adam's own self-irony.
- **Q9B.004 kept.** The continuity problem was fixed by moving x03 instead.
- **POSTA.ambient 2.x01 kept.** GPT saw the live text of .002, not the draft text.

## Main changes

- **Term: *uhľový papier*.** *Uhlový* is the Czech form, and in Slovak it means "angular".
  - Changed in every C3 key: I14.001, label and journal, I14.x01/x02, I10.z07, I15.001, the hotspot, the item name and
    look, and M10 hints 2 and 3.
  - `GLOSSARY.md`: CARBON is a bold rename, with a do-not-write row.
  - `glossary.json`: the term regex is now `\buh[lľ]ov\w*`, so the old spelling in other chunks does not break checks.
  - Still to follow in other chunks: C2 `ZUZANA95` („poslali na poštu po uhlový papier“) and C4 `ui.hint_step.I14/I15`.
- **Old ironic tags removed:**
  - entry.S34 *Aspoň nebudem jediný* became a callback to Božo's "obyčajný návštevník".
  - Vera's look *Momentálne môj obľúbený druh umenia*.
  - The bench, the bucket, the empty suitcase, the bottles "bez fyziky", Q7B *názov môjho dnešného dňa* (now the fuse
    running gag), Mira's *otvorenú dokorán*, Oto's explained joke, Alojz's aphorism, and Oto 66's *Aspoň ste sa nezmenili*.
- **Sense and continuity:**
  - I01.005 *Práve vďaka nim to funguje*.
  - I01.x07: *text hry* could be read as a meta joke. It is now Rudo's running gag.
  - I16.x03: Adam now answers *doručenie vám nezaručím*.
  - Q9B order, Q9C *druhý návrh*, E03 *odletel*, and Mira's margin joke.
  - POSTA *služobný holubník*, Štefan's *Položku „niečo“ nevedieme*.
  - Božo's double *aspoň*.
- **Facts:**
  - OTO82.extra 3 said there was no tram to Dúbravka yet, but the S57 1982 picture shows a tram. The tram detail is
    removed; the topic is now about identical blocks of flats.
  - The look.S33 calendar no longer makes the third phone joke in Ivanka.
- **State independence:**
  - RUDO.extra 2 and VERA60.extra 1 are always available, so Adam no longer uses Zuzka's name before he can know it.
  - The Vera label is now „Dievča, čo skáče škôlku“.
- **Zuzana:**
  - Q10A.004 *Naša učiteľka*, not GPT's *súdružka*. ZUZANA.md rules out *súdruh/súdružka* for her.
  - I09.z03 *Ona sa tu ešte nestratila* became *trafí všade aj so zavretými očami*, so there is no "not yet" reading.

## Read-through (story order) and checks

I read the whole chunk in bundle order twice: before the decisions (from the dump) and after them, as a diff. The
order was I01–I17, E01–E10, Q6, Q7, Q9, Q10, then the rooms, the 16 NPCs with all their topics, the items, the quests,
the 8 Zuzana topics and epilogue 10.

Clue lines keep their facts. The Zuzana rules hold:
- She appears and is named only in 1962 texts. A scan found no 1982 mention.
- There is nothing about family, home, job or her future. A scan for banned words was clean.
- The farewell is „To je dohoda.“

Checks:
- `check_rewrite.py out_v2/C3.csv --chunk C3 --overlay out_v2/C3_ext.json`: 0 errors and 2 warnings. The DOBRO "40"
  drop is acknowledged. M10 hint 3 is 212 characters, as before.
- `check_rewrite.py --self-test` and `--overlay-only`: OK.
- `check_strings.py`: OK.
- `content_ext.py check`: OK, with the draft world and the dialogue merged over the live overlays in scratch copies:
  56 extended exchanges, 49 new topics, 516 new lines.

## Open points for the owner / lead

- **Prepážka or priehradka** for the post counter. GPT flagged *prepážka* twice. Changing it means renaming the room
  „Pošta s prepážkou“ (game data name) everywhere, so it is left as it is.
- **Carry the *uhľový papier* fix** into C2 (`ZUZANA95` line) and C4 (`ui.hint_step.I14`, `ui.hint_step.I15`) when those
  chunks are merged.
