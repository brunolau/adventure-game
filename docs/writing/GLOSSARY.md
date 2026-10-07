# Posledný zvonec – glossary and protected facts

Canonical Slovak names for people, places, items, devices and recurring ideas, so that all four
chunks use the same words; and the facts that must survive every rewrite. The machine-readable
part (regexes for names, terms, protected facts, deprecated words, length limits) is
[glossary.json](glossary.json); `tools/check_rewrite.py` uses it. Change both files together and
run `python tools/check_rewrite.py --self-test`.

Rules:

- Use the canonical form. Synonyms are allowed in speech only where listed ("in speech").
- A **bold** name in the tables is a decided rename: every key that shows the old name (item name,
  looks, goals, hints, exit labels) is updated in the same chunk.
- Nobody renames anything else. If you think a name is wrong, write it in your note.

## 1. Address and naming conventions

- Adam calls his grandmother **babka** (*babka, babky, babke, babku, babkou; babkin nákup*). Every
  other text that is not Adam speaking (objectives, journal, hints, item and room names) says
  **Mira** (*Miry, Mire, Miru, Mirou; Mirin, Mirina, Mirino*). Neighbours and strangers say
  **pani Hrušková**; Oto and other 1960 colleagues say **Mira**. The diminutive *Mirka/Mirkin* is
  not used.
- Ages in system texts are written as qualifiers, never as id suffixes: *dvanásťročný Tóno*,
  *mladá Mira*, *Tóno pri servisnom okne v roku 2020* — never *Tóno 12*, *Tónovi 2020*, *Jana 82*.
- Years in system texts: *v roku 1982*, *z roku 1995*, *Jasná 2035* (map/era style) — consistent
  per text type.

## 2. People

| Speaker id(s) | Canonical name | In speech | Declension / notes |
|---|---|---|---|
| ADAM | Adam Hruška | Adam; *pán Hruška* (officials) | Adama, Adamovi, Adamom |
| ADAM10 | Adam (10 rokov, nahrávka 1995) | — | voice on the 1995 tape |
| MIRA20, MIRA95, MIRA60 | Mira Hrušková | babka (Adam 2020), pani Hrušková, Mira | see § 1; *mladá Mira* (1960) |
| TONO82, TONO, TONO20 | Anton Farkaš | Tóno | Tóna, Tónovi, Tónom; Tónov, Tónova; *školník* (1995, 2020); *dedo* = Oto |
| OTO, OTO82 | Oto Bielik | Oto, *dedo* (Tóno) | Ota, Otovi, Otom; Otov, Otova |
| JANA82, JANA95, JANA20, JANA35 | Jana Vargová | Jana | Jany, Jane, Janu; Janin, Janina |
| LEA95, LEA_REC | Lea Kormanová | pani Kormanová, pani učiteľka (children) | Ley, Lei, Leu, Leou; Lein, Leina |
| VIKTOR | Viktor Korman | Viktor, pán Korman | Lea's son |
| NINA, NINA_REMOTE | Nina Švecová | Nina | Ela's daughter |
| ELA | Ela Švecová | Ela | Ely, Ele, Elu, Elou; Elin, Elina |
| DANA | Dana Valová | Dana | Dany, Dane; Danin |
| ROMAN | Roman Kováč | Roman | Romana, Romanovi; Romanov podpis |
| LENKA | Lenka Bartošová | Lenka | Lenky, Lenke |
| BODKA | pes Bodka | Bodka | male dog: Bodku, Bodkovi; *Bodkova loptička* |
| JOZEF | Jozef Mlynár | pán Jozef | Jozefa, Jozefovi |
| SONA | Soňa Urbanová | Soňa | Sone/Soni (dat. Soni), Soňu |
| ZITA | Zita Ondrušová | Zita, pani Zita | Zity, Zite |
| EMIL | Emil Belan | Emil, pán Belan | Emila, Emilovi; Emilov metronóm |
| PALI | Pavol Drobný | Pali | Paliho, Palimu, s Palim; **Paliho** opravovňa (not *Palova*) |
| VIERA | Viera Holubová | Viera, pani Holubová | 1995 bookseller; not Vera |
| ARCHIVAR / KAROL | Karol Merta | pán Merta, Karol (hints) | Karola, Karolovi |
| FOTO / ALENA | Alena Svobodová | Alena, pani Svobodová | Aleny, Alene |
| TRH / FERO | Fero Lánik | Fero | Fera, Ferovi; Ferova váha |
| MILADA | Milada Kyselová | Milada, pani Kyselová | Milady, Milade |
| JURO | Juraj Malík, **Juro Kazeta** | Juro | Jura, Jurovi; never *Juraj* (that is the painter) |
| JURAJ | Juraj Križan | Juraj | Juraja, Jurajovi; Jurajova skica |
| DEZI | Dezider Kováč | Dezider (*Dezi* only from friends) | Dezidera, Deziderovi; Deziderova garáž, cievka |
| BOZO | Božidar Fiala | Božo, pán Fiala | Boža, Božovi |
| BERTA | Berta Kovárová | pani Kovárová, Berta | Berty, Berte |
| POSTA / ALOJZ | Alojz Baran | pán Baran, Alojz (hints) | Alojza, Alojzovi |
| — | holub Béla | Béla | Bélu, Bélovi; Bélovo krmivo |
| LIDA | Lída Fialová | Lída | Lídy, Líde, Lídu; Lídin dierovač |
| RUDO | Rudolf Pavlík | Rudo | Ruda, Rudovi; Rudov scenár |
| SKLAD / STEFAN | Štefan Haluška | Štefan | Štefana, Štefanovi |
| VERA60 | Vera Nemcová | Vera | Very, Vere, Veru; Verino rydlo; 1960 draughtswoman, not Viera |
| ZUZANA | Zuzana (no surname, ever) | Zuzana; *Zuzka* (Ivanka adults, 1962) | Zuzany, Zuzane, Zuzanu, Zuzanou; *Zuzanin lístok*; 7 years old in June 1962; only in Ivanka 1962 (S37, traces in S32/S38) and as ZUZANA95 in 1995; never in 1982, 2020, 2035 |
| ZUZANA95 | Zuzana (no surname, ever) | Zuzana; *teta Zuzana* (Kubo); nobody says *Zuzka* in 1995 | as ZUZANA; 40 years old on 15 June 1995; only in S69 Pri LEALe; recognises Adam from the Ivanka park 1962; nothing about her life is ever stated |
| KUBO | Kubo | Kubo, *Kubko* | Kuba, Kubovi, Kubom; *Kubov bicykel*; 7, first-grader from a neighbouring entrance (1995, S69); a neighbour's child, never Zuzana's |
| DOBRO | učiteľ Dobrovič | súdruh učiteľ (pupils), pán učiteľ | Dobroviča, Dobrovičovi |
| RUZENA | Ružena Malá | pani Malá | Ruženy, Ružene |
| MARTA82 | Marta Dobiášová | pani Dobiášová | Marty, Marte |
| SIMON | Šimon Rybár | Šimon, pán Rybár | Šimona, Šimonovi |
| TAMARA | Tamara Kráľová | Tamara | Tamary, Tamare; Tamarina dielňa |
| BORIS | Boris Urban | pán Urban, Boris | Borisa, Borisovi |
| SARA | Sára Vrbová | Sára | Sáry, Sáre |
| ROBOT | doručovací robot Očko | Očko | Očka, Očkovi; Očkova požiadavka |
| IVAN | Ivan Horský | — | Ivana, Ivanovi |
| TURISTA | Miloš Polák | Miloš | Miloša, Milošovi |

Surnames that repeat (Kováč: Roman and Dezider; Fiala/Fialová: Božo and Lída; Urban/Urbanová:
Boris and Soňa) are coincidences. Do not suggest relationships.

## 3. Places

### 3.1 Regions and how to say "in / to"

| Place | in | to | from |
|---|---|---|---|
| Chorvátsky Grob | v Chorvátskom Grobe, *v Grobe* (speech) | do Grobu | z Grobu |
| Čierna Voda | v Čiernej Vode | do Čiernej Vody | z Čiernej Vody |
| Lúčny koník (playground, S03) | pri Lúčnom koníku, *na Lúčnom koníku* (speech) | k Lúčnemu koníku, *na Lúčny koník* (speech) | od Lúčneho koníka |
| Dúbravka | v Dúbravke | do Dúbravky | z Dúbravky |
| ZŠ Sokolíkova | na Sokolíkovej, v škole na Sokolíkovej | na Sokolíkovu | zo Sokolíkovej |
| Pri LEALe (S69, the walled courtyard by the school) | pri LEALe | k LEALu | od LEALu |
| Karlova Ves | v Karlovej Vsi | do Karlovej Vsi | z Karlovej Vsi |
| Staré Mesto | v Starom Meste | do Starého Mesta | zo Starého Mesta |
| Ružinov | v Ružinove | do Ružinova | z Ružinova |
| Miletičova | na Miletičovej, *na Miletičke* (speech) | na Miletičovu | z Miletičovej |
| Petržalka | v Petržalke | do Petržalky | z Petržalky |
| Starý most (the old bridge, S30) | na Starom moste | na Starý most | zo Starého mosta |
| Ivanka pri Dunaji | v Ivanke | do Ivanky | z Ivanky |
| Jasná | v Jasnej | do Jasnej | z Jasnej |
| Biela Púť | na Bielej Púti | na Bielu Púť | z Bielej Púte |
| Priehyba | na Priehybe | na Priehybu | z Priehyby |
| Chopok | na Chopku | na Chopok | z Chopku |
| Rotunda | pri Rotunde | k Rotunde | od Rotundy |
| Grand Jasná (hotel) | v hoteli Grand Jasná, *v Grande* (speech) | do hotela Grand Jasná | z hotela |
| Vrbické pleso | pri Vrbickom plese | k Vrbickému plesu | od Vrbického plesa |
| Funitel | vo Funiteli | na Funitel (nastúpiť) | z Funitelu |

### 3.2 Named places and businesses

| Canonical | Notes |
|---|---|
| ZŠ Sokolíkova | the real school in Dúbravka; interiors, people and experiments are invented |
| Pri LEALe | the walled courtyard ihrisko between the Sokolíkova blocks (S69, 1995). Owner decision 2026-10-07: its name in the whole game is the local name *Pri LEALe*, never *Sokolíkovský dvor*. LEAL is always in capitals and declined *pri LEALe, k LEALu, od LEALu*; room name, exit and map labels *Pri LEALe*, inside a sentence *pri LEALe* (*pod modrým smrekom pri LEALe*). No text explains what LEAL is. The plain word *dvor* for the courtyard itself stays fine (*celý dvor počuje*) |
| Lúčny koník | the real playground with the timber picnic shelter in Čierna Voda (Rekreapark by Javorová alej, opened 2015); owner decision 2026-10-06: S03 is painted there and named after it. Spelled *Lúčny koník* (only the first word capitalised), *pri Lúčnom koníku* |
| výdajné miesto (pri Lúčnom koníku) | Ela's outdoor pick-up point in the shelter of Lúčny koník (2020); the old *dobrovoľnícke výdajné miesto* stays fine in speech, goals and hints say *výdajné miesto pri Lúčnom koníku* |
| Mirina záhradná dielňa | the empty garden workshop (*predsieň* S09 + *dielňa ZVON* S10) |
| Paliho opravovňa | Karlova Ves |
| Antikvariát Pod druhou rukou | Viera |
| Fotoateliér Svetlo | Alena |
| archívna študovňa | Karol; Mira's fond is registered here |
| kazetový klub v suteréne | Juro, Ružinov |
| Deziderova garáž | Petržalka, garage number 17 |
| merací stánok na Starom moste | the small sheet-metal measuring booth on the footway of the old Starý most in 1995 (S30, P03); owner decision 2026-10-06 (it replaced the *nábrežný merací prístrešok*: no embankment, no shelter). Short forms: *v stánku*, *pri stánku* (the round table stands beside it), *na Starom moste*. Spelled *Starý most* (only the first word capitalised) |
| skúšobná čerpacia búdka, meracia miestnosť | Ivanka 1960; the door (S38) leads to the room of the first ZVON (S39) |
| povala technického archívu | Ivanka 1960, with the metal archive box |
| servisné okno (školnícke) | the same window in 1982, 1995 and 2020 with Tóno's swallow |
| servisný múrik, servisná dutina | the low wall in the school yard; the cavity in row 2, column 3 |
| Druhý život | Tamara's travelling repair workshop (sign DRUHÝ ŽIVOT on the bench by Vrbické pleso) |
| výstava Atlas, servisný pavilón, chronokomora | Atlas exhibition in the hotel salon; its own temporary pavilion and chamber by the Rotunda on Chopok |
| klientske centrum Biela Púť | Sára |

### 3.3 Rooms (69)

Room names are also exit labels and map labels; a rename changes every exit label that equals it. **Bold** = decided rename.

| Id | Year | District | Canonical name | Current |
|---|---|---|---|---|
| S01 | 2020 | Chorvátsky Grob | Adamova garáž | = |
| S02 | 2020 | Chorvátsky Grob | Ulica medzi plotmi | = |
| S03 | 2020 | Chorvátsky Grob | **Lúčny koník – výdajné miesto** | Dobrovoľnícke výdajné miesto |
| S04 | 2020 | Chorvátsky Grob | Potraviny cez okienko | = |
| S05 | 2020 | Chorvátsky Grob | **Mirina bránka** | Mirkina bránka |
| S06 | 2020 | Chorvátsky Grob | Pod zatvoreným oknom | = |
| S07 | 2020 | Čierna Voda | Čierna Voda pri výveske | = |
| S08 | 2020 | Čierna Voda | Chodník pri retenčnej nádrži | = |
| S09 | 2020 | Chorvátsky Grob | Predsieň záhradnej dielne | = |
| S10 | 2020 | Chorvátsky Grob | Dielňa ZVON | = |
| S11 | 1995 | Dúbravka | Dúbravská zastávka | = |
| S12 | 1995 | Dúbravka | Pred ZŠ Sokolíkova | = |
| S13 | 1995 | Dúbravka | Školská vstupná chodba | = |
| S14 | 1995 | Dúbravka | Trieda pamäťového krúžku | = |
| S15 | 1995 | Dúbravka | Fyzikálny kabinet | = |
| S16 | 1995 | Dúbravka | Miestnosť školského rozhlasu | = |
| S17 | 1995 | Dúbravka | Školský dvor | = |
| S18 | 1995 | Dúbravka | Sídliskový dvor s kioskom | = |
| S19 | 1995 | Karlova Ves | Karloveské nástupište | = |
| S20 | 1995 | Karlova Ves | **Paliho opravovňa** | Palova opravovňa |
| S21 | 1995 | Staré Mesto | Kamenné námestie | = |
| S22 | 1995 | Staré Mesto | Antikvariát Pod druhou rukou | = |
| S23 | 1995 | Staré Mesto | Archívna študovňa | = |
| S24 | 1995 | Staré Mesto | Fotoateliér Svetlo | = |
| S25 | 1995 | Ružinov | Miletičova medzi stánkami | = |
| S26 | 1995 | Ružinov | Opravovňa odevov | = |
| S27 | 1995 | Ružinov | Kazetový klub v suteréne | = |
| S28 | 1995 | Petržalka | Petržalský podchod | = |
| S29 | 1995 | Petržalka | Garáž rádioamatéra | = |
| S30 | 1995 | Petržalka | **Merací stánok na Starom moste** | Nábrežný merací prístrešok |
| S31 | 1960 | Ivanka pri Dunaji | Ivanská železničná zastávka | = |
| S32 | 1960 | Ivanka pri Dunaji | Ivanská náves | = |
| S33 | 1960 | Ivanka pri Dunaji | Pošta s prepážkou | = |
| S34 | 1960 | Ivanka pri Dunaji | Kultúrna sála pred skúškou | = |
| S35 | 1960 | Ivanka pri Dunaji | Dvor hospodárskej dielne | = |
| S36 | 1960 | Ivanka pri Dunaji | Otova mechanická dielňa | = |
| S37 | 1960 | Ivanka pri Dunaji | Park pri kaštieli | = |
| S38 | 1960 | Ivanka pri Dunaji | Pred skúšobnou čerpacou búdkou | = |
| S39 | 1960 | Ivanka pri Dunaji | Miestnosť prvého ZVONu | = |
| S40 | 1960 | Ivanka pri Dunaji | Povala technického archívu | = |
| S41 | 2035 | Biela Púť | Biela Púť pri dolnej stanici | = |
| S42 | 2035 | Biela Púť | Pred hotelom Grand Jasná | = |
| S43 | 2035 | Grand Jasná | Lobby hotela Grand Jasná | = |
| S44 | 2035 | Grand Jasná | Výstavný salón hotela Grand Jasná | = |
| S45 | 2035 | Vrbické pleso | Chodník pri Vrbickom plese | = |
| S46 | 2035 | Biela Púť | Klientske centrum Biela Púť | = |
| S47 | 2035 | Chopok | Chopok pri Rotunde | = |
| S48 | 2035 | Chopok | Servisný pavilón výstavy Atlas | = |
| S49 | 2035 | Chopok | Chronokomora pavilónu Atlas | = |
| S50 | 2035 | Chopok | Vyhliadková terasa pri Rotunde | = |
| S51 | 2020 | Dúbravka | Dúbravská zastávka v roku 2020 | = |
| S52 | 2020 | Dúbravka | Pred ZŠ Sokolíkova v roku 2020 | = |
| S53 | 2020 | Dúbravka | Školské zádverie v roku 2020 | = |
| S54 | 2020 | Dúbravka | Fyzikálny kabinet v roku 2020 | = |
| S55 | 2020 | Dúbravka | Školský dvor v roku 2020 | = |
| S56 | 2020 | Dúbravka | Školnícke servisné okno v roku 2020 | = |
| S57 | 1982 | Dúbravka | Dúbravská zastávka v roku 1982 | = |
| S58 | 1982 | Dúbravka | Pred ZŠ Sokolíkova v roku 1982 | = |
| S59 | 1982 | Dúbravka | Školská chodba v roku 1982 | = |
| S60 | 1982 | Dúbravka | Trieda pred technickou výstavkou v roku 1982 | = |
| S61 | 1982 | Dúbravka | Školský dvor s mladou lipou v roku 1982 | = |
| S62 | 1982 | Dúbravka | Sídliskový obchod v roku 1982 | = |
| S63 | 1982 | Dúbravka | Fyzikálny kabinet v roku 1982 | = |
| S64 | 1982 | Dúbravka | Tóno a dedo pri servisnom okne v roku 1982 | = |
| S65 | 1982 | Dúbravka | Výdajňa školského údržbového materiálu v roku 1982 | = |
| S66 | 1982 | Dúbravka | Školský záhradný sklad v roku 1982 | = |
| S67 | 2035 | Priehyba | Priehyba pri prestupe na Funitel | = |
| S68 | 2035 | Funitel | Kabína Funitelu medzi Priehybou a Chopkom | = |
| S69 | 1995 | Dúbravka | Pri LEALe | = (world overlay, content v2: the walled courtyard of the Sokolíkova estate, reached from S18; Zuzana 40, Kubo, Q11, B19; local name decided by the owner 2026-10-07, was *Sokolíkovský dvor*) |


## 4. Devices and recurring concepts

| Canonical (Slovak) | Meaning | Not |
|---|---|---|
| **ZVON** (*ZVONu, ZVONom*) | the civil time-measuring device of Mira and Oto, 1960 | *časostroj, stroj času* |
| **prenosný chronometer** (*chronometra*), *chronometer ZVON* | the portable brass unit Adam carries; it cannot be put away | *chronometr, hodinky* |
| **ochranné pole chronometra** | protects Adam, his bag and what he carries; that is why he remembers Mira and why his photos do not change (*chránená fotografia, chránená pamäť*) | *bublina, kotva* |
| **stolový uzol ZVON** with the **kolíska** | the stationary unit in Mira's garden workshop (low voltage); the chronometer docks in its cradle; the **tvarový panel** is P01 | |
| **časový uzol**, *uzlové hodiny* (speech) | the old clock frames at the stops through which Adam travels (Dúbravská zastávka 1995/1982/2020, Ivanka station, Biela Púť) and the workshop unit; UI button *Uzol* | |
| **časové okno** | a year that is open for travel; *otvoriť časové okno* | *časová adresa* in goals and hints (the device may say *referencia*) |
| **spätný zápis** | Atlas writing "corrections" back into the traces of real lives | *retroaktívny zápis* |
| **normalizátor**, **panel normalizácie** | Viktor's filter; the public panel by the Rotunda shows its rule `ROZDIEL = ZAHODIŤ` | |
| **návratový zásobník** (*zásobník*) | where erased data wait until the write is confirmed; they can still be returned | *buffer, buffr* |
| **Atlas** (*Atlasu*) | Viktor's fictional organisation and exhibition, 2035 | not the 1995 club |
| **Zvukový atlas našej školy**, **krúžok** | Mira's and Lea's afternoon club and its tape, 1995 (*trieda pamäťového krúžku*) | |
| **Mirin fond**, **fond Z-17**, **krabica Z-17** | Mira's technical archive: registered at the post office in 1960 as **Z-17**, the box moved by Roman in 2020, catalogued by Atlas in 2035 | |
| **kalibračná platňa** (mosadzná) | the brass plate of 1960 with PÔVOD, HLAS, SÚHLAS, NÁVRAT and the rule; it stays on the device | |
| **odtlačok** → *nezvýraznený*, *čitateľný*, **overený odtlačok z roku 1962** | Adam's imprint of the plate on waxed paper, worked out with the blunt stylus, then registered | *kópia* (that is Mira's archive copy) |
| **archívna kópia**, **kovová schránka** | Mira's clean copy, locked with the registration in the metal box in the attic | |
| **registračný list**, **druhopis** (via **uhľový papier**), **pečiatka** | the post office confirms the date and existence of the record, not its truth | *prepisový papier*, *uhlový papier* (Czech form; Slovak *uhlový* means 'angular'; changed 2026-10-06 in the C3 final control, C2/C4 texts follow on their next pass) |
| **pravidlo** `Rôzne údaje neznamenajú neplatné údaje.` | Mira's 1960 rule, engraved on the plate | |
| **štyri svedectvá**: **Pôvod**, **Hlas**, **Súhlas**, **Návrat** | the four proofs and the four **porty** of the chamber: Pôvod = overený odtlačok 1960, Hlas = pôvodná školská kazeta 1995, Súhlas = potvrdené odovzdanie 2020, Návrat = obnovovací postup 2035 | *dôkaz Súhlas* (say *dôkaz súhlasu*) |
| **pôvodná školská kazeta** | the 1995 sound-atlas tape with Lea and ten-year-old Adam; first *kazeta s rušenými stopami* (two tracks against each other) | |
| **krížový adaptér**, **dvojpólový konektor**, **izolačný návlek**, **zvuková prepojka**, **servisný zvukový vstup** | the 1995 audio repair chain | *návlečka* |
| **mapa meracích uzlov**, **priehľadná fólia K-17**, **tri registračné značky** (dierka, dvojitý kríž, štvorec) | the 1995 map puzzle P02 | *priehľadná mapa* |
| **meracia cievka**, **metronóm**, **rytmický nákres**, **tri kalibračné číslice** | the riverside measurement P03 | *slučka* |
| **ručná pumpa** (*demonštračný chladiaci model*), **kožená manžeta**, **nity**, **dierovač**, **svorka kulisy** | 1960 repair before Oto opens the measuring room | |
| **návratový mostík** (keramický) | the physical safe-return bridge Oto designed in 1982; the reserve piece Adam builds, seals and hides, and finds again in 2020 (*zachovaný návratový mostík*) | *prepojka* (that is the audio cable) |
| **keramická pätica**, **tri prepojky**, **servisná doska** | the bridge parts and the workbench in the 1982 physics cabinet | |
| **zavárací pohár s tesnením**, **zapečatený pohár** | the jar that keeps the bridge dry for 38 years | |
| **servisná dutina v múriku**, mriežka **3 × 4** | the cavity behind the service board: second row from the top, third stone from the left | *skrýša* in system texts (fine in Tóno's speech) |
| **nákres servisnej dutiny** (Tónova mapa), **Tónova poznámka z roku 1995** | the two notes that lead to the cavity (P05) | |
| **lastovička** | Tóno's swallow: a wooden model in 1982, a metal ornament on the same window in 1995 and 2020, drawn on the bridge label and on his map | |
| **heslo** `Lastovička sa vracia.` | the recognition sentence between Adam and Tóno | |
| **mladá lipa**, **ochranná ohrádka**, **trasa ručného vozíka** | the 1982 tree; protecting it changes the 2020 yard (big lime tree, the low wall kept) | *motýlí efekt* in player texts |
| **chránená fotografia dvora 2020** | Adam's phone photo of the yard before the change (asphalt, no tree, no wall); it does not change | |
| **servisná kniha z roku 1982** → **kópia servisného záznamu 1982** | Oto's record in the 2020 physics cabinet that opens the 1982 window | |
| **protokol o odovzdaní** → *s Romanovým podpisom* → **potvrdené odovzdanie 2020** | the real handover of box Z-17 during quarantine, with Ela's and Roman's signatures and Mira's recorded consent | |
| **lokálna (zvuková) čítačka**, **katalógová karta fondu Z-17**, **servisný preukaz**, **spiatočný lístok na oba úseky** | the 2035 access chain | |
| **kabínková lanovka** (Biela Púť – Priehyba), **Funitel** (Priehyba – Chopok) | real cable cars; they work normally and are never part of a trick | |
| **servisný terminál**, **pasívny stojan** pri Vrbickom plese, **miestna referenčná stopa**, **podpísaný obnovovací postup** | the 2035 diagnosis and restore procedure | |
| **oddelený konektor Atlasu** (terasa), **prepínač ZÁPIS / MONITOR** | the bridge goes into Atlas's separate low-voltage connector; MONITOR only reads and stops the erasing; not connected to the cable cars | |
| **chronokomora**, **panel obnovy** | the chamber where Viktor hears the message and the four proofs are inserted | *synchronizačná komora* |
| **Leina pôvodná správa** | the full message of 2032; the normalizer left only `ozvi sa` | |

## 5. Items (83)

Canonical inventory names. **Bold** = decided rename; dialogue, looks, goals and hints must use the same noun (declined). 'Got' = action that gives it, 'Used in' = actions that need it.

| Id | Canonical name | Current | Got (chunk) | Used in |
|---|---|---|---|---|
| PHONE | Adamov telefón | = | initial (C1) | F05, D01 |
| TOOLS | Servisná brašna | = | G01 (C1) | G08, B04, B08, I03, I06, E04, E09, D05, D06 |
| ORDER | **Mirin nákupný lístok** | Mirkin nákupný lístok | G02 (C1) | G03 |
| GROCERIES | Taška s nákupom | = | G03 (C1) | G04 |
| SHEDKEY | Kľúč od dielne | = | G05 (C1) | G06 |
| CHRONO | Prenosný chronometer ZVON | = | G07 (C1) | G08, G10, G11, B02, B22, I01, C05, F07, D02, D04, E01 |
| FUSE_OLD | Prerušená poistka | = | G08 (C1) | G09 |
| FUSE | Náhradná poistka | = | G09 (C1) | G10 |
| LETTER | Mirino poverenie | = | B03 (C2) | B13 |
| BELT_OLD | Rozpadnutý remienok | = | B04 (C2) | B05 |
| BELT_NEW | Nový remienok | = | B05 (C2) | B06 |
| TAPE_RAW | Kazeta s rušenými stopami | = | B06 (C2) | B07, B12 |
| ADAPTER | Krížový adaptér bez konektora | = | B07 (C2) | B10 |
| CONNECTOR | Dvojpólový konektor | = | B08 (C2) | B10 |
| BRAID | **Textilný izolačný návlek** | Textilná izolačná návlečka | B09 (C2) | B11 |
| LINK_OPEN | **Adaptér s konektorom bez izolácie** | Zapojený neizolovaný adaptér | B10 (C2) | B11 |
| STEREOLINK | Hotová zvuková prepojka | = | B11 (C2) | B12 |
| TAPE | Pôvodná školská kazeta | = | B12 (C2) | B22, C05, F02, F06, F13 |
| DIAGRAM | **Mapa uzlov bez fólie** | Mapa bez priehľadnej vrstvy | B13 (C2) | B16 |
| NEGATIVE | Technický fotografický negatív | = | B13 (C2) | B14 |
| CALPHOTO | Fotografia kalibračného stojana | = | B14 (C2) | B15 |
| OVERLAY | **Priehľadná fólia K-17** | Priehľadná mapa K-17 | B15 (C2) | B16 |
| NODEMAP | **Úplná mapa meracích uzlov** | Úplná mapa uzlov | B16 (C2) | B17, B22 |
| COIL | Deziderova meracia cievka | = | B17 (C2) | B20 |
| METRONOME | Emilov metronóm | = | B18 (C2) | B21 |
| SUPPLYSLIP | Otov výdajný lístok | = | I01 (C3) | I02 |
| LEATHER | Predrezaná kožená manžeta | = | I02 (C3) | I04 |
| RIVETS | Dva duté nity | = | I02 (C3) | I05 |
| PUNCH | Lídin ručný dierovač | = | I03 (C3) | I04, I05, I07 |
| CUFF_OPEN | Dierovaná manžeta | = | I04 (C3) | I05 |
| CUFF | Hotová manžeta | = | I05 (C3) | I06 |
| PUMPKEY | Kľúč od meracej miestnosti | = | I07 (C3) | I08 |
| REGFORM | Technický registračný list | = | I09 (C3) | I15 |
| STYLUS | Verino tupé rydlo | = | I10 (C3) | I13, I17 |
| WAXPAPER | Voskovaný hárok | = | I11 (C3) | I12 |
| PRESSED | Nezvýraznený odtlačok | = | I12 (C3) | I13 |
| ORIGIN_RAW | Čitateľný odtlačok | = | I13 (C3) | I17 |
| CARBON | **Uhľový papier** | Uhlový papier | I14 (C3) | I15 |
| REGDOUBLE | Dve vyhotovenia listu | = | I15 (C3) | I16 |
| REGISTERED | Potvrdený registračný list | = | I16 (C3) | I17 |
| ORIGIN | Overený odtlačok z roku 1962 | = | I17 (C3) | C01, C05, F06, F12, E02 |
| HANDOVER | Protokol o odovzdaní | = | C02 (C1) | C03 |
| HANDOVER_R | Protokol s Romanovým podpisom | = | C03 (C1) | C04 |
| CHAIN | Potvrdené odovzdanie 2020 | = | C04 (C1) | C05, F03, F14 |
| READER | Lokálna zvuková čítačka | = | F02 (C4) | F06 |
| CATALOG | Katalógová karta fondu Z-17 | = | F03 (C4) | F04 |
| PASS | Servisný návštevnícky preukaz | = | F04 (C4) | F10 |
| FILTER_PHOTO | Záznam panelu normalizácie | = | F05 (C4) | F06 |
| LEA_MESSAGE | Leina nezmenená hlasová správa | = | F06 (C4) | F11 |
| DIAGNOSTIC | Diagnostický protokol | = | F06 (C4) | F08 |
| PULSE | Miestna referenčná stopa | = | F07 (C4) | F08 |
| PATCH | Podpísaný obnovovací postup | = | F08 (C4) | F09, F10, F15 |
| BALL | Bodkova loptička | = | Q1B (C1) | Q1C |
| FLYER | Veľký čitateľný oznam | = | Q2B (C1) | Q2C |
| TEAMNEG | Obálka s tímovým negatívom | = | Q3B (C2) | Q3C |
| TEAMPHOTO | Fotografia družstva | = | Q3C (C2) | Q3D |
| SCORE | Noty k Emilovej skladbe | = | Q4B (C2) | Q4C |
| CHALK | Biela školská krieda | = | Q5B (C2) | Q5C |
| SEEDS | Hrsť semien pre Bélu | = | Q6B (C3) | Q6C |
| PLAY | Rudov scenár | = | Q7B (C3) | Q7C |
| DELIVERY_NOTE | Očkova doručovacia požiadavka | = | Q8A (C4) | Q8B, Q8C |
| DELIVERY_OK | Potvrdenie opravovne | = | Q8C (C4) | Q8D |
| BELL_MUTE | Triedny zvonček bez pútka | = (world overlay) | Q10A (C3) | Q10C |
| ZUZA_SLIP | Zuzanin lístok | = (world overlay) | Q10A (C3) | Q10B |
| STRAP | Kožený odrezok | = (world overlay; not LEATHER) | Q10B (C3) | Q10C |
| BELL_FIXED | Opravený triedny zvonček | = (world overlay) | Q10C (C3) | Q10D |
| BELLCAP | Vrchnák zvončeka | = (world overlay) | Q11B (C2) | Q11C |
| PHOTO2020 | Chránená fotografia dvora 2020 | = | D01 (C1) | E02 |
| SCHOOLPASS | Povolenie prevziať Mirin technický majetok | = | D02 (C1) | — |
| LOG1982 | Kópia servisného záznamu 1982 | = | D03 (C1) | D04, E02, E04 |
| PARTSNOTE | Otov školský výdajný lístok | = | E02 (C3) | E03 |
| CERAMICPARTS | Diely návratového mostíka | = | E03 (C3) | E04 |
| BRIDGE_NEW | Nový keramický mostík | = | E04 (C3) | E06 |
| JAR | Pohár s viečkom a tesnením | = | E05 (C3) | E06 |
| SEALED_NEW | Zapečatený pohár s mostíkom | = | E06 (C3) | E08 |
| TREEGUARD | Ochranná ohrádka pre lipu | = | E07 (C3) | E09 |
| CACHEMAP | Nákres servisnej dutiny | = | E08 (C3) | D05 |
| KEEPERNOTE | Tónova poznámka z roku 1995 | = | E11 (C2) | D05 |
| SEALED_OLD | Pohár vyzdvihnutý po 38 rokoch | = | D05 (C1) | D06 |
| RETURNBRIDGE | Zachovaný návratový mostík | = | D06 (C1) | C05, D07, J05 |
| LIFT_TICKET | Spiatočný lístok na oba úseky | = | F04 (C4) | J02, J03 |
| JANA_DRAWING | Janina pôvodná schéma | = | Q9A (C3) | Q9B |
| JANA_APPROVED | Schéma s povolením na výstavku | = | Q9B (C3) | Q9C |


## 6. Protected facts

Everything here must survive every rewrite, verbatim or with exactly the same meaning and value.
The checker knows the keys (glossary.json → `protected`, `verbatim`); if you must move a fact to
another line of the same exchange, say so in the note.

### 6.1 Puzzles

| Puzzle | What the player must be able to read | Solution | Keys that carry it |
|---|---|---|---|
| **P01** Tri referenčné tvary (S10) | join equal shapes; colours do not matter | kruh–kruh, trojuholník–trojuholník, štvorec–štvorec | `look.S10.panel`, `action.G10.002/.003`, `action.G10.objective/.journal`, `puzzle.P01.*`, `journal.clue.P01`, `quest.M02.hint.3` |
| **P02** Zarovnanie mapovej fólie (bag) | the base map and the overlay both show **dierka, dvojitý kríž, štvorec**; rotate until all three match | **180°** | `item.OVERLAY`, `action.B15.004`, `puzzle.P02.*`, `journal.clue.P02`, `quest.M06.hint.3` |
| **P03** Kalibrácia na Starom moste (S30) | the rhythm drawing on the courtyard wall pri LEALe (S69, content v2; B19 relocated from the school yard S17) says `TRI VLNY, DVA ÚDERY, ŠESŤ DIELIKOV`; Dezider says the three digits are on the wall pri LEALe and Emil has the metronome | **3–2–6** | `look.S69.rhythm`, `action.B17.003`, `action.B19.001/.objective/.journal`, `action.B22.001`, `look.S30.dial`, `puzzle.P03.*`, `journal.clue.P03`, `quest.M07.hint.2/.3` |
| **P04** Priradenie štyroch svedectiev (S49) | ports and items carry name and year; the journal repeats them | **Pôvod 1962, Hlas 1995, Súhlas 2020, Návrat 2035** (shown; value 1960) | `look.S39.plate`, `action.I13.001`, `action.C05.001`, `look.S49.port_*`, `action.F11.objective/.journal`, `action.F12.001`–`F15.001`, `puzzle.P04.*`, `journal.clue.P04`, `quest.M15.hint.2/.3` |
| **P05** Dutina v tom istom múriku (S55) | grid **3 × 4**; **druhý rad zhora, tretí kameň zľava** = **rad 2, stĺpec 3**, written in Tóno's 1982 map and his 1995 note | row 2, column 3 | `action.E08.001`, `item.CACHEMAP`, `look.S61.niche`, `action.E11.006`, `item.KEEPERNOTE`, `action.D05.002`, `puzzle.P05.*`, `journal.clue.P05`, `quest.M11C.hint.3` |

Puzzle option labels (`puzzle.P01.left/right.*`, `puzzle.P04.left/right.*`) are verbatim.

### 6.2 Codes, numbers and painted texts

| Fact | Value | Where |
|---|---|---|
| annex number on the photo, Viera's shelf mark | **K-17** | B14, B15, `item.CALPHOTO`, `item.OVERLAY.name` |
| registration number of Mira's box/fond | **Z-17** | I16, C03, `item.HANDOVER`, `item.CHAIN`, `item.CATALOG.name`, F01, F03, `look.S15.register.variant1` |
| Dezider's garage | číslo **17** | `entry.S29.001` |
| help-line hours on Jozef's flyer | **9–17** (*od deviatej do piatej*) | `item.FLYER`, Q2C |
| the four meanings on the plate | `PÔVOD, HLAS, SÚHLAS, NÁVRAT` | § 6.1 P04 |
| Mira's rule | `Rôzne údaje neznamenajú neplatné údaje.` | `look.S39.plate`, `action.I13.001`; quoted by F05 (*opak Mirinej vety*), CS04 |
| the faulty rule | `ROZDIEL = ZAHODIŤ` | `item.FILTER_PHOTO`, `action.F05.001`, `look.S47.filter` |
| warning sign in the workshop | `NEPREPISOVAŤ ORIGINÁL` | `look.S10.ambient 2` |
| switch positions | `ZÁPIS`, `MONITOR` | F06–F10, J05, `look.S50.switch` |
| the password | `Lastovička sa vracia.` | E02, E11, D07, M11C hints |
| play title / first line | `Žiaden strach, miláčik!` | Q7, `look.S40.script`, `topic.LEA95.after`, epilogue 7 |
| Emil's song | `Štyri zastávky` | Q4, epilogue 4 |
| Tamara's workshop | `Druhý život` / sign `DRUHÝ ŽIVOT` | Q8, `look.S45.bench` |
| shelf sign on the thermos | `NEDOLIEVAŤ POLIEVKU` | `look.S03.ambient 2` (pairs with `topic.ELA.ambient 2`) |

### 6.3 Dates, ages, durations

| Fact | Value |
|---|---|
| time windows | Ivanka **6. júna 1962** (shown year; the era id stays 1960, docs/DECISIONS.md "Ivanka is shown as June 1962"), Dúbravka **7. decembra 1982**, Bratislava **15. júna 1995**, Chorvátsky Grob a Dúbravka **29. októbra 2020**, Jasná **6. júna 2035** |
| Adam | **35** in 2020, born **1985**; **10** on the 1995 tape; in 1982 he "will be born in three years" |
| Mira | **22** (June 1962), **55** (1995), **80** (2020) |
| Tóno | born March **1970**: **12** (1982), **25** (1995), **50** (2020) |
| Oto | **46** (1962), **66** (1982): *zostarol o dvadsať rokov* |
| Vera | **24** (1962); other Ivanka people +2 against game.json where a text states an age |
| Jana | **12** (1982), **25** (1995), **50** (2020), **65** (2035) |
| Lea | 33 in 1995; message and natural death in **2032** (her death is not changed) |
| Nina | 30 in 2035 (15 in 2020) |
| the jar in the wall | **38 rokov** (1982 → 2020) |
| Tóno's wait to 1995 | **13 rokov** |
| Mira's box | *skoro šesťdesiat rokov* in it (1962 → 2020 = 58); *o sedemdesiattri rokov* (1962 → 2035) |
| Adam in 1995 | *meškám o dvadsaťpäť rokov*, *štvrťstoročie* |
| Mira 1962 vs Adam | *o trinásť rokov mladšia než ja* |

### 6.4 Verbatim lines (do not touch)

| Key | Text |
|---|---|
| `action.F11.003` (Lea, 2032) | `Viktor? To som ja. Len ti volám. Nemusíš nič opravovať. Keď budeš mať čas, ozvi sa.` |
| `action.F11.004` | must keep `ozvi sa` (what the normalizer left) |
| `action.D07.006` (Tóno 50) | `Nečakal som. Žil som. Len som si pamätal miesto.` |
| `cutscene.CS07.04.001` (Mira) | `Čaj ti spravím, keď bude možné prísť normálne.` |
| `cutscene.CS07.04.002` (Adam) | `Tentoraz počkám.` |
| `journal.clue.P04` | `Pôvod 1962, Hlas 1995, Súhlas 2020, Návrat 2035` (P04 option values stay 1960 internally) |
| `game.title` | `Posledný zvonec` |

### 6.5 Story facts a rewrite must not blur

- Adam never enters Mira's house in 2020; they talk by phone through the closed window. Nobody
  breaks quarantine, steals medicine or forges documents. The handover is recorded after it really
  happened, with Mira's recorded consent; nothing is invented backwards.
- Adam does not talk to his ten-year-old self; the child is only a voice on the tape.
- The cassette is read, never re-recorded or corrected (*čítať, nekorigovať*).
- The plate stays in 1960 on the device; Adam carries an imprint; the registered copy stays in the
  metal box.
- Tóno chose his job himself; he did not wait 38 years. Oto, not the child, signs materials and
  permissions in 1982.
- The cable cars work normally; Atlas's connector is separate from them; MONITOR only reads.
- Viktor is responsible for continuing the test after Nina's warning; he is not a villain or a
  madman. Lea's death is not caused by the erasing.
- Side stories never block the main story; after the credits the time windows stay open.

## 7. Which item goes where (walkthrough order)

Generated from walkthrough.json and game.json. Every hint level 3, objective and look must stay consistent with this table. `→` = use the item on the target, `+` = combine in the bag, *téma* = dialogue choice, *klik* = left click. Names are the current table names; apply the renames of § 3.3 and § 5.

| Step | Action | Room | What the player does | Gets |
|---|---|---|---|---|
| 1 | G01 | S01 | klik: Servisná brašna | Servisná brašna |
| 2 | G02 | S03 | téma u: Ela Švecová | Mirkin nákupný lístok |
| 3 | G03 | S04 | Mirkin nákupný lístok → Dana Valová | Taška s nákupom |
| 4 | G04 | S05 | Taška s nákupom → Stolík pred bránkou | — |
| 5 | G05 | S06 | téma u: Mira Hrušková | Kľúč od dielne |
| 6 | G06 | S05 | Kľúč od dielne → Dvere záhradnej dielne | — |
| 7 | G07 | S09 | klik: Mosadzné puzdro | Prenosný chronometer ZVON |
| 8 | G08 | S10 | Servisná brašna → Stolový uzol ZVON | Prerušená poistka |
| 9 | G09 | S01 | klik: Zásuvka s poistkami | Náhradná poistka |
| 10 | G10 | S10 | Náhradná poistka → Stolový uzol ZVON | — |
| 11 | G11 | S10 | klik: Tvarový prepojovací panel (hádanka, riešenie ['kruh', 'trojuholník', 'štvorec']) | — |
| 12 | B01 | S12 | klik: Nástenka krúžku | — |
| 13 | B02 | S13 | Prenosný chronometer ZVON → Anton Farkaš | — |
| 14 | B03 | S14 | téma u: Mira Hrušková | Mirino poverenie |
| 15 | B04 | S16 | Servisná brašna → Kazetový mechanizmus | Rozpadnutý remienok |
| 16 | B05 | S20 | Rozpadnutý remienok → Pavol Drobný | Nový remienok |
| 17 | B06 | S16 | Nový remienok → Kazetový mechanizmus | Kazeta s rušenými stopami |
| 18 | B07 | S27 | Kazeta s rušenými stopami → Juraj Malík zvaný Juro Kazeta | Krížový adaptér bez konektora |
| 19 | B08 | S25 | Servisná brašna → Zaseknutá stolová váha | Dvojpólový konektor |
| 20 | B09 | S26 | téma u: Milada Kyselová | Textilná izolačná návlečka |
| 21 | B10 | S26 | Dvojpólový konektor + Krížový adaptér bez konektora | Zapojený neizolovaný adaptér |
| 22 | B11 | S26 | Textilná izolačná návlečka + Zapojený neizolovaný adaptér | Hotová zvuková prepojka |
| 23 | B12 | S16 | Hotová zvuková prepojka → Servisný zvukový vstup | Pôvodná školská kazeta |
| 24 | B13 | S23 | Mirino poverenie → Karol Merta | Mapa bez priehľadnej vrstvy, Technický fotografický negatív |
| 25 | B14 | S24 | Technický fotografický negatív → Alena Svobodová | Fotografia kalibračného stojana |
| 26 | B15 | S22 | Fotografia kalibračného stojana → Viera Holubová | Priehľadná mapa K-17 |
| 27 | B16 | S22 | Priehľadná mapa K-17 + Mapa bez priehľadnej vrstvy (hádanka, riešenie 180) | Úplná mapa uzlov |
| 28 | B17 | S29 | Úplná mapa uzlov → Dezider Kováč | Deziderova meracia cievka |
| 29 | B18 | S19 | téma u: Emil Belan | Emilov metronóm |
| 30 | B19 | S69 | klik: Rytmický nákres (relocated from S17 by the world overlay; walk S11 → S18 → S69) | — |
| 31 | B20 | S30 | Deziderova meracia cievka → Držiak meracej cievky | — |
| 32 | B21 | S30 | Emilov metronóm → Stolík s rytmickou značkou | — |
| 33 | B22 | S30 | klik: Tri kalibračné číslice (hádanka, riešenie [3, 2, 6]) | — |
| 34 | I01 | S36 | Prenosný chronometer ZVON → Oto Bielik | Otov výdajný lístok |
| 35 | I02 | S35 | Otov výdajný lístok → Štefan Haluška | Predrezaná kožená manžeta, Dva duté nity |
| 36 | I03 | S34 | Servisná brašna → Svorka kulisy | Lídin ručný dierovač |
| 37 | I04 | S34 | Lídin ručný dierovač + Predrezaná kožená manžeta | Dierovaná manžeta |
| 38 | I05 | S34 | Dva duté nity + Dierovaná manžeta | Hotová manžeta |
| 39 | I06 | S38 | Hotová manžeta → Demonštračná ručná pumpa | — |
| 40 | I07 | S36 | téma u: Oto Bielik | Kľúč od meracej miestnosti |
| 41 | I08 | S38 | Kľúč od meracej miestnosti → Dvere meracej miestnosti | — |
| 42 | I09 | S39 | téma u: Mira Hrušková | Technický registračný list |
| 43 | I10 | S37 | téma u: Vera Nemcová | Verino tupé rydlo |
| 44 | I11 | S40 | klik: Voskovaný papier | Voskovaný hárok |
| 45 | I12 | S39 | Voskovaný hárok → Kalibračná mosadzná platňa | Nezvýraznený odtlačok |
| 46 | I13 | S39 | Verino tupé rydlo + Nezvýraznený odtlačok | Čitateľný odtlačok |
| 47 | I14 | S33 | klik: Uhľový papier | Uhľový papier |
| 48 | I15 | S33 | Uhľový papier + Technický registračný list | Dve vyhotovenia listu |
| 49 | I16 | S33 | Dve vyhotovenia listu → Alojz Baran | Potvrdený registračný list |
| 50 | I17 | S40 | Potvrdený registračný list → Kovová archívna schránka | Overený odtlačok z roku 1960 |
| 51 | C01 | S06 | Overený odtlačok z roku 1960 → Mira Hrušková | — |
| 52 | D01 | S52 | Adamov telefón → Roh dvora a servisné okno | Chránená fotografia dvora 2020 |
| 53 | D02 | S56 | Prenosný chronometer ZVON → Anton Farkaš | Povolenie prevziať Mirin technický majetok |
| 54 | D03 | S54 | klik: Servisná kniha z roku 1982 | Kópia servisného záznamu 1982 |
| 55 | D04 | S51 | Kópia servisného záznamu 1982 → Rám starých hodín | — |
| 56 | E01 | S64 | Prenosný chronometer ZVON → Anton Farkaš | — |
| 57 | E02 | S64 | Chránená fotografia dvora 2020 → Anton Farkaš | Otov školský výdajný lístok |
| 58 | E03 | S65 | Otov školský výdajný lístok → Marta Dobiášová | Diely návratového mostíka |
| 59 | E04 | S63 | Diely návratového mostíka → Servisná doska | Nový keramický mostík |
| 60 | E05 | S62 | téma u: Ružena Malá | Pohár s viečkom a tesnením |
| 61 | E06 | S62 | Pohár s viečkom a tesnením + Nový keramický mostík | Zapečatený pohár s mostíkom |
| 62 | E07 | S66 | téma u: Šimon Rybár | Ochranná ohrádka pre lipu |
| 63 | E08 | S61 | Zapečatený pohár s mostíkom → Servisná dutina v múriku | Nákres servisnej dutiny |
| 64 | E09 | S61 | Ochranná ohrádka pre lipu → Mladá lipa | — |
| 65 | E10 | S66 | téma u: Šimon Rybár | — |
| 66 | E11 | S13 | téma u: Anton Farkaš | Tónova poznámka z roku 1995 |
| 67 | D05 | S55 | Servisná brašna → Miesto pôvodnej servisnej dutiny (hádanka, riešenie {'row': 2, 'column': 3}) | Pohár vyzdvihnutý po 38 rokoch |
| 68 | D06 | S55 | Servisná brašna + Pohár vyzdvihnutý po 38 rokoch | Zachovaný návratový mostík |
| 69 | D07 | S56 | Zachovaný návratový mostík → Anton Farkaš | — |
| 70 | C02 | S03 | téma u: Ela Švecová | Protokol o odovzdaní |
| 71 | C03 | S02 | Protokol o odovzdaní → Roman Kováč | Protokol s Romanovým podpisom |
| 72 | C04 | S03 | Protokol s Romanovým podpisom → Ela Švecová | Potvrdené odovzdanie 2020 |
| 73 | C05 | S10 | Potvrdené odovzdanie 2020 → Stolový uzol ZVON | — |
| 74 | F01 | S42 | téma u: Nina Švecová | — |
| 75 | F02 | S43 | Pôvodná školská kazeta → Tamara Kráľová | Lokálna zvuková čítačka |
| 76 | F03 | S44 | Potvrdené odovzdanie 2020 → Boris Urban | Katalógová karta fondu Z-17 |
| 77 | F04 | S46 | Katalógová karta fondu Z-17 → Sára Vrbová | Servisný návštevnícky preukaz, Spiatočný lístok na oba úseky |
| 78 | J02 | S41 | Spiatočný lístok na oba úseky → Čítačka platného lístka | — |
| 79 | J03 | S67 | klik: Nástup na Funitel | — |
| 80 | J04 | S68 | klik: Príchod do vrcholovej stanice | — |
| 81 | F05 | S47 | Adamov telefón → Panel normalizácie | Záznam panelu normalizácie |
| 82 | F06 | S48 | Lokálna zvuková čítačka → Servisný terminál | Leina nezmenená hlasová správa, Diagnostický protokol |
| 83 | F07 | S45 | Prenosný chronometer ZVON → Pasívny stojan pri chodníku | Miestna referenčná stopa |
| 84 | F08 | S48 | Miestna referenčná stopa → Servisný terminál | Podpísaný obnovovací postup |
| 85 | J05 | S50 | Zachovaný návratový mostík → Oddelený návratový konektor Atlasu | — |
| 86 | F09 | S50 | klik: Prepínač zápisu | — |
| 87 | F10 | S48 | klik: Servisný terminál | — |
| 88 | F11 | S49 | Leina nezmenená hlasová správa → Viktor Korman | — |
| 89 | F12 | S49 | Overený odtlačok z roku 1960 → Port Pôvod | — |
| 90 | F13 | S49 | Pôvodná školská kazeta → Port Hlas | — |
| 91 | F14 | S49 | Potvrdené odovzdanie 2020 → Port Súhlas | — |
| 92 | F15 | S49 | Podpísaný obnovovací postup → Port Návrat | — |
| 93 | F16 | S49 | klik: Panel obnovy (hádanka, riešenie ['1960', '1995', '2020', '2035']) | — |
| 94 | F17 | S49 | klik: Panel obnovy | — |
| + | Q1A | S02 | téma u: Lenka Bartošová | — |
| + | Q1B | S08 | klik: Červená loptička | Bodkova loptička |
| + | Q1C | S02 | Bodkova loptička → Lenka Bartošová | — |
| + | Q2A | S07 | téma u: Jozef Mlynár | — |
| + | Q2B | S03 | téma u: Ela Švecová | Veľký čitateľný oznam |
| + | Q2C | S07 | Veľký čitateľný oznam → Komunitná výveska | — |
| + | Q3A | S17 | téma u: Soňa Urbanová | — |
| + | Q3B | S18 | téma u: Zita Ondrušová | Obálka s tímovým negatívom |
| + | Q3C | S24 | Obálka s tímovým negatívom → Alena Svobodová | Fotografia družstva |
| + | Q3D | S17 | Fotografia družstva → Soňa Urbanová | — |
| + | Q4A | S19 | téma u: Emil Belan | — |
| + | Q4B | S22 | téma u: Viera Holubová | Noty k Emilovej skladbe |
| + | Q4C | S19 | Noty k Emilovej skladbe → Emil Belan | — |
| + | Q5A | S28 | téma u: Juraj Križan | — |
| + | Q5B | S13 | téma u: Anton Farkaš | Biela školská krieda |
| + | Q5C | S28 | Biela školská krieda → Povolený výtvarný panel | — |
| + | Q6A | S33 | téma u: Alojz Baran | — |
| + | Q6B | S35 | téma u: Štefan Haluška | Hrsť semien pre Bélu |
| + | Q6C | S37 | Hrsť semien pre Bélu → Poštový holub | — |
| + | Q6D | S33 | téma u: Alojz Baran | — |
| + | Q7A | S34 | téma u: Rudolf Pavlík | — |
| + | Q7B | S40 | klik: Ochotnícky scenár | Rudov scenár |
| + | Q7C | S34 | Rudov scenár → Rudolf Pavlík | — |
| + | Q8A | S41 | téma u: Doručovací robot Očko | Očkova doručovacia požiadavka |
| + | Q8B | S45 | klik: Lavička so psom | — |
| + | Q8C | S43 | Očkova doručovacia požiadavka → Tamara Kráľová | Potvrdenie opravovne |
| + | Q8D | S41 | Potvrdenie opravovne → Doručovací robot Očko | — |
| + | Q9A | S60 | téma u: Jana Vargová | Janina pôvodná schéma |
| + | Q9B | S60 | Janina pôvodná schéma → Učiteľ Dobrovič | Schéma s povolením na výstavku |
| + | Q9C | S60 | Schéma s povolením na výstavku → Jana Vargová | — |
| + | Q9D | S15 | téma u: Jana Vargová | — |
| + | Q9E | S54 | téma u: Jana Vargová | — |
| + | Q9F | S44 | téma u: Jana Vargová | — |
| + | Q10A | S37 | téma u: Zuzana | Triedny zvonček bez pútka, Zuzanin lístok |
| + | Q10B | S35 | Zuzanin lístok → Štefan Haluška | Kožený odrezok |
| + | Q10C | inventory | Kožený odrezok + Triedny zvonček bez pútka (needs Servisná brašna) | Opravený triedny zvonček |
| + | Q10D | S37 | Opravený triedny zvonček → Zuzana | — |
| + | Q11A | S69 | téma u: Kubo | — |
| + | Q11B | S69 | klik: Modrý smrek | Vrchnák zvončeka |
| + | Q11C | S69 | Vrchnák zvončeka → Kubov bicykel (needs Servisná brašna) | — |


## 8. Deprecated words (the checker warns)

| Do not write | Write |
|---|---|
| *Mirka, Mirkin, Mirkina, Mirkinej* | Mira / Mirin, Mirina (system texts), babka (Adam), pani Hrušková (neighbours) |
| *buffer, buffri, buffru* | návratový zásobník / zásobník |
| *retroaktívny zápis* | spätný zápis |
| *návlečka* | izolačný návlek |
| *Palova opravovňa, Palovi* | Paliho opravovňa, Palimu |
| *Dezi, Deziho* (outside friends' speech) | Dezider, Dezidera |
| *prepisový papier*, *uhlový papier* | uhľový papier |
| *slučka* (the coil) | meracia cievka |
| *časostroj* | chronometer / ZVON |
| *Žiaden strach miláčik* | Žiaden strach, miláčik |
| *priehľadná mapa* | priehľadná fólia K-17 |
| *synchronizačná komora* | chronokomora |
| *chronotechnický hardvér* | technika výstavy, prístroj |
| *spomienková kotva* | pamäť nositeľa |
| *Tóno 12, Tónovi 2020, Jana 82* | dvanásťročný Tóno, Tóno pri servisnom okne, Jana v triede v roku 1982 |
| *dôkaz Súhlas / Pôvod …* | dôkaz súhlasu / pôvodu …; port Súhlas |
| *odblokovanie časovej adresy* | otvorí cestu do roku 2035 / otvorí časové okno |
| *Sokolíkovský dvor, v Sokolíkovskom dvore* (S69) | Pri LEALe (room name), pri LEALe, k LEALu, od LEALu (owner 2026-10-07) |

Design jargon (*v hre, herný, fiktívny, mimo obrazu, pixel, zoom, servisný krok, pôvodná línia,
motýlí efekt, finále, klik, inventár, kombinácia, hádanka, v denníku*) is listed in
STYLE_GUIDE.md § 8.

## 9. Speaker labels (C4 decides, the others use them as given)

Shown above every subtitle. Current values and the recommended ones:

| Speaker id | Current label | Recommended |
|---|---|---|
| SYSTEM | Text zariadenia | Zariadenie |
| NARRATOR | Záverečné titulky | Rozprávač |
| ADAM10 | Adam vo veku 10 rokov zo záznamu 1995 | Adam (10 rokov, nahrávka 1995) |
| LEA_REC | Lea Kormanová zo záznamu 2032 | Lea Kormanová (správa z roku 2032) |
| NINA_REMOTE | Nina cez servisný kanál | Nina (na diaľku) |
| JURO | Juraj Malík zvaný Juro Kazeta | Juro Kazeta |
| BODKA | Pes Bodka | Bodka |
