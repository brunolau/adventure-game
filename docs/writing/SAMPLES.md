# Posledný zvonec – the new Slovak texts: 25 before/after samples

For the product owner. In October 2026 you said the texts "basically make no sense". Since then all Slovak player
texts have been rewritten in four chunks (2020, 1995, 1960 + 1982, 2035 + cutscenes + UI). A writer
did each chunk and an editor checked it. Then everything was merged and checked once more across the
chunks. **The story, the puzzles, their solutions and the item recipes are unchanged.** Only the
wording changed.

What changed, in numbers:

| | |
|---|---|
| Texts the player can see | 2 947 (dialogue 756, world 1 872, UI 319) |
| Rewritten texts from game.json (lines, looks, goals, journal, hints, names, labels, epilogue) | 1 445 |
| Rewritten UI texts (menus, help, bag, journal) | 16, and one design-only UI line removed |
| Rows in `sk_overrides.csv` (1 445 new ones plus 1 from TEXT-01 that stays) | 1 446 |
| Automatic checks | `extract_strings.py` OK, `check_strings.py` 0 errors, `check_rewrite.py` 0 errors, glossary self-test OK, `dotnet test` 294 passed, engine acceptance m1 + m2 passed |

Every sample shows the old text, the new text and the reason. "Before" is the text in
`design-doc/game.json`, which is still the source and has not been edited.

## 2020 – Chorvátsky Grob, Čierna Voda, Dúbravka

**1. The joke now follows the line before it** (Mira at the window, then Adam)

| | |
|---|---|
| Before | MIRA: *Ďakujem. Keď pôjdeš bočným chodníčkom, uvidíš ma cez okno. Zavolaj mi, sklo má mizernú akustiku.*<br>ADAM: *Konečne hodnotenie, v ktorom za nič nemôžem.* |
| After | MIRA: *Ďakujem. Choď bočným chodníčkom k oknu a zavolaj mi. Cez sklo by si ma nepočul.*<br>ADAM: *Dobre. Dva metre a telefón. Bližšie sme sa celý mesiac nerozprávali.* |
| Why | The old punchline did not answer anything Mira said. The new one is about the lockdown, which is what the scene is about. |

**2. Ela's punchline** (Adam: *Viem. Babka mi to povedala skôr ako ty. Dvakrát.*)

| | |
|---|---|
| Before | ELA: *To nie je epidemiologická otázka.* |
| After | ELA: *Tak to máš potvrdené z dvoch zdrojov.* |
| Why | The old line had no connection to Adam's. The new one answers him and keeps the dry tone. |

**3. Topic and answer belong together** (topic label + Mira's first line)

| | |
|---|---|
| Before | Topic *Spýtať sa na staré krabice* → *Roman mi dal krabice do samostatnej dielne. V puzdre je malý prístroj. Začal znieť, aj keď je odpojený.* |
| After | Topic *Potrebuješ ešte niečo?* → *Roman mi preniesol krabice do záhradnej dielne. Je v nich malý prístroj, ZVON. Ozýva sa, hoci je odpojený.* |
| Why | At this point Adam knows nothing about the boxes, so he could not ask about them. ZVON is now named here, so Adam's later question *Prečo práve ZVON?* has something to refer to. |

**4. A look that contradicted its side quest** (pán Jozef at the notice board)

| | |
|---|---|
| Before | *Pán Jozef má lupu pripravenú ako nástroj verejnej kontroly.* |
| After | *Pán Jozef so skladacou lupou. Na výveske prečíta všetko okrem QR kódu.* |
| Why | The old line was a bureaucratic joke. The new one tells the player what his problem is (side quest Q2). |

**5. A wrong answer that helps** (shape panel P01)

| | |
|---|---|
| Before | *Tvary sa nezhodujú. Prístroj nič nespustil.* |
| After | *Tieto tvary k sebe nepatria. Schéma nad panelom spája rovnaký s rovnakým.* |
| Why | A wrong-answer line now says where the clue is. The solution is the same. |

**6. A level-3 hint without internal ids**

| | |
|---|---|
| Before | *G01 brašna → G02 Ela → lístok na Danu → nákup na stolík → rozhovor s Mirou pod zatvoreným oknom.* |
| After | *Servisná brašna v garáži → Ela: téma „Babkin nákup“ → nákupný lístok na Danu → taška s nákupom na stolík pred bránkou → pod zatvoreným oknom Mira: téma „Potrebuješ ešte niečo?“* |
| Why | Hints use only names the player sees in the game: items, places and the exact topic names in quotes. All hints now use the same form. |

**7. Thirty-eight years in the jar** (Adam opens the jar in 2020)

| | |
|---|---|
| Before | *Ten istý kus. Jediná súčiastka, na ktorú som dnes čakal tridsaťosem rokov a päť minút.* |
| After | *Ten istý kus. Na žiadnu súčiastku som ešte nečakal tridsaťosem rokov a päť minút.* |
| Why | The joke stays. The old sentence said he waited for it "today", and that broke the logic. |

## 1995 – Bratislava

**8. The little namesake** (Adam introduces himself to the caretaker Tóno)

| | |
|---|---|
| Before | TÓNO: *Máme tu malého s tým menom.* |
| After | TÓNO: *Adam Hruška? Jedného takého už máme. Má desať rokov a chodí do krúžku.* |
| Why | *Malý* could mean "short". The running joke (ten-year-old Adam is in the club) only works if it is clear. |

**9. Zita at the kiosk** (topic label + her answer)

| | |
|---|---|
| Before | Topic *Čerstvé správy* → *Čerstvé sú za príplatok. O včerajších ti poviem sama.* |
| After | Topic *Máte dnešné noviny?* → *Čerstvé správy máš v novinách za pár korún. Tie včerajšie ti poviem zadarmo.* |
| Why | The label is now a question Adam would ask. A newspaper cost a few crowns in 1995, so "za pár korún" fits the year. |

**10. First entry into Pali's repair shop**

| | |
|---|---|
| Before | *Opravovňa. V deväťdesiatom piatom sa pokazené veci ešte nevolali nový model.* |
| After | *Opravovňa. Tu sa pokazené veci ešte opravujú, nie vyhadzujú.* |
| Why | The old line was hard to follow. The new one makes the same point in plain words, and *ešte* carries the year. |

**11. A clue in its own sentence** (Alena hands over the photo)

| | |
|---|---|
| Before | *Tu máš pozitív. K-17. Viera z antikvariátu drží mapové prílohy osobitne. Negatív založím späť pre archív.* |
| After | *Tu je pozitív. Na stole je číslo K-17. Mapové prílohy drží Viera v antikvariáte. Negatív vrátim archívu.* |
| Why | K-17 now has its own sentence, so the player notices it (P02). Alena says *vy* to Adam everywhere, as VOICES.md sets. |

**12. Viera's joke** (Adam: *Máte niečo o cestovaní v čase?*)

| | |
|---|---|
| Before | *Vráť sa včera, práve som to predala.* |
| After | *Príďte včera. Poslednú knihu som práve predala.* |
| Why | She now says *vy* to Adam, as she does everywhere else. *Poslednú knihu* tells us what she sold. |

## 1960 – Ivanka pri Dunaji, and 1982 – Dúbravka

**13. A calque removed** (after Oto: *…Tu je lístok na kožu a nity. Dierovač vám požičia Lída v sále, ak jej pomôžete.*)

| | |
|---|---|
| Before | ADAM: *Na cestu v čase je tu veľmi veľa remeselnej výroby.* |
| After | ADAM: *Myslel som, že pri cestovaní v čase bude menej kože a nitov.* |
| Why | The old line read like a translation. The new one is natural spoken Slovak, and Adam is joking about himself. |

**14. A reply that makes sense** (Štefan: *…Len ju nasypte do misky a odstúpte, nech sa nesplaší.*)

| | |
|---|---|
| Before | ADAM: *Prvý raz som dostal návod, ktorému rozumie aj adresát.* |
| After | ADAM: *Dva kroky a žiaden lístok. To zvládnem.* |
| Why | The old line did not follow from what Štefan said. The new one plays on the paper slips Adam has been carrying around all day. |

**15. Journal notes instead of "Dokončené: …"**

| | |
|---|---|
| Before | *Dokončené: Zobrať Rudov zabudnutý scenár.* |
| After | *Na povale som našiel Rudov scenár.* |
| Why | The journal used to repeat the action's button text. Now it reads like Adam's own notebook. All "Dokončené: …" entries are gone. |

**16. The password, written as a password** (twelve-year-old Tóno, 1982)

| | |
|---|---|
| Before | *Ja nakreslím mapu. A keď sa stretneme potom, povedz lastovička sa vracia.* |
| After | *Ja nakreslím mapu. A keď sa raz zase stretneme, povedz: „Lastovička sa vracia.“* |
| Why | In quotes it reads as the exact sentence the player must say in 1995 (the topic *Heslo „Lastovička sa vracia“*). |

**17. A topic label as Adam's question** (Šimon answers first)

| | |
|---|---|
| Before | Topic *Potvrdiť ochranu stromu a servisného múrika* → *Zapísané: zdravá lipa, ohrádka a trasa vozíka mimo koreňov…* |
| After | Topic *Zapíšete lipu aj múrik?* → *Zapísal som to: lipa s ohrádkou, vozík pôjde mimo koreňov. A k múriku bude stále prístup kvôli servisu.* |
| Why | Labels used to sound like work orders. Now they are something a person would say. The facts are the same: tree, guard, cart route, access to the wall. |

## 2035 – Jasná

**18. A line that contradicted the story** (Viktor agrees)

| | |
|---|---|
| Before | *Súhlasím. Zastavíme zápis, vrátime originály. A zverejním, čo som urobil.* |
| After | *Súhlasím. Zápis vypneme natrvalo a originály vrátime. A zverejním, čo som urobil.* |
| Why | The switch had already paused the write a few steps earlier. Now Viktor says what is still left to do. |

**19. Tamara hands over the reader** (Adam: *Posiela ma Nina. Potrebujem prečítať túto starú školskú kazetu.*)

| | |
|---|---|
| Before | *Toto číta analóg aj servisnú pamäť. Vezmi si lokálnu čítačku. Kávu ti dám, keď sa prestanú strácať mená na objednávkach.* |
| After | *Vezmi si túto čítačku, prečíta kazetu aj servisnú pamäť. Kávu dostaneš, až mi z objednávok prestanú miznúť mená.* |
| Why | The player gets the reader in this exchange, so the line now plainly hands it over. *Analóg* is gone. |

**20. The cable car without a third copy of the same joke**

| | |
|---|---|
| Before | *Prvá etapa je Biela Púť–Priehyba. Tento nástup sa dá vysvetliť aj bez fyzikálneho výskumu.* |
| After | *Prvý úsek: Biela Púť – Priehyba. Obyčajná kabínka, žiadne uzlové hodiny.* |
| Why | The same joke ("travel I finally understand") came three times in a row. The cutscene caption and the next room's entry are different now too. |

**21. A look at Viktor**

| | |
|---|---|
| Before | *Viktor nespal a veľmi chce, aby to malo zmysel. Nebezpečná kombinácia pri veľkom vypínači.* |
| After | *Viktor nespal a veľmi chce, aby to celé malo zmysel. Taký človek by nemal stáť pri veľkom vypínači.* |
| Why | The joke is the same. The old line ended on an abstract noun, and the new one ends on the person. |

**22. A locked exit that says what to do**

| | |
|---|---|
| Before | *Na nástup potrebujem riadny spiatočný lístok od Sáry.* |
| After | *Na lanovku potrebujem lístok. Vybaví mi ho Sára v klientskom centre.* |
| Why | The old line sounded like an official form. The new one says where Sára is. |

**23. Epilogue** (pán Jozef reads the large notice to a neighbour)

| | |
|---|---|
| Before | *Vidíte? Netreba mať účet, stačí mať písmená.* |
| After | *Vidíte? Netreba žiadny účet. Stačí veľké písmo.* |
| Why | Jozef never wanted an app. He wanted large print. |

## UI

**24. The bag no longer shows design notes**

| | |
|---|---|
| Before | Bag detail card: name, Adam's look, and then *Účel: Dôkaz Súhlas a odblokovanie časovej adresy 2035.* |
| After | Name and Adam's look only, e.g. *Potvrdené odovzdanie 2020* – *Krabica Z-17: výdajné miesto, Roman, dielňa. Babka súhlasila cez zaznamenaný hovor, do domu nemusel nikto.* |
| Why | The *Účel* line was a design note: it told the player what to do with the item. The bag now shows only the name and the look, and the `ui.inventory.purpose` line is deleted. Where only the purpose carried a clue, the look now carries it. For example, the new ceramic bridge now ends with *Ukryjem ho v suchom pohári.* The journal heading *Vodidlá k hádankám* is now *Vodidlá*, because *hádanka* was design jargon. |

**25. Menus and system messages**

| | |
|---|---|
| Before | *Len o krok bokom, tadiaľto sa nedostanem.* · *I – inventár* · *Kontrolný bod pred finále* · *Titulky* (menu, the same word as subtitles) |
| After | *Tadiaľto neprejdem.* · *I – brašna* · *Kontrolný bod pred záverom* · *Autori* |
| Why | The HUD calls the inventory *Brašna*, so the help text does too. *Finále* is a game term. *Titulky* meant two different things. |

## Screenshots from the game

`build/screens/writing/` has 10 screenshots with the new texts in the real engine (dialogue, look,
bag detail card, journal, hint, topic menu, locked exit, map). The list is at the end of this file.

## How to revert

All rewrites from game.json are rows in **`src/game/localization/overrides/sk_overrides.csv`**
(columns `keys,game_json,sk,note`). game.json itself has not been touched.

1. To revert one text, delete its row (search for the key, e.g. `action.G04.003`). To revert
   everything, delete every row except the header.
2. Run `python tools/extract_strings.py`, then `python tools/check_strings.py`. The generated tables
   `dialogue.csv` and `world.csv` go back to the game.json text for those keys.
3. Open the project in Godot (or run `--headless --path src/game --import`) so the `.translation`
   files are rebuilt.

The 16 UI texts are edited directly in `src/game/localization/ui.csv` (it is hand-written). To revert
them, get that file back from git. Two of them, `ui.system.path_blocked` and `ui.tutorial.right_click`,
are also Core fallbacks in `src/LastBell.Core/Text/TextKeys.cs` (`UiText`), and a test keeps them equal
to ui.csv. The bag change is in `src/game/scripts/UI/Inventory/InventoryPanel.cs` (`ShowDetail`).

The `game_json` column guards against stale rewrites. If someone later changes a text in game.json,
`extract_strings.py` shows the new game.json text instead of the old rewrite and fails with "stale sk
override" until the row is reviewed.

## How to give feedback

The easiest way is to name the **key** or quote the text, and say what is wrong ("doesn't make
sense", "Mira would never say this", "too long"). The key is in the first column of
`src/game/localization/*.csv`. Searching those files for a few words of the line finds it.

- Collect the lines in one list, or write them in `docs/writing/FEEDBACK.md` (key – what is wrong –
  optional suggestion).
- A screenshot is also fine. Each line can be traced to its key with `--lines` in the QA harness.
- You decide which rewrite stays. For every rewritten line, the reason it was rewritten is in the
  note column of `sk_overrides.csv`. The full chunk outputs and the editors' reviews are in
  `docs/writing/out/` and `docs/writing/review/`.

## Open points for you (from the editors' reviews)

These are data or story questions. Answering them is your call.

1. **Lea's speaker label** reads `Lea Kormanová (správa z roku 2032)`. If it is too long on screen,
   use `Lea Kormanová (2032)`.
2. **F08 → J05:** the F08 goal names only the switch. The player learns that the bridge goes into
   Atlas's connector from the connector's look and from hint 2. Before, the item's *Účel* line also
   said it. Should the goal name the bridge too?
3. **Oto and the jar:** `Oto skontroloval závit/viečko` is said in the shop, where Oto is not present.
4. **Two "servisná doska":** the word means both the workbench in the 1982 physics cabinet and the
   board in front of the cavity in the wall.
5. **Map label** `Okno školníckej dielne v roku 1982` differs from the room name `Tóno a dedo pri
   servisnom okne v roku 1982`. It is the only map label that differs.
6. A few looks have no "after" version (`look.S10.chrono` after the fuse, `look.S05.shed_door` after
   unlocking). They are worded so they are true in both states.

### Screenshot list (`build/screens/writing/`, 1920x1080, real window)

| File | What it shows |
|---|---|
| `01_topic_menu_2020_ela.png` | Topic menu with Ela: *Babkin nákup*, *Ako to zvládate?*, *Tá termoska?* |
| `02_dialogue_2020_ela.png` | Spoken line with the speaker name, and the "new goal" notice with the new objective |
| `03_look_2020_jozef.png` | Look bubble: *Pán Jozef so skladacou lupou. Na výveske prečíta všetko okrem QR kódu.* |
| `04_inventory_1960.png` | Bag in 1960: the detail card has the name and the look, no *Účel* line |
| `05_inventory_2020_selected.png` | Bag in 2020 with *Potvrdené odovzdanie 2020* selected |
| `06_journal_goals_1982.png` | Journal, goals: quest goal and current objective (1982) |
| `07_journal_findings_1982.png` | Journal, findings: *Vodidlá* (puzzle clues) and progress notes |
| `08_hint_level3_1982.png` | Hint screen with all three levels open (M11B chain) |
| `09_locked_exit_2035.png` | Locked exit at Biela Púť: *Na lanovku potrebujem lístok. Vybaví mi ho Sára v klientskom centre.* |
| `10_topic_menu_2035_robot.png` | Topic menu with Očko (2035) |
| `11_map_1995.png` | Map 1995: room names and regions |

All texts fit their boxes. Bag slot captions are cut to two lines, so a long item name ends in "…"
in the slot (*Prenosný chronometer…*, *Overený odtlačok z roku…*). The full name appears on hover
and in the detail card. This is how the slot is built, and it was the same before the rewrite.

Scripts and logs: `build/screens/writing/logs/` (`shots.sh`, `acceptance_m1.txt`, `acceptance_m2.txt`).
