# C2 – GPT tone check of the whole chunk and Claude's final control (2026-10-06)

Scope: the complete 1995 chunk C2 as drafted in `docs/writing/out_v2/C2.csv` and `C2_ext.json`. That covers Bratislava 1995,
the new room S69 Sokolíkovský dvor, Zuzana at 40, Kubo, side quest Q11 and the relocated B19. The writer's own
GPT run (`C2.json`, `C2_verify.json`) had checked only the changed and new texts. This pass also judges the
unchanged texts in their scenes for the owner's Polda tone. Method: design-doc/WRITING_METHOD.md § 4, steps 2–3.

## GPT runs (openai/gpt-6-astra-pro)

| run | scope | keys | flags | accept | adapt | reject | USD |
|---|---|---|---|---|---|---|---|
| `C2_tone` | whole chunk, `--all-keys`, tone instruction `C1_tone.instruction.txt`, 22 batches (`--merge-small 30`) | 798 | 43 | 11 | 18 | 14 | 10.24 |
| `C2_tone_verify` | only the rewritten texts in their scenes (`--trim-topics`, input `C2_tone_verify.input.csv` + the overlay) | 38 | 6 | 3 | 1 | 2 | 1.18 |

Total: **USD 11.42** of the USD 14 budget, every call is in `art/spend-log.csv`. Decisions with reasons are in
`C2_tone.decisions.csv` and `C2_tone_verify.decisions.csv`. `--check-decisions` passes for both, and still passes
for the writer's `C2` and `C2_verify`.

GPT did not judge these, as in C1 (they are shown as context only, `--skip-role`): names, exit and map labels,
topic and choice labels, objectives, journal, hints, quest goals, item tooltips and locked-exit looks. These were
already in the writer's run 1, and Claude read them in the read-through. No change was needed: the B19 relocation
texts point to the Sokolíkovský dvor everywhere.

## Rewritten in this pass: 35 texts

13 existing keys (`C2.csv`, now 69 rows) and 22 overlay texts (`C2_ext.json`: dialogue lines, the Q11C line, the S69
looks).

- **Old ironic one-liners removed:** Pali *Za obsah… neručí nikto* (he now says what repairmen do vouch for), Adam
  *Takto by mali vyzerať všetky moje opravy* (now a callback to Milada's coat rule), *Typická oprava* at Zita's
  bench (now a question that Zita answers), *Asi má pravdu* (pigeon), *Závidím jej* (ship), *Aj vtedy som mal dobré
  inštinkty* (S17 entry, now *ako na každej fotke*), *Sociálna sieť v dvoch radoch*, the skateboard with wheels too
  small for time travel, *prítomnosť trochu stará* (archive clock), *Spoľahlivejšie ako hodinky* (S69 lamp), and
  Zita's cake and Mira's cassette aphorisms.
- **The character or the situation instead:** Karol keeps a separate card index for small parts. Dezider keeps
  his call sign secret, which is his running gag. Adam tells Kubo not to tap the bell while his fingers are in
  it. The children can hide a watch from their parents, not a lamp. The shy family portrait. Tóno tells keys
  apart *podľa zúbkov*.
- **Sense and grammar:** *Ten ešte nenastal* (it refers to *čas*). No comma before a simple comparison with *ako*
  (3×). *kým nahrávka doznie*. *Po dvadsiatich rokoch… pozerajú*. Kubo's *Keď lopta spadne na balkón* (the old
  *jej* had no referent). Jana's radios now play for *skoro všetkým* deťom. Juro's question now asks what plays on
  the tape. Mira puts soldering second again, without a contradiction.
- **Claude's own fixes that GPT had passed (6):** `action.Q9D.x04`, `topic.KUBO.extra 2.005`, `look.S30.ambient 1`,
  `entry.S17.001`, `look.S21.ambient 1`, `topic.EMIL.ambient 1.x03`. They were all re-checked in `C2_tone_verify`.
- **Read-through edits (not re-sent to GPT, word order and length only):** `look.S69.lamp` and `look.S69.court`
  were shortened to ≤ 110 characters, and the word order of `look.S24.ambient 2` was smoothed.

### Rejected flags (16)
- `action.B09.002` (Milada's coat), `action.B13.004` (archive like a service), `action.Q4C.003` (*prestup*),
  `look.S14.ambient 2`, `look.S16.deck.variant1`, `look.S28.mural`, `topic.Q11C.label` (×2): the same flags as
  in run 1, kept for the same reasons.
- `action.B14.x04`: Alena's 1995 view of phones. GPT's fix would have Adam show a 2020 phone in 1995.
- `action.Q4B.002`: the *zastaviť sa / zastávka* pun works, and Viera answers it.
- `action.Q5B.002`: chalk and a test on the board are clear, and Tóno's reply follows.
- `look.S14.LEA95` (verify): *Vie nechať ticho dokončiť vetu* is Lea's defining trait (VOICES).
- `look.S15.register`: *krabica* is standard Slovak.
- `topic.LEA95.after.001`: after a quotation that ends with *!*, Slovak puts no full stop.
- `topic.SONA.ambient 2.x04`: Soňa's verdict about the boy works.
- `topic.ZUZANA95.extra 2.003`: *Uhlový papier* is the canonical item name (see the open points).

## Checks

- `check_rewrite.py docs/writing/out_v2/C2.csv --chunk C2` with the dialogue and world drafts, and with the
  patched glossary of SOKOLIKOVA_YARD.md § 3.4: **0 errors**. 6 warnings, all from before this pass and explained
  in the notes.
- `check_rewrite.py --overlay-only --overlay docs/writing/out_v2/C2_ext.json`: 0 errors, 0 warnings.
- `content_ext.py check` with the C2 dialogue draft and the world draft (1995 part + 1962 stand-in): OK.
- The bundle `docs/writing/context/C2.md` was regenerated from the drafts.
- Nothing is merged into the live game. As before, the merge needs the 1962 world part of C3 in the same step.

## Read-through in story order

The whole chunk was read in play order: B01–B22, E11, Q3–Q5, Q9D, Q11, the rooms S11–S30 and S69, then all 18
conversations. The read-through checked these points:

- **Clues:** every clue line is unchanged and can still be found: the shapes, the six pieces, 3–2–6, K-17, the
  32 panels, *tri vpravo pri priechode*. ZUZANA95.extra 4 still appears only between B17 and B19. B19.z03 now
  says plainly why the sixth piece was painted twice.
- **Ty/vy:** correct per VOICES. Dezider, Emil, Fero and Zita say *ty*. Tóno stays neutral or uses *vy* before
  E11. Zuzana and Adam say *vy* to each other.
- **Running gags:** they are not overused. The fourth-floor neighbour appears in 3 topics, each time from another
  angle. *Pätnásť dní* is said by Zuzana, Soňa and Q11C and is consistent across them.

**Zuzana rules: respected.** She appears only in S69 in 1995 and never in 2020 or 2035. Nothing is said about
her job, family, home or future, and no line foreshadows anything. She never names Mira or anyone of Adam's
family. Kubo is a neighbour's child. Her 1962 callbacks still match C3_ext.json: *iba do štvorky, dospelí ďalej
padajú*, *Toto bola skúška* / *Toto je skúška*, the *dohoda* to wave, pán Baran's paper. The only Zuzana line this
pass changed is B19.z03, a plain fact about the painted wall.

## Open points for the owner
- Carbon paper: the item is called *Uhlový papier*. In standard Slovak *uhlový* means "angular", and the usual
  term is *kopírovací papier* (GPT flagged *uhľový*). A rename would touch chunk C3 and the glossary, so it is your
  call. The C2 line follows the item name.
