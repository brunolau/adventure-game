# C1 – GPT check and final control (2026-10-06)

Chunk C1 (2020: Chorvátsky Grob, Čierna Voda, Dúbravka 2020), v2 rewrite in the Polda tone
(`docs/writing/out_v2/C1.csv` = 27 existing keys, `docs/writing/out_v2/C1_ext.json` = new lines,
22 extra topics and the proposed bus link). Method: `design-doc/WRITING_METHOD.md` § 4, steps 2 and 3.

## Step 2 – GPT check

- `tools/gpt_review.py --chunk C1 --overrides docs/writing/out_v2/C1.csv --overlay docs/writing/out_v2/C1_ext.json`,
  openai/gpt-6-astra-pro, all 38 batches, 280 keys, 0 unreviewed → `C1.json`: **36 flags**.
- **Tool fix before the run counted.** The first attempt showed GPT only the *new* lines of an
  extended exchange, appended after the old ones, so GPT judged `action.G02.x01` ("Máme.") as an
  answer that comes too late, although it plays right after Adam's question. That run was stopped
  after G03, and `render_block` now prints extended exchanges in their **full play order** (old and
  new lines interleaved; overlay strings are existing keys). The relative `--overrides` path crash
  is fixed too. Every result in `C1.json` comes from the corrected prompt.
- **Verification pass** (`C1_verify.json`): the 16 blocks where Claude rewrote text itself (adapted
  flags and read-through edits) went through GPT again: **6 flags** (153 keys).

Spend (logged in `art/spend-log.csv`): C1 USD 6.42 (including USD 0.44 for the stopped first
attempt) + verification USD 2.68 + an estimated USD 0.15 row for the call that was in flight when
the first attempt was stopped (its billing is unknown) = **about USD 9.25** of the USD 15 budget.

## Step 3 – decisions

| round | flags | accept | adapt | reject |
|---|---|---|---|---|
| C1 (`C1.decisions.csv`) | 36 | 18 | 13 | 5 |
| verification (`C1_verify.decisions.csv`) | 6 | 0 | 3 | 3 |

By category (round 1): unnatural 12, joke 9, nonsense 8, grammar 4, ty/vy 2, calque 1.
GPT's conversation notes: D07 (the window joke went on after it landed → acted on, see below) and
LENKA (plural *chodíte* is correct → no change).

### Most instructive cases

**Accepted – real Slovak errors GPT is good at**
- `action.C03.x03` `len chladnička má aspoň za čo chytiť` → `len chladničku je aspoň za čo chytiť`
  (impersonal construction).
- `topic.MIRA20.after.x02` `hovoril samé čudné roky` → `spomínal samé čudné roky` (collocation).
- `action.C01.x02` and `look.S09.ambient 1`: commas (`pre prípad, že`; `vie, prečo`).
- `action.D02.x04` `… Spravodlivo rozdelené.` deleted: the old ironic-summary tag that the owner
  called cringy. GPT found four of these (`D02.x04`, `Q1A.x05`, `ROMAN.extra 2.004`,
  `look.S55.ambient 2`).

**Adapted – GPT found the problem, its fix was flat or longer**
- `action.G07.003` `Prístroj, ktorý ma spoznal skôr ako ja jeho.` contradicted G07.001 (Adam
  recognised it first). GPT: `Takže ten prístroj spoznal aj mňa.` → final `Ja poznám jeho a on
  pozná mňa.`
- `topic.DANA.extra 3.004` buying a lot of yeast does not prove the baking fails. GPT dropped the
  joke; final `Podľa toho, koľko chleba si u mňa popritom kupujú, zatiaľ nie.`, so the evidence now
  makes sense.
- `topic.ELA.extra 3.004` (list of lists): GPT's `kde je ktorý z tých troch` makes sense but loses the
  joke; final `Aby som vedela, ktorý z tých troch práve nemôžem nájsť.`
- `action.C05.x03` `Vždy mal sklon k veľkým číslam` was an arbitrary punchline; final `Zapíš si, čo
  hovorí, a potom ho vypni.`: Mira the engineer, and it leads into Adam's `Idem to vypnúť pri zdroji`.
- `topic.MIRA20.extra 1.005` `Za ako dlho?` is a Czech calque; GPT's `Za aký čas?` is bookish; final
  `A ako rýchlo som ju našiel?`
- `action.C04.x04` (the pen): round 1 `dopisuje pero` got flagged again in the verification pass,
  so the final is the unambiguous `Myslela som, že mi pero prestáva písať. Ale pero píše normálne.`

**Rejected – GPT was wrong**
- `action.D07.x01` `Povedzte to ešte raz.` (flagged twice): the *vy* is intended. Tóno switches to
  *ty* in D07.002, after he hears the password twice. The switch is the moment he recognises Adam.
- `topic.TONO20.extra 3.001` `…si urobil sám?` (flagged twice): the topic `requires_done` D07, so
  *ty* is right. The neutral rule only covers Tóno's always-available topics. GPT does not see
  `requires_done` in its prompt.
- `topic.ELA.ambient 2.x04` `Osobné údaje nevydávam, ani keď ide o polievku.`: here the official
  wording is the joke. Ela is quoting her own rule (her role). Same for `action.G03.004` `tak to ber
  ako pripomenuté`, which is ordinary spoken Slovak and not officialese.
- `topic.LENKA.ambient 2.x03` `Vždy vyhrá ten, kto stojí pri dverách.`: this is Lenka's own amused
  answer to `A kto vyhral?`, not a commentary tag.
- `topic.ELA.extra 2.006` was rejected in round 1 as Ela's own reply. GPT flagged it a second time,
  and on rereading it is a generic tag, so it was adapted in the verification round to `Má pätnásť.
  Nech plánuje, zoznamy jej zatiaľ požičiam.` (it keeps the foreshadowing of Nina as the 2035
  curator).

## Lead read-through in story order (own changes, not GPT flags)

The whole chunk was read in play order: G01–G07, C01, D01–D03, D07, C02–C05, Q1, Q2, Q9E, rooms,
then the topics of Dana, Ela, Jana 50, Jozef, Lenka, Mira, Roman and Tóno 50. Changes:

- `action.G02.x03` `Odvtedy to tam mám.` was ambiguous → `Tak som si to tam dopísala.`;
  `action.G02.x04` counted Mira's calls against Ela's third reminder and then repeated
  *tretíkrát* → `Ak ti babka zavolá ešte raz, povedz jej, že už idem.`
- `action.D03.x02` did not follow from Jana's line → `Oto si zapisoval naozaj všetko. Taký zoznam by
  sa mi zišiel aj v garáži.`, so her running gag `Nie zoznam. Záznam.` now corrects something.
- `topic.JANA20.ambient 1.x03` Jana said `v zozname` herself, against her own gag → `v evidencii`.
- `action.D07`: following GPT's conversation note, x06 (`Lebo v dvanástich je okno najbližšie
  letisko.`) is **removed**. The recognition scene closes plainly with x05 `Poviem mu. Slovo od
  slova.` (a serious beat stays plain). D07 is now 13 lines instead of 8.
- `action.C05.x01` `Všetko, čo som nazbieral` sounded like inventory talk (meta) → `Babka, teraz to
  všetko priložím k tvojmu prístroju.` (Mira is on the phone).
- `topic.ELA.ambient 1.x02` `som tu bol o desiatej` → `som prišiel o desiatej`.
- `topic.TONO20.ambient 2.x03` `Do kabinetu.` did not answer *ktoré* → `Tie do kabinetu.`
- `travel.S07.to_S51.first.002` `Prvý raz za mesiac idem ďalej ako k babkinej bránke.` is false if
  the first ride comes after the 1960 trip. Neither the car exit nor the bus exit has a lock, so the
  line is now state-independent: `Autobus je skoro prázdny. Každý sedí pri svojom okne, akoby si ho
  rezervoval.`

Checked and fine: clues stay in their keys (Ela's protocol, Roman's Z-17, Tóno's servisná kniha,
Jana's kópia/originál, D07.006 verbatim), ty/vy per VOICES (Jozef, Jana 50 and Tóno 50 before D07
say *vy*), glossary forms (Bodka – s Bodkom, pani Hrušková, Čierna Voda), labels ≤ 28 characters,
no spoken line over 110 characters in the overlay, no ids.

## Checks

- `tools/check_rewrite.py docs/writing/out_v2/C1.csv --chunk C1`: 0 errors, 3 warnings (the same
  three as before, explained in the notes).
- `tools/gpt_review.py --chunk C1 --check-decisions` and `--name C1_verify --check-decisions`: 0
  problems.
- Overlay lines are not covered by check_rewrite (no Core overlay schema yet). They were checked with
  an ad-hoc lint for length, ids and typography.

## Open questions for the owner

1. **Bus link:** keep the S02 car exit to Dúbravka or replace it with the bus from Čierna Voda
   (S07)? Jozef's tip (`JOZEF.extra 3`) and hint `quest.M11A.hint.1` (variant) assume the bus
   exists. If it is not built, drop both.
2. D07 is 13 lines (1.6 times the original) because it is the recognition beat; the other story
   exchanges are about 2–2.5 times longer.
