"""Ask external LLMs (via fal.ai's OpenRouter proxy) to write the prologue sample in three tones.

Usage: python tools/llm_tone_trial.py openai/gpt-6-astra-pro openai/gpt-6.1-sol-pro
Writes docs/writing/llm_trials/<model>.md and logs the cost to art/spend-log.csv.
"""
import csv
import datetime
import os
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "writing" / "llm_trials"
LOG = ROOT / "art" / "spend-log.csv"
URL = "https://fal.run/openrouter/router/openai/v1/chat/completions"

# USD per million tokens (input, output), from openrouter.ai/api/v1/models on 2026-10-05.
PRICES = {"openai/gpt-6-astra-pro": (10.0, 50.0), "openai/gpt-6-astra": (10.0, 50.0),
          "openai/gpt-6.1-sol-pro": (2.0, 10.0), "openai/gpt-6.1-sol": (2.0, 10.0)}

SYSTEM = """You are a top Slovak screenwriter and game writer (native Slovak, Bratislava). You write dialogue
for a hand-painted point-and-click adventure game in the spirit of classic Czech/Slovak adventures.
You write natural, contemporary spoken Slovak: correct grammar and declension, no calques from English,
no officialese, no forced wit. Every line must be something a real person would actually say in that
situation. Output only what is asked."""

BRIEF = """GAME: "Posledný zvonec". Hero: Adam Hruška, 35, a repairman of old audio electronics, lives in Čierna
Voda (part of Chorvátsky Grob near Bratislava). Date: 29 October 2020, autumn afternoon, covid lockdown.
His grandmother Mira (in 2020 an old lady) is in quarantine at home; he helps her with shopping.
Other people here: Ela (volunteer who runs the neighbourhood food-distribution point under an outdoor
shelter), Dana (shop assistant selling through a small window of the grocery), Roman (courier).
Everyone says "ty" to Adam. Mira is his grandma and says "ty"; he calls her "babka".

FACTS THAT MUST STAY (the game logic depends on them):
- In the garage Adam takes his service bag: screwdriver, pliers, a meter (skrutkovač, kliešte, meradlo).
- Ela gives him the order slip (lístok) and a spare face mask; the shopping is ready at Dana's; he must leave the
  bag OUTSIDE for grandma (on the little table in front of the gate) and phone her.
- Dana: the bag contains tea, oat flakes, potatoes (čaj, vločky, zemiaky); it is already paid, Ela arranged it.
- Grandma's rule: carry the bag by both handles.
- Mira: go along the side path to the window and call her (through the glass she cannot hear him).
- Mira: Roman carried her old boxes into the garden workshop; inside is a small device called ZVON; it makes
  sounds although it is unplugged. The key is in the outside box by the window; take it, but do not go into the house.
- Adam asks why it is called ZVON; Mira: because it sounded ("ozval sa") right at the start, and they had no better name.
- The key fits the workshop door.
- Looks: an old radio on the bench (gets one station, with noise); yellow-and-black tape on the ground marking
  the queue distance; Ela's thermos with a strip of tape that says NEDOLIEVAŤ POLIEVKU (do not pour soup in); Ela
  herself; a VITAJTE doormat turned to face the door.

THE LINES (keep the same number, order and speakers; one line each; subtitles, max ~110 characters):
 1 ADAM (enters his garage, the radio he is repairing is on the bench)
 2 ADAM (greets Ela at the distribution point: grandma said there is an order for her)
 3 ELA  (Dana has it ready; here is the slip and a spare mask; leave the bag outside for grandma and call her)
 4 ADAM (reacts: he knows, grandma told him)
 5 ELA  (replies)
 6 ADAM (greets Dana at the shop window, he brings grandma's slip)
 7 DANA (tea, oat flakes, potatoes; already paid, Ela arranged it)
 8 ADAM (he will carry it by both handles, grandma's rule)
 9 DANA (replies)
10 ADAM (at the gate: tells grandma the shopping is on the little table, he steps back)
11 MIRA (thanks him; go along the side path to the window and call me, I would not hear you through the glass)
12 ADAM (agrees)
13 MIRA (Roman carried the boxes into the garden workshop; there is a small device in them, ZVON; it sounds although unplugged)
14 ADAM (short guess what it is, as a repairman)
15 MIRA (the key is in the outside box by the window; take it, but don't come into the house)
16 ADAM (asks why it is called ZVON)
17 MIRA (because it sounded right at the start, and they had no better name back then)
18 ADAM (unlocks the workshop: the key fits)
19 LOOK the old radio
20 LOOK the tape on the ground
21 LOOK Ela's thermos
22 LOOK Ela
23 LOOK the doormat
24 ADAM (asks Ela how many people need help today)
25 ELA  (more than yesterday, but more helpers too)
26 ADAM (reacts)
27 ADAM (asks Roman the courier: many addresses today?)
28 ROMAN (two people described their address to him as "the house that used to be yellow")
29 ADAM (reacts)

CURRENT TEXT (the owner finds it cringy: almost every exchange ends with a forced punchline):
 1 Moja garáž. Keď človek pracuje z domu, pokazené veci si myslia, že má otvorené nonstop.
 4 Viem. Babka mi to povedala skôr ako ty. Dvakrát.   5 Tak to máš potvrdené z dvoch zdrojov.
 8 Ponesiem to za obe uchá. Babkino pravidlo.   9 Vidíš, ty to vieš.
12 Dobre. Dva metre a telefón. Bližšie sme sa celý mesiac nerozprávali.
18 Kľúč pasuje. Aspoň niečo dnes funguje na prvý pokus.
20 Páska na zemi ukazuje odstup. Funguje aj bez aplikácie.
23 Rohožka VITAJTE je otočená k dverám, akoby vítala ľudí von. V roku 2020 to sedí.
26 Tak aspoň jedna krivka ide dobrým smerom.
29 Navigácia s historickou vrstvou. Poznám.

TASK: write ALL 29 lines three times, in three tones:
A) NATURAL, ALMOST NO JOKES: people talk like real people from Čierna Voda; short, warm, ordinary; at most
   one gentle smile in the whole sample, arising from the situation.
B) LIGHT HUMOUR, ONLY SOMETIMES: natural speech with an occasional dry smile, at most one per scene; never a
   wisecrack after every line; no ironic commentary on covid.
C) BOLDER, LIVELIER HUMOUR in the spirit of the Czech "Polda" adventure games: playful, a bit absurd, real
   jokes and character comedy (not ironic summaries), but still natural Slovak and still keeping every fact.

FORMAT: for each tone a heading "## A", "## B", "## C", then 29 numbered lines "N. SPEAKER: text"
(LOOK lines as "N. POZRI: text"). Nothing else."""


def fal_key():
    key = os.environ.get("FAL_KEY")
    if not key and sys.platform == "win32":
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as k:
            key, _ = winreg.QueryValueEx(k, "FAL_KEY")
    return key


def run(model, key):
    r = requests.post(URL, headers={"Authorization": f"Key {key}", "Content-Type": "application/json"},
                      json={"model": model, "temperature": 0.8, "max_tokens": 6000,
                            "messages": [{"role": "system", "content": SYSTEM},
                                         {"role": "user", "content": BRIEF}]}, timeout=600)
    r.raise_for_status()
    data = r.json()
    text = data["choices"][0]["message"]["content"]
    usage = data.get("usage", {})
    pin, pout = PRICES.get(model, (10.0, 50.0))
    cost = usage.get("prompt_tokens", 0) / 1e6 * pin + usage.get("completion_tokens", 0) / 1e6 * pout
    return text, usage, round(cost, 4)


def main(models):
    OUT.mkdir(parents=True, exist_ok=True)
    key = fal_key()
    for model in models:
        text, usage, cost = run(model, key)
        name = model.replace("/", "_")
        (OUT / f"{name}.md").write_text(f"# {model}\n\nusage: {usage}, approx USD {cost}\n\n{text}\n", encoding="utf-8")
        with LOG.open("a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow([datetime.datetime.now().isoformat(timespec="seconds"), model,
                                    "writing/tone_trial_prologue", cost])
        print(f"{model}: {usage} -> USD {cost} -> docs/writing/llm_trials/{name}.md")


if __name__ == "__main__":
    main(sys.argv[1:] or ["openai/gpt-6-astra-pro", "openai/gpt-6.1-sol-pro"])
