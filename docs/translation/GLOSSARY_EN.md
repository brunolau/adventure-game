# The Last Bell – English glossary and translation rules

Added 2026-10-08 on the product owner’s request ("please draft the translations to english ... using your
model so we don’t use confirmation for now, then recheck yourself using some of your language plugins
[don’t include fal here]"). Binding for every English text: the `en` column of
`src/game/localization/{dialogue,world,ui}.csv`. Only the owner can change a decision; a change is recorded in
`docs/DECISIONS.md` and here.

The machine-readable twin is [glossary_en.json](glossary_en.json): sk → en for every speaker label, room,
region, era card, item, quest title, cutscene title, hint-quoted topic label, hotspot name and the core UI
labels, plus the protected facts, verbatim lines, text in the art, era vocabulary, puns, running gags,
deprecated words and the spell-check allow list. The tables below are generated from the same data, so the
two files always agree. When they seem to disagree, the JSON wins.

The Slovak rules stay the base: `design-doc/WRITING_METHOD.md` (tone), `docs/writing/STYLE_GUIDE.md`,
`docs/writing/VOICES.md` (who speaks how), `docs/writing/GLOSSARY.md` (facts),
`docs/story/ZUZANA.md` and `docs/writing/knowledge/AUDIT.md`. This file says how they carry into English.

## Key decisions at a glance

1. **British English** (en-GB), contemporary and natural when read aloud. The Polda feel comes across as dry British understatement.
2. **Title: *The Last Bell*.** It keeps the school-year "last bell" and the device ZVON (*zvon* = bell).
3. **ZVON stays ZVON.** It is never translated to BELL. Mira explains the name once (G05.005), and the title and the bells of Q10/Q11 carry the pun.
4. **Names keep their Slovak spelling and diacritics.** Slovak cases disappear (*Tóna* → Tóno) and possessive adjectives become *’s* (*Paliho* → Pali’s).
5. **Nicknames.** *Zuzka* is said only by Ivanka adults in 1962, *Kubko* only by adults to Kubo, *Dezi* only by Dezider’s friends. A descriptive epithet is translated when its meaning is the joke: **Juro Cassette**.
6. **Family words.** *babka* → **Gran** (Adam, 2020). *dedo* → **Grandad** (Tóno 12). *mamka* → **Mum**. System texts always say Mira.
7. **ty/vy becomes register.** Polite speech uses fuller sentences, "please" and *Mr/Mrs/Ms* + surname. Familiar speech uses first names and is casual. Tóno’s three switches stay visible: *mister* → Adam (12), stranger → *Hang on. It’s you.* (25), formal → familiar (50).
8. **Titles.** *pán* → Mr. *pani* → Mrs (1962–1995, and Mira always) or Ms (working women in 2020/2035). *pán Jozef* → Mr Jozef. *mladý pán* → young man.
9. **Children’s forms.** Adults are **Auntie / Uncle** + first name (Auntie Mira, Uncle Oto, Auntie Zuzana). Teachers are **Miss** (1995) and **Comrade Teacher / Comrade Headmistress** (1982). Children call Adam *mister* at most.
10. **Places.** Real places keep their Slovak names with no article. Exonyms are used only for the Danube, the Tatras, the Low Tatras and Czechoslovakia. Slovak adjectives become the place name plus a short descriptor: *Dúbravka stop*, *Karlova Ves tram stop*, *Miletičova market*, *Ivanka village green*. Years in room names are a suffix: *Physics prep room, 1982*.
11. **Pri LEALe** stays *Pri LEALe*: no article, no explanation, never "by the LEAL".
12. **One English word per game term.** For example *base node*, *cradle*, *time node*, *time window*, *write-back*, *return buffer*, *normaliser*, *chronochamber*, *Origin / Voice / Consent / Return*, *imprint*, *collection Z-17*, *tool bag* and *bag* (in-world) vs **Inventory** (UI). The full list is in § 6.
13. **British school and home words.** *školník* = caretaker, *fyzikálny kabinet* = physics prep room, *školský rozhlas* = school PA, *lipa* = lime tree, *povala* = loft, *náves* = village green, *sídlisko* = housing estate, *koruny* = crowns, *spiatočný lístok* = return ticket.
14. **Every item name and quest title is fixed** (§ 7, § 8). Puns are rebuilt in English, for example *Bodka Drops the Ball*, *The First Last Bell* / *Another Last Bell* and *Béla Comes Back*, which echoes *The swallow comes back.*
15. **Hints quote topic labels exactly.** All 34 story-topic labels are fixed in § 8.3, because hints quote them.
16. **Protected facts and verbatim lines have one English rendering each.** Lea’s message ends in *call me*, and that is exactly what the normaliser left. Mira’s rule is *Different data are not invalid data.* The faulty rule is *DIFFERENCE = DISCARD* and the switch reads *WRITE / MONITOR*. All codes and numbers are unchanged.
17. **Text in the art.** The art has almost no lettering. *DRUHÝ ŽIVOT*, *ZÁPIS / MONITOR* and the FLYER icon are the candidates to variablise. Real signage stays Slovak. English text always quotes the English rendering of a story text.
18. **Era vocabulary is kept, not explained away.** This covers Comrade, Pioneers, work brigade, requisition slip and returnable jars (1982), crowns, phonecard and personal stereo (1995), and two metres, quarantine and remote learning (2020). Brand names are avoided.
19. **The knowledge rule and the Zuzana rules carry over unchanged.** English never adds a name, a role or a hint the Slovak line does not have. Zuzana gets no surname, no life story and no foreshadowing, and a list of banned English phrases enforces it.
20. **Typography and checks.** Curly ’ and ‘…’, a spaced en dash, sentence case for names and UI, title case for titles, and the same length limits as Slovak. The checks are local LanguageTool en-GB with the allow list, plus the consistency scripts. No paid service is used.

## How the English is made (and checked)

1. **Translate.** Claude translates from the live Slovak (`sk` column = game.json + `sk_overrides.csv` + the
   content overlays), chunk by chunk (C1 2020, C2 1995, C3 1962 + 1982, C4 2035 + cutscenes + UI; the bundles of
   `tools/writing_bundles.py`), in story order, one whole exchange at a time, with this glossary, VOICES.md and
   the bundle open.
2. **Independent review.** A second Claude pass (not the translator’s own) per chunk: meaning, voice, register,
   jokes, era, knowledge rule, Zuzana rules, length.
3. **Local checks.** LanguageTool en-GB run locally (Java 21 + `language_tool_python`, offline, words of
   `spellcheck_allow` ignored), plus scripts: glossary consistency (items, rooms, hotspots, topic labels exactly
   as here), placeholders, length limits, protected facts and verbatim lines, deprecated words and jargon. No
   fal.ai, no GPT, no paid service.
4. **Final read-through** in story order by Claude, then the texts go into the `en` column. The owner does not
   approve the English first (owner, 2026-10-08).

## 0. What never changes

- The English translates the **current Slovak text of the same key**. It never adds or drops information, a
  clue, a name, an item or a step; same key, same speaker, same order. Overlay keys (`x01`, `z01`, `k01` …)
  are translated like every other key.
- A clue line states the clue plainly, with the same value (§ 10). Verbatim lines use the fixed English of
  § 10.4. Puzzle options are fixed (§ 10.4).
- `{placeholders}` stay exactly as they are; no line breaks, emoji or stage directions.
- English is not a second rewrite. If a Slovak line looks wrong, translate it faithfully and report it in the
  note; the Slovak fix goes through WRITING_METHOD.md.
- A missing English text falls back to Slovak (ARCHITECTURE.md), so a key is either fully translated or left
  empty, never half.

## 1. Language variant

- **British English**, today’s natural spoken English. Every line must sound like something a person would
  say in that situation; read it aloud. No translationese: restructure the sentence rather than mirror Slovak
  word order.
- **Spelling:** -ise (*recognise, normalise, organise, realise*), -our (*colour, behaviour, neighbour*), -re
  (*centre, metre*), *catalogue, programme* (but *program* for software), *travelled, cancelled, grey,
  aluminium, tyre, kerb, licence* (noun) / *license* (verb), *practice* (noun) / *practise* (verb), *defence*,
  *mum, maths*.
- **Vocabulary:** *shop, queue, pavement, flat, block of flats, lift, torch, bin, rubbish, post, postman,
  holidays, autumn, football, biscuit, sweets, car park, mobile, tap, trolley, letterbox, net curtain, flask,
  aerial, spade, handcart, offcut, mended, perished (rubber), lead (cable), adaptor, tailor’s dummy, telly
  (speech)*.
- **Register** comes from VOICES.md: Adam dry and self-ironic; Alojz charmingly official; Rudo theatrical (the
  only one with frequent exclamation marks); devices terse; children plain, never baby talk.
- **Contractions** are natural in speech (*I’m, don’t, it’s*). Device and system texts (`SYSTEM`) use none and
  stay terse: *Wearer recognised. Wearer’s memory protected.* Officials may contract less.
- **Numbers:** as in Slovak: years in digits; ages and durations may be words in speech (*thirty-eight
  years*), digits in goals and hints (*38 years*). Metric units. Money: *crowns* (koruna), never *korunas*.
- **Dates:** *6 June 1962*, *7 December 1982*, *15 June 1995*, *29 October 2020*, *6 February 2035* (no
  ordinal, no comma). Times of day in speech: *nine till five*.
- **Typography:** apostrophe ’; quotation marks ‘…’, nested “…”; spaced en dash ` – ` in sentences, unspaced in
  ranges and codes (`9–17`, `3–2–6`); hyphen in codes (`K-17`, `Z-17`); `3 × 4`; ellipsis `…` as one
  character; *Mr, Mrs, Ms, Dr* without a full stop; no Oxford comma unless it prevents a misreading. Signs,
  switch positions and port names in capitals exactly as fixed here. The game fonts (Alegreya, Alegreya Sans)
  contain every one of these characters (checked 2026-10-08).
- **Case:** sentence case for rooms, hotspots, items, exits, action and topic labels and the UI (*Physics prep
  room*, *Spare fuse*, *Fast travel*). Title case only for the game title, quest titles and cutscene titles.

## 2. The title and the bell

- **`game.title` = *The Last Bell*** (code name LastBell). In Slovakia the *posledný zvonec* is the bell that
  ends the school year; the English title keeps both meanings, the school bell and the device ZVON.
- **ZVON stays ZVON**: capitals, never translated, possessive *ZVON’s*, *the ZVON workshop*, *the ZVON base
  node*, *the first ZVON*. It is not *BELL*, *the Bell* or a *time machine*.
- The pun is carried by (a) the title, (b) Mira’s answer in G05.005 to *Prečo práve ZVON?* (*Why ZVON, of all
  names?*), which says the name once in plain words, for example: *Because the first thing it did was ring
  out. Like a bell – a zvon. We never came up with anything better.*, (c) the bell emblem on the chronometer
  and (d) every *zvonček / zvonec / zvonenie*, which is always *bell / ringing*: Zuzana’s class bell, Kubo’s
  bike bell, *The First Last Bell*, *Another Last Bell*.

## 3. People

### 3.1 Names

- People keep their **Slovak names with diacritics**: Adam Hruška, Mira Hrušková, Tóno, Soňa, Štefan, Šimon,
  Lída, Sára, Ružena, Božo, Béla, Očko. Never anglicise (*Anton* not *Anthony*, *Jozef* not *Joseph*,
  *Zuzana* not *Susan*). Female surnames keep *-ová* (*Mrs Hrušková*).
- Slovak cases disappear: *Tóna, Tónovi, Tónom* → *Tóno*. Possessive adjectives become *’s*: *Mirin* → Mira’s,
  *Otov* → Oto’s, *Paliho* → Pali’s, *Deziderova* → Dezider’s, *Leina* → Lea’s, *Ninin* → Nina’s, *Bodkova* →
  Bodka’s, *Kubov* → Kubo’s. Names ending in *-s*: *Boris’s*.
- Surnames that repeat (Kováč, Fiala/Fialová, Urban/Urbanová) are coincidences in English too.

### 3.2 Nicknames, diminutives, animals

- *Tóno, Pali, Juro, Fero, Rudo, Božo* are the names people use; keep them.
- **Zuzka** only from Ivanka adults in 1962, to or about little Zuzana. **Kubko** only from adults to Kubo.
  **Dezi** only from Dezider’s friends; everyone else, and every system text, says *Dezider*.
- A descriptive epithet is translated when its meaning is the joke: *Juro Kazeta* → **Juro Cassette**
  (speaker label, hover label and *Juro Cassette, that’s me.*). He is *Juro* in speech, never *Juraj*.
- **Bodka** (a male dog, *he*; *Woof!*), **Béla** (Alojz’s carrier pigeon, *he*), **Očko** (the delivery robot,
  *it*) keep their names.

### 3.3 Family words and ages

- *babka* → **Gran**: Adam in 2020, and Adam’s own remarks about her in any era (*Gran said Oto was a
  mechanic.*). Neighbours say *Mrs Hrušková* or *your gran*. Every text that is not someone speaking
  (objectives, journal, hints, item and room names) says **Mira**. Never *Grandma, Granny, Nan, Mirka*.
- *dedo* (Tóno 12 about Oto) → **Grandad**. *mamka* (Zuzana 1962) → **Mum**, *my mum*. *vnuk* → grandson.
- Ages in system texts are qualifiers: *twelve-year-old Tóno*, *young Mira*, *Tóno at the service window in
  2020*; never *Tóno 12*, *Jana 82*.

### 3.4 Speaker labels that change in English

All other labels are identical to the Slovak (names). Hover labels of NPCs use the same text.

| id | Slovak label | English label |
|---|---|---|
| JURO | Juro Kazeta | Juro Cassette |
| ROBOT | Doručovací robot Očko | Očko the delivery robot |
| DOBRO | Učiteľ Dobrovič | Mr Dobrovič |
| LEA_REC | Lea Kormanová (správa z roku 2032) | Lea Kormanová (message from 2032) |
| ADAM10 | Adam (10 rokov, nahrávka 1995) | Adam (aged 10, 1995 recording) |
| SYSTEM | Zariadenie | Device |
| NARRATOR | Rozprávač | Narrator |
| NINA_REMOTE | Nina (na diaľku) | Nina (remote) |

### 3.5 People

| speaker id(s) | English name | in speech | address with Adam | notes |
|---|---|---|---|---|
| ADAM | Adam Hruška | Adam; Mr Hruška (officials) | — | 35 in every era; repairman; British register: dry, self-ironic, contractions |
| ADAM10 | Adam (aged 10, 1995 recording) | — | Lea → him: first name | a child’s voice on the tape |
| MIRA20, MIRA95, MIRA60 | Mira Hrušková | Gran (Adam in 2020 only); Mrs Hrušková (neighbours, 1995 adults, Tóno 50); Mira (Oto, Vera, colleagues, system texts); young Hrušková (Ivanka villagers 1962) | she → Adam: ‘Adam’, familiar; Adam → Mira 1995: polite, ‘Mrs Hrušková’ when he must; Adam → Mira 1962: polite, no title | never Granny, Grandma, Nan, Mirka; system texts (goals, journal, hints, items, rooms) say Mira |
| TONO82, TONO, TONO20 | Tóno | Tóno; Mr Farkaš (Adam in D02 before the 1982 trip, officials); the caretaker | see § 4.3: the switch from polite to first name is a story beat | full name Anton Farkaš; label is ‘Tóno’ in every era |
| OTO, OTO82 | Oto Bielik | Oto; Mr Bielik (Adam, Marta, Ružena); Grandad (Tóno 12 only); Uncle Oto (Zuzana) | polite both ways | Oto’s workshop, Oto’s slip |
| JANA82, JANA95, JANA20, JANA35 | Jana Vargová | Jana; Mrs Vargová (1995), Ms Vargová (2020, 2035) when formal | Jana 12 → Adam: polite, no name; Adam → Jana 12: first name; later polite both ways | Jana’s schematic |
| LEA95, LEA_REC | Lea Kormanová | Mrs Kormanová; Miss (pupils addressing her); Miss Lea (pupils talking about her) | polite both ways; she → the 10-year-old Adam: first name | her message of 2032 is verbatim (§ 10.4) |
| VIKTOR | Viktor Korman | Viktor; Mr Korman | polite both ways | Lea’s son; never a villain |
| NINA, NINA_REMOTE | Nina Švecová | Nina; Ms Švecová | polite both ways | Ela’s daughter |
| ELA | Ela Švecová | Ela | first names both ways |  |
| DANA | Dana Valová | Dana | first names both ways |  |
| ROMAN | Roman Kováč | Roman | first names both ways | Roman’s signature |
| LENKA | Lenka Bartošová | Lenka | first names both ways |  |
| BODKA | Bodka | Bodka | — | a male dog: he/him; Bodka’s ball; only barks: ‘Woof!’ |
| JOZEF | Jozef Mlynár | Mr Jozef (Adam; first name kept on purpose: respectful and warm) | he → Adam: ‘young man’, familiar; Adam → him: polite |  |
| SONA | Soňa Urbanová | Soňa | she → Adam: polite, no name; Adam → her: first name | 11 |
| ZITA | Zita Ondrušová | Zita | she → Adam: familiar; Adam → her: polite |  |
| EMIL | Emil Belan | Emil | he → Adam: familiar; Adam → him: polite | Emil’s song ‘Four Stops’ |
| PALI | Pavol Drobný | Pali | first names both ways (fellow repairmen) | Pali’s repair shop (never ‘Pavol’s’) |
| VIERA | Viera Holubová | Viera; Mrs Holubová | polite both ways | 1995 bookseller; never confuse with Vera (1962) |
| ARCHIVAR / KAROL | Karol Merta | Mr Merta; Karol (hints) | polite both ways | head of the archive reading room |
| FOTO / ALENA | Alena Svobodová | Alena; Mrs Svobodová | polite both ways |  |
| TRH / FERO | Fero Lánik | Fero | he → Adam: familiar; Adam → him: polite | Fero’s scales |
| MILADA | Milada Kyselová | Milada; Mrs Kyselová | polite both ways | tailor |
| JURO | Juraj Malík, known as Juro Cassette | Juro | first names both ways | label ‘Juro Cassette’; never ‘Juraj’ (that is the painter) |
| JURAJ | Juraj Križan | Juraj | he → Adam: polite; Adam → him: first name | 19; Juraj’s sketch |
| DEZI | Dezider Kováč | Dezider; Dezi (only his friends) | he → Adam: familiar; Adam → him: polite | the radio ham; Dezider’s garage, coil |
| BOZO | Božidar Fiala | Božo; Mr Fiala; Uncle Božo (Zuzana) | polite both ways | station worker |
| BERTA | Berta Kovárová | Mrs Kovárová; Berta; Auntie Berta (Zuzana) | polite both ways; she → Adam: ‘young man’ |  |
| POSTA / ALOJZ | Alojz Baran | Mr Baran; Alojz (hints) | polite both ways | the only one allowed charming officialese |
| — | Béla | Béla | — | Alojz’s carrier pigeon (he); Béla’s feed |
| LIDA | Lída Fialová | Lída; Auntie Lída (Zuzana) | polite both ways | Lída’s hand punch |
| RUDO | Rudolf Pavlík | Rudo; Uncle Rudo (Zuzana) | polite both ways | Rudo’s script |
| SKLAD / STEFAN | Štefan Haluška | Štefan; Uncle Štefan (Zuzana) | polite both ways | storekeeper |
| VERA60 | Vera Nemcová | Vera; Auntie Vera (Zuzana) | polite both ways | Vera’s blunt stylus; 1962 draughtswoman, not Viera |
| ZUZANA | Zuzana | Zuzana; Zuzka (Ivanka adults in 1962 only) | she → Adam: polite, ‘mister’ at most; Adam → her: first name | 7 in June 1962; no surname, ever; § 14 |
| ZUZANA95 | Zuzana | Zuzana; Auntie Zuzana (Kubo only) | polite both ways; she → Kubo: first name | 40 on 15 June 1995; nobody says Zuzka in 1995 |
| KUBO | Kubo | Kubo; Kubko (diminutive, adults to him) | he → Adam: polite, ‘mister’ at most; Adam → him: first name | 7; a neighbour’s child, never Zuzana’s; Kubo’s bike |
| DOBRO | Mr Dobrovič | Comrade Teacher (pupils, 1982); Mr Dobrovič (Adam, adults) | polite both ways | 1982 teacher; no first name |
| RUZENA | Ružena Malá | Mrs Malá | polite both ways |  |
| MARTA82 | Marta Dobiášová | Mrs Dobiášová | polite both ways |  |
| SIMON | Šimon Rybár | Šimon; Mr Rybár | polite both ways | school gardener |
| TAMARA | Tamara Kráľová | Tamara | first names both ways | her travelling workshop ‘Second Life’ |
| BORIS | Boris Urban | Mr Urban; Boris | polite both ways | Boris’s footnotes |
| SARA | Sára Vrbová | Sára; Ms Vrbová | polite both ways |  |
| ROBOT | Očko the delivery robot | Očko (it) | it → Adam: polite | Očko’s delivery request |
| IVAN | Ivan Horský | Ivan | polite both ways | cable-car staff |
| TURISTA | Miloš Polák | Miloš | polite both ways |  |

## 4. Forms of address and ty / vy

### 4.1 Register instead of pronouns

English has one *you*, so *vy* and *ty* become register.

- **vy (polite):** complete sentences, *please*, *would you*, *excuse me*, *thank you very much*; a title and
  surname when the Slovak uses *pán / pani* or English needs an address; no first name unless the Slovak has
  one; no *mate*, *love*, *pal*.
- **ty (familiar):** first names, shorter sentences, casual turns (*Hang on.*, *Go on, then.*), teasing allowed.
- A line never mixes the two registers, just as a Slovak line never mixes *ty* and *vy*.

### 4.2 Titles and address words

| Slovak | English | who |
|---|---|---|
| pán + surname | Mr + surname | everyone (*Mr Bielik, Mr Merta, Mr Korman*) |
| pani + surname | Mrs + surname | 1962, 1982, 1995; and Mira Hrušková in every era |
| pani + surname (2020, 2035, working women) | Ms + surname | Nina, Sára, Jana at 50 and 65 when formal |
| pán + first name (*pán Jozef*) | Mr + first name (*Mr Jozef*) | Adam to Jozef: respectful and warm on purpose |
| mladý pán | young man | Jozef, Berta to Adam |
| pani učiteľka (pupils, 1995) | Miss; about her: *Miss Lea* | Soňa, the children on the tape |
| súdruh učiteľ, súdružka riaditeľka (pupils, 1982) | Comrade Teacher, Comrade Headmistress | Jana 12, Tóno 12; never a joke |
| pán učiteľ (adults) | Mr Dobrovič | Adam |
| teta / ujo + first name (children to adults) | Auntie / Uncle + first name | Zuzana 1962 (Auntie Mira, Auntie Vera, Auntie Lída, Auntie Berta, Uncle Oto, Uncle Štefan, Uncle Rudo, Uncle Božo; but *Mr Baran*), Kubo (*Auntie Zuzana*) |
| children’s *vy* to Adam | polite, at most *mister* | Zuzana, Kubo, Tóno 12 before E02; sparingly |
| *mladá Hrušková* (villagers 1962) | young Hrušková | Berta, Božo |

### 4.3 The switches are story beats

| who | before | after | the moment |
|---|---|---|---|
| Tóno 12 (1982) | polite, *mister* | first name and cheek from **E02** | *So I’m actually older than you.* |
| Tóno 25 (1995) | polite stranger, no name | *Adam*, familiar, from **E11** | E11.002 *Hang on. It’s you. Grandad was right.* |
| Tóno 50 (2020) | polite in D02 (*Mr Farkaš* from Adam) | familiar in **D07** | *I didn’t wait. I lived. …* |
| Tóno’s ambient topics (all ages) | neutral | neutral | no name, no *mister*, no *sir*: they play before and after the switch |
| Mira 1962 / 1995 | she calls him *Adam* (family echo) | – | Adam stays polite and never calls them *Gran* to their face |

The full per-character table is the *address* column of § 3.5 (from VOICES.md "Who says *ty* and who says
*vy*").

## 5. Places

- **Real places keep their Slovak names** with diacritics and **no article**: *in Dúbravka*, *on Kamenné
  námestie*, *on Starý most* (never *the old Starý most*), *at Biela Púť*, *on Chopok*.
- **Exonyms** only for features every English map uses: *the Danube*, *the Tatras*, *the Low Tatras*,
  *Czechoslovakia*. *Bratislava* is the same.
- **Slovak adjectives become the place name**, with a short English descriptor where the room name needs one:
  *Dúbravská zastávka* → Dúbravka stop, *Karloveské nástupište* → Karlova Ves tram stop, *Ivanská náves* →
  Ivanka village green, *Petržalský podchod* → Petržalka underpass, *Miletičova medzi stánkami* → Miletičova
  market. A descriptor never tells more than the Slovak (knowledge rule, § 14): *Garáž rádioamatéra* is
  *Radio ham’s garage*, not *Dezider’s garage*.
- **Year suffix** in room names: *Dúbravka stop, 1982*; in a sentence *in 1982*.
- **Exit and map labels** that equal a room name are exactly the English room name; `glossary_en.json` →
  `exit_labels_not_room_names` lists the others.
- **Businesses:** a fictional name is translated when its meaning carries a joke and the art has no
  lettering (*Pod druhou rukou* → *Second Hand*); a name is kept when the art or a line depends on the Slovak
  (*Svetlo*); real signage stays Slovak (§ 11).
- **Pri LEALe** (S69) is the owner’s local name: always *Pri LEALe*, undeclined, no article, never explained,
  never *by the LEAL* or *Sokolíkova courtyard*. *the wall at Pri LEALe*, *back to Pri LEALe*.

### 5.1 Places and how to use them

| Slovak | English | in a sentence | note |
|---|---|---|---|
| Chorvátsky Grob | Chorvátsky Grob | in Chorvátsky Grob; ‘Grob’ in speech | Adam’s village |
| Čierna Voda | Čierna Voda | in Čierna Voda |  |
| Lúčny koník | Lúčny koník | at Lúčny koník | real playground; not translated (‘meadow grasshopper’) |
| Dúbravka; Dúbravská zastávka | Dúbravka; Dúbravka stop | in Dúbravka | adjectives become the place name |
| ZŠ Sokolíkova | Sokolíkova School | at Sokolíkova | the painted sign ZÁKLADNÁ ŠKOLA SOKOLÍKOVA stays Slovak |
| Pri LEALe | Pri LEALe | at Pri LEALe; back to Pri LEALe; the wall at Pri LEALe | owner’s local name; LEAL always capitals; never explained, never ‘by the LEAL’ |
| Karlova Ves | Karlova Ves | in Karlova Ves |  |
| Staré Mesto | Staré Mesto | in Staré Mesto; ‘the Old Town’ only in speech |  |
| Kamenné námestie | Kamenné námestie | on Kamenné námestie | no article |
| Ružinov | Ružinov | in Ružinov |  |
| Miletičova (Miletička) | Miletičova | on Miletičova; the Miletičova market | the colloquial ‘Miletička’ is not used in English |
| Petržalka | Petržalka | in Petržalka |  |
| Starý most | Starý most | on Starý most | no article; never ‘the old Starý most’ |
| Dunaj | the Danube |  | exonym |
| Ivanka pri Dunaji (Ivanka; Ivanská …) | Ivanka pri Dunaji (Ivanka) | in Ivanka |  |
| kanál (Šúrsky kanál) | the canal |  |  |
| Jasná | Jasná | in Jasná |  |
| Biela Púť | Biela Púť | at Biela Púť |  |
| Priehyba | Priehyba | at Priehyba |  |
| Chopok | Chopok | on Chopok |  |
| Rotunda | the Rotunda | by the Rotunda |  |
| Grand Jasná (v Grande) | Hotel Grand Jasná; the Grand Jasná | ‘the Grand’ in speech |  |
| Vrbické pleso | Vrbické pleso | by Vrbické pleso; ‘the lake’ | pleso → lake (not ‘tarn’) |
| Funitel | the Funitel | on the Funitel | real lift type |
| Tatry; Nízke Tatry | the Tatras; the Low Tatras |  | exonyms |
| ČSSR; Československo | Czechoslovakia (‘ČSSR’ only where painted or quoted) |  |  |
| Bratislava | Bratislava |  |  |
| sídlisko; panelák | housing estate (the estate); block of flats (the blocks) |  | British |

### 5.2 Businesses and named places

| Slovak | English | note |
|---|---|---|
| Antikvariát Pod druhou rukou | the Second Hand bookshop | fictional, no lettering in the art: translated so the pun survives (second-hand books, the clock’s second hand) |
| Fotoateliér Svetlo | the Svetlo photo studio | kept: Alena explains the name (‘Svetlo means light’), see § 13 |
| Druhý život / plaque DRUHÝ ŽIVOT | Second Life / plaque SECOND LIFE | Tamara’s travelling workshop; the meaning is the point; plaque is a variablisation candidate (§ 11) |
| Paliho opravovňa | Pali’s repair shop |  |
| kazetový klub v suteréne | the basement cassette club |  |
| Deziderova garáž (číslo 17) | Dezider’s garage (number 17) |  |
| Otova (mechanická) dielňa | Oto’s (mechanical) workshop |  |
| archívna študovňa | the archive reading room |  |
| klientske centrum Biela Púť | the Biela Púť customer centre |  |
| Potraviny (sign POTRAVINY) | the shop (sign stays POTRAVINY) | real Slovak signage |
| kultúrna sála | the village hall |  |
| hospodársky dvor; sklad | the farm yard; the store |  |

### 5.3 Rooms (69)

Room names are also exit and map labels.

| id | Slovak | English |
|---|---|---|
| S01 | Adamova garáž | Adam’s garage |
| S02 | Ulica medzi plotmi | Lane between the fences |
| S03 | Lúčny koník – výdajné miesto | Lúčny koník – pick-up point |
| S04 | Potraviny cez okienko | Shop at the hatch |
| S05 | Mirina bránka | Mira’s garden gate |
| S06 | Pod zatvoreným oknom | Below the closed window |
| S07 | Čierna Voda pri výveske | Čierna Voda, by the notice board |
| S08 | Chodník pri retenčnej nádrži | Path by the retention pond |
| S09 | Predsieň záhradnej dielne | Garden workshop porch |
| S10 | Dielňa ZVON | ZVON workshop |
| S11 | Dúbravská zastávka | Dúbravka stop |
| S12 | Pred ZŠ Sokolíkova | Outside Sokolíkova School |
| S13 | Školská vstupná chodba | School entrance hall |
| S14 | Trieda pamäťového krúžku | Memory club classroom |
| S15 | Fyzikálny kabinet | Physics prep room |
| S16 | Miestnosť školského rozhlasu | School PA room |
| S17 | Školský dvor | School yard |
| S18 | Sídliskový dvor s kioskom | Estate courtyard with kiosk |
| S19 | Karloveské nástupište | Karlova Ves tram stop |
| S20 | Paliho opravovňa | Pali’s repair shop |
| S21 | Kamenné námestie | Kamenné námestie |
| S22 | Antikvariát Pod druhou rukou | Second Hand bookshop |
| S23 | Archívna študovňa | Archive reading room |
| S24 | Fotoateliér Svetlo | Svetlo photo studio |
| S25 | Miletičova medzi stánkami | Miletičova market |
| S26 | Opravovňa odevov | Tailor’s repair shop |
| S27 | Kazetový klub v suteréne | Basement cassette club |
| S28 | Petržalský podchod | Petržalka underpass |
| S29 | Garáž rádioamatéra | Radio ham’s garage |
| S30 | Merací stánok na Starom moste | Measuring booth on Starý most |
| S31 | Ivanská železničná zastávka | Ivanka railway station |
| S32 | Ivanská náves | Ivanka village green |
| S33 | Pošta s prepážkou | Post office counter |
| S34 | Kultúrna sála pred skúškou | Village hall before rehearsal |
| S35 | Dvor hospodárskej dielne | Farm workshop yard |
| S36 | Otova mechanická dielňa | Oto’s mechanical workshop |
| S37 | Park pri kaštieli | Manor house park |
| S38 | Pred skúšobnou čerpacou búdkou | Outside the test pump hut |
| S39 | Miestnosť prvého ZVONu | Room of the first ZVON |
| S40 | Povala technického archívu | Technical archive loft |
| S41 | Biela Púť pri dolnej stanici | Biela Púť, bottom station |
| S42 | Pred hotelom Grand Jasná | Outside Hotel Grand Jasná |
| S43 | Lobby hotela Grand Jasná | Hotel Grand Jasná lobby |
| S44 | Výstavný salón hotela Grand Jasná | Grand Jasná exhibition room |
| S45 | Chodník pri Vrbickom plese | Path by Vrbické pleso |
| S46 | Klientske centrum Biela Púť | Biela Púť customer centre |
| S47 | Chopok pri Rotunde | Chopok, by the Rotunda |
| S48 | Servisný pavilón výstavy Atlas | Atlas exhibition service pavilion |
| S49 | Chronokomora pavilónu Atlas | Atlas pavilion chronochamber |
| S50 | Vyhliadková terasa pri Rotunde | Viewing terrace by the Rotunda |
| S51 | Dúbravská zastávka v roku 2020 | Dúbravka stop, 2020 |
| S52 | Pred ZŠ Sokolíkova v roku 2020 | Outside Sokolíkova School, 2020 |
| S53 | Školské zádverie v roku 2020 | School entrance lobby, 2020 |
| S54 | Fyzikálny kabinet v roku 2020 | Physics prep room, 2020 |
| S55 | Školský dvor v roku 2020 | School yard, 2020 |
| S56 | Školnícke servisné okno v roku 2020 | Caretaker’s service window, 2020 |
| S57 | Dúbravská zastávka v roku 1982 | Dúbravka stop, 1982 |
| S58 | Pred ZŠ Sokolíkova v roku 1982 | Outside Sokolíkova School, 1982 |
| S59 | Školská chodba v roku 1982 | School corridor, 1982 |
| S60 | Trieda pred technickou výstavkou v roku 1982 | Classroom before the exhibition, 1982 |
| S61 | Školský dvor s mladou lipou v roku 1982 | School yard with a young lime, 1982 |
| S62 | Sídliskový obchod v roku 1982 | Estate shop, 1982 |
| S63 | Fyzikálny kabinet v roku 1982 | Physics prep room, 1982 |
| S64 | Tóno a dedo pri servisnom okne v roku 1982 | Tóno and Grandad at the service window, 1982 |
| S65 | Výdajňa školského údržbového materiálu v roku 1982 | School maintenance store, 1982 |
| S66 | Školský záhradný sklad v roku 1982 | School garden shed, 1982 |
| S67 | Priehyba pri prestupe na Funitel | Priehyba, change for the Funitel |
| S68 | Kabína Funitelu medzi Priehybou a Chopkom | Funitel cabin, Priehyba to Chopok |
| S69 | Pri LEALe | Pri LEALe |

Regions (map) and era cards keep the Slovak place names (`region.*`, `era.*.card`); era dates are in § 1.

## 6. Devices and recurring terms

One English rendering per term. "Also / in speech" lists the only allowed variants.

| Slovak | English (canonical) | also / in speech | note |
|---|---|---|---|
| ZVON (ZVONu, ZVONom) | ZVON | ZVON’s; ‘the ZVON’ only in hints as the device | device name, always capitals, never translated; the bell pun is carried once by Mira (G05.005) and by the title (§ 2) |
| prenosný chronometer (ZVON) | portable chronometer; Portable ZVON chronometer (item) | the chronometer | never ‘time machine’, ‘watch’, ‘chronograph’ |
| ochranné pole chronometra | the chronometer’s protective field | the field | protects Adam, his bag and what he carries |
| nositeľ; pamäť nositeľa | wearer; the wearer’s memory |  | device voice: ‘Wearer recognised. Wearer’s memory protected.’ |
| stolový uzol ZVON | ZVON base node | the base node | the stationary unit in Mira’s garden workshop; pairs with the portable chronometer |
| kolíska | cradle |  | the chronometer docks in the base node’s cradle |
| tvarový panel; tvarový prepojovací panel | shape panel; shape patch panel |  | P01 |
| časový uzol; uzlové hodiny (speech); UI Uzol | time node; the node clock; UI ‘Node’ |  | the old clock frames at the stops |
| časové okno; otvoriť časové okno | time window; open a time window |  | a year open for travel |
| časová adresa / referencia (device) | reference (device only) |  | ‘time address’ is never used in goals, hints or journal; device: ‘Reference 1995 restored.’ |
| spätný zápis | write-back | Atlas’s write-back | never ‘retroactive write’ |
| zápis (Atlas’s process); ZÁPIS (switch) | the write; WRITE (switch) |  | ‘WRITE off, MONITOR on.’ |
| normalizátor; panel normalizácie; normalizácia | normaliser; normalisation panel; normalisation |  | British -ise; the panel shows DIFFERENCE = DISCARD |
| návratový zásobník (zásobník) | return buffer (the buffer) |  | the Slovak ban on ‘buffer’ does not apply: in English it is the natural word |
| Atlas (Atlasu) | Atlas | Atlas’s | Viktor’s organisation and exhibition (2035); never the 1995 tape |
| výstava Atlas; servisný pavilón; chronokomora; panel obnovy | the Atlas exhibition; service pavilion; chronochamber; restore panel |  | never ‘synchronisation chamber’ |
| Zvukový atlas našej školy; krúžok; pamäťový krúžok | Our School’s Sound Atlas (tape label); the club; the memory club | the sound atlas | Mira’s and Lea’s 1995 after-school club |
| značka krúžku | the club’s emblem |  | the small bell emblem on the chronometer |
| Mirin fond; fond Z-17; krabica Z-17 | Mira’s collection; collection Z-17; box Z-17 |  | archive sense; never ‘fonds’, ‘fund’ |
| kalibračná platňa (mosadzná) | brass calibration plate | the plate | stays in 1962 on the device |
| odtlačok → nezvýraznený, čitateľný, overený odtlačok z roku 1962 | imprint → faint imprint, legible imprint, verified imprint from 1962 |  | never ‘copy’ (that is Mira’s archive copy) |
| archívna kópia; kovová schránka | archive copy; metal archive box |  |  |
| registračný list; druhopis; uhľový papier; pečiatka | registration form; duplicate; carbon paper; stamp |  | the post office confirms the date, not the truth |
| pravidlo ‘Rôzne údaje neznamenajú neplatné údaje.’ | the rule ‘Different data are not invalid data.’ | Mira’s rule, Mira’s sentence | engraved on the plate; spoken variant ‘What doesn’t match, we keep side by side.’ |
| štyri svedectvá: Pôvod, Hlas, Súhlas, Návrat | the four testimonies: Origin, Voice, Consent, Return | proof of origin / consent | port names; capitals on the plate and in device texts: ORIGIN, VOICE, CONSENT, RETURN |
| port Pôvod / Hlas / Súhlas / Návrat | Origin port / Voice port / Consent port / Return port |  |  |
| pôvodná školská kazeta; kazeta s rušenými stopami | original school cassette; cassette with clashing tracks | ‘tape’ allowed in speech |  |
| kazeta; magnetofón; kazetový mechanizmus | cassette; tape recorder; cassette deck | tape (speech) |  |
| remienok | drive belt (belt) |  | rozpadnutý = perished |
| krížový adaptér; dvojpólový konektor; izolačný návlek; zvuková prepojka; servisný zvukový vstup | cross adaptor; two-pin connector; insulating sleeve; audio lead; service audio input |  | British ‘adaptor’ and ‘lead’ |
| mapa meracích uzlov; priehľadná fólia K-17; tri registračné značky (dierka, dvojitý kríž, štvorec) | map of measuring nodes (node map); transparent overlay K-17; three registration marks (a hole, a double cross, a square) |  | P02; ‘double cross’ without a hyphen (not the betrayal) |
| meracia cievka; metronóm; rytmický nákres; tri kalibračné číslice | measuring coil; metronome; rhythm drawing; three calibration digits |  | P03; never ‘loop’ for the coil |
| merací stánok na Starom moste | the measuring booth on Starý most | the booth |  |
| ručná pumpa; demonštračný chladiaci model; kožená manžeta; nity; dierovač; svorka kulisy | hand pump; demonstration cooling model; leather cuff; rivets; hand punch; stage flat clamp |  | ‘cuff’ keeps Zuzana’s shirt-cuff joke |
| skúšobná čerpacia búdka; meracia miestnosť | test pump hut; measuring room | the hut |  |
| povala technického archívu | technical archive loft | the loft |  |
| návratový mostík (keramický); keramická pätica; tri prepojky; servisná doska | return bridge (ceramic); ceramic base; three copper links; service board | the bridge | never ‘jumper’ for prepojky (avoids a clash with the audio lead) |
| zavárací pohár s tesnením; zapečatený pohár | preserving jar with a seal; sealed jar | the jar |  |
| servisná dutina v múriku; mriežka 3 × 4 | service cavity in the low wall; 3 × 4 grid | the cavity; ‘hiding place’ only in Tóno’s speech | second row from the top, third stone from the left = row 2, column 3 |
| múrik | the low wall | the wall |  |
| lastovička | swallow |  | Tóno’s swallow: wooden in 1982, metal in 1995 and 2020 |
| heslo ‘Lastovička sa vracia.’ | the password ‘The swallow comes back.’ |  | verbatim; echoed by Q6 ‘Béla Comes Back’ |
| mladá lipa; ochranná ohrádka; trasa ručného vozíka | young lime tree; tree guard; the handcart’s route | the lime | British ‘lime tree’, never ‘linden’; never ‘butterfly effect’ |
| chránená fotografia dvora 2020 | protected photo of the 2020 yard |  | does not change |
| servisné okno (školnícke) | service window (the caretaker’s) |  | the same window in 1982, 1995, 2020 |
| školník | caretaker |  | never ‘janitor’ |
| fyzikálny kabinet | physics prep room | the prep room | British school term; never ‘cabinet’ |
| školský rozhlas | school PA |  | never the brand ‘Tannoy’ |
| servisná kniha z roku 1982; kópia servisného záznamu 1982 | 1982 service logbook; copy of the 1982 service record |  |  |
| protokol o odovzdaní; potvrdené odovzdanie 2020 | handover record; confirmed handover 2020 | the handover | recorded after it really happened |
| poverenie | letter of authority |  |  |
| výdajný lístok; výdajka | requisition slip | slip |  |
| lokálna (zvuková) čítačka; katalógová karta; servisný preukaz; spiatočný lístok na oba úseky | local audio reader; catalogue card; service visitor pass; return ticket for both sections | the reader; the pass; the ticket |  |
| kabínková lanovka; Funitel; dolná / vrcholová stanica | gondola (cable car in general speech); the Funitel; bottom / top station |  | they always work; never part of a trick |
| servisný terminál; pasívny stojan; miestna referenčná stopa; podpísaný obnovovací postup | service terminal; passive stand; local reference trace; signed restore procedure |  |  |
| oddelený konektor Atlasu; prepínač ZÁPIS / MONITOR | Atlas’s separate connector; the WRITE / MONITOR switch |  | MONITOR only reads |
| Leina pôvodná správa | Lea’s original message |  | the normaliser left only ‘call me’ |
| výdajné miesto (pri Lúčnom koníku) | pick-up point (at Lúčny koník) |  | Ela’s outdoor point |
| servisná brašna | tool bag | the bag | the in-world word for what the UI calls Inventory is ‘bag’ |
| brašňa (inventory in hints) | bag | ‘in the bag’ | hints say ‘In the bag, combine …’; the UI says Inventory |
| denník | journal |  | in-world: Adam’s notes; UI: Journal |
| zápisník | notebook |  |  |
| nápoveda (UI) | Hints |  |  |
| Mirina záhradná dielňa; predsieň; dielňa ZVON | Mira’s garden workshop; porch; ZVON workshop | the workshop | Adam may call it ‘Gran’s workshop’ |
| hádanka (UI only) | puzzle (UI only) |  | never in in-world text |

## 7. Items (83)

The bag shows the name; looks, goals and hints use **the same noun** (with *the* / *a* as English needs:
*Use the spare fuse on the ZVON base node.*). Lower case inside sentences except proper names.

| id | Slovak | English |
|---|---|---|
| PHONE | Adamov telefón | Adam’s phone |
| TOOLS | Servisná brašna | Tool bag |
| ORDER | Mirin nákupný lístok | Mira’s shopping list |
| GROCERIES | Taška s nákupom | Bag of shopping |
| SHEDKEY | Kľúč od dielne | Workshop key |
| CHRONO | Prenosný chronometer ZVON | Portable ZVON chronometer |
| FUSE_OLD | Prerušená poistka | Blown fuse |
| FUSE | Náhradná poistka | Spare fuse |
| LETTER | Mirino poverenie | Mira’s letter of authority |
| BELT_OLD | Rozpadnutý remienok | Perished drive belt |
| BELT_NEW | Nový remienok | New drive belt |
| TAPE_RAW | Kazeta s rušenými stopami | Cassette with clashing tracks |
| ADAPTER | Krížový adaptér bez konektora | Cross adaptor, no connector |
| CONNECTOR | Dvojpólový konektor | Two-pin connector |
| BRAID | Textilný izolačný návlek | Cloth insulating sleeve |
| LINK_OPEN | Adaptér s konektorom bez izolácie | Adaptor with connector, uninsulated |
| STEREOLINK | Hotová zvuková prepojka | Finished audio lead |
| TAPE | Pôvodná školská kazeta | Original school cassette |
| DIAGRAM | Mapa uzlov bez fólie | Node map without overlay |
| NEGATIVE | Technický fotografický negatív | Technical photo negative |
| CALPHOTO | Fotografia kalibračného stojana | Photo of the calibration stand |
| OVERLAY | Priehľadná fólia K-17 | Transparent overlay K-17 |
| NODEMAP | Úplná mapa meracích uzlov | Complete map of measuring nodes |
| COIL | Deziderova meracia cievka | Dezider’s measuring coil |
| METRONOME | Emilov metronóm | Emil’s metronome |
| SUPPLYSLIP | Otov výdajný lístok | Oto’s requisition slip |
| LEATHER | Predrezaná kožená manžeta | Pre-cut leather cuff |
| RIVETS | Dva duté nity | Two hollow rivets |
| PUNCH | Lídin ručný dierovač | Lída’s hand punch |
| CUFF_OPEN | Dierovaná manžeta | Punched cuff |
| CUFF | Hotová manžeta | Finished cuff |
| PUMPKEY | Kľúč od meracej miestnosti | Measuring room key |
| REGFORM | Technický registračný list | Technical registration form |
| STYLUS | Verino tupé rydlo | Vera’s blunt stylus |
| WAXPAPER | Voskovaný hárok | Waxed sheet |
| PRESSED | Nezvýraznený odtlačok | Faint imprint |
| ORIGIN_RAW | Čitateľný odtlačok | Legible imprint |
| CARBON | Uhľový papier | Carbon paper |
| REGDOUBLE | Dve vyhotovenia listu | Form in duplicate |
| REGISTERED | Potvrdený registračný list | Stamped registration form |
| ORIGIN | Overený odtlačok z roku 1962 | Verified imprint from 1962 |
| HANDOVER | Protokol o odovzdaní | Handover record |
| HANDOVER_R | Protokol s Romanovým podpisom | Handover record signed by Roman |
| CHAIN | Potvrdené odovzdanie 2020 | Confirmed handover 2020 |
| READER | Lokálna zvuková čítačka | Local audio reader |
| CATALOG | Katalógová karta fondu Z-17 | Catalogue card, collection Z-17 |
| PASS | Servisný návštevnícky preukaz | Service visitor pass |
| FILTER_PHOTO | Záznam panelu normalizácie | Normalisation panel photo |
| LEA_MESSAGE | Leina nezmenená hlasová správa | Lea’s unaltered voice message |
| DIAGNOSTIC | Diagnostický protokol | Diagnostic report |
| PULSE | Miestna referenčná stopa | Local reference trace |
| PATCH | Podpísaný obnovovací postup | Signed restore procedure |
| BALL | Bodkova loptička | Bodka’s ball |
| FLYER | Veľký čitateľný oznam | Large-print notice |
| TEAMNEG | Obálka s tímovým negatívom | Envelope with the team negative |
| TEAMPHOTO | Fotografia družstva | Team photo |
| SCORE | Noty k Emilovej skladbe | Sheet music for Emil’s song |
| CHALK | Biela školská krieda | White school chalk |
| SEEDS | Hrsť semien pre Bélu | Handful of seed for Béla |
| PLAY | Rudov scenár | Rudo’s script |
| DELIVERY_NOTE | Očkova doručovacia požiadavka | Očko’s delivery request |
| DELIVERY_OK | Potvrdenie opravovne | Workshop’s confirmation |
| PHOTO2020 | Chránená fotografia dvora 2020 | Protected photo of the 2020 yard |
| SCHOOLPASS | Povolenie prevziať Mirin technický majetok | Permit to collect Mira’s equipment |
| LOG1982 | Kópia servisného záznamu 1982 | Copy of the 1982 service record |
| PARTSNOTE | Otov školský výdajný lístok | Oto’s school requisition slip |
| CERAMICPARTS | Diely návratového mostíka | Return bridge parts |
| BRIDGE_NEW | Nový keramický mostík | New ceramic bridge |
| JAR | Pohár s viečkom a tesnením | Jar with lid and seal |
| SEALED_NEW | Zapečatený pohár s mostíkom | Sealed jar with the bridge |
| TREEGUARD | Ochranná ohrádka pre lipu | Guard for the lime tree |
| CACHEMAP | Nákres servisnej dutiny | Sketch of the service cavity |
| KEEPERNOTE | Tónova poznámka z roku 1995 | Tóno’s note from 1995 |
| SEALED_OLD | Pohár vyzdvihnutý po 38 rokoch | Jar recovered after 38 years |
| RETURNBRIDGE | Zachovaný návratový mostík | Preserved return bridge |
| LIFT_TICKET | Spiatočný lístok na oba úseky | Return ticket for both sections |
| JANA_DRAWING | Janina pôvodná schéma | Jana’s original schematic |
| JANA_APPROVED | Schéma s povolením na výstavku | Exhibition-approved schematic |
| BELL_MUTE | Triedny zvonček bez pútka | Class bell without its loop |
| ZUZA_SLIP | Zuzanin lístok | Zuzana’s slip |
| STRAP | Kožený odrezok | Leather offcut |
| BELL_FIXED | Opravený triedny zvonček | Mended class bell |
| BELLCAP | Vrchnák zvončeka | Bell cap |

## 8. Quests, cutscenes, topic labels

### 8.1 Quest titles (title case)

| id | Slovak | English | note |
|---|---|---|---|
| M01 | Nákup pre babku | Shopping for Gran |  |
| M02 | Prístroj v záhrade | The Device in the Garden |  |
| M03 | Späť v škole | Back at School |  |
| M04 | Mechanika kazety | The Cassette Deck |  |
| M05 | Hlasy sa nerušia | No Interference | Slovak ‘nerušiť’ = interfere / do not disturb; English keeps the technical sense |
| M06 | Mapa v troch kusoch | A Map in Three Pieces |  |
| M07 | Rytmus na Dunaji | Rhythm on the Danube |  |
| M08 | Dielňa v Ivanke | The Workshop in Ivanka |  |
| M09 | Pôvodná veta | The Original Words |  |
| M10 | Dokument musí prežiť | The Document Must Survive |  |
| M11A | Tá istá škola o štvrťstoročie neskôr | The Same School, 25 Years Later | ‘štvrťstoročie’ is the quarter-century; digits keep the title short |
| M11B | Človek, ktorý si to zapamätá | Someone Who’ll Remember |  |
| M11C | Tridsaťosem rokov v jednom pohári | Thirty-Eight Years in a Jar |  |
| M11D | Skutočné odovzdanie počas karantény | A Real Handover in Quarantine |  |
| M12 | Prístup do Atlasu | Getting into Atlas |  |
| M13 | Zastaviť zápis | Stop the Write-Back | zápis / spätný zápis = the write-back (§ 6) |
| M14 | Čo z hlasu zostalo | What Was Left of a Voice |  |
| M15 | Štyria svedkovia | Four Witnesses |  |
| Q1 | Bodka bez bodky | Bodka Drops the Ball | Slovak pun: Bodka (= dot) without his ‘dot’ (the red ball); English idiom ‘drop the ball’, literally true here |
| Q2 | Výveska pre všetkých | A Notice Everyone Can Read |  |
| Q3 | Celý tím na jednej fotke | The Whole Team in One Photo |  |
| Q4 | Štyri zastávky | Four Stops |  |
| Q5 | Mapa rozsvietených okien | A Map of Lit Windows |  |
| Q6 | Béla sa vracia | Béla Comes Back | echoes the password ‘The swallow comes back.’ exactly as the Slovak ‘Béla sa vracia’ / ‘Lastovička sa vracia’ do |
| Q7 | Žiaden strach, miláčik | Never Fear, Darling |  |
| Q8 | Adresa nie je len súradnica | An Address Isn’t Just Coordinates |  |
| Q9 | Nápad mimo predlohy | Not by the Book | predloha / schválený vzor = the approved model; idiom ‘by the book’ |
| Q10 | Prvý posledný zvonec | The First Last Bell | keeps the paradox; Zuzana’s line ‘Last bell! And in September, the first one again.’ |
| Q11 | Druhý posledný zvonec | Another Last Bell | not ‘The Second Last Bell’: in British English ‘second last’ means ‘penultimate’ |

### 8.2 Cutscene titles (journal → *Replay scenes*)

| key | Slovak | English |
|---|---|---|
| ui.journal.scene_cs01 | Prvý skok: Dúbravka 1995 | First Jump: Dúbravka 1995 |
| ui.journal.scene_cs02 | Kazeta zo školského rozhlasu | The Tape from the School PA |
| ui.journal.scene_cs03 | Cesta do Ivanky 1962 | The Road to Ivanka, 1962 |
| ui.journal.scene_cs04 | Jeden predmet, veľa rúk | One Object, Many Hands |
| ui.journal.scene_cs05 | Stopa vedie do Jasnej 2035 | The Trail Leads to Jasná, 2035 |
| ui.journal.scene_cs06 | Leina správa | Lea’s Message |
| ui.journal.scene_cs07 | Mená sú späť | The Names Are Back |
| ui.journal.scene_cs08 | Lipa a múrik | The Lime Tree and the Wall |
| ui.journal.scene_cs09 | Lanovkou na Chopok | By Cable Car to Chopok |

### 8.3 Story topic labels (all 34; hints quote them)

Hints quote these labels in quotation marks (*Talk to Ela about ‘Gran’s shopping’.*), so the label and every
hint use exactly this text. Topic labels are the topic or Adam’s short question, ≤ 28 characters (hard 40),
and must not repeat Adam’s first line.

| action | Slovak label | English label |
|---|---|---|
| G02 | Babkin nákup | Gran’s shopping |
| G05 | Potrebuješ ešte niečo? | Anything else you need? |
| B03 | Problém s chronometrom | Trouble with the chronometer |
| B09 | Návlek na kábel | A sleeve for the cable |
| B18 | Metronóm na meranie | A metronome for measuring |
| I07 | Pumpa je opravená | The pump’s mended |
| I09 | Mazanie výnimiek v budúcnosti | What the future erases |
| I10 | Tupé rydlo | The blunt stylus |
| C02 | Protokol k babkinej krabici | A form for Gran’s box |
| F01 | Prichádzam kvôli fondu Z-17 | About collection Z-17 |
| Q1A | Čo je s Bodkom? | What’s up with Bodka? |
| Q2A | Pomôcť vám s oznamom? | Help with the notice? |
| Q2B | Máš oznam veľkým písmom? | Got a notice in large print? |
| Q3A | Hľadáš nejakú fotografiu? | Looking for a photo? |
| Q3B | Máte obálku pre školu? | An envelope for the school? |
| Q4A | Prečo tá melódia nekončí? | Why doesn’t the tune end? |
| Q4B | Máte Emilove noty? | Have you got Emil’s music? |
| Q5A | Čo chýba mape svetiel? | What’s missing from the map? |
| Q5B | Kúsok kriedy na panel? | Chalk for the panel? |
| Q6A | Kde je váš holub? | Where’s your pigeon? |
| Q6B | Krmivo pre Bélu | Feed for Béla |
| Q6D | Bélov návrat | Béla’s return |
| Q7A | Môžem pomôcť so scenárom? | Can I help with the script? |
| Q8A | Kam máte doručiť balík? | Where’s the parcel going? |
| E05 | Suchý pohár pre školu | A dry jar for the school |
| E07 | Ochrana mladej lipy | Protecting the young lime |
| E10 | Zapíšete lipu aj múrik? | Record the lime and the wall? |
| E11 | Heslo „Lastovička sa vracia“ | Password: ‘The swallow comes back’ |
| Q9A | Janin vlastný návrh | Jana’s own design |
| Q9D | Čo bolo s vašou schémou? | What became of your schematic? |
| Q9E | Čo robíte s notebookmi? | What are the laptops for? |
| Q9F | Jana, čo je s vašou schémou? | Jana, how’s your schematic? |
| Q10A | Zvonček, ktorý nezvoní | The bell that won’t ring |
| Q11A | Zvonček na bicykli | The bell on the bike |

## 9. UI

- Sentence case; short buttons; the player is *you*, instructions in the imperative (*Hold Space to show
  every clickable spot.*). Describe the controls as built (`docs/DECISIONS.md`: Space is held).
- Key names: *Space, Esc, Enter, Tab, Shift+Enter, Backspace*; mouse: *left-click, right-click,
  double-click*; touch: *tap, press and hold*, the *Eye* button.
- UI may use game words (*Inventory, puzzle, quest, save*); in-world text may not (§ 16).
- `glossary_en.json` → `ui` fixes about 230 labels by key; sentences are translated with these terms.

| Slovak | English |
|---|---|
| Inventár | Inventory (UI only) |
| Denník | Journal |
| Nápoveda | Hints / hint |
| Oko (touch button) | Eye |
| Obťažnosť: Ľahká / Štandardná / Ťažká | Difficulty: Easy / Standard / Hard |
| Smer / Postup / Riešenie (Easy) | Direction / Steps / Solution |
| Postrčenie / Kde hľadať (Standard, Hard) | Nudge / Where to look |
| Ciele / Zistenia / Ľudia / Mapa času / Album | Goals / Findings / People / Time map / Album |
| Pozorovania / Vodidlá / Prepisy rozhovorov / Záznamy postupu | Observations / Clues / Conversation transcripts / Progress log |
| hlavná úloha / vedľajšia úloha | main quest / side quest (UI only; in-world text never says ‘quest’) |
| Témy; už prebraté | Topics; already discussed |
| ľavý klik / pravý klik / dvojklik | left-click / right-click / double-click |
| prezrieť (objekt) | look at |
| ťuknúť; podržať prst | tap; press and hold |
| Space (podržať) | hold Space |
| miesta na kliknutie | clickable spots |
| objekt | object |
| značky | markers |
| rýchly presun | fast travel |
| zastávka (hub) | stop |
| oblasť | area |
| pozícia (uloženia) | slot |
| automatické uloženie | autosave |
| kontrolný bod | checkpoint |
| rozohraná hra | the game in progress |
| voľné hranie | free play |
| úvodné rady | starting tips |
| Legenda (mapa) | Key |
| titulky | subtitles |
| hovoriaci | speaker |

## 10. Protected facts and verbatim lines

### 10.1 Codes, painted texts, rules

| fact | Slovak | English | where |
|---|---|---|---|
| annex number on the photo, Viera’s shelf mark | K-17 | K-17 | B14, B15, item.CALPHOTO, item.OVERLAY.name |
| registration number of Mira’s box / collection | Z-17 | Z-17 | I16, C03, HANDOVER, CHAIN, CATALOG, F01, F03 |
| Dezider’s garage | číslo 17 | number 17 | entry.S29.001 |
| help-line hours on the notice | 9–17 (od deviatej do piatej) | 9–17 (speech: ‘nine till five’) | item.FLYER, Q2C |
| the four meanings on the plate | PÔVOD, HLAS, SÚHLAS, NÁVRAT | ORIGIN, VOICE, CONSENT, RETURN | P04 |
| Mira’s rule (plate) | Rôzne údaje neznamenajú neplatné údaje. | Different data are not invalid data. | look.S39.plate, action.I13.001; F05 calls the panel rule its opposite |
| Mira’s rule (spoken) | Čo sa nezhoduje, necháme vedľa seba. | What doesn’t match, we keep side by side. | CS04, F16 |
| the faulty rule | ROZDIEL = ZAHODIŤ | DIFFERENCE = DISCARD | item.FILTER_PHOTO, F05, look.S47.filter |
| warning sign in the workshop | NEPREPISOVAŤ ORIGINÁL | DO NOT OVERWRITE THE ORIGINAL | look.S10.ambient 2, entry.S10.001 (Adam: ‘I’m more used to DO NOT OPEN.’) |
| switch positions | ZÁPIS, MONITOR | WRITE, MONITOR | F06–F10, J05, look.S50.switch |
| restore procedure | ZACHOVAŤ VÝNIMKY | KEEP EXCEPTIONS | item.PATCH |
| the password | Lastovička sa vracia. | The swallow comes back. | E02, E11, D07, M11C hints |
| play title / first line | Žiaden strach, miláčik! | Never fear, darling! | Q7, look.S40.script, topic.LEA95.after, epilogue 7 |
| Emil’s song | Štyri zastávky | Four Stops (in quotes: ‘Four Stops’) | Q4, epilogue 4 |
| Tamara’s workshop | Druhý život / DRUHÝ ŽIVOT | Second Life / SECOND LIFE | Q8, look.S45.bench, S43 |
| sign on the thermos | NEDOLIEVAŤ POLIEVKU | DO NOT TOP UP WITH SOUP | look.S03.ambient 2, topic.ELA.ambient 2 |
| rhythm drawing | TRI VLNY, DVA ÚDERY, ŠESŤ DIELIKOV | THREE WAVES, TWO BEATS, SIX NOTCHES | look.S69.rhythm, B19, puzzle.P03.clue |
| P03 solution | 3–2–6 | 3–2–6 |  |
| P02 solution | 180° | 180° |  |
| P05 cell | rad 2, stĺpec 3; druhý rad zhora, tretí kameň zľava; mriežka 3 × 4 | row 2, column 3; second row from the top, third stone from the left; 3 × 4 grid |  |
| notice headline | SUSEDSKÁ POMOC 9–17 | NEIGHBOURLY HELP 9–17 | item.FLYER |
| Zuzana’s slip | LÍSTOK. PROSÍM JEDEN KÚSOK KOŽE NA ZVONČEK. ZUZANA, 1. TRIEDA. | SLIP. PLEASE ONE PIECE OF LEATHER FOR THE BELL. ZUZANA, FIRST YEAR. | item.ZUZA_SLIP, Q10A, Q10B (the child’s grammar stays) |
| Očko’s folder | Nepotrebné, ale milé | Not needed, but nice | ROBOT lines |
| thank-you card | ĎAKUJEM | THANK YOU | epilogue 8, look.S19.ambient 2 |
| device: chronometer recognises Adam | Nositeľ rozpoznaný. Jeho pamäť je chránená. | Wearer recognised. Wearer’s memory protected. | action.G07.002 |
| time windows | 6. júna 1962; 7. decembra 1982; 15. júna 1995; 29. októbra 2020; 6. februára 2035 (shown) | 6 June 1962; 7 December 1982; 15 June 1995; 29 October 2020; 6 February 2035 | era.*.date; game.json keeps 2035-06-06, the shown date is February (winter) |
| ages and spans | Adam 35 (1985), 10 on the tape; Mira 22/55/80; Tóno 12/25/50; Oto 46/66; Jana 12/25/50/65; jar 38 rokov; Tóno’s wait 13 rokov; 58 / 73 rokov; meškám o dvadsaťpäť rokov | identical values: ‘thirty-eight years’ in speech, ‘38 years’ in goals and hints; ‘a quarter of a century’ | GLOSSARY.md § 6.3 |

### 10.2 How clues are written

- A line that carries a clue states it plainly, as in Slovak; the joke goes before or after it, never instead.
- Values never change for a pun or for natural English: *3–2–6*, *180°*, *row 2, column 3*, *K-17*, *Z-17*,
  *9–17*, *38 years*, *13 years*, the dates and ages of GLOSSARY.md § 6.3.
- Port names, switch positions and painted texts are in capitals exactly as above; device texts quote them:
  *ORIGIN: confirmed.*, *WRITE off, MONITOR on.*, *MONITOR mode confirmed.*

### 10.3 The story facts that English must not blur

GLOSSARY.md § 6.5 holds word for word. Pay attention to: Adam never enters Mira’s house in 2020; nobody breaks quarantine, forges or
steals; the handover is recorded after it happened (*we only write down the truth*); the cassette is read,
never re-recorded; Tóno chose his job (*I chose it myself*); the cable cars work normally; Viktor is
responsible, not a villain; Lea’s death is not caused by the erasing.

### 10.4 Verbatim lines (fixed English)

| key | Slovak | English |
|---|---|---|
| action.F11.003 | Viktor? To som ja. Len ti volám. Nemusíš nič opravovať. Keď budeš mať čas, ozvi sa. | Viktor? It’s me. I’m just ringing. You don’t have to fix anything. When you have time, call me. |
| action.F11.004 | V upravenej verzii zostalo len „ozvi sa“. | must quote exactly ‘call me’ (the last two words of F11.003) |
| action.D07.006 | Nečakal som. Žil som. Len som si pamätal miesto. | I didn’t wait. I lived. I just remembered the place. |
| cutscene.CS07.04.001 | Čaj ti spravím, keď bude možné prísť normálne. | I’ll make you a cup of tea when you can come round properly. |
| cutscene.CS07.04.002 | Tentoraz počkám. | This time I’ll wait. |
| journal.clue.P04 | Pôvod 1962, Hlas 1995, Súhlas 2020, Návrat 2035 | Origin 1962, Voice 1995, Consent 2020, Return 2035 |
| game.title | Posledný zvonec | The Last Bell |
| puzzle.P01.left/right.* | kruh, trojuholník, štvorec | circle, triangle, square |
| puzzle.P04.left.* | Pôvod, Hlas, Súhlas, Návrat | Origin, Voice, Consent, Return |
| puzzle.P04.right.* | 2020, 1962, 2035, 1995 | unchanged digits |

## 11. Text in the art ("variablised" art)

The paintings follow strict fiction rules: almost nothing is legible (papers are scribbles, devices show ticks,
exhibitions pictograms). The table lists every lettering the art prompts allow, with the decision.

- **Variablise** = make an English variant (or an engine-drawn text layer) of a picture whose lettering the
  story quotes. Recommended only for the rows marked so; everything else stays as painted.
- **What the English text says:** a story text (a clue, a sign Adam reads out, a switch) is always quoted in
  its English rendering in capitals, whether or not the art was variablised. The English text works as the
  subtitle of the painted Slovak. Real signage that stays Slovak (POTRAVINY, POŠTA, the school name board,
  SPOLOČNOU PRÁCOU, VITAJTE) is described or glossed in English when a line mentions it (*the shop sign*,
  *a banner: SPOLOČNOU PRÁCOU – ‘through common work’*).

| where | painted text | English | decision |
|---|---|---|---|
| S45 bench plaque, S43 plaque on Tamara’s table | DRUHÝ ŽIVOT | SECOND LIFE | variablise (story text quotes it) |
| S50 switch | ZÁPIS / MONITOR | WRITE / MONITOR | variablise (story-critical) |
| item icon FLYER | SUSEDSKÁ POMOC, 9–17 | NEIGHBOURLY HELP, 9–17 | variablise (the look quotes it) |
| item icon ORDER | čaj / zemiaky / ovsené vločky | tea / potatoes / porridge oats | variablise if cheap; otherwise keep (handwriting) |
| S12, S52, S58 school name board | ZÁKLADNÁ ŠKOLA SOKOLÍKOVA / ZŠ SOKOLÍKOVA | — | keep: real signage |
| S04 shop sign | POTRAVINY | — | keep: real Slovak signage; texts say ‘the shop’ |
| S32 / S33 post office sign | POŠTA | — | keep |
| S31 station board | IVANKA PRI DUNAJI | — | keep |
| S05 doormat | VITAJTE | ‘welcome’ | keep; a look may gloss it |
| S65 banner (1982) | SPOLOČNOU PRÁCOU | ‘through common work’ | keep: period slogan; the look gives the meaning |
| S47, S50, S67, S68 | CHOPOK, ROTUNDA CHOPOK | — | keep: real place names |
| S42 gable | Grand Jasná | — | keep |
| S43 wall | RECEPTION | — | already English |
| S29 garage, S33 calendar, CHRONO counter, CATALOG / HANDOVER Z-17 | 17, June 1962, 2020, Z-17 | — | language-neutral |
| text-only signs (art shows scribbles or pictograms) | NEPREPISOVAŤ ORIGINÁL, NEDOLIEVAŤ POLIEVKU, ROZDIEL = ZAHODIŤ, TRI VLNY…, PÔVOD… | § 10 renderings | nothing to variablise: English text quotes the English rendering |

## 12. Era flavour

Every era sounds like itself without caricature (STYLE_GUIDE.md § 4). Adam always speaks his own 2020 English.
Socialist-era terms are **kept and made clear by the English noun** (*the Pioneers*, *a work brigade*,
*Comrade Teacher*); an abbreviation (JRD, ROH, MNV, ČSSR) is used only where it is painted or quoted, with the
English noun beside it the first time. No footnotes, no history lessons in a line. Brand names are avoided
(owner’s licensing rules).

**1962 Ivanka pri Dunaji**

| Slovak | English | note |
|---|---|---|
| pán, pani; mladý pán | Mr, Mrs; ‘young man’ |  |
| prosím pekne; nech sa páči; ráčte (Alojz) | if you please; here you are; would you care to | Alojz’s charming officialese |
| telegram; známky; pečiatka; prepážka | telegram; stamps; stamp; counter |  |
| rádio (večerná zábava) | the wireless (older villagers), the radio |  |
| náves; kultúrna sála; ochotnícke divadlo; kulisa | village green; village hall; amateur dramatics; flat |  |
| hospodársky dvor; sklad; výdajný lístok | farm yard; store; requisition slip |  |
| JRD (jednotné roľnícke družstvo) | the collective farm (‘JRD’ only if painted or quoted) | keep the idea, explain by the English noun |
| MNV (miestny národný výbor) | the local council |  |
| škôlka (hra); prvá trieda; vysvedčenie; prázdniny; mamka | hopscotch; the first year; school report; the holidays; Mum | Zuzana; never ‘comrade’ |
| avoid | OK, stress, system, info, mobile, display, any modern word in an NPC’s mouth |  |

**1982 Dúbravka**

| Slovak | English | note |
|---|---|---|
| súdruh učiteľ; súdružka riaditeľka (pupils) | Comrade Teacher; Comrade Headmistress | never as a joke |
| pionieri; pionierska schôdzka; pionierska šatka | the Pioneers; Pioneer meeting; Pioneer neckerchief |  |
| brigáda | work brigade (Saturday work brigade) |  |
| schválený vzor; výstavka; výdajka; formulár | the approved model; the exhibition; requisition slip; form |  |
| vratné fľaše / poháre; záloha | returnable bottles / jars; deposit |  |
| ROH | the trade union (ROH) | only if it appears |
| národný podnik (n. p.) | national enterprise | only if it appears |
| Jednota | the Jednota co-op shop, then ‘Jednota’ | only if it appears |
| Tuzex; bony | Tuzex, the hard-currency shop; Tuzex vouchers | explain once, then the name |
| ČSSR; štátny znak | Czechoslovakia; state emblem |  |
| MS vo futbale 1982; večerná rozprávka | the 1982 World Cup; the bedtime story on telly |  |
| avoid | slogans as punchlines, secret police, ‘nothing in the shops’ jokes, modern words |  |

**1995 Bratislava**

| Slovak | English | note |
|---|---|---|
| koruny (Sk) | crowns | never ‘korunas’ |
| kiosk; noviny; telefónna karta; pevná linka | kiosk; papers; phonecard; landline |  |
| kazeta; walkman; magnetofón | cassette, tape; personal stereo (never the brand Walkman); tape recorder |  |
| trh na Miletičovej; stánky | the Miletičova market; stalls |  |
| električka; podchod; paneláky | tram; underpass; the blocks |  |
| fakt, kamoš, frajer (sparingly) | really, mate, show-off (sparingly) |  |
| avoid | smartphones, internet talk, today’s slang, forced 90s brands |  |

**2020 Chorvátsky Grob, Čierna Voda, Dúbravka**

| Slovak | English | note |
|---|---|---|
| rúško; odstup; dezinfekcia | mask; distance (two metres); hand sanitiser |  |
| karanténa; dištančné vyučovanie | quarantine; remote learning |  |
| výdajné miesto; dobrovoľníci; oznam; výveska | pick-up point; volunteers; notice; notice board |  |
| kuriér; cez okno; na diaľku; QR kód; aplikácia | courier; through the window; remotely; QR code; app |  |
| avoid | illness jokes, ‘corona’ puns, office English (‘touch base’, ‘going forward’) |  |

**2035 Jasná**

| Slovak | English | note |
|---|---|---|
| kurátorka; výstava; pavilón | curator; exhibition; pavilion |  |
| čítačka; terminál; servisný režim; servisný kanál; servisná pamäť | reader; terminal; service mode; service channel; service memory |  |
| normalizátor; zásobník; spätný zápis; diagnostika | normaliser; buffer; write-back; diagnostics |  |
| lístok; skipas; lanovka; kabínka; Funitel | ticket; ski pass; cable car; gondola cabin; the Funitel |  |
| návštevnícka kniha (papierová) | the paper visitors’ book |  |
| avoid | cyberpunk, invented jargon, claims that the lifts are unsafe |  |

**Repair and technical words (all eras)**

| Slovak | English |
|---|---|
| kondenzátor | capacitor |
| poistka; prepálená | fuse; blown |
| zdroj | power supply |
| kryt | cover |
| napätie | voltage |
| elektroodpad | e-waste |
| stopa (zvuková) | track |
| šum | hiss |
| vývody | leads |
| spájkovať | solder |
| meradlo | multimeter |
| skrutkovač; klieštiky | screwdriver; pliers |
| remienok | drive belt |
| motor sa točí naprázdno | the motor spins freely |
| piest | piston |
| srdce zvončeka; pútko | clapper; loop |
| vrchnák zvončeka | bell cap |

## 13. Humour in English

1. **The Polda tone is the same**: playful, a little absurd, character comedy and situational jokes that make
   sense; in English it comes out as dry British understatement. Warm, never mean; no jokes about illness,
   death, age, bodies, nations, the regime or the game itself.
2. **Translate the joke, not the words.** If the literal English is not funny, rebuild the joke from the same
   situation and the same character, in the same place in the exchange and at the same length. If no English
   joke fits, write the line plainly. A flat line is better than a calque.
3. **Puns and wordplay that need Slovak** get an English equivalent or a different joke in the same spirit
   (table below). Never a footnote, never *in Slovak this means*. The only exception is the one-time gloss of
   a kept Slovak name by someone who would explain it anyway (Mira for ZVON, Alena for Svetlo).
4. **No English-only culture.** No British TV, Monty Python, royals, pounds or Brexit: the people are Slovaks
   in Slovakia. British idioms are fine when the speaker and era fit (*by the book*, *drop the ball*, *a new
   lease of life*). No modern slang in 1962 or 1982 mouths, and no swearing.
5. **Running gags** keep one English phrasing (table below) and change only slightly each time they return.
6. **The old pattern stays banned**: no ironic one-liner after every line. Serious beats stay plain: Lea’s
   message, Tóno’s recognition, Viktor, the last scene with Mira, covid itself.
7. **Exclamation marks are rare**: Rudo gets them, children sometimes, Adam almost never.

### 13.1 Puns and decided adaptations

| where | Slovak | English decision |
|---|---|---|
| title, ZVON, zvonček | Posledný zvonec / ZVON (= bell) / triedny zvonček | ‘The Last Bell’; ZVON stays; Mira glosses it once in G05.005 (‘Like a bell. Zvon.’); every school or bike bell is ‘bell’, so the motif survives |
| Q1 title | Bodka bez bodky (Bodka = dot) | ‘Bodka Drops the Ball’ |
| S22 bookshop | Pod druhou rukou (second-hand) | ‘Second Hand’: second-hand books and the clock’s second hand |
| Alena (B14.x04) | Fotí sa svetlom, preto sme Svetlo. | keep the name and gloss it: ‘Photos are made with light. Svetlo means light. Hence the name.’ |
| Vera / Adam (I10.003–.004) | Rydlo, ktorým sa nemá ryť (rydlo from ryť) | ‘A scratching tool that mustn’t scratch. I’ll remember that.’ – ‘That’s why it’s blunt. It remembers for you.’ |
| Zuzana (extra 4) | manžeta on a pump vs. on a shirt | works in English with ‘cuff’; ‘So it’s a belt for water.’ |
| Zuzana (extra 1) | škôlka = hopscotch and nursery school | pun lost; keep her pride: ‘Hopscotch, yes. But I’m not in the infants any more. I’m in the first year.’ |
| Zuzana (Q10A) | Chýba mu srdce (srdce = heart and clapper) | ‘It’s missing its clapper.’ – ‘No it isn’t. It’s in my hanky.’ (no heart pun) |
| M05 title | Hlasy sa nerušia (nerušiť = do not disturb) | ‘No Interference’ |
| Soňa | družstvo, nie skupina | ‘a team, not just a group’ |
| Štefan | Lístok, podpis, materiál. | ‘Slip, signature, supplies. In that order.’ |
| Ela’s flask | NEDOLIEVAŤ POLIEVKU | ‘DO NOT TOP UP WITH SOUP’ |
| Q10 / Q11 / epilogues | Prvý / Druhý posledný zvonec; ‘Posledný zvonec! A v septembri zase prvý.’ | ‘The First Last Bell’ / ‘Another Last Bell’; ‘Last bell! And in September, the first one again.’ |
| Q6 / password | Béla sa vracia / Lastovička sa vracia | ‘Béla Comes Back’ / ‘The swallow comes back.’ |
| Juro (B07.x02) | Juro Kazeta, to som ja. | ‘Juro Cassette, that’s me.’ |
| Mira (G04.x03) | Som inžinierka, nie veštica. | ‘I’m an engineer, not a fortune teller.’ (works as is) |
| Boris | poznámka pod čiarou | ‘Footnote: …’ |
| Zuzana 1995 | Niektoré veci sú krajšie bez návodu. | ‘Some things are nicer without the instructions.’ |
| Lea’s message (F11) | ozvi sa | ‘call me’ – serious beat, no joke |

### 13.2 Running gags (fixed English phrasing)

| speaker | fixed English phrasing |
|---|---|
| ADAM | I only wanted to change a fuse. |
| MIRA20 | Gran’s rules: carry it by both handles; don’t come in. |
| MIRA95 | First … then … |
| MIRA60 | If it doesn’t fit, we write it alongside. |
| TONO82 | Grandad says … |
| OTO | First we look. |
| JANA82 | It’s different from the model. |
| JANA95 / JANA20 / JANA35 | the exact word: ‘not a list – a register’ |
| ELA | lists of lists |
| DANA | I don’t sell that. (patience, luck, time) |
| ROMAN | the house that used to be yellow |
| JOZEF | in big letters; ‘young man’ |
| SONA | a team, not just a group |
| ZITA | The news is free. |
| ZUZANA, ZUZANA95 | counts everything; ‘only up to four – grown-ups fall over after that’ |
| KUBO | the ball escapes ‘only higher’ |
| EMIL | the trams keep my tempo |
| PALI | Not worth it.; ‘It was working yesterday.’ |
| VIERA | Books sell, inserts go missing. |
| KAROL | the reading-room rules |
| ALENA | People look best when they think I’ve stopped. |
| FERO | Original. Just from a different maker. |
| MILADA | like with a coat; ‘it’s always been like that’ |
| JURO | people as tracks on a mixtape |
| JURAJ | never has white chalk |
| DEZI | Exact doesn’t mean the same. |
| BOZO | Where are you headed? |
| BERTA | young Hrušková’s lit up again |
| ALOJZ | Béla isn’t a service pigeon. |
| LIDA | six actors, four coats |
| RUDO | Never fear, darling! |
| STEFAN | Slip, signature, supplies. |
| VERA60 | Oto keeps changing the dimensions. |
| DOBRO | the approved model |
| RUZENA | What you see is what we’ve got. |
| MARTA82 | without any fuss |
| SIMON | thinks in decades |
| NINA | lists, like her mother |
| TAMARA | The system works. |
| BORIS | Footnote: … |
| SARA | the pen that has never fallen |
| ROBOT | Confidence: sixty per cent.; folder ‘Not needed, but nice’ |
| IVAN | I’ll tell you, not the weather. |
| TURISTA | photographs the fog |

## 14. The knowledge rule and the Zuzana rules

**Adam never names what he has not learned** (AUDIT.md, owner 2026-10-06) holds word for word in English:

- English names exactly the entities the Slovak line names, nothing more. Do not "help" a line with a name,
  role or descriptor it does not have (*tá pani z ateliéru* stays *the lady from the studio*, not *Alena*;
  *rádioamatér* stays *the radio ham*).
- Hover, speaker and exit labels count as introductions, so a line that names someone uses the form the
  label introduced (*Juro*, *Mr Dobrovič*, *Očko*).
- Vague Slovak stays vague in English (*niekto*, *tam*, *tá krabica*); pronouns must not resolve to someone
  who has not been introduced.
- Glosses are spoken by someone who knows: Adam may gloss Slovak signs (he is Slovak), but never something
  he has not learned.

**Zuzana** (ZUZANA.md § 6.1) holds word for word in English:

- She appears only in June 1962 (7, S37 and her traces in S32 / S38) and on 15 June 1995 (40, S69); never in
  1982, 2020 or 2035.
- No surname, ever. Nothing about her life: no job, family, partner, children, illness, home or fate. In 1962
  she has *Mum*; in 1995 nobody of her family is mentioned. Kubo is *a boy from the next entrance*, never hers.
- **No foreshadowing.** Banned for her and about her (also in looks and hints): *I won’t see it*, *I won’t be
  here*, *while I’m still here / around*, *one day I’ll be gone*, *when I’m gone*, *to remember me by*, *as a
  keepsake*, *in memory of*, *the last time I*, *never again*, *when I grow old*. Lines about time stay
  inside the two afternoons (*twenty-four more days*, *fifteen more days*).
- *Zuzka* only from Ivanka adults in 1962; in 1995 nobody says *Zuzka*; *Auntie Zuzana* only from Kubo.
- She never learns that Adam travels in time; in 1995 she chooses not to ask: *Some things are nicer without
  the instructions.* The *dohoda* is *a deal*: *That’s a deal.* / *Deal.*

## 15. Text types in English

| type | English form | example |
|---|---|---|
| spoken lines | one or two short sentences, ≤ 110 characters (hard 160), each follows from the one before | *Diagnosis: blown fuse. Finally a fault I know without a manual.* |
| looks, item looks | Adam, first person, present tense, concrete; state, cause, what is missing | *The belt has perished. I can’t get the cassette out safely without fixing it.* |
| first-entry lines | one observation of what is visible, at most one dry remark | |
| locked exits | Adam’s in-world reason, one line | *Without reporting to the caretaker, they won’t let me into the prep room.* |
| names (rooms, hotspots, items, exits) | short noun phrase, sentence case, ≤ 32 (hard 50) | *Fuse drawer* |
| action labels (item use, click) | verb first, imperative form without *to*, ≤ 45 | *Insert the spare fuse*, *Fit the cuff to the pump* |
| story topic labels | the topic or Adam’s short question, ≤ 28 | *Gran’s shopping*, *Why ZVON?* |
| objectives, journal, quest goals | imperative to *you*, one sentence, who / where / with what, ≤ 100 | *Show the perished drive belt to Pali in Karlova Ves.* |
| journal records (*Dokončené: …* style) | past or present perfect, Adam’s notebook voice | *The connector is in the adaptor. Insulation still missing.* |
| item purposes (not shown) | infinitive phrase with a full stop | *To return to Lenka and Bodka.* |
| hints | level 1 direction; level 2 people and items in order; level 3 the chain with arrows, glossary names, no ids | *Tool bag in the garage → Ela: topic ‘Gran’s shopping’ → …* |
| step hints (`ui.hint_step`, `hint.nudge`, `hint.where`) | as level 2 / 3; quote topic labels exactly (§ 8.3) | *At the pick-up point by Lúčny koník, talk to Ela about ‘Gran’s shopping’.* |
| puzzle texts | title: noun phrase; clue exactly as informative; wrong line: why and where the clue is | |
| device (`SYSTEM`) | terse, passive participles, no contractions, capitals for ports and switches | *Reference 1995 restored.*, *Ticket valid.* |
| narrator, epilogue | calm present tense captions; the epilogue line closes the side story | *Bodka is lying by the red ball.* |
| UI | § 9 | |

## 16. Do not write

| do not write | write |
|---|---|
| time machine, time-travel device | ZVON / the chronometer |
| linden | lime tree |
| janitor | caretaker |
| cabinet (fyzikálny kabinet) | physics prep room |
| retroactive write, retro-write | write-back |
| synchronisation chamber | chronochamber |
| time address (goals, hints, journal) | time window / ‘opens the way to 2035’ |
| Grandma, Granny, Nan, Mirka | Gran (Adam, 2020) / Mira / Mrs Hrušková |
| Grandpa, Granddad | Grandad (Tóno 12 only) |
| Mom, mommy | Mum |
| Mr., Mrs., Ms., Dr. | Mr, Mrs, Ms, Dr (no full stop) |
| Pavol’s repair shop, Juraj (for Juro) | Pali’s repair shop, Juro |
| Dezi (outside friends’ speech) | Dezider |
| by the LEAL, the LEAL courtyard, Sokolíkova courtyard | Pri LEALe |
| Tóno 12, Jana 82 | twelve-year-old Tóno, Jana in 1982 |
| proof Consent / Origin | proof of consent / of origin; the Consent port |
| loop (the coil), transparent map | measuring coil, transparent overlay K-17 |
| fonds, fund | collection |
| Second Hand Life, Second Wind | Second Life (Tamara’s workshop) |
| Walkman, Tannoy, Thermos, Perspex, Kilner (brands) | personal stereo, PA, flask, plastic screen, preserving jar |
| korunas, Slovak crowns | crowns |
| subway (underpass) | underpass |
| color, center, organize, realize, analyze, program (except software), catalog, traveled, gray, aluminum, tire, curb, license (noun), practice (verb), defense, mom | colour, centre, organise, realise, analyse, programme, catalogue, travelled, grey, aluminium, tyre, kerb, licence, practise, defence, mum |
| gotten, fall (autumn), vacation, sidewalk, apartment, elevator, flashlight, trash / garbage, mail, zip code, soccer, math, cookie, candy, line (queue), parking lot, cell phone, faucet, eraser | got, autumn, holidays, pavement, flat, lift, torch, rubbish / bin, post, postcode, football, maths, biscuit, sweets, queue, car park, mobile, tap, rubber (only where unambiguous) |
| awesome, cool (adults before 1995), OK (1962, 1982 NPCs), guys, y’all | great, good, fine, everyone |

**Design jargon never in in-world text** (UI is exempt): *in the game, in-game, player, quest, NPC, hotspot,
pixel, zoom, click, inventory, puzzle, level, unlock, timeline, original line, butterfly effect, finale,
combine, in the journal, save game, cutscene, fictional, off-screen, game*. A character may use one only where a
real person would (Lída may call the costume count a puzzle).

## 17. Checks

- **LanguageTool en-GB**, local: `pip install --user language_tool_python` (downloads LanguageTool 6.8, ~260
  MB, once; needs Java 21), `language_tool_python.LanguageTool('en-GB')`; ignore spelling hits on the words in
  `spellcheck_allow` and on Slovak names; every other hit is read and either fixed or noted.
- **Consistency:** item, room, hotspot, speaker and topic-label texts exactly as in `glossary_en.json`; an item
  name inside a look, goal or hint uses the same noun; exits equal to a room name equal its English name.
- **Facts:** every `protected` value and every `verbatim` line present in its keys; placeholders identical to
  Slovak; lengths within `variant.limits`.
- **Words:** no `deprecated_en`, no `jargon_en` in in-world text, no `zuzana_banned_en` in ZUZANA / ZUZANA95 lines
  or about her; American spellings flagged by LanguageTool (`MORFOLOGIK_RULE_EN_GB`) are fixed, not ignored.
