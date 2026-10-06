#!/usr/bin/env python3
"""Knowledge-state audit: does Adam (or a text in his voice) name something the player has not met yet?

Owner rule 2026-10-06 (docs/DECISIONS.md "Adam never knows what he has not learned"): every person, place,
item, organisation or fact that Adam names, and every look, journal entry, objective, goal or hint that names
it, must have been introduced to the player earlier in EVERY legal order of play. Introductions are:

  * a line spoken by someone else (NPC, phone, recording, device text SYSTEM, captions) — the speaker's own
    name too, because it is shown above the subtitle;
  * seeing it: the room's name and district (map caption), the hotspot names of a visited room (hover / Space
    labels, NPCs show their full name), the exit and map-connection labels of a visited room;
  * an item in the bag (its inventory name);
  * soft (optional, not counted as an introduction): Adam's looks and optional ambient topics the player may
    or may not have heard.

The order model is the real one (Core: GameRules.GuardsPass / ValidAction, Navigation.BuildGraph,
ContentPlayability.Possible) evaluated as a MUST analysis over all legal orders: for every action the set of
actions that are done before it in every legal order (requires_done, the givers of every needed item — the
intersection when several actions give it —, the room's reachability over gated connections, chronometer
portals and special transitions, the target's visible_after), plus the rooms that are visited before it in every
order (room dominators). A text counts as introduced only when an introduction lies inside that must-set (or
earlier in the same exchange). `--simulate N` cross-checks the must-sets against N seeded random legal orders
(the same step model as ContentPlayability); any violation means the model is wrong and fails the run.

Candidates are all player-visible texts that are not someone else speaking: Adam's lines (actions, topics,
cutscenes, puzzle lines, first entry, first ride), looks and look variants, item looks and purposes, locked
looks, objectives, journal entries, quest goals / hints / rewards, step hints (actions[].hint_step and
ui.hint_step.*), action labels (dialogue choices) and topic labels, puzzle clues and journal clues, epilogue
captions. Each mention of an entity gets an automatic status:

  introduced   an introduction is guaranteed before (in every legal order)
  background   the entity belongs to Adam's own background (family, his school, the places he grew up in, the
               real places of the era every Bratislava/Slovak adult knows, the device once it is in his hands)
  order        an introduction exists that comes earlier in the walkthrough, but not in every legal order
  soft         only an optional look / ambient topic can have introduced it
  none         nothing introduces it before this text (in walkthrough order)

`docs/writing/knowledge/judgements.json` holds Claude's verdict for every non-introduced, non-background
candidate: `problem` (with why + proposed fix type a/b/c) or `acceptable` / `fine` (with the reason). The tool
merges the verdicts and writes `audit.json` (machine-readable) and, with `--write-md`, `AUDIT.md`.

Usage:
    python tools/knowledge_audit.py [--simulate 200] [--write-md] [--list STATUS] [--key KEY] [--entity ID]
    python tools/knowledge_audit.py --unjudged      # candidates without a verdict (exit 1 if any)

Only reads game.json, the overlays, the localization tables and walkthrough.json. Exit 0 ok, 1 unjudged
candidates or simulation mismatch with --strict, 2 input error.
"""
from __future__ import annotations

import argparse
import json
import random
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import text_keys as tk  # noqa: E402
import writing_bundles as wb  # noqa: E402

OUT_DIR = tk.REPO_ROOT / "docs" / "writing" / "knowledge"
JUDGEMENTS = OUT_DIR / "judgements.json"
INVENTORY = "inventory"
CHRONO = "CHRONO"

# --------------------------------------------------------------------------- entities
# (id, type, regex, flags, background, note). Order matters: earlier (more specific) patterns mask their match
# so that later, broader ones do not see it again ("Sokolíkovský dvor" before "Sokolíkova").
CS, CI = 0, re.IGNORECASE
B = True   # Adam's background: acceptable without an introduction

ENTITY_SPECS: list[tuple[str, str, str, int, bool, str]] = [
    # ---- specific places / organisations first (they contain names of people or districts)
    ("place:Sokolíkovský dvor", "place", r"Sokolíkovsk\w* dvor\w*", CS, False, "S69 courtyard (content v2)"),
    ("org:kazetový klub", "org", r"kazetov\w* klub\w*|\bklub\w* v suteréne", CI, False, "Juro's club, S27"),
    ("org:opravovňa odevov", "org", r"opravovň\w* odevov", CI, False, "Milada, S26"),
    ("org:antikvariát", "org", r"antikvariát\w*|Pod druhou rukou", CI, False, "Viera, S22"),
    ("org:fotoateliér", "org", r"fotoateli\w*|\bateliér\w*", CI, False, "Alena, S24"),
    ("org:archívna študovňa", "org", r"študovň\w*", CI, False, "Karol, S23"),
    ("place:Kamenné námestie", "place", r"Kamenn\w* námest\w*", CI, False, "S21"),
    ("place:podchod", "place", r"\bpodchod\w*", CI, False, "S28 Petržalka underpass"),
    ("place:merací stánok", "place", r"merac\w* stán\w*|\bstánk\w* na Starom moste", CI, False, "S30 (P03)"),
    ("place:kultúrna sála", "place", r"kultúrn\w* sál\w*", CI, False, "S34 Ivanka"),
    ("place:kaštieľ / park", "place", r"kaštie\w*", CI, False, "S37 manor park, Ivanka"),
    ("place:čerpacia búdka", "place", r"čerpac\w* búd\w*|skúšobn\w* búd\w*", CI, False, "S38"),
    ("place:meracia miestnosť", "place", r"meraci\w* miestnos\w*|miestnos\w* prvého ZVON\w*", CI, False, "S39"),
    ("place:povala archívu", "place", r"\bpoval\w*", CI, False, "S40 attic"),
    ("place:hospodárska dielňa", "place", r"hospodársk\w* dieln\w*", CI, False, "S35"),
    ("place:výdajňa 1982", "place", r"výdajň\w*", CI, False, "S65 school material store 1982"),
    ("place:záhradný sklad", "place", r"záhradn\w* sklad\w*", CI, False, "S66 school garden store 1982"),
    ("place:technická výstavka", "place", r"technick\w* výstavk\w*|\bvýstavk\w*", CI, False, "S60 class exhibition 1982 / Q9"),
    ("org:Druhý život", "org", r"Druh\w* život\w*|DRUHÝ ŽIVOT", CS, False, "Tamara's workshop, 2035"),
    ("org:klientske centrum", "org", r"klientsk\w* centr\w*", CI, False, "Sára, S46"),
    ("place:servisný pavilón", "place", r"\bpavil[oó]n\w*", CI, False, "S48 Atlas pavilion"),
    ("place:chronokomora", "place", r"chronokomor\w*|synchronizačn\w* komor\w*", CI, False, "S49"),
    ("place:servisné okno", "place", r"servisn\w* okn\w*|školníck\w* okn\w*", CI, False, "the service window 1982/1995/2020"),
    # ---- facts, codes, phrases
    ("fact:K-17", "fact", r"\bK-17\b", CS, False, "annex number / overlay shelf mark"),
    ("fact:Z-17", "fact", r"\bZ-17\b", CS, False, "registration of Mira's fond"),
    ("fact:3–2–6", "fact", r"\b3\s*[–—-]\s*2\s*[–—-]\s*6\b|TRI VLNY|DVA ÚDERY|ŠESŤ DIELIKOV", CS, False, "P03 digits"),
    ("fact:rad 2, stĺpec 3", "fact", r"rad\w* 2\b|stĺp\w* 3\b|druh\w* rad\w* zhora|tret\w* kame\w* zľava|3\s*×\s*4", CI, False, "P05 cavity"),
    ("fact:heslo Lastovička sa vracia", "fact", r"Lastovička sa vracia", CI, False, "password E02/E11/D07"),
    ("fact:ROZDIEL = ZAHODIŤ", "fact", r"ROZDIEL\s*=\s*ZAHODIŤ", CS, False, "normalizer rule"),
    ("fact:Mirina veta", "fact", r"Rôzne údaje neznamenajú neplatné", CI, False, "Mira's 1960 rule"),
    ("fact:Štyri zastávky", "fact", r"Štyri zastávky", CS, False, "Emil's song"),
    ("fact:Žiaden strach, miláčik", "fact", r"Žiaden strach", CS, False, "Rudo's play"),
    ("fact:2032", "fact", r"\b2032\b", CS, False, "Lea's message / death"),
    ("fact:38 rokov", "fact", r"\b38\b|tridsaťosem", CI, False, "the jar in the wall"),
    ("fact:svedectvá Pôvod/Hlas/Súhlas/Návrat", "fact", r"(?<![.!?„\"]\s)(?<!^)\b(Pôvod\w*|Hlas\w*|Súhlas\w*|Návrat\w*)\b|PÔVOD|HLAS\b|SÚHLAS|NÁVRAT|štyri svedectv\w*|svedectv\w*", CS, False, "the four proofs / ports"),
    ("fact:ZÁPIS/MONITOR", "fact", r"\bMONITOR\w*|\bZÁPIS\w*", CS, False, "switch positions"),
    # ---- devices, concepts, items
    ("item:ZVON", "item", r"\bZVON\w*", CS, False, "the 1960 device"),
    ("item:chronometer", "item", r"chronomet\w*", CI, False, "the portable unit"),
    ("item:ochranné pole", "item", r"ochrann\w* pol(e|a|om|i)\b", CI, False, "protects Adam's memory"),
    ("item:spätný zápis", "item", r"spätn\w* zápis\w*", CI, False, "Atlas writing back"),
    ("item:zásobník", "item", r"zásobník\w*", CI, False, "return buffer"),
    ("item:normalizátor", "item", r"normaliz\w*", CI, False, "Viktor's filter"),
    ("org:Atlas", "org", r"\bAtlas\w*", CS, False, "Viktor's organisation / exhibition 2035"),
    ("org:zvukový atlas / krúžok", "org", r"zvukov\w* atlas\w*|\bkrúž(ok|ku|kom|ky|kov|koch)\b|pamäťov\w* krúž\w*", CI, B, "Mira's & Lea's 1995 club (Adam was in it at 10)"),
    ("item:Mirin fond / krabica", "item", r"\bfond\w*|\bkrabic\w* Z|technick\w* archív\w*", CI, False, "Mira's archive"),
    ("item:kalibračná platňa", "item", r"\bplat[ňn]\w*", CI, False, "1960 brass plate"),
    ("item:odtlačok", "item", r"\bodtlač\w*(?! veľk)", CI, False, "imprint 1962"),
    ("item:registračný list", "item", r"registračn\w* list\w*|\bregistrác\w*|\bzaregistr\w*|druhopis\w*", CI, False, "post office 1962"),
    ("item:uhľový papier", "item", r"\buh[lľ]ov\w* papier\w*", CI, False, "carbon paper"),
    ("item:rydlo", "item", r"\brydl\w*", CI, False, "Vera's stylus"),
    ("item:pumpa / manžeta", "item", r"ručn\w* pump\w*|\bpump(a|y|e|u|ou)\b|\bmanžet\w*", CI, False, "1960 cooling model"),
    ("item:dierovač", "item", r"\bdierova\w*", CI, False, "Lída's punch"),
    ("item:nity", "item", r"\bnit(y|ov|mi|ami)\b", CI, False, "rivets"),
    ("item:mostík", "item", r"\bmostík\w*|keramick\w* pätic\w*", CI, False, "the return bridge 1982"),
    ("item:lastovička", "item", r"\blastovič\w*", CI, False, "Tóno's swallow"),
    ("item:servisná dutina", "item", r"\bdutin\w*", CI, False, "the cavity in the wall"),
    ("item:múrik", "item", r"\bmúrik\w*", CI, False, "the low wall"),
    ("item:pohár", "item", r"\bpoh[áa]r\w*", CI, False, "the jar"),
    ("item:lipa", "item", r"\blip(a|y|e|u|ou|ami|ách|ovom)\b|\bsadenic\w*", CI, False, "the 1982 lime tree"),
    ("item:ohrádka", "item", r"\bohrád\w*", CI, False, "tree guard"),
    ("item:vozík", "item", r"\bvozík\w*", CI, False, "hand cart route 1982"),
    ("item:servisný záznam 1982", "item", r"servisn\w* knih\w*|servisn\w* záznam\w*|Otov\w* nákres\w*", CI, False, "LOG1982"),
    ("item:protokol o odovzdaní", "item", r"protokol\w* o odovzdan\w*|potvrden\w* odovzdan\w*", CI, False, "handover 2020"),
    ("item:remienok", "item", r"\bremien\w*", CI, False, "1995 belt"),
    ("item:kazeta s rušenými stopami / školská kazeta", "item", r"rušen\w* stop\w*|školsk\w* kazet\w*|pôvodn\w* kazet\w*", CI, False, "1995 tape"),
    ("item:adaptér", "item", r"\badaptér\w*", CI, False, "1995 audio chain"),
    ("item:konektor", "item", r"\bkonektor\w*", CI, False, "1995 audio chain"),
    ("item:návlek", "item", r"\bnávl[eé]?[kč]\w*", CI, False, "1995 audio chain"),
    ("item:prepojka", "item", r"\bprepojk\w*|zvukov\w* vstup\w*", CI, False, "1995 audio chain"),
    ("item:mapa uzlov", "item", r"map\w* (meracích )?uzlov|\buzlov\w* map\w*", CI, False, "1995 map"),
    ("item:fólia", "item", r"\bfóli\w*", CI, False, "1995 overlay"),
    ("item:negatív", "item", r"\bnegatív\w*", CI, False, "1995 photo negative"),
    ("item:kalibračný stojan", "item", r"kalibračn\w* stojan\w*", CI, False, "1995 photo"),
    ("item:metronóm", "item", r"metronóm\w*", CI, False, "Emil's"),
    ("item:cievka", "item", r"\bciev\w*", CI, False, "Dezider's"),
    ("item:čítačka", "item", r"\bčítač\w*", CI, False, "2035 reader"),
    ("item:katalógová karta", "item", r"katalógov\w* kart\w*", CI, False, "2035"),
    ("item:servisný preukaz", "item", r"\bpreukaz\w*", CI, False, "2035"),
    ("item:lístok na oba úseky", "item", r"lístok na oba|spiatočn\w* lístk?\w*", CI, False, "2035 lift ticket"),
    ("item:terminál / stojan / stopa / postup", "item", r"\btermin[áa]l\w*|pasívn\w* stojan\w*|referenčn\w* stop\w*|obnovovac\w* postup\w*", CI, False, "2035 restore chain"),
    ("item:Leina správa", "item", r"hlasov\w* správ\w*|pôvodn\w* správ\w*", CI, False, "Lea's message"),
    ("item:Bodkova loptička", "item", r"\bloptič\w*", CI, False, "Q1"),
    ("item:oznam", "item", r"veľk\w* (čitateľn\w* )?oznam\w*|oznam\w* veľkým písmom|\bletá(k|ku|kom|ky)\b", CI, False, "Q2 flyer"),
    ("item:noty", "item", r"\bnot(y|ami|ách)\b", CI, False, "Q4"),
    ("item:krieda", "item", r"biel\w* (školsk\w* )?kried\w*|kús\w* kried\w* na panel", CI, False, "Q5 white chalk"),
    ("item:krmivo", "item", r"\bkrmiv\w*|\bsemen\w*|\bsemien\w*", CI, False, "Q6"),
    ("item:scenár", "item", r"\bscenár\w*", CI, False, "Q7"),
    ("item:Janina schéma", "item", r"Janin\w* (pôvodn\w* )?schém\w*|\bjej schém\w*|vlastn\w* schém\w*|vylepšen\w* schém\w*", CI, False, "Q9"),
    ("item:zvonček", "item", r"triedn\w* zvonč\w*|\bpútk\w*", CI, False, "Q10 class bell"),
    ("item:vrchnák", "item", r"\bvrchn[áa]k\w*", CI, False, "Q11"),
    ("item:Zuzanin lístok", "item", r"Zuzanin\w* lístok\w*|Zuzanin\w* lístk\w*", CI, False, "Q10"),
    # ---- people (glossary.json names, extended with surnames and roles; case-sensitive)
    ("person:Adam", "person", r"\bAdam\w*|\bpán(a|ovi|om)? Hrušk(a|u|ovi|om)\b", CS, B, "himself"),
    ("person:Mira", "person", r"\bMir(a|y|e|u|ou|in\w*)\b|\b[Bb]abk\w*|Hrušková|Hruškovej|Hruškovú|Hruškovou|stará mama|starej mam\w*", CS, B, "his grandmother (family)"),
    ("person:Tóno", "person", r"\bTón(o|a|ovi|om|ov\w*)\b|\bAnton\w*|Farkaš\w*", CS, False, "school caretaker; Oto's grandson"),
    ("person:Oto", "person", r"\bOt(o|a|ovi|om|ov|ova|ovo|ove|ovu|ovom|ovho|ovmu|ovej|ových|ovi)\b|\bBielik\w*", CS, False, "mechanic, ZVON co-author"),
    ("person:Ela", "person", r"\bEl(a|y|e|u|ou|in|ina|ino|ine|inu|inej|inho|inmu|inom|iným)\b|\bŠvecov(á|ej|ú|ou)\b", CS, False, "volunteer coordinator 2020"),
    ("person:Dana", "person", r"\bDan(a|y|e|u|ou|in|ina|ino|ine|inu|inej|inho)\b|Valov\w*", CS, False, "shop 2020"),
    ("person:Roman", "person", r"\bRoman(a|ovi|om|ov\w*)?\b", CS, False, "volunteer 2020"),
    ("person:Lenka", "person", r"\bLenk\w*|Bartošov\w*", CS, False, "neighbour 2020"),
    ("person:Bodka", "person", r"\bBodk\w*", CS, False, "dog 2020"),
    ("person:Jozef", "person", r"\bJozef\w*|Mlynár\w*", CS, False, "neighbour 2020"),
    ("person:Jana", "person", r"\bJan(a|y|e|u|ou|in|ina|ino|ine|inu|inej|inho|inmu|inom)\b|\bVargov\w*", CS, False, "side story 1982-2035"),
    ("person:Lea", "person", r"\bLe(a|y|i|u|ou|in|ina|ino|ine|inu|inej|inho)\b|\bKormanov(á|ej|ú|ou)\b", CS, False, "teacher 1995 (Adam's own teacher at 10)"),
    ("person:Viktor", "person", r"\bViktor\w*|\bKorman(a|ovi|om)?\b", CS, False, "Atlas 2035, Lea's son"),
    ("person:Nina", "person", r"\bNin(a|y|e|u|ou|in|ina|ino|ine|inu|inej|inho)\b", CS, False, "Ela's daughter 2035"),
    ("person:Soňa", "person", r"\bSo(ňa|ne|ni|ňu|ňou|ňin\w*|nin\w*)\b|Urbanov(á|ej|ú|ou)\b", CS, False, "pupil 1995"),
    ("person:Zita", "person", r"\bZit(a|y|e|u|ou|in\w*)\b|Ondrušov\w*", CS, False, "kiosk 1995"),
    ("person:Emil", "person", r"\bEmil\w*|\bBelan\w*", CS, False, "musician 1995"),
    ("person:Pali", "person", r"\bPal(i|iho|imu|im)\b|\bDrobn(ý|ého|ému|ým)\b", CS, False, "repairman 1995, Karlova Ves"),
    ("person:Viera", "person", r"\bVier(a|y|e|u|ou|in\w*)\b|Holubov\w*", CS, False, "bookseller 1995"),
    ("person:Karol", "person", r"\bKarol\w*|\bMert(a|u|ovi|om)\b|\barchivár\w*", CS, False, "archivist 1995"),
    ("person:Alena", "person", r"\bAlen\w*|Svobodov\w*|\bfotografk\w*", CS, False, "photographer 1995"),
    ("person:Fero", "person", r"\bFer(o|a|ovi|om|ov\w*)\b|Lánik\w*", CS, False, "market 1995"),
    ("person:Milada", "person", r"\bMilad\w*|Kyselov\w*", CS, False, "tailor 1995"),
    ("person:Juro", "person", r"Juraj Malík\w*|\bJur(o|a|ovi|om|ov\w*)\b|\bMalík\w*", CS, False, "cassette club 1995"),
    ("person:Juraj", "person", r"\bJuraj\w*|Križan\w*", CS, False, "painter 1995"),
    ("person:Dezider", "person", r"\bDezi\w*|\brádioamatér\w*", CS, False, "radio amateur 1995, Petržalka"),
    ("person:Zuzana", "person", r"\bZuz\w*", CS, False, "1962 child / 1995 adult"),
    ("person:Kubo", "person", r"\bKub(o|a|ovi|om|ko|kovi|ov\w*)\b", CS, False, "child 1995"),
    ("person:Božo", "person", r"\bBož(o|a|ovi|om|idar\w*)\b|\bFial(a|u|ovi|om)\b", CS, False, "station 1962"),
    ("person:Berta", "person", r"\bBert\w*|Kovárov\w*", CS, False, "village green 1962"),
    ("person:Alojz", "person", r"\bAlojz\w*|\bBaran\w*|\bpoštár\w*|\bpoštmajster\w*", CS, False, "post office 1962"),
    ("person:Béla", "person", r"\bBél\w*", CS, False, "pigeon 1962"),
    ("person:Lída", "person", r"\bLíd\w*|Fialov\w*", CS, False, "hall 1962"),
    ("person:Rudo", "person", r"\bRud(o|a|ovi|om|olf\w*|ov\w*)\b|Pavlík\w*", CS, False, "director 1962"),
    ("person:Štefan", "person", r"\bŠtefan\w*|Haluš\w*|\bskladník\w*", CS, False, "store 1962"),
    ("person:Vera", "person", r"\bVer(a|y|e|ou|in\w*)\b|Nemcov\w*", CS, False, "draughtswoman 1962"),
    ("person:Tamara", "person", r"\bTamar\w*|Kráľov(á|ej|ú|ou)\b", CS, False, "repair workshop 2035"),
    ("person:Boris", "person", r"\bBoris\w*|\bUrban(a|ovi|om)?\b", CS, False, "exhibition 2035"),
    ("person:Sára", "person", r"\bSár(a|y|e|u|ou|in\w*)\b|Vrbov(á|ej|ú|ou)\b", CS, False, "client centre 2035"),
    ("person:Očko", "person", r"\bOčk(o|a|ovi|om|ov\w*)\b", CS, False, "delivery robot 2035"),
    ("person:Ivan", "person", r"\bIvan(a|ovi|om)?\b|\bHorsk(ý|ého|ému|ým)\b", CS, False, "Priehyba 2035"),
    ("person:Miloš", "person", r"\bMiloš\w*|\bPolák\w*", CS, False, "Funitel tourist 2035"),
    ("person:Dobrovič", "person", r"\bDobrovič\w*", CS, False, "teacher 1982"),
    ("person:Ružena", "person", r"\bRužen\w*|[Pp]ani Mal(á|ej|ú|ou)\b", CS, False, "shop 1982"),
    ("person:Marta", "person", r"\bMart(a|y|e|u|ou|in\w*)\b|Dobiášov\w*", CS, False, "store 1982"),
    ("person:Šimon", "person", r"\bŠimon\w*|\bRybár(a|ovi|om)?\b|\bzáhradník\w*", CS, False, "gardener 1982"),
    # ---- places (glossary.json places; districts and real places)
    ("place:Lúčny koník", "place", r"Lúčn\w* koník\w*", CS, B, "playground where he lives"),
    ("place:výdajné miesto", "place", r"výdajn\w* miest\w*", CI, B, "the pick-up point he volunteers at (2020)"),
    ("place:Chorvátsky Grob", "place", r"\bGrob\w*|Chorvátsk\w* Grob\w*", CS, B, "where he lives"),
    ("place:Čierna Voda", "place", r"Čiern\w* Vod\w*", CS, B, "where he lives"),
    ("place:Dúbravka", "place", r"Dúbrav\w*", CS, B, "where he grew up"),
    ("place:Sokolíkova", "place", r"Sokolíkov\w*", CS, B, "his school"),
    ("place:Karlova Ves", "place", r"Karlov\w* Ves\w*|Karlovej Vsi|Karlovesk\w*|Karlovesk\w*", CS, B, "Bratislava district"),
    ("place:Staré Mesto", "place", r"Star\w* Mest\w*", CS, B, "Bratislava district"),
    ("place:Ružinov", "place", r"Ružinov\w*", CS, B, "Bratislava district"),
    ("place:Miletičova", "place", r"Miletič\w*", CS, B, "Bratislava market street"),
    ("place:Petržalka", "place", r"Petržal\w*", CS, B, "Bratislava district"),
    ("place:Starý most", "place", r"\bStar(ý|ého|ému|om|ým) most(a|e|u|om)?\b", CS, B, "Bratislava bridge"),
    ("place:Dunaj", "place", r"\bDunaj\w*", CS, B, "the river"),
    ("place:Ivanka pri Dunaji", "place", r"\bIvank\w*|\bivansk\w*|\bIvansk\w*", CS, B, "real village"),
    ("place:Jasná", "place", r"\bJasn(á|ej|ú|ou)\b", CS, B, "real resort"),
    ("place:Biela Púť", "place", r"Biel\w* Pú\w*", CS, B, "real area of Jasná"),
    ("place:Priehyba", "place", r"Priehyb\w*", CS, B, "real station"),
    ("place:Chopok", "place", r"\bChop\w*", CS, B, "real mountain"),
    ("place:Rotunda", "place", r"Rotund\w*", CS, B, "real building on Chopok"),
    ("place:Grand Jasná", "place", r"\bGrand\w*", CS, B, "real hotel"),
    ("place:Vrbické pleso", "place", r"Vrbick\w*", CS, B, "real lake"),
    ("place:Funitel", "place", r"Funitel\w*", CS, B, "real cable car"),
]

# speaker / character id -> person entity
SPEAKER_ENTITY = {
    "ADAM": "Adam", "ADAM10": "Adam", "MIRA20": "Mira", "MIRA95": "Mira", "MIRA60": "Mira",
    "TONO82": "Tóno", "TONO": "Tóno", "TONO20": "Tóno", "OTO": "Oto", "OTO82": "Oto",
    "JANA82": "Jana", "JANA95": "Jana", "JANA20": "Jana", "JANA35": "Jana", "LEA95": "Lea", "LEA_REC": "Lea",
    "VIKTOR": "Viktor", "NINA": "Nina", "NINA_REMOTE": "Nina", "ELA": "Ela", "DANA": "Dana", "ROMAN": "Roman",
    "LENKA": "Lenka", "BODKA": "Bodka", "JOZEF": "Jozef", "SONA": "Soňa", "ZITA": "Zita", "EMIL": "Emil",
    "PALI": "Pali", "VIERA": "Viera", "KAROL": "Karol", "ARCHIVAR": "Karol", "ALENA": "Alena", "FOTO": "Alena",
    "FERO": "Fero", "TRH": "Fero", "MILADA": "Milada", "JURO": "Juro", "JURAJ": "Juraj", "DEZI": "Dezider",
    "BOZO": "Božo", "BERTA": "Berta", "ALOJZ": "Alojz", "POSTA": "Alojz", "LIDA": "Lída", "RUDO": "Rudo",
    "STEFAN": "Štefan", "SKLAD": "Štefan", "VERA60": "Vera", "ZUZANA": "Zuzana", "ZUZANA95": "Zuzana",
    "KUBO": "Kubo", "DOBRO": "Dobrovič", "RUZENA": "Ružena", "MARTA82": "Marta", "SIMON": "Šimon",
    "TAMARA": "Tamara", "BORIS": "Boris", "SARA": "Sára", "ROBOT": "Očko", "IVAN": "Ivan", "TURISTA": "Miloš",
}
# speakers whose lines are not an introduction (Adam himself)
SELF_SPEAKERS = {"ADAM"}


@dataclass
class Entity:
    id: str
    type: str
    rx: re.Pattern
    background: bool
    note: str


ENTITIES = [Entity(i, t, re.compile(r, f), b, n) for i, t, r, f, b, n in ENTITY_SPECS]
ENTITY_BY_ID = {e.id: e for e in ENTITIES}


def mentions(text: str) -> list[tuple[str, str]]:
    """(entity id, matched text) for every entity in text, in ENTITY_SPECS priority (masking)."""
    out: list[tuple[str, str]] = []
    buf = text
    for ent in ENTITIES:
        found = []
        for m in ent.rx.finditer(buf):
            if m.group(0).strip():
                found.append(m)
        if found:
            out.append((ent.id, found[0].group(0)))
            for m in reversed(found):
                buf = buf[:m.start()] + " " * (m.end() - m.start()) + buf[m.end():]
    return out


def person(name: str) -> str:
    return "person:" + name


# --------------------------------------------------------------------------- order model (must analysis)

class OrderModel:
    """Must-before sets over all legal orders (mirrors Core's step model)."""

    def __init__(self, game: dict, walkthrough: dict):
        self.g = game
        self.actions = {a["id"]: a for a in game["actions"]}
        self.ids = [a["id"] for a in game["actions"]]
        self.rooms = {r["id"]: r for r in game["rooms"]}
        self.hotspots = {h["id"]: (r["id"], h) for r in game["rooms"] for h in r.get("hotspots", [])}
        self.initial_items = set(game["initial_state"].get("inventory", []))
        self.start = game["initial_state"]["room"]
        self.givers: dict[str, list[str]] = defaultdict(list)
        for a in game["actions"]:
            for it in a.get("gives", []):
                self.givers[it].append(a["id"])
        self.eras = {e["year"]: e for e in game["eras"]}
        self.main_route = [s["action"] for s in walkthrough.get("main_route", [])]
        self.post_route = list(walkthrough.get("postgame_optional_route", []))
        self._solve()
        self._positions()
        self._timeline(walkthrough)

    # -- helpers
    def needs(self, a: dict) -> set[str]:
        out = set(a.get("requires_items", [])) | set(a.get("consumes", []))
        if a.get("selected_item"):
            out.add(a["selected_item"])
        if a.get("kind") == "combine":
            out.add(a["target"])
        return out

    def is_inv(self, aid: str) -> bool:
        return self.actions[aid]["room"] == INVENTORY

    def _edges(self):
        """(from_room or None, to_room, required actions, required items) for every way into a room."""
        edges = []
        for c in self.g["connections"]:
            req = set(c.get("requires_done", []))
            edges.append((c["from"], c["to"], req, set()))
            if c.get("bidirectional"):
                edges.append((c["to"], c["from"], req, set()))
        for src in self.g["anchor_nodes"]:
            for era in self.g["eras"]:
                if era["year"] == src["year"]:
                    continue
                req = set(src.get("requires_done", []))
                if era.get("unlocked_by"):
                    req.add(era["unlocked_by"])
                edges.append((src["room"], era["anchor"], req, {CHRONO}))
        for st in self.g.get("special_transitions", []):
            edges.append((None, st["to"], {st["after"]}, set()))
        return edges

    def _solve(self) -> None:
        ALL = frozenset(self.ids)
        ROOMS = frozenset(self.rooms)
        G = {a: ALL for a in self.ids}               # must-done before action
        R = {r: ALL for r in self.rooms}              # must-done before first entering room
        V = {r: ROOMS for r in self.rooms}            # must-visited rooms when entering room (incl. itself)
        R[self.start] = frozenset()
        V[self.start] = frozenset({self.start})
        edges = self._edges()

        def closure(req) -> frozenset:
            out = set()
            for d in req:
                out.add(d)
                out |= G[d]
            return frozenset(out)

        def item_must(item) -> frozenset:
            if item in self.initial_items:
                return frozenset()
            gs = self.givers.get(item, [])
            if not gs:
                return frozenset()
            acc = None
            for gid in gs:
                s = frozenset({gid}) | G[gid]
                acc = s if acc is None else acc & s
            return acc

        def visited_of(acts) -> frozenset:
            out = set()
            for x in acts:
                if not self.is_inv(x):
                    out |= V[self.actions[x]["room"]]
            return frozenset(out)

        changed = True
        rounds = 0
        while changed:
            rounds += 1
            changed = False
            for r in self.rooms:
                if r == self.start:
                    continue
                accR, accV = None, None
                for frm, to, req, items in edges:
                    if to != r:
                        continue
                    need = closure(req)
                    for it in items:
                        need |= item_must(it)
                    if frm is None:
                        er, ev = need, visited_of(need)
                    else:
                        er, ev = R[frm] | need, V[frm] | visited_of(need)
                    accR = er if accR is None else accR & er
                    accV = ev if accV is None else accV & ev
                newR = accR if accR is not None else ALL
                newV = (accV | {r}) if accV is not None else ROOMS
                if newR != R[r]:
                    R[r], changed = newR, True
                if newV != V[r]:
                    V[r], changed = newV, True
            for aid in self.ids:
                a = self.actions[aid]
                s = set(closure(a.get("requires_done", [])))
                for it in self.needs(a):
                    s |= item_must(it)
                if a["room"] != INVENTORY:
                    s |= R[a["room"]]
                    hs = self.hotspots.get(a["target"])
                    if hs:
                        s |= closure(hs[1].get("visible_after", []))
                s.discard(aid)
                ns = frozenset(s)
                if ns != G[aid]:
                    G[aid], changed = ns, True
            if rounds > 500:
                raise RuntimeError("must analysis does not converge")
        self.G, self.R, self.V = G, R, V
        self._closure, self._item_must, self._visited_of = closure, item_must, visited_of

    def closure(self, req) -> frozenset:
        return self._closure(req)

    def item_must(self, item) -> frozenset:
        return self._item_must(item)

    def visited_of(self, acts) -> frozenset:
        return self._visited_of(acts)

    def _positions(self) -> None:
        """Walkthrough position of every action: main route index; other actions as early as they can be."""
        pos = {aid: float(n) for n, aid in enumerate(self.main_route)}
        for aid in self.ids:
            if aid in pos:
                continue
            mains = [pos[x] for x in self.G[aid] if x in pos]
            pos[aid] = (max(mains) if mains else -1.0) + 0.5
        self.pos = pos

    def _timeline(self, walkthrough: dict) -> None:
        """Story order of the walkthrough: when each main action is done and each room first entered."""
        INF = float("inf")
        self.at = {aid: INF for aid in self.ids}
        self.vt = {r: INF for r in self.rooms}
        self.vt[self.start] = 0.0
        for n, step in enumerate(walkthrough.get("main_route", []), 1):
            for k, room in enumerate(step.get("travel_path", [])):
                if room in self.vt and self.vt[room] == INF:
                    self.vt[room] = n - 0.5 + k * 0.01
            self.at[step["action"]] = float(n)
            own = self.actions.get(step["action"], {}).get("room")
            if own in self.vt and self.vt[own] == INF:
                self.vt[own] = n - 0.05   # relocated actions (world overlay): the walkthrough's path predates the room
            st = next((t for t in self.g.get("special_transitions", []) if t["after"] == step["action"]), None)
            for room in ([st["to"]] if st else []) + [step.get("room_after")]:
                if room in self.vt and self.vt[room] == INF:
                    self.vt[room] = n + 0.1

    def wt_of(self, acts, rooms=()) -> float:
        vals = [self.at[x] for x in acts if x in self.at] + [self.vt[r] for r in rooms if r in self.vt]
        return max(vals) if vals else 0.0

    def pos_of_set(self, acts) -> float:
        vals = [self.pos[x] for x in acts if x in self.pos]
        return max(vals) if vals else -1.0

    def step_label(self, aid: str) -> str:
        if aid in self.main_route:
            return f"step {self.main_route.index(aid) + 1} ({aid})"
        mains = [x for x in self.G[aid] if x in self.main_route]
        after = max(mains, key=lambda x: self.main_route.index(x)) if mains else None
        return f"{aid} (optional, possible after step {self.main_route.index(after) + 1} {after})" if after else f"{aid} (optional, from the start)"

    # -- random legal orders (cross-check, ContentPlayability.Possible)
    def simulate(self, n: int, seed0: int = 1, quest_must: dict | None = None) -> list[str]:
        """Plays n seeded random legal orders; reports every action done before an action of its must-set, and (with
        quest_must) every main quest that becomes Quests.NextMainQuest before its must-set is done."""
        problems: list[str] = []
        self.sim_lengths: list[int] = []
        mains = [q for q in self.g["quests"] if q.get("type") == "main"]
        conns = self.g["connections"]
        anchors = self.g["anchor_nodes"]
        special = {st["after"]: st["to"] for st in self.g.get("special_transitions", [])}
        for k in range(n):
            rnd = random.Random(seed0 + k * 7919)
            done: list[str] = []
            dset: set[str] = set()
            inv = set(self.initial_items)
            room = self.start
            for _ in range(len(self.ids) + 1):
                # reachable rooms (BuildGraph)
                graph = defaultdict(set)
                for c in conns:
                    if set(c.get("requires_done", [])) <= dset:
                        graph[c["from"]].add(c["to"])
                        if c.get("bidirectional"):
                            graph[c["to"]].add(c["from"])
                if CHRONO in inv:
                    for src in anchors:
                        if set(src.get("requires_done", [])) <= dset:
                            for era in self.g["eras"]:
                                if era["year"] != src["year"] and (not era.get("unlocked_by") or era["unlocked_by"] in dset):
                                    graph[src["room"]].add(era["anchor"])
                seen, todo = {room}, [room]
                while todo:
                    x = todo.pop()
                    for y in graph[x]:
                        if y not in seen:
                            seen.add(y)
                            todo.append(y)
                enabled = []
                for aid in self.ids:
                    a = self.actions[aid]
                    if aid in dset or dset & set(a.get("excluded_done", [])):
                        continue
                    if not set(a.get("requires_done", [])) <= dset or not set(a.get("requires_items", [])) <= inv:
                        continue
                    if not set(a.get("consumes", [])) <= inv or any(it in inv for it in a.get("gives", [])):
                        continue
                    if a.get("selected_item") and a["selected_item"] not in inv:
                        continue
                    if a["room"] == INVENTORY:
                        if a.get("kind") == "combine" and a["target"] not in inv:
                            continue
                        enabled.append(aid)
                        continue
                    if a["room"] not in seen:
                        continue
                    hs = self.hotspots.get(a["target"])
                    if not hs or hs[0] != a["room"]:
                        continue
                    h = hs[1]
                    if not set(h.get("visible_after", [])) <= dset or dset & set(h.get("hide_after", [])):
                        continue
                    enabled.append(aid)
                if quest_must:
                    for q in mains:
                        if q["completion"] in dset:
                            continue
                        if any(x in enabled for x in q["actions"]):
                            miss = quest_must[q["id"]] - dset
                            if miss:
                                problems.append(f"random order {k + 1}: quest {q['id']} is next before {sorted(miss)}")
                            break
                if not enabled:
                    break
                nxt = enabled[rnd.randrange(len(enabled))]
                a = self.actions[nxt]
                missing = self.G[nxt] - dset
                if missing:
                    problems.append(f"random order {k + 1}: {nxt} done before {sorted(missing)} (must-set wrong)")
                if a["room"] != INVENTORY:
                    room = a["room"]
                for it in a.get("consumes", []):
                    inv.discard(it)
                inv |= set(a.get("gives", []))
                done.append(nxt)
                dset.add(nxt)
                if nxt in special:
                    room = special[nxt]
            self.sim_lengths.append(len(done))
        return problems


# --------------------------------------------------------------------------- display points

@dataclass
class Point:
    """When a text is shown: actions surely done, rooms surely visited, the exchange it belongs to."""
    must: frozenset
    rooms: frozenset
    owner: str            # action id / topic id / cutscene id / room id ...
    idx: int              # position inside the owner (lines), -1 before, 999 after the lines
    pos: float            # earliest possible position (main-route index of its must-set)
    where: str            # plain words
    wt: float = 0.0       # time in the walkthrough's story order (inf: not on the walkthrough)
    at_rooms: tuple = ()  # the room(s) where it is shown


@dataclass
class Intro:
    entity: str
    hard: bool
    owner: str
    idx: int
    must: frozenset       # actions that are done whenever this intro has happened (its own action included)
    req_rooms: frozenset  # rooms that must be visited (a room-visit intro)
    pos: float
    what: str             # plain words
    key: str = ""
    wt: float = 0.0


@dataclass
class Candidate:
    key: str
    kind: str
    era: str
    text: str
    speaker: str | None
    point: Point
    mentions: list = field(default_factory=list)   # (entity, matched)


CANDIDATE_FIELDS = {
    "rooms[].first_entry[].text", "rooms[].hotspots[].look", "rooms[].hotspots[].look_variants[].text",
    "rooms[].exits[].locked_look", "rooms[].exits[].first_ride[].text", "connections[].locked_look",
    "items[].look", "items[].purpose", "actions[].label", "actions[].journal_text", "actions[].objective",
    "actions[].lines[].text", "actions[].hint_step", "characters[].ambient_topics[].label",
    "characters[].ambient_topics[].lines[].text", "cutscenes[].beats[].lines[].text", "quests[].title",
    "quests[].goal", "quests[].reward", "quests[].hints[]", "puzzles[].title", "puzzles[].clue",
    "puzzles[].wrong_line", "puzzles[].success_line", "journal_contract.clues[]", "epilogue[].shot",
    "epilogue[].line", "puzzles[].controls.confirm_label",
}
LINE_FIELDS = {"actions[].lines[].text", "characters[].ambient_topics[].lines[].text",
               "cutscenes[].beats[].lines[].text", "rooms[].first_entry[].text",
               "rooms[].exits[].first_ride[].text", "epilogue[].line"}


def era_name(era) -> str:
    return {2020: "2020", 1995: "1995", 1960: "1962", 1982: "1982", 2035: "2035"}.get(era, "general")


class Audit:
    def __init__(self):
        self.game, overlay = tk.effective_game()
        if overlay.errors:
            raise SystemExit("content overlay invalid: " + "; ".join(overlay.errors[:3]))
        self.walk = wb.load_walkthrough()
        self.index, self.model = wb.build_key_index(self.game, self.walk)
        self.om = OrderModel(self.game, self.walk)
        self.text = {k: v.text for k, v in self.index.items()}
        self.intros: dict[str, list[Intro]] = defaultdict(list)
        self.cands: list[Candidate] = []
        self._topic_must: dict[str, tuple[frozenset, frozenset, float, str]] = {}
        self._build()

    # ---- points
    def action_point(self, aid: str, idx: int) -> Point:
        om = self.om
        must = om.G[aid] | ({aid} if idx >= 999 else frozenset())
        rooms = om.visited_of(must | {aid})
        a = om.actions[aid]
        where = f"{aid} ({a['room']})"
        return Point(must, rooms, aid, idx, om.pos[aid] + (0.01 * min(idx, 100) / 100 if idx >= 0 else 0), where,
                     at_rooms=() if a["room"] == INVENTORY else (a["room"],))

    def room_point(self, room: str, extra=frozenset(), owner: str | None = None, idx: int = 0) -> Point:
        om = self.om
        must = om.R[room] | om.closure(extra)
        rooms = om.V[room] | om.visited_of(must)
        return Point(must, rooms, owner or room, idx, om.pos_of_set(must) + 0.2, f"room {room}", at_rooms=(room,))

    def item_point(self, item: str) -> Point | None:
        om = self.om
        if item in om.initial_items:
            return Point(frozenset(), frozenset({om.start}), "initial", 0, -1.0, "initial inventory")
        gs = om.givers.get(item, [])
        if not gs:
            return None
        must = om.item_must(item)
        first = min(gs, key=lambda g: om.pos[g])
        return Point(must, om.visited_of(must), first, 999, om.pos[first] + 0.05, f"item {item} (from {', '.join(gs)})")

    def topic_info(self, cid: str, topic: dict):
        om = self.om
        rooms = [h_room for h_room, h in ((r, h) for r, h in om.hotspots.values()) if h.get("character_id") == cid]
        if not rooms:
            rooms = self.model.characters.get(cid, {}).get("rooms") or []
        rmust = None
        rvis = None
        for r in rooms:
            if r not in om.R:
                continue
            m = om.R[r]
            v = om.V[r]
            rmust = m if rmust is None else rmust & m
            rvis = v if rvis is None else rvis & v
        rmust = rmust or frozenset()
        rvis = rvis or frozenset()
        req = om.closure(topic.get("requires_done", []))
        must = rmust | req
        rvis = rvis | om.visited_of(must)
        return must, rvis, om.pos_of_set(must) + 0.3, ",".join(rooms)

    # ---- intros
    def add_intro(self, ent: str, hard: bool, owner: str, idx: int, must: frozenset, rooms: frozenset, pos: float,
                  what: str, key: str = "") -> None:
        wt = self.om.wt_of(must, rooms)
        self.intros[ent].append(Intro(ent, hard, owner, idx, must, rooms, pos, what, key, wt))

    def intro_text(self, text: str, hard: bool, owner: str, idx: int, must, rooms, pos, what, key="") -> None:
        for ent, _ in mentions(text):
            self.add_intro(ent, hard, owner, idx, frozenset(must), frozenset(rooms), pos, what, key)

    def _build(self) -> None:
        g, om, T = self.game, self.om, self.text
        # -- rooms: names, district, hotspot names, exit / connection labels, looks (soft)
        for room in g["rooms"]:
            rid = room["id"]
            rp_must, rp_rooms = om.R[rid], om.V[rid]
            pos = om.pos_of_set(rp_must) + 0.2
            self.intro_text(T.get(tk.room_name(rid), room["name"]), True, rid, 0, rp_must, frozenset({rid}), pos,
                            f"room name {rid} (seen on entering)", tk.room_name(rid))
            if room.get("district"):
                self.intro_text(room["district"], True, rid, 0, rp_must, frozenset({rid}), pos, f"district caption of {rid}")
            for h in room.get("hotspots", []):
                vis = om.closure(h.get("visible_after", []))
                name = T.get(tk.hotspot_name(h["id"]), h["name"])
                self.intro_text(name, True, rid, 0, rp_must | vis, frozenset({rid}), om.pos_of_set(rp_must | vis) + 0.2,
                                f"hotspot name {h['id']} (hover / Space label in {rid})", tk.hotspot_name(h["id"]))
                if h.get("character_id") in SPEAKER_ENTITY:
                    self.add_intro(person(SPEAKER_ENTITY[h["character_id"]]), True, rid, 0, rp_must | vis, frozenset({rid}),
                                   om.pos_of_set(rp_must | vis) + 0.2, f"NPC {h['id']} seen in {rid}")
                look_key = h.get("look_line_id") or tk.hotspot_look(h["id"])
                self.intro_text(T.get(look_key, h.get("look", "")), False, rid, 0, rp_must | vis, frozenset({rid}),
                                om.pos_of_set(rp_must | vis) + 0.2, f"look {look_key}", look_key)
                for n, var in enumerate(h.get("look_variants", [])):
                    vk = tk.hotspot_look_variant(h["id"], n + 1)
                    vm = rp_must | vis | om.closure([var["after"]])
                    self.intro_text(T.get(vk, var.get("text", "")), False, rid, 0, vm, frozenset({rid}),
                                    om.pos_of_set(vm) + 0.2, f"look variant {vk}", vk)
            for ex in room.get("exits", []):
                lk = tk.exit_label(ex["id"])
                self.intro_text(T.get(lk, ex.get("label", "")), True, rid, 0, rp_must, frozenset({rid}), pos,
                                f"exit label {ex['id']} (in {rid})", lk)
        for c in g["connections"]:
            for frm in ([c["from"], c["to"]] if c.get("bidirectional") else [c["from"]]):
                lk = tk.connection_label(c["from"], c["to"])
                self.intro_text(T.get(lk, c.get("label", "")), True, frm, 0, om.R[frm], frozenset({frm}),
                                om.pos_of_set(om.R[frm]) + 0.2, f"map/exit label {c['from']}-{c['to']} (in {frm})", lk)
        # -- items in the bag
        for it in g["items"]:
            p = self.item_point(it["id"])
            if p is None:
                continue
            self.intro_text(T.get(tk.item_name(it["id"]), it["name"]), True, p.owner, 999, p.must | ({p.owner} if p.owner in om.actions else frozenset()),
                            p.rooms, p.pos, f"item {it['id']} in the bag", tk.item_name(it["id"]))
            self.intro_text(T.get(tk.item_look(it["id"]), it.get("look", "")), False, p.owner, 999, p.must, p.rooms, p.pos,
                            f"item look {it['id']}", tk.item_look(it["id"]))
        # -- action lines
        for a in g["actions"]:
            aid = a["id"]
            for n, line in enumerate(a.get("lines", [])):
                spk = line.get("speaker")
                if spk in SELF_SPEAKERS:
                    continue
                must = om.G[aid] | {aid}
                key = line.get("line_id")
                self.intro_text(T.get(key, line["text"]), True, aid, n, must, om.visited_of(must), om.pos[aid],
                                f"{spk} in {aid} (line {n + 1})", key)
                if spk in SPEAKER_ENTITY:
                    self.add_intro(person(SPEAKER_ENTITY[spk]), True, aid, n, frozenset(must), om.visited_of(must),
                                   om.pos[aid], f"{spk} speaks in {aid} (name above the subtitle)", key)
        # -- cutscenes (after the action that plays them)
        cut_owner = defaultdict(list)
        for a in g["actions"]:
            if a.get("cutscene"):
                cut_owner[a["cutscene"]].append(a["id"])
        self.cut_owner = cut_owner
        for cs in g["cutscenes"]:
            owners = cut_owner.get(cs["id"], [])
            must = self._cut_must(cs["id"])
            n = 0
            for beat in cs.get("beats", []):
                for line in beat.get("lines", []):
                    spk = line.get("speaker")
                    if spk not in SELF_SPEAKERS:
                        key = line.get("line_id")
                        self.intro_text(T.get(key, line["text"]), True, cs["id"], n, must, om.visited_of(must),
                                        om.pos_of_set(must) + 0.1, f"{spk} in cutscene {cs['id']}", key)
                        if spk in SPEAKER_ENTITY:
                            self.add_intro(person(SPEAKER_ENTITY[spk]), True, cs["id"], n, must, om.visited_of(must),
                                           om.pos_of_set(must) + 0.1, f"{spk} speaks in {cs['id']}", key)
                    n += 1
        # -- ambient topics: hard inside the topic, soft elsewhere
        for c in g["characters"]:
            for t in c.get("ambient_topics", []):
                must, rooms, pos, where = self.topic_info(c["id"], t)
                self._topic_must[t["id"]] = (must, rooms, pos, where)
                for n, line in enumerate(t.get("lines", [])):
                    spk = line.get("speaker")
                    if spk in SELF_SPEAKERS:
                        continue
                    key = line.get("line_id")
                    self.intro_text(T.get(key, line["text"]), False, t["id"], n, must, rooms, pos,
                                    f"{spk} in optional topic {t['id']}", key)
        # -- candidates
        self._candidates()

    def _set_wt(self, p: Point) -> None:
        own = {p.owner} if p.owner in self.om.actions else set()
        p.wt = self.om.wt_of(p.must | own, p.at_rooms)
        if p.owner == "epilogue":
            p.wt = 1000.0

    def _cut_must(self, cid: str) -> frozenset:
        owners = self.cut_owner.get(cid, [])
        acc = None
        for o in owners:
            s = self.om.G[o] | {o}
            acc = s if acc is None else acc & s
        return frozenset(acc or ())

    def quest_must(self, q: dict, started: bool) -> frozenset:
        """Actions surely done when a quest is shown in the journal / asked for a hint.

        Main quest: listed (and hinted) when it is Quests.NextMainQuest — in this game that is after every earlier main
        quest is complete (each main quest always has an available action until it is complete; --simulate checks
        it) and when one of its actions can be done. Side quest: listed only once started (an action done)."""
        om = self.om
        acc = None
        for aid in q.get("actions", []):
            s = (om.G[aid] | {aid}) if (started or q.get("type") != "main") else om.G[aid]
            acc = s if acc is None else acc & s
        acc = set(acc or ())
        if q.get("type") == "main":
            for prev in self.game["quests"]:
                if prev["id"] == q["id"]:
                    break
                if prev.get("type") == "main":
                    acc |= om.closure([prev["completion"]])
        return frozenset(acc)

    def _quest_hint_point(self, q: dict, n: int) -> Point | None:
        """When quest hint n can be shown (Core Hints.Direction, level 1), or None when never.

        Hint 1: while no action of the quest is done — only a main quest can be the hinted quest then (a side quest
        is hinted only once started). Hint 2: once the quest is started, only while none of its done actions has an
        objective (else the latest objective is the level-1 text). Hints 3+ are never shown (level 3 = step text)."""
        om = self.om
        if n == 1:
            return self._quest_point(q) if q.get("type") == "main" else None
        if n != 2:
            return None
        acts = set(q.get("actions", []))
        firsts = [a for a in acts if not (om.G[a] & acts)]
        silent = [a for a in firsts if not om.actions[a].get("objective")]
        if not silent:
            return None
        acc = None
        for a in silent:
            s = om.G[a] | {a}
            acc = s if acc is None else acc & s
        if q.get("type") == "main":
            acc = acc | self.quest_must(q, False)
        acc = frozenset(acc)
        return Point(acc, om.visited_of(acc), q["id"], 0, om.pos_of_set(acc) + 0.05, f"quest {q['id']} hint 2 (started, no objective yet)")

    def _quest_point(self, q: dict, started: bool = False) -> Point:
        om = self.om
        acc = self.quest_must(q, started)
        first = min(q["actions"], key=lambda x: om.pos[x])
        return Point(acc, om.visited_of(acc), q["id"], 0, om.pos_of_set(acc) + 0.05, f"quest {q['id']} {'started' if started else 'current'}")

    def _candidates(self) -> None:
        g, om, T = self.game, self.om, self.text
        rooms = {r["id"]: r for r in g["rooms"]}
        quests = {q["id"]: q for q in g["quests"]}
        puzzles_action = {a["puzzle"]: a["id"] for a in g["actions"] if a.get("puzzle")}
        line_pos: dict[str, tuple[str, int]] = {}
        for a in g["actions"]:
            for n, line in enumerate(a.get("lines", [])):
                line_pos[line.get("line_id")] = (a["id"], n)
        topic_line: dict[str, tuple[str, str, int]] = {}
        for c in g["characters"]:
            for t in c.get("ambient_topics", []):
                for n, line in enumerate(t.get("lines", [])):
                    topic_line[line.get("line_id")] = (c["id"], t["id"], n)
        cut_line: dict[str, tuple[str, int]] = {}
        for cs in g["cutscenes"]:
            n = 0
            for beat in cs.get("beats", []):
                for line in beat.get("lines", []):
                    cut_line[line.get("line_id")] = (cs["id"], n)
                    n += 1
        last_main = om.main_route[-1]
        end_must = om.G[last_main] | {last_main}

        for e in tk.iter_text_entries(g):
            fld = e.field
            if fld not in CANDIDATE_FIELDS:
                continue
            info = self.index.get(e.key)
            if info is None or info.never_shown:
                continue
            text = info.text
            spk = e.speaker
            if fld in LINE_FIELDS and spk not in SELF_SPEAKERS:
                continue   # someone else speaking: that is an introduction, not a candidate
            src = e.source
            p: Point | None = None
            m = re.match(r"^rooms\[([^\]]+)\]", src)
            if fld == "rooms[].first_entry[].text":
                p = self.room_point(m.group(1), idx=int(re.search(r"first_entry\[(\d+)\]", src).group(1)))
                p.where = f"first entry of {m.group(1)}"
            elif fld in ("rooms[].hotspots[].look", "rooms[].hotspots[].look_variants[].text"):
                rid = m.group(1)
                hid = re.search(r"hotspots\[([^\]]+)\]", src).group(1)
                h = om.hotspots[hid][1]
                extra = list(h.get("visible_after", []))
                if fld.endswith("text"):
                    vi = int(re.search(r"look_variants\[(\d+)\]", src).group(1))
                    extra.append(h["look_variants"][vi]["after"])
                p = self.room_point(rid, extra, owner="look:" + hid)
                p.where = f"look at {hid} in {rid}"
            elif fld in ("rooms[].exits[].locked_look", "rooms[].exits[].first_ride[].text"):
                rid = m.group(1)
                p = self.room_point(rid, owner="exit:" + rid)
                p.where = ("locked exit in " if "locked" in fld else "first ride from ") + rid
            elif fld == "connections[].locked_look":
                a_, b_ = re.search(r"connections\[([^\]]+)->([^\]]+)\]", src).groups()
                pa, pb = self.room_point(a_), self.room_point(b_)
                p = Point(pa.must & pb.must, pa.rooms & pb.rooms, "conn:" + a_, 0, min(pa.pos, pb.pos), f"locked map connection {a_}-{b_}",
                          at_rooms=(a_,) if om.vt[a_] <= om.vt[b_] else (b_,))
            elif fld in ("items[].look", "items[].purpose"):
                iid = re.search(r"items\[([^\]]+)\]", src).group(1)
                p = self.item_point(iid)
                if p is not None:
                    p = Point(p.must | ({p.owner} if p.owner in om.actions else frozenset()), p.rooms, p.owner, 1000, p.pos, p.where)
            elif fld.startswith("actions[]"):
                aid = re.search(r"actions\[([^\]]+)\]", src).group(1)
                if fld == "actions[].label":
                    p = self.action_point(aid, -1)
                elif fld == "actions[].lines[].text":
                    p = self.action_point(aid, line_pos[e.key][1])
                elif fld in ("actions[].objective", "actions[].journal_text"):
                    p = self.action_point(aid, 999)
                elif fld == "actions[].hint_step":
                    p = self.action_point(aid, -1)
                    p.where = f"step hint of {aid}"
            elif fld.startswith("characters[].ambient_topics[]"):
                cid, tid = re.search(r"characters\[([^\]]+)\]\.ambient_topics\[([^\]]+)\]", src).groups()
                must, rms, pos, where = self._topic_must[tid]
                idx = -1 if fld.endswith(".label") else topic_line[e.key][2]
                p = Point(must, rms, tid, idx, pos, f"topic {tid} ({where})", at_rooms=tuple(x for x in where.split(",") if x))
            elif fld == "cutscenes[].beats[].lines[].text":
                cid, n = cut_line[e.key]
                must = self._cut_must(cid)
                p = Point(must, om.visited_of(must), cid, n, om.pos_of_set(must) + 0.1, f"cutscene {cid}")
            elif fld.startswith("quests[]"):
                qid = re.search(r"quests\[([^\]]+)\]", src).group(1)
                q = quests[qid]
                if fld == "quests[].hints[]":
                    n = int(e.key.rsplit(".", 1)[1])
                    p = self._quest_hint_point(q, n)
                    if p is None:
                        continue
                else:
                    p = self._quest_point(q)
                if fld == "quests[].reward":
                    comp = quests[qid]["completion"]
                    must = om.G[comp] | {comp}
                    p = Point(must, om.visited_of(must), comp, 1000, om.pos[comp] + 0.06, f"reward of {qid}")
            elif fld.startswith("puzzles[]") or fld == "journal_contract.clues[]":
                pid = (re.search(r"puzzles\[([^\]]+)\]", src).group(1) if fld.startswith("puzzles")
                       else e.key.rsplit(".", 1)[1])
                aid = puzzles_action.get(pid)
                if aid:
                    p = self.action_point(aid, 998 if fld == "puzzles[].success_line" else -1)
                    p.where = f"puzzle {pid} ({aid})"
            elif fld.startswith("epilogue[]"):
                n = int(e.key.split(".")[1])
                ep = g["epilogue"][n - 1]
                must = end_must | (om.closure([ep["after"]]) if ep.get("after") else frozenset())
                p = Point(frozenset(must), om.visited_of(must), "epilogue", n, 999.0, "epilogue / credits")
            if p is None:
                continue
            found = mentions(text)
            if not found:
                continue
            self._set_wt(p)
            self.cands.append(Candidate(e.key, info.kind, era_name(info.era), text, spk, p, found))
        # ui.hint_step.<action> (ui.csv, level 3 hints) and other ui strings with names
        for key, info in self.index.items():
            if info.table != tk.TABLE_UI:
                continue
            m = re.match(r"^ui\.hint_step\.(\w+)$", key)
            if m and m.group(1) in om.actions:
                aid = m.group(1)
                p = self.action_point(aid, -1)
                p.where = f"step hint (level 3) of {aid}"
                found = mentions(info.text)
                self._set_wt(p)
                if found:
                    era = era_name(self.model.room_era(self.model.action_room.get(aid)))
                    self.cands.append(Candidate(key, "hint", era, info.text, None, p, found))

    # ---- status of one mention
    def status(self, c: Candidate, ent: str) -> tuple[str, Intro | None, Intro | None]:
        e = ENTITY_BY_ID[ent]
        p = c.point
        best_order: Intro | None = None
        best_soft: Intro | None = None
        for it in self.intros.get(ent, []):
            same = it.owner == p.owner
            if same and it.idx < p.idx:
                return "introduced", it, None   # earlier in the same exchange (action, topic, cutscene, item)
            guaranteed = it.must <= p.must and it.req_rooms <= p.rooms
            if it.hard and guaranteed:
                return "introduced", it, None
            earlier = it.wt < p.wt
            if it.hard and earlier and (best_order is None or it.wt < best_order.wt):
                best_order = it
            if not it.hard and (guaranteed or earlier) and (best_soft is None or it.wt < best_soft.wt):
                best_soft = it
        first_any = min((i for i in self.intros.get(ent, []) if i.hard), key=lambda i: (i.wt, i.pos), default=None)
        if e.background:
            return "background", None, first_any
        if best_order:
            return "order", best_order, first_any
        if best_soft:
            return "soft", best_soft, first_any
        return "none", None, first_any


# --------------------------------------------------------------------------- report

def story(wt: float):
    """Story step of the walkthrough (1..94; .5 = while travelling to it), or 'off-route' when the walkthrough never shows it."""
    if wt == float("inf"):
        return "off-route"
    return round(wt, 2)


def load_judgements() -> dict:
    if JUDGEMENTS.exists():
        return json.loads(JUDGEMENTS.read_text(encoding="utf-8"))
    return {"about": "", "entries": {}}


def jkey(key: str, ent: str) -> str:
    return f"{key}|{ent}"


def run(args) -> int:
    audit = Audit()
    om = audit.om
    sim_problems: list[str] = []
    if args.simulate:
        qm = {q["id"]: audit.quest_must(q, False) for q in audit.game["quests"] if q.get("type") == "main"}
        sim_problems = om.simulate(args.simulate, quest_must=qm)
        ln = om.sim_lengths
        print(f"simulation: {args.simulate} random legal orders ({min(ln)}-{max(ln)} of {len(om.ids)} actions each), "
              f"{len(sim_problems)} must-set violations")
        for s in sim_problems[:10]:
            print("  " + s)
    J = load_judgements()
    entries = J.get("entries", {})
    rows = []
    for c in audit.cands:
        for ent, matched in c.mentions:
            st, intro, first = audit.status(c, ent)
            if ent == "person:Adam":
                continue
            row = {
                "key": c.key, "era": c.era, "kind": c.kind, "speaker": c.speaker, "text": c.text,
                "entity": ent, "matched": matched, "auto_status": st, "where": c.point.where,
                "walkthrough_pos": round(c.point.pos + 1, 2),
                "story_step": story(c.point.wt),
                "intro_before": (intro.what + (f" [{intro.key}]" if intro.key else "") + f" (story step {story(intro.wt)})") if intro else None,
                "first_introduction": (first.what + (f" [{first.key}]" if first.key else "") + f" (story step {story(first.wt)}, earliest possible {round(first.pos + 1, 2)})") if first else None,
            }
            j = entries.get(jkey(c.key, ent))
            if j:
                row["verdict"] = j.get("verdict")
                row.update({k: v for k, v in j.items() if k != "verdict"})
            else:
                row["verdict"] = {"introduced": "fine", "background": "acceptable"}.get(st)
            rows.append(row)
    rows.sort(key=lambda r: (r["story_step"] if isinstance(r["story_step"], (int, float)) else 10000, r["walkthrough_pos"], r["key"]))
    if args.key:
        rows_show = [r for r in rows if r["key"] == args.key]
    elif args.entity:
        rows_show = [r for r in rows if r["entity"] == args.entity]
    elif args.list:
        rows_show = [r for r in rows if r["auto_status"] in args.list.split(",")]
    elif args.unjudged:
        rows_show = [r for r in rows if not r.get("verdict")]
    else:
        rows_show = []
    for r in rows_show:
        print(f"{str(r['story_step']):>6} {r['walkthrough_pos']:6.2f} {r['era']} {r['auto_status']:10} {r.get('verdict') or '-':10} {r['key']} | {r['entity']} ({r['matched']})")
        print(f"         {r['text']}")
        print(f"         at: {r['where']}; before: {r['intro_before']}; first intro: {r['first_introduction']}")
    stale = [k for k in entries if not any(jkey(r["key"], r["entity"]) == k for r in rows)]
    counts = Counter((r["era"], r.get("verdict") or "unjudged") for r in rows)
    auto = Counter(r["auto_status"] for r in rows)
    print("auto status:", dict(auto))
    print("verdicts:", dict(sorted(counts.items())))
    if stale:
        print(f"{len(stale)} judgement(s) match no current candidate: " + ", ".join(stale[:8]))
    if args.write:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        out = {
            "about": "Knowledge-state audit (tools/knowledge_audit.py). One row per (text key, entity) mention in a "
                     "player-visible text that is not someone else speaking. auto_status from the must-analysis over "
                     "all legal orders; verdict by Claude (docs/writing/knowledge/judgements.json): problem / "
                     "acceptable / fine.",
            "simulation": {"orders": args.simulate, "must_set_violations": len(sim_problems)},
            "counts_by_era": {era: {v: n for (e2, v), n in counts.items() if e2 == era} for era in sorted({r['era'] for r in rows})},
            "problems": [r for r in rows if r.get("verdict") == "problem"],
            "rows": rows,
        }
        (OUT_DIR / "audit.json").write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print("wrote", (OUT_DIR / "audit.json").relative_to(tk.REPO_ROOT))
    if args.write_md:
        ln = getattr(om, "sim_lengths", [])
        write_md(rows, J, sim_problems, args.simulate,
                 f"(each order plays {min(ln)}–{max(ln)} of {len(om.ids)} actions)" if ln else "")
    if args.unjudged and any(not r.get("verdict") for r in rows):
        return 1
    if args.strict and sim_problems:
        return 1
    return 0


FIX_TYPES = {
    "a": "add a source line earlier (someone tells Adam)",
    "b": "turn Adam's line into a question / observation; name it only after the introduction",
    "c": "adjust the look / journal / goal / hint text",
}


def write_md(rows: list[dict], J: dict, sim_problems: list[str], sim_n: int, sim_len: str = "") -> None:
    probs = [r for r in rows if r.get("verdict") == "problem"]
    sev_rank = {"high": 0, "medium": 1, "low": 2}
    groups: dict[str, list[dict]] = defaultdict(list)
    for r in probs:
        groups[r.get("group") or r["key"]].append(r)
    order = sorted(groups, key=lambda g: (0 if groups[g][0].get("owner_example") else 1,
                                          sev_rank.get(groups[g][0].get("severity", "medium"), 1),
                                          min(_num(r["story_step"]) for r in groups[g])))
    eras = ["2020", "1995", "1962", "1982", "2035", "general"]
    lines = [
        "# Knowledge audit: Adam never knows what he has not learned",
        "",
        "Owner rule 2026-10-06 (docs/DECISIONS.md \"Adam never knows what he has not learned\"): every person, place,",
        "item, organisation or fact that Adam names — and every look, journal entry, objective, goal or hint in his",
        "voice — must have been introduced to the player earlier **in every legal order of play**.",
        "",
        "Generated by `python tools/knowledge_audit.py --simulate 200 --write --write-md` from the live texts",
        "(game.json + `sk_overrides.csv` + the content overlays) and Claude's verdicts in",
        "[judgements.json](judgements.json); machine-readable result: [audit.json](audit.json). **Nothing here is",
        "applied to the game.** The Slovak wording under *Fix* is a proposal for the writer: the new and changed texts",
        "go through the writing method (design-doc/WRITING_METHOD.md, drafts in `docs/writing/out_v3/`) and live only",
        "after the owner approves them.",
        "",
        "## How it was checked",
        "",
        "- **Texts checked:** every player-visible text that is not someone else speaking — Adam's lines in actions,",
        "  topics, cutscenes and puzzles, first-entry and first-ride lines, looks and look variants, item looks and",
        "  purposes, locked-exit looks, objectives, journal entries, quest titles / goals / rewards, the quest hints",
        "  the engine can show (hint 1 while a main quest has no done action, hint 2 while a started quest has no",
        "  objective yet; hint 3 is never shown), step hints, dialogue choices and topic labels, puzzle and journal",
        "  clues, epilogue captions.",
        "- **Entities:** people with nicknames, surnames and roles (*rádioamatér* = Dezider, *archivár* = Karol),",
        "  places, rooms and districts, organisations (*kazetový klub*, *Atlas*, *Druhý život*), story items and",
        "  devices, codes and facts (K-17, Z-17, 3–2–6, rad 2 / stĺpec 3, the password, ROZDIEL = ZAHODIŤ, 38 rokov).",
        "- **Introductions:** a line by someone else (incl. phone, recordings, device text), the speaker's name above",
        "  the subtitle, the name and district of a visited room, the hover / Space labels of a visited room (NPCs",
        "  show their full name), exit and map labels seen there, an item in the bag. Adam's looks and optional",
        "  ambient topics are *soft*: the player may never see them, so they do not count.",
        "- **Legal orders:** a must-analysis over the real step model (requires_done, the givers of every needed",
        "  item, gated connections, chronometer portals, special transitions, visible_after, NextMainQuest) gives for",
        "  every text the actions that are done before it in **every** legal order and the rooms surely visited. An",
        "  introduction counts only inside that set or earlier in the same exchange. Story order = the 94-step",
        "  walkthrough (`story step`); side content is checked both early and late.",
        f"- **Cross-check:** {sim_n} seeded random legal orders with ContentPlayability's step model {sim_len}: "
        f"{len(sim_problems)} violations of the must-sets.",
        "- **Judgement (Claude):** *problem* = Adam / a look / the journal anticipates something; *acceptable* = Adam's",
        "  own background (Mira = babka; his school ZŠ Sokolíkova and its caretaker; Chorvátsky Grob, Čierna Voda,",
        "  Dúbravka and their neighbours; the real districts and places of Bratislava, Ivanka and Jasná every adult",
        "  knows; general knowledge of the era and of his trade), what the device or a visible sign shows, or the thing",
        "  he is looking at; *fine* = introduced before in every legal order.",
        "",
        "Fix types: **(a)** add a source line to whoever would plausibly tell Adam earlier; **(b)** turn Adam's line into",
        "a question / observation and move the name after the introduction; **(c)** adjust a look / journal / goal /",
        "hint text.",
        "",
        "## Counts by era",
        "",
        "One row = one (text key, entity) mention. *Root fixes* = the numbered sections below (one fix resolves all its",
        "rows). *Acceptable* = judged one by one + automatic background entities. *General* = cutscenes, epilogue,",
        "journal clues.",
        "",
        "| era | problems (rows) | root fixes | acceptable (judged + background) | fine (introduced) |",
        "|---|---|---|---|---|",
    ]
    for e in eras:
        er = [r for r in rows if r["era"] == e]
        if not er:
            continue
        c = Counter(r.get("verdict") for r in er)
        nb = sum(1 for r in er if r.get("verdict") == "acceptable" and r["auto_status"] == "background")
        gs = {r.get("group") for r in er if r.get("verdict") == "problem"}
        lines.append(f"| {e} | {c.get('problem', 0)} | {len(gs)} | {c.get('acceptable', 0)} "
                     f"({c.get('acceptable', 0) - nb} + {nb}) | {c.get('fine', 0)} |")
    tot = Counter(r.get("verdict") for r in rows)
    nb = sum(1 for r in rows if r.get("verdict") == "acceptable" and r["auto_status"] == "background")
    lines.append(f"| **all** | **{tot.get('problem', 0)}** | **{len(groups)}** | **{tot.get('acceptable', 0)} "
                 f"({tot.get('acceptable', 0) - nb} + {nb})** | **{tot.get('fine', 0)}** |")
    lines += ["", "A root fix that touches several eras is counted in each of them.", "",
              "## Problems (owner's example first, then by severity and story order)", ""]
    for n, g in enumerate(order, 1):
        rs = sorted(groups[g], key=lambda r: (_num(r["story_step"]), r["key"]))
        h = rs[0]
        eras_g = ", ".join(sorted({r["era"] for r in rs}, key=lambda x: eras.index(x) if x in eras else 9))
        ents = ", ".join(sorted({r["entity"].split(":", 1)[1] for r in rs}))
        title = f"### {n}. {ents} — {g}" + (" (owner's example)" if h.get("owner_example") else "")
        lines += [title, "",
                  f"Era {eras_g} · severity **{h.get('severity', 'medium')}** · fix type **{h.get('fix_type', '')}**", "",
                  f"- **Why:** {h.get('why', '')}",
                  f"- **Earliest introduction found:** {h.get('earliest_intro') or 'none'}",
                  f"- **Fix:** {h.get('fix', '')}", "",
                  "| key | entity | story step | text |", "|---|---|---|---|"]
        for r in rs:
            txt = r["text"].replace("|", "\\|")
            lines.append(f"| `{r['key']}` | {r['entity'].split(':', 1)[1]} | {r['story_step']} | {txt} |")
        lines.append("")
    acc = [r for r in rows if r.get("verdict") == "acceptable" and r["auto_status"] != "background"]
    if acc:
        lines += ["## Acceptable without an introduction (judged one by one)", "",
                  "| key | entity | auto status | reason |", "|---|---|---|---|"]
        for r in sorted(acc, key=lambda r: (_num(r["story_step"]), r["key"])):
            lines.append(f"| `{r['key']}` | {r['entity'].split(':', 1)[1]} | {r['auto_status']} | {r.get('reason', '')} |")
        lines.append("")
    bg = Counter(r["entity"].split(":", 1)[1] for r in rows if r["auto_status"] == "background")
    lines += ["## Background entities (acceptable automatically)", "",
              "Mentions of entities from Adam's own background that had no earlier introduction (counted, not listed): "
              + ", ".join(f"{k} ×{v}" for k, v in bg.most_common()) + ".", "",
              "## Limits", "",
              "- The audit is entity-based: it catches names, places, items, organisations and fixed facts, not every",
              "  sentence in which Adam infers a plan; every flagged text was read and judged by Claude.",
              "- Hover / Space labels and exit labels count as introductions (the owner's rule: \"told or shown\").",
              "- Main quests are assumed to become current in data order; `--simulate` checks this on every random order.",
              "- Re-run after every text change: `python tools/knowledge_audit.py --unjudged` lists new candidates.",
              ""]
    (OUT_DIR / "AUDIT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote", (OUT_DIR / "AUDIT.md").relative_to(tk.REPO_ROOT))


def _num(v) -> float:
    return v if isinstance(v, (int, float)) else 10000.0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--simulate", type=int, default=0, help="cross-check the must-sets on N random legal orders")
    ap.add_argument("--write", action="store_true", help="write docs/writing/knowledge/audit.json")
    ap.add_argument("--write-md", action="store_true", help="write docs/writing/knowledge/AUDIT.md")
    ap.add_argument("--list", help="print candidates with these auto statuses (comma list)")
    ap.add_argument("--key", help="print the rows of one text key")
    ap.add_argument("--entity", help="print the rows of one entity id (e.g. person:Juro)")
    ap.add_argument("--unjudged", action="store_true", help="print candidates without a verdict; exit 1 if any")
    ap.add_argument("--strict", action="store_true", help="exit 1 on a simulation mismatch")
    args = ap.parse_args()
    try:
        return run(args)
    except (OSError, ValueError, KeyError) as exc:
        print(f"error: {exc!r}", file=sys.stderr)
        raise


if __name__ == "__main__":
    sys.exit(main())
