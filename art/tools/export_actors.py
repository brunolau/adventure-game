"""Export NPC sprite sets from art/characters/<ID>/ to the game: src/game/assets/actors/<ID>/ (free, local).

For each actor this writes WebP spritesheets (lossy RGB q92, lossless alpha) next to their JSON (cell, pivot =
feet centre or sill line, playback_fps, stride_px_per_s, oneshot, frame names) and an actor.json manifest that
maps the presentation's IActorVisual calls (idle, SetTalking, PlayGesture, blink) onto sheets and frames.

Usage: python export_actors.py [ID ...]      (default: the prologue NPCs ELA DANA MIRA20 ROMAN LENKA JOZEF)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image

ART = Path(__file__).resolve().parent.parent
REPO = ART.parent
CHAR_ROOT = ART / "characters"
GAME_ACTORS = REPO / "src" / "game" / "assets" / "actors"

STILL_FRAMES = ["idle", "blink", "talk_a", "talk_b", "gesture"]

# sheet key -> source sheet (relative to art/characters/<ID>/)
SHEETS = {
    "npc": "npc_set/npc_sheet.png",
    "idle": "idle_hailuo/idle_sheet.png",
    "idle_checklist": "idle_checklist_hailuo/idle_checklist_sheet.png",
    "npc_bust": "window/npc_bust_sheet.png",
    "npc_bust_glass": "window/npc_bust_glass_sheet.png",
    "idle_bust": "window/idle_bust_sheet.png",
    "idle_bust_glass": "window/idle_bust_glass_sheet.png",
}

NOTES = {
    "ELA": "S03. Standing (the art_brief says she sits; see ISSUES ART-NPC-01). Magenta key (green vest). idle = calm "
           "ping-pong of a Hailuo clip (head turns toward the road and back); idle_checklist = optional fidget "
           "(she checks her clipboard), play it now and then instead of one idle cycle.",
    "DANA": "S04, seen at the shop's serving window. Full figure by default; window/ bust variants (sill line at 50 % "
            "of the figure height) if the S04 background puts her behind glass.",
    "MIRA20": "S06, only ever behind a closed big window, on the phone with Adam. Use the window_glass variant in S06: "
              "pivot = top edge of the painted window sill (cut at 45 % of the figure height from the top). No mask "
              "(indoors, alone).",
    "ROMAN": "S02. Courier with one parcel; the van with the invented ŠUP brand belongs to the background.",
    "LENKA": "S02. The dog Bodka (one black spot) is part of every frame; the sprite is wider than the hotspot rect.",
    "JOZEF": "S07. Folding magnifier in hand; the gesture raises it to his eye.",
}


def to_webp(src: Path, dst: Path) -> tuple[int, int]:
    img = Image.open(src).convert("RGBA")
    if max(img.size) > 16383:
        raise SystemExit(f"{src} is {img.size}, beyond the WebP limit")
    dst.parent.mkdir(parents=True, exist_ok=True)
    img.save(dst, "WEBP", quality=92, alpha_quality=100, method=6)
    check = Image.open(dst)
    assert check.size == img.size
    return img.size


def sheet_json(src_json: Path, key: str, webp_name: str) -> dict:
    meta = json.loads(src_json.read_text(encoding="utf-8"))
    out = dict(meta)
    out["file"] = webp_name
    if isinstance(meta.get("frames"), list):
        out["frame_names"] = meta["frames"]
        out["frames"] = len(meta["frames"])
    out.setdefault("oneshot", False)
    out.setdefault("stride_px_per_s", None)
    out["loop"] = key.startswith("idle") and not out["oneshot"]
    out.setdefault("pivot_is_sill_line", False)
    for drop in ("source_frames", "sources"):
        out.pop(drop, None)
    return out


def export(char_id: str) -> dict:
    src_dir = CHAR_ROOT / char_id
    dst_dir = GAME_ACTORS / char_id
    sheets = {}
    for key, rel in SHEETS.items():
        src = src_dir / rel
        if not src.exists():
            continue
        name = f"{key}_sheet.webp"
        size = to_webp(src, dst_dir / name)
        meta = sheet_json(src.with_suffix(".json"), key, name)
        (dst_dir / f"{key}_sheet.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n",
                                                  encoding="utf-8", newline="\n")
        sheets[key] = {"file": name, "json": f"{key}_sheet.json", "size": list(size), "cell": meta["cell"],
                       "pivot": meta["pivot"], "frames": meta["frames"]}
    has_video_idle = "idle" in sheets

    def anims(still: str, video: str | None) -> dict:
        a = {
            "idle": ({"sheet": video, "loop": True} if video else {"sheet": still, "frames": ["idle"]}),
            "idle_still": {"sheet": still, "frames": ["idle"]},
            "blink": {"sheet": still, "frames": ["blink"], "hold_ms": 110, "every_s": [2.5, 6.0],
                      "note": "only while the still idle is shown (the video idle blinks by itself)"},
            "talk": {"sheet": still, "frames": ["talk_a", "talk_b", "talk_a", "idle", "talk_b", "talk_a", "idle"],
                     "fps": 8, "loop": True},
            "gesture": {"sheet": still, "frames": ["gesture"], "hold_ms": 1200, "oneshot": True,
                        "note": "PlayGesture: hold, then return to idle (no in-betweens)"},
        }
        if video and "idle_checklist" in sheets and still == "npc":
            a["idle_fidget"] = {"sheet": "idle_checklist", "loop": False, "every_s": [12, 25]}
        return a

    manifest = {
        "id": char_id,
        "source": f"art/characters/{char_id}",
        "view": "three-quarter, facing right (mirror for facing left)",
        "height_px": 512,
        "pivot": "feet centre, 4 px above the cell bottom (window variants: centre of the sill cut edge)",
        "sheets": sheets,
        "animations": anims("npc", "idle" if has_video_idle else None),
        "switching": ("Start talking only at a video idle loop boundary (cell 0 matches the still idle pose) or "
                      "cross-fade ~80 ms; video cells are slightly softer than the edit-based stills."),
        "notes": NOTES.get(char_id, ""),
    }
    if "npc_bust_glass" in sheets:
        manifest["variants"] = {
            "window_glass": {"animations": anims("npc_bust_glass", "idle_bust_glass" if "idle_bust_glass" in sheets
                                                 else None),
                             "note": "behind closed glass: bust cut at the sill line, pale veil + soft reflection"},
            "window": {"animations": anims("npc_bust", "idle_bust" if "idle_bust" in sheets else None),
                       "note": "bust without the glass treatment (if the engine adds its own glass layer)"},
        }
        manifest["default_variant"] = "window_glass" if char_id == "MIRA20" else None
    (dst_dir / "actor.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8",
                                        newline="\n")
    return manifest


def main() -> None:
    ids = sys.argv[1:] or ["ELA", "DANA", "MIRA20", "ROMAN", "LENKA", "JOZEF"]
    for char_id in ids:
        manifest = export(char_id)
        print(char_id, {k: (v["size"], v["frames"]) for k, v in manifest["sheets"].items()})


if __name__ == "__main__":
    main()
