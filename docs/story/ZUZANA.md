# Zuzana – design for 1962 (Ivanka) and 1995 (Dúbravka)

Status: **final design, ready to implement** (2026-10-06, evening). History:
- 2026-10-06 morning (owner): Zuzana becomes an important character of the Ivanka chapter, Adam meets her playing in
  the manor park, and Ivanka moves from 1960 to 1962.
- 2026-10-06 afternoon (owner, docs/DECISIONS.md "Owner answers (2026-10-06, afternoon)"): no appearance of or
  reference to her later life in 2020 or 2035; the 2020 topic `MIRA20.extra Z` is dropped.
- **2026-10-06 evening (owner): "Zuzana in the game – do it, 1962 Ivanka and 1995 Dúbravka."** She appears in
  exactly two places: **June 1962, age 7**, in the manor park of Ivanka (S37), and **15 June 1995, age 40**, in the
  new room S69 *Sokolíkovský dvor* (spec of the room and of her 1995 part: [SOKOLIKOVA_YARD.md](SOKOLIKOVA_YARD.md)).
  The 1962 line that foreshadowed her future (*„Ja to neuvidím, ale aj tak."*) is replaced (section 4.2, Q10D).

Code, ids and this document are English; player-facing text is Slovak. Every Slovak line here is a **draft
(writing step 1)**. It still goes through design-doc/WRITING_METHOD.md steps 2–4 (GPT check, final control,
automatic checks) like every other text. The exact data for both eras is in
`docs/writing/out/content_v2_draft.json` (world overlay + dialogue overlay drafts).

---

## 0. Summary for the owner

- **Who she is.** In the game the only facts about her are the ones you gave: her name (Zuzana, no surname) and
  that she was born in 1955 in Ivanka pri Dunaji. Everything else is game fiction about two afternoons: one in
  June 1962 and one in June 1995. Nothing in the game says anything about her life between or after them: no job,
  family, partner, children, illness or later fate, and no line hints at her future.
- **1962 (age 7).** She plays hopscotch (*škôlka*) in the manor park next to Vera's bench, counts everything and
  finds her way around Ivanka by sounds and smells. At each point where the story needs it she sends Adam to
  the right person or place (Oto's workshop, the loose stage clamp, the leaking pump, Vera's blunt stylus, the
  carbon paper at the post office). She gives no story item and opens no door; the main logic does not change.
- **Her 1962 side quest Q10 "Prvý posledný zvonec" (4 steps).** Her class hand bell is mute. She wrote her own
  supply slip for the strict storekeeper Štefan, Adam ties a new leather loop, and she rings across the park.
  The ending is now a promise, not a farewell: *„A keď budete niekedy počuť zvoniť na konci roka, zamávajte. To
  je dohoda."* – *„Dohoda."*
- **1962 epilogue shot.** End of June 1962: she rings the class bell and the first graders run out into the
  holidays: *„Posledný zvonec! A v septembri zase prvý."*
- **1995 (age 40).** She is a resident of the Sokolíkova estate (game fiction) whom Adam meets in the walled
  courtyard *Sokolíkovský dvor*. She recognises him as the man from the Ivanka park in June 1962, because he has
  not aged: the shoes, and the carbon paper she once sent him for. Because the game visits 1995 **before** 1962,
  the first time they meet she remembers and he cannot; after Ivanka he can. She is warm, gentle and light.
- **Her 1995 role.** She helps with the main step "read the rhythm drawing" (B19), which moves from the school
  yard to a painted panel of the courtyard wall, and she is part of a small new side quest Q11 "Druhý posledný
  zvonec" (a neighbour's first-grader's bike bell). It ends with the school bell ringing across the yard and
  the two of them keeping the 1962 *dohoda*: they wave. Her epilogue shot (end of June 1995) repeats her
  1962 line: *„Posledný zvonec. A v septembri zase prvý."*
- **Never** in 1982, 2020 or 2035: no appearance, no mention, no picture.
- **Privacy.** The family photo is only a private likeness reference for the generated character (section 10).

Two small choices that work either way: adults in 1962 call her by the diminutive **Zuzka** (her label stays
**Zuzana**; in 1995 nobody says Zuzka: the yard child says *teta Zuzana*); and in 1962 she
is a **neighbour of young Mira**, two houses away, not related to Adam's family.

---

## 1. Who Zuzana is

| | 1962 | 1995 |
|---|---|---|
| id / speaker | `ZUZANA` (one era, no suffix, like `BERTA`) | `ZUZANA95` (era suffix, like `MIRA95`) |
| name shown | **Zuzana** (no surname, ever). Adults may say *Zuzka*. | **Zuzana** |
| age | 7 on 6 June 1962, finishing first grade; the school year ends in **24 days** (she counts them) | 40 on 15 June 1995; the school year ends in **15 days** (she still counts) |
| where | manor park S37, front gravel path near Vera's bench | courtyard S69, by the green bench at the court |
| what she does | plays hopscotch she drew in chalk, or crouches and draws | has chalked a hopscotch on the court for the yard children; holds a stick of chalk |
| character | lively once she trusts you, curious, very observant; a serious little face that warms up slowly | calm, kind, quietly funny; the same attentive eyes; accepts the inexplicable without prying (*„Niektoré veci sú krajšie bez návodu."*) |
| how she is funny | kid logic and literal words; **counts everything** | still counts everything (32 wall panels, balls over the wall, days to the holidays); dry understatement |
| running gag | directions by **sound and smell** | counting; the *„iba do štvorky, dospelí ďalej padajú"* hopscotch rule |
| address | Zuzana → Adam **vy**; Adam → Zuzana **ty**. She says *teta Mira, teta Vera, teta Lída, teta Berta, ujo Oto, ujo Štefan, ujo Rudo, ujo Božo*, *pán Baran* | Zuzana → Adam **vy**; Adam → Zuzana **vy**; she tykne the yard child Kubo, he says *teta Zuzana* |
| knows | the park, the square, the canal bank, the culture hall (from the doorway), the post office, the farm yard (children are kept out) | the courtyard, the yard children, who painted the wall panel (the school club with "a lady with a tape recorder"), how many panels the wall has |
| does not | enter Oto's workshop, S39 or the attic, handle tools or ZVON, keep secrets from adults, learn that Adam comes from the future | get an explanation (Adam gives none), mention anything about her own life, meet or name anyone of Adam's family |
| era words | *prvá trieda, vysvedčenie, učiteľka, prázdniny, krieda, škôlka, švihadlo, mamka*; no *súdruh/súdružka* | plain 1995 Bratislava speech, no slang |

Voice examples (VOICES.md format):
- 1962: `Ešte dvadsaťštyri dní a mám za sebou celú prvú triedu.`
- 1962: `Ujo Oto? Toho nájdete po zvuku. Tam, kde to tiká zo všetkých strán.`
- 1995: `Múr má tridsaťdva panelov. Nákres je na troch vpravo, hneď pri priechode.`
- 1995: `Nebojte sa, nebudem sa pýtať, ako to robíte. Niektoré veci sú krajšie bez návodu.`

---

## 2. First meeting in 1962 – manor park S37

**Staging.** Her NPC hotspot `S37.ZUZANA` is always visible in S37 and never moves, so hints can always send the
player to the park. She plays to the right of Vera's bench (Vera feet ~[600, 800]) on the front gravel path, away
from the spawn point (1150, 930) and the bird bowl.
- Template blocking (final values from the blocking pass and `tools/check_blocking.py`): child feet ~[330, 885],
  scale s(885) ≈ 0.74, so the 350 px figure is drawn ~258 px tall. Rect `[270, 625, 125, 262]`, interaction point
  `[455, 905]`, label anchor `[332, 615]`; actor variant `playing` (art set exists: `src/game/assets/actors/ZUZANA/`).
- The hopscotch is a ground decal: hotspot `S37.hopscotch` „Škôlka kriedou", rect `[90, 905, 330, 95]`,
  interaction point `[480, 960]`; atmospheric (a click looks).
- The class bell lies on the grass beside the hopscotch until Q10A and again after Q10D: layer
  `variants/S37_zuzana_bell.webp` after B22 (always in 1962), covered by the grass patch
  `S37_zuzana_bell_gone` after Q10A and shown again by `S37_zuzana_bell_back` after Q10D (layers draw in list order).
  While Adam carries it, the grass is empty.

**Looks**
- `look.S37.ZUZANA`: `Malá Zuzana skáče škôlku a každé políčko nahlas odpočíta. Vedľa v tráve leží zvonček, ktorý ani raz necinkol.`
  - after Q10A: `Zuzana kreslí kriedou ďalšiu škôlku, pre istotu aj s vchodom. Občas sa pozrie, či jej nesiem zvonček.`
  - after Q10D: `Zuzana skáče škôlku a po každom desiatom skoku zazvoní. Vera už ani nedvíha hlavu.`
- `look.S37.hopscotch`: `Škôlka nakreslená kriedou na chodníku: osem políčok a hore polkruh. Čiary má rovnejšie ako ja na nákresoch.`

**Intro topic `ZUZANA.extra 1` „Kto si?"** (repeatable, Adam speaks first, always offered)
```
ADAM:   Ahoj. Ty hráš škôlku?
ZUZANA: Hrám. Ale do škôlky už nechodím. Chodím do prvej triedy.
ZUZANA: Ešte dvadsaťštyri dní a mám za sebou celú prvú triedu.
ADAM:   Ty si to rátaš?
ZUZANA: Ja si rátam všetko. Políčka, schody aj to, koľkokrát ujo Rudo zabudne text.
ADAM:   Ja som Adam.
ZUZANA: Ja som Zuzana. Vy nie ste odtiaľto. Vy zniete inak.
```

---

## 3. Her part in the 1962 main story (no change in logic)

The main route stays exactly `B22 → I01 … I17` (walkthrough.json `main_route`, 94 main actions). Neither layer
below adds a condition, item or step.

### 3.1 Her pointer topics on `S37.ZUZANA`

Each appears when the story needs that information and disappears once the step is done. The v1 overlay field
`excluded_done` does exactly that (the earlier `hide_after` proposal is not needed). They give only the
direction or the place (hint level 1–2), never the solution or an item.

| topic id | label (≤ 28) | requires_done | excluded_done | serves | points to |
|---|---|---|---|---|---|
| `ZUZANA.extra 2` | `Kde je Otova dielňa?` | – | `I01` | I01 | the route S32 → S35 → S36 |
| `ZUZANA.extra 3` | `Kto má dierovač?` | `I01` | `I03` | I03 | Lída in the hall S34 and the loose clamp |
| `ZUZANA.extra 4` | `Čo je s pumpou?` | `I01` | `I06` | I06 | the pump at the booth S38 needs a new cuff |
| `ZUZANA.extra 5` | `Poznáš Miru?` | – | – | colour | Mira is her neighbour; the booth by the canal lights up |
| `ZUZANA.extra 6` | `Holub pri miske` | – | `Q6C` | Q6 | the pigeon wants its own feed (Štefan) |
| `ZUZANA.extra 7` | `Ujo Rudo` | – | `Q7C` | Q7 | she knows only the first line of the play |
| `ZUZANA.extra 8` | `Prázdniny` | `I17` | – | colour | the canal, the trains |

Drafts (all lines in `content_v2_draft.json` → `topics`):

`ZUZANA.extra 2` „Kde je Otova dielňa?"
```
ADAM:   Nevieš, kde má dielňu pán Bielik?
ZUZANA: Ujo Oto? Toho nájdete po zvuku.
ZUZANA: Z námestia choďte tam, kde vonia koža. To je dvor, tam je ujo Štefan.
ZUZANA: A za ním tam, kde to tiká zo všetkých strán. To je ujo Oto.
ADAM:   Vôňa kože a potom tikanie. Zapamätám si to.
ZUZANA: Hlavne nechoďte tam, kde to kotkodáka. Tam sú len sliepky.
```
`ZUZANA.extra 3` „Kto má dierovač?"
```
ADAM:   Nevieš, kde nájdem pani Lídu?
ZUZANA: Teta Lída je v sále. Tam, kde niekto kričí „Žiaden strach, miláčik!"
ZUZANA: Ten látkový les sa im celý deň kýve. Má voľnú svorku, ja som to videla.
ADAM:   A povedala si im to?
ZUZANA: Povedala. Ale skrutkovač mi nikto nepožičia, lebo som malá.
ADAM:   Ja jeden mám.
ZUZANA: Tak vám to skôr dovolia.
```
`ZUZANA.extra 4` „Čo je s pumpou?"
```
ADAM:   Tá pumpa pri búdke za parkom…
ZUZANA: Kvapká. Ráno som jej narátala sto kvapiek, potom som prestala.
ZUZANA: Teta Mira hovorí, že jej treba novú manžetu.
ZUZANA: Ja som myslela, že manžeta je na košeli. Pumpa predsa košeľu nemá.
ADAM:   Táto je kožená. Drží vodu tam, kde má byť.
ZUZANA: Tak je to taký opasok pre vodu.
```
`ZUZANA.extra 5` „Poznáš Miru?"
```
ADAM:   Poznáš Miru Hruškovú?
ZUZANA: Teta Mira je naša suseda. Cez dva domy.
ZUZANA: Keď v búdke pri kanáli svieti, mamka povie: Mira zas meria čas.
ZUZANA: Neviem, kam ho potom dáva. Asi do zošita.
ADAM:   Niekam, kde sa nestratí. Na to je veľmi poriadna.
ZUZANA: To je. Mne raz našla gombík, čo som stratila pred rokom.
```
`ZUZANA.extra 6` „Holub pri miske" (fixed: Štefan gives Béla's feed **without** a slip, Q6B, so she no longer
says he gives only on a slip)
```
ZUZANA: Ten holub pri miske je poštový. Má na nohe krúžok.
ZUZANA: Dala som mu chlieb, ale nechcel. Asi je zvyknutý na lepšie.
ADAM:   Možno chce svoje vlastné krmivo.
ZUZANA: To má ujo Štefan na dvore. Mne nedá, ja som malá. Vám dá.
```
`ZUZANA.extra 7` „Ujo Rudo"
```
ZUZANA: Ja viem prvú vetu od uja Ruda. Žiaden strach, miláčik!
ADAM:   A druhú?
ZUZANA: Druhú nevie ani on. Je v scenári a scenár sa stratil.
ZUZANA: Teta Lída hovorí, že ak sa nenájde, bude to veľmi krátke divadlo.
```
`ZUZANA.extra 8` „Prázdniny"
```
ADAM:   Čo budeš robiť cez prázdniny?
ZUZANA: Budem sa pozerať na kanál. Kúpať sa v ňom nesmieme. Mamka hovorí, že voda nemá zábradlie.
ZUZANA: A budem chodiť na zastávku. Ujo Božo mi dovolí kývať vlakom do Bratislavy.
ADAM:   Všetkým?
ZUZANA: Iba tým, čo idú načas. Ostatným kýva on sám. Nahnevane.
```

### 3.2 Lines inside existing 1962 actions (overlay `sequences`)

New keys use the suffix **`zNN`**, so they never collide with the `xNN` keys of the writing passes. Existing keys
keep their text, speaker and order (WRITING_METHOD § 0). **Merge rule:** an exchange is extended at most once, so
when the C3 (1962) writing pass also extends I03, I09, I10, I14 or `BOZO.ambient 1`, both sets of new lines go
into one sequence entry.

| action | room | where | what they add |
|---|---|---|---|
| **I10** (Vera lends the stylus) | S37 | z01 after `.001`; z02–z06 after `.004` | where Vera keeps the blunt stylus; **points to the carbon paper at the post office (I14)**. Needs core request (a): a speaker rule for NPCs standing in the room, or I10 guest `ZUZANA` |
| **I09** (Mira explains) | S39 | z01–z03 after `.008` | Mira: the stylus is with Vera in the park, and the little neighbour there can help |
| **I03** (stage clamp → punch) | S34 | z01–z03 after `.001` | Lída: Zuzka noticed that the flat wobbles on one screw |
| **I14** (carbon paper) | S33 | z01–z03 after `.001` | Alojz knows her from the counter |
| `BOZO.ambient 1` | S31 | z01–z03 after `.001` | Božo: if you get lost, ask little Zuzka in the park |
| new topic `BERTA.extra Z` „Kto je tá malá?" | S32 | – | the village *čí je* gag |
| new topic `MIRA60.extra Z` „Suseda Zuzka" (requires `I08`) | S39 | – | Zuzka asked Mira where she puts the time she measures |

I10 (full play order; existing keys in brackets):
```
[action.I10.001] ADAM:   Mira ma posiela za vami. Robím odtlačok kalibračnej platne a potrebujem niečo tupé.
 action.I10.z01  ZUZANA: Tupé má teta Vera v puzdre. Ostré si nechá pre seba.
[action.I10.002] VERA60: Tak si vezmite moje rydlo. Papier najprv pritlačte, potom obtiahnite hrany. Do platne neryte.
[action.I10.003] ADAM:   Rydlo, ktorým sa nemá ryť. To si zapamätám.
[action.I10.004] VERA60: Preto je tupé. Zapamätá si to za vás.
 action.I10.z02  ZUZANA: A čo ešte potrebujete?
 action.I10.z03  ADAM:   Jeden list mám mať dvakrát, oba presne rovnaké.
 action.I10.z04  ZUZANA: Na to má pán Baran na pošte čierny papier. Píšete hore a dole sa to napíše samo.
 action.I10.z05  VERA60: Uhlový papier. Zuzka, ty by si mohla pracovať na úrade.
 action.I10.z06  ZUZANA: Nemohla. Ja chodím do školy.
```
I10.z04 is the line she quotes back to Adam in 1995 (SOKOLIKOVA_YARD.md § 2.1): I10 is on the main route, so
every player hears it.

I09 (after `.008`; true on every route: the first way to the booth leads through the park, where she always plays):
```
 action.I09.z01  MIRA60: Vera kreslí v parku. Pri nej sa hrá naša malá suseda Zuzka.
 action.I09.z02  ADAM:   Tú so škôlkou? Videl som ju cestou sem.
 action.I09.z03  MIRA60: Tak počúvaj, čo ti povie. V Ivanke sa ešte nestratila.
```
I03 (after `.001`):
```
 action.I03.z01  LIDA:   Presne to mi včera hovorila malá Zuzka. Že náš les sa kýve na jednej skrutke.
 action.I03.z02  ADAM:   Mala pravdu.
 action.I03.z03  LIDA:   Tá má pravdu skoro vždy. Len skrutkovač nemá.
```
I14 (after `.001`):
```
 action.I14.z01  ALOJZ:  Len opatrne, prosím. Farbí aj prsty. Malá Zuzka si ním u mňa obkresľuje ruky.
 action.I14.z02  ADAM:   Tá malá so škôlkou v parku?
 action.I14.z03  ALOJZ:  Tá. Chodí si sem po známky. Kupuje iba tie, ktoré sa jej páčia.
```
BOZO.ambient 1 (after `.001`):
```
 topic.BOZO.ambient 1.z01  BOZO: A keby ste predsa zablúdili, v parku skáče škôlku malá Zuzka.
 topic.BOZO.ambient 1.z02  ADAM: Ona pozná cestu?
 topic.BOZO.ambient 1.z03  BOZO: Ona pozná v Ivanke každý kút. Lepšie ako ja cestovný poriadok, a ten viem naspamäť.
```
`BERTA.extra Z` „Kto je tá malá?" (repeatable)
```
ADAM:  Kto je to malé dievča v parku?
BERTA: Zuzka. Ráno v škole, poobede v parku, večer pri kanáli, kým ju mamka nezavolá.
ADAM:  A čia je?
BERTA: Predsa mamkina. Tu je každý niečí, mladý pán.
ADAM:  Čí som ja, zatiaľ nikto neuhádol.
BERTA: Zuzka to zistí prvá. Uvidíte.
```
`MIRA60.extra Z` „Suseda Zuzka" (repeatable, requires `I08`)
```
ADAM:   Vaša suseda Zuzka je všade, kam prídem.
MIRA60: To robí každému. Aj tým, čo nevedia, že potrebujú sprievod.
MIRA60: Včera sa ma pýtala, kam dávam ten čas, čo meriam.
ADAM:   A čo ste jej povedali?
MIRA60: Pravdu. Že ho zapisujem, aby sa nestratil.
```

**Guarantees.** No inserted line or topic is in `gives`, `consumes` or `requires_*`. No main action gets a new
condition. Removing the overlay entries restores the handoff exchanges. Protected facts stay in their keys
(I09.005 still names the attic and Vera; I14.001 still names the counter).

---

## 4. Side quest Q10 „Prvý posledný zvonec" (1962)

**Story.** Zuzana's teacher has picked her to ring the class hand bell on the last day of the school year,
"because she has the steadiest hand". The bell is mute: the old leather loop that holds the clapper (*srdce*) has
torn; the clapper is wrapped in her handkerchief. Oto was to fix it, but he "has four alarm clocks today and no
free hand", and children are kept out of the farm yard. So she wrote a supply slip for Štefan, as the grown-ups
do. Adam takes the bell, Štefan honours the child's slip, Adam ties a new loop, and she rings in the park.

4 steps, available from the first visit to Ivanka, no main action needs it and it needs none; it can also be
finished in the postgame.

### 4.1 Items (4 new)

| id | name | look | origin | purpose | icon |
|---|---|---|---|---|---|
| `BELL_MUTE` | Triedny zvonček bez pútka | Mosadzný ručný zvonček s drevenou rúčkou. Srdce je zabalené v Zuzaninej vreckovke, pútko je roztrhnuté. | Q10A | Zavesiť srdce na nové kožené pútko. | `items/BELL_MUTE.webp` |
| `ZUZA_SLIP` | Zuzanin lístok | List z linajkového zošita, tlačeným písmom: LÍSTOK. PROSÍM JEDEN KÚSOK KOŽE NA ZVONČEK. ZUZANA, 1. TRIEDA. | Q10A | Podať Štefanovi v hospodárskom dvore. | `items/ZUZA_SLIP.webp` |
| `STRAP` | Kožený odrezok | Úzky pásik kože zo Štefanových odrezkov. Na pútko akurát, ani o kúsok viac. | Q10B | Zavesiť naň srdce zvončeka. | `items/STRAP.webp` |
| `BELL_FIXED` | Opravený triedny zvonček | Srdce visí na novom pútku, uzol je schovaný vnútri. Zvoní čisto. | Q10C | Vrátiť Zuzane do parku. | `items/BELL_FIXED.webp` |

All `disposition: retain`. `STRAP` is not `LEATHER` (*Predrezaná kožená manžeta*): no recipe connects them and its
hover over the pump shows nothing (resolver: only defined pairs).

### 4.2 Actions (all `quest: "Q10"`, `once`, no puzzle or cutscene, atomic commit policy)

| id | room | target | kind | requires_items | selected | gives | consumes | animation / sfx |
|---|---|---|---|---|---|---|---|---|
| `Q10A` | S37 | `S37.ZUZANA` | topic | – | – | `BELL_MUTE`, `ZUZA_SLIP` | – | talk / item_soft |
| `Q10B` | S35 | `S35.SKLAD` | click | `ZUZA_SLIP` | `ZUZA_SLIP` | `STRAP` | `ZUZA_SLIP` | show_item / paper |
| `Q10C` | inventory | `BELL_MUTE` | combine (symmetric) | `BELL_MUTE`, `STRAP`, `TOOLS` | `STRAP` | `BELL_FIXED` | `BELL_MUTE`, `STRAP` | inventory_combine / item_soft |
| `Q10D` | S37 | `S37.ZUZANA` | click | `BELL_FIXED` | `BELL_FIXED` | – | `BELL_FIXED` | show_item / **school_handbell** (new) |

S35.SKLAD already has I02 (selected `SUPPLYSLIP`) and Q6B (topic): Q10B is told apart by `selected_item`.
`TOOLS` is never consumed, so Q10C is always possible. Q10D has the staging guest speaker `VERA60` (she speaks
from her bench).

| id | label | objective (= journal) |
|---|---|---|
| Q10A | `Zvonček, ktorý nezvoní` (topic label) | `Vyzdvihni u Štefana v hospodárskom dvore kožený odrezok na Zuzanin lístok.` |
| Q10B | `Podať Štefanovi Zuzanin lístok` | `Zaves srdce zvončeka na nové pútko.` |
| Q10C | `Zavesiť srdce zvončeka na nové pútko` | `Vráť opravený zvonček Zuzane do parku.` |
| Q10D | `Vrátiť Zuzane opravený zvonček` | journal: `Zuzana skúšobne zazvonila celému parku.` |

Q10A
```
ZUZANA: Toto je zvonček našej triedy. Pozrite. Nič.
ADAM:   Chýba mu srdce.
ZUZANA: Nechýba. Mám ho vo vreckovke. Len sa mu roztrhlo pútko.
ZUZANA: Na konci roka mám zvoniť ja. Učiteľka povedala, že mám najistejšiu ruku.
ADAM:   A kto ho mal opraviť?
ZUZANA: Ujo Oto. Ale ujo Oto má dnes štyri budíky a ani jednu voľnú ruku.
ZUZANA: Kožu má ujo Štefan. Ten dáva iba na lístok. Tak som mu lístok napísala.
ADAM:   „Lístok. Prosím jeden kúsok kože na zvonček. Zuzana, prvá trieda."
ZUZANA: Aj podpis tam je. Ujo Štefan vraví, že bez podpisu nič.
ADAM:   Kožu prinesiem a pútko spravím. Požičiaš mi zvonček?
ZUZANA: Požičiam. Ale opatrne, je triedny, nie môj.
```
Q10B
```
STEFAN: Lístok. „Prosím jeden kúsok kože na zvonček."
STEFAN: Podpis: Zuzana, prvá trieda.
ADAM:   Platí?
STEFAN: Lístok, podpis, materiál. Všetko sedí. Nikde nepíše, že podpis musí byť dospelý.
STEFAN: Úzky odrezok z remeňa. Na pútko akurát. Lístok si nechávam.
ADAM:   Do evidencie?
STEFAN: Na stenu. Taký pekný lístok som tu ešte nemal.
```
Q10C
```
ADAM:   Pútko cez uško, srdce na miesto, uzol dovnútra, aby sa nešúchal.
ADAM:   Skúšobne cinknem do dlane. Zvoní.
```
Q10D (**changed ending**: the foreshadowing line *„Ja to neuvidím, ale aj tak."* and Adam's *„Zamávam."* are
replaced by a promise that pays off in 1995)
```
ZUZANA: Zvoní? Naozaj?
ADAM:   Skús. Ale pomaly, je triedny.
ZUZANA: Počuli ste? Takto bude znieť koniec roka.
VERA60: Zuzka, teraz celý park vie, že sa skončila hodina.
ZUZANA: Ešte sa neskončila. Ešte dvadsaťštyri dní. Toto bola skúška.
ADAM:   Skúška vyšla.
ZUZANA: Ďakujem. Môžete si skočiť škôlku. Ale iba do štvorky, dospelí ďalej padajú.
ZUZANA: A keď budete niekedy počuť zvoniť na konci roka, zamávajte. To je dohoda.
ADAM:   Dohoda.
```
The ring itself is the action sfx `school_handbell` (three short rings) before *„Počuli ste?"*; the next line
says what happened, so no meaning lives only in the sound. Three phrases return in 1995 (Q11C, topics):
*„Toto je skúška." / „Skúška vyšla."*, *„iba do štvorky"* and the *dohoda*.

### 4.3 Quest record

```json
{ "id": "Q10", "title": "Prvý posledný zvonec", "type": "side",
  "actions": ["Q10A", "Q10B", "Q10C", "Q10D"], "completion": "Q10D", "missable": false,
  "goal": "Oprav Zuzanin triedny zvonček, aby mohla na konci roka zvoniť.",
  "reward": "Zuzana so zvončekom a jej kriedová škôlka v Adamovom albume.",
  "hints": [
    "Zuzana v parku pri kaštieli má zvonček, ktorý nezvoní.",
    "Srdce treba zavesiť na nové kožené pútko. Kožené odrezky má Štefan v hospodárskom dvore a vydáva ich iba na lístok.",
    "Zuzana v parku, téma zvonček → Zuzanin lístok Štefanovi → v brašni odrezok so zvončekom → opravený zvonček Zuzane." ] }
```
(The goal is now imperative, STYLE_GUIDE § 6.8.) Step hints (`ui.csv`): `ui.hint_step.Q10A` *Porozprávaj sa so
Zuzanou v parku o zvončeku, ktorý nezvoní.* · `Q10B` *Zuzanin lístok podaj Štefanovi v hospodárskom dvore.* ·
`Q10C` *V brašni spoj kožený odrezok so zvončekom.* · `Q10D` *Opravený zvonček použi na Zuzanu v parku.*
Album: on Q10D the album gets the epilogue still and the reward text (the reward is automatic).

---

## 5. Her traces elsewhere in Ivanka (1962 only)

| room | what | data |
|---|---|---|
| S32 square | chalk arrow on a stone by the well, PARK written under it | prop `S32.chalk_arrow` „Kriedová šípka": `Na kameni pri studni je kriedou šípka a pod ňou PARK. Niekto v Ivanke robí orientačné tabule.` |
| S38 canal bank | a paper boat stuck in the grass at the edge of the Šúrsky kanál | prop `S38.paper_boat` „Papierová loďka": `Papierová loďka uviazla v tráve pri kanáli. Na boku má ceruzkou ZUZKA. Ďalej ju nepustili, správne.` |
| S32, S38 after Q10D | a distant hand bell now and then | ambient sound layer `school_handbell_far`, after `Q10D`, at most once per ~40 s, no gameplay meaning |
| S34, S33 | Lída, Rudo and Alojz talk about her | text only (I03, I14 lines; a Rudo extra-topic idea: *Zuzka vie moju prvú vetu lepšie ako ja*) |

Props are purely atmospheric (left click = look), shown by Space, ≥ 44 × 44 px. Template rects:
`S32.chalk_arrow` [250, 905, 140, 70], `S38.paper_boat` [1340, 840, 120, 60]; the blocking pass places them.

---

## 6. Payoff and the two eras

**Epilogue `epilogue.10` (Q10, after Q10D; quest order, 5–7 s):**
```json
{ "quest": "Q10", "after": "Q10D",
  "shot": "Koniec júna 1962. Zuzana zvoní triednym zvončekom a prváci vybiehajú na prázdniny.",
  "line": "ZUZANA: Posledný zvonec! A v septembri zase prvý." }
```
Art `EPILOGUE_10`: a generic village school door (a game composite, not a claim about the real Ivanka school), the
hopscotch chalked on the path; likeness from the generated ZUZANA sheet, not from the photo directly.

**1995.** The 1962 thread closes in 1995 (SOKOLIKOVA_YARD.md): she recognises Adam (topic `ZUZANA95.extra 1/2`),
tells him the bell rang on the last day (topic `ZUZANA95.extra 3`, after Q10D), keeps the *dohoda* in Q11C and
has her own epilogue shot `epilogue.11` with the same line she said at seven. `epilogue_rules`: `Q1–Q9` →
`Q1–Q11`.

### 6.1 Rules for every later writer, artist and coder

- Zuzana appears **only** in June 1962 (age 7, Ivanka: S37 and her traces in S32/S38) and on 15 June 1995 (age
  40, S69). No appearance, mention, look, journal entry, hint or picture in 1982, 2020 or 2035. The dropped 2020
  topic `MIRA20.extra Z` stays dropped.
- The only facts are her name (Zuzana, no surname) and her birth in 1955 in Ivanka pri Dunaji. Everything else is
  fiction about those two afternoons. Living on the Sokolíkova estate in 1995 is game fiction for that scene.
- **Nothing about her life is invented**: no job, family, partner, children, illness or later fate, no address
  details. In 1962 she has a *mamka* (a seven-year-old in the story needs one); in 1995 nobody of her family is
  mentioned. The yard child Kubo is a neighbour's child, never hers.
- **No foreshadowing**: no line may hint at her future or death (*neuvidím, kým tu budem, raz už nebudem, na
  pamiatku* and similar are banned for her and about her). Lines about time stay inside the two afternoons.
- She never learns from Adam that he travels in time; in 1995 she notices that he has not aged and chooses not to
  ask. She does not meet or name anyone of Adam's family in 1995, and she is not "the reason" for anything in the
  main story.
- Nothing about her real life is written into the repository.

---

## 7. Consistency with the cast

| character | relation to Zuzana | note |
|---|---|---|
| Mira (`MIRA60`, 22 in 1962) | neighbour, two houses away; *teta Mira* | Mira tykne Zuzke |
| Oto (`OTO`, 46) | the village fixer; *ujo Oto* | children are not allowed in his workshop; he was to fix the bell |
| Vera (`VERA60`, 24) | Zuzka plays next to her bench; *teta Vera* | dry and fond of her (Q10D, I10) |
| Berta (`BERTA`, 70) | *teta Berta* | *predsa mamkina* |
| Rudo (`RUDO`, 36) | *ujo Rudo* | she knows his first line, not the second |
| Lída (`LIDA`, 45) | *teta Lída* | I03 lines |
| Alojz (`POSTA`/`ALOJZ`, 56) | *pán Baran* | she buys stamps that look nice (I14) |
| Štefan (`SKLAD`/`STEFAN`, 53) | *ujo Štefan* | keeps children out of the yard; honours her slip (Q10B) |
| Božo (`BOZO`, 47) | *ujo Božo* | lets her wave at the trains |
| Adam (35 in every era) | 1962: a stranger "who sounds different"; 1995: the man who did not age | never tells her he is from the future |
| Kubo (`KUBO`, 7, 1995) | a first-grader from a neighbouring entrance of the estate; *teta Zuzana* | not her child |
| Zita (`ZITA`, 1995) | none spoken; the green bench in S69 is the one Zita's ambient line complains about | text callback only |
| Tóno, Jana, Lea, Viktor, Mira 1995/2020 | none | no scene with Zuzana; in 1995 she only mentions "a lady from the school club with a tape recorder" who painted the wall |

---

## 8. The 1962 date shift – done

The shift of Ivanka to **6 June 1962** (display only; era id 1960, ids and saves unchanged) is implemented:
docs/DECISIONS.md "Ivanka is shown as June 1962", ISSUES TEXT-IVANKA-1962, 36 rewritten keys in
`docs/writing/out/ivanka1962.csv`, `era.<year>.year` keys, the 1962 facts in GLOSSARY.md § 6.3 / glossary.json,
and the painted dates (form icons, S33 calendar, CS03_1, EPILOGUE_6). Ages in June 1962: Mira 22, Vera 24, Oto 46,
other Ivanka people +2 where a text states an age; spans 58 years to 2020, 73 to 2035, 13 years Adam–Mira.
Writing drafts that still carry 1960 texts (`C2.csv`, `C3.csv`, `C4.csv`) must keep the 1962 values on the next
merge.

---

## 9. Implementation checklist

All data: `docs/writing/out/content_v2_draft.json`. Its `world_ext` part follows the Core agent's world overlay
(`src/game/data/content_ext/world_ext.json`, format `lastbell.world_ext`, `src/LastBell.Core/Content/ContentOverlay.World.cs`);
its `dialogue_ext` part is the dialogue overlay v1 shape; `core_requests` lists the three things the schema does not
cover yet.

1. `world_ext.characters`: `ZUZANA` (age 7, room S37), `ZUZANA95` (age 40, S69), `KUBO` (age 7, S69); names
   `Zuzana`, `Zuzana`, `Kubo` (rooms are derived from the NPC hotspots).
2. `world_ext.hotspots` (existing rooms): `S37.ZUZANA` (npc), `S37.hopscotch`, `S32.chalk_arrow`, `S38.paper_boat`.
   `world_ext.rooms`: S69 with its hotspots and exit (SOKOLIKOVA_YARD.md).
3. `world_ext.items`: BELL_MUTE, ZUZA_SLIP, STRAP, BELL_FIXED (1962), BELLCAP (1995); keys `item.<id>` etc. are derived.
4. `world_ext.actions`: Q10A–Q10D, Q11A–Q11C with lines (`{key, speaker, sk}`, keys `action.<id>.NNN`), journal,
   objective, `hint_step`, staging guest speakers (Q10D: VERA60; Q11A: ZUZANA95; Q11C: ZUZANA95, KUBO).
5. `world_ext.relocations`: B19 → `S69.rhythm` (`retire_hotspot: false`, `hint_step`).
6. `world_ext.quests` Q10, Q11; `world_ext.epilogue` shots for Q10 and Q11 (`epilogue_rules` text: Q1–Q11).
7. `dialogue_ext.sequences` / `topic_extensions`: I10, I09, I03, I14, B19, `BOZO.ambient 1`. `dialogue_ext.topics`:
   ZUZANA.extra 1–8, BERTA.extra Z, MIRA60.extra Z (1962); ZUZANA95.extra 1–6, KUBO.extra 1–2 (1995).
8. `world_ext.visual_variant_layers` (only `after`, drawn in list order): S37 hopscotch and bell after B22 (= always in
   1962), the "bell gone" grass patch after Q10A, the bell again after Q10D; S32 chalk arrow and S38 paper boat after
   B22; S69 cap glint after Q11A, "cap gone" patch after Q11B; S17 "shapes only" sign patch after G11 (= always in
   1995). Ambient sounds (audio data, not world data): `school_handbell_far` in S32/S38 after Q10D, `bike_bell` in
   S69 after Q11C.
9. `core_requests`: (a) Zuzana's lines in the existing actions I10 and B19 need a speaker rule for NPCs standing in
   the room (or a staging patch); (b) Q10B's speaker alias STEFAN for the hotspot S35.SKLAD; (c) the walkthrough
   replay of the relocated B19 (S11 → S18 → S69).
10. Glossary and voices (writers, same commit as the merge): GLOSSARY.md § 2 rows
   `ZUZANA | Zuzana | Zuzana, Zuzka (1962 adults) | Zuzany, Zuzane, Zuzanu; Zuzanin lístok; no surname`,
   `ZUZANA95 | Zuzana | Zuzana, teta Zuzana (Kubo) | as above`, `KUBO | Kubo | Kubo, Kubko | Kuba, Kubovi, Kubom;
   Kubov bicykel`; glossary.json names; VOICES.md ty/vy rows (Zuzana 1962: vy → Adam, Adam → ty; Zuzana 1995: vy
   both ways; Kubo: vy → Adam, Adam → ty) and the ZUZANA / ZUZANA95 / KUBO entries from section 1 and
   SOKOLIKOVA_YARD.md § 2.
11. Counts after both parts: rooms 69, characters 53, items 83, side quests 11, side actions 40, hotspots 254
    (Core recounts ambient props), main actions **94**. Update `stats` and every test or validator that counts.
12. Checks: the main route replay is identical except that step 30 (B19) walks S11 → S18 → S69; the side-quest
    run includes Q10 and Q11, also after the credits; no main `requires_*` or `consumes` names a Q10/Q11 action or
    item; `check_strings`, `check_rewrite` (with the glossary change of SOKOLIKOVA_YARD.md § 3.4), `check_blocking`,
    `dotnet test`, acceptance m1/m2/travel, `--play-all` and the headless line dump all pass.

---

## 10. Privacy rules for this character

- `art/source/owner_refs/family_zuzana.jpg` stays private and git-ignored. It is read only by the art tool as a
  likeness reference, sent as a data URI, and never copied into `art/characters/`, the build, docs or any
  published page. The same applies to the 40-year-old sheet: its likeness anchor is the approved generated ZUZANA
  sheet, plus the private photo only in the same way.
- Documents, sidecars and credits call it only **"family photo supplied by the owner"**. Do not describe it.
- Game text uses only the owner's facts (Zuzana, born 1955 in Ivanka pri Dunaji). Everything else is presented as
  fiction about June 1962 and June 1995. Nothing is said about her life outside those two afternoons.
