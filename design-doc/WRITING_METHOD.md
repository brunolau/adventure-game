# Posledný zvonec – writing method (binding for every Slovak text)

Added 2026-10-06 on the product owner's request ("Lets rewrite it in polda style humor ... you write it
like before and control it by GPT ... then one more control by you ... make dialogues 2-3 times longer
... add a bit more topics"). This method applies to every player-visible Slovak text from now on:
the current rewrite, new content, fixes after playtests, ports and later languages built on the
Slovak text. Only the product owner can change it; a change is recorded in `docs/DECISIONS.md` and
here.

The detailed craft rules are in `docs/writing/STYLE_GUIDE.md` (tone, humour toolbox, Slovak, era
flavour, lengths), `docs/writing/VOICES.md` (who speaks how, ty/vy, how each person is funny,
running gags, ideas for extra topics) and `docs/writing/GLOSSARY.md` + `glossary.json` (names, terms,
protected facts, checker rules). This file says **what** the method is and **who does what in which
order**.

## 0. What never changes

The handoff (`design-doc/game.json`, `walkthrough.json`, `runtime_contract.ts`) stays the source of
the game. Writing changes **how** things are said, never **what** happens:

- `game.json` is never edited (neither `design-doc/game.json` nor its copy `src/game/data/game.json`).
- Logic, conditions, items, who gives what, puzzle solutions, the order of events, the clue a line
  carries and every protected fact (GLOSSARY.md § 6) stay exactly as they are.
- An existing key keeps its speaker. A clue stays in the key that carries it today, stated plainly
  (`check_rewrite.py` checks the protected facts per key). New lines around it may react to the
  clue or repeat it, never change or contradict it.
- Verbatim lines (GLOSSARY.md § 6.4, e.g. Lea's message `action.F11.003`) and puzzle options are
  not touched.
- Code, ids and technical docs stay English; Slovak only in player-facing text (ARCHITECTURE.md).

## 1. Tone: Polda-style humour that makes sense

The reference is the humour of the Czech *Polda* adventure games: playful, a little absurd,
character comedy, real situational jokes, running gags, lively characters with quirks who are
enjoyable to talk to. *Polda* is a reference for the **tone only**: no names, quotes, catchphrases,
characters, plots or likeness from those games (game.json: "Žiadna podoba s postavami Polda").

Binding rules:

1. **Every line makes sense in its situation.** It answers what was asked, reacts to what was
   said, and is something this person would say here and now. A joke that needs an explanation, a
   non sequitur or a picture that does not mean anything is cut, however witty it sounds.
2. **Natural spoken Slovak.** Correct grammar and declension, no calques and no anglicisms where
   Slovak has a word (no "toaster", "dáva to zmysel", "level", "update"), no officialese except an
   official character being official on purpose. Read it aloud.
3. **The humour lives in the characters and the situation**: misunderstandings with a payoff,
   people's quirks and hobby-horses, logical absurdity of real situations (a thermos labelled
   NEDOLIEVAŤ POLIEVKU), exaggeration that fits the person (Rudo), literalness (Očko), callbacks
   across eras, running gags per character (VOICES.md). Both sides of a conversation may be funny;
   the NPCs are not straight men for Adam.
4. **Explicitly not the old pattern.** No ironic one-liner summary after every line or at the end
   of every exchange (`Tak aspoň jedna krivka ide dobrým smerom.`, `Navigácia s historickou
   vrstvou. Poznám.`, `Aspoň niečo dnes funguje na prvý pokus.`). A line that only comments on the
   previous one with a wink is the pattern to remove, not to imitate.
5. **Warm, never mean.** No jokes about illness, death, age, bodies, nations, the regime as a
   punchline, or the game itself (no meta jokes about puzzles, inventory, players, levels).
6. **Serious beats stay plain.** Lea's message, Tóno's recognition (12 / 25 / 50), Viktor hearing his
   mother, the last scene with Mira, covid itself: short, simple sentences, no jokes.
7. **Goals, journal entries and hints stay clear.** They may be friendly; they are never jokes.

## 2. Length: conversations 2–3× longer, lines short

- **Conversations** (story topics, item actions that talk to an NPC, ambient topics) are written
  **2–3 times as long as the handoff's** version of that exchange, counted in lines: a 3-line
  exchange becomes 6–9 lines. The extra lines make it feel like a real conversation: a greeting
  or opening when people meet, small talk, reactions, a follow-up question, a closing. They are not
  filler: every added line has a reason (character, information, a joke, a reaction).
- The business of the exchange (what is asked, what is given, the clue) keeps its original order
  and keys; the new lines go before, between and after them (section 5).
- **Every line stays a subtitle**: aim for ≤ 110 characters (hard limit 160), one or two short
  sentences, one idea, readable in the time it is shown. A long thought becomes two lines, not one
  long line.
- **Repeatable ambient topics** are heard many times: 4–8 lines, and they must not annoy on the
  third hearing (no long set-up for a weak punchline).
- **Looks** may be 1–3 short sentences (still ≤ 160 characters): what it is, its state or what is
  missing, and a remark if there is a good one. Progress looks keep their hint.
- **Single solo lines** (Adam using an item on a thing, first-entry lines, system texts) stay short;
  the 2–3× rule is for conversations. Labels, names, goals, hints keep their limits
  (`glossary.json` → `limits`).

## 3. More topics: 2–4 extra optional topics per speaking NPC

Every speaking NPC (an id in `game.json` `characters` with lines, plus Očko) gets **2–4 extra
optional ambient topics** in addition to the handoff's. Not for devices and captions (`SYSTEM`,
`NARRATOR`), recordings (`LEA_REC`, `ADAM10`) or Bodka, who only barks.

What they are about (mix per NPC; ideas per character in VOICES.md):

- **Local colour of the real place and era**: Ivanka pri Dunaji 1960, Dúbravka 1982, Bratislava
  1995, Chorvátsky Grob and Čierna Voda in the covid autumn 2020, Jasná 2035 (STYLE_GUIDE.md § era
  flavour). Only details a 12+ player understands without a footnote and that are true or plainly
  fictional; when unsure about a historical detail, leave it out or ask in the note.
- **Their own life and quirks**: job, hobby-horses, family, habits, opinions.
- **Running gags** of that character (VOICES.md).
- **Gentle nudges toward the current goal** without spoiling: at most the direction (where to go,
  whom to ask), as hint level 1 would give it, never the item or the solution.

Rules that keep the game intact:

- Extra topics never change logic: no items, no progress, no new conditions in game.json, no
  solutions, no facts that contradict the story. They only play lines (like the handoff's ambient
  topics, `Dialogue.StartTopic`).
- Availability may only use what already exists (the NPC's presence and `requires_done` on existing
  action ids). A nudge must fit the state in which it is shown; when in doubt, make it
  state-independent.
- They respect the ty/vy switches (Tóno, Tóno 50) and the optional story of Jana (no topic reveals
  an outcome that has not happened).
- Topic labels ≤ 28 characters, written as the topic or Adam's short question (STYLE_GUIDE.md § 6.7).

## 4. The stack: who does what, in this order

Every text, new or changed, goes through all four steps. A text that skipped a step is not done.

| step | who | input | output |
|---|---|---|---|
| 1. Write | Claude (writer agent) | context bundle `docs/writing/context/<chunk>.md`, STYLE_GUIDE.md, VOICES.md, GLOSSARY.md | `docs/writing/out/<chunk>.csv` (existing keys) and `docs/writing/out/<chunk>_ext.json` (new lines and topics, overlay schema) |
| 2. GPT language check | `tools/gpt_review.py` → openai/gpt-6-astra-pro via fal.ai OpenRouter | step 1 outputs + bundle + voices | `docs/writing/review_gpt/<chunk>.json` (per key: verdict ok/fix, problem, suggestion) |
| 3. Final control | Claude (lead writer, not the step-1 writer's own pass) | step 2 result | `docs/writing/review_gpt/<chunk>.decisions.csv`, corrected outputs, final read-through in story order |
| 4. Automatic checks + in-engine review | tools + Claude | merged texts | green checks, a story-order line dump, screenshots when needed |

### Step 1 – Claude writes

1. Regenerate the bundles if the tables changed: `python tools/writing_bundles.py`.
2. Read the bundle top to bottom, then STYLE_GUIDE.md, VOICES.md, GLOSSARY.md. Write in story order,
   one whole exchange at a time, extended per section 2 and with the extra topics of section 3.
3. Existing keys go to `out/<chunk>.csv` (`keys,sk_new,note`; note in English: why, `drop: …` for
   intended drops). New lines and topics go to `out/<chunk>_ext.json` in the overlay schema
   (section 5).
4. Run `python tools/check_rewrite.py docs/writing/out/<chunk>.csv --chunk <chunk>` until there are
   no errors; explain every remaining warning in the note.

### Step 2 – GPT language check

```
PYTHONIOENCODING=utf-8 python -X utf8 tools/gpt_review.py --chunk <chunk> --overlay docs/writing/out/<chunk>_ext.json --dry-run
PYTHONIOENCODING=utf-8 python -X utf8 tools/gpt_review.py --chunk <chunk> --overlay docs/writing/out/<chunk>_ext.json --max-usd <task budget>
```

- One batch per scene / conversation (a `###` block of the bundle) with its context: where it
  happens, the whole exchange in play order with the new texts, the voices of its speakers and the
  ty/vy table. GPT judges the changed and new keys (`--all-keys`: every key of the block).
- GPT flags nonsense, unnatural phrasing, grammar, calques and anglicisms, jokes that do not make
  sense or are the old ironic-summary pattern, tone/voice and era breaks, ty/vy errors and length,
  and proposes a complete fix for each flag. It is told not to touch facts, names, items or clues.
- Cost: about USD 0.13 per conversation (measured 2026-10-06), so a whole chunk is about USD 6–9.
  The dry run prints the estimate; `--max-usd` caps the run; every call is logged in
  `art/spend-log.csv`. Re-runs skip unchanged batches.

### Step 3 – Claude's final control

1. `tools/gpt_review.py --chunk <chunk> --decisions-template` writes every flagged key into
   `docs/writing/review_gpt/<chunk>.decisions.csv`
   (`key,gpt_category,gpt_problem,gpt_suggestion,text,decision,final_text,reason`).
2. Decide **every** flag: `accept` (final_text = GPT's suggestion), `adapt` (GPT found a real
   problem, final_text is a better fix, e.g. one that keeps the Polda tone or the character's
   voice), or `reject` (the text stays; the reason says why GPT is wrong, e.g. a plural *vy*, an
   intended era word, a protected fact). GPT is an advisor, not the author: a suggestion that is
   correct but flat is adapted, not pasted.
3. Apply the decisions to `out/<chunk>.csv` / `out/<chunk>_ext.json`;
   `tools/gpt_review.py --chunk <chunk> --check-decisions` must pass (every flag decided, with a
   reason).
4. **Final read-through in story order**: the whole chunk, exchange by exchange, as the player meets
   it (the bundle order; `gpt_review.py --dry-run --show-prompt --all-keys` prints every block with the new
   texts). Check that each conversation flows, the jokes land, running gags are not overused, and
   nothing blurs a clue. Changes made here go through `check_rewrite.py` again; substantial new text
   goes back through step 2.
5. Write `docs/writing/review/<chunk>.md`: what changed, counts of accepted / adapted / rejected
   flags, open questions for the owner.

### Step 4 – automatic checks and in-engine review

1. `python tools/check_rewrite.py docs/writing/out/<chunk>.csv --chunk <chunk> --overrides-out <scratch>/sk_overrides.csv`
   → review → copy into `src/game/localization/overrides/sk_overrides.csv`.
2. Overlay: copy the accepted entries into the overlay file (section 5) and run the validator the
   Core README names for it.
3. `python tools/extract_strings.py`, then `python tools/check_strings.py` (must be OK).
4. Tests that stay green: `dotnet test src/LastBell.sln`, `tools/check_strings.py`,
   `tools/check_blocking.py`, `tools/check_rewrite.py`, the acceptance runs and `--play-all`.
5. In-engine review: a **headless** story-order line dump
   (`python tools/qa_godot.py --headless --path src/game -- --fast-text --play 94 --lines --quit-after 1`)
   is read like a script; screenshots of long lines in the subtitle box only when needed. Never
   disturb the person at the computer (ARCHITECTURE.md): prefer `--headless`; start every run that
   needs a window through `tools/qa_godot.py` (hidden window, no focus, muted, low priority); never
   `--visible`, `--qa-show`, `--warp-mouse` or OS-level input.

## 5. Where texts live and how to revert

| what | where | how it is applied |
|---|---|---|
| handoff texts (never edited) | `design-doc/game.json`, `design-doc/dialogues.csv` | `tools/extract_strings.py` builds the tables |
| new text for an **existing key** | `src/game/localization/overrides/sk_overrides.csv` (`keys,game_json,sk,note`) | `extract_strings.py` writes it into `dialogue.csv` / `world.csv`; `check_strings.py` verifies it |
| UI texts | `src/game/localization/ui.csv` (hand-written) | edited directly |
| **longer sequences** (lines added before / between / after the lines of an existing exchange) and **new topics** | `src/game/data/content_ext/dialogue_ext.json` (overlay) | loaded by Core on top of game.json; schema and keys by the Core agent, documented in `src/LastBell.Core/README.md` |
| drafts and review records | `docs/writing/out/`, `docs/writing/review_gpt/`, `docs/writing/review/` | kept for audit |

The overlay is written to the schema in `src/LastBell.Core/README.md` (by the Core agent, in
parallel with this method). Writers read that README and never invent fields; until it lands,
drafts use `out/<chunk>_ext.json` with one object per sequence (`id`, the anchor such as the action
id or the character id, optional `label`, and `lines` of `{key, speaker, sk}`), which
`gpt_review.py` already reads. What the writing side needs from the schema: stable keys per new
line, the speaker per line, the position relative to existing line ids, new ambient topics per
character with label, lines, repeatable flag and availability on existing action ids only, and the
same `Tr(key)` / Slovak-fallback path as every other text.

**Revert**

- One existing key: delete its row in `sk_overrides.csv`. Everything: keep only the header.
- One extended sequence or extra topic: remove its entry from `dialogue_ext.json`. Everything: an
  empty overlay (or no file); the game then plays exactly the handoff's exchanges.
- Then `python tools/extract_strings.py`, `python tools/check_strings.py`, and a Godot import
  (`<console exe> --headless --path src/game --import`) to rebuild the `.translation` files.
- The `game_json` column of `sk_overrides.csv` guards against stale rewrites; git history keeps
  every earlier version.

## 6. Done means

- Tone, length and topic rules of sections 1–3 hold for the whole chunk.
- All four steps ran: check_rewrite clean, GPT review file present, every flag decided
  (`--check-decisions` passes), the read-through done, review notes written.
- check_strings OK, tests green, the headless line dump read.
- Spend logged in `art/spend-log.csv`.
