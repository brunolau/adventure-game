"""Voice-over of the look bubbles (2026-10-08): every text Adam says when the player looks at something.

Scope (art/voice/full/looks.json, written by extract_full.py / write_looks): the room looks look.* (and the changed
looks later in the story), the inventory descriptions item.<ID>, the locked exit / route lines (exit.*.locked,
conn.*.locked), the puzzle success / wrong lines and ui.system.path_blocked. Not the place names shown when looking at
an open exit. All of them are Adam (Achird, his casting_full direction); the recast's dry-irony sentence goes on the
clearly ironic ones only (IRONY_LOOKS).

The same sentence is one take: the first key of each text is generated, every other key with that text is an alias.
The game reads the aliases from src/game/assets/voice/aliases.json (key -> file stem) instead of duplicate files.

Same model, prompt, check and post-processing as gen_full.py (whose take/render/check are reused): Gemini 3.8 Flash
TTS, one ElevenLabs Scribe v2 check per take, exactly one retake when the transcript differs in meaning, the rest is
flagged; trim, -16 LUFS, OGG. Spend scope voice/full/looks/ with its own cap.

usage:
  python looks_full.py gen [--workers N] [--only KEY ...] [--cap 3]   take 1 + Scribe (resumable, cached per key)
  python looks_full.py report
  python looks_full.py retake [--cap 3]                               one retake for every meaning difference
  python looks_full.py finalize                                       manifest.json / flags.json / casting.json
  python looks_full.py install                                        OGGs + aliases.json into src/game/assets/voice/
"""
from __future__ import annotations

import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import voice_lib as V  # noqa: E402
import recast as R  # noqa: E402
import gen_full as G  # noqa: E402

FULL = G.FULL
RAW = V.ROOT / "art/voice/raw/full/looks"
SCOPE = "voice/full/looks/"
ALIASES = G.GAME / "aliases.json"

# Clearly ironic look texts (a wry twist Adam means: self-irony, dry punchline, understatement, mock-seriousness).
# Read one by one with the rule of irony_full.py; descriptive, sincere, tender and instructive looks are not marked.
IRONY_LOOKS = set("""
look.S01.ambient 1|look.S01.ambient 2|look.S02.ambient 1|look.S02.ambient 2|look.S02.LENKA|look.S03.ambient 1|
look.S03.ambient 2|look.S03.ELA|look.S04.ambient 2|look.S05.ambient 1|look.S05.ambient 2|look.S06.photo|
look.S06.ambient 1|look.S06.MIRA20|look.S09.case|look.S09.ambient 1|look.S09.ambient 2|look.S10.ambient 1|
look.S51.ambient 2|look.S52.ambient 1|look.S52.ambient 2|look.S54.JANA20|look.S55.ambient 2|look.S08.ball|
look.S08.ambient 2|look.S07.board|look.S07.ambient 1|look.S07.ambient 2|look.S07.JOZEF|look.S12.ambient 1|
look.S12.ambient 2|look.S13.ambient 1|look.S14.ambient 1|look.S14.ambient 2|look.S14.MIRA95|look.S15.ambient 1|
look.S16.ambient 1|look.S16.ambient 2|look.S11.ambient 1|look.S11.ambient 2|look.S19.ambient 1|look.S19.EMIL|
look.S20.ambient 1|look.S20.ambient 2|look.S21.ambient 1|look.S21.ambient 2|look.S25.ambient 1|look.S25.ambient 2|
look.S25.TRH|look.S27.ambient 1|look.S27.ambient 2|look.S26.ambient 1|look.S23.ambient 1|look.S23.ambient 2|
look.S23.ARCHIVAR|look.S24.ambient 1|look.S24.ambient 2|look.S22.ambient 1|look.S22.ambient 2|look.S29.ambient 1|
look.S29.ambient 2|look.S29.DEZI|look.S17.ambient 1|look.S17.SONA|look.S69.wall|look.S69.court|look.S69.lamp|
look.S69.bench|look.S69.ZUZANA95|look.S69.KUBO.variant1|look.S18.ambient 2|look.S18.ZITA|look.S31.ambient 1|
look.S31.BOZO|look.S32.ambient 1|look.S32.ambient 2|look.S35.ambient 2|look.S34.ambient 1|look.S34.ambient 2|
look.S34.RUDO|look.S37.ambient 1|look.S37.VERA60|look.S37.hopscotch|look.S38.ambient 1|look.S39.ambient 1|
look.S39.MIRA60|look.S40.script|look.S40.ambient 2|look.S33.ambient 2|look.S41.ambient 1|exit.S41.to_S67.locked|
look.S42.NINA|look.S43.ambient 1|look.S43.ambient 2|look.S44.ambient 1|look.S44.BORIS|look.S46.ambient 1|
look.S46.ambient 2|look.S46.SARA|look.S67.IVAN|look.S47.ambient 2|look.S48.ambient 1|look.S57.ambient 1|
look.S57.ambient 2|look.S58.ambient 1|look.S58.ambient 2|look.S62.ambient 1|look.S62.ambient 2|look.S65.ambient 1|
look.S65.ambient 2|look.S63.ambient 2|look.S66.ambient 2|look.S36.ambient 2|
item.PHONE|item.TOOLS|item.SHEDKEY|item.REGISTERED|item.BALL|item.DELIVERY_NOTE
""".replace("\n", "").split("|")) - {""}


def looks() -> list[dict]:
    return json.loads((FULL / "looks.json").read_text(encoding="utf-8"))["lines"]


def aliases(lines: list[dict]) -> dict[str, str]:
    """key -> the first key with the same text (all are Adam, no colour)."""
    first, out = {}, {}
    for l in lines:
        if l["text"] in first:
            out[l["line_id"]] = first[l["text"]]
        else:
            first[l["text"]] = l["line_id"]
    return out


def unique(lines: list[dict]) -> list[dict]:
    al = aliases(lines)
    return [l for l in lines if l["line_id"] not in al]


def setup(cap: float = 3.0) -> None:
    """Point gen_full's take/render at the looks: own raw folder, own spend scope and cap, the look irony set."""
    G.RAW = RAW
    G.ASSET = SCOPE
    G.BUDGET = (SCOPE, cap)
    G.IRONY = set(G.IRONY) | IRONY_LOOKS
    RAW.mkdir(parents=True, exist_ok=True)
    V.fal_api.download = _download_retry  # a stalled media read (300 s timeout) must not lose a paid take


def _download_retry(url: str, dest: Path) -> Path:
    import time
    import requests
    dest.parent.mkdir(parents=True, exist_ok=True)
    err = None
    for attempt in range(5):
        try:
            r = requests.get(url, timeout=(10, 40), headers={"User-Agent": V.fal_api.USER_AGENT})
            r.raise_for_status()
            dest.write_bytes(r.content)
            return dest
        except Exception as e:  # noqa: BLE001
            err = e
            time.sleep(2 + 3 * attempt)
    raise RuntimeError(f"download failed after retries: {err}")


def records() -> list[dict]:
    out = []
    for l in unique(looks()):
        f = RAW / f"{l['line_id']}.json"
        if f.exists():
            out.append(json.loads(f.read_text(encoding="utf-8")))
    return out


def gen_one(line: dict) -> dict:
    return G.gen_one(line)  # cached per key in RAW (text_sha1 + voice settings), paid take kept before render


def cmd_gen(a) -> None:
    lines = unique(looks())
    if a.only:
        lines = [l for l in lines if l["line_id"] in a.only]
    todo = [l for l in lines if not (RAW / f"{l['line_id']}.json").exists()]
    print(len(lines), "unique texts,", len(todo), "to take,", sum(len(G.spoken(l["text"])) for l in todo), "chars;",
          f"logged in {SCOPE} so far ${V.fal_api.logged_spend(SCOPE):.3f} (cap {G.BUDGET[1]})")
    failed, done, stop = [], 0, False
    with ThreadPoolExecutor(max_workers=a.workers) as pool:
        futs = {pool.submit(gen_one, l): l["line_id"] for l in lines}
        for f in as_completed(futs):
            try:
                f.result()
                done += 1
                if done % 50 == 0:
                    print(f"{done} done, spend ${V.fal_api.logged_spend(SCOPE):.3f}", flush=True)
            except Exception as e:  # noqa: BLE001
                failed.append(futs[f])
                print("FAILED", futs[f], str(e)[:300], flush=True)
                if not stop and ("budget" in str(e).lower() or "cap" in str(e).lower()):
                    print("BUDGET CAP REACHED - stopping")
                    stop = True
                    pool.shutdown(cancel_futures=True)
    print(f"{done} done, {len(failed)} failed: {failed[:20]}")
    cmd_report(a)


def cmd_report(a=None) -> None:
    recs = records()
    bad = [r for r in recs if not r["best"]["check"]["ok"]]
    for r in bad:
        c = r["best"]["check"]
        print(f"{r['line_id']}{' [retaken]' if r['retaken'] else ''} {c['meaning_errors']} {c['timing']}\n"
              f"   script: {r['text']}\n   scribe: {r['best']['stt_scribe']}")
    me = sum(1 for r in recs if r["best"]["check"]["meaning_errors"])
    print(f"{len(recs)} records, {sum(1 for r in recs if r['best']['wer_scribe']['wer'] == 0)} verbatim, {len(bad)} with "
          f"differences ({me} meaning); spend per call ${G.spend(recs):.4f}; logged ${V.fal_api.logged_spend(SCOPE):.4f}")


def cmd_retake(a) -> None:
    lines = {l["line_id"]: l for l in looks()}
    ids = [r["line_id"] for r in records() if r["best"]["check"]["meaning_errors"] and not r["retaken"]]
    print(len(ids), "retakes")

    def one(lid: str) -> None:
        f = RAW / f"{lid}.json"
        rec = json.loads(f.read_text(encoding="utf-8"))
        if rec["retaken"]:
            return
        short = len(V.norm_words(rec["text"])) <= 6
        t = G.take(lines[lid], rec["takes"] + 1, (R.CLEAR if short else G.VERBATIM) + G.name_hint(rec["text"]))
        rec["all_takes"].append(t)
        rec["takes"] += 1
        rec["retaken"] = True
        if R.score(t) < R.score(rec["best"]):
            rec["best"] = t
            G.render(rec)
        print(lid, "-> take", rec["best"]["take"], "|", t["stt_scribe"], t["check"]["meaning_errors"], flush=True)
        f.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
    with ThreadPoolExecutor(max_workers=8) as pool:
        for fut in [pool.submit(one, i) for i in ids]:
            try:
                fut.result()
            except Exception as e:  # noqa: BLE001
                print("FAILED retake", str(e)[:300])
    cmd_report()


# --------------------------------------------------------------------------- manifest part (used by manifest_full)

def manifest_part(flag_of) -> tuple[list[dict], dict[str, str], dict, list[str]]:
    """The manifest entries of every look key (aliases point at their take), their flags, counts, missing keys."""
    from collections import Counter
    lines = looks()
    al = aliases(lines)
    recs = {r["line_id"]: r for r in records()}
    out, flags, missing = [], {}, []
    for l in lines:
        lid = l["line_id"]
        src = al.get(lid, lid)
        r = recs.get(src)
        if r is None:
            missing.append(lid)
            continue
        b = r["best"]
        f = flag_of(r) if src == lid else None
        if f:
            flags[lid] = f
        out.append({k: l[k] for k in ("line_id", "speaker", "text", "kind", "kind_label", "era", "scene", "scene_name",
                                       "label", "fx")}
                   | {"text_sha1": G.text_hash(l["text"]), "source": "looks", "alias_of": src if src != lid else None,
                      "model": r["model"], "voice": r["voice"], "delivery": r["delivery"], "tts_text": r["tts_text"],
                      "file": f"{src}.ogg", "duration_s": r["duration_s"], "lufs": r["lufs"],
                      "peak_dbtp": r["peak_dbtp"], "takes": r["takes"], "retaken": r["retaken"],
                      "stt": {"scribe_v2": b["stt_scribe"], "wer_scribe": b["wer_scribe"]["wer"],
                              "meaning_errors": b["check"]["meaning_errors"], "minor": b["check"].get("minor", []),
                              "timing": b["check"]["timing"], "chars_per_s": b["measure"].get("chars_per_s"),
                              "ok": flag_of(r) is None, "flag": flag_of(r)}})
    takes = [e for e in out if not e["alias_of"]]
    counts = {"keys": len(out), "takes": len(takes), "aliases": len(out) - len(takes),
              "by_kind": dict(Counter(e["kind"] for e in out)),
              "takes_by_kind": dict(Counter(e["kind"] for e in takes)),
              "retaken": sum(1 for e in takes if e["retaken"]), "flagged": len(flags),
              "verbatim": sum(1 for e in takes if e["stt"]["wer_scribe"] == 0),
              "irony": sum(1 for e in takes if e["delivery"]),
              "minutes": round(sum(e["duration_s"] for e in takes) / 60, 1),
              "chars": sum(len(e["text"]) for e in takes),
              "spend_usd": round(G.spend(list(recs.values())), 4),
              "spend_logged_usd": round(V.fal_api.logged_spend(SCOPE), 4)}
    return out, flags, counts, missing


def install() -> None:
    """Copy the takes (one file per distinct text) and write aliases.json, after checking the live text."""
    import filecmp
    import shutil
    man = json.loads((FULL / "manifest.json").read_text(encoding="utf-8"))
    live = {l["line_id"]: l["text"] for l in looks()}
    entries = man.get("looks") or []
    stale = [e["line_id"] for e in entries if live.get(e["line_id"]) != e["text"]]
    if stale or len(entries) != len(live):
        raise SystemExit(f"looks out of date (run extract_full.py, looks_full.py gen, finalize): {stale[:10]} "
                         f"{len(entries)} entries vs {len(live)} live keys")
    copied, same = [], 0
    for e in entries:
        if e["alias_of"]:
            continue
        dst = G.GAME / e["file"]
        if dst.exists() and filecmp.cmp(FULL / e["file"], dst, shallow=False):
            same += 1
            continue
        shutil.copyfile(FULL / e["file"], dst)
        copied.append(e["line_id"])
    old = json.loads(ALIASES.read_text(encoding="utf-8")) if ALIASES.exists() else {}
    keep = {k: v for k, v in old.items() if k not in live}  # aliases of other line kinds stay
    keep.update({e["line_id"]: e["alias_of"] for e in entries if e["alias_of"]})
    ALIASES.write_text(json.dumps(dict(sorted(keep.items())), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("copied", len(copied), f"files ({same} identical, untouched); aliases.json: {len(keep)} keys")


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("gen")
    g.add_argument("--workers", type=int, default=10)
    g.add_argument("--only", nargs="*")
    g.add_argument("--cap", type=float, default=3.0)
    sub.add_parser("report")
    r = sub.add_parser("retake")
    r.add_argument("--cap", type=float, default=3.0)
    sub.add_parser("finalize")
    sub.add_parser("install")
    a = ap.parse_args()
    if a.cmd in ("gen", "report", "retake"):
        setup(getattr(a, "cap", 3.0))  # finalize/install must not repoint gen_full (manifest_full reads its records)
    if a.cmd == "finalize":
        from manifest_full import build
        build()
    elif a.cmd == "install":
        install()
    else:
        {"gen": cmd_gen, "report": cmd_report, "retake": cmd_retake}[a.cmd](a)


if __name__ == "__main__":
    main()
