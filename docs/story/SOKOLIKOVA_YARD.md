# S69 Pri LEALe – the walled courtyard between the Sokolíkova blocks (1995)

> **Renamed 2026-10-07 (owner):** the room is not „Sokolíkovský dvor“; its name in the whole game is the local name **„Pri LEALe“** (LEAL always in capitals; *pri LEALe, k LEALu, od LEALu*). Every player-visible text, the protected-fact rules (`P03-source`, `P03-wrong` now require `\bLEAL\w*`) and this document were updated; the changed keys are listed in `docs/writing/out_v5/leal_rename.csv`. Older drafts and review records under `docs/writing/out*/` and `review_gpt/` keep the old name as history.

Status: **design, ready to implement** (2026-10-06, evening). Owner request of 2026-10-06: "Sokolíkova yard – do it,
you can place Zuzana there and a minority of some of the game's puzzles", and "Zuzana in the game – do it, 1962
Ivanka and 1995 Dúbravka". The painting is the owner-loved `art/backgrounds/sokolikova-yard.png` (owner feedback
2026-10-05: "must be in the game: a new walk-through room next to the school yard / kiosk courtyard").

Companion documents: [ZUZANA.md](ZUZANA.md) (who she is, her 1962 part, the binding rules), the exact data in
`docs/writing/out/content_v2_draft.json` (`world_ext` = the Core world overlay shape, `dialogue_ext` = the dialogue
overlay shape, `core_requests`, `sk_override_proposals`, `glossary_change`). Every Slovak line is a **draft
(writing step 1)**; WRITING_METHOD.md steps 2–4 follow. game.json is not edited.

---

## 0. Summary for the owner

- **New room S69 „Pri LEALe"** (1995, Dúbravka, 15 June afternoon): your painting of the walled ihrisko
  between the panel blocks, with three things added: a green bench, a child's bike and a chalk hopscotch on the
  court. You reach it from the kiosk street S18 through the gap between the blocks (the way to the right of the
  school, not through the podlubie).
- **Zuzana, 40,** stands by the bench. She lives on the estate (game fiction for this scene). She recognises Adam
  as the man from the Ivanka park in June 1962 because he has not aged: the same shoes, and the carbon paper she once
  sent him for. The game reaches 1995 **before** 1962, so the first time they meet she remembers and he cannot (*„To
  si zapamätám. Pre istotu."*); after Ivanka he can. She is warm, light and does not ask how (*„Niektoré veci sú
  krajšie bez návodu."*). Nothing is said about her life: no job, family or future.
- **One main step moves into the yard:** reading the rhythm drawing (B19). The four shapes, three waves, two strokes
  and six pieces that the school club painted are now on three panels of the courtyard wall instead of the sign in
  the school yard. The logic is identical (same action, same condition, same clue 3–2–6). Zuzana helps: she knows
  which of the 32 panels (she counts everything, as she did at seven) and confirms the six pieces.
- **A small side quest Q11 „Druhý posledný zvonec" (3 steps):** Kubo, a first-grader from a neighbouring entrance,
  has a mute bike bell; the cap bounced off and rolled away. Zuzana counted the bounces: under the blue spruce.
  Adam finds the cap and screws it on. The school bell rings across the yard, and Zuzana keeps the promise from
  1962 (*„zamávajte, to je dohoda"*): they wave. Kubo: *„Komu mávate?"* – *„Jednému zvončeku z Ivanky."*
- **Epilogue shot** (end of June 1995): the yard children ride round the court ringing, Kubo loudest; Zuzana says
  what she said at seven: *„Posledný zvonec. A v septembri zase prvý."*
- **Licence note:** the yard painting was made from a CC BY-NC-SA source photo (`art/backgrounds/index.html`), so S69
  joins the non-commercial list of DECISIONS item 9 (with S17, S18, S55, S61, S62, S65, S66).

---

## 1. The place

| | |
|---|---|
| id / name | `S69` „Pri LEALe" (≤ 32; the exit label into it is the same) |
| era / district / region | 1995 · Dúbravka · map region **Dúbravka 1995** (hub stays S11; S69 is not a hub) |
| time | 15 June 1995, evening at sunset: the painting was relit on 2026-10-07 to the light of S18 next door (art/masters/bg_natural/S69_v7, S69.md; owner request) |
| what it is | the walled courtyard ihrisko between the early-1970s panel blocks of Sokolíkova: a long wall of upright concrete panels in the foreground left, a low back wall, a right wall, a worn asphalt court, a birch and a blue spruce behind the back wall, a globe street lamp, the blocks with balconies behind the trees |
| added to the painting | a green wooden bench on the right edge of the court where the grass bank begins; a small child's bike with stabiliser wheels leaning on it; a chalk hopscotch (8 squares and a half-circle) on the court; the school club's painting (four shapes; three waves, two strokes, six pieces – the same content and colours as the S17 sign) across three panels of the right wall next to the passage; a column of chalk tally marks on one panel (Kubo's days to the holidays) |
| background asset | `bg/S69.webp` (1920 × 1080 from the 2752 × 1536 painting: scale to height 1080, crop 7 px each side), music `music/1995.ogg`, camera family `S69` (its own) |
| art brief (data, Slovak) | in the draft: *Ohradené ihrisko medzi panelákmi na Sokolíkovej v júni 1995 popoludní …* |
| ambience | *Lopta o betón, detské hlasy, vrabce na múre, z balkóna rádio, vzdialená električka.* |
| first entry | ADAM: `Tento dvor poznám. Raz som tu prehodil loptu cez múr a domov som prišiel až za tmy.` (Adam went to ZŠ Sokolíkova as a boy; in June 1995 his ten-year-old self is in the school) |

### 1.1 Walk area and camera (template; the blocking pass makes the final `data/blocking/S69.json`)

The camera stands outside the court on the lawn at the bottom left, looking over the foreground wall into the court.
The walk area is the court: bounded by the back-wall foot, the right-wall foot, the grass bank at the bottom right and,
on the left, the **top edge of the foreground wall** (the hero's feet stay above that edge, so no foreground mask is
needed). Template polygon `[[830,800],[1000,770],[1268,702],[1385,712],[1700,748],[1860,800],[1880,880],[1640,960],
[1580,1015],[1150,1015],[1150,885],[1000,840],[830,812]]`, spawn `[1360, 985]` (arriving from S18). Estimated hero
scale ~0.21 at the back (y ≈ 705) to ~0.55 at the bottom (y ≈ 1015); the blocking pass measures it from the panel
heights and runs `tools/check_blocking.py`. If figures read too small, the art agent may repaint a closer framing
of the same view (keeping its look) before blocking: that is the one open camera question.

### 1.2 Connections

| exit | in room | rect / interaction point (template) | label | travel |
|---|---|---|---|---|
| `S18.to_S69` | S18 (kiosk street) | `[430, 850, 190, 45]` / `[525, 880]`: the side road between the beige block and the pines that runs into the gap between the blocks | „Pri LEALe" | walk |
| `S69.to_S18` | S69 | `[1150, 1000, 430, 80]` / `[1360, 1000]`: the court opens towards the camera between the end of the foreground wall and the grass bank | „Sídliskový dvor s kioskom" | walk |

Connection `S18 ↔ S69`, bidirectional, walk, no condition. **No S17 ↔ S69 link:** S17's one way to the right of the
school already is `S17.to_S18`, a second exit on the same edge would confuse, and the podlubie stays a no-go
(DECISIONS, owner 2026-10-06). The passage at the back of the court (`S69.gap`) is a look, not an exit. Shortest walk
from the tram stop: S11 → S18 → S69 (two steps, as S11 → S12 → S17 before).

### 1.3 Hotspots (`world_ext.rooms[S69].hotspots`; keys `hotspot.<id>.name`, `look.<id>`, `look.<id>.variant<n>`)

| id | name | kind | template rect / point | look (Slovak draft) | variants |
|---|---|---|---|---|---|
| `S69.wall` | Betónový múr | prop | `[240,690,900,380]` / `[1185,995]` | Múr z betónových panelov postavených na výšku. Lopta sa od neho nikdy neodrazí tam, kam chceš. | – |
| `S69.rhythm` | Rytmický nákres | prop (**B19 target**) | `[1440,585,185,125]` / `[1520,790]` | Kruh, trojuholník, štvorec, fialové V a pod nimi TRI VLNY, DVA ÚDERY, ŠESŤ DIELIKOV. To je nastavenie 3–2–6. | – |
| `S69.court` | Ihrisko so škôlkou | prop | `[1190,790,260,100]` / `[1320,930]` | Asfaltové ihrisko a na ňom kriedou škôlka: osem políčok a hore polkruh. Čiary sú rovnejšie ako moje nákresy. | – |
| `S69.birch` | Breza | prop | `[640,20,120,660]` / `[900,805]` | Breza za múrom. Biela kôra, tenké vetvy a lístie sa trasie, aj keď vôbec nefúka. | – |
| `S69.spruce` | Modrý smrek | prop (**Q11B target**) | `[820,40,290,600]` / `[1080,760]` | Modrý smrek, pichľavý zo všetkých strán. Pod takými končia lopty, kriedy a odvaha. | after Q11A: *Pod smrekom sa medzi ihličím niečo leskne. Niečo mosadzné.* · after Q11B: *Pod smrekom zostalo už len ihličie a jedna zabudnutá krieda.* |
| `S69.lamp` | Guľová lampa | prop | `[305,455,60,240]` / `[845,806]` | Guľová lampa na stĺpe. Keď sa večer rozsvieti, deti vedia, že sa ide domov. Lepšie ako hodinky. | – |
| `S69.bench` | Lavička | prop | `[1590,830,240,110]` / `[1580,960]` | Zelená lavička, čerstvo natretá. Asi tá, na ktorú sa sťažujú pri kiosku. (callback to Zita's topic *Opravili lavičku …*) | – |
| `S69.bike` | Kubov bicykel | prop (**Q11C target**) | `[1440,860,150,100]` / `[1470,985]` | Malý bicykel s prídavnými kolieskami. Na zvončeku chýba vrchnák, ostali len holé zúbky. | after Q11C: *Kubov bicykel. Zvonček má zase vrchnák a zvoní pri každom hrbole.* |
| `S69.gap` | Priechod medzi blokmi | prop | `[1275,600,105,100]` / `[1330,720]` | Úzky priechod medzi blokmi. Vedie k ďalším vchodom a k ďalším múrom. | – |
| `S69.ZUZANA95` | Zuzana | npc | `[1600,670,120,265]` / `[1560,955]`, feet ~`[1660,935]`, facing left | Žena s kúskom kriedy v ruke si ma prezerá, akoby ma odniekiaľ poznala. Ja ju nepoznám. Asi. | after I10: *Zuzana z parku v Ivanke. Pre ňu prešlo tridsaťtri rokov, pre mňa oveľa menej.* |
| `S69.KUBO` | Kubo | npc | `[1355,785,90,178]` / `[1330,990]`, feet ~`[1400,960]`, facing right | Malý chlapec s odretým kolenom ťuká do zvončeka na bicykli. Zvonček mlčí. | after Q11C: *Kubo krúži okolo ihriska a zvoní v každej zákrute. Aj tam, kde žiadna nie je.* |

All interaction points lie inside the template walk polygon (checked), every rect is ≥ 44 × 44 px. Atmospheric props:
wall, court, birch, lamp, bench, gap (left click = look, shown by Space). The NPC hover names are „Zuzana" and „Kubo"
from the start, like every NPC; before the 1962 chapter the name simply means nothing yet to the player.

---

## 2. Zuzana in 1995 (`ZUZANA95`)

| | |
|---|---|
| name / age | Zuzana, 40 (born 1955; the only facts are the owner's) |
| in the scene | stands by the green bench, a stick of chalk in her hand; she has chalked the hopscotch for the yard children |
| voice | calm, kind, quietly funny; short sentences; still counts everything; never pries |
| address | vy → Adam, Adam → vy; she tykne Kubo, Kubo says *teta Zuzana* |
| knows | the yard, its children, the 32 wall panels, who painted the panel (school-club children "with a lady who had a tape recorder under her arm and chalk falling from her sleeve" – Mira 1995's look, never named) |
| never | explains or is told about time travel; mentions her own life (job, family, home details beyond "here"); names or meets anyone of Adam's family; says anything about her future |
| running gags | counting (panels, balls over the wall, days); *„iba do štvorky, dospelí ďalej padajú"* (her 1962 hopscotch rule); the fourth-floor neighbour who throws the ball back, more annoyed each time |

### 2.1 The two orders of meeting (why every line is true in every state)

The main route visits 1995 (B-steps) **before** Ivanka 1962 (I-steps), and again later (E11). Adam always meets
the seven-year-old in I10 (main route, S37, her z-lines send him to the post office for carbon paper). So:

| state | what she says | what Adam can say |
|---|---|---|
| before I10 (e.g. the first 1995 visit) | topic `ZUZANA95.extra 1` „Poznáme sa?": she recognises him (the shoes; she sent him to the post office for paper that writes twice) | only true things: he was not born in 1962; the shoes are from last autumn; *„To si zapamätám. Pre istotu."* – it pays off when he hears I10.z04 in 1962 |
| after I10 | topic `ZUZANA95.extra 2` „Park v Ivanke": now he knows; *„Pre mňa je to tridsaťtri rokov. A pre vás?" – „Oveľa menej. Viac vám povedať neviem." – „Nemusíte. Hlavne že ste prišli aj sem."* | – |
| after Q10D (the bell repaired in 1962) | topic `ZUZANA95.extra 3` „Triedny zvonček": it rang on the last day; the class ran out before she finished | – |
| Q11 done before Q10 | her *„stará dohoda … s jedným opravárom zvončekov"* (Q11C) is a seed; Q10D's *„To je dohoda."* pays it off in 1962 | Adam asks *„S kým?"* and waves with her: true in both orders |

### 2.2 Topics (`dialogue_ext.topics`, keys `topic.ZUZANA95.extra <n>.NNN`)

| id | label (≤ 28) | requires_done | excluded_done | purpose |
|---|---|---|---|---|
| `ZUZANA95.extra 1` | Poznáme sa? | – | I10 | recognition, phase 1 |
| `ZUZANA95.extra 2` | Park v Ivanke | I10 | – | recognition, phase 2 |
| `ZUZANA95.extra 3` | Triedny zvonček | Q10D | – | closes the 1962 thread |
| `ZUZANA95.extra 4` | Nákres s vlnami | B03 | B19 | **her help with B19**: which panel (direction only) |
| `ZUZANA95.extra 5` | Škôlka na asfalte | – | – | hopscotch callback |
| `ZUZANA95.extra 6` | Koniec školského roka | – | – | last-bell motif, 15 days left |

`ZUZANA95.extra 1` „Poznáme sa?"
```
ADAM:     Prepáčte, pozeráte sa na mňa, akoby sme sa poznali.
ZUZANA95: Lebo sa poznáme. Z parku v Ivanke, z júna šesťdesiatdva.
ADAM:     Šesťdesiatdva? Vtedy som ešte nebol ani na svete.
ZUZANA95: Viem, ako to znie. Ale mali ste presne tieto topánky.
ADAM:     Tieto topánky som si kúpil minulú jeseň.
ZUZANA95: A hľadali ste papier, ktorý píše dvakrát. Poslala som vás na poštu za pánom Baranom.
ADAM:     To si zapamätám. Pre istotu.
ZUZANA95: Nebojte sa, nebudem sa pýtať, ako to robíte. Niektoré veci sú krajšie bez návodu.
ADAM:     To hovoríte opravárovi.
ZUZANA95: Práve preto.
```
`ZUZANA95.extra 2` „Park v Ivanke"
```
ADAM:     Už viem, odkiaľ sa poznáme. Z parku pri kaštieli.
ZUZANA95: Tak predsa. Už som si myslela, že sa mi to celé iba prisnilo.
ADAM:     Vy ste ma vtedy poslali na poštu po uhlový papier.
ZUZANA95: A vy ste naozaj išli. Dospelí ma vtedy veľmi nepočúvali.
ADAM:     Mali by. Ten papier zabral.
ZUZANA95: Pre mňa je to tridsaťtri rokov. A pre vás?
ADAM:     Oveľa menej. Viac vám povedať neviem.
ZUZANA95: Nemusíte. Hlavne že ste prišli aj sem.
```
`ZUZANA95.extra 3` „Triedny zvonček"
```
ADAM:     Ten triedny zvonček z Ivanky… Zazvonili ste ním na konci roka?
ZUZANA95: Zazvonila. Trieda vybehla na prázdniny skôr, ako som dozvonila.
ZUZANA95: Učiteľka povedala, že takto rýchlo ešte nikto prázdniny nezačal.
ADAM:     A pútko vydržalo?
ZUZANA95: Celý jún. Potom som to už nerátala.
ADAM:     Vy a nerátať? Tomu sa mi nechce veriť.
ZUZANA95: Boli prázdniny. Aj rátanie má raz za čas voľno.
```
`ZUZANA95.extra 4` „Nákres s vlnami"
```
ADAM:     Nevideli ste tu niekde nákres s vlnami a čiarkami?
ZUZANA95: Videla. Na jar ho tu na múr maľovali deti zo školského krúžku s jednou pani.
ZUZANA95: Pani mala pod pazuchou magnetofón a z rukáva jej padala krieda.
ADAM:     To bude ona. A na ktorom paneli to je?
ZUZANA95: Múr má tridsaťdva panelov. Nákres je na troch vpravo, hneď pri priechode.
ADAM:     Vy ste tie panely rátali?
ZUZANA95: Ja rátam všetko. To mi zostalo.
```
`ZUZANA95.extra 5` „Škôlka na asfalte"
```
ADAM:     Tú škôlku na asfalte ste kreslili vy?
ZUZANA95: Ja. Kubo ju chcel, tak ju má. Osem políčok a hore polkruh.
ADAM:     A rovné čiary. Ja by som na to potreboval pravítko.
ZUZANA95: Môžete si skočiť. Ale iba do štvorky, dospelí ďalej padajú.
ADAM:     Tak radšej do trojky. Nech mám rezervu.
ZUZANA95: Rozumné. Kubo skáče až do osmičky, ale on ešte nevie, že by mal padať.
```
`ZUZANA95.extra 6` „Koniec školského roka"
```
ADAM:     Deti sa už určite tešia na prázdniny.
ZUZANA95: Ešte pätnásť dní. Kubo si ich škrtá kriedou na múre, aby mu ani jeden neušiel.
ADAM:     A vy mu ich pomáhate rátať.
ZUZANA95: Ja rátam stále. Schody, dni aj loptu, keď preletí cez múr.
ZUZANA95: Dnes preletela štyrikrát. Pani zo štvrtého poschodia ju zakaždým hodila späť nahnevanejšie.
ADAM:     Tá by mohla chytať za družstvo.
ZUZANA95: Ona chytá. Len proti nám.
```

### 2.3 Kubo (`KUBO`, 7)

A first-grader from a neighbouring entrance (never Zuzana's child), finishing first grade like Zuzana in 1962. Quick
child speech, takes things literally, proud of what he can do; vy → Adam, Adam → ty. Two extra topics (WRITING_METHOD
§ 3), both state-independent:

`KUBO.extra 1` „Prvá trieda"
```
ADAM: Do ktorej triedy chodíš?
KUBO: Do prvej. Už viem čítať, písať a pískať na prstoch.
ADAM: A čo z toho ťa naučili v škole?
KUBO: Čítať a písať. Pískať ma naučil brat, ale to sa na vysvedčenie nepíše.
ADAM: Škoda. Za to by si mal jednotku.
KUBO: Pani učiteľka by nesúhlasila. Ona to pískanie počula.
```
`KUBO.extra 2` „Prečo je tu taký múr?"
```
ADAM: Prečo je okolo ihriska taký vysoký múr?
KUBO: Aby lopta neutekala na ulicu. Ale ona uteká aj tak, len vyššie.
ADAM: A kto pre ňu potom chodí?
KUBO: Najmenší. Čiže ja.
KUBO: Pani zo štvrtého poschodia ju vždy hodí späť. Ale najprv nám povie, koľko muškátov sme zlomili.
ADAM: A koľko?
KUBO: Všetky. Ale ona ich má veľa.
```

---

## 3. The relocated main step: B19 „Zapísať tri kalibračné číslice"

### 3.1 What moves and why

| | before | after |
|---|---|---|
| action | `B19` (quest M07, main, kind click, `requires_done [B03]`, no items, gives nothing) | **identical** |
| target | `S17.rhythm` (freestanding painted sign on two posts in the school yard) | `S69.rhythm` (the same painting across three panels of the courtyard wall) |
| room | S17 Školský dvor | S69 Pri LEALe |
| clue | TRI VLNY, DVA ÚDERY, ŠESŤ DIELIKOV → 3–2–6 | identical, in `look.S69.rhythm` and `action.B19.001` |
| hint step | `ui.hint_step.B19` | relocation `hint_step`: *Pri LEALe si prečítaj rytmický nákres na múre.* (key `action.B19.hint_step`) |

World overlay record: `{"action": "B19", "to_hotspot": "S69.rhythm", "retire_hotspot": false, "hint_step": …}`.
`S17.rhythm` stays in S17 as an atmospheric prop (its sign keeps the four shapes), so no S17 hotspot disappears.

**Why this step.** Its target is a painted panel, and the yard is literally a wall of concrete panels that a school
club could paint; the painting moves almost unchanged. B19 has no item, no NPC and no condition besides B03, so moving
it cannot break any order: every route that reached S17 can reach S69 (two walking steps from the tram stop either
way). It is a puzzle clue (P03), so the yard really gets "some of the puzzles", together with the new side quest. Its
lines are Adam's own, so no existing conversation has to move.

**Considered and not chosen:** Soňa's photo quest Q3 (Q3A/Q3D: moving Soňa would empty the school yard of people);
the club notice B01 (it belongs at the school front); Q5 (Petržalka). One main step plus the side quest keeps the
yard "a minority" of the puzzles.

**Zuzana's help (real, not required):** her topic „Nákres s vlnami" (after B03, until B19) points to the right panels;
during B19 she confirms the count (lines below). Neither adds a condition: B19 works exactly as before without her.

### 3.2 B19 in play order (`dialogue_ext.sequences`, new keys `action.B19.zNN`)
```
[action.B19.001] ADAM:     „Tri vlny, dva údery, šesť dielikov.“ Čiže tri, dva, šesť.
 action.B19.z01  ZUZANA95: Sedí to. Šesť dielikov, rátala som ich, keď to deti maľovali.
 action.B19.z02  ADAM:     Vy ste ich rátali?
 action.B19.z03  ZUZANA95: Ja rátam všetko. Schody, dni do prázdnin aj lopty za múrom.
[action.B19.002] ADAM:     Zapíšem si to. Vlastnej pamäti dnes veľmi neverím.
 action.B19.z04  ZUZANA95: Zapíšte. Ja si to budem pamätať aj tak.
```
The P03 words stay in `.001` (protected `P03-spoken-words`); she repeats *šesť dielikov*, never another number. If the
C2 (1995) writing pass also extends B19, both go into one sequence entry (an exchange is extended at most once). Core
request (a): ZUZANA95 must be allowed to speak in B19 (an NPC standing in the action's room).

### 3.3 Texts that name the old place (for the writers; drafts in `sk_override_proposals`)

| key | now (in the game) | proposed |
|---|---|---|
| `action.B17.003` (Dezider, **protected P03-source**) | … Tri číslice Mira nakreslila na panel na školskom dvore. | Lepší bude metronóm, má ho Emil v Karlovej Vsi. Tri číslice namaľovala Mira na múr pri LEALe. |
| `action.B17.004` (Adam) | Na školský dvor sa vraciam dobrovoľne. To sa mi ako žiakovi nestalo. | K LEALu sa vraciam dobrovoľne. Ako žiak som tam chodil iba po loptu. |
| `action.B17.objective` = `.journal` | … prečítaj rytmický nákres na školskom dvore. | Požičaj Emilov metronóm a prečítaj rytmický nákres pri LEALe. |
| `quest.M07.hint.2` | … Tri číslice sú na paneli na školskom dvore. | Dezider dá cievku, Emil metronóm. Tri číslice sú na múre pri LEALe. |
| `quest.M07.hint.3` | … prečítaj rytmický nákres na školskom dvore … | the same chain with *pri LEALe* |
| `puzzle.P03.wrong` (protected P03-wrong) | … na rytmickom nákrese na školskom dvore. | Nesedí to. Správne číslice sú na rytmickom nákrese pri LEALe. |
| `look.S30.dial` (protected P03-wrong) | … číslice z nákresu na školskom dvore. | … a číslice z nákresu pri LEALe. |
| `hotspot.S17.rhythm.name` | Rytmický nákres | Výtvarný panel |
| `look.S17.rhythm` (protected P03-words/-digits move to `look.S69.rhythm`) | Pod nákresom je napísané TRI VLNY … 3–2–6 … | Kruh, trojuholník, štvorec a fialové V. Deti z krúžku maľovali vo veľkom. |
| `ui.hint_step.B19` (ui.csv) | Na školskom dvore si prečítaj rytmický nákres. | Pri LEALe si prečítaj rytmický nákres na múre. (Core shows the relocation's `hint_step`; keep ui.csv equal so no stale text remains) |

Checked and **not** affected: `puzzle.P03.clue` (*Rytmický nákres a zápisník …*, no place), `journal.clue.P03`
(3–2–6), `action.B19.001/.002/.label/.objective/.journal` (no place), `action.B22.001`, Soňa's and the 2020/1982 school
yard texts (`quest.Q3.*`, `ui.hint_step.Q3A/Q3D/D05/E08/E09`, `action.C01/D01/E11.*`, `item.KEEPERNOTE.purpose`: they
mean the real school yard and stay). The C2 draft `docs/writing/out/C2.csv` still holds the old B17.003/B17.004/
M07.hint.3/P03.wrong/look.S30.dial/look.S17.rhythm rows: update them, or the next merge brings the school yard back.

### 3.4 Glossary change (same commit as the overrides)

- `glossary.json` protected `P03-words.keys` and `P03-digits.keys`: `look.S17.rhythm` → `look.S69.rhythm`.
- `glossary.json` protected `P03-source.require` and `P03-wrong.require`: `(?i)školsk\w* dvor` → `(?i)Sokolíkovsk\w* dvor\w*` → (owner rename 2026-10-07) `\bLEAL\w*`.
- GLOSSARY.md § 6.1 P03 row (the courtyard wall, `look.S69.rhythm`), the rooms table (+ `S69 | 1995 | Dúbravka |
  Pri LEALe`), the walkthrough table row 30 (B19 → S69), the people rows ZUZANA / ZUZANA95 / KUBO.
- **Verified:** `tools/check_rewrite.py` on the ten proposed rows with a glossary patched as above: **0 errors**
  (two acknowledged warnings on `look.S17.rhythm`, note `drop: 3–2–6`). With today's glossary the same rows fail
  exactly on the four old-place rules, as expected.

### 3.5 Other effects of the move

- `walkthrough.json` step 30 (travel S11 → S12 → S17, target S17.rhythm) is never edited; the replayer recomputes the
  path to the relocated target (S11 → S18 → S69), as it does for the travel overlay's S02 → S51 hop; step 31 starts in
  S69 (Core request c).
- Art: the 1995 S17 sign loses its waves / strokes / pieces rows (layer `variants/S17_sign_shapes_only.webp` after G11
  = always in 1995); the same content is painted on the S69 wall. S55 (2020) and S61 (1982) have no sign.
- `tools/writing_bundles.py`: add S69 to chunk C2's rooms.

---

## 4. Side quest Q11 „Druhý posledný zvonec"

**Story.** Kubo's bike bell is mute: the brass cap bounced off on the kerb and rolled away. At the end of the school
year the yard children ride round the court ringing, and without a bell "it does not count". Zuzana counted the
bounces: three, then it vanished under the blue spruce. Adam finds the cap and screws it back with his tools. The
school bell rings across the yard; Zuzana keeps an "old agreement with a bell repairman" and waves, Adam waves with
her. (Title alternative if the owner prefers it plainer: „Zvonček pre Kuba".)

3 steps, available from the first 1995 visit, needs no main action and no main action needs it; also playable after
the credits. Items and logic in `world_ext` (all `quest: "Q11"`, `once`, atomic commit, no puzzle or cutscene).

| id | room | target | kind | requires | selected | gives / consumes | animation / sfx | label | objective / journal | hint_step |
|---|---|---|---|---|---|---|---|---|---|---|
| `Q11A` | S69 | `S69.KUBO` | topic | – | – | – | talk | Zvonček na bicykli | Pod modrým smrekom pri LEALe nájdi vrchnák Kubovho zvončeka. | Pri LEALe sa porozprávaj s Kubom o zvončeku na bicykli. |
| `Q11B` | S69 | `S69.spruce` | click | done Q11A | – | gives `BELLCAP` | reach_low / item_soft | Pohľadať vrchnák pod smrekom | Naskrutkuj vrchnák na zvonček Kubovho bicykla. | Pohľadaj vrchnák zvončeka pod modrým smrekom pri LEALe. |
| `Q11C` | S69 | `S69.bike` | click | items BELLCAP, TOOLS | BELLCAP | consumes `BELLCAP` | use_tool / **bike_bell** (new) | Naskrutkovať vrchnák na zvonček | journal: Kubov zvonček zvoní. So Zuzanou sme zamávali zvoneniu zo školy. | Vrchnák zvončeka použi na Kubov bicykel. |

New item `BELLCAP` „Vrchnák zvončeka": *Mosadzný vrchnák z detského zvončeka. Vnútri má zúbky, na boku škrabanec od
obrubníka.* (icon `items/BELLCAP.webp`). `TOOLS` is never consumed, so Q11C is always possible. A click on the spruce
before Q11A is only its look. Speakers: Q11A Kubo + Zuzana (she stands in the room); Q11C Kubo + Zuzana on a prop
(staging guests listed).

Q11A
```
ADAM:     Prečo ťukáš do toho zvončeka?
KUBO:     Lebo nezvoní. Ťukám, ťukám a nič.
ADAM:     Ukáž. Chýba mu vrchnák, ten, čo zvoní.
KUBO:     Odskočil, keď som vyšiel na obrubník. A potom sa kotúľal.
ZUZANA95: Trikrát poskočil a zmizol pod modrým smrekom. Rátala som to.
KUBO:     Ja som nerátal. Ja som padal.
KUBO:     Na konci roka ideme všetci okolo dvora a zvoníme. Bez zvončeka sa to nepočíta.
ADAM:     Vrchnák nájdem a naskrutkujem. Na konci roka budeš zvoniť.
```
Q11B
```
ADAM: Ihličie, dve kriedy, stará loptička a… mosadzný vrchnák.
ADAM: Trikrát poskočil a zastavil sa presne tu. Rátala dobre.
```
Q11C (sfx `bike_bell` before line 2; the distant ZŠ Sokolíkova electric bell `school_bell_far` before line 4; line 4
says what is heard, so no meaning lives only in the sound)
```
ADAM:     Zúbky do závitu, pootočiť a skrutkovačom jemne dotiahnuť. Je to zvonček, nie trezor.
KUBO:     Zvoní! Teta Zuzana, počujete?
ZUZANA95: Počujem. Celý dvor počuje.
ZUZANA95: A počujte aj toto. V škole práve zvonia.
ZUZANA95: Keď počujem zvoniť na konci roka, zamávam. Taká stará dohoda.
ADAM:     S kým?
ZUZANA95: S jedným opravárom zvončekov.
KUBO:     Ale veď ešte nie je koniec roka.
ZUZANA95: Ešte pätnásť dní. Toto je skúška.
ADAM:     Skúška vyšla. Mávam s vami.
KUBO:     Komu mávate?
ZUZANA95: Jednému zvončeku z Ivanky.
```
(*Toto je skúška / Skúška vyšla* repeats the 1962 Q10D exchange word for word.)

Quest record: title „Druhý posledný zvonec"; goal *Oprav Kubov zvonček na bicykli, aby mohol na konci roka zvoniť
s ostatnými deťmi.*; reward *Kubo so zvončekom a Zuzanina škôlka na Sokolíkovej v Adamovom albume.*; hints
1 *Kubo pri LEALe má na bicykli zvonček, ktorý nezvoní.* · 2 *Vrchnák zvončeka sa odkotúľal pod modrý
smrek a Zuzana videla kam. Naskrutkuješ ho náradím zo servisnej brašne.* · 3 *Kubo, téma „Zvonček na bicykli" →
modrý smrek v dvore → vrchnák zvončeka na Kubov bicykel.*

**Epilogue `epilogue.11`** (after Q11C, after Q10 in quest order): shot *Koniec júna 1995. Deti zo Sokolíkovej jazdia
okolo dvora a Kubo zvoní najhlasnejšie.* · line `ZUZANA95: Posledný zvonec. A v septembri zase prvý.` (the same words
as her 1962 epilogue line). Still `EPILOGUE_11`.

---

## 5. Living world (ambient ideas for the living-world agent; no meaning, reduced motion respected)

- Sparrows hopping along the wall tops; now and then one lands on the globe lamp.
- A ball flies over the back wall from the far side every ~40–60 s and bounces once on the court.
- Birch leaves trembling (the look says so); a few spruce needles drift.
- Swallows high over the blocks (a quiet echo of Tóno's *Lastovička sa vracia*, purely visual).
- A laundry line on one balcony moving in the wind; an open balcony window with a radio (sound only, no brands).
- After Q11C: Kubo's bell `bike_bell` now and then (audio, at most every ~30 s); optionally Kubo rides a small loop if
  a riding sprite is ever made (not required).
- Ambient sound bed: ball on concrete, children's voices, sparrows, a distant tram bell (`data/audio`, audio agent).

---

## 6. Asset list (art and audio agents)

Budget note: no paid calls were made for this design. Rough fal.ai estimates from earlier sets: a character sheet
set USD 0.6–1.5, a background edit USD 0.05–0.45, an item icon ~USD 0.03, a still ~USD 0.1–0.3. Rejected attempts go
to `rejected/` subfolders; log every paid call in `art/spend-log.csv`; look at every image.

### 6.1 S69 room
| asset | what | notes |
|---|---|---|
| `bg/S69.webp` (master in `art/masters/bg_natural/`) | the owner's painting at 1920 × 1080, plus: green wooden bench on the right court edge (~1590–1830, 830–940), child's bike with stabilisers leaning on it (~1440–1590, 860–960; the bell on the handlebar visibly without its cap), chalk hopscotch on the court (~1190–1450, 790–890), the club painting across three right-wall panels next to the passage (~1440–1625, 585–710: red circle, blue triangle, yellow square, purple V; green zigzag of three waves; two black strokes; six red pieces – the S17 sign's content), a column of chalk tally marks on one panel | keep the painting's look; no lettering besides the painted marks; 1995 (no modern objects); source licence CC BY-NC-SA → NC list |
| `data/blocking/S69.json` | natural blocking: walk polygon, actor scale, anchors, final rects, NPC feet | from the template in § 1; `tools/check_blocking.py` |
| `fg/S69.webp` | only if the blocking pass lets the hero walk behind the foreground wall | otherwise none |
| `variants/S69_bellcap_glint.webp` | a small brass glint under the lowest spruce branches by the back wall | after Q11A |
| `variants/S69_bellcap_gone.webp` | the same spot with needles only | after Q11B, drawn over the glint |
| ambient layers | sparrows, ball, swallows, laundry (§ 5) | living-world agent |

### 6.2 Characters
| sheet | brief | size / sets |
|---|---|---|
| `ZUZANA95` | Zuzana at 40 in June 1995, **derived from the approved 7-year-old ZUZANA sheet**: the same round face (now an adult's, softer cheeks, a few faint smile lines), the same gentle, serious, attentive dark eyes under straight light-brown brows, small nose, small mouth with a slightly full lower lip; light-brown hair in a simple mid-1990s short cut with the side parting kept. A navy-blue short-sleeved cotton blouse with a small round white collar (a quiet echo of her 1962 dress), a light beige knee-length skirt, flat brown sandals; a stick of white chalk in one hand. **No jewellery, no rings, no glasses** (nothing that implies a life fact; glasses are Mira's mark), no print or text. Calm, kind expression that warms into a small smile. | adult 512 px; three-quarter view facing right (mirror for left), npc sheet idle / blink / talk_a / talk_b / gesture (points ahead and slightly up, as towards the wall panels), idle video loop; optional seated-on-bench set. Likeness anchor: the generated ZUZANA sheet; the private family photo only as for the child (ZUZANA.md § 10) |
| `KUBO` | a 7-year-old Slovak boy in June 1995, clearly a real child (not a toddler, not a teen): short dark-brown hair with a fringe, a scraped knee, a plain red T-shirt with one white band across the chest (no logo), navy shorts, white socks, plain canvas trainers without logos. Lively, a bit offended at his mute bell. | child 350 px (like ZUZANA 7); npc sheet idle / blink / talk_a / talk_b / gesture (taps the air with one finger as if tapping a bell), idle video |

### 6.3 Items (icons, `items/<ID>.webp`, style of the existing set)
`BELLCAP` (brass bike-bell cap, teeth inside, a scratch on the side) · and the four 1962 icons from ZUZANA.md § 4.1:
`BELL_MUTE` (brass hand bell, wooden handle, clapper wrapped in a white handkerchief), `ZUZA_SLIP` (ruled exercise-book
sheet with a child's capitals – illegible marks are fine, the look carries the text), `STRAP` (a narrow leather strip),
`BELL_FIXED` (the bell with its clapper hanging on a new loop).

### 6.4 Ivanka 1962 (Zuzana's part)
| asset | what |
|---|---|
| `variants/S37_hopscotch.webp` | chalk hopscotch on the gravel path right of Vera's bench (~90–420, 905–1000) |
| `variants/S37_zuzana_bell.webp`, `variants/S37_zuzana_bell_back.webp` | the class bell lying in the grass beside the hopscotch (two identical files: before and after Q10) |
| `variants/S37_zuzana_bell_gone.webp` | the same grass without the bell (after Q10A) |
| `variants/S32_chalk_arrow.webp` | chalk arrow and the word PARK on a stone by the well |
| `variants/S38_paper_boat.webp` | a paper boat stuck in the grass at the canal edge, ZUZKA in pencil (illegible is fine) |
| `cutscenes/EPILOGUE_10.webp` | end of June 1962: Zuzana rings the class bell at a generic village school door, first graders run out; hopscotch on the path (game composite, not the real Ivanka school) |
| ZUZANA actor set | exists (`src/game/assets/actors/ZUZANA/`) |

### 6.5 Other
| asset | what |
|---|---|
| `variants/S17_sign_shapes_only.webp` | the 1995 S17 sign with only the four shapes (rows of waves, strokes and pieces painted out); a local edit, no generation needed |
| `cutscenes/EPILOGUE_11.webp` | end of June 1995 in the S69 yard: children ride round the court, Kubo ringing; Zuzana by the bench, chalk in hand, smiling |
| sfx `school_handbell` | three short rings of a small brass hand bell (Q10D) |
| sfx `school_handbell_far` | the same, distant (S32/S38 ambience after Q10D) |
| sfx `bike_bell` | a child's bike bell, two rings (Q11C; S69 ambience after Q11C) |
| sfx `school_bell_far` | a 1990s electric school bell heard from across the yard (Q11C line 4) |
| `design-doc/assets.csv` | new rows for all of the above (orchestrator) |

---

## 7. Implementation order and checks

1. **Core** (in progress: `ContentOverlay.World.cs`, world_ext.json): load `world_ext` of the draft; answer the
   `core_requests` (speakers standing in the room for I10/B19 sequences; the STEFAN alias for Q10B; the B19 replay
   path; S69 in the 1995 Dúbravka region); epilogue order Q1–Q11.
2. **Blocking**: `data/blocking/S69.json` from § 1.1/1.3; S18 exit `S18.to_S69` on the side road; S37/S32/S38 prop
   positions; `check_blocking.py`.
3. **Art / audio**: § 6.
4. **Writers**: WRITING_METHOD steps 2–4 for the `zuzana_yard` chunk (GPT review of every block of this file and
   ZUZANA.md, decisions, story-order read-through), the glossary change § 3.4, the overrides § 3.3, VOICES.md entries,
   `writing_bundles.py` (S69 in C2).
5. **Checks**: `dotnet test src/LastBell.sln`, `check_strings`, `check_blocking`, `check_rewrite`, `--acceptance m1/m2/
   travel`, `--play-all` routes, headless line dump (`tools/qa_godot.py --headless …`). Main actions stay 94; the main
   route is the same except step 30's walk.

---

## 8. Rules (binding, see ZUZANA.md § 6.1 and § 10)

- Zuzana appears only here (15 June 1995, age 40) and in Ivanka 1962; never in 1982, 2020 or 2035.
- Nothing is invented about her life; living on the estate is game fiction for this scene; Kubo is not her child;
  she wears no ring or other sign of a life fact.
- No line foreshadows her future or death; time words stay inside the afternoon (*pätnásť dní do prázdnin*).
- She is not told about time travel and does not meet or name Adam's family.
- The family photo is a private likeness reference only; documents call it "family photo supplied by the owner".
