# Zuzana – design for the Ivanka chapter (1962)

Status: design, ready to implement (2026-10-06). Owner request of 2026-10-06: Zuzana becomes an important
character of the Ivanka chapter, Adam meets her playing in the manor park, and Ivanka moves from 1960 to 1962.
Updated 2026-10-06 (afternoon) by the owner's decision (docs/DECISIONS.md "Owner answers (2026-10-06, afternoon)"):
**Zuzana appears only in 1962**; a possible appearance in Dúbravka 1995 waits for the owner's details (section 6.1);
there is no appearance of or reference to her later life in 2020 or 2035, and the 2020 topic `MIRA20.extra Z` is
dropped.
Code, ids and this document are English; player-facing text is Slovak. Every Slovak line in this file is a
**draft (writing step 1)**. It still goes through WRITING_METHOD.md steps 2–4 (GPT check, final control,
automatic checks) like every other text.

---

## 0. Summary for the owner

**What changes**

- **Ivanka is now 6 June 1962** (it was 6 June 1960). The day stays 6 June, so it still matches Jasná on
  6 June 2035. Mira is 22, Oto 46, and every visible date, age and number of years changes to match
  (section 8). The internal ids stay as they are (era key `1960`, `MIRA60`, `VERA60`, `music/1960.ogg`), so
  existing saves, tests and file names keep working.
- **Zuzana is 7.** She is about to finish first grade: her school year ends in 24 days, and she has been
  picked to ring the class bell on the last day. That is her own first "last bell", which echoes the title
  *Posledný zvonec*.
- **First meeting:** in the manor park (S37), next to Vera's bench. Zuzana is playing hopscotch (*škôlka*) on
  the gravel path, which she drew herself in chalk. Her art set (standing, playing loop, crouched chalk
  drawing) is already being made from the family photo you supplied.
- **Why she matters:** she knows every corner of Ivanka and finds her way by **sounds and smells** ("where it
  smells of leather", "where it ticks from every side", "where somebody shouts *Žiaden strach, miláčik*"). At
  each point where the main story needs it, she sends Adam to the right person, place or detail: Oto's
  workshop, the loose stage clamp in the hall, the leaking pump, Vera's blunt stylus and the carbon paper at
  the post office. Mira, Vera, Lída, Alojz, Božo and Berta talk about her too. **The main story's logic does
  not change at all:** she gives no story item and opens no door. She only adds lines and pointers.
- **Her own side quest Q10 "Prvý posledný zvonec" (4 steps).** The class hand bell has lost its clapper. Zuzana
  has written her own supply slip in first-grade capitals for the strict storekeeper Štefan ("LÍSTOK. PROSÍM
  JEDEN KÚSOK KOŽE NA ZVONČEK. ZUZANA, 1. TRIEDA."). Štefan honours it: *lístok, podpis, materiál – všetko
  sedí*. Adam makes a new leather loop, and Zuzana rings the bell across the whole park. The ending is warm:
  *"A keď budete niekedy počuť zvoniť na konci roka, zamávajte. Ja to neuvidím, ale aj tak."*
- **Payoff:** a credits shot at the end of June 1962. Zuzana rings the bell at the school door as the first
  graders run out into the summer holidays: *"Posledný zvonec! A v septembri zase prvý."* **She appears only
  in 1962** (owner decision 2026-10-06): no other era shows her, and no line in 2020 or 2035 mentions her or her
  later life. A possible 1995 Dúbravka appearance is pending with the owner (section 6.1). The only facts are her
  name (Zuzana, no surname) and that she was born in 1955 in Ivanka pri Dunaji.
- **Privacy:** the photo is used only as a likeness reference for the generated character. It is never
  copied into the repository or published, and the documents call it only "family photo supplied by the
  owner".

**Two small things you may want to decide** (the design works either way):
1. Adults call her by the diminutive **Zuzka**, as Slovak villagers would call a 7-year-old. Her name label
   stays **Zuzana**. If you want "Zuzana" everywhere, replace "Zuzka" in the lines.
2. In the data she is a **neighbour of young Mira**, two houses away. She is not related to Adam's family.

---

## 1. Who Zuzana is in 1962

| | |
|---|---|
| id / speaker | `ZUZANA` (one era, so no era suffix, like `BERTA` or `RUDO`) |
| name shown | **Zuzana** (no surname, ever). Adults may say *Zuzka*. |
| facts (owner) | born 1955 in Ivanka pri Dunaji. Nothing else is factual; everything below is game fiction set in June 1962. |
| in the game | 7 years old on 6 June 1962, finishing first grade. Her school year ends in **24 days** (she counts them). |
| where | manor park S37, on the gravel path in front of the lawn near Vera's bench. School is over for the day (the Ivanka paintings are afternoon light). |
| what she does | plays hopscotch (*škôlka*) that she drew in chalk, or crouches and draws in chalk (art variants: standing, playing loop, drawing). |
| character | lively once she trusts you, curious and very observant. Her small face starts out serious and warms up slowly (matches the art brief). She asks questions and remembers everything. |
| how she is funny | kid logic and literal words (a pump *manžeta* must be on a shirt sleeve; *škôlka* is the game and also the kindergarten she no longer attends). She **counts everything**: hopscotch squares, days to the school report, drips of the leaking pump, how often Rudo forgets his line. |
| running gag | **directions by sound and smell**: Ivanka has its own sound in every corner. This matches the game's theme, since Mira later records "how a school break sounds". |
| address | Zuzana → Adam: **vy** (a child to a stranger, like Soňa). Adam → Zuzana: **ty**. She says *teta Mira, teta Vera, teta Lída, teta Berta, ujo Oto, ujo Štefan, ujo Rudo, ujo Božo* and *pán Baran* (the clerk is the one person she is formal with). Adults say *ty* to her. |
| knows | the manor park, the square (náves) with the well and the notice board, the bank of the Šúrsky kanál by the measuring booth, the culture hall (she watches rehearsals from the doorway), the post office (she buys stamps "that look nice"), the farm yard (children are kept out because of the hand cart). |
| does not | enter Oto's workshop, the measuring room S39 or the attic S40, handle tools or ZVON, keep secrets from adults, or learn that Adam comes from the future. |
| era words | *prvá trieda, vysvedčenie, učiteľka, prázdniny, krieda, škôlka, švihadlo, mamka*. Avoid modern words and *súdruh/súdružka* (STYLE_GUIDE § 4). She says "naša učiteľka", which needs no period term. |

Voice examples (VOICES.md format):
- `Ešte dvadsaťštyri dní a mám za sebou celú prvú triedu.`
- `Ujo Oto? Toho nájdete po zvuku. Tam, kde to tiká zo všetkých strán.`

---

## 2. First meeting – manor park S37

**Staging.** Zuzana's NPC hotspot `S37.ZUZANA` is always visible in S37. She is never moved, so the hints
can always send the player to the park. She plays to the right of Vera's bench (Vera feet ~[600, 800]), on
the front gravel path, away from the spawn point (1150, 930) and the bird bowl.
- Template blocking (final values come from the blocking pass and `tools/check_blocking.py`): child feet
  ~[330, 885], scale s(885) ≈ 0.74, so a 350 px figure is drawn ~258 px tall. Proposed values: rect
  `[270, 625, 125, 262]`, interaction_point `[455, 905]`, label_anchor `[332, 615]`.
- The hopscotch is a ground decal next to her: hotspot `S37.hopscotch`, rect `[90, 905, 330, 95]`,
  interaction_point `[480, 960]`. It is an atmospheric prop, so a click only looks at it.
- The class bell lies on the grass beside the hopscotch until Q10A, and again after Q10D: visual variant
  layer `S37_zuzana_bell`, visible when `not Q10A or Q10D`. While Adam carries it, the grass is empty.

**Looks**
- `look.S37.ZUZANA`: `Malá Zuzana skáče škôlku a každé políčko nahlas odpočíta. Vedľa v tráve leží zvonček, ktorý ani raz necinkol.`
  - variant after Q10A: `Zuzana kreslí kriedou ďalšiu škôlku, pre istotu aj s vchodom. Občas sa pozrie, či jej nesiem zvonček.`
  - variant after Q10D: `Zuzana skáče škôlku a po každom desiatom skoku zazvoní. Vera už ani nedvíha hlavu.`
- `look.S37.hopscotch` ("Škôlka kriedou"): `Škôlka nakreslená kriedou na chodníku: osem políčok a hore polkruh. Čiary má rovnejšie, ako ja na nákresoch.`

**Intro topic `ZUZANA.extra 1` "Kto si?"** (repeatable, Adam speaks first, no conditions)
```
ADAM:   Ahoj. Ty hráš škôlku?
ZUZANA: Hrám. Ale do škôlky už nechodím. Chodím do prvej triedy.
ZUZANA: Ešte dvadsaťštyri dní a mám za sebou celú prvú triedu.
ADAM:   Ty si to rátaš?
ZUZANA: Ja si rátam všetko. Políčka, schody aj to, koľkokrát ujo Rudo zabudne text.
ADAM:   Ja som Adam.
ZUZANA: Ja som Zuzana. Vy nie ste odtiaľto. Vy zniete inak.
```
This is the first meeting. The engine needs no flag for it: the topic is always offered, and the transcript
records it.

---

## 3. Her importance in the main story (no change in logic)

The main route stays exactly `B22 → I01 … I17` (walkthrough.json `main_route`, 94 main actions). Zuzana's
part has two layers. Neither one adds a condition, item or step.

### 3.1 Her own pointer topics on `S37.ZUZANA`

Each topic appears when the walkthrough needs that information and disappears once the step is done. It
gives only the direction or the place (hint level 1–2), never the solution or an item.
`hide_after` is a **new optional field for overlay ambient topics** (same meaning as on hotspots: hidden once
any listed action is done). If Core does not add it, keep these topics anyway: every line stays true after
its step, except that Z3 and Z4 mention a fault that is already fixed. In that case drop the last two lines
of Z3 and Z4.

| topic id | label (≤ 28) | requires_done | hide_after | serves step | what she points to |
|---|---|---|---|---|---|
| `ZUZANA.extra 2` | `Kde je Otova dielňa?` | – | `I01` | I01 (B22 objective "find Oto") | the route S32 → S35 → S36 |
| `ZUZANA.extra 3` | `Kto má dierovač?` | `I01` | `I03` | I03 | Lída in the hall S34 and the loose clamp `S34.clamp` |
| `ZUZANA.extra 4` | `Čo je s pumpou?` | `I01` | `I06` | I06 | the pump at the booth S38 needs a new cuff |
| `ZUZANA.extra 5` | `Poznáš Miru?` | – | – | I08/I09 (colour) | Mira is her neighbour; the booth by the canal lights up |
| `ZUZANA.extra 6` | `Holub pri miske` | – | `Q6C` | Q6 (side) | the pigeon wants its own feed (Štefan) |
| `ZUZANA.extra 7` | `Ujo Rudo` | – | – | Q7 (side, colour) | she knows only the first line of the play |
| `ZUZANA.extra 8` | `Prázdniny` | `I17` | – | colour | the canal, the trains |

Drafts:

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
`ZUZANA.extra 6` „Holub pri miske"
```
ZUZANA: Ten holub pri miske je poštový. Má na nohe krúžok.
ZUZANA: Dala som mu chlieb, ale nechcel. Asi je zvyknutý na lepšie.
ADAM:   Možno chce svoje vlastné krmivo.
ZUZANA: Zrno má ujo Štefan. Ale ten dáva iba na lístok.
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

### 3.2 Extra lines inside existing main actions (overlay `sequences`)

New keys use the suffix **`zNN`**, so they never collide with the `xNN` keys of the C3 writing pass. The
existing keys keep their text, speaker and order (WRITING_METHOD § 0). Positions are given relative to the
existing line ids. Lines are added only where Zuzana is really present (S37) or where an adult talks about
her.

| action | room | where the new lines go | what they add |
|---|---|---|---|
| **I10** (Vera lends the stylus) | S37, Zuzana present | z01 after `.001`; z02–z06 after `.004` | Zuzana says where Vera keeps the blunt stylus and **points Adam to the carbon paper at the post office (I14)**, exactly when the second copy is the next need |
| **I09** (Mira explains, gives REGFORM) | S39 | z01–z03 after `.008` | Mira: the stylus is with Vera in the park, and the little neighbour there can help |
| **I03** (stage clamp → punch) | S34 | z01–z03 after `.001` | Lída: Zuzka was the one who noticed that the flat wobbles on one screw |
| **I14** (carbon paper) | S33 | z01–z03 after `.001` | Alojz knows her from the counter |
| `BOZO.ambient 1` (topic "Kde nájdem Miru?") | S31 | z01–z03 after `.001` | Božo: if you get lost, ask little Zuzka in the park |
| `BERTA` new topic `BERTA.extra Z` „Kto je tá malá?" | S32 | new topic | the village *čí je* gag |
| `MIRA60` new topic `MIRA60.extra Z` „Suseda Zuzka" | S39, requires `I08` | new topic | Zuzka asks Mira where she puts the time she measures |

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
I09 (after `.008`):
```
 action.I09.z01  MIRA60: Vera kreslí v parku. Pri nej sa hrá naša malá suseda Zuzka.
 action.I09.z02  ADAM:   Tú poznám. Ukazuje cestu podľa zvukov.
 action.I09.z03  MIRA60: Tak počúvaj, čo ti povie. V Ivanke sa ešte nestratila.
```
I03 (after `.001`):
```
 action.I03.z01  LIDA:   Presne to mi včera hovorila malá Zuzka. Že náš les sa kýve na jednej skrutke.
 action.I03.z02  ADAM:   Mala pravdu.
 action.I03.z03  LIDA:   Tá má pravdu skoro vždy. Len skrutkovač nemá.
```
I14 (after `.001`; it is true on every route, because I14 needs I09 and the way to I09 passes the park):
```
 action.I14.z01  ALOJZ:  Len opatrne, prosím. Farbí aj prsty. Malá Zuzka si ním u mňa obkresľuje ruky.
 action.I14.z02  ADAM:   Tá malá zo škôlky v parku?
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
condition. If the whole overlay is removed, the game plays exactly as before. `check_rewrite.py` protected
facts stay in their keys (I09.005 still names the attic and Vera; I14.001 still names the counter).

---

## 4. Side quest Q10 „Prvý posledný zvonec"

**Story.** Zuzana's teacher has picked her to ring the class hand bell on the last day of the school year,
"because she has the steadiest hand". The bell is mute: the old leather loop holding the clapper (*srdce*)
has torn. The clapper is wrapped in her handkerchief. The teacher said Oto could fix it, but Oto "has four
alarm clocks today and no free hand", and children are kept out of the farm yard. So Zuzana did what she
saw the grown-ups do: she wrote a supply slip for Štefan. Adam takes the bell, Štefan honours the child's
slip, Adam ties a new loop, and Zuzana rings the bell in the park.

It is 4 steps. It is available from the first visit to Ivanka. It needs no main action, and no main action
needs it (WRITING rules, bible "Výsledok nemôže blokovať hlavnú líniu"). It can also be finished in the
postgame.

### 4.1 Items (4 new)

| id | name (sk) | look (sk) | origin | purpose (sk) | disposition | icon |
|---|---|---|---|---|---|---|
| `BELL_MUTE` | Triedny zvonček bez pútka | Mosadzný ručný zvonček s drevenou rúčkou. Srdce je zabalené v Zuzaninej vreckovke, pútko je roztrhnuté. | Q10A | Zavesiť srdce na nové kožené pútko. | retain | `items/BELL_MUTE.webp` |
| `ZUZA_SLIP` | Zuzanin lístok | List z linajkového zošita, tlačeným písmom: LÍSTOK. PROSÍM JEDEN KÚSOK KOŽE NA ZVONČEK. ZUZANA, 1. TRIEDA. | Q10A | Podať Štefanovi v hospodárskom dvore. | retain | `items/ZUZA_SLIP.webp` |
| `STRAP` | Kožený odrezok | Úzky pásik kože zo Štefanových odrezkov. Na pútko akurát, ani o kúsok viac. | Q10B | Zavesiť naň srdce zvončeka. | retain | `items/STRAP.webp` |
| `BELL_FIXED` | Opravený triedny zvonček | Srdce visí na novom pútku, uzol je schovaný vnútri. Zvoní čisto. | Q10C | Vrátiť Zuzane do parku. | retain | `items/BELL_FIXED.webp` |

Keys: `item.<id>.name`, `item.<id>` (look, the look_line_id), `item.<id>.purpose`. `STRAP` is not
`LEATHER` (*Predrezaná kožená manžeta*): the names differ and no recipe connects them. Its hover over the
pump shows nothing (resolver rule: only defined pairs).

### 4.2 Actions (game.json shape; all `quest: "Q10"`, `once: true`, `excluded_done: []`, `puzzle: null`, `cutscene: null`, `commit_policy: "atomic_after_validation_and_puzzle_before_lines"`)

| id | room | target | kind | requires_done | requires_items | selected_item | gives | consumes | animation / sfx |
|---|---|---|---|---|---|---|---|---|---|
| `Q10A` | S37 | `S37.ZUZANA` | topic | – | – | null | `BELL_MUTE`, `ZUZA_SLIP` | – | talk / item_soft |
| `Q10B` | S35 | `S35.SKLAD` | click | – | `ZUZA_SLIP` | `ZUZA_SLIP` | `STRAP` | `ZUZA_SLIP` | show_item / paper |
| `Q10C` | inventory | `BELL_MUTE` | combine (`symmetric: true`) | – | `BELL_MUTE`, `STRAP`, `TOOLS` | `STRAP` | `BELL_FIXED` | `BELL_MUTE`, `STRAP` | inventory_combine / item_soft |
| `Q10D` | S37 | `S37.ZUZANA` | click | – | `BELL_FIXED` | `BELL_FIXED` | – | `BELL_FIXED` | show_item / **school_handbell** (new) |

Resolver checks: S35.SKLAD already has I02 (selected `SUPPLYSLIP`) and Q6B (topic). Q10B is told apart by
`selected_item`. S37.ZUZANA has one story topic (Q10A) and one item use (Q10D), so there is no ambiguity.
`TOOLS` is never consumed in the game, so Q10C can always be done.

Labels, objectives, journal:

| id | label (≤ limits) | objective (= journal) |
|---|---|---|
| Q10A | `Zvonček, ktorý nezvoní` (topic label) | `Vyzdvihni u Štefana v hospodárskom dvore kožený odrezok na Zuzanin lístok.` |
| Q10B | `Podať Štefanovi Zuzanin lístok` | `Zaves srdce zvončeka na nové pútko.` |
| Q10C | `Zavesiť srdce zvončeka na nové pútko` | `Vráť opravený zvonček Zuzane do parku.` |
| Q10D | `Vrátiť Zuzane opravený zvonček` | journal: `Zuzana skúšobne zazvonila celému parku.` |

Lines:

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
Q10D
```
ZUZANA: Zvoní? Naozaj?
ADAM:   Skús. Ale pomaly, je triedny.
ZUZANA: Počuli ste? Takto bude znieť koniec roka.
VERA60: Zuzka, teraz celý park vie, že sa skončila hodina.
ZUZANA: Ešte sa neskončila. Ešte dvadsaťštyri dní. Toto bola skúška.
ADAM:   Skúška vyšla.
ZUZANA: Ďakujem. Môžete si skočiť škôlku. Ale iba do štvorky, dospelí ďalej padajú.
ZUZANA: A keď budete niekedy počuť zvoniť na konci roka, zamávajte. Ja to neuvidím, ale aj tak.
ADAM:   Zamávam.
```
(The ring itself is the action sfx `school_handbell`, three short rings played before the line "Počuli ste?".
No meaning lives only in the sound: the next line says what happened.)

### 4.3 Quest record

```json
{ "id": "Q10", "title": "Prvý posledný zvonec", "type": "side",
  "actions": ["Q10A", "Q10B", "Q10C", "Q10D"], "completion": "Q10D", "missable": false,
  "goal": "Opraviť Zuzanin triedny zvonček, aby mohla na konci roka zvoniť.",
  "reward": "Zuzana so zvončekom a jej kriedová škôlka v Adamovom albume.",
  "hints": [
    "Zuzana v parku pri kaštieli má zvonček, ktorý nezvoní.",
    "Srdce treba zavesiť na nové kožené pútko. Kožené odrezky má Štefan v hospodárskom dvore a vydáva ich iba na lístok.",
    "Zuzana v parku, téma zvonček → Zuzanin lístok Štefanovi → v brašni odrezok so zvončekom → opravený zvonček Zuzane." ] }
```
Step hints (`ui.hint_step.<id>`, ui.csv):
- `Q10A` `Porozprávaj sa so Zuzanou v parku o zvončeku, ktorý nezvoní.`
- `Q10B` `Zuzanin lístok podaj Štefanovi v hospodárskom dvore.`
- `Q10C` `V brašni spoj kožený odrezok so zvončekom.`
- `Q10D` `Opravený zvonček použi na Zuzanu v parku.`

Album: on Q10D the album gets the epilogue still and the reward text (bible: the reward is automatic, and
nothing has to be collected afterwards).

---

## 5. Ambient presence elsewhere

Zuzana's NPC stays in S37 (one place, so the hints and the inserted I10 lines always work). Elsewhere she is
present through **traces and sound**, which suits a child who is "everywhere":

| room | what | data |
|---|---|---|
| S32 náves | chalk arrow on a stone by the well, with PARK written under it | new prop `S32.chalk_arrow`, look: `Na kameni pri studni je kriedou šípka a pod ňou PARK. Niekto v Ivanke robí orientačné tabule.` |
| S38 canal bank | a paper boat stuck in the grass at the edge of the Šúrsky kanál | new prop `S38.paper_boat`, look: `Papierová loďka uviazla v tráve pri kanáli. Na boku má ceruzkou ZUZKA. Ďalej ju nepustili, správne.` |
| S32, S38 (after Q10D) | a distant hand bell, now and then, in the room ambience | ambient sound layer `school_handbell_far`, condition `Q10D`, max once per ~40 s, no gameplay meaning |
| S34 culture hall | Lída and Rudo talk about her (I03 lines; Rudo extra topic idea: "Zuzka vie moju prvú vetu lepšie ako ja") | text only |
| S33 post office | Alojz talks about her (I14 lines) | text only |

Props follow the rules: purely atmospheric (left click = look), no fake puzzle, shown by Space,
≥ 44 × 44 px. Template rects: `S32.chalk_arrow` [250, 905, 140, 70] near the well, `S38.paper_boat`
[1340, 840, 120, 60]. The blocking pass places them on the painting.

---

## 6. Payoff

**Epilogue shot (rule: completed episodes in quest order, 5–7 s each; Q10 comes after Q9, so it is
`epilogue.10`):**
```json
{ "quest": "Q10", "after": "Q10D",
  "shot": "Koniec júna 1962. Zuzana zvoní pred dedinskou školou triednym zvončekom a prváci vybiehajú na prázdniny.",
  "line": "ZUZANA: Posledný zvonec! A v septembri zase prvý." }
```
Art: a generic village school door (a game composite, not a claim about the real Ivanka school). The
hopscotch is chalked on the path. The likeness comes from the generated ZUZANA sheet, not from the photo
directly. `epilogue_rules` text: `Q1–Q9` → `Q1–Q10`.

**No cross-era echo with her name (owner decision 2026-10-06).** The 2020 topic `MIRA20.extra Z` „Zuzka z
Ivanky" (grandma Mira remembering that June) is **dropped from the design**: Zuzana appears only in 1962, and no
text, topic, look, journal entry, hint or picture of 2020 or 2035 shows her, names her or refers to her later
life. Nothing in the other eras depends on Q10. The epilogue shot above (end of June 1962) is the payoff.
Thematic echo with nothing added: in 1995 Adam hears the school's own bell and break noise on the tape.
Zuzana's "zamávajte" is only a feeling for the player, not a data link.

Not allowed (also for later writers): no appearance of Zuzana outside June 1962 and no mention of her in 1982,
1995 (until the owner settles section 6.1), 2020 or 2035; no adult Zuzana unless the owner's 1995 details ask
for one; no surname, no job, family, address or fate, and no claim that she later went to Sokolíkova, knew Adam's
family after 1962 or is "the reason" for anything in the main story. Nothing about her real life is written into
the repository.

### 6.1 1995 (pending owner)

The owner may add an appearance of Zuzana in Dúbravka 1995; the details are pending with the owner. Until they
arrive, nothing is designed, written, painted or implemented for it, and no 1995 text names her. Open points for
the owner's answer (the design follows the answer, it does not guess):
- where in Dúbravka 1995 (an existing room S11–S18 or a new place) and in which part of the 1995 chapter;
- what she does there, whether Adam speaks with her, and whether she recognises him from 1962;
- how she looks then (a new character sheet would be needed; no photo of a real person is used without the
  owner's explicit go-ahead, and the privacy rules of section 10 apply);
- whether anything in 1995 links back to Q10 (the bell) or stays independent of it.

---

## 7. Consistency with the cast (June 1962)

Rule for the shift: **birth years stay, ages go up by two.** Ages shown in text change (section 8). The
`age` fields in data may be patched by the overlay for consistency (no player sees them).

| character | 1960 → 1962 | relation to Zuzana | note |
|---|---|---|---|
| Mira (`MIRA60`) | 20 → **22** | neighbour, two houses away; *teta Mira* | Mira tykne Zuzke; Zuzana once asked her where she puts the time she measures |
| Oto (`OTO`) | 44 → **46** (66 in 1982 is unchanged) | the village fixer; *ujo Oto* | children are not allowed in his workshop; he was supposed to fix the bell |
| Vera (`VERA60`) | 22 → **24** | Zuzka plays next to her bench; *teta Vera* | Vera is dry and fond of her (Q10D, I10) |
| Berta (`BERTA`) | 68 → **70** | village grandmother figure; *teta Berta* | knows "whose" everyone is: *predsa mamkina* |
| Rudo (`RUDO`) | 34 → **36** | she watches rehearsals from the door; *ujo Rudo* | she knows his first line, not the second |
| Lída (`LIDA`) | 43 → **45** | Zuzka told her the flat wobbles; *teta Lída* | I03 lines |
| Alojz (`POSTA`/`ALOJZ`) | 54 → **56** | she buys stamps that look nice; *pán Baran* | I14 lines |
| Štefan (`SKLAD`/`STEFAN`) | 51 → **53** | keeps children out of the yard (hand cart); *ujo Štefan* | honours her slip in Q10B |
| Božo (`BOZO`) | 45 → **47** | lets her wave at the trains; *ujo Božo* | points to her in his topic |
| Adam | 35 (2020 visitor) | a stranger "who sounds different" | never tells her he is from the future |
| Tóno, Jana, Lea, Viktor | – | none | Zuzana never appears outside June 1962 (1995 Dúbravka pending, section 6.1) |
| Mira (`MIRA20`, 2020) | – | none in the game | she does not mention Zuzana (the `MIRA20.extra Z` topic is dropped) |

Zuzana is **not** family of Adam, Mira or Oto. Repeated surnames are coincidences (GLOSSARY § 2), and she has
none.

---

## 8. The 1962 shift – everything that changes

**Unchanged on purpose:** internal ids and keys (era key `1960`, `MIRA60`, `VERA60`, `music/1960.ogg`,
`ui.journal.scene_cs03` key, `era.1960.*` keys, file names such as `ivanka1960.csv`). The P04 puzzle values
and solution stay `"1960"` internally. `game.json` is not edited (WRITING_METHOD § 0). All visible changes go
through `sk_overrides.csv` / `ui.csv` / the overlay. Durations: 1962 → 2020 = **58** years, 1962 → 2035 =
**73**, 1962 → 1982 = **20**, Mira 22 vs Adam 35 = **13**.

### 8.1 Texts (key → new Slovak; current text in brackets where it is not just the year)

dialogue (via `sk_overrides.csv`):
- `entry.S31.001` → `Ivanka, rok 1962. Telefón je tu rovnako zbytočný ako v roku 1995. Ja som o niečo nervóznejší.`
- `action.B22.003` → `Ivanka, rok 1962. Babka toho dokázala viac, ako sa o nej hovorilo na rodinných oslavách.`
- `action.I16.002` → `Potrebujem, aby aj o sedemdesiattri rokov bolo jasné, že tento papier existoval.` (was *sedemdesiatpäť*)
- `action.I16.003` → `Na sedemdesiattri rokov vám doručenie nezaručím. Ale pečiatka vydrží.`
- `action.C03.002` → `Bolo v nej takmer šesťdesiat rokov.` (58)
- `action.C05.001` → `Pôvod 1962. Hlas 1995. Súhlas 2020. Cieľ fondu: Atlas, Jasná, 2035.`
- `action.F08.001` → `Pravidlo z roku 1962 aj miestna stopa sedia. Obnovovací postup som podpísala.`
- `cutscene.CS03.01.001` → `Ivanka pri Dunaji. 6. júna 1962.`

world (via `sk_overrides.csv`):
- `look.S15.register.variant1` → `… správny pôvod: Z-17 z roku 1962. …`
- `look.S33.ambient 2` → `Nástenný kalendár: jún 1962. Môj telefón by s ním nesúhlasil.`
- `look.S39.MIRA60` → `Je o trinásť rokov mladšia než ja a stále vyzerá, že ma o chvíľu pošle umyť si ruky.`
- `look.S49.port_origin` → `Port Pôvod. Sem patrí overený odtlačok z roku 1962.`
- `look.S64.OTO82` → `Oto zostarol o dvadsať rokov. Nákresy má stále rovné.`
- `item.REGFORM.purpose`, `item.ORIGIN.name` (`Overený odtlačok z roku 1962`), `item.ORIGIN`, `item.CATALOG` (`… s rokmi 1962, 1995 a 2020 …`)
- `action.B22.journal` / `.objective` (`… vyber Ivanku 1962 …`)
- `action.I08.journal` / `.objective` → `Porozprávaj sa s dvadsaťdvaročnou Mirou v meracej miestnosti.`
- `action.C01.label`, `action.F12.label`, `action.F12.journal`
- `quest.M07.goal`, `quest.M10.hint.1`, `quest.M11A.hint.3`, `quest.M15.hint.1`, `quest.M15.hint.3` (`Pôvod 1962, …`)
- `puzzle.P03.success` → `Pôvodná referencia nájdená: Ivanka pri Dunaji, 6. júna 1962.`
- `puzzle.P04.right.2` → `1962` (**label only**; the option value and the solution stay `"1960"`, `PuzzleControls.OptionLabel` shows the key)
- `journal.clue.P04` → `Pôvod 1962, Hlas 1995, Súhlas 2020, Návrat 2035` (verbatim line: the owner's decision changes it)

ui.csv (edited directly):
- `era.1960.date` → `6. júna 1962` (`era.1960.card` stays `Ivanka pri Dunaji`)
- `ui.hint_step.C01`, `ui.hint_step.F12`, `ui.hint_step.F16` (`Pôvod 1962 …`), `ui.journal.scene_cs03` → `Cesta do Ivanky 1962`
- **new** `era.1960.year` = `1962` (and `era.<y>.year` = `<y>` for the other eras), see 8.3

Writing drafts that feed the overrides: `docs/writing/out/C2.csv`, `C3.csv`, `C4.csv` (they contain 1960
texts). Update them, or the next merge brings 1960 back. Then rerun `tools/writing_bundles.py`,
`extract_strings.py` and `check_strings.py`.

### 8.2 Protected facts and checker (must change, or `check_rewrite.py` fails)

- `docs/writing/GLOSSARY.md` § 6.3: time window `6. júna 1962`; Mira **22 (1962)**; Oto **46 (1962)**, *zostarol
  o dvadsať rokov*; Mira's box *takmer šesťdesiat rokov* (1962 → 2020) and *o sedemdesiattri rokov* (1962 → 2035);
  Mira vs Adam *o trinásť rokov mladšia*. § 6.1 P04 and § 6.4 `journal.clue.P04`: `Pôvod 1962`. § 2: add
  `ZUZANA | Zuzana | Zuzana, Zuzka | Zuzany, Zuzane, Zuzanu; Zuzanin lístok; no surname`.
- `docs/writing/glossary.json`: the same values in `protected` / `verbatim`, plus `ZUZANA` in the names.
- `docs/writing/VOICES.md`: ty/vy table row for Zuzana (vy → Adam, Adam → ty); Ivanka header `1962`; ages
  of the Ivanka cast +2 (Mira 22, Oto 46, Vera 24, Božo 47, Berta 70, Alojz 56, Lída 45, Rudo 36, Štefan 53);
  a new ZUZANA entry (section 1 above); MIRA60 "Mira 20 (1960)" → "Mira 22 (1962)".
- `docs/writing/STYLE_GUIDE.md` § 4 / 4.1: era name `1962 Ivanka pri Dunaji`.

### 8.3 Code (for the engine agent; no ids change)

The year number is printed straight from the era key in four places. Each should show `Tr("era.<y>.year")`
with the year as fallback: `UI/Cutscenes/EraCardView.cs:67`, `UI/Map/MapScreen.cs:68` (`ui.map.sheet_year`
{year}), `UI/Menus/PortalChooser.cs:46,48`, `UI/Journal/JournalScreen.cs:307`. Saves, tests
(`AcceptanceTests`, `PuzzleAndDialogueTests` use 1960) and `Navigation.UsePortal(…, 1960)` stay unchanged.

### 8.4 Art and assets with a legible year

| asset | now | change |
|---|---|---|
| `CS03_1` (art/cutscenes/CS03_1_v1.png → assets/cutscenes/CS03_1.webp) | chronometer counter reads **1960** | inpaint the last digit to **1962**; brief in `art/tools/cutscene_shots.py` ("reads exactly 1962") |
| `EPILOGUE_6` (post office) | wall calendar **1960** | inpaint to **1962**; the weekday header is pseudo-English (SU MO TU …): replace it with Slovak `PO UT ST ŠT PI SO NE` or illegible marks in the same pass; brief "1962 wall calendar" |
| `S33` background (bg_natural/S33 and any S33 variant) | painted calendar **1960** | inpaint to **1962**; `art/prompts/natural/S33.txt` ("the only lettering is the number 1962") |
| item icons (REGFORM, REGDOUBLE, REGISTERED, ORIGIN, …) | no legible year (`art/tools/item_briefs.py`: illegible typed lines) | none |
| all other Ivanka paintings, sprites, CS04, EPILOGUE_7 | no lettering. Two years are not visible in clothes or buildings. | briefs/metadata only: "June 1962" in `cutscene_shots.py`, `art/prompts/natural/S3x.txt`, `characters.json` descriptions (no regeneration) |
| `art/characters/characters.json` ZUZANA | `"era": 1962` | game data uses era key `1960`; align the tooling field (1960 + display 1962) so scripts that join on era find her |

### 8.5 Documentation

- `docs/DECISIONS.md`: owner decision 2026-10-06. Ivanka moves to 6 June 1962 (display only, ids kept), and
  Zuzana plus side quest Q10 are added. This supersedes the bible's "nemá dopĺňať nové … vedľajšie úlohy"
  for this one case and its "Ivanka 1960" lines.
- `design-doc/ISSUES.md`: one row (1960 → 1962, keys unchanged, P04 value kept "1960").
- `design-doc/README.txt`: an addendum under "Doplnky k handoffu" (the handoff text itself, including
  PRIBEH_A_PRAVIDLA.txt and the HTML, stays as delivered).
- `design-doc/LOCATIONS_REGISTER.csv`, `design-doc/locations/ivanka1960.csv`, `docs/locations.html`: the
  displayed period becomes 1962 (file names stay).
- `design-doc/assets.csv`: new rows (section 9).

---

## 9. Implementation checklist (data for the overlay)

Overlay file proposal: `src/game/data/content_ext/zuzana_ext.json` (format `lastbell.zuzana_ext`,
loaded like `travel_ext.json`). Field names are those of game.json. The Core agent fixes the schema in
`src/LastBell.Core/README.md`.

1. `characters`: `ZUZANA` (name `Zuzana`, age 7, rooms [S37], role/voice/design from section 1, the design
   from `characters.json`), with ambient topics `ZUZANA.extra 1–8` (sections 2, 3.1). `char.ZUZANA.name` =
   `Zuzana`. Speaker label `ZUZANA`.
2. `rooms` patches: S37 adds hotspots `S37.ZUZANA` (npc, character_id ZUZANA, looks + variants after Q10A
   and Q10D) and `S37.hopscotch` (prop), and `npc_ids` + `ZUZANA`. S32 adds `S32.chalk_arrow`. S38 adds
   `S38.paper_boat`.
3. `items`: BELL_MUTE, ZUZA_SLIP, STRAP, BELL_FIXED (4.1).
4. `actions`: Q10A–Q10D (4.2), with `journal_text` / `objective` and `staging.guest_speakers: ["VERA60"]` on
   Q10D (Vera only speaks from her bench, nothing moves).
5. `quests`: Q10 (4.3). `epilogue`: the Q10 entry (6). `epilogue_rules`: Q1–Q10.
6. `sequences` / `topic_extensions`: I10, I09, I03, I14, BOZO.ambient 1 (3.2). New `topics`: BERTA.extra Z,
   MIRA60.extra Z (all in 1962; no topic in another era, section 6).
7. `visual_variant_layers`: `S37_zuzana_bell` (bell on the grass when not Q10A or Q10D). Ambience layers
   `school_handbell_far` in S32/S38 after Q10D.
8. Assets (`design-doc/assets.csv`, art pipeline): ZUZANA sprite set (in production: `art/tools/zuzana_set.py`),
   4 item icons, 3 prop paintings or patches (hopscotch decal S37, chalk arrow S32, paper boat S38), the S37
   bell prop, the epilogue still `EPILOGUE_10`, sfx `school_handbell` + `school_handbell_far`, and the three
   1962 patches (8.4).
9. Counts: characters 51, items 82, side quests 10, side actions 37, hotspots +4 (ambient props +3).
   Update `stats` and any test or validator that counts them. Main actions stay **94**.
10. Checks: the main route replay (walkthrough `main_route`) is identical. The side-quest run includes Q10,
    also after the credits. No main `requires_done`, `requires_items` or `consumes` names a Q10 action or
    item. `check_strings`, `check_rewrite` (with the new protected values), `check_blocking`, `dotnet test`,
    and the headless line dump (`tools/qa_godot.py --headless …`) all pass.

---

## 10. Privacy rules for this character

- `art/source/owner_refs/family_zuzana.jpg` stays private and git-ignored. It is read only by the art tool as
  a likeness reference, sent as a data URI, and never copied into `art/characters/`, the build, docs or any
  published page.
- Documents, sidecars and credits call it only **"family photo supplied by the owner"**. Do not describe it.
- Game text uses only the owner's facts (Zuzana, born 1955 in Ivanka pri Dunaji). Everything else is
  presented as fiction about June 1962. Nothing is said about her life after 1962.
