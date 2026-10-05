"""S41 winter repaint: ONE paid paint_natural attempt (USD 0.15) with the owner's friend's photos as the main inputs.

Uses art/tools/paint_natural.py (install(): natural geometry, sketch, prompt placeholders, review overlay) with two
local changes for this room only:
  * image-role preamble: images 2-3 show EXACTLY this real view (the usual preamble says "references only, do not
    copy their camera"), image 4 is the style reference;
  * masters are named art/masters/bg_natural/S41_winter_v<N>.png (the summer S41_v1..v4 stay untouched); the paid
    call writes into a staging folder first, then the master + sidecar are moved and reviewed under that name.
Usage: python paint_s41_winter.py [--seed N] [--dry]
"""
import argparse
import datetime
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]   # repo root
sys.path.insert(0, str(ROOT / "art" / "tools"))
import paint_natural  # noqa: E402

paint_natural.install()
import paint_room  # noqa: E402
import review_room  # noqa: E402
import fal_api  # noqa: E402

ROOM = "S41"
SCOPE = "bg_natural/S41_winter/"
BUDGET = 4.0
MAX_ATTEMPTS = 3
FINAL_DIR = ROOT / "art" / "masters" / "bg_natural"
STAGE = ROOT / "art" / "review" / "natural" / "_s41_winter_stage"   # git-ignored


def preamble(refs, sketch):
    n = len(refs)
    return (
        f"You receive {n + 2} images. Image 1 is the LAYOUT SKETCH of the finished 1920x1080 game screen: a crude "
        f"flat-colour blocking traced from image 2 that fixes the exact composition - camera, horizon, road, wall, "
        f"buildings, trees and the position, size and outline of every object. Repaint image 1 into a finished "
        f"painting: keep every line and every block exactly where it is and exactly as large as it is, paint each "
        f"block as the object described below, do not move, enlarge, shrink, add or remove anything, and leave no "
        f"flat colour areas or hard geometric edges. Image 2 is a photo of EXACTLY THIS VIEW of the real place, taken "
        f"in summer from the same camera (image 1 is traced from it): paint its real buildings, road, footbridge, "
        f"retaining wall, fence, station, pylon, trees and hills as they really are and in the same places, but in "
        f"deep winter, and leave out its cars, people, flags, posters and signs. Image 3 is a second summer photo of "
        f"the same place from a few dozen metres further along the road: the same chalet hotel on the left and the "
        f"same gondola station on the right, seen closer; use it for their real shapes, materials and colours, do not "
        f"copy its camera. Image {n + 2} is a finished background painting from our game: use it ONLY as the "
        f"reference for the painting technique (brushwork, palette harmony, edge softness, level of detail, line "
        f"quality); do not copy anything from its scene, season or light.")


paint_room.roles_preamble = preamble


def winter_versions():
    import re
    return sorted(int(m.group(1)) for p in FINAL_DIR.glob(f"{ROOM}_winter_v*.png")
                  if (m := re.fullmatch(rf"{ROOM}_winter_v(\d+)\.png", p.name)))


def paid_winter_attempts():
    n = 0
    for v in winter_versions():
        side = FINAL_DIR / f"{ROOM}_winter_v{v}.json"
        if side.exists():
            meta = json.loads(side.read_text(encoding="utf-8"))
            if meta.get("usd", 0) > 0 and meta.get("kind", "paint") == "paint":
                n += 1
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int)
    ap.add_argument("--dry", action="store_true", help="assemble and print the prompt only (free)")
    ap.add_argument("--finish", type=int, help="post-process a staged attempt N (move, sidecar, review)")
    args = ap.parse_args()
    if args.finish:
        finish(args.finish)
        return
    if paint_natural.run_check(ROOM) != 0:
        sys.exit("fix the blocking errors first")
    paint_natural.write_guide(ROOM)
    paint_room.render_sketch(ROOM)
    paint_natural.natural_review(ROOM, paint_room.LAYOUT / f"{ROOM}_sketch.png")
    job = paint_room.assemble(ROOM, "sketch")
    if args.dry:
        print(job["prompt"])
        for i, (_, _, name) in enumerate(job["images"], 1):
            print(f"{i}: {name}")
        print(len(job["prompt"]), "characters")
        return
    done = paid_winter_attempts()
    if done >= MAX_ATTEMPTS:
        sys.exit(f"{done} paid winter attempts already (max {MAX_ATTEMPTS})")
    number = (winter_versions() or [0])[-1] + 1
    STAGE.mkdir(exist_ok=True)
    for p in STAGE.glob("*"):
        p.unlink()
    paint_room.MASTERS = STAGE
    review_room.MASTERS = STAGE
    saved_review = review_room.review
    review_room.review = lambda *a, **k: None
    # next_version in the empty stage folder is 1; make the spend-log asset name carry the winter number
    paint_room.next_version = lambda room_id: number
    ns = argparse.Namespace(room=ROOM, mode="sketch", seed=args.seed, budget=BUDGET, scope=SCOPE)
    print(f"{ROOM} winter attempt {done + 1} of {MAX_ATTEMPTS} -> S41_winter_v{number} (scope {SCOPE}, budget {BUDGET})")
    paint_room.cmd_paint(ns)
    review_room.review = saved_review
    finish(number)


def finish(number):
    staged = STAGE / f"{ROOM}_v{number}.png"
    final = FINAL_DIR / f"{ROOM}_winter_v{number}.png"
    shutil.move(str(staged), final)
    meta = json.loads((STAGE / f"{ROOM}_v{number}.json").read_text(encoding="utf-8"))
    meta.update({"version": f"winter_v{number}", "kind": "paint", "master": final.relative_to(ROOT).as_posix(),
                 "prompt_file": f"art/prompts/natural/{ROOM}.txt", "blocking_file": f"src/game/data/blocking/{ROOM}.json",
                 "blocking": paint_natural.blocking_of(ROOM),
                 "preamble": "custom (scratch wrapper paint_s41_winter.py): photos 2-3 show exactly this view",
                 "image_urls": [f"art/layout/natural/{ROOM}_sketch.png (rendered from art/prompts/natural/{ROOM}.sketch.json, model geometry)"]
                 + meta["image_urls"][1:],
                 "note": "owner photos (friend's private archive, permission per owner 2026-10-06) used as image inputs; kept local"})
    final.with_suffix(".json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    (STAGE / f"{ROOM}_v{number}.json").unlink()
    paint_natural.natural_review(ROOM, final)
    print(f"LOOK at {final} and art/review/natural/{final.stem}_overlay.png")


if __name__ == "__main__":
    main()
