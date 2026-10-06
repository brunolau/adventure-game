# S30 – Merací stánok na Starom moste (1995, Petržalka): focused review bundle

Assembled for the S30 rename review (owner decision 2026-10-06) from the blocks of `C2.md` and `C4.md` that contain a changed key, with every text replaced by the current table text (dialogue.csv / world.csv / ui.csv). Ids in brackets are context only and never appear in the Slovak text.

## 1. Story actions in play order

### B16 · main quest M06 „Mapa v troch kusoch“

- Where: S22 Antikvariát Pod druhou rukou (1995)
- How: in the bag: combine „Priehľadná mapa K-17“ (OVERLAY) with „Mapa bez priehľadnej vrstvy“ (DIAGRAM)
- Available: holding „Mapa bez priehľadnej vrstvy“ (DIAGRAM), „Priehľadná mapa K-17“ (OVERLAY)
- Player gets: „Úplná mapa uzlov“ (NODEMAP)
- Used up: „Mapa bez priehľadnej vrstvy“ (DIAGRAM), „Priehľadná mapa K-17“ (OVERLAY)
- Puzzle P02 opens first (solution: 180); see section Puzzles.

- `action.B16.label` [action sentence shown while combining the two items (hover line)] Zarovnať fóliu s mapou
- `action.B16.001` [spoken line] **ADAM** (Adam Hruška): Mapa je celá a vedie do Petržalky: k Deziderovej garáži a k meraciemu stojanu pri Dunaji.
- `action.B16.002` [spoken line] **ADAM** (Adam Hruška): Rádioamatér v garáži. Konečne niekto, kto hovorí mojou rečou.
- `action.B16.objective` [objective: the pinned 'current goal' sentence after this action] Ukáž úplnú mapu meracích uzlov Deziderovi v garáži v Petržalke.
- `action.B16.journal` [journal entry (same text as the objective in game.json)] Ukáž úplnú mapu meracích uzlov Deziderovi v garáži v Petržalke.

### B17 · main quest M07 „Rytmus na Dunaji“

- Where: S29 Garáž rádioamatéra (1995)
- How: use „Úplná mapa uzlov“ (NODEMAP) on „Dezider Kováč“ (S29.DEZI)
- Available: holding „Úplná mapa uzlov“ (NODEMAP)
- Player gets: „Deziderova meracia cievka“ (COIL)

- `action.B17.label` [action sentence shown when the selected item hovers over the target] Ukázať Deziderovi úplnú mapu
- `action.B17.001` [spoken line] **DEZI** (Dezider Kováč): Túto mapu sme kreslili s Mirou. Tu máš cievku k stojanu na nábreží. Ešte potrebuješ nezávislý rytmus.
- `action.B17.002` [spoken line] **ADAM** (Adam Hruška): Mechanické hodiny?
- `action.B17.003` [spoken line] **DEZI** (Dezider Kováč): Lepší bude metronóm, má ho Emil v Karlovej Vsi. Tri číslice Mira nakreslila na panel na školskom dvore.
- `action.B17.004` [spoken line] **ADAM** (Adam Hruška): Na školský dvor sa vraciam dobrovoľne. To sa mi ako žiakovi nestalo.
- `action.B17.objective` [objective: the pinned 'current goal' sentence after this action] Požičaj Emilov metronóm a prečítaj rytmický nákres na školskom dvore.
- `action.B17.journal` [journal entry (same text as the objective in game.json)] Požičaj Emilov metronóm a prečítaj rytmický nákres na školskom dvore.

### B18 · main quest M07 „Rytmus na Dunaji“

- Where: S19 Karloveské nástupište (1995)
- How: dialogue choice when talking to „Emil Belan“ (S19.EMIL)
- Available: after „Ukázať úplnú mapu uzlov“ (B17)
- Player gets: „Emilov metronóm“ (METRONOME)

- `action.B18.label` [dialogue choice the player picks (also the heading of this exchange in the conversation log)] Metronóm na meranie
- `action.B18.001` [spoken line] **ADAM** (Adam Hruška): Dezider vraví, že na Mirino meranie potrebujem mechanický rytmus. Požičali by ste mi metronóm?
- `action.B18.002` [spoken line] **EMIL** (Emil Belan): Vezmi si ho. Dezider mi ho potom vráti, poznáme sa roky.
- `action.B18.003` [spoken line] **ADAM** (Adam Hruška): Ďakujem. Raz vám za to pustím hudbu z budúcnosti.
- `action.B18.004` [spoken line] **EMIL** (Emil Belan): Len nech nie je príliš hlasná.
- `action.B18.objective` [objective: the pinned 'current goal' sentence after this action] V nábrežnom prístrešku nasaď cievku do držiaka pri meracom stojane a metronóm polož na stolík.
- `action.B18.journal` [journal entry (same text as the objective in game.json)] V nábrežnom prístrešku nasaď cievku do držiaka pri meracom stojane a metronóm polož na stolík.

### B19 · main quest M07 „Rytmus na Dunaji“

- Where: S17 Školský dvor (1995)
- How: left click on „Rytmický nákres“ (S17.rhythm)
- Available: after „Vysvetliť problém s chronometrom“ (B03)

- `action.B19.label` [action name (journal/transcript; the click itself shows the hotspot name)] Zapísať tri kalibračné číslice
- `action.B19.001` [spoken line] **ADAM** (Adam Hruška): „Tri vlny, dva údery, šesť dielikov.“ Čiže tri, dva, šesť.
- `action.B19.002` [spoken line] **ADAM** (Adam Hruška): Zapíšem si to. Vlastnej pamäti dnes veľmi neverím.
- `action.B19.objective` [objective: the pinned 'current goal' sentence after this action] Na meracom stojane v nábrežnom prístrešku nastav 3–2–6.
- `action.B19.journal` [journal entry (same text as the objective in game.json)] Na meracom stojane v nábrežnom prístrešku nastav 3–2–6.

### B20 · main quest M07 „Rytmus na Dunaji“

- Where: S30 Merací stánok na Starom moste (1995)
- How: use „Deziderova meracia cievka“ (COIL) on „Držiak meracej cievky“ (S30.coil)
- Available: holding „Deziderova meracia cievka“ (COIL)
- Used up: „Deziderova meracia cievka“ (COIL)

- `action.B20.label` [action sentence shown when the selected item hovers over the target] Nasadiť meraciu cievku
- `action.B20.001` [spoken line] **ADAM** (Adam Hruška): Cievka zapadla do držiaka. Obvod je pripravený.
- `action.B20.journal` [journal entry recorded by this action] Deziderova cievka sedí v držiaku na nábreží.

### B21 · main quest M07 „Rytmus na Dunaji“

- Where: S30 Merací stánok na Starom moste (1995)
- How: use „Emilov metronóm“ (METRONOME) on „Stolík s rytmickou značkou“ (S30.metro)
- Available: holding „Emilov metronóm“ (METRONOME)
- Used up: „Emilov metronóm“ (METRONOME)

- `action.B21.label` [action sentence shown when the selected item hovers over the target] Postaviť metronóm na stolík
- `action.B21.001` [spoken line] **ADAM** (Adam Hruška): Metronóm tiká. Konečne niečo, čo nepotrebuje elektrinu ani vysvetlenie.
- `action.B21.journal` [journal entry recorded by this action] Emilov metronóm tiká na stolíku v prístrešku.

### B22 · main quest M07 „Rytmus na Dunaji“

- Where: S30 Merací stánok na Starom moste (1995)
- How: left click on „Tri kalibračné číslice“ (S30.dial)
- Available: after „Zapísať trojicu kalibračných číslic“ (B19), „Nasadiť meraciu cievku“ (B20), „Umiestniť mechanický metronóm“ (B21), „Prehrať kazetu cez opravenú prepojku“ (B12), „Zarovnať fóliu s mapou“ (B16); holding „Úplná mapa uzlov“ (NODEMAP), „Pôvodná školská kazeta“ (TAPE), „Prenosný chronometer ZVON“ (CHRONO)
- Puzzle P03 opens first (solution: [3, 2, 6]); see section Puzzles.
- Afterwards cutscene CS03 plays (context only): SYSTEM: Ivanka pri Dunaji. 6. júna 1962. / ADAM: Idem za ženou, ktorá ešte nevie, že raz bude moja babka. / ADAM: A musím to stihnúť, kým jej meno nezmizne aj z neskorších rokov.

- `action.B22.label` [action name (journal/transcript; the click itself shows the hotspot name)] Nastaviť číslice a nájsť pôvodnú kalibráciu
- `action.B22.001` [spoken line] **ADAM** (Adam Hruška): Tri, dva, šesť. Mapa sedí, kazeta beží ako referencia.
- `action.B22.002` [spoken line] **SYSTEM** (Text zariadenia): Nové časové okno uložené.
- `action.B22.003` [spoken line] **ADAM** (Adam Hruška): Ivanka, rok 1962. Babka toho dokázala viac, ako sa o nej hovorilo na rodinných oslavách.
- `action.B22.004` [spoken line] **ADAM** (Adam Hruška): Odcestujem cez uzlové hodiny na Dúbravskej zastávke.
- `action.B22.objective` [objective: the pinned 'current goal' sentence after this action] Na časovom uzle Dúbravskej zastávky vyber Ivanku 1962 a nájdi Ota v jeho mechanickej dielni.
- `action.B22.journal` [journal entry (same text as the objective in game.json)] Na časovom uzle Dúbravskej zastávky vyber Ivanku 1962 a nájdi Ota v jeho mechanickej dielni.

## 2. Rooms in first-visit order

### S28 · Petržalský podchod (1995, Petržalka)

Picture: Presvetlený peší podchod s legálnym výtvarným panelom, mladý výtvarník Juraj, staré výlepy, kachličky. Žiadne hrozivé stereotypy o štvrti.

People here: JURAJ Juraj Križan

- `room.S28.name` [room name (map, exit labels elsewhere)] Petržalský podchod
- `entry.S28.001` [first entry line (Adam, once)] **ADAM** (Adam Hruška): Podchod s dobrou ozvenou. Tu by aj tri tóny zneli ako koncert.
- Hotspot S28.JURAJ: kind npc; actions here: „Ponúknuť kriedu na mapu svetiel“ (Q5A)
  - `hotspot.S28.JURAJ.name` [hotspot name (hover / Space label)] Juraj Križan
  - `look.S28.JURAJ` [right-click look (Adam's observation)] Juraj kreslí paneláky tak, že na nich vidno domovy.
- Hotspot S28.ambient 1: kind prop
  - `hotspot.S28.ambient 1.name` [hotspot name (hover / Space label)] Kachličky
  - `look.S28.ambient 1` [right-click look (Adam's observation)] Každá kachlička má trochu inú bielu. A spolu aj tak tvoria stenu.
- Hotspot S28.ambient 2: kind prop
  - `hotspot.S28.ambient 2.name` [hotspot name (hover / Space label)] Skateboard
  - `look.S28.ambient 2` [right-click look (Adam's observation)] Skateboard. Na cestovanie v čase má priveľmi malé kolieska.
- Hotspot S28.mural: kind prop; actions here: „Dokresliť svetlá podľa Jurajovej skice“ (Q5C)
  - `hotspot.S28.mural.name` [hotspot name (hover / Space label)] Povolený výtvarný panel
  - `look.S28.mural` [right-click look (Adam's observation)] Povolený panel klubovne, kreslí sa naň kriedou. Juraj má skicu, chýba mu však biela krieda.
  - `look.S28.mural.variant1` [look variant, shown after „Dokresliť svetlá podľa Jurajovej skice“ (Q5C)] Rozsvietené okná spojili paneláky do jedného susedstva. V rohu je Jurajov podpis a nakreslený kúsok kriedy.
- `exit.S28.to_S21.label` [exit label → S21] Kamenné námestie
- `exit.S28.to_S29.label` [exit label → S29] Garáž rádioamatéra
- `exit.S28.to_S30.label` [exit label → S30] Nábrežný merací prístrešok
- `conn.S28.S29.label` [map connection label] Garáž rádioamatéra
- `conn.S28.S30.label` [map connection label] Nábrežný merací prístrešok

### S30 · Merací stánok na Starom moste (1995, Petržalka)

Picture (natural painting bg_natural/S30, 1995): the wooden plank footway of the old Starý most, riveted grey steel truss members framing the view, a small grey-green sheet-metal measuring booth with an open hatch and a counter (ring holder for the coil, a demo circuit board, a grey box with three number wheels), a small round table with a rhythm mark at the railing beside the booth, the Danube, Most SNP and the castle behind.

- `room.S30.name` [room name (map, exit labels elsewhere)] Nábrežný merací prístrešok
- `entry.S30.001` [first entry line (Adam, once)] **ADAM** (Adam Hruška): Dunaj tečie, ako má. Z nás dvoch som tu ja ten, kto cestuje čudne.
- Hotspot S30.ambient 1: kind prop
  - `hotspot.S30.ambient 1.name` [hotspot name (hover / Space label)] Loď
  - `look.S30.ambient 1` [right-click look (Adam's observation)] Loď sa plaví po vode a v správnom roku. Závidím jej.
- Hotspot S30.ambient 2: kind prop
  - `hotspot.S30.ambient 2.name` [hotspot name (hover / Space label)] Zábradlie
  - `look.S30.ambient 2` [right-click look (Adam's observation)] Toto si nechám medzi sebou a Dunajom.
- Hotspot S30.coil: kind prop; actions here: „Nasadiť meraciu cievku“ (B20)
  - `hotspot.S30.coil.name` [hotspot name (hover / Space label)] Držiak meracej cievky
  - `look.S30.coil` [right-click look (Adam's observation)] Kruhový držiak na Deziderovu meraciu cievku. Má výrez, takže opačne ju nevložím.
- Hotspot S30.dial: kind prop; actions here: „Nastaviť a odmerať pôvodnú časovú adresu“ (B22)
  - `hotspot.S30.dial.name` [hotspot name (hover / Space label)] Tri kalibračné číslice
  - `look.S30.dial` [right-click look (Adam's observation)] Tri kolieska od 0 po 9. Potrebujem mapu uzlov, pôvodnú kazetu a číslice z nákresu na školskom dvore.
- Hotspot S30.metro: kind prop; actions here: „Umiestniť mechanický metronóm“ (B21)
  - `hotspot.S30.metro.name` [hotspot name (hover / Space label)] Stolík s rytmickou značkou
  - `look.S30.metro` [right-click look (Adam's observation)] Stolík so značkou pre metronóm. Rytmus tu nesmie závisieť od elektriny.
- `exit.S30.to_S28.label` [exit label → S28] Petržalský podchod

## 5. Quests (journal, goal card, hints)

### M07 (main) — actions B17, B18, B19, B20, B21, B22

- `quest.M07.goal` [quest goal (journal + pinned goal card)] Nájdi meraním na nábreží časové okno do Ivanky 1962.
- `quest.M07.hint.1` [hint level 1: direction] S úplnou mapou choď za rádioamatérom Deziderom do Petržalky.
- `quest.M07.hint.2` [hint level 2: concrete steps] Dezider dá cievku, Emil metronóm. Tri číslice sú na paneli na školskom dvore.
- `quest.M07.hint.3` [hint level 3: exact solution] Mapa na Dezidera → téma „Metronóm na meranie“ u Emila → prečítaj rytmický nákres na školskom dvore → cievka na držiak v nábrežnom meracom prístrešku → metronóm na stolík → keď máš pôvodnú kazetu, nastav 3–2–6.
- `quest.M07.title` [quest title (journal)] Rytmus na Dunaji

## 6. Puzzles

### P03 — controls digits, solution [3, 2, 6] (action B22)

- `puzzle.P03.clue` [clue shown in the puzzle window] Rytmický nákres a zápisník: TRI VLNY, DVA ÚDERY, ŠESŤ DIELIKOV.
- `puzzle.P03.confirm` [confirm button] Odmerať
- `puzzle.P03.success` [line after solving] **SYSTEM** (Text zariadenia): Pôvodná referencia nájdená: Ivanka pri Dunaji, 6. júna 1962.
- `puzzle.P03.title` [puzzle window title] Nábrežná kalibrácia
- `puzzle.P03.wrong` [line after a wrong answer] **ADAM** (Adam Hruška): Nesedí to. Správne číslice sú na rytmickom nákrese na školskom dvore.
- `journal.clue.P03` [journal 'Findings' line for the puzzle clue] 3–2–6

## 4. Items first obtained in this chunk

### ITEMS · items that name the S30 place

Inventory texts: the look (right click in the bag), the name and the tooltip that says what the item is for.

- Item NODEMAP: from „Zarovnať fóliu s mapou“ (B16); used in B17, B22; used up by — (stays)
  - `item.NODEMAP` [right-click look in the bag (Adam)] Mapa vedie k Deziderovej garáži a k meraciemu bodu na nábreží. Ktorý rok ukáže, zistím až meraním.
  - `item.NODEMAP.name` [inventory name (hover in the bag, action sentences)] Úplná mapa meracích uzlov
  - `item.NODEMAP.purpose` [inventory tooltip: what the item is for] Ukázať Deziderovi; potrebná pri meraní na nábreží v roku 1995.
- Item COIL: from „Ukázať úplnú mapu uzlov“ (B17); used in B20; used up by B20
  - `item.COIL` [right-click look in the bag (Adam)] Izolovaná meracia cievka. Patrí do kruhového držiaka v prístrešku na nábreží.
  - `item.COIL.name` [inventory name (hover in the bag, action sentences)] Deziderova meracia cievka
  - `item.COIL.purpose` [inventory tooltip: what the item is for] Nasadiť do držiaka v nábrežnom meracom prístrešku.
- Item METRONOME: from „Požičať si metronóm na meranie“ (B18); used in B21; used up by B21
  - `item.METRONOME` [right-click look in the bag (Adam)] Emilov metronóm, požičaný na meranie. Emilovi ho potom vráti Dezider.
  - `item.METRONOME.name` [inventory name (hover in the bag, action sentences)] Emilov metronóm
  - `item.METRONOME.purpose` [inventory tooltip: what the item is for] Nezávislý rytmus pre meranie na nábreží v roku 1995.

## 7. Step hints (ui.csv)

### HINTS · step hints of quest M07 „Rytmus na Dunaji“

The hint screen shows one step hint per open main action, in play order.

- `ui.hint_step.B16` [ui] V brašni spoj priehľadnú fóliu K-17 s mapou uzlov, fóliu otoč o 180° a potvrď.
- `ui.hint_step.B17` [ui] Úplnú mapu meracích uzlov použi na Dezidera v jeho garáži v Petržalke.
- `ui.hint_step.B18` [ui] Na Karloveskom nástupišti sa s Emilom porozprávaj o téme „Metronóm na meranie“.
- `ui.hint_step.B19` [ui] Na školskom dvore si prečítaj rytmický nákres.
- `ui.hint_step.B20` [ui] Deziderovu meraciu cievku použi na držiak v nábrežnom meracom prístrešku.
- `ui.hint_step.B21` [ui] Emilov metronóm polož na stolík s rytmickou značkou v nábrežnom prístrešku.
- `ui.hint_step.B22` [ui] Keď máš zachránenú kazetu aj úplnú mapu, nastav na meracom stojane v nábrežnom prístrešku 3–2–6.
