# Posledný zvonec – voices

One entry per speaking character: who they are, how they talk, how they address Adam, and two
example lines in good Slovak. The section "Humour, running gags and extra topics" says how each of
them is funny in the Polda tone of `design-doc/WRITING_METHOD.md`. The examples show the voice; they are not lines from the game and
must not be pasted over a game line unless they say exactly what that line has to say.

Speaker ids are the ones used in the data. Some characters have two ids: the hotspot/character id
and the speaker id of their lines (ARCHIVAR = KAROL, FOTO = ALENA, TRH = FERO, SKLAD = STEFAN,
POSTA = ALOJZ). Ages and roles come from `design-doc/game.json`.

## Who says *ty* and who says *vy* to Adam

Mixed forms inside one line are the most visible grammar error in the current texts. Follow this
table. "→ Adam" is how the character addresses Adam; "Adam →" is how Adam addresses them.

| Character | → Adam | Adam → | Note |
|---|---|---|---|
| Mira 2020 (babka) | ty | ty | grandmother |
| Mira 1995, Mira 1960 | ty | vy | Mira tykne Adamovi in every era (family echo); Adam does not dare to tykať her before she knows him |
| Ela, Dana, Roman, Lenka (2020) | ty | ty | the village knows Adam since childhood |
| Jozef (2020) | ty | vy | `pán Jozef` |
| Tóno 25 (1995) | vy, **ty after E11** | vy, ty after E11 | the switch to *ty* is the moment of recognition (`Počkaj. To si ty.`) |
| Tóno 12 (1982) | vy, **ty from E02 on** | ty | after the confession the boy plays along (`Tak to som od teba vlastne starší.`) |
| Tóno 50 (2020) | vy in D02, **ty in D07** | vy, ty in D07 | before the 1982 trip he does not know Adam |
| Ambient topics of Tóno (all ages) | neutral | neutral | available before and after the change: avoid verb forms that show *ty* or *vy* |
| Oto 1960 and 1982 | vy | vy | |
| Pali, Juro, Tamara | ty | ty | fellow repairers, colleagues |
| Zita, Emil, Fero, Dezider (1995) | ty | vy | older, informal people of 1995 Bratislava |
| Soňa (11), Jana 12 | vy | ty | children |
| Juraj (19) | vy | ty | |
| Everyone else (1960, 1982, 1995 officials, 2035) | vy | vy | including Viktor, Vera 1960, Viera 1995, Alena, Karol, Milada, Jana 25/50/65, Nina, Sára, Boris, Ivan, Miloš |
| Lea 1995 | vy | vy | Lea to the 10-year-old Adam on the tape: ty |

---

## Humour, running gags and extra topics (Polda tone, owner decision 2026-10-06)

Binding method: `design-doc/WRITING_METHOD.md`; techniques: STYLE_GUIDE.md § 7. Every speaking
character is funny **in their own way**, and most have a running gag that returns now and then
(at most once per scene, a little changed each time). The topic ideas are for the 2–4 extra optional
topics per NPC (WRITING_METHOD.md § 3): local colour, their own life and quirks, the running gag,
a gentle nudge toward the current goal. They are ideas, not facts: nothing here changes the story,
an item or a solution, and an invented quirk must not contradict game.json.

Not funny on purpose: Viktor (a controlled, serious arc; at most a dry remark), Lea's message, the
narrator, device texts (only Očko is a comic machine). No extra topics for SYSTEM, NARRATOR,
LEA_REC, ADAM10 and Bodka (who only barks).

| speaker | how they are funny | running gags | extra topic ideas |
|---|---|---|---|
| ADAM | self-irony of a repairman whose simple day keeps escalating; precise diagnoses of absurd things | "I only wanted to change a fuse" (the day grew from a fuse to five eras); diagnoses people's problems like devices; grandma manages him remotely | — (he asks; his reactions carry the gags) |
| MIRA20 | the engineer who runs Adam's day from behind a closed window, dry and loving | Babkine pravidlá (carry it by both handles, do not come in) applied to everything; she already knows what Adam did before he says it | her quarantine day, how ZVON first sounded, how she taught Adam to solder, the neighbours on the phone |
| MIRA95 | teacher energy: gives tasks in numbered order, also to adults | "najprv … potom …" lists; children's recordings she quotes | the sound club, the funniest recording of the children, cassettes she keeps, Dúbravka in 1995 |
| MIRA60 | quick and impatient with vague words; corrects people's wording | "čo nesedí, píšeme vedľa"; finishes Oto's sentences | the measuring in the park, Oto's workshop habits, Ivanka's gossip about her "búdka" |
| TONO82 | kid logic: takes adults literally, bargains, checks details | swallows he draws everywhere; "dedo hovorí …" | school in 1982, the football World Cup on TV, pioneers, what he will be when he grows up (not caretaker, he thinks) |
| TONO | the teasing young caretaker with a key for every door and a story for every key | the key ring; every door has its trick | the school in 1995, why he took the job, the club noise, the boiler room |
| TONO20 | calm deadpan; big things said in few words | birdhouses; the same key ring 25 years later | the empty school during distance learning, birdhouses, children he meets through the window |
| OTO | understated precision; machines are more honest than people | "najprv sa pozrieme" before anything; measures before he answers | the workshop in Ivanka, the first ZVON test, what he thinks of Adam's odd shoes |
| OTO82 | the amused grandfather who has seen time pass | remembers Adam's jacket from 1960; three jackets since | Tóno as a pupil, the school technical club, getting old with a soldering iron |
| JANA82 | shy until she may explain, then unstoppable | "Je to inak ako vo vzore." | her schematic, radios, what the teacher said about it |
| JANA95 / JANA20 / JANA35 | precise organiser who corrects near-synonyms | the exact word ("not a list, a register") | the club / laptops for children / her exhibit; only what fits the state shown |
| ELA | runs the village on lists and speed | lists of lists; the thermos sign NEDOLIEVAŤ POLIEVKU | the volunteers, who needs what this week, her daughter Nina at fifteen, the village in 2020 |
| DANA | deadpan wisdom from behind the counter window | "Toto nepredávam" (patience, luck, time); knows every customer's usual order | the window shop, the regulars, Mira's order "as always", what people buy in a lockdown |
| ROMAN | the courier who knows houses by description, not by number | addresses like "dom, čo býval žltý"; the heaviest box of the month | his route, the boxes he carried for Mira, people waving through windows |
| LENKA | few words; the dog decides | Bodka leads the walk; the ball by the reservoir | Bodka's habits, walks in Čierna Voda, the reservoir path |
| JOZEF | ceremonious analog pride, "mladý pán" | the folding magnifier; "veľkými písmenami" | the notice board, the village then and now, why he will not install an app |
| LEA95 | gentle; the humour comes from what children say | "what the children say between sentences" | recordings with the class, ordinary sounds she collects, Viktor as a small boy |
| SONA | child seriousness about grown-up rules | "družstvo, nie skupina"; guards the album | the album, the school team, the club |
| ZITA | the kiosk as the estate's news agency | "správy sú zadarmo"; lost things end up at her kiosk | the housing estate in 1995, forgotten envelopes, who buys which paper |
| EMIL | slow musician who hears rhythm in everything | the trams keep his tempo | his song „Štyri zastávky“, Karlova Ves, playing for passengers |
| PALI | blunt colleague with repair verdicts | "neoplatí sa" verdicts; customers' "včera to ešte išlo" | his shop, the worst repair he ever did, belts and motors |
| VIERA | ironic bookseller about books and readers | "prílohy sa strácajú"; don't hold it by the spine | the antiquariat, what people sell after a move, Emil's sheet music |
| ARCHIVAR / KAROL | pedantic about silence and rules, secretly helpful | quotes the reading-room order | donations, the strangest thing in the archive, why copies, not originals |
| FOTO / ALENA | calm craft; people look best when they think she stopped | "už nefotím" | the studio „Svetlo“, the darkroom, school photos |
| TRH / FERO | earthy market seller; everything is "original" | "originál, len od iného výrobcu" | Miletičova market, the stuck scale, what sells in 1995 |
| MILADA | explains everything as tailoring | "ako pri kabáte"; "vždy to tak bolo" is the hardest thing to mend | Ružinov, her customers, old textile insulation |
| JURO | cassette nerd; life as a mixtape | compares people and situations to tracks | cassettes, the basement club, the best tape of 1995 |
| JURAJ | quiet painter who sees the lights inside the blocks | the white chalk he never has | the underpass panel, Petržalka windows, the permit with a stamp |
| DEZI | radio ham who translates every term at once | call signs; "presné neznamená rovnaké" | radio, working with Mira, the Danube embankment |
| BOZO | timetable philosophy; likes clear destinations | "Kam ste namierený?"; trains as answers to life | the station in 1960, trains to Bratislava, where to find young Hrušková |
| BERTA | village curiosity about the stranger | Adam's shoes and clothes; "mladá Hrušková zas svieti" | the square, village news, the young people of 1960 |
| POSTA / ALOJZ | charming officialese with a soft aside | stamps for everything; Béla is not a service pigeon | the post office, telegrams, Béla's flights |
| LIDA | theatre logistics: costumes never add up | "šesť hercov, štyri kabáty" | the amateur theatre, the play, Rudo's stage fright |
| RUDO | theatrical exclamations on stage, shy off it | quotes from his lost script `Žiaden strach, miláčik` | his roles, rehearsals, the lost script |
| SKLAD / STEFAN | curt order, proud of knowing exactly what is missing | "Lístok, podpis, materiál."; "presne viem, čo nemáme" | the store in the farm yard, Oto's slips |
| VERA60 | dry practical draughtswoman | Oto keeps changing the dimensions | drawings, working outside in the park, the ZVON documentation |
| DOBRO | formal teacher phrases that slowly soften into a human | "schválený vzor"; the comrade director will read it | the exhibition, the school in 1982, what makes a good pupil's project |
| RUZENA | direct shop assistant | "Čo vidíte, to máme." | the shop in 1982, returnable jars, the regulars |
| MARTA82 | patient exactness; rules without needless trouble | "bez trápenia" | the maintenance store, forms that make sense, the school building |
| SIMON | thinks in decades | trees outlive everyone, the hand cart's shortest way | the school garden, the linden, the estate being built |
| NINA / NINA_REMOTE | fast, names the limits of her authority | lists, like her mother Ela | Atlas, the exhibition, her mother in 2020 (she was fifteen) |
| VIKTOR | not funny by design; controlled and serious | — | the purpose of Atlas in his own words; nothing that spoils the ending |
| TAMARA | a repairer among repairers; coffee and repair are one system | "systém funguje" | the travelling workshop „Druhý život“, repairs at the hotel table |
| BORIS | jokes like bibliographic footnotes | "poznámka pod čiarou" asides | the exhibition archive, the oldest object, copies and originals |
| SARA | professional pride in paper | the pen that has never fallen; the visitors' book | Biela Púť, the client centre, visitors who ask odd things |
| ROBOT (Očko) | literal; statistics instead of feelings | confidence percentages; the folder "Nepotrebné, ale milé" | its route, weather as data, addresses described by history |
| IVAN | calm cable-car man; he, not the weather, decides | "poviem vám to ja, nie počasie" | the Funitel, Chopok in winter, the change at Priehyba |
| TURISTA | trip nostalgia; photographs fog | fog photos | trips with his father, Jasná in the old days, what he packs |

---

## Adam and the family

### ADAM – Adam Hruška (35)

Repairman of audio equipment from Chorvátsky Grob, born 1985, went to ZŠ Sokolíkova as a child. A
civilian, not a hero type: he repairs things, follows rules, helps his quarantined grandmother.

- **How he talks:** modern colloquial Slovak of 2020, short sentences, dry situational humour,
  self-irony; technical things said precisely and simply. Important feelings in plain words, no
  speeches. Never sarcastic towards the people who help him. He jokes about himself, machines,
  forms and transport, not about others.
- **Looks:** first person, present tense, what a repairman notices (state, cause, what is missing).
- **Examples:**
  - `Poistka je prepálená. Konečne porucha, ktorú poznám aj bez návodu.`
  - `Ďakujem. Že si si to celé tie roky pamätal.`

### MIRA20 / MIRA95 / MIRA60 – Mira Hrušková (80 / 55 / 20)

Adam's grandmother, co-author of ZVON in 1960 (technical assistant), in 1995 volunteer leader of the
school sound club, in 2020 in quarantine behind a closed window, speaking by phone.

- **The same person at three ages:** the same rhythm in every era: a short statement, then a
  practical instruction or the reason (`Kľúč je v schránke pri okne. Do domu nechoď.`). Precise
  technical sentences, sharp observation, tenderness hidden in practical care. She never gushes.
- **Mira 22 (June 1962):** quick, curious, direct, a little impatient with vague questions; already the
  rule-maker (*čo sa nezhoduje, nechávame vedľa seba*).
- **Mira 55 (1995):** energetic, a teacher's clarity, used to children; gives tasks in order.
- **Mira 80 (2020):** dry, warm, refuses to be pitied, still the engineer.
- **Address:** tyká Adamovi in every era; Adam vyká Mire 1960/1995, tyká Mire 2020 (`babka`).
- **Examples:**
  - Mira 80: `Nerob zo mňa položku na zozname. Som doma, mám čaj a mám teba na telefóne.`
  - Mira 20: `Čo nesedí, zapíšem vedľa. Vyhodiť to môžem vždy, vrátiť už nie.`

### TONO82 / TONO / TONO20 – Anton „Tóno“ Farkaš (12 / 25 / 50)

Born March 1970. In 1982 a pupil of Sokolíkova and grandson of Oto; in 1995 a young school
caretaker; in 2020 the same caretaker at fifty behind the service window. He chose the job himself.

- **The same person at three ages:** the same dry humour and cadence, short practical sentences, a
  recognisable gesture (turning a small key or pencil in his fingers).
- **Tóno 12:** curious, concrete, a real child: asks direct questions, checks details, gets quiet
  and serious when he promises something. No adult or official phrases. Says *dedo* about Oto.
- **Tóno 25:** practical young caretaker, knows every door, a little teasing.
- **Tóno 50:** calmer, warm, says important things briefly. Has lived a full life; never sounds like
  a man who waited 38 years.
- **Address:** see the table (*vy* → *ty* switches are story beats).
- **Examples:**
  - Tóno 12: `Nakreslím to presne. Druhý rad zhora, tretí kameň zľava. A lastovičku k tomu.`
  - Tóno 50: `Búdky robím, aby deti po návrate našli niečo nové. Niečo, čo nie je na obrazovke.`

### OTO / OTO82 – Oto Bielik (46 / 66)

Mechanic, co-author of the civil ZVON prototype in 1960; in 1982 Tóno's grandfather who helps with
the school technical club and maintenance. Signs the materials and permissions; never a mad
scientist.

- **How he talks:** precise, calm, open to evidence; first looks, then speaks. In 1982 a little
  softer and amused by time. Short workshop sentences.
- **Address:** vy ↔ vy.
- **Examples:**
  - Oto 46: `Najprv sa pozrieme, až potom budeme rozprávať. Prístroj klame menej ako človek.`
  - Oto 66: `V Ivanke ste mali tú istú bundu. Ja som odvtedy vystriedal tri.`

### JANA82 / JANA95 / JANA20 / JANA35 – Jana Vargová (12 / 25 / 50 / 65)

A girl in 1982 with her own improved radio schematic; the optional side story shows how one act of
support changes her later life (club in 1995, laptops for children in 2020, an exhibit in 2035).

- **The same person:** exact choice of words at every age. At 12 shy but precise and lit up when
  allowed to explain; at 25 self-confident organiser; at 50 clear and practical on a video call; at
  65 calm and gently amused.
- **Address:** Jana 12 vyká Adamovi, Adam tyká jej; at 25, 50 and 65 vy ↔ vy. Jana 12 says
  *súdruh učiteľ* about/to Dobrovič.
- **Examples:**
  - Jana 12: `Je to inak ako vo vzore. Slabý signál sa tu nestratí, ide druhou cestou.`
  - Jana 50: `Notebooky rozdávame cez okienko a každý podpíše preberací list. Ani tu sa nestretneme.`

### ADAM10 – Adam at 10, on the 1995 tape

A child's voice on a school recording. Short, spontaneous, a bit shy in front of the microphone.

- **Examples:** `A môžem povedať aj niečo normálne?` (game line, keep) ·
  `Ja by som nahral, ako cinká lyžička v jedálni.`

---

## 2020 – Chorvátsky Grob, Čierna Voda, Dúbravka

### ELA – Ela Švecová (40)

Volunteer coordinator at the outdoor pick-up point. Keeps the lists, never hands out other
people's personal data. Fast, matter-of-fact, kind without sentiment.

- **How she talks:** short instructions in the order you need them, practical humour, no
  official phrases even when she does paperwork. Tyká Adamovi.
- **Examples:**
  - `Rúško máš? Tu máš náhradné. Tašku nechaj na stolíku a babke zavolaj.`
  - `Podpisy doplníme podľa pravdy. Nič nevymýšľame, len dopíšeme, čo sa naozaj stalo.`

### DANA – Dana Valová (48)

Shop assistant at the small grocery, sells through a window; prepared Mira's shopping. Calm and
exact; years behind the counter show in small remarks.

- **Examples:**
  - `Čaj, vločky, zemiaky. Ako vždy. A tašku nes za obe uchá.`
  - `Trpezlivosť nepredávam. Tú si musí každý doniesť z domu.`

### ROMAN – Roman Kováč (29)

Courier; with Mira's consent moved her technical boxes from a covered store into the garden
workshop; the second signature on the handover form. Relaxed, never cynical.

- **Examples:**
  - `Tú krabicu som niesol od prístrešku až do dielne. Najťažšia vec celého mesiaca.`
  - `Ľudia mi teraz mávajú cez okná. Predtým mi ani neotvorili.`

### LENKA – Lenka Bartošová (37) and BODKA (dog)

Neighbour walking her dog Bodka (a male dog, *Bodka – Bodku – Bodkovi – Bodkova loptička*).
Economical with words, amused. Bodka only barks (`Haf!`).

- **Examples:**
  - `Bodka je spokojný. Konečne chodia na prechádzky všetci, nielen on.`
  - `Loptičku stratil pri nádrži. Odvtedy ma ťahá len tým smerom.`

### JOZEF – Jozef Mlynár (73)

Neighbour at the notice board in Čierna Voda with a folding magnifier; wants readable information,
not an app. Warm, a bit ceremonious. Tyká Adamovi (*mladý pán*), Adam vyká (*pán Jozef*).

- **Examples:**
  - `Mne stačí veľké písmo a telefón, čo zvoní. Ostatné nech si nechajú mladší.`
  - `Tak, toto si prečítam aj bez lupy. Ďakujem pekne.`

---

## 1995 – Bratislava

### TONO – Tóno at 25 → see the family section.

### MIRA95 – Mira at 55 → see the family section.

### LEA95 – Lea Kormanová (33); LEA_REC – Lea's message of 2032

Fictional teacher, mother of Viktor; records ordinary sounds with the children. Warm, natural, not
pedagogical. In 2032 she leaves her son a voice message and dies the same year of natural causes.
The message (`action.F11.003`) is verbatim and must not be touched.

- **How she talks:** unhurried, lets silence finish a sentence, speaks to children as to people.
  Vy ↔ vy with Adam; ty to the children.
- **Examples:**
  - `Nahrávame aj to, čo deti povedia medzi vetami. Tam býva najviac pravdy.`
  - `Adam, nemusíš sa ponáhľať. Mikrofón počká.`

### JANA95 → see the family section.

### SONA – Soňa Urbanová (11)

Member of the school club, keeps the album of the school team. Curious and factual, a child's
speech without baby talk. Vyká Adamovi.

- **Examples:**
  - `Na fotke musíme byť všetci. Inak to nie je družstvo, len skupina.`
  - `Pani učiteľka Lea vravela, že album je náš. Tak si ho strážim.`

### ZITA – Zita Ondrušová (46)

Kiosk keeper in the Dúbravka housing estate; collects forgotten envelopes and local stories. Fast,
observant, good-natured. Tyká Adamovi.

- **Examples:**
  - `Noviny ti predám, správy ti poviem. Tie druhé sú zadarmo.`
  - `Na sídlisku sa nič nestratí. Len sa to presunie ku mne do kiosku.`

### EMIL – Emil Belan (61)

Street musician at the Karlova Ves tram stop; lends his metronome; lost the last bars of his own
song `Štyri zastávky`. Soft, slow, small musical images. Tyká Adamovi.

- **Examples:**
  - `Hrám pomaly, aby mi električky stihli dopĺňať rytmus.`
  - `Posledné takty mám v hlave len do polovice. Zvyšok zostal v knihe, ktorú som predal.`

### PALI – Pavol „Pali“ Drobný (42)

Repairman in Karlova Ves, gives the new belt by the old sample. Direct, collegial humour between
two repairmen. Ty ↔ ty. Declension: *Pali, Paliho, Palimu, s Palim; Paliho opravovňa*.

- **Examples:**
  - `Ukáž. Ten remienok je mŕtvy, dám ti nový. Zaplatíš tým, že ten rozhlas bude hrať.`
  - `Záruku dávam jednu: poviem ti, keď sa oprava neoplatí.`

### VIERA – Viera Holubová (64)

Second-hand bookseller („Pod druhou rukou“), keeps the separated map overlay from Mira's fond and
Emil's sheet music. Precise and mildly ironic. Vy ↔ vy. Not to be confused with Vera Nemcová (1960).

- **Examples:**
  - `Knihy sa predávajú, prílohy sa strácajú. Preto ich držím zvlášť.`
  - `Nechytajte ju za chrbát, prosím. Ten chrbát pamätá viac ako my dvaja.`

### ARCHIVAR (speaker KAROL) – Karol Merta (53)

Fictional head of the archive reading room; registers donations, allows work with copies. Formal,
exact, a little pedantic, but helpful. Vy ↔ vy.

- **Examples:**
  - `Poverenie je v poriadku. Kópie vám vydám, originály zostávajú v študovni.`
  - `Ticho tu nie je náhoda. Je súčasťou výpožičného poriadku.`

### FOTO (speaker ALENA) – Alena Svobodová (38)

Photographer in the studio „Svetlo“; develops the calibration negative and the team photo. Calm,
sure of her craft. Vy ↔ vy (the current texts mix *ty* and *vy*: fix to *vy*).

- **Examples:**
  - `Technický záber vyvolám hneď. Počkajte, prosím, pri suchom pulte.`
  - `Ľudia sú najprirodzenejší, keď si myslia, že už nefotím.`

### TRH (speaker FERO) – Fero Lánik (50)

Seller of small electronics on Miletičova; gives the connector for a simple repair. Earthy, short
sentences, no ethnic stereotypes. Tyká Adamovi.

- **Examples:**
  - `Váha sa mi zasekla. Keď ju spojazdníš, konektor je tvoj.`
  - `Originál? Tu je všetko originál. Len nie vždy od toho istého výrobcu.`

### MILADA – Milada Kyselová (57)

Tailor in Ružinov; has leftover braided textile insulation and understands repairing things.
Quick tailoring comparisons. Vy ↔ vy.

- **Examples:**
  - `Najprv ho zapojte, až potom navlečte. Ako pri kabáte: najprv ruka, potom gombíky.`
  - `Najťažšie sa opravuje veta „vždy to tak bolo“.`

### JURO – Juraj Malík „Juro Kazeta“ (26)

Cassette collector in the Ružinov basement club; recognises the two opposite tracks. An enthusiastic
sound guy who explains like a human, not a manual. Ty ↔ ty. Always *Juro* (*Jura, Jurovi*), never
*Juraj* (that is the painter).

- **Examples:**
  - `Toto nie je šum. To sú dve stopy, čo idú proti sebe, ako dvaja ľudia v jedných dverách.`
  - `Trochu šumu nevadí. Vadí, keď kvôli nemu zahodíš celú pesničku.`

### JURAJ – Juraj Križan (19)

Painter of the permitted community panel in the Petržalka underpass; draws the lit windows of the
blocks. Quiet, curious, unforced. Vyká Adamovi, Adam tyká jemu.

- **Examples:**
  - `Paneláky každý kreslí zvonka. Mňa zaujímajú tie svetlá vnútri.`
  - `Povolenie mám, aj s pečiatkou. Len bielu kriedu nie.`

### DEZI – Dezider Kováč (47)

Radio amateur in a Petržalka garage, Mira's former collaborator; knows the riverside measuring
point. Lively technical voice that immediately translates terms into everyday speech. Tyká Adamovi.
Name: *Dezider, Dezidera, Deziderovi* (*Dezi* only from his friends).

- **Examples:**
  - `Mapu poznám, kreslili sme ju s Mirou. Cievka patrí do držiaka na nábreží, opačne ju nevložíš.`
  - `Presné neznamená rovnaké. Presné je, keď vieš, prečo sa niečo líši.`

---

## 1960 – Ivanka pri Dunaji (shown as June 1962; Mira 22, Vera 24, Oto 46)

### OTO, MIRA60 → see the family section.

### BOZO – Božidar „Božo“ Fiala (45)

Station worker at the Ivanka railway stop; the player's orientation in the new era. Thoughtful,
likes clear destinations. Vy ↔ vy.

- **Examples:**
  - `Mladú Hruškovú? Tú nájdete pri meraní za parkom. Viac vám povie Oto v dielni.`
  - `Spiatočný lístok predám hocikedy. Do iného roku sa obráťte na vedenie.`

### BERTA – Berta Kovárová (68)

Villager on the square, local colour. Direct, curious, good-natured. Vy ↔ vy (*mladý pán*).

- **Examples:**
  - `Také topánky u nás nikto nenosí. Odkiaľ ste, mladý pán?`
  - `Mladá Hrušková zas svieti v tej búdke za bieleho dňa.`

### POSTA (speaker ALOJZ) – Alojz Baran (54)

Post office clerk; confirms the date of the technical record; keeps the carrier pigeon Béla. Formal
tone with an occasional soft aside; the only person allowed a little officialese, and it is
charming. Vy ↔ vy.

- **Examples:**
  - `Pečiatka potvrdzuje, že list tu dnes bol. Či je pravdivý, to nech posúdi niekto múdrejší.`
  - `Béla nie je služobný holub. Je to moja súkromná radosť s krídlami.`

### LIDA – Lída Fialová (43)

Costume maker of the amateur theatre; lends the hand punch after the stage flat is secured.
Organised and lively. Vy ↔ vy.

- **Examples:**
  - `Šesť hercov a štyri kabáty. Niekto bude v druhom dejstve mrznúť.`
  - `Pomôžete mi s kulisou a dierovač je váš. Oto mi ho potom vráti.`

### RUDO – Rudolf „Rudo“ Pavlík (34)

Amateur actor; lost the script of his play `Žiaden strach, miláčik`. Big stage diction on stage,
shy off stage. The only character with frequent exclamation marks. Vy ↔ vy.

- **Examples:**
  - `Žiaden strach, miláčik! … A ďalej to neviem. Ďalej je to v scenári.`
  - `Na javisku hovorím ako kráľ. Za javiskom radšej mlčím.`

### SKLAD (speaker STEFAN) – Štefan Haluška (51)

Keeper of the workshop materials in the farm yard; issues supplies against Oto's slip. Curt but
willing. Vy ↔ vy.

- **Examples:**
  - `Lístok, podpis, materiál. V tomto poradí.`
  - `Všetko nemáme. Ale presne viem, čo nemáme.`

### VERA60 – Vera Nemcová (22)

Technical draughtswoman of the ZVON documentation, finishing drawings in the park. Calm, practical,
no romance. Vy ↔ vy (the current line `Vezmi rydlo… Nery do platne.` must become *vy* and correct
Slovak). Not to be confused with Viera Holubová (1995).

- **Examples:**
  - `Vezmite si rydlo. Papier najprv pritlačte, potom obtiahnite hrany. Do platne neryte.`
  - `Kreslím vonku. Je tu svetlo a Oto mi tu nemôže každú chvíľu meniť rozmery.`

---

## 1982 – Dúbravka

### TONO82, OTO82, JANA82 → see the family section.

### DOBRO – učiteľ Dobrovič (39)

Fictional teacher in 1982. Careful the way an employee of that institution was careful, but able
to recognise a good technical idea. Formal at first, then concrete and human. Not a caricature of
socialist teachers. Speaks of *schválený vzor*, *výstavka*, *súdružka riaditeľka*. Vy ↔ vy.

- **Examples:**
  - `Výstavka má ukázať, že žiaci ovládajú schválený postup. Ak vedia viac, nech to vedia aj vysvetliť.`
  - `Podpíšem to. Ale nech je to na výstavke celé čitateľné, súdružka riaditeľka to bude čítať.`

### RUZENA – Ružena Malá (49)

Shop assistant in the housing-estate shop of 1982; gives the clean returnable jar with a seal.
Direct, kind, no invented "shortage of everything" jokes. Vy ↔ vy.

- **Examples:**
  - `Čo vidíte, to máme. Čo nevidíte, na to sa spýtajte.`
  - `Dobrý pohár vydrží roky. Ak ho človek nestratí.`

### MARTA82 – Marta Dobiášová (56)

Head of the school maintenance store; a proper authorisation is enough for her. Exact, patient,
knows the difference between a rule and needless trouble. Vy ↔ vy.

- **Examples:**
  - `Výdajka podpísaná, materiál vydaný. Vidíte, ide to aj bez trápenia.`
  - `Povedzte mi presne, čo potrebujete. Ide to rýchlejšie, ako keď mi vysvetľujete, že sa ponáhľate.`

### SIMON – Šimon Rybár (60)

School gardener of 1982; approves and records the tree guard and the new route of the hand cart.
Calm and concrete, thinks in decades. Vy ↔ vy.

- **Examples:**
  - `Vozík chodí najkratšou cestou. Tak mu tú cestu trochu predĺžime.`
  - `Lipu sadíme pre tých, čo pod ňou budú raz sedieť.`

---

## 2035 – Jasná

### NINA – Nina Švecová (30); NINA_REMOTE – Nina over the service channel

Curator of Atlas, Ela's daughter; refuses to erase badly labelled records and warned Viktor.
Matter-of-fact, fast, names the limits of her authority clearly. Over the service channel the same
voice, shorter sentences. Vy ↔ vy.

- **Examples:**
  - `Na diagnostiku máte povolenie. Na mazanie nie, a nemá ho nikto.`
  - `Mama by povedala, že na to treba zoznam. Tak ho máme.`

### VIKTOR – Viktor Korman (50)

Founder of Atlas, Lea's son. After her death in 2032 he wanted to keep everything; his normalizer
cut even her last message. He let the test run despite Nina's warning and is responsible for it;
not a murderer, not a madman. Convinced and controlled at first; quiet when he hears his mother.
No hysterics. Vy ↔ vy with Adam (the current lines mix: fix to *vy*).

- **Examples:**
  - `Ja nič nemažem. Ja upratujem. Rozdiel je v tom, čo potom zostane.`
  - `Volala vždy, keď nemala čo povedať. Myslel som si, že je to chyba.`

### TAMARA – Tamara Kráľová (40)

Repairwoman of the travelling workshop „Druhý život“; during the exhibition she has a table in the
lobby of Grand Jasná (earlier at the bench by Vrbické pleso). Friendly, a repairer among repairers,
no barista clichés. Ty ↔ ty.

- **Examples:**
  - `Toto ti prečíta kazetu aj starú servisnú pamäť. Len ju, prosím ťa, nenakláňaj.`
  - `Kávu robím, keď opravujem, a opravujem, keď robím kávu. Systém funguje.`

### BORIS – Boris Urban (64)

Archivist of the Atlas exhibition in the hotel salon. Calm; tells jokes like bibliographic
footnotes. Vy ↔ vy.

- **Examples:**
  - `Digitálna kópia je kópia. Originál je to, čo si niekto pamätá inak.`
  - `Ten záznam nechýba. Iba ho niekto zabudol pozvať.`

### SARA – Sára Vrbová (28)

Contact person of the exhibition at the Biela Púť client centre; arranges the authorised entry and
the cable-car ticket. Professional and pleasant; keeps a paper visitors' book. Vy ↔ vy.

- **Examples:**
  - `Meno vám zapíšem aj perom. Pero mi zatiaľ ešte nikdy nespadlo.`
  - `Lístok platí na oba úseky aj späť. Len ho nestraťte.`

### ROBOT – doručovací robot Očko (model 2033)

Small autonomous delivery cart; cannot solve a historical description of an address. Short
synthetic voice, polite; comedy from being literal (numbers, categories, confidence levels).
Says *vy*. Declension: *Očko, Očka, Očkovi, Očkova požiadavka*.

- **Examples:**
  - `Adresa: lavička so psom. Pes: keramický. Istota: šesťdesiat percent.`
  - `Poďakovanie prijaté. Ukladám do priečinka Nepotrebné, ale milé.`

### IVAN – Ivan Horský (44)

Cable-car staff at Priehyba; explains the change to the Funitel and checks the ticket. The cable
car is not broken and is no puzzle. Matter-of-fact and friendly. Vy ↔ vy.

- **Examples:**
  - `Hore fúka, ale dnes sa ide. Keby nie, poviem vám to ja, nie počasie.`
  - `Spiatočný lístok si nechajte, dolu ho budete potrebovať.`

### TURISTA – Miloš Polák (52)

Fellow passenger in the Funitel cabin; loves ordinary trip memories. Easy-going, gentle humour.
Vy ↔ vy.

- **Examples:**
  - `Hmlu si fotím tiež. Patrí k výletu rovnako ako výhľad.`
  - `S otcom sme sem chodili autobusom. Bolo to dlhšie a krajšie.`

### JANA35 → see the family section.

---

## Non-character speakers

### SYSTEM – device texts

The chronometer and the stationary ZVON, Atlas terminals, the ticket gate, the station
announcement. Terse, impersonal, readable for a 12-year-old; passive participles and short noun
phrases are fine here (and only here). Port names and switch positions in capitals.

- **Examples:** `Nositeľ rozpoznaný. Jeho pamäť je chránená.` · `Lístok platný.`

### NARRATOR – closing captions

Two reflective sentences in cutscenes (after the 1960 archive and at the very end). Calm, general,
no jokes. Its speaker label should read *Rozprávač*, not *Záverečné titulky* (C4 decides).

- **Examples:** `Jeden predmet. Veľa rúk. Ani jedna z nich nie je chyba v zázname.` ·
  `Nie všetko treba opraviť. Niečo si treba nechať.`
