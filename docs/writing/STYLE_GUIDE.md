# Posledný zvonec – Slovak text style guide

For the chunk writers of the Slovak text rewrite (TEXT-04). Read this file, then
[VOICES.md](VOICES.md) and [GLOSSARY.md](GLOSSARY.md), then your context bundle in
`docs/writing/context/<chunk>.md`.

Why this rewrite exists: the product owner played the build and said the texts "basically make no
sense". The story is good; the sentences are not. Many lines are literal translations of design
notes, jokes that do not follow from the line before, answers that do not answer the topic the
player picked, and looks that read like a specification. Your job is to make every text sound like
a real person said or wrote it, in correct, natural Slovak, without changing what happens.

---

## 1. The one rule: change how, never what

Fixed and not yours to change: the story, the puzzles and their solutions, which item goes where,
who gives what, what the player has to infer, the order of events, the number of lines, the
speaker of every line, and every fact in
[GLOSSARY.md § Protected facts](GLOSSARY.md#6-protected-facts). Sources of truth:
`design-doc/game.json`, `design-doc/PRIBEH_A_PRAVIDLA.txt`, `design-doc/walkthrough.json`, and for
controls the owner decisions in `docs/DECISIONS.md` (for example, Space is held, not toggled).

Yours: word choice, word order, grammar, tone, rhythm, jokes, how a fact is phrased, which
character says it in what voice, how long it is.

Concretely:

- One key = one subtitle or label. Never add, remove, merge or split keys. A line that is too long
  is shortened, not split.
- The speaker of a line comes from the data. Do not write `ADAM:` or `Mira:` into the text, and do
  not write a line that only works if someone else says it.
- A clue keeps its information. If Dezider says where the three digits are and who has the
  metronome, the new line still says both, unmistakably.
- If you think a fact is wrong (a contradiction, a wrong year), do not fix it silently. Keep it and
  write the problem into the `note` column; the lead writer decides.
- If a line cannot be made good without changing the story, keep the meaning, make it as good as
  possible and explain in the note.

## 2. Tone

The reference is a civil, humorous Central European point-and-click adventure: warm, dry and
observant. The players are adults and children of 12 or older.

- **Warm, never cynical.** People help each other. Nobody is stupid. Jokes come from situations
  (technology, paperwork, public transport, family) and from Adam's self-irony, not from mocking
  seniors, sick people, children, a profession or a nation.
- **Dry, not wacky.** A good line is understated. One joke per exchange is plenty; many lines should
  simply be clear and kind.
- **Never bureaucratic.** Officialese is only allowed when a character is being official on
  purpose (the post office clerk in 1960, a form in 1982), and then the joke is that it is official.
  Narration, looks, goals and hints are never officialese.
- **Emotion is said simply.** The important moments (Tóno at 12, 25 and 50, Lea's message, the
  last scene with Mira) work with short, plain sentences. Do not decorate them.
- **No meta humour.** Nobody jokes about puzzles, inventories, game design, "levels" or "the player".
  Adam may joke about time travel because it is happening to him.
- **Covid 2020 is real and handled with respect.** Humour about logistics (masks, distance, phone
  calls through a window, paper notices), never about the illness, the dead or rules being silly.

## 3. Natural spoken Slovak

Write the way a Slovak speaker would say it out loud. Read every line aloud before you keep it.

### 3.1 Verbs, not nouns

| Instead of (nominal, translated) | Write |
|---|---|
| Výroba tesnenia demonštračnej pumpy. | Vyrobiť nové tesnenie na pumpu. |
| Najprv dokončím dohodnutý servisný krok. Je zapísaný v denníku. | Najprv položím babke nákup na stolík. Potom pôjdem k oknu. |
| Vyzdvihnutie materiálu podľa lístka. | Vyzdvihni materiál podľa Otovho lístka. |
| Uloženie je zapísané medzi neškodné technické rezervy. | Zapíšem to ako neškodnú technickú rezervu. |

### 3.2 No calques, no anglicisms where Slovak has a word

| Avoid | Prefer |
|---|---|
| To dáva zmysel. (in 1960/1982) | To je logické. / Má to zmysel. |
| Som rozhodne motivovaný. | Tak to sa poponáhľam. |
| …nech ho nestresujete. (1960) | …nech sa nesplaší. |
| informačná asymetria, legitímny vstup, autorizovaný | say what it means: povolený vstup, so súhlasom |
| buffer | návratový zásobník / zásobník (see glossary) |
| Si v poriadku? (stiff) | Ako sa máš? / Všetko v poriadku? / Si okej? (2020 only) |

### 3.3 Grammar watch list (all of these occur in the current texts)

- `vo vonkajšej schránke`, not `v vonkajšej` (vo before v/f + consonant).
- Imperative of *ryť*: `Do platne neryte.` / `Neryj do platne.`; `Nery` does not exist.
- `Pozdravujte Tóna`, not `Tónovi pozdravte` (pozdraviť koho).
- `Napíšem: služobná návšteva.` A line like `Dám služobná návšteva.` is broken Slovak.
- Agreement and word order: `Potom celé tri dejstvá dokazujem, že som to prehnal.`, not
  `Potom sa tri dejstvá ukazuje…`.
- Declension of names: `Paliho, Palimu` (Pali); `Jura, Jurovi` (Juro); `Dezidera` (Dezider);
  `Ley, Lei` (Lea); `Very` (Vera, 1960) vs `Viery` (Viera, 1995). See GLOSSARY.md § People.
- One address form per pair of characters. A line like `Tak sa zapíš… Kabinet vám otvorím.` mixes
  *ty* and *vy*. VOICES.md has the table of who says *ty* and who says *vy* to Adam.
- Commas before *že, ktorý, keď, aby, ako, kde, lebo, ale* and in vocatives: `Žiaden strach, miláčik!`

### 3.4 Typography

- Quotes `„…“`, ellipsis `…` (one character), en dash `–` with spaces in sentences
  (`Nákup – a potom k oknu.`) and without spaces in ranges and codes (`9–17`, `3–2–6`).
  Codes keep their hyphen: `K-17`, `Z-17`. Multiplication sign: `3 × 4`.
- Route names with multi-word stops: `Biela Púť – Priehyba`, `Priehyba – Chopok`.
- Years always in digits. Dates as `7. decembra 1982`. Ages and durations in speech may be words
  (`tridsaťosem rokov`), in goals and hints use digits (`38 rokov`). The value never changes.
- Signs, labels and switch positions in capitals exactly as they are painted: `ZVON`, `MONITOR`,
  `ZÁPIS`, `NEPREPISOVAŤ ORIGINÁL`, `TRI VLNY, DVA ÚDERY, ŠESŤ DIELIKOV`, `ROZDIEL = ZAHODIŤ`,
  `DRUHÝ ŽIVOT`. Capitalised device names decline with lowercase endings: `ZVONu`, `ZVONom`.
- No line breaks, no emoji, no stage directions in brackets, no `…` at the start of a line.
- Exclamation marks are rare. Rudo the amateur actor gets them; Adam almost never.

## 4. Register per era

Every era should sound like itself, without caricature. Adam always speaks his own 2020 Slovak
(he is the visitor), but he adapts his politeness: he says *vy* to adults he has just met.

| Era | Feel | Use | Avoid |
|---|---|---|---|
| **1960** Ivanka pri Dunaji | village and small workshops, everyone knows everyone, people are formal with strangers and warm after a minute | *pán, pani, dievča*, plain practical words, a few old-fashioned turns (*prosím pekne*, *nech sa páči*, *ráčte*) in the mouth of the post clerk | modern words (*okej, fajn, stres, systém, info, mobil, displej*), slang, *súdruh* as a joke; NPCs reacting to anachronisms they cannot understand |
| **1982** Dúbravka, socialist school | the school is an institution: approved models, forms, pioneer notices; people are careful in official places and normal in private | pupils say *súdruh učiteľ*, *súdružka riaditeľka*; notices in official language (*Pionierska schôdzka v stredu o 14.00*); adults say *formulár, výdajka, podpis, schválený vzor* | real political slogans or speeches, secret police, cheap anti-communist punchlines, every adult as a caricature; modern words in NPC mouths |
| **1995** Bratislava | post-1989 city in motion: kiosks, markets, cassette culture, repair shops, school clubs; relaxed and quick | colloquial Bratislava speech (*Miletička, fakt, kamoš, frajer* sparingly), *koruny*, cassettes and tapes, landline phones | smartphones, internet talk, today's slang (*cringe, chill*), forced 90s references |
| **2020** Chorvátsky Grob, Čierna Voda, Dúbravka | covid autumn: neighbourly help, distance, phone calls, paper lists | *rúško, odstup, karanténa, dištančné vyučovanie, dezinfekcia, cez okno, na diaľku, výdajné miesto* | jokes about the illness, denial, "corona" puns; English office words |
| **2035** Jasná | fifteen years later, not science fiction; a fictional exhibition and pavilion, real cable cars | *kurátorka, výstava, pavilón, čítačka, servisný režim, lístok, lanovka, Funitel* | cyberpunk, invented tech jargon, English loanwords where Slovak has a word, any claim that the cable cars are broken or unsafe |

## 5. Length and shape

- **Subtitles (spoken lines, first-entry lines, looks): aim for at most 110 characters**; the
  checker errors above 160. A subtitle shows at most three lines on screen.
- Action labels (the hover sentence with an item): at most 45 characters, start with the verb in
  the infinitive: `Vložiť náhradnú poistku`.
- Topic labels (dialogue choices): at most 28 characters.
- Names (rooms, hotspots, items, exits): at most 32 characters, nominative, what a person would call
  the thing.
- Objectives, journal entries, quest goals, item purposes: at most 100 characters, one sentence.
- Hints: level 1 and 2 at most 140, level 3 at most 200 (360 is the hard limit for long chains).
- One idea per line. If a line carries a clue, the clue is the main idea of that line.
- Exact limits for the checker: `docs/writing/glossary.json` → `limits`.

## 6. Text types

The bundle tells you for every key what it is ("role"). Rules per type:

### 6.1 Spoken lines (`action.*.NNN`, `topic.*.NNN`, `cutscene.*`)

- Lines of one exchange play in order. Each line must follow from the one before it: an answer
  answers, a reaction reacts. Read the whole exchange before you change one line.
- The exchange must make sense on its own, without the player having read the design document.
- Keep the information distribution: if line 2 gives the item and names the next person, the new
  line 2 still does.
- Small talk exchanges (ambient topics) may end with a joke; story exchanges end with something the
  player can act on, or with a natural closing.

### 6.2 First-entry lines (`entry.SNN.001`)

Adam's first impression when he enters a room the first time. One concrete observation about what
the player sees (check the "Picture" line in the bundle) plus, at most, one dry remark. Never a
hint about a puzzle, never a non sequitur.

- Weak: `Tu sa zadržiava voda. Na obecnej skupine sa zadržiava už len slušnosť.`
- Better: `Retenčná nádrž. Voda tu pokojne stojí. Obecná skupina na internete by sa od nej mohla učiť.`

### 6.3 Looks (`look.*`, `item.<ID>`, look variants)

What Adam says when the player right-clicks. First person, present tense, concrete.

- Progress objects: say what it is, its state, and what is missing or needed, as Adam would notice
  it (`Remienok sa rozpadol. Kazetu bez opravy bezpečne nevyberiem.`). This is often the only hint
  the player gets: keep it.
- Atmosphere objects: one short observation or joke, max ~80 characters.
- Look variants describe the changed state after an event (`Lipa, ktorú sme v roku 1982 ochránili,
  má teraz hustú korunu.`).
- Never design notes: no *v hre, herný, fiktívny, mimo obrazu, nie je to hádanka, bez pixelového
  presúvania, predmet sa získava iba raz, nie je určená na skúšanie kombinácií, pôvodná línia,
  motýlí efekt*. If a design note carries a real fact for the player, say the fact in-world:
  `Mimo 2020 funguje fotoaparát a lokálny zápisník; sieť ani internet nie.` →
  `Mimo roku 2020 mi z telefónu ostal fotoaparát a poznámky. Signál nečakám.`

### 6.4 Locked exits (`exit.*.locked`, `conn.*.locked`)

Adam's one-line reason why he does not go there yet and what would change it, in-world:
`Bez ohlásenia u školníka ma do kabinetu nepustia.` — not `Najprv dokončím dohodnutý servisný
krok. Je zapísaný v denníku.` Most of these keys are never shown (exits without a lock); the
bundle marks them, leave those unchanged.

### 6.5 Names (`room.*.name`, `hotspot.*.name`, `item.*.name`, `exit.*.label`, `conn.*.label`)

Short nouns, as a person would point at the thing: `Mosadzné puzdro`, `Zásuvka s poistkami`.
Use the canonical names from GLOSSARY.md; do not invent synonyms. An exit label that equals the
name of the room it leads to must stay equal to it. Renames are decided in the glossary only.

### 6.6 Action labels (`action.*.label`)

- **Item actions** (use an item on a target, combine two items): the hover sentence shown only
  when the action is possible. Infinitive, verb first, names the item or the result:
  `Nasadiť manžetu na pumpu`, `Spojiť konektor s adaptérom`.
- **Story topics** (kind *topic*, the player picks it in the NPC's menu): this is what Adam brings
  up. Write it as the topic or as Adam's short question, not as an instruction:
  `Babkin nákup`, `Prečo sa to volá ZVON?`, `Krabice v dielni` — not `Spýtať sa na staré krabice`.
  The label also titles the exchange in the conversation log.
- **Plain clicks**: the label is the name of the action in the journal and log; infinitive.

### 6.7 Topic labels and answers (`topic.*.label` + its lines)

This is the most common failure in the current texts. Rules:

1. **Adam speaks first** (the bundle says so): the label is the topic, Adam's first line is the
   actual question. They must not repeat each other.
   - Bad: label `Ako dlho vyvolanie trvá?` → Adam: `Ako dlho vyvolanie potrvá?`
   - Good: label `Vyvolávanie` → Adam: `Ako dlho to bude trvať?`
2. **The NPC speaks first**: the label is what Adam asked, and the NPC's first line answers exactly
   that question.
   - Bad: label `Koľko balíkov?` → Adam: `Máš dnes pokoj?` → Roman: `Dve adresy mali uvedené ten
     dom, čo bol predtým žltý.`
   - Good: label `Ako ide rozvoz?` → Adam: `Veľa adries dnes?` → Roman: `Dve mi dnes opísali ako
     „ten dom, čo býval žltý“.` → Adam: `Navigácia s historickou vrstvou. Poznám.`
3. The label must make sense before the player hears the answer. `Tá termoska?` works only because
   the thermos with the sign NEDOLIEVAŤ POLIEVKU is visible next to Ela; such labels are fine when
   the object is in the room, otherwise name the topic.
4. The last line closes the exchange (a reaction, a punchline or a fact), never a new question
   nobody answers.

### 6.8 Objectives, journal entries, quest goals (`*.objective`, `*.journal`, `quest.*.goal`)

- Addressed to the player as *ty*, imperative, one sentence, concrete: who, where, with what.
  `Ukáž rozpadnutý remienok Palimu v Karlovej Vsi.`
- Quest goals use the same imperative form: `Pomôž Mire s nákupom a dostaň sa do jej záhradnej
  dielne.` (not the infinitive *Získať prístup…*).
- When game.json keeps journal and objective identical, write the same text in both keys (the
  checker enforces it).
- Journal entries of the form `Dokončené: <label>.` become a short record of what happened, in
  Adam's notebook voice, past or present-perfect: `Konektor je zapojený v adaptéri. Chýba izolácia.`
  or `Lenka hovorí, že Bodka stratil loptičku pri nádrži.`
- No design words: *odblokovanie, časová adresa 2035 sa odomkne, dôkaz Súhlas, finále, vedľajšia
  vetva*. Use the in-world words from the glossary.

### 6.9 Item purposes (`item.*.purpose`)

**Not shown to players** since the writing merge (2026-10-05): the bag shows only the item name and
Adam's look (`item.<ID>`). A clue that only the purpose carried belongs in the look. The purpose stays
a design note (and is still translated, in case a later screen needs it). Old rule, for that case:
short infinitive phrase or noun phrase that reads after
*Účel:*, capital first letter, period at the end: `Vrátiť Lenke a Bodkovi.`,
`Dôkaz súhlasu pre záverečnú obnovu.` Never `Dôkaz Súhlas a odblokovanie časovej adresy 2035.`

### 6.10 Hints (`quest.*.hint.1/2/3`)

- Level 1 (Smer): where to go or whom to ask, no items, no solution.
- Level 2 (Postup): the people and items involved, in order, still in a sentence.
- Level 3 (Riešenie): the exact chain with arrows, every step, in-game names from the glossary,
  no ids, no *klik*: `Kľúč na dvere dielne → chronometer z puzdra → brašna na stolový ZVON → …`
- Never comment on the game (`Nevyberaj správnu repliku z hádanky.`); say what to do.

### 6.11 Puzzle texts (`puzzle.*`, `journal.clue.*`)

Title: short noun phrase. Clue: the readable clue, exactly as informative as now. Wrong line:
Adam says briefly why it does not fit and where the clue is. Success line: short. Puzzle options
(`puzzle.P01.left.1` …) are verbatim and must not be changed.

### 6.12 Device and system speakers

- `SYSTEM` is a device talking: the chronometer, Atlas terminals, the ticket gate, the station
  announcement. Terse, passive, understandable: `Nositeľ rozpoznaný. Jeho pamäť je chránená.`,
  `Lístok platný.`, `Príchod do stanice. Vystupujte po otvorení dverí.`
- The robot Očko is literal and polite, statistics instead of feelings.
- `NARRATOR` lines are short reflective captions, not jokes.

### 6.13 Epilogue (`epilogue.N.shot`, `epilogue.N.line`)

The shot caption is a short present-tense sentence about what the player sees: `Bodka leží pri
červenej loptičke.` The line is spoken by the named speaker and closes that side story.

### 6.14 UI (`ui.*`, `era.*`, `region.*`)

ui.csv is mostly fine. Change only what is wrong or unclear. Keep `{placeholders}` exactly, keep
buttons short, address the player as *ty*, describe the controls as the build implements them
(`docs/DECISIONS.md`: Space is held to show markers). UI rewrites are applied by editing ui.csv
directly, not via overrides.

## 7. Humour rules

1. **The joke must follow from the line before.** If you need the design document to understand
   why it is funny, it is not funny. Current example that fails: Mira says the glass has bad
   acoustics, Adam replies `Konečne hodnotenie, v ktorom za nič nemôžem.` Better: `Dobre. Dva metre
   a telefón. Bližšie sme sa celý mesiac nerozprávali.`
2. **Adam's humour is dry self-irony.** He laughs at himself, at his day, at machines and forms; he
   is never sarcastic to the people who help him. `Ja som chcel len vymeniť poistku.`
3. **One joke per exchange is enough.** Many ambient looks can be plain observations.
4. **A clue is never the punchline.** The line that gives the clue states it plainly; the joke, if
   any, comes after it in the same line or in the next one. Never twist a protected fact for a
   pun (`3–2–6` stays `3–2–6`).
5. **Jokes must work in Slovak.** No English puns, no wordplay that needs the English original.
6. **Each character jokes in their own way** (VOICES.md): Pali is a blunt colleague, Boris tells
   jokes like footnotes, Očko is funny by being literal, Rudo by being theatrical.
7. **No jokes about** illness, death, age, bodies, nationalities, the regime as a punchline, or
   game mechanics.
8. **Running gags are allowed** if they come from the data: "the same thing in another year"
   (the cupboard scratch, the bin, the swallow), papers that outlive people.

## 8. Words that must not appear

The checker (`tools/check_rewrite.py`) enforces most of these:

- Internal ids: `S17`, `G01`, `Q9C`, `P03`, `M11B`, `CS04`, `TONO82`, `CHRONO`, hotspot ids.
- Design jargon: *v hre, herný, hráč, fiktívny, mimo obrazu, pixel, zoom, quest, NPC, hotspot,
  servisný krok, pôvodná/základná/časová línia, motýlí efekt, finále, klik/klikni, inventár,
  kombinácia, odblokovať, hádanka, v denníku*. A character may use one of these words only when a
  real person would (Lída counting costumes may call it a puzzle; Adam may say *zapíšem si to*).
- Deprecated forms listed in GLOSSARY.md § Deprecated (`Mirka`, `buffer`, `retroaktívny`,
  `návlečka`, `Palova`, `Dezi` …).

## 9. Workflow

1. Read your bundle top to bottom once before writing anything. Note how each NPC talks.
2. Copy `docs/writing/context/<chunk>_keys.csv` if you like; your output is
   `docs/writing/out/<chunk>.csv` with the header `keys,sk_new,note`:
   - only keys you change (unchanged rows are ignored);
   - `note` in English: why, and anything the lead must know (`moved "Emil" to .004`,
     `fact looks wrong: …`). If you drop a name, term or number on purpose (a decided rename, a
     joke that no longer needs a count), write `drop: <word>` in the note; the checker then
     warns instead of failing. Protected facts and verbatim lines can never be dropped.
3. Rewrite in story order, one exchange at a time, reading the whole exchange aloud.
4. Run `python tools/check_rewrite.py docs/writing/out/<chunk>.csv --chunk <chunk>` until there are
   no errors; read every warning and either fix it or explain it in the note.
5. The lead writer reviews, merges with `--overrides-out`, and the accepted rows go into
   `src/game/localization/overrides/sk_overrides.csv`; `tools/extract_strings.py` then writes them
   into the tables and `tools/check_strings.py` validates them.

## 10. Checklist per line

- Does it sound like this person, in this year, talking to this listener?
- Does it follow from the previous line, and does the next line follow from it?
- Is every protected fact still there, with the same value?
- Are names, items and places the glossary forms, correctly declined?
- *ty*/*vy* consistent with VOICES.md?
- No design jargon, no ids, no speaker prefix, no line break?
- Within the length limit?
- Would a 12-year-old understand what to do next?
