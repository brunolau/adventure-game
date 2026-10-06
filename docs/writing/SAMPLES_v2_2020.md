# Posledný zvonec – 2020 in the new style: 20 samples and what to try

For the product owner (2026-10-06). On 2026-10-06 you asked for three things. First, Polda-style humour that makes
sense. Second, conversations 2–3 times longer, with more topics. Third, every text goes Claude → GPT → Claude.
This file shows the result for the 2020 chapter: Chorvátsky Grob, Čierna Voda and Dúbravka 2020. It is the first
chapter that went through the whole method (`design-doc/WRITING_METHOD.md`). The other eras follow the same way.

**The story, the puzzles, the items and the clues are unchanged.** `game.json` was not edited. New lines go
before, between and after the original lines. A clue stays in its own line and keeps its facts. The automatic
check `check_rewrite.py` verifies this.

## What changed in 2020, in numbers

| | handoff | now |
|---|---|---|
| Story conversations made longer (G02–G05, C01–C05, D02, D03, D07, Q1A, Q1C, Q2A–Q2C, Q9E) | 18 conversations, 70 lines | 151 lines (2.2×) |
| Repeatable small-talk topics made longer | 16 topics, 42 lines | 87 lines (2.1×) |
| New optional topics (2–3 per person: Ela, Dana, Roman, Lenka, Jozef, Mira, Tóno, Jana) | – | 22 topics, 104 lines |
| Bus Čierna Voda ↔ Dúbravka with first-ride lines (replaces the car from the street) | – | 2 exits, 3 lines |
| Existing 2020 texts rewritten again for tone (old ironic one-liners removed) | – | 33 texts + 11 overlay lines |
| GPT language check (openai/gpt-6-astra-pro), every flag decided by Claude | – | 4 runs (writing pass + check, tone pass + check): 82 flags, 32 accepted, 37 adapted, 13 rejected |

Where the texts live: `src/game/localization/overrides/sk_overrides.csv` (existing lines) and
`src/game/data/content_ext/dialogue_ext.json` (new lines and topics). The drafts and review records are in
`docs/writing/out/C1.csv`, `docs/writing/out/C1_ext.json` and `docs/writing/review_gpt/C1*`.

How to read the samples: **Handoff** is the text in `game.json`. **First rewrite** is the 2026-10-05 version (the
one you found cringy). **Now** is what the game shows today. Lines marked **+** are new.

---

## A. Story conversations (longer, with the clue in the same place)

**1. Ela and the shopping (G02)**

| | |
|---|---|
| Handoff | ADAM: *Som tu kvôli babkinmu nákupu.* · ELA: *Dana ho pripravila. Tu je lístok a čisté rúško…* · ADAM: *Viem. Dnes jej ani cez plot nevysvetlím, že som dospelý.* · ELA: *To nie je epidemiologická otázka.* |
| First rewrite | 4 lines, ending ELA: *Tak to máš potvrdené z dvoch zdrojov.* |
| Now (9 lines) | ADAM: *Ahoj, Ela. Babka vraví, že tu pre ňu máte objednávku.*<br>**+** ELA: *Máme. Volala o siedmej, či je hotová, a o ôsmej, či si už vstal.*<br>**+** ADAM: *A čo si jej povedala?*<br>**+** ELA: *Že budíček nerobíme. Tak si ho u nás objednala na zajtra o šiestej.*<br>ELA: *Dana ju má pripravenú. Tu máš lístok a náhradné rúško. Tašku nechaj babke vonku a zavolaj jej.*<br>ADAM: *Viem. Babka mi to povedala skôr ako ty. Dvakrát.*<br>ELA: *Tak to máš tretíkrát. A do obeda ti to zopakuje ešte aj Dana.*<br>**+** ADAM: *Ak ti babka zavolá ešte raz, povedz jej, že už idem.*<br>**+** ELA: *Poviem. Mám ju v zozname hneď za zemiakmi.* |
| Why | The joke comes from a person: Mira organises everyone. It is the running gag of the chapter. |

**2. Dana and the shopping list (G03)**

| | |
|---|---|
| Handoff | ADAM: *Toto je babkina objednávka.* · DANA: *Čaj, vločky, zemiaky…* · ADAM: *A dva ušká. Rozumiem.* · DANA: *Vidíš, vieš to.* |
| First rewrite | 4 lines, same order. |
| Now (9 lines) | **+** DANA: *Ahoj. Ten lístok poznám naspamäť. Pani Hrušková píše každý týždeň to isté, len iným perom.*<br>**+** ADAM: *Tak prečo ho vôbec píše?*<br>**+** DANA: *Aby som videla, že je pani Hrušková v poriadku. Rukopis mi povie viac ako telefón.*<br>… then the original lines, and Adam asks whether she sells a bit of free time too. **+** DANA: *Čas nepredávam. Ten si musí každý ušetriť sám.* |
| Why | A small warm moment about lockdown: the handwriting tells Dana that Mira is fine. |

**3. Shopping at the gate (G04)**

| | |
|---|---|
| Handoff | ADAM: *…Odstupujem.* · MIRA: *…Zavolaj mi, sklo má mizernú akustiku.* · ADAM: *Konečne hodnotenie, v ktorom za nič nemôžem.* |
| First rewrite | ADAM: *Dobre. Dva metre a telefón. Bližšie sme sa celý mesiac nerozprávali.* |
| Now (7 lines) | **+** MIRA: *Vidím. Ešte krok dozadu. Tak, teraz máš presne dva metre.*<br>**+** ADAM: *Ty si to vymeriavala?*<br>**+** MIRA: *V pondelok, ešte pred karanténou. Som inžinierka, nie veštica.*<br>MIRA: *Ďakujem. Choď bočným chodníčkom k oknu a zavolaj mi. Cez sklo by si ma nepočul.*<br>ADAM: *Dobre. Bočný chodníček a telefón. Takto blízko sme sa celý mesiac nerozprávali.*<br>**+** MIRA: *A ešte niečo pre teba mám. Ale to až pri okne.* |
| Why | The handoff punchline answered nothing. Now Mira the engineer has measured the two metres herself, and the last line leads to the next scene. |

**4. ZVON in the boxes (G05)**

| | |
|---|---|
| Handoff | 5 lines: the boxes, *Asi kondenzátor*, the key, *Prečo sa volá ZVON?* |
| First rewrite | The same 5 lines, smoother Slovak. |
| Now (10 lines) | After the key: **+** ADAM: *Do domu nie, do dielne áno. Babkine pravidlá poznám.* **+** MIRA: *Jedno si zabudol: najprv počúvaj, až potom rozoberaj.* After ZVON: **+** ADAM: *My? Kto my?* **+** MIRA: *Ja a jeden šikovný človek. Viac ti poviem, keď prestaneš hovoriť o kondenzátoroch.* **+** ADAM: *Tak idem pre kľúč. A o kondenzátore sa ešte porozprávame.* |
| Why | Adam's quirk (it is always the capacitor) becomes a callback, and Mira hints at Oto without giving away the story. |

**5. Mira recognises Adam (C01)**

| | |
|---|---|
| Handoff | 7 lines: the fingerprint, the return bridge, Oto and Tóno in 1982. |
| First rewrite | The same 7 lines. |
| Now (16 lines) | **+** ADAM: *Babka, som späť. Aspoň v správnom roku. Musím ti niečo ukázať.*<br>**+** MIRA: *Prilož to k sklu. Okuliare mám na nose od rána pre prípad, že sa vrátiš.*<br>MIRA: *Tak to si bol ty. Ten odtlačok si pamätám.*<br>**+** MIRA: *Aj tie topánky. V Ivanke sa o nich hovorilo až do Vianoc.*<br>**+** ADAM: *Ty si si ma celé tie roky pamätala?*<br>**+** MIRA: *Topánky áno. Tvár som si k nim priradila až teraz.*<br>… the clue lines unchanged … **+** ADAM: *Technický majetok. Znie to, akoby som išiel po traktor.* … and at the end Mira asks him to photograph the school yard. |
| Why | A callback to 1962 (Adam's strange shoes) and a gentle, funny recognition. The clue about Oto, Tóno and 1982 is unchanged. |

**6. Tóno at the window, still formal (D02)**

| | |
|---|---|
| Now (11 lines, was 5) | **+** ADAM: *Dobrý deň, pán Farkaš. Som vnuk pani Hruškovej a toto vám mám ukázať.*<br>**+** TONO: *Dobrý deň. Priložte to k sklu, prosím. Okno tento rok otváram iba pre balíky.*<br>… the clue (the service book in the cabinet, Jana lets him in remotely) …<br>**+** ADAM: *Na diaľku? Ako sa človek púšťa do kabinetu na diaľku?*<br>**+** TONO: *Jana zapne kameru, ja odomknem dvere. Ona dozerá, ja zodpovedám.*<br>… **+** TONO: *Celý deň. Rodičia volajú, ja zapisujem, kuriéri zvonia. Školník je teraz hlavne telefonista.* |
| Why | Tóno uses *vy* until he recognises Adam (D07), as the voice table requires. His jokes are dry and about his work. |

**7. Jana and the service book (D03)**

| | |
|---|---|
| Now (7 lines, was 3) | **+** JANA: *Dobrý deň. Vidím vás, len trochu zhora. Tú knihu máte správnu.* (she is on a laptop camera)<br>… the clue line with the date 7 December 1982, Oto Bielik, grandson Anton …<br>**+** ADAM: *Oto si zapisoval naozaj všetko. Taký zoznam by sa mi zišiel aj v garáži.*<br>**+** JANA: *Nie zoznam. Záznam. Zoznam sa píše pred prácou, záznam po nej.* |
| Why | The teacher corrects a word, which is her character. The joke comes from the video call itself. |

**8. Tóno recognises Adam – serious beat (D07)**

| | |
|---|---|
| Handoff | TONO: *Tak si splnil tú vec zo školy. Mal som dvanásť, teraz mám päťdesiat. Ty stále tú istú bundu.* … *Nečakal som. Žil som. Len som si pamätal miesto.* |
| Now (13 lines, was 8) | ADAM: *Lastovička sa vracia. Mostík je celý.*<br>**+** TONO: *Povedzte to ešte raz.*<br>**+** ADAM: *Lastovička sa vracia.*<br>TONO: *Tak predsa. Vtedy som mal dvanásť, teraz mám päťdesiat. A ty nosíš stále tú istú bundu.*<br>… **+** ADAM: *Tvoja mapa sedela na kameň presne.* **+** TONO: *Dedo ma naučil kresliť tak, aby tomu rozumel aj ten, kto pri tom nebol.* … and at the end **+** ADAM: *Poviem mu. Slovo od slova.* |
| Why | This beat stays plain, with no jokes. The added lines slow the moment down. Tóno switches from *vy* to *ty* on the code word: that switch is the recognition. |

**9. Roman signs (C03)**

| | |
|---|---|
| Now (8 lines, was 3) | **+** ADAM: *Ahoj, Roman. Máš chvíľu na jeden podpis?* **+** ROMAN: *Podpis? Zvyčajne ich zbieram ja od iných.*<br>ROMAN: *Z-17, z prístrešku do dielne v záhrade…* **+** ROMAN: *Niesol som ju ako chladničku, len chladničku je aspoň za čo chytiť.*<br>… **+** ADAM: *Poviem babke. Ešte ťa opraví, že si zabudol na muškát v okne.* |
| Why | A courier's view of the world: everything is a parcel. The ending calls back to Mira, who corrects everyone. |

**10. The name that faded (C04)**

| | |
|---|---|
| Now (7 lines, was 3) | **+** ADAM: *Roman podpísal. Vraj to bola najťažšia krabica mesiaca.* **+** ELA: *To hovorí o každej tretej. Ale pri tejto mu verím.*<br>ELA: *…Zvláštne, jej meno pred chvíľou bledlo. Teraz drží.*<br>**+** ADAM: *Bledlo? Na papieri?* **+** ELA: *Myslela som, že mi pero prestáva písať. Ale pero píše normálne.* |
| Why | The strange fact (the name fading) gets a natural follow-up question instead of a wink. |

**11. Bodka's ball (Q1C)**

| | |
|---|---|
| Handoff | ADAM: *Oceňujem. Dnes mám veľa dialógov.* (a meta joke about the game) |
| First rewrite | ADAM: *Oceňujem. Konečne niekto, kto hovorí k veci.* |
| Now | ADAM: *Prijímam. Aj so slinami.* **+** LENKA: *Teraz ju zasa stratí. Ale aspoň už vieme kde.* **+** ADAM: *Nabudúce mu na ňu napíš telefónne číslo.* **+** LENKA: *Napísala som. Zjedol ho.* **+** BODKA: *Haf!* |
| Why | No meta jokes. The dog gets the last word, as in all of his scenes. |

**12. Jozef and the QR code (Q2A)**

| | |
|---|---|
| Now (6 lines, was 3) | JOZEF: *Ak budeš taký dobrý, mladý pán. Potrebujem len hodiny výdaja…*<br>**+** ADAM: *Hodiny sú v tom QR kóde. Stačí naň namieriť telefón.*<br>**+** JOZEF: *Namieril som naň lupu. Ukázala mi ten istý štvorček, len väčší.*<br>… **+** JOZEF: *A nech je tam aj telefón. Do telefónu hovoriť viem, do štvorčeka nie.* |
| Why | Jozef is analogue and proud of it. It is a real misunderstanding with a payoff, not a gag about old people. |

## B. Small-talk topics (the old ironic tags removed)

**13. Ela: "Ako to zvládate?"**

| | |
|---|---|
| Handoff and first rewrite | ADAM: *Tak aspoň jedna krivka ide dobrým smerom.* (the pattern you disliked) |
| Now | ADAM: *Tak ma pripíš medzi pomocníkov.* **+** ELA: *Už tam si. Babka ťa nahlásila ráno, aj s poznámkou „ochotný, ale mešká“.* **+** ADAM: *Meškám? Veď som prišiel o desiatej.* **+** ELA: *Ona ťa čakala o deviatej. Aj to je v zozname.* |

**14. Roman: "Ako ide rozvoz?"**

| | |
|---|---|
| First rewrite | ADAM: *Navigácia s historickou vrstvou. Poznám.* |
| Now | ADAM: *A ktorý to je?* **+** ROMAN: *Ten zelený. Prefarbili ho v júli, ale pre dedinu bude žltý ešte desať rokov.* **+** ADAM: *A tá druhá adresa?* **+** ROMAN: *Ten istý dom. Bývajú v ňom dve rodiny a obe zabudli, že je už zelený.* |

**15. Tóno: "Škola je taká tichá"**

| | |
|---|---|
| First rewrite | ADAM: *Tú vetu si zapamätám.* |
| Now | ADAM: *Teraz tu počuť aj vlastné kroky.* **+** TONO: *Aj každé dvere. Konečne viem, ktoré treba namazať.* **+** ADAM: *A ktoré vŕzgajú najviac?* **+** TONO: *Tie do kabinetu. Vŕzgali už vtedy, keď som tam chodil ja.* |

**16. Lenka: "Bodkovo meno"**

| | |
|---|---|
| First rewrite | ADAM: *Takže Bodka s pokračovaním.* |
| Now | ADAM: *Bodka, ešte chceš niečo dodať?* **+** BODKA: *Haf!* **+** LENKA: *Vidíš. Aj teraz.* |
| Why | The dog shows the joke, so nobody has to explain it. The topic is repeatable, so it is short. |

## C. New optional topics

**17. Ela – "Zoznamy"** (new)

> ADAM: *Koľko zoznamov vlastne máš?* · ELA: *Štyri. Nákupy, lieky, telefóny a zoznam zoznamov.* · ADAM: *A ten
> štvrtý je na čo?* · ELA: *Aby som vedela, ktorý z tých troch práve nemôžem nájsť.* · ADAM: *Babka by to
> schválila.* · ELA: *Schválila. A navrhla piaty: kto nezdvíha telefón. Si na ňom prvý.*

**18. Dana – "Predaj cez okienko"** (new)

> ADAM: *Ako sa ti predáva cez okienko?* · DANA: *Ľudia sa menej hádajú. Cez sklo to nemá ten efekt.* · ADAM: *A čo
> ti najviac chýba?* · DANA: *Klebety. Cez okienko sa dajú povedať len tie rýchle.* · ADAM: *Rýchla klebeta je tiež
> klebeta.* · DANA: *Nie. Rýchla klebeta je len správa. Na poriadnu treba lavičku.*

**19. Jozef – "Autobus do mesta"** (new, appears after C01) **and the bus itself**

> ADAM: *Ako sa odtiaľto najlepšie dostanem do Dúbravky?* · JOZEF: *Autobusom z tejto zastávky do mesta a tam
> prestúpiš. Rúško si nezabudni, šofér je prísnejší ako ja.* · ADAM: *Prísnejší ako vy?* · JOZEF: *Ja prosím len o
> veľké písmo. On ťa bez rúška nepustí ani na schod.*

First bus ride, at the Čierna Voda stop: ADAM: *Autobusom do mesta a potom prestup do Dúbravky. Rúško mám, lístok
tiež.* · *Autobus je skoro prázdny. Každý sedí pri svojom okne, akoby si ho rezervoval.* Then the card
"Dúbravka · Autobusom". The first ride back from Dúbravka: *Späť do Čiernej Vody. Odtiaľ už do Grobu trafím aj
poslepiačky.*

**20. Tóno – "Kovová lastovička"** (new, appears only after D07, so Tóno already says *ty*)

> ADAM: *Tú kovovú lastovičku si urobil sám?* · TONO: *Z plechu, ešte ako učeň. Drevenú mám doma na poličke.* ·
> ADAM: *Prečo práve lastovička?* · TONO: *Lebo sa vracia na to isté miesto. Mne sa to v dvanástich zdalo ako
> dobrý plán.*

---

## What to try in `play.bat`

Double-click `play.bat` for a new game. The prologue is all 2020:

1. **Ela** at the volunteer point: open her menu. She has six topics: *Babkin nákup*, two small-talk topics and
   the new *Dobrovoľníci*, *Nina*, *Zoznamy*. Play *Babkin nákup* first and listen to the whole conversation.
2. **Dana** at the shop window: *Stáli zákazníci*, *Predaj cez okienko*, *Karanténne nákupy*.
3. **Roman and Lenka** in the street: Lenka's *Bodkovo meno* (the dog answers), *Prechádzky*, *Keď prší*. Roman's
   *Babkine krabice* appears after you have spoken to Mira at the window (G05).
4. **Mira** at the window: *Spájkovanie* and *Telefonáty*.
5. **Jozef** at the Čierna Voda bus stop: *Tá lupa*, *Čierna Voda kedysi*.

To jump straight to the later 2020 scenes (dev jumps work in `play.bat`, which is a debug build):

| command | what you see |
|---|---|
| `play.bat -- --replay 50 --room S06` | Mira's long recognition conversation (C01): click Mira |
| `play.bat -- --replay 51 --room S07` | Jozef's new topic *Autobus do mesta*, then click the bus exit at the kerb: two first-ride lines, the "Dúbravka · Autobusom" card, arrival at the Dúbravka stop. Press **M**: the map shows the regions first (Dúbravka, Chorvátsky Grob). Click a region to see its places. Inside a region you can travel freely; another region only through its stop. |
| `play.bat -- --replay 52 --room S56` | Tóno at the window, formal *vy* (D02), and his topics *Zväzok kľúčov*, *Deti pri okne* |
| `play.bat -- --replay 55 --room S51` | the bus back from Dúbravka to Čierna Voda (one first-ride line, then the card) |
| `play.bat -- --replay 68 --room S56` | the recognition (D07): click Tóno |
| `play.bat -- --replay 69 --room S56` | after the recognition: *Kovová lastovička*, with Tóno saying *ty* |

Please note in particular:
- Are the conversations too long anywhere? Each one is now 2–3 times longer. You can skip a line with a click or
  Enter.
- Do the jokes land? Is anything still "cringy"? Name the line and I will rewrite it through the same three steps.
- The bus: is it clear that Dúbravka is reached from the Čierna Voda stop?

## Checked in the engine (screenshots)

`build/screens/v2_2020/`: the topic menus of all eight 2020 people (`01`–`10`), conversations with the longest line
of the chapter (113 characters, two rows, `11`), the recognition (`12`) and new topics (`02`, `13`, `14`).
`build/screens/v2_2020/travel/`: the bus there and back with lines and cards, and the region map for 2020 and 1995.

- Text fits: the longest 2020 line breaks into two rows inside the subtitle box. Nothing overlaps.
- Topic menus: at most 6 topics plus *Ukončiť rozhovor* (Ela, Jozef), and every one fits without scrolling. The
  panel sits on the side away from the speakers and has room for 8 topics before it scrolls.
- Region map: the region view is clear. One thing to look at: inside **Chorvátsky Grob** the ten places are wider
  than the panel. The last card (*Dielňa…*) is cut at the right edge and you reach it with the horizontal scroll
  bar. It works, but a tighter layout would look better (a UI task, not a text task).

## Automatic checks (2026-10-06, after the merge)

| check | result |
|---|---|
| `extract_strings.py`, `check_strings.py` | OK, 0 errors (dialogue 989, world 1894, ui 476 keys; 1465 overrides applied) |
| `check_rewrite.py docs/writing/out/C1.csv --chunk C1`, `--overlay-only`, `--self-test` | OK, 0 errors, 0 warnings (261 overlay texts) |
| `content_ext.py check` | OK: 34 longer exchanges, 22 new topics, 233 new lines, bus S07 ↔ S51, 13 map regions |
| `check_blocking.py` | 68 rooms, 0 errors |
| `dotnet test src/LastBell.sln` | 361 passed, 3 skipped, 0 failed |
| `--acceptance m1` / `m2` (headless) | 0 failures each |
| `--acceptance travel` (hidden window) | TR01–TR03 passed (evidence in `build/screens/v2_2020/travel/`) |
| `--play-all` routes (headless) | route A (`--save-load-each`), route B (`--interleave early --all-lines`), route C7 (`--interleave seed:7 --skip-cutscenes`): 127/127 actions, 0 blockers, 0 failures each |

Line counts that grew with the longer conversations (no test has them hard-coded; they are the reference
numbers of `docs/MILESTONE5.md`): route A shows **621** lines (was 537). Route B shows **1007** lines and **990** distinct
line ids (was 774 / 757), with the same 471 look texts. Logs and coverage files are in `build/v2_2020/`.

## Open points

- D07: Tóno's *A ty nosíš stále tú istú bundu* is a light touch in a serious beat. It is in the handoff, so it
  was kept. Tell me if you want it plainer.
- G04 staging (from the GPT check): Mira speaks to Adam at the gate before she tells him he would not hear her
  through the glass. The handoff has the same order.
