# C4 – GPT tone pass and Claude's final control (2026-10-06)

Chunk C4 covers 2035 Jasná in winter, all cutscenes, the epilogue (with both Zuzana shots) and the system and UI
texts. This is step 2 and step 3 of `design-doc/WRITING_METHOD.md`, run on the writer's v2 draft
(`docs/writing/out_v2/C4.csv`, `C4_ext.json`). It follows the writer's own runs `C4_v2` and `C4_v2_verify`,
whose decisions are kept.

What this pass did:
- GPT judged the whole chunk again with `--all-keys` and the C1 Polda-tone instruction.
- Claude decided every flag.
- Claude rewrote the lines that still fell short.
- GPT checked the rewritten blocks once more, and Claude decided those flags too.
- Claude read the chunk in story order.

## Inputs and outputs

- Bundle: `docs/writing/context/C4.md`, unchanged. It already lists the Q10/Q11 epilogue shots.
- Instruction: `C4_tone.instruction.txt`. It is `C1_tone.instruction.txt` plus the C4 setting facts:
  - winter, 6 February 2035;
  - the cable cars work normally;
  - the room name "Lobby" is fixed;
  - Viktor is not funny by design;
  - Lea's message is verbatim;
  - the ty/vy rules;
  - the Zuzana rules;
  - UI, hint, journal and goal texts are judged for clarity only.
- Epilogue texts: they are the `world_ext_patch` of `C4_ext.json`. GPT saw them through the scratch overlay
  `epilogue_review.json`, which holds the same shots and lines.
- Results:
  - `C4_tone.json` and `C4_tone.decisions.csv` (main run);
  - `C4_tone_verify.json` and `C4_tone_verify.decisions.csv` (re-check);
  - the re-check inputs `C4_tone_verify.input.csv` and `C4_tone_verify.input_dialogue.json`.
- Applied to `docs/writing/out_v2/C4.csv` (50 → 73 rows) and `docs/writing/out_v2/C4_ext.json` (10 overlay
  line texts). Nothing was merged into the live game, `game.json` is untouched, and nothing was committed.

## GPT runs (openai/gpt-6-astra-pro)

| run | scope | keys judged | flags | accept | adapt | reject | USD |
|---|---|---|---|---|---|---|---|
| `C4_tone` | whole chunk, `--all-keys`, tone instruction: actions, rooms, conversations, quests, puzzle, cutscenes, epilogue (36 batches), then every UI block (7 merged batches) | 1045 | 56 | 16 | 17 | 23 | 12.36 |
| `C4_tone_verify` | only the lines rewritten as *adapt* or by Claude, each in its scene (`--trim-topics`) | 64 | 5 | 2 | 3 | 0 | 1.22 |
| **total** | | | **61** | **18** | **20** | **23** | **13.57** |

Not judged by GPT (`--skip-role`), but read by Claude in the read-through: names, labels, objectives, journal
lines, quest titles, the puzzle window title and locked-exit looks. These are the same roles C1 skipped, and they
were already part of the `C4_v2` run. `--check-decisions` passes for both runs: 56 and 5 flags, 0 problems.
`check_rewrite` gives 0 errors and 5 warnings, the same five as before, each explained in its row's note. The
overlay check gives 0 errors and 0 warnings.

On its own GPT was again lenient about tone. Story actions F07–F17 and the Viktor scenes got 0 tone flags, and
its notes rightly say those beats should stay plain. Most of the flags were about grammar, logic gaps and three
remaining ironic tags.

## Decisions in short

**Old ironic tags and summary lines replaced:**
- **F02.x07, Tamara:** *Vitaj v klube. Ja si pri každom origináli sadám na ruky.* Before:
  *Správny opravár. Trpí, ale nesiahne.*
- **F04.004, Adam:** *…? Na taký som dnes čakal celý deň.* This is his escalating-day gag. Before: *To sa mi
  páči.*
- **S43 entry:** *Nabudúce si na dovolenku zbalím aj pokazený magnetofón.*
- **Q8C.002:** Adam's practical next step.
- **S45 ice look:** *Trochu nakrivo, ako horizont na mojej fotke s babkou.* This is a callback to `look.S06.photo`.

**Logic gaps closed:**
- **IVAN.ambient 2.002:** Adam asks about the clouds, so Ivan's *Oblakom by som tak neveril* now has a set-up.
- **JANA35.ambient 1.001:** *Možno.* now answers the label *Poznáme sa?*.
- **SARA.extra 1.004 / 3.004:** Sára explains the ink, and she deciphered the names through the stain.
- **TURISTA.ambient 2.002:** now *A na čom sa smial?*.
- **CS03.02.001:** *z neskorších zápisov*.

**Grammar and wording:** *pol metra snehu*, *prešiel cez dosť dverí*, *Je zadarmo ako hmla*, *dostatočné nabitie
batérie*, *Na výstavu zbierame…*.

**UI, 15 texts:**
- the save messages now end in *Rozohraná hra beží ďalej*;
- *Automatický posun titulkov*;
- *s letopočtom*;
- *S čím ti mám poradiť?*;
- *Esc preskočí titulok, dvakrát Esc celú scénu*;
- *prerušenú scénu*;
- *pozastaviť hru*;
- *vykonať akciu*;
- *zvuky prostredia*;
- the touch and Space hints.

### Rejected flags (23, reasons in the CSV)

- **Fixed names and terms:**
  - "Lobby" stays.
  - "Uhlový papier" and "Pošta s prepážkou" are the glossary names (I14, I15).
  - *ZVONu* takes no hyphen (STYLE 3.4; I09, I12).
  - The key is called *Space* in every control text.
  - *Herný engine*, *Obnoviť predvolené* and *Ďakujeme za hranie* are standard Slovak UI wording.
- **Deliberate wording:**
  - *vyčistiť* is Viktor's word for normalizing (CS06.02.001, BORIS.ambient 1.x03).
  - *úzke pravidlo* calls back Adam's *príliš úzke police*.
  - *mená, ktoré si odporujú* is the story's own concept (CS07.01.002).
  - Boris's "invitation" look is his voice.
  - Tamara's *Zatvárame o šiestej* is a punchline that lands as it is.
  - In F03.005, Boris's *A práve preto…* is his quiet reproach to Viktor.
- **Verbatim and conventions:**
  - CS07.04.001 is a verbatim line.
  - Level-3 hints use *na <target>* (Q8.hint.3).
  - Captions keep bare years (epilogue.9.shot).
  - Hints never say *klikni* (J04).
  - `{target}` stays after a colon in the nominative (hint.step_place).
- **Kept on purpose:**
  - F01.005 is 130 characters, below the 160 limit. The clue (all four handovers) stays in this key.
  - F06.label: *porovnať so zásobníkom* is a normal shortcut.
  - *v brašni* is the house form in 22 texts, so it is not changed in one key (see open points).

## Claude's own rewrites (no GPT flag), all re-checked by GPT in `C4_tone_verify`

- **JANA35.extra 2.004–.006:** fixes a contradiction across eras. Jana 2020 says she corrected the planes Tóno
  drew in her notebooks (*Ja som mu ich opravovala*), but Jana 2035 said she had not. Now she corrected all of
  them except the first, which she keeps in her archive: *Na prvé verzie nesiaham, ani keď majú krivé krídla.*
  That line is GPT's verify suggestion, accepted.
- **entry.S50.001:** *zachrániť* read as rescuing people from danger. Now: *Keby tak Atlas nechal v záznamoch aj
  ľudí, ktorí sa naň pozerajú.*
- **TAMARA.extra 2.006:** the line now answers *Skrutky zamrznú?*: *Skrutky nie, prsty áno. …*
- **F06.x02:** *Aj to, ako mi cvakajú zuby.* replaces the unclear *Aj vlastné zuby*.

`TURISTA.ambient 2.002` (*A na čom sa smial?*) was changed in the final read-through, after the verify run. The
accepted GPT text only repeated Miloš's sentence. It is a four-word question and was not sent to GPT again,
because the budget was nearly used up.

## Read-through in story order

The read-through used scratch dumps of every block with the final texts, in bundle order:
- F01–F17 and Q8A–Q9F;
- the rooms S41 → S49;
- the nine NPCs;
- the quests and P04;
- CS01–CS09;
- the UI;
- the epilogue 1–11.

What I checked:
- **Jokes:** every running gag returns at most once per scene, each time a little changed:
  - Adam's fuse;
  - Sára's pen;
  - Očko's *zlatý* and his folder *Nepotrebné, ale milé*;
  - Ela's thermos *NEDOLIEVAŤ POLIEVKU*, now through Nina;
  - Tamara's coffee promise, paid off in `TAMARA.extra 3` after F09.
- **Clues:** each clue still sits in its own key, and `check_rewrite` checks the protected facts. These are:
  - who gives what (F01.005);
  - the route (F04.003);
  - ROZDIEL = ZAHODIŤ;
  - MONITOR and ZÁPIS;
  - the ports and the years 1962/1995/2020/2035.
- **Serious beats:** F10–F17, CS06 and CS07 stay plain. Viktor is not a joke, and Lea's message
  (`action.F11.003`) and CS07.04.001 are untouched.
- **Ty/vy:** Tamara says ty; everybody else in 2035 says vy.
- **Facts checked against the other chunks:**
  - Adam sealed the bridge in the jar in 1982 (E08), which J05.x02 repeats.
  - Jana's notebook (Q9C/Q9D) matches Q9F.
  - The planes Tóno drew (JANA20) match JANA35.
  - The *uzlové hodiny* in J02.002 are the 1995 time-node clock at the Dúbravka stop.

## Zuzana rules

Checked by searching every C4 text, CSV and overlay, for *Zuzan, Zuzk, Kubo, Sokolík, neuvid, pamiatk*:
- She appears only in `epilogue.10` (June 1962, age 7) and `epilogue.11` (June 1995, the Sokolíkova yard).
- No 2035 line, look, hint or UI text mentions her.
- `ui.hint_step.B19` names the yard and its wall drawing, not her.
- Both lines read *Posledný zvonec. A v septembri zase prvý.* They are about the school year only and say
  nothing about her life or future.
- GPT flagged neither shot.
- The school-bell vitrine on Chopok (`look.S47.ambient 2`, handoff text) names no person.
- No private fact about her was written anywhere.

## Open points for the owner

- **brašna / brašni:** the game writes *Servisná brašna* in the nominative and *v brašni* in 22 texts (that
  is the locative of *brašňa*). GPT wants *v brašne*. One consistent form should be decided in the glossary and
  then applied everywhere. This pass did not change it.
- **Epilogue texts:** they still live under `world_ext_patch` in `C4_ext.json`. They must be copied into the
  Q10/Q11 entries when the yard's world overlay is merged; the writer's note still applies.
  `ui.hint_step.B19` goes in only together with that overlay.
- **Live checks:** the merge into the live game (`content_ext.py merge`, overrides, `extract_strings`) and the
  live checks after it (`dotnet test`, `check_blocking`, acceptance, `--play-all`, headless line dump) are still
  to do. `content_ext.py merge --dry-run`, `check_strings` and `check_rewrite --self-test` are OK.

## Spend

USD 13.57 in 47 calls (C4_tone 12.36 + C4_tone_verify 1.22), all logged in `art/spend-log.csv`, within the
USD 14 budget.
