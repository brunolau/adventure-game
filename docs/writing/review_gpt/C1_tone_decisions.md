# C1 – tone completion pass (2026-10-06)

Why: the owner found the earlier texts cringy and asked for Polda-style humour. The C1 v2 writer changed
only 27 of the existing keys, so most 2026-10-05 lines had never been judged for tone. This pass checks the
whole 2020 chunk for tone and rewrites what is still flat, an ironic one-liner, or cringy
(WRITING_METHOD.md § 1). Labels, names and exit labels were not touched.

## Inputs and outputs

- Bundle regenerated (`tools/writing_bundles.py --chunk C1`). It now shows the effective game: overlay lines
  and the S07↔S51 bus first-ride lines.
- `docs/writing/out/C1.csv` is now the **complete** C1 draft. It contains the v1 rows and the v2 rows at
  their live texts, plus this pass. The retired `conn.S02.S51.label` row was dropped. Before this pass the
  file still held the outdated v1 texts and failed `check_rewrite`.
- `docs/writing/out/C1_ext.json` is the overlay draft. It is identical to `docs/writing/out_v2/C1_ext.json`,
  which was updated too, so a re-merge from either file keeps this pass.
- Both are applied: `sk_overrides.csv` (+33 rows changed or added via `--overrides-out`) and
  `dialogue_ext.json` (`content_ext.py merge`, 11 line texts).

## GPT runs (openai/gpt-6-astra-pro)

| run | scope | keys | flags | accept | adapt | reject | USD |
|---|---|---|---|---|---|---|---|
| `C1_tone` | whole chunk, `--all-keys`, tone instruction `C1_tone.instruction.txt` | 436 | 35 | 13 | 17 | 5 | 8.31 |
| `C1_tone_verify` | only the rewritten lines, plus the whole S07 block (the main run stopped before it at its cap) | 50 | 5 | 1 | 4 | 0 | 1.30 |

Not judged by GPT: labels, names, objectives, journal, hints, locked-exit looks (skipped with
`--skip-role`), item looks (the bundle's item section has no `###` block), and the four P01/P05
success and wrong lines (budget). Claude read these in the read-through and kept them.

On its own GPT was lenient: 0 flags in G02–G05, DANA and ROMAN. Most of the tone work is therefore Claude's
own: 13 more lines that GPT passed.

### Rejected flags
- `action.D07.x01`: *vy* is intended. The switch to *ty* is the recognition.
- `topic.TONO20.extra 3.001`: this topic `requires_done` D07, so *ty* is right.
- `action.Q2C.003`: this is Jozef's own reaction in his analog-pride voice.
- `look.S06.ambient 2`: *zatiaľ* foreshadows the fading.
- `entry.S08.001`: this is the STYLE_GUIDE 6.2 model line.

## Lines rewritten in this pass: 44

33 existing keys (overrides) and 11 overlay lines. The main changes:
- **Old ironic tags removed:** S04 potatoes (*Aspoň niekto…*), S05 doormat, S07 magnifier, S52 flower pot,
  S03 tape, S51 kerb, Roman's *orientačný bod*, Lenka's *Bodka s pokračovaním*, Jozef's bus,
  `C05.002` *reklamácia*, Adam's *Tú vetu si zapamätám* / *Znie to ako dobrý tím* / *Aj to sa počíta*.
- **Character or situation instead:** Mira books a wake-up call through Ela (`G02.x03`). Adam says Mira will
  correct Roman about the geranium (`C03.x05`). Ela is the team's answer desk, not its boss. The teacher's
  microphone is still on (`ELA.extra 2`). Adam's systematic search proves he is a repairer (`MIRA20.extra 1`).
  The duck keeps its distance since Bodka started coming (S08).
- **Images without meaning replaced:** the globe, the plexiglass, Jana's "rectangle", the cupboard
  "timestamp", the S10 pressure washer, the S07 "technologies".
- **Grammar:** *bledlo* (not *blednulo*), *tu nechám*, *fixka*, *on ma viedol*, *spája kruh s kruhom*.
  Clue lines keep their facts (`check_rewrite` 0 errors).

## Read-through

Read in story order with `scratchpad dump`: actions G01–C05, then Q1, Q2, Q9E, the rooms and the eight NPCs.
One read-through fix: in `entry.S10.001` the comma before *a* became two sentences. One remaining warning:
`look.S05.ambient 2` drops "2020" on purpose.

## Tool changes (`tools/gpt_review.py`)

- `--skip-role`: some roles are shown as context but not judged.
- `--instruction FILE`: adds an instruction to every prompt.
- `--merge-small N` and `--merge-any-section`: batches small blocks together.
- `--trim-topics`: a conversation block shows only the topics that are re-checked.
- `--all-keys-in BLOCK`: judges every key of one block.
- Bundles built from the effective game now work. Overlay lines appear once, in play order. An overlay line
  is re-judged only when its text changed (or with `--all-keys`).

## Open points for the owner
- G04 staging, noted by GPT: Mira speaks to Adam at the gate before she tells him that he would not hear her
  through the glass. The handoff has the same order, so it was left as it is.
