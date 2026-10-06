"""ZUZANA production set (style A): a 7-year-old girl in the manor park of Ivanka pri Dunaji, June 1962.

Built on npc_batch.py (NPC still set, face transplant, video idle, export) with three extras:
  * the base sheet takes a likeness reference: a family photo supplied by the owner. The photo is PRIVATE: it is
    read from art/source/owner_refs/ (git-ignored), sent to the generator as a data URI only (no upload to fal
    storage), never copied into art/characters/ and never named in a sidecar (sidecars say "family photo supplied
    by the owner");
  * a 'playing' loop (hopscotch hops on the spot, Hailuo-02 Pro, start = end = the standing idle) that keeps the
    video's vertical motion (the hops) instead of aligning every frame's lowest pixel to the feet line;
  * a crouching chalk-drawing pose (Pro edit of the base) with its own face frames and a Hailuo drawing loop,
    exported as the 'drawing' variant at the same scale as the standing figure (same head size).

Paid (fal.ai, logged to art/spend-log.csv under characters/ZUZANA/, refused beyond --budget):
  python zuzana_set.py --budget 6 sheet --take A --seed 1962
  python zuzana_set.py --budget 6 faces                 (blink, talk_a, talk_o, gesture on the chosen base)
  python zuzana_set.py --budget 6 crouch
  python zuzana_set.py --budget 6 crouch_faces
  python zuzana_set.py --budget 6 video --kind idle|hop|draw [--suffix _r2]
Free:
  python zuzana_set.py build | crouch_build | idle | hop | draw | export | preview
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

import chars
import fal_api
import frames as fr
import npc_batch as nb
from hero_coat import save_result

CID = "ZUZANA"
D = nb.CHAR_ROOT / CID
PHOTO = fal_api.ART / "source" / "owner_refs" / "family_zuzana.jpg"   # private, git-ignored, never copied
PHOTO_LABEL = "family photo supplied by the owner (private; not stored in the repository)"
SONA_KEYED = nb.CHAR_ROOT / "SONA" / "keyed" / "base_3q.png"
HAILUO_PRO = "fal-ai/minimax/hailuo-02/pro/image-to-video"

# The likeness note (how the generator should read the photo) lives next to the photo in the git-ignored
# art/source/owner_refs/, so no description of the private photo is committed. Sidecars store a placeholder.
LIKENESS_NOTE_FILE = PHOTO.with_name("family_zuzana_prompt_note.txt")
LIKENESS_PLACEHOLDER = "[likeness note on the family photo supplied by the owner; kept with the photo, not in the repository]"


def likeness_note() -> str:
    if not LIKENESS_NOTE_FILE.exists():
        sys.exit("the likeness note is not available locally")
    return LIKENESS_NOTE_FILE.read_text(encoding="utf-8").strip()


SONA_NOTE = (
    "The SECOND reference image shows another approved child character from our game, an 11-year-old girl: use it "
    "only for how children are painted and proportioned in this game. Our new girl is four years younger, clearly "
    "smaller and rounder in the face, and must not copy her face, hair, clothes or album."
)
VIEW_1962 = (
    "Paint a single full-body character for a point-and-click adventure game: {desc} "
    "Pose: standing relaxed in a three-quarter view turned toward the right, exactly like the approved character in "
    "the first reference image: body and face turned about 45 degrees toward the right edge of the image, both eyes "
    "visible, the near side of the body toward the viewer, both feet flat on the ground, weight evenly balanced, "
    "calm, serious expression with the mouth closed, eyes open. Hands and props exactly as described. Clothing, hair "
    "and shoes are period-correct for a Slovak village near Bratislava in the early 1960s, with no brand names, no "
    "logos and no readable text anywhere. Same framing as the first reference image: the figure is centred and "
    "fills about 80% of the image height."
)
CHILD7_RULES = chars.SPRITE_RULES.replace(
    "(head a little large, about 1/6.5 of the height), but still a believable adult.",
    "(head a little large), but clearly a believable 7-year-old child with a young child's body proportions: the "
    "head is about 1/5 of her height, short legs, short arms, narrow shoulders, a soft round child's face. She is "
    "a schoolchild of seven, not a toddler and not a teenager.")
POSE_LIGHT = (" Keep the face, hair colour, skin tone and the soft even lighting exactly as in the first image: no "
              "dappled light spots or sun patches on her or her clothes.")


def budget(cap: float) -> None:
    nb.BUDGET = nb.Budget(cap, [CID], None)


OLDER_NOTE = (
    "Age check: she is SEVEN, a first-grade schoolgirl, clearly older than in the photograph: her baby fat is "
    "mostly gone (the cheeks are still soft and round), her neck is visible, her arms and legs are slimmer and "
    "longer, the legs make up nearly half of her height, and the head is about 1/5.7 of her height. The skirt of "
    "the dress falls softly; it is not a stiff puffed skirt."
)


def sheet_prompt(take: str) -> str:
    brief = nb.brief_of(CID)
    notes = [chars.CAST_REF_NOTE]
    if take == "B":
        notes.append(SONA_NOTE)
    notes.append(likeness_note())
    parts = notes + [VIEW_1962.format(desc=brief["description"]), CHILD7_RULES]
    if take == "C":
        parts.append(OLDER_NOTE)
    return nb.finish(" ".join(parts), "green")


def paid_edit(model: str, prompt: str, refs: list, resolution: str, name: str, seed: int | None,
              ref_labels: list[str]) -> list[Path]:
    """One image edit; the sidecar lists ref_labels instead of paths (the private photo is never named)."""
    price = fal_api.IMAGE_PRICES[(model, resolution)]
    asset = f"characters/{CID}/{name}"
    nb.BUDGET.reserve(asset, price)
    try:
        arguments = {"prompt": prompt, "image_urls": [fal_api.image_data_uri(r, max_side=2048) for r in refs],
                     "aspect_ratio": "3:4", "resolution": resolution, "output_format": "png", "num_images": 1}
        if seed is not None:
            arguments["seed"] = seed
        result = fal_api.run(model, arguments, asset, price, budget=None, timeout_s=900)
    finally:
        nb.BUDGET.release(price)
    if LIKENESS_NOTE_FILE.exists():
        prompt = prompt.replace(likeness_note(), LIKENESS_PLACEHOLDER)
    meta = {"model": model, "usd": price, "prompt": prompt, "aspect_ratio": "3:4", "resolution": resolution,
            "references": ref_labels, "seed": seed}
    return save_result(result, D / name, meta)


def do_sheet(take: str, seed: int) -> list[Path]:
    if not PHOTO.exists():
        sys.exit("the owner's family photo is not available locally")
    cast = chars.cast_reference(nb.CAST_ANCHOR, "green", D)
    refs, labels = [cast], [str(cast.relative_to(fal_api.ART))]
    if take == "B":
        sona = chars.cast_reference(SONA_KEYED, "green", D)
        refs.append(sona)
        labels.append(str(sona.relative_to(fal_api.ART)))
    # the photo goes in as an in-memory crop of the girl (encoded straight to a data URI, no file is written)
    photo = Image.open(PHOTO).convert("RGB")
    crop = photo.crop((30, 20, 280, 470))
    crop = crop.resize((crop.width * 3, crop.height * 3), Image.Resampling.LANCZOS)
    refs.append(crop)
    labels.append(PHOTO_LABEL)
    return paid_edit(nb.PRO, sheet_prompt(take), refs, "2K", f"sheet_take{take}_s{seed}", seed, labels)


def do_crouch(seed: int, suffix: str = "", model: str = "nb2") -> list[Path]:
    """Pro returned the standing base unchanged for the first crouch prompt (take 1, rejected); NB2 follows pose
    changes better (PIPELINE.md section 2)."""
    brief = nb.brief_of(CID)
    prompt = nb.finish("Change the pose of the girl in the first image. She is no longer standing: " + brief["crouch"]
                       + " Same face, same hair, same navy dress with the white collar and the white buttons, same "
                       "white knee socks and brown sandals, same painting style, same flat green background."
                       + POSE_LIGHT, "green")
    mdl = nb.NB2 if model == "nb2" else nb.PRO
    return paid_edit(mdl, prompt, [nb.base_path(CID)], "2K", f"pose_crouch_{model}{suffix}", seed,
                     [str(nb.base_path(CID).relative_to(fal_api.ART))])


def crouch_base() -> Path:
    return D / "crouch_base.png"


def do_crouch_face(kind: str, seed: int, suffix: str = "") -> list[Path]:
    brief = nb.brief_of(CID)
    text = nb.FACE_PROMPTS[kind].format(**nb.words(brief))
    if kind == "blink":
        text = text.replace("closed in a natural blink", "closed in a natural blink (she looks down, so the lids "
                                                         "cover the eyes completely)")
    prompt = nb.finish(text, "green")
    return paid_edit(nb.NB2, prompt, [crouch_base()], "1K", f"crouch_{kind}_nb2{suffix}", seed,
                     [str(crouch_base().relative_to(fal_api.ART))])


CROUCH_GESTURE = (
    "She stays crouched in exactly the same position, on the same spot, with her feet, knees, dress and the chalk "
    "hand exactly where they are. She lifts only her free hand from her knee and points with the index finger toward "
    "the right and slightly down, at a spot on the ground a few steps ahead of her, and she glances that way. "
    "Exactly two arms and two hands, exactly one stick of chalk.")


def do_crouch_gesture(seed: int, suffix: str = "") -> list[Path]:
    prompt = nb.finish(nb.GESTURE_PROMPT.replace("standing on the same spot", "crouching on the same spot").format(
        **dict(nb.words(nb.brief_of(CID)), gesture=CROUCH_GESTURE)), "green")
    return paid_edit(nb.NB2, prompt, [crouch_base()], "2K", f"crouch_gesture_nb2{suffix}", seed,
                     [str(crouch_base().relative_to(fal_api.ART))])


VIDEO_SUFFIX = nb.IDLE_SUFFIX


def video_canvas(base: Path, out: Path, fig: float, feet: float, size: tuple[int, int]) -> Path:
    keyed = nb._CHROMA_KEY(fr.load_rgb(base))
    x0, y0, x1, y1 = fr.alpha_bbox(keyed)
    cx = fr.torso_center_x(keyed)
    w, h = size
    scale = h * fig / (y1 - y0)
    img = Image.fromarray(keyed, "RGBA").resize((round(keyed.shape[1] * scale), round(keyed.shape[0] * scale)),
                                                Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", size, (0, 255, 0))
    canvas.paste(img, (round(w / 2 - cx * scale), round(h * feet - y1 * scale)), img)
    canvas.save(out)
    meta = {"base": base.name, "scale": scale, "cx": cx, "feet_src": y1, "paste": [round(w / 2 - cx * scale),
            round(h * feet - y1 * scale)], "size": list(size), "fig": fig, "feet": feet}
    out.with_suffix(".json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return out


def do_video(kind: str, suffix: str = "") -> list[Path]:
    brief = nb.brief_of(CID)
    if kind == "hop":
        endpoint, res = HAILUO_PRO, "1080P"
        image = video_canvas(nb.base_path(CID), D / "video_in_hop.png", 0.62, 0.90, (1080, 1080))
        motion = brief["hop_motion"]
    elif kind == "idle":
        endpoint, res = nb.HAILUO, "768P"
        image = video_canvas(nb.base_path(CID), D / "video_in_3q.png", nb.VIDEO_FIG, nb.VIDEO_FEET, nb.VIDEO_CANVAS)
        motion = brief["idle_motion"]
    elif kind == "draw":
        endpoint, res = nb.HAILUO, "768P"
        image = video_canvas(crouch_base(), D / "video_in_crouch.png", 0.62, 0.86, nb.VIDEO_CANVAS)
        motion = brief["draw_motion"]
    else:
        raise ValueError(kind)
    prompt = motion + VIDEO_SUFFIX
    uri = fal_api.image_data_uri(image, fmt="PNG")
    arguments = {"prompt": prompt, "image_url": uri, "end_image_url": uri, "prompt_optimizer": False}
    if endpoint == nb.HAILUO:
        arguments.update(duration="6", resolution=res)
    price = fal_api.video_price(endpoint, 6.0, res)
    name = f"video_{kind}_loop{suffix}"
    asset = f"characters/{CID}/{name}"
    nb.BUDGET.reserve(asset, price)
    try:
        result = fal_api.run(endpoint, arguments, asset, price, budget=None, timeout_s=1800, poll_s=8)
    finally:
        nb.BUDGET.release(price)
    meta = {"model": endpoint, "usd": round(price, 4), "prompt": prompt, "input": image.name, "tail_image": True,
            "seconds": 6.0, "resolution": res,
            "arguments": {k: v for k, v in arguments.items() if not str(v).startswith("data:")}}
    return save_result(result, D / name, meta)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--budget", type=float, default=0.0)
    parser.add_argument("--seed", type=int, default=1962)
    parser.add_argument("--suffix", default="")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("cmd")
    parser.add_argument("--take", default="A")
    parser.add_argument("--kind")
    args = parser.parse_args()
    budget(args.budget)
    if args.cmd == "sheet":
        print(do_sheet(args.take, args.seed))
    elif args.cmd == "faces":
        jobs = [(k, lambda k=k: nb.do_face(CID, k, args.seed, args.suffix)) for k in ("blink", "talk_a", "talk_o")]
        jobs.append(("gesture", lambda: nb.do_gesture(CID, args.seed, args.suffix)))
        nb.run_jobs(jobs, args.workers)
    elif args.cmd == "face":
        print(nb.do_face(CID, args.kind, args.seed, args.suffix))
    elif args.cmd == "gesture":
        print(nb.do_gesture(CID, args.seed, args.suffix))
    elif args.cmd == "crouch":
        print(do_crouch(args.seed, args.suffix, args.kind or "nb2"))
    elif args.cmd == "crouch_faces":
        kinds = args.kind.split(",") if args.kind else ["blink", "talk_a", "talk_o", "gesture"]
        nb.run_jobs([(k, lambda k=k: (do_crouch_gesture(args.seed, args.suffix) if k == "gesture" else
                                      do_crouch_face(k, args.seed, args.suffix))) for k in kinds], args.workers)
    elif args.cmd == "video":
        print(do_video(args.kind, args.suffix))
    else:
        import zuzana_build
        zuzana_build.run(args)


if __name__ == "__main__":
    main()
