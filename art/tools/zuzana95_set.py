"""ZUZANA95 (Zuzana at 40, Sokolikovsky dvor S69, 15 June 1995) and KUBO (a first-grader of the estate, 7) production
sets, style A. Specs: docs/story/SOKOLIKOVA_YARD.md section 2 and 6.2, docs/story/ZUZANA.md sections 6.1 and 10.

Built on npc_batch.py (still set with face transplants, video idle, export); paid calls go through the content v2
task guard (art/tools/content_v2_budget.py). Sheets:
  * ZUZANA95: Nano Banana Pro 2K edit with ADAM's keyed 3/4 sprite as the cast anchor (FIRST), the approved
    7-year-old ZUZANA sheet as the identity reference (SECOND: the same person 33 years later) and the family photo
    supplied by the owner LAST, exactly as for the child: read from the git-ignored art/source/owner_refs/, sent as
    an in-memory data URI only, never copied, never named in a sidecar; its likeness note stays next to the photo.
    Nothing in the brief implies a life fact: no ring, no jewellery, no watch, no glasses, no bag, no work clothes.
  * KUBO: Pro 2K edit with ADAM's cast anchor and the approved ZUZANA (7) sheet as the reference for how a child of
    seven is proportioned in this game (not for her face, hair or clothes).

  python zuzana95_set.py sheet ZUZANA95 [--take A --seed N]      (USD 0.15)
  python zuzana95_set.py sheet KUBO [--seed N]
  python zuzana95_set.py faces ZUZANA95|KUBO                     (blink, talk_a, talk_o NB2 1K + gesture NB2 2K: 0.36)
  python zuzana95_set.py face ZUZANA95 --kind blink [--suffix _r2]
  python zuzana95_set.py gesture KUBO [--suffix _r2]
  python zuzana95_set.py video ZUZANA95|KUBO [--suffix _r2]      (Hailuo-02 768p 6 s: 0.27)
Free: build / idle / export / review go straight to npc_batch.py (python npc_batch.py build ZUZANA95 ...).
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

from PIL import Image

import chars
import content_v2_budget as guard
import fal_api
import npc_batch as nb

PHOTO = fal_api.ART / "source" / "owner_refs" / "family_zuzana.jpg"   # private, git-ignored, never copied
PHOTO_LABEL = "family photo supplied by the owner (private; not stored in the repository)"
NOTE_95 = PHOTO.with_name("family_zuzana95_prompt_note.txt")          # private, next to the photo
NOTE_PLACEHOLDER = "[likeness note on the family photo supplied by the owner; kept with the photo, not in the repository]"
ZUZANA7_KEYED = nb.CHAR_ROOT / "ZUZANA" / "keyed" / "base_3q.png"


class _Adapter:
    """npc_batch's BUDGET interface on top of the content v2 task guard."""

    def reserve(self, asset: str, usd: float) -> None:
        guard.reserve(asset, usd)

    def release(self, usd: float) -> None:
        guard.release(usd)


nb.BUDGET = _Adapter()

IDENTITY_NOTE = (
    "The SECOND reference image shows this same person as a seven-year-old girl: the approved child version of her "
    "in our game, in June 1962. It is her identity reference. Paint her 33 years later, at forty, as a grown woman, "
    "clearly the same person: the same soft round face shape (now a woman's face, the cheeks still soft and round, a "
    "few faint smile lines at the outer corners of the eyes), the same gentle, serious, attentive dark brown eyes, "
    "the same straight light-brown eyebrows, the same small nose, the same small mouth with the slightly full lower "
    "lip, the same light-brown hair colour and the same side parting with the longer side swept across the top of "
    "the forehead. Do not copy her child's dress, socks or sandals and do not make her look like a child."
)

KUBO_CHILD_NOTE = (
    "The SECOND reference image shows another approved child character from our game, a seven-year-old girl: use "
    "it only for how a child of seven is proportioned and painted in this game (head size, short legs, short arms, "
    "narrow shoulders, the soft round child's face, the scale of the figure in the frame). Our new character is a "
    "boy of the same age; do not copy her face, hair, dress, socks or sandals."
)

VIEW_1995 = (
    "Paint a single full-body character for a point-and-click adventure game: {desc} "
    "Pose: standing relaxed in a three-quarter view turned toward the right, exactly like the approved character in "
    "the first reference image: body and face turned about 45 degrees toward the right edge of the image, both eyes "
    "visible, the near side of the body toward the viewer, both feet flat on the ground, weight evenly balanced, "
    "{expression} Hands and props exactly as described. Clothing, hair and shoes are period-correct for a Bratislava "
    "housing estate in the summer of 1995, with no brand names, no logos and no readable text anywhere. Same framing "
    "as the first reference image: the figure is centred and fills about 80% of the image height."
)

ADULT_RULES = chars.SPRITE_RULES + (
    " She is an ordinary woman of forty with a natural slim build and medium height: not glamorous, no make-up "
    "look, no jewellery, no rings, no earrings, no watch, no glasses, no bag."
)

CHILD7_BOY_RULES = chars.SPRITE_RULES.replace(
    "(head a little large, about 1/6.5 of the height), but still a believable adult.",
    "(head a little large), but clearly a believable 7-year-old child with a young child's body proportions: the "
    "head is about 1/5.3 of his height, short legs, short arms, narrow shoulders, a soft round child's face. He is "
    "a schoolboy of seven who is just finishing first grade, not a toddler and not a teenager.")


def note_95() -> str:
    if not NOTE_95.exists():
        sys.exit("the private likeness note for ZUZANA95 is not available locally")
    return NOTE_95.read_text(encoding="utf-8").strip()


def sheet_prompt(cid: str) -> str:
    brief = nb.brief_of(cid)
    if cid == "ZUZANA95":
        parts = [chars.CAST_REF_NOTE, IDENTITY_NOTE, note_95(),
                 VIEW_1995.format(desc=brief["description"],
                                  expression="a calm, kind expression with the hint of a small warm smile, the mouth "
                                             "closed, eyes open."),
                 ADULT_RULES]
    else:
        parts = [chars.CAST_REF_NOTE, KUBO_CHILD_NOTE,
                 VIEW_1995.format(desc=brief["description"],
                                  expression="a lively but slightly offended expression with the mouth closed, eyes "
                                             "open."),
                 CHILD7_BOY_RULES]
    return nb.finish(" ".join(parts), nb.key_of(brief))


def do_sheet(cid: str, take: str, seed: int) -> list[Path]:
    d = nb.cdir(cid)
    cast = chars.cast_reference(nb.CAST_ANCHOR, "green", d)
    child = chars.cast_reference(ZUZANA7_KEYED, "green", d)
    refs = [cast, child]
    labels = [str(cast.relative_to(fal_api.ART)), str(child.relative_to(fal_api.ART))
              + (" (identity: the same person at 7)" if cid == "ZUZANA95" else " (child proportions only)")]
    if cid == "ZUZANA95":
        if not PHOTO.exists():
            sys.exit("the owner's family photo is not available locally")
        photo = Image.open(PHOTO).convert("RGB")
        crop = photo.crop((30, 20, 280, 470))                    # the girl, as for the child sheet
        refs.append(crop.resize((crop.width * 3, crop.height * 3), Image.Resampling.LANCZOS))
        labels.append(PHOTO_LABEL)
    prompt = sheet_prompt(cid)
    name = f"sheet_take{take}_s{seed}"
    price = fal_api.IMAGE_PRICES[(nb.PRO, "2K")]
    asset = f"characters/{cid}/{name}"
    arguments = {"prompt": prompt, "image_urls": [fal_api.image_data_uri(r, max_side=2048) for r in refs],
                 "aspect_ratio": "3:4", "resolution": "2K", "output_format": "png", "num_images": 1, "seed": seed}
    result = guard.run(nb.PRO, arguments, asset, price, timeout_s=900)
    if cid == "ZUZANA95":
        prompt = prompt.replace(note_95(), NOTE_PLACEHOLDER)
    meta = {"model": nb.PRO, "usd": price, "prompt": prompt, "aspect_ratio": "3:4", "resolution": "2K",
            "references": labels, "seed": seed}
    return chars.save_outputs(result, d / name, meta)


def choose(cid: str, name: str) -> None:
    """Copy a sheet take to the pipeline's base name sheet_npc_3q.png (+ sidecar)."""
    d = nb.cdir(cid)
    for ext in (".png", ".json"):
        src = d / f"{name}{ext}"
        if src.exists():
            shutil.copyfile(src, d / f"sheet_npc_3q{ext}")
    print(f"{cid}: base = {name}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["sheet", "choose", "faces", "face", "gesture", "video"])
    ap.add_argument("cid", choices=["ZUZANA95", "KUBO"])
    ap.add_argument("--take", default="A")
    ap.add_argument("--seed", type=int, default=1995)
    ap.add_argument("--kind")
    ap.add_argument("--suffix", default="")
    ap.add_argument("--name")
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()
    if args.cmd == "sheet":
        print(do_sheet(args.cid, args.take, args.seed))
    elif args.cmd == "choose":
        choose(args.cid, args.name)
    elif args.cmd == "faces":
        jobs = [(k, lambda k=k: nb.do_face(args.cid, k, args.seed, args.suffix)) for k in ("blink", "talk_a", "talk_o")]
        jobs.append(("gesture", lambda: nb.do_gesture(args.cid, args.seed, args.suffix)))
        nb.run_jobs(jobs, args.workers)
    elif args.cmd == "face":
        print(nb.do_face(args.cid, args.kind, args.seed, args.suffix))
    elif args.cmd == "gesture":
        print(nb.do_gesture(args.cid, args.seed, args.suffix))
    elif args.cmd == "video":
        print(nb.do_video(args.cid, args.suffix))


if __name__ == "__main__":
    main()
