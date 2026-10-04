POSLEDNÝ ZVONEC
Kompletný obsahový a technický handoff pre coding agenta
Kanonická verzia 2.0

Začni súborom Posledny_zvonec_handoff.html. Otvorí sa priamo v prehliadači,
nepotrebuje server, pripojenie ani externé knižnice. Obsahuje úplný príbeh,
pravidlá, playbook, 68 scén, všetky postavy, akcie, dialógy a riešenia.

Záväzné posledné rozhodnutia
- Ivanka pri Dunaji 1960.
- Dúbravka 1982 za socializmu.
- Bratislava 1995: Dúbravka, Karlova Ves, Staré Mesto, Ružinov, Petržalka.
- Chorvátsky Grob a tá istá Dúbravka so ZŠ Sokolíkova 2020 počas covidu.
- Jasná 2035: Biela Púť, Grand Jasná, Vrbické pleso, Priehyba,
  Funitel na Chopok, Rotunda a výslovne fiktívne vybavenie Atlasu.
- Tóno: 12-ročný žiak v 1982, 25-ročný školník v 1995,
  50-ročný školník v 2020. Oto je jeho starý otec a dospelý technik.
- Uloženie vlastného predmetu 1982 a vyzdvihnutie na tom istom mieste 2020.
- Povinný butterfly effect lipy a voliteľný butterfly effect Janinho návrhu.
- Ľavý klik = logická akcia. Pravý nad cieľom = prezretie;
  pravý na voľnej ploche = inventár; pri vybratom predmete najprv zruší výber.
- Space prepína všetky viditeľné hotspoty vrátane čisto atmosférických.
- Text použitia vybratého predmetu sa ukáže len pri vykonateľnej kombinácii.

Súbory
Posledny_zvonec_handoff.html  Úplný čitateľný návrh s navigáciou a vyhľadávaním.
PRIBEH_A_PRAVIDLA.txt         Samostatná príbehová a technická biblia v čistom texte.
game.json                    Kanonické dáta celej hry, nie vzorový obsah.
walkthrough.json             Presný validovaný priechod 94 hlavnými akciami,
                             s legálnymi cestami, riešeniami a stavom inventára.
runtime_contract.ts          Čisté referenčné funkcie pravidiel bez závislosti na engine.
validate_handoff.py           Spustiteľná obsahová validácia iba s Python 3 stdlib.
validation_report.json       Výsledok validácie a jej presne uvedené limity.
dialogues.csv                Stabilné line IDs, rečníci a kompletné texty na titulky/dabing.
assets.csv                   Zoznam potrebných vizuálnych assetov a briefov.
acceptance_tests.csv          Akceptačné scenáre pre skutočný herný runtime.
sources.txt                  Geografické zdroje a hranice hernej fikcie.
CODING_AGENT_START.txt        Priame zadanie na začatie implementácie.

Spustenie kontroly obsahu
  python3 validate_handoff.py
Príkaz nemení game.json. Aktualizuje validation_report.json a walkthrough.json.
Testuje legálny hlavný priechod bez vedľajších úloh, dohranie všetkých vedľajších
úloh po titulkoch, 120 náhodných legálnych poradí a 24 poradí finálnych portov.

Rozsah dôkazu
Je to úplné zadanie a referenčný model. Nie je priložený hotový herný engine,
maľované pozadia, nahratý dabing ani hrateľný build. Tie má coding agent vytvoriť
podľa tohto obsahu. Nemusí domýšľať dej, NPC, úlohy, dialógy, predmetové recepty,
historické následky ani koniec.

Autoritatívnosť
game.json je zdroj podmienok a ID. HTML a textová biblia vysvetľujú význam.
Každý main a side action je priradený práve jednej questovej skupine.
Vedľajšia Q9 sa dokončí Q9C; Q9D/Q9E/Q9F sú voliteľné rozhovory o následkoch.
Všetky save a runtime operácie musia zachovať raz vykonané action IDs.

Lokality v rôznych epochách sú odlišné hrateľné scény, ale zdieľajú kameru
a oporné body podľa location_families a landmark_layouts. Zmeny nedosiahnite
len farebným filtrom. Kabína Funitelu je hrateľná scéna; film dolnej lanovky
sa nepočíta ako ďalšia lokalita. Reálne názvy rezortu sú podložené zdrojmi;
podoba a program 2035 zostávajú fikciou, nie tvrdením o skutočnej prevádzke.
