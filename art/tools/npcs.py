"""NPC sprite generation for LastBell (style A) via fal.ai, built on chars.py / fal_api.py.

NPCs use one house view: a three-quarter view facing right, with the approved hero sprite (ADAM) as the cast
style anchor (PIPELINE.md section 3.2). Face frames are pronoun- and face-mask-aware (2020 characters keep the
mask on while speaking), the gesture and the idle motion come from each brief in art/characters/characters.json.

Subcommands (paid, logged to art/spend-log.csv, refused once the task budget would be exceeded):
  sheet  <char>                       base sheet: Pro 2K 3:4, cast anchor = ADAM keyed 3/4 sprite
  pose   <char> blink|talk|talk_oh|gesture|seated --base SHEET
                                      NB2 edit (face frames 1K, gesture 2K); talk/talk_oh switch to the masked
                                      variants for masked characters
  fix    <char> --base SHEET --instruction TEXT --out NAME
                                      NB2 edit that changes one design detail (keeps the rest)
  video  <char> --image CANVAS        Hailuo-02 768p 6 s idle loop (start = end frame)

Budget: --budget USD over --budget-scope prefixes (comma-separated) counted from --budget-since (ISO time).

Run from art/tools, for example:
  python npcs.py sheet DANA
  python npcs.py pose DANA blink --base ../characters/DANA/sheet_npc_3q.png
  python npcs.py video DANA --image ../characters/DANA/video_in_3q.png
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import chars
import fal_api

ART = fal_api.ART
CHAR_ROOT = ART / "characters"
CAST_ANCHOR = CHAR_ROOT / "ADAM" / "keyed" / "side_right_3q.png"

PRONOUNS = {"he": {"subj": "he", "pos": "his", "obj": "him"}, "she": {"subj": "she", "pos": "her", "obj": "her"}}

VIEW_NPC_3Q = (
    "Paint a single full-body character for a point-and-click adventure game: {desc} "
    "Pose: standing relaxed in a three-quarter view turned toward the right, exactly like the approved character in "
    "the first reference image: body and face turned about 45 degrees toward the right edge of the image, both eyes "
    "visible, the near side of the body toward the viewer, both feet flat on the ground, weight evenly balanced, "
    "calm neutral expression, eyes open. Hands and props exactly as described in the brief. Same framing and scale "
    "as the first reference image: the figure is centred and fills about 80% of the image height."
)

KEEP = ("Edit the first image: keep everything exactly the same (same character, same pose, same position and size "
        "in the frame, same clothes, same colours, same flat green background{mask_keep})")

FACE_PROMPTS = {
    "blink": KEEP + " and change ONLY {pos} eyes: they are closed in a natural blink{glasses}. Do not move or redraw "
                    "anything else.",
    "talk": KEEP + " and change ONLY {pos} mouth: {subj} is in the middle of speaking, mouth clearly open as if saying "
                   "'ah', a slightly animated expression, eyebrows a little raised. Do not move or redraw anything else.",
    "talk_oh": KEEP + " and change ONLY {pos} mouth to a small rounded 'oh' shape, as in mid-speech, with a lively, "
                      "attentive look. Do not move or redraw anything else.",
    "talk_masked": KEEP + " and change ONLY the face: {subj} is in the middle of speaking behind the mask. The jaw is "
                          "clearly lowered, so the lower half of the mask is pulled down and stretched, with a soft "
                          "horizontal fold across the mask; the cheeks lift a little and the eyebrows rise in an "
                          "animated, talking expression. Do not move or redraw anything else.",
    "talk_oh_masked": KEEP + " and change ONLY the face: {subj} is saying a short rounded 'oh' behind the mask. The jaw "
                             "is a little lowered, the mask fabric is pushed slightly forward with a small soft dent "
                             "over the rounded lips, and the eyebrows are drawn slightly together in a thoughtful, "
                             "speaking expression. Do not move or redraw anything else.",
}

GESTURE_PROMPT = (
    "Edit the first image: the same character, same face, same clothes, same colours, same scale, same flat green "
    "background, the same three-quarter view facing right, standing on the same spot with the feet in exactly the "
    "same place. Change only the pose of the arms and hands: {gesture} Keep the head, the face{mask_word}, the hair, "
    "the body, the legs and the feet unchanged, and keep the whole figure inside the frame."
)

SEATED_PROMPT = (
    "Edit the first image: the same character, same face, same hair, same clothes, same colours, same scale, same "
    "flat green background, the same three-quarter view facing right. Change only the posture: {seated} Keep the "
    "whole figure, including the seat, inside the frame."
)

# Seated characters (brief 'posture': 'seated'): gesture edits keep the seat instead of the standing feet.
LIGHT_GUARD = ("Keep the soft even lighting of the first image: no dappled light spots, sun patches or leaf shadows on the "
               "character, the clothes or the seat.")

SEATED_GESTURE_SWAP = ("standing on the same spot with the feet in exactly the same place",
                       "sitting on the same seat in exactly the same place, the seat and the feet unchanged")

IDLE_SUFFIX = (
    " The character keeps the same position, facing and scale. Seamless loop. The camera is completely static. The "
    "background stays a perfectly flat uniform green, nothing else appears. Same hand-painted style throughout."
)


# ----------------------------------------------------------------------------- budget

def task_spend(prefixes: tuple[str, ...], since: str | None) -> float:
    if not fal_api.SPEND_LOG.exists():
        return 0.0
    with fal_api.SPEND_LOG.open(encoding="utf-8") as handle:
        return sum(float(row["usd"]) for row in csv.DictReader(handle)
                   if row["asset"].startswith(prefixes) and (since is None or row["timestamp"] >= since))


def guard(args: argparse.Namespace, asset: str, usd: float) -> None:
    prefixes = tuple(p for p in args.budget_scope.split(",") if p)
    spent = task_spend(prefixes, args.budget_since)
    if spent + usd > args.budget + 1e-9:
        sys.exit(f"BUDGET: {asset}: {spent:.3f} + {usd:.3f} USD would exceed the {args.budget:.2f} USD task cap")
    print(f"[budget] {spent:.3f} spent of {args.budget:.2f}; this call {usd:.3f}", file=sys.stderr)


# ----------------------------------------------------------------------------- helpers

def load_brief(char_id: str) -> dict:
    briefs = json.loads((CHAR_ROOT / "characters.json").read_text(encoding="utf-8"))
    if char_id not in briefs:
        sys.exit(f"{char_id} has no brief in art/characters/characters.json")
    return briefs[char_id]


def key_of(brief: dict) -> str:
    return brief.get("key", "green")


def words_of(brief: dict) -> dict:
    masked = bool(brief.get("masked"))
    return dict(PRONOUNS[brief.get("pronoun", "he")], gesture=brief.get("gesture", ""),
                mask_keep="; the light blue face mask stays on and still covers the nose and mouth" if masked else "",
                mask_word=", the face mask" if masked else "",
                glasses=" behind the glasses" if "glasses" in brief.get("description", "").lower()
                and "round" in brief.get("description", "").lower() else "")


def edit(args: argparse.Namespace, model_key: str, prompt: str, refs: list[Path], aspect: str, resolution: str,
         asset: str, out_base: Path) -> list[Path]:
    model = chars.IMAGE_MODELS[model_key]
    price = fal_api.IMAGE_PRICES[(model, resolution)]
    guard(args, asset, price)
    arguments = {"prompt": prompt, "image_urls": chars.image_inputs(refs, None), "aspect_ratio": aspect,
                 "resolution": resolution, "output_format": "png", "num_images": 1}
    if args.seed is not None:
        arguments["seed"] = args.seed
    result = fal_api.run(model, arguments, asset, price, budget=None, timeout_s=600)
    meta = {"model": model, "usd": price, "prompt": prompt, "aspect_ratio": aspect, "resolution": resolution,
            "references": [str(r.relative_to(ART)) for r in refs], "style_reference": None, "seed": args.seed}
    return chars.save_outputs(result, out_base, meta)


# ----------------------------------------------------------------------------- commands

def cmd_sheet(args: argparse.Namespace) -> None:
    brief = load_brief(args.char)
    key = key_of(brief)
    cast = chars.cast_reference(CAST_ANCHOR, key, CHAR_ROOT / args.char)
    prompt = " ".join([chars.CAST_REF_NOTE, VIEW_NPC_3Q.format(desc=brief["description"]), chars.SPRITE_RULES,
                       chars.key_background(key), chars.STYLE_FOR_CHARACTER + chars.STYLE_A])
    prompt = chars.recolour_key_words(prompt, key).replace("with green margin", f"with {key} margin")
    name = args.out or "sheet_npc_3q"
    paths = edit(args, args.model, prompt, [cast], "3:4", args.res, f"characters/{args.char}/{name}",
                 CHAR_ROOT / args.char / name)
    print("\n".join(str(p) for p in paths))


def cmd_pose(args: argparse.Namespace) -> None:
    brief = load_brief(args.char)
    key = key_of(brief)
    words = words_of(brief)
    if args.pose == "gesture":
        if not words["gesture"]:
            sys.exit(f"{args.char} has no 'gesture' in characters.json")
        template, res = GESTURE_PROMPT, args.res or "2K"
        if brief.get("posture") == "seated":
            template = template.replace(*SEATED_GESTURE_SWAP)
        template += " " + LIGHT_GUARD
    elif args.pose == "seated":
        if not brief.get("seated"):
            sys.exit(f"{args.char} has no 'seated' in characters.json")
        template, res = SEATED_PROMPT.replace("{seated}", brief["seated"]) + " " + LIGHT_GUARD, args.res or "2K"
    else:
        name = args.pose + ("_masked" if brief.get("masked") and args.pose.startswith("talk") else "")
        template, res = FACE_PROMPTS[name], args.res or "1K"
    prompt = (template.format(**words) + " " + chars.key_background(key) + " " + chars.STYLE_FOR_CHARACTER
              + chars.STYLE_A)
    prompt = chars.recolour_key_words(prompt, key)
    out = args.out or f"pose_{args.pose}_nb2"
    paths = edit(args, args.model, prompt, [Path(args.base).resolve()], "3:4", res, f"characters/{args.char}/{out}",
                 CHAR_ROOT / args.char / out)
    print("\n".join(str(p) for p in paths))


def cmd_fix(args: argparse.Namespace) -> None:
    """Design-fidelity fix of a sheet (one NB2 edit with a free-text instruction, e.g. era-correct boots)."""
    brief = load_brief(args.char)
    key = key_of(brief)
    prompt = (KEEP.format(**words_of(brief)) + " and change ONLY this: " + args.instruction + " Do not move or "
              "redraw anything else. " + chars.key_background(key) + " " + chars.STYLE_FOR_CHARACTER + chars.STYLE_A)
    prompt = chars.recolour_key_words(prompt, key)
    paths = edit(args, "nb2", prompt, [Path(args.base).resolve()], "3:4", args.res,
                 f"characters/{args.char}/{args.out}", CHAR_ROOT / args.char / args.out)
    print("\n".join(str(p) for p in paths))


def cmd_video(args: argparse.Namespace) -> None:
    brief = load_brief(args.char)
    key = key_of(brief)
    endpoint = "fal-ai/minimax/hailuo-02/standard/image-to-video"
    prompt = chars.recolour_key_words(brief.get("idle_motion", chars.MOTION_PROMPTS["idle"]) + IDLE_SUFFIX, key)
    image_uri = fal_api.image_data_uri(Path(args.image), fmt="PNG")
    arguments = {"prompt": prompt, "image_url": image_uri, "end_image_url": image_uri, "duration": "6",
                 "resolution": "768P", "prompt_optimizer": False}
    price = fal_api.video_price(endpoint, 6.0, "768P")
    name = args.out or "video_idle_hailuo_loop"
    asset = f"characters/{args.char}/{name}"
    guard(args, asset, price)
    result = fal_api.run(endpoint, arguments, asset, price, budget=None, timeout_s=1500, poll_s=8)
    meta = {"model": endpoint, "usd": round(price, 4), "prompt": prompt, "input": Path(args.image).name,
            "tail_image": True, "seconds": 6.0, "resolution": "768P",
            "arguments": {k: v for k, v in arguments.items() if not str(v).startswith("data:")}}
    paths = chars.save_outputs(result, CHAR_ROOT / args.char / name, meta)
    print("\n".join(str(p) for p in paths))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--budget", type=float, required=True, help="USD cap of the task")
    parser.add_argument("--budget-scope", required=True, help="comma-separated spend-log asset prefixes")
    parser.add_argument("--budget-since", help="ISO timestamp: only spend logged from then on counts")
    parser.add_argument("--seed", type=int, default=1985)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("sheet")
    p.add_argument("char")
    p.add_argument("--model", choices=chars.IMAGE_MODELS, default="pro")
    p.add_argument("--res", default="2K")
    p.add_argument("--out")
    p.set_defaults(func=cmd_sheet)

    p = sub.add_parser("pose")
    p.add_argument("char")
    p.add_argument("pose", choices=["blink", "talk", "talk_oh", "gesture", "seated"])
    p.add_argument("--base", required=True)
    p.add_argument("--model", choices=chars.IMAGE_MODELS, default="nb2")
    p.add_argument("--res")
    p.add_argument("--out")
    p.set_defaults(func=cmd_pose)

    p = sub.add_parser("fix")
    p.add_argument("char")
    p.add_argument("--base", required=True)
    p.add_argument("--instruction", required=True)
    p.add_argument("--res", default="2K")
    p.add_argument("--out", required=True)
    p.set_defaults(func=cmd_fix)

    p = sub.add_parser("video")
    p.add_argument("char")
    p.add_argument("--image", required=True)
    p.add_argument("--out")
    p.set_defaults(func=cmd_video)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
