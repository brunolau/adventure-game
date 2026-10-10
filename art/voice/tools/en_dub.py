"""English dubbing (2026-10-10, owner: "now make english dubbing").

Every key that has a Slovak recording gets an English one: the 2,217 dialogue lines and the 567 look keys of
art/voice/full/manifest.json and the Standard/Hard variants of art/voice/full/std_manifest.json. The text is the `en`
column of the live tables (src/game/localization/{dialogue,world,ui}.csv). Each speaker keeps the stock voice, the
character direction, the dry-irony marking and the call / tape / device colour of the Slovak dub; only the language
sentence of the direction changes (EN below), and a line with a Slovak name in it gets a pronunciation hint.

Same method as the Slovak dub (gen_full.py): Gemini 3.8 Flash TTS, one ElevenLabs Scribe v2 check per take, exactly
one retake when the transcript differs in meaning, the rest is flagged for the ear. Post-processing is gen_full.finish
(trim, colour, -16 LUFS, fades, OGG Vorbis q4 mono).

Files: raw takes and per-line records in art/voice/raw/en/ (git-ignored), finished OGGs in art/voice/takes/en/
(git-ignored), the manifest in art/voice/en/manifest.json, the game copy in src/game/assets/voice_en/ (with its own
aliases.json: keys that share one recording).

usage:
  python en_dub.py plan                                   counts, characters, estimated cost
  python en_dub.py gen [--workers N] [--only ID ...] [--limit N] [--sample]
  python en_dub.py report [--all]
  python en_dub.py retake [--all-flagged | ID ...]        one retake per line (never a second one)
  python en_dub.py recheck                                run the free text check again on every stored take
  python en_dub.py rerender                               post-process every best take again (free)
  python en_dub.py finalize                               art/voice/en/manifest.json
  python en_dub.py install                                copy the OGGs + aliases.json into src/game/assets/voice_en/
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import voice_lib as V  # noqa: E402
import gen_full as G  # noqa: E402  (finish / colour: the same post-processing as the Slovak dub)
from casting import IRONY as IRONY_DIRECTION, SK  # noqa: E402
from casting_full import CAST  # noqa: E402

MODEL = "google/gemini-3.8-flash-tts"
ASSET = "voice/en/"
BUDGET = (ASSET, 16.0)                      # cap of the English dub (USD); the Slovak dub cost about 13
FULL = V.ROOT / "art/voice/full"            # the Slovak manifests: which keys are spoken, by whom, with which colour
OUT = V.ROOT / "art/voice/en"               # manifest (tracked)
TAKES = V.ROOT / "art/voice/takes/en"       # finished OGGs (git-ignored; the game folder is the tracked copy)
RAW = V.ROOT / "art/voice/raw/en"
GAME = V.ROOT / "src/game/assets/voice_en"
LOCALIZATION = V.ROOT / "src/game/localization"

# The language sentence of every direction (the Slovak dub's is casting.SK). The texts are British English
# (docs/translation/README.md), so the voices are too.
EN = ("Speak natural, native British English with a neutral, contemporary accent (standard southern British, "
      "neither posh nor regional); no foreign accent. Read the text verbatim. ")
VERBATIM = " Say every word exactly as written; do not add, drop or change any word."
CLEAR = " Pronounce every word fully and clearly, unhurried."

# Spoken forms the TTS needs (the subtitle text stays unchanged); the check accepts either form.
SPOKEN = {
    "Z-17": "Zed-seventeen",
    "K-17": "K-seventeen",
    "3–2–6": "three, two, six",
    "0–9": "zero to nine",
    "9–17": "nine to five",
    "3 × 4": "three by four",
    " = ": " equals ",
    "‘": "",
}

# Slovak names left in the English texts (docs/translation/README.md: real places keep their names without
# diacritics). The voice is told how to say the ones in its line. Longer names first.
HINTS = [
    ("Ivanka pri Dunaji", "EE-vahn-kah pri DOO-nah-yee"),
    ("Karlova Ves", "KAR-lo-vah VES"),
    ("Cierna Voda", "CHYER-nah VOH-dah"),
    ("Biela Put", "BYEH-lah POOT"),
    ("Druhý život", "DROO-hee ZHEE-vot"),
    ("Ivanka", "EE-vahn-kah"),
    ("Dubravka", "DOO-brahf-kah"),
    ("Chopok", "KHOH-pok, the „ch“ as in Scottish „loch“"),
    ("Funitel", "FOO-nee-tel"),
    ("Priehyba", "PREE-eh-hee-bah"),
    ("Jasna", "YAHS-nah"),
    ("Sokolikova", "SOH-ko-lee-ko-vah"),
    ("Svantnerova", "SHVANT-neh-ro-vah"),
    ("Petrzalka", "PET-er-zhal-kah"),
    ("Ruzinov", "ROO-zhi-nof"),
    ("Vrbicke", "VER-bits-keh"),
    ("Mileticka", "MEE-leh-tich-kah"),
    ("Kamenne", "KAH-men-neh"),
    ("Grob", "grob, rhymes with „rob“"),
    ("lángos", "LAHN-gosh"),
    ("LEAL", "LEH-al, two syllables, said as a word and never spelled"),
    ("ZVON", "zvon, one syllable that rhymes with „on“, said as a word and never spelled"),
]
FOREIGN = {w.lower() for name, _ in HINTS for w in V.strip_diacritics(name).split()} - {"pri"}


def hint(text: str) -> str:
    rest, found = text, []
    for name, say in HINTS:
        pattern = re.compile(r"(?<!\w)" + re.escape(name) + r"(?!\w)", re.IGNORECASE)
        if pattern.search(rest):
            found.append(f"„{name}“ = {say}")
            rest = pattern.sub(" ", rest)
    if not found:
        return ""
    return (" Slovak names in this line are said the Slovak way, with the stress on the first syllable: "
            + "; ".join(found) + ".")


def spoken(text: str) -> str:
    t = text
    for a, b in SPOKEN.items():
        t = t.replace(a, b)
    t = re.sub(r"(?<![A-Za-z])’|’(?![A-Za-z])", "", t)          # a closing quote; an apostrophe inside a word stays
    return V.tts_text(t)


def text_hash(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]


# --------------------------------------------------------------------------- script

def english() -> dict[str, tuple[str, str]]:
    """key -> (Slovak, English) of the live tables."""
    rows = {}
    for name in ("dialogue", "world", "ui"):
        with (LOCALIZATION / f"{name}.csv").open(encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                rows[row["keys"]] = (row["sk"], row["en"])
    return rows


def jobs() -> list[dict]:
    """One job per spoken key, in the order of the Slovak manifest (dialogue, looks, Standard/Hard variants)."""
    man = json.loads((FULL / "manifest.json").read_text(encoding="utf-8"))
    std = json.loads((FULL / "std_manifest.json").read_text(encoding="utf-8"))
    rows = english()
    base = {r["line_id"]: r for r in man["looks"]}
    base.update({r["line_id"]: r for r in man["lines"]})
    out = []

    def add(key: str, rec: dict, group: str) -> None:
        sk, en = rows[key]
        if not en.strip():
            raise SystemExit(f"no English text for {key}")
        out.append({"line_id": key, "group": group, "speaker": rec["speaker"], "text": en, "sk": sk,
                    "fx": rec.get("fx"), "irony": bool(rec.get("delivery")), "era": rec.get("era"),
                    "scene": rec.get("scene"), "kind": rec.get("kind")})
    for r in man["lines"]:
        add(r["line_id"], r, "dialogue")
    for r in man["looks"]:
        add(r["line_id"], r, "looks")
    for r in std:
        add(r["key"], base[r["key"][: -len(".std")]], "std")
    return out


def aliases(all_jobs: list[dict]) -> dict[str, str]:
    """Same speaker, same English text, same colour: one take (key -> the key that owns the recording)."""
    first, out = {}, {}
    for j in all_jobs:
        k = (j["speaker"], j["text"], j["fx"])
        if k in first:
            out[j["line_id"]] = first[k]
        else:
            first[k] = j["line_id"]
    return out


def voice_for(job: dict) -> dict:
    c = CAST[job["speaker"]]
    if not c["style"].startswith(SK):
        raise SystemExit(f"direction of {job['speaker']} does not start with the Slovak language sentence")
    style = EN + c["style"][len(SK):]
    if job["irony"]:
        style += IRONY_DIRECTION
    return {"voice": c["voice"], "style": style + hint(job["text"])}


# --------------------------------------------------------------------------- check

WORDS = {"mister": "mr", "missus": "mrs", "misses": "mrs", "doctor": "dr", "okay": "ok", "percent": "%",
         "grey": "gray", "nought": "zero", "oh": "o", "till": "to", "until": "to", "zed": "z", "zee": "z",
         "kerb": "curb", "kerbs": "curbs", "tyre": "tire", "tyres": "tires", "storey": "story", "cheque": "check",
         "plough": "plow", "draught": "draft", "pyjamas": "pajamas", "sceptical": "skeptical", "cosy": "cozy",
         "aluminium": "aluminum", "moustache": "mustache", "round": "around", "towards": "toward", "whilst": "while",
         "amongst": "among", "mum": "mom", "mums": "moms", "maths": "math", "grant": "gran", "grants": "grans"}
NUMBER_WORD = re.compile(r"^(zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|(thir|four|fif|six|seven|"
                         r"eigh|nine)teen|(twen|thir|for|fif|six|seven|eigh|nine)ty|hundred|thousand|first|second|third|"
                         r"fourth|fifth|sixth|seventh|eighth|ninth|tenth|eleventh|twelfth|\w+teenth|\w+tieth)s?$")
FILLERS = {"oh", "o", "ah", "um", "uh", "hm", "hmm", "mm", "well", "so", "and", "er", "eh", "huh", "now", "yes", "no"}
# Spoken short forms a voice in character may use and the STT may write ("them" / "'em"): the same words.
COLLOQUIAL = {"gonna": "going to", "wanna": "want to", "gotta": "got to", "outta": "out of", "outa": "out of",
              "'em": "them", "em": "them", "kinda": "kind of", "dunno": "do not know", "'cause": "because",
              "cos": "because", "yeah": "yes", "ya": "you", "grant": "gran"}
# Words that sound alike: the STT picks one spelling, the voice said the same sound either way. Applied to both sides.
HOMOPHONES = [g.split() for g in """write right rite|knot not|soles souls|loan lone|allowed aloud|for four fore|
their there|to too two|by buy bye|hear here|know no|new knew|one won|our hour|see sea|son sun|wear where ware|
whole hole|would wood|weak week|wait weight|way weigh|which witch|break brake|bored board|sight site|steal steel|
tail tale|plain plane|pair pear|peace piece|mail male|made maid|meet meat|flour flower|die dye|dear deer|
cent sent scent|cell sell|bear bare|be bee|ate eight|heard herd|hi high|role roll|route root|rain reign|road rode|
sail sale|so sew|some sum|stair stare|threw through|waist waste|weather whether|passed past|principal principle|
lesson lessen|missed mist|guessed guest|find fined|band banned|pause paws|caught court|sort sought|saw sore|
adapter adaptor|practice practise|practicing practising|practiced practised|licence license|storey story|
in inn|led lead|red read|ring wring|wrap rap|whose whos|morning mourning|higher hire|flew flu|fair fare|
grown groan|hall haul|heal heel|him hymn|idle idol|key quay|knight night|knows nose|main mane|none nun|
oar or ore|pail pale|rose rows|scene seen|seam seem|shore sure|soar sore|sole soul|stationary stationery|
suite sweet|tea tee|toe tow|vain vein|wade weighed|warn worn|wood would""".replace("\n", " ").split("|")]
# Weak forms the STT often does not hear ("I've filled" / "I filled", "the teacher's" / "the teacher has"): a
# difference in one of these alone is noted, not retaken.
WEAK = {"have", "has", "had", "is", "are", "am", "will", "would"}
DATE_WORDS = {"the", "of", "and"}
# People of the English names table (docs/translation/README.md) and other proper nouns: the STT spells them freely.
NAMES = set("""adam mira perry tony anthony wolfe otto whitlock jane varley leah victor korman ella nina swift dana vale
roman smith helen bartlett joseph miller sonia urban rita andrews emil bellamy paulie paul small faith holbrook charles
merton elaine freeman frank furlong mildred sowerby jerry cassette george crossley desmond des theodore ted fielding
bertha smithson aloysius ramsey lydia rudolph rudy pawley stephen hallam vera norman susanna susie jake goodwin rose
little martha dobson simon fisher tamara king boris sarah willows ian hill miles pollard dotty barnaby blinky atlas
gran grandad bratislava danube walkman walkmans perspex""".split())


def tokens(text: str) -> list[str]:
    t = V.strip_diacritics(text.lower()).replace("’", "'").replace("‘", " ")
    # Contractions are written out on both sides ("it'll" / "it will"); 's only loses its apostrophe here, because it
    # is a possessive as often as "is" ("whatever's" / "whatever is" is handled in errors()).
    t = re.sub(r"(?<=\w)n't\b", " not", t)
    for short, full in (("'ll", " will"), ("'ve", " have"), ("'re", " are"), ("'m", " am"), ("'d", " would")):
        t = re.sub(r"(?<=\w)" + short + r"\b", full, t)
    for short, full in COLLOQUIAL.items():
        t = re.sub(r"(?<![\w'])" + short + r"(?![\w'])", full, t)
    t = re.sub(r"(?<=\w)'(?=\w)", "", t)                       # what is left: o'clock -> oclock
    t = t.replace("%", " percent ").replace("per cent", "percent")
    t = re.sub(r"(\d):00\b", r"\1", t)                          # the STT writes "six" as 6:00
    t = re.sub(r"[^a-z0-9%]+", " ", t)
    return [w for w in t.split() if w]


def canon(w: str) -> str:
    """One spelling for British and American forms and for digits with an ordinal ending. Applied to both sides, so
    a rule that is too broad can only make two words equal that sound alike."""
    w = WORDS.get(w, w)
    if re.fullmatch(r"\d+(st|nd|rd|th)", w):
        return re.sub(r"\D", "", w)
    if NUMBER_WORD.match(w):
        return w
    w = w.replace("our", "or").replace("ise", "ize").replace("isa", "iza").replace("isi", "izi").replace("yse", "yze")
    w = re.sub(r"re(s?)$", r"er\1", w)                         # centre / center, metres / meters
    w = re.sub(r"(n|l|m)t$", r"\1ed", w)                       # learnt / learned, spelt / spelled
    w = re.sub(r"ence$", "ense", w)
    w = w.replace("ae", "e").replace("ogue", "og").replace("grey", "gray")
    w = re.sub(r"(.)\1", r"\1", w)                             # travelling / traveling, Otto / Oto
    return re.sub(r"me$", "m", w) if w.endswith("gram") or w.endswith("grame") else w


SOUND = {canon(w): canon(g[0]) for g in HOMOPHONES for w in g}   # compared word by word, after the number rules


def skeleton(w: str) -> str:
    """Rough sound of a name: consonants only, common spellings of one sound merged."""
    w = canon(w).replace("ph", "f").replace("ck", "k").replace("gh", "").replace("wh", "w").replace("ch", "h")
    w = re.sub(r"c(?=[eiy])", "s", w).replace("c", "k").replace("q", "k").replace("x", "ks").replace("z", "s")
    w = w.replace("j", "y").replace("v", "f").replace("d", "t").replace("b", "p").replace("g", "k")
    w = w[:1] + re.sub(r"r(?![aeiouy])", "", w[1:])            # British r: "Paulie" / "Porly"
    head = "a" if w[:1] in "aeiouy" else w[:1]
    body = re.sub(r"[aeiouyhw]", "", w[1:])
    return head + (body[:-1] if len(body) > 1 and body.endswith("s") else body)   # Tony's / Tony


def errors(ref_text: str, hyp_text: str) -> tuple[list, list, list]:
    """(real differences, minor ones, weak forms). Minor: an added filler word, a foreign name the STT spelled its own
    way. Weak forms: only an auxiliary differs ("I've" / "I")."""
    ref_raw, hyp_raw = tokens(ref_text), tokens(hyp_text)
    ref, hyp = [canon(w) for w in ref_raw], [canon(w) for w in hyp_raw]
    _, ops = V.edit_ops(ref, hyp)
    raw_of = {}
    for w in ref_raw:
        raw_of.setdefault(canon(w), w)
    has_digit = any(w.isdigit() for w in ref + hyp)
    number = lambda w: bool(NUMBER_WORD.match(w))  # noqa: E731
    mixed = any((a.isdigit() and number(b)) or (b.isdigit() and number(a)) for a, b in ops if a and b)

    def name_like(a: str) -> bool:
        w = raw_of.get(a, a)
        return w in NAMES or w in FOREIGN or (w.endswith("s") and (w[:-1] in NAMES or w[:-1] in FOREIGN))

    # word-boundary runs ("all right" / "alright", "Du brovka" / "Dubravka"): equal when joined, or the same sound
    # when the run holds a name
    out_ops, i = [], 0
    while i < len(ops):
        for j in range(min(len(ops), i + 4), i + 1, -1):
            run = ops[i:j]
            a, b = "".join(x for x, _ in run), "".join(y for _, y in run)
            if a == b or (a and b and any(name_like(x) for x, _ in run) and skeleton(a) == skeleton(b)):
                i = j
                break
            # "whatever's" / "whatever is", "the teacher's" / "the teacher has", either way round
            if any(long.endswith("s") and short in (long[:-1] + "is", long[:-1] + "has") for long, short in ((a, b), (b, a))):
                i = j
                break
        else:
            out_ops.append(ops[i])
            i += 1
    # a Slovak name comes back from the STT as English words ("Cierna Voda" / "a churn of water"): the words beside
    # it are part of that guess
    foreign_at = {k for k, (a, _) in enumerate(out_ops) if a and raw_of.get(a, a) in FOREIGN}
    real, minor, weak = [], [], []
    for k, (a, b) in enumerate(out_ops):
        if a and b and (a.isdigit() != b.isdigit()) and (number(a) or number(b)):
            continue                                           # three / 3
        if mixed and ((not a and number(b)) or (not b and number(a))):
            continue                                           # twenty-five / 25: the second word has no partner
        if has_digit and not a and b in DATE_WORDS:
            continue                                           # 7 December / the seventh of December
        if a and b and name_like(a) and skeleton(a) == skeleton(b):
            continue
        if a and b and SOUND.get(a, a) == SOUND.get(b, b):
            continue                                           # write / right
        if raw_of.get(a, a) in ("gran", "grans") and b.startswith("gra"):
            continue                                           # the STT writes Graham, Grant or grand for "Gran"
        if k in foreign_at and b:
            minor.append((raw_of.get(a, a), b))
            continue
        if not a and any(abs(k - f) <= 2 for f in foreign_at):
            minor.append((a, b))
            continue
        if (a in WEAK or not a) and (b in WEAK or not b):
            weak.append((a, b))
            continue
        if not a and b in FILLERS:
            minor.append((a, b))
            continue
        real.append((raw_of.get(a, a), b))
    return real, minor, weak


def timing(m: dict, text: str = "") -> list[str]:
    out = []
    if m.get("longest_pause_s", 0) > 1.4:
        out.append(f"pause {m['longest_pause_s']} s")
    # English is spelled about 1.2 times longer than Slovak for the same speech (measured on the first 900 takes: the
    # takes are as long as the Slovak ones), and a quick short question of Adam's reaches 28 characters per second.
    # Adam's quick short questions reach 37 characters per second and are as long as their Slovak takes; a slow
    # rate means nothing for a single word or a line of years, which are spoken in full.
    rate = m.get("chars_per_s", 12)
    if rate > 38 or (rate < 7.5 and len(text) >= 12 and not re.search(r"\d", text)):
        out.append(f"rate {rate} chars/s")
    return out


def check(job: dict, heard: str, m: dict) -> dict:
    """Against the subtitle text and the spoken form; the one with fewer differences counts."""
    best = None
    for ref in dict.fromkeys((job["text"], spoken(job["text"]))):
        real, minor, weak = errors(ref, heard)
        if best is None or len(real) < len(best[0]):
            best = (real, minor, weak)
    t = timing(m, job["text"])
    return {"meaning_errors": best[0], "minor": best[1], "weak": best[2], "timing": t, "ok": not best[0] and not t}


def score(t: dict) -> tuple:
    c = t["check"]
    return (len(c["meaning_errors"]), len(c["timing"]), len(c["minor"]), len(c.get("weak", [])))


# --------------------------------------------------------------------------- takes

def cache_path(line_id: str) -> Path:
    return RAW / f"{line_id}.json"


def download(url: str, dest: Path) -> Path:
    for attempt in range(4):
        try:
            return V.fal_api.download(url, dest)
        except Exception:  # noqa: BLE001  (a stalled download: the take is paid, try again)
            if attempt == 3:
                raise
            time.sleep(2 + 3 * attempt)
    raise RuntimeError("unreachable")


def take(job: dict, n: int, extra: str = "") -> dict:
    lid = job["line_id"]
    text = spoken(job["text"])
    voice = voice_for(job)
    usd = len(text) / 1000 * V.TTS_PRICE[MODEL]
    res = V.fal_api.run(MODEL, {"prompt": text, "voice": voice["voice"], "style_instructions": voice["style"] + extra},
                        f"{ASSET}gemini/{lid}#t{n}", usd, budget=BUDGET, poll_s=1.0)
    url = res["audio"]["url"]
    raw = download(url, RAW / f"{lid}.t{n}.wav")
    x = V.load_mono(raw)
    m = {k: (float(v) if hasattr(v, "item") else v) for k, v in V.measure(x, text).items()}
    usd_stt = max(float(m["raw_s"]), 1.0) / 60 * 0.008
    heard = ""
    for attempt in range(3):
        try:
            heard = V.fal_api.run(V.SCRIBE, {"audio_url": url, "language_code": "eng", "diarize": False,
                                             "tag_audio_events": False}, f"{ASSET}stt-scribe/{lid}#t{n}", usd_stt,
                                  budget=BUDGET, poll_s=1.0).get("text", "").strip()
            break
        except V.fal_api.BudgetExceeded:
            raise
        except Exception:  # noqa: BLE001  (Scribe HTTP 500 now and then)
            if attempt == 2:
                raise
            time.sleep(3)
    return {"take": n, "raw": raw.name, "measure": m, "heard": heard, "check": check(job, heard, m),
            "usd_tts": round(usd, 5), "usd_stt": round(usd_stt, 5),
            **({"extra_direction": extra.strip()} if extra else {})}


def render(rec: dict) -> dict:
    x = V.load_mono(RAW / rec["best"]["raw"])
    y, lufs, peak = G.finish(x, rec.get("fx"))
    TAKES.mkdir(parents=True, exist_ok=True)
    V.write_ogg(TAKES / f"{rec['line_id']}.ogg", y)
    rec.update(duration_s=round(len(y) / V.SR, 2), lufs=round(float(lufs), 1), peak_dbtp=round(float(peak), 1))
    return rec


def save(rec: dict) -> None:
    cache_path(rec["line_id"]).write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")


def gen_one(job: dict) -> dict:
    cache = cache_path(job["line_id"])
    v = voice_for(job)
    if cache.exists():
        rec = json.loads(cache.read_text(encoding="utf-8"))
        if rec.get("text_sha1") == text_hash(job["text"]) and rec.get("voice_settings") == v and rec.get("fx") == job["fx"]:
            if "duration_s" not in rec or not (TAKES / f"{job['line_id']}.ogg").exists():
                save(render(rec))
            return rec
        print("text, casting or colour changed, taking again:", job["line_id"], flush=True)
    rec = {**job, "model": MODEL, "voice": v["voice"], "voice_settings": v, "tts_text": spoken(job["text"]),
           "text_sha1": text_hash(job["text"]), "takes": 0, "all_takes": [], "best": None, "retaken": False}
    t = take(job, 1)
    rec.update(takes=1, all_takes=[t], best=t)
    save(rec)                                                  # the paid take is kept even if the render fails
    save(render(rec))
    return rec


def owners(all_jobs: list[dict]) -> list[dict]:
    al = aliases(all_jobs)
    return [j for j in all_jobs if j["line_id"] not in al]


def records() -> list[dict]:
    out = []
    for j in owners(jobs()):
        f = cache_path(j["line_id"])
        if f.exists():
            out.append(json.loads(f.read_text(encoding="utf-8")))
    return out


def spend(recs: list[dict]) -> float:
    return sum(t["usd_tts"] + t["usd_stt"] for r in recs for t in r["all_takes"])


def sample(todo: list[dict]) -> list[dict]:
    """Pilot: two lines per speaker (a short and a long one), every colour, and every line with a name hint or a
    spoken form among the first 40 such lines."""
    picked, seen = [], {}
    for j in todo:
        n = seen.get(j["speaker"], 0)
        if n < 2 and (n == 0 or len(j["text"]) > 60):
            seen[j["speaker"]] = n + 1
            picked.append(j)
    special = [j for j in todo if hint(j["text"]) or spoken(j["text"]) != V.tts_text(j["text"])][:40]
    colours = {}
    for j in todo:
        if j["fx"]:
            colours.setdefault(j["fx"], j)
    ids = set()
    return [j for j in picked + special + list(colours.values()) if not (j["line_id"] in ids or ids.add(j["line_id"]))]


def cmd_plan(a) -> None:
    all_jobs = jobs()
    todo = owners(all_jobs)
    chars = sum(len(spoken(j["text"])) for j in todo)
    by = {}
    for j in all_jobs:
        by[j["group"]] = by.get(j["group"], 0) + 1
    print("keys", len(all_jobs), by, "| takes", len(todo), "| aliases", len(all_jobs) - len(todo))
    print("characters", chars, f"| TTS ${chars / 1000 * V.TTS_PRICE[MODEL]:.2f}",
          f"| with hints: {sum(1 for j in todo if hint(j['text']))} lines")
    print("speakers", len({j['speaker'] for j in todo}), "| logged so far", round(V.fal_api.logged_spend(ASSET), 3))


def cmd_gen(a) -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    todo = owners(jobs())
    if a.sample:
        todo = sample(todo)
    if a.only:
        todo = [j for j in todo if j["line_id"] in a.only]
    if a.limit:
        todo = todo[: a.limit]
    print(len(todo), "lines to take,", sum(len(spoken(j["text"])) for j in todo), "chars;",
          f"logged spend so far ${V.fal_api.logged_spend(ASSET):.3f}", flush=True)
    failed, done = [], 0
    with ThreadPoolExecutor(max_workers=a.workers) as pool:
        futs = {pool.submit(gen_one, j): j["line_id"] for j in todo}
        for f in as_completed(futs):
            lid = futs[f]
            try:
                f.result()
                done += 1
                if done % 100 == 0:
                    print(f"{done} done, spend ${V.fal_api.logged_spend(ASSET):.3f}", flush=True)
            except Exception as e:  # noqa: BLE001
                failed.append(lid)
                print("FAILED", lid, str(e)[:300], flush=True)
                if isinstance(e, V.fal_api.BudgetExceeded):
                    print("BUDGET CAP REACHED - stopping", flush=True)
                    pool.shutdown(cancel_futures=True)
                    break
    print(f"{done} done, {len(failed)} failed: {failed[:20]}", flush=True)
    cmd_report(a)


def cmd_report(a=None) -> None:
    recs = records()
    bad = [r for r in recs if not r["best"]["check"]["ok"]]
    show = recs if getattr(a, "all", False) else bad
    for r in show:
        c = r["best"]["check"]
        print(f"{r['line_id']} [{r['speaker']}{' retaken' if r['retaken'] else ''}] {c['meaning_errors']} {c['timing']}"
              f"{' minor ' + str(c['minor']) if c['minor'] else ''}\n   script: {r['text']}\n   heard:  {r['best']['heard']}")
    me = sum(1 for r in recs if r["best"]["check"]["meaning_errors"])
    clean = sum(1 for r in recs if r["best"]["check"]["ok"] and not r["best"]["check"]["minor"])
    secs = sum(r.get("duration_s", 0) for r in recs)
    print(f"{len(recs)} of {len(owners(jobs()))} takes recorded, {clean} clean, {len(bad)} with differences ({me} meaning); "
          f"{secs / 60:.1f} min; spend (per call) ${spend(recs):.4f}; logged ${V.fal_api.logged_spend(ASSET):.4f}")


def cmd_retake(a) -> None:
    by_id = {j["line_id"]: j for j in jobs()}
    if a.all_flagged:
        ids = [r["line_id"] for r in records() if r["best"]["check"]["meaning_errors"] and not r["retaken"]]
    else:
        ids = a.ids
    print(len(ids), "retakes", flush=True)

    def one(lid: str) -> None:
        rec = json.loads(cache_path(lid).read_text(encoding="utf-8"))
        if rec["retaken"]:
            print("already retaken once:", lid)
            return
        short = len(tokens(rec["text"])) <= 6
        t = take(by_id[lid], rec["takes"] + 1, CLEAR if short else VERBATIM)
        rec["all_takes"].append(t)
        rec["takes"] += 1
        rec["retaken"] = True
        if score(t) < score(rec["best"]):
            rec["best"] = t
            render(rec)
        print(lid, "-> take", rec["best"]["take"], "|", t["heard"], t["check"]["meaning_errors"], flush=True)
        save(rec)
    with ThreadPoolExecutor(max_workers=10) as pool:
        for f in [pool.submit(one, lid) for lid in ids]:
            try:
                f.result()
            except Exception as e:  # noqa: BLE001
                print("FAILED retake", str(e)[:300], flush=True)
    cmd_report()


def cmd_recheck(a=None) -> None:
    by_id = {j["line_id"]: j for j in jobs()}
    changed = 0
    for r in records():
        for t in r["all_takes"]:
            t["check"] = check(by_id[r["line_id"]], t["heard"], t["measure"])
        best = min(r["all_takes"], key=score)
        if best["take"] != r["best"]["take"]:
            changed += 1
            r["best"] = best
            render(r)
        else:
            r["best"] = best
        save(r)
    print("best take changed for", changed)
    cmd_report()


def cmd_rerender(a) -> None:
    recs = records()

    def one(r: dict) -> None:
        save(render(r))
    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(one, recs))
    lu = [r["lufs"] for r in recs]
    print(f"{len(recs)} rendered; LUFS {min(lu)} .. {max(lu)}; peak max {max(r['peak_dbtp'] for r in recs)} dBTP")


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("plan")
    g = sub.add_parser("gen")
    g.add_argument("--workers", type=int, default=12)
    g.add_argument("--only", nargs="*")
    g.add_argument("--limit", type=int, default=0)
    g.add_argument("--sample", action="store_true")
    rp = sub.add_parser("report")
    rp.add_argument("--all", action="store_true")
    r = sub.add_parser("retake")
    r.add_argument("ids", nargs="*")
    r.add_argument("--all-flagged", action="store_true")
    sub.add_parser("recheck")
    sub.add_parser("rerender")
    sub.add_parser("finalize")
    sub.add_parser("install")
    a = ap.parse_args()
    if a.cmd in ("finalize", "install"):
        import en_dub_manifest as M
        (M.build if a.cmd == "finalize" else M.install)()
        return
    {"plan": cmd_plan, "gen": cmd_gen, "report": cmd_report, "retake": cmd_retake, "recheck": cmd_recheck,
     "rerender": cmd_rerender}[a.cmd](a)


if __name__ == "__main__":
    main()
