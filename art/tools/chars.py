"""Character art generation for LastBell (style A) via fal.ai. Pipeline notes: art/characters/PIPELINE.md.

Subcommands (all paid, all logged to art/spend-log.csv, all refused once --budget would be exceeded):
  view   <char> <view>            model-sheet view on a flat chroma-key background
                                  views: side_right, profile, turnaround (front | side | back), front, back
  pose   <char> <pose> --base IMG pose edit of an existing sheet (talk, talk_oh, blink, mask2020, reach_mid)
  video  <char> --image IMG       image-to-video on the flat key background (walk, walk_toward, walk_away,
                                  idle loops with --tail; pose transitions with --end KEYPOSE)

Outputs go to art/characters/<char>/ with a JSON sidecar (model, prompt, inputs, seed, price) per file.
Character briefs come from art/characters/characters.json (English, derived from game.json).
Local processing (keying, loops, spritesheets) is in frames.py and costs nothing.

Examples (run from art/tools):
  python chars.py view ADAM side_right                                   # first sheet: background as style ref
  python chars.py view ADAM turnaround --ref ../characters/ADAM/sheet_side_right.png
  python chars.py view ADAM profile --model nb2 --ref ../characters/ADAM/sheet_turnaround.png
  python chars.py view ELA side_right --key magenta --cast-ref ../characters/ADAM/keyed/side_right_3q.png
  python chars.py pose ADAM talk --base ../characters/ADAM/sheet_profile_nb2.png --model nb2 --res 1K
  python chars.py video ADAM --image ../characters/ADAM/video_in_profile_1080.png --engine hailuo_pro \
      --motion walk --tail
  python chars.py video ADAM --image ../characters/ADAM/video_in_reach_start.png \
      --end ../characters/ADAM/video_in_reach_end.png --engine hailuo --motion reach
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import fal_api

ART = fal_api.ART
CHAR_ROOT = ART / "characters"
STYLE_REF_DEFAULT = ART / "backgrounds" / "tram-stop.png"
DEFAULT_BUDGET = ("characters/", 6.00)  # hard cap for the character prototype

# Canonical style prompt from design-doc/ART_DIRECTION.md section 1 (must be appended verbatim).
STYLE_A = (
    "Style: classic 1990s hand-painted adventure game background. Rich painterly brushwork, slightly "
    "exaggerated cartoon proportions with gently curved lines, warm late-afternoon sunlight, saturated but "
    "harmonious colours, soft dappled shadows under the trees."
)

IMAGE_MODELS = {"pro": "fal-ai/nano-banana-pro/edit", "nb2": "fal-ai/nano-banana-2/edit"}

CAST_REF_NOTE = (
    "The FIRST reference image shows a different, already approved character from our game. Use it only as the "
    "reference for how characters are drawn and painted in this game: painting technique, soft outlines, body and "
    "head proportions, level of detail, lighting and colour palette. Do not copy his face, hair, clothes or bag."
)

STYLE_REF_NOTE = (
    "The LAST reference image is a finished background painting from our game. Use it only as the reference for "
    "the painting technique: brushwork, colour palette, edge softness, level of detail and line quality. Do not "
    "copy anything from its scene into the new image."
)

KEY_COLOURS = {"green": ("green", "#00FF00"), "magenta": ("magenta", "#FF00FF")}


def key_background(key: str = "green") -> str:
    """Background instruction for a flat chroma-key colour (magenta for characters who wear green)."""
    word, hex_code = KEY_COLOURS[key]
    return (f"Background: one perfectly flat, uniform, pure chroma-key {word} ({hex_code}) filling the entire image, "
            "edge to edge, with no gradient, no texture, no floor line, no cast shadow, no vignette, no props and no "
            f"text. The character must have crisp clean edges against the {word}, with no {word} tint, glow or "
            "reflection on the character.")


def recolour_key_words(prompt: str, key: str) -> str:
    """Pose and motion prompts say 'green'; swap the word when another key colour is used."""
    if key == "green":
        return prompt
    return (prompt.replace("flat green background", f"flat {key} background")
            .replace("keep the background flat green", f"keep the background flat {key}")
            .replace("uniform green", f"uniform {key}"))

SPRITE_RULES = (
    "The figure is a game sprite: the complete body from the top of the hair to the soles of the shoes is visible, "
    "with green margin on every side; both feet stand on the same invisible ground line. Even, soft, warm daylight "
    "from the front-left, no strong cast shadows, so the sprite fits many scenes. Slightly exaggerated cartoon "
    "proportions as in classic 1990s adventure games (head a little large, about 1/6.5 of the height), "
    "but still a believable adult."
)

STYLE_FOR_CHARACTER = (
    "Paint the character in the game's style. The following style line describes the whole game; apply its "
    "brushwork, proportions and palette to the character only and keep the background flat green: "
)

VIEW_PROMPTS = {
    "side_right": (
        "Paint a single full-body character for a point-and-click adventure game: {desc} "
        "Pose: standing relaxed in an exact 90-degree side view (true profile, not three-quarter): the chest points at "
        "the right edge of the image, the shoulders are seen edge-on and only one eye is visible; arms hanging "
        "naturally at the sides, both feet flat on the ground, weight evenly balanced, neutral calm expression with "
        "the mouth closed. The figure is centred and fills about 80% of the image height."
    ),
    "turnaround": (
        "The FIRST reference image shows our character, {name}, in side view. Paint a character turnaround model sheet of "
        "exactly the same man: the same face, hair, clothes, colours, bag, body proportions and painting style. "
        "Three full-body views side by side, evenly spaced, all at exactly the same scale and with the feet of all "
        "three on the same horizontal ground line: on the left a FRONT view facing the viewer, in the middle an exact "
        "90-degree PROFILE view facing right (chest pointing at the right edge of the image, shoulders seen edge-on, "
        "only one eye visible), on the right a BACK view facing away from the viewer. Neutral standing pose, arms "
        "relaxed at his sides. Each figure is about 80% of the image height. No labels, no arrows, no text. "
        "Brief, for reference: {desc}"
    ),
    "profile": (
        "The FIRST reference image is the model sheet of our character, {name}. Paint exactly the same man (same face, "
        "hair, clothes, colours, bag, proportions and painting style) as a single full-body PROFILE view facing "
        "right, like the side view of a walk-cycle reference drawing: an exact 90-degree side view, not "
        "three-quarter. His nose and chest point at the right edge of the image, the shoulders are seen edge-on so "
        "the torso looks narrow, only his left side, left arm and left ear are visible, only one eye is visible. "
        "Standing upright and relaxed, arms hanging at his sides, feet together flat on the ground, mouth closed. "
        "The figure is centred and fills about 80% of the image height. Brief, for reference: {desc}"
    ),
    # Design-fidelity fix of an existing side view (ADAM production set): the jacket must hang open over the
    # mustard T-shirt so the T-shirt reads in profile too; the first reference is edited, the second one only
    # shows the clothes.
    "side_open": (
        "The FIRST reference image shows our hero, {name}, in side view facing right; edit it. Keep exactly the same "
        "man: the same face, hair, head angle, expression, body proportions, scale and position in the frame, the "
        "same dark grey-blue jeans, brown leather shoes and brown leather messenger bag, and the same hand-painted "
        "look. The SECOND reference image shows the same man from a three-quarter angle; use it only as the reference "
        "for his clothes. Correct his clothes to match the brief: his mid-blue cotton work jacket is completely "
        "unbuttoned and worn open, its two front edges hanging apart and falling back, so that his plain "
        "mustard-yellow crew-neck T-shirt is clearly visible as a broad strip on his chest and stomach, from the "
        "neckline down to the belt; the mustard T-shirt must read clearly even when the figure is small. Turn his "
        "chest and shoulders just slightly toward the viewer (about 20 degrees from a pure profile) so that the open "
        "jacket front and the T-shirt show; his head, hips, legs and feet stay in side view facing right. The bag "
        "strap runs from his far shoulder diagonally across the T-shirt down to the bag on his near hip, as in the "
        "first image. Arms hang relaxed at his sides, both feet flat on the ground, mouth closed. "
        "Brief, for reference: {desc}"
    ),
    "profile_open": (
        "The FIRST reference image shows our hero, {name}, with the correct clothes: the blue work jacket worn open "
        "over the mustard-yellow T-shirt. The SECOND reference image shows the body angle we need. Paint exactly the "
        "same man as in the first image (same face, hair, clothes, colours, bag, proportions, scale and painting "
        "style) in the body angle of the second image: a near-profile side view facing right, his nose pointing at "
        "the right edge of the image and only one eye visible, his chest turned only slightly toward the viewer "
        "(about 15 degrees from a pure profile). The open jacket front hangs back from his chest, so a clear "
        "vertical strip of the mustard-yellow T-shirt shows on his chest and stomach between the jacket edge and "
        "the front of his body, from the neckline to the belt; the bag strap crosses it diagonally to the bag on "
        "his near hip. Standing upright and relaxed, arms hanging at his sides, feet flat on the ground, mouth "
        "closed. The figure is centred and fills about 80% of the image height. Brief, for reference: {desc}"
    ),
    "front": (
        "The FIRST reference image shows our character, {name}. Paint exactly the same man (same face, hair, clothes, "
        "colours, bag, proportions and painting style) as a single full-body FRONT view, standing relaxed and facing "
        "the viewer, arms at his sides, feet slightly apart. Same scale as the reference: the figure fills about 80% "
        "of the image height. Brief, for reference: {desc}"
    ),
    "back": (
        "The FIRST reference image shows our character, {name}. Paint exactly the same man (same hair, clothes, colours, "
        "bag strap, proportions and painting style) as a single full-body BACK view, standing relaxed and facing "
        "away from the viewer, arms at his sides. Same scale as the reference: the figure fills about 80% of the "
        "image height. Brief, for reference: {desc}"
    ),
}

POSE_PROMPTS = {
    "talk": (
        "Edit the first image: keep everything exactly the same (same character, same pose, same position and size "
        "in the frame, same clothes, same colours, same flat green background) and change ONLY his mouth: he is in "
        "the middle of speaking, mouth clearly open as if saying 'ah', a slightly animated expression, eyebrows a "
        "little raised. Do not move or redraw anything else."
    ),
    "talk_oh": (
        "Edit the first image: keep everything exactly the same (same character, pose, position, size, clothes, "
        "colours and flat green background) and change ONLY his mouth to a small rounded 'oh' shape, as in "
        "mid-speech. Do not move or redraw anything else."
    ),
    "blink": (
        "Edit the first image: keep everything exactly the same (same character, pose, position, size, clothes, "
        "colours and flat green background) and change ONLY his eyes: they are closed in a natural blink. "
        "Do not move or redraw anything else."
    ),
    "mask2020": (
        "Edit the first image: keep everything exactly the same (same character, pose, position, size, clothes, "
        "colours and flat green background) and add ONLY a light blue disposable surgical face mask covering his "
        "nose, mouth and chin, with a thin white ear loop over his visible ear. Do not move or redraw anything else."
    ),
    "reach_mid": (
        "Edit the first image: the same character, same clothes, same colours, same scale, same flat green "
        "background, still in exact side view facing right and standing on the same spot with his feet in the same "
        "place. Change his pose: he reaches forward with his right arm extended straight out at chest height, the "
        "open hand about to take or operate something in front of him (for example a door handle or a switch on a "
        "wall), his body leaning very slightly forward, the other arm relaxed. Nothing in his hand, no object in "
        "front of him."
    ),
    "open_jacket": (
        "Edit the first image: keep the same man in exactly the same near-profile pose and angle, same face, hair, "
        "expression, position and size in the frame, same jeans, shoes and bag, same flat green background. The "
        "SECOND image shows the same man with the correct clothes; use it only as the reference for the clothes. "
        "Change ONLY his clothes: his mid-blue work jacket is completely unbuttoned and hangs open, its front edge "
        "swung back from his chest, so that his plain mustard-yellow crew-neck T-shirt shows clearly as a broad "
        "vertical strip on his chest and stomach, from the neckline to the belt, between the jacket edge and the "
        "front of his body; turn his chest just a few degrees toward the viewer if needed so the mustard T-shirt "
        "reads clearly at small size. The bag strap still crosses the T-shirt diagonally to the bag on his near hip. "
        "Do not change his head, legs or feet."
    ),
    "open_jacket_solo": (
        "Edit the first image: keep the same man in exactly the same near-profile pose and angle facing right, the "
        "same face, hair, expression, position and size in the frame, the same jeans, shoes and bag, the same flat "
        "green background. Change ONLY his jacket: the mid-blue work jacket is completely unbuttoned and hangs wide "
        "open, the near front panel swung back toward his side, so that his plain mustard-yellow crew-neck T-shirt "
        "is clearly visible as a broad vertical band on his chest and stomach, from the neckline down to the belt "
        "(about a third of the width of his torso). The bag strap still crosses the mustard T-shirt diagonally to "
        "the bag on his near hip. Do not change his head, legs or feet."
    ),
    # --- mouth shapes that leave eyes and eyebrows alone (talk loops cycle them quickly) ---
    "talk_a": (
        "Edit the first image: keep everything exactly the same (same character, pose, position, size, clothes, "
        "colours and flat green background) and change ONLY his mouth and jaw: he is in the middle of speaking, "
        "mouth open as if saying 'ah', the jaw lowered a little. His eyes, eyebrows, nose, hair and head position "
        "stay exactly as they are. Do not move or redraw anything else."
    ),
    "talk_o": (
        "Edit the first image: keep everything exactly the same (same character, pose, position, size, clothes, "
        "colours and flat green background) and change ONLY his mouth: the lips form a small rounded 'oh' shape, "
        "as in mid-speech. His eyes, eyebrows, nose, hair and head position stay exactly as they are. Do not move "
        "or redraw anything else."
    ),
    "talk_e": (
        "Edit the first image: keep everything exactly the same (same character, pose, position, size, clothes, "
        "colours and flat green background) and change ONLY his mouth: lips slightly parted in a relaxed half-open "
        "shape with a hint of the upper teeth, as when saying 'eh' in mid-speech. His eyes, eyebrows, nose, hair "
        "and head position stay exactly as they are. Do not move or redraw anything else."
    ),
    "mask2020_back": (
        "Edit the first image, which shows the man from behind: keep everything exactly the same (same character, "
        "pose, position, size, hair, clothes, colours and flat green background) and add ONLY what is visible from "
        "behind of a light blue disposable surgical face mask that he wears over his nose and mouth: a thin white "
        "elastic ear loop around each ear and, just in front of each ear, a narrow sliver of the light blue mask "
        "edge on his cheeks. Do not move or redraw anything else."
    ),
    # --- body key poses (side view facing right unless stated) ---
    "reach_low": (
        "Edit the first image: the same character, same clothes, same colours, same scale, same flat green "
        "background, still in the same side view facing right, with both feet on exactly the same spot. Change his "
        "pose: he bends his knees into a low crouch and leans his upper body forward, reaching down with his right "
        "arm toward the floor just in front of his toes, the open hand about to pick something up from the ground; "
        "his other hand rests on his knee and he looks down at his hand. The bag still hangs from its strap. Nothing "
        "in his hand, nothing on the floor."
    ),
    "reach_high": (
        "Edit the first image: the same character, same clothes, same colours, same scale, same flat green "
        "background, still in the same side view facing right, standing upright with both feet flat on exactly the "
        "same spot. Change his pose: he stretches his right arm up and slightly forward above his head, the open "
        "hand reaching for something on a high shelf in front of him, about one head height above the top of his "
        "head, and he looks up at his hand; the other arm stays relaxed at his side. Nothing in his hand, no shelf "
        "and no object in the image."
    ),
    "use_tool": (
        "Edit the first image: the same character, same clothes, same colours, same scale, same flat green "
        "background, still in the same side view facing right, standing on exactly the same spot with his feet "
        "unchanged. Change his pose: both forearms are raised in front of him at chest height and he works with a "
        "small screwdriver held in his right hand on something just in front of him, his left hand steadying it, "
        "his head slightly bowed as he looks at his hands with concentration. The screwdriver is the only object "
        "in the image; nothing else in front of him."
    ),
    "show_item": (
        "Edit the first image: the same character, same clothes, same colours, same scale, same flat green "
        "background, still in the same side view facing right, standing on exactly the same spot with his feet "
        "unchanged. Change his pose: he holds his right hand out in front of him at chest height, palm up and "
        "slightly cupped, as if showing a small object to a person standing in front of him, with a friendly open "
        "expression and mouth closed; the other arm stays relaxed. The hand is empty, nothing in the image besides "
        "him."
    ),
    "inventory_combine": (
        "Edit the first image, which shows the man in front view: the same character, same clothes, same colours, "
        "same scale, same flat green background, still facing the viewer and standing on exactly the same spot with "
        "his feet unchanged. Change his pose: he raises both hands in front of his stomach, close together, and "
        "looks down at them with concentration, the fingertips of both hands pinched together as if fitting two "
        "tiny parts together. No visible objects in his hands, nothing else in the image."
    ),
}

MOTION_PROMPTS = {
    "walk": (
        "The man walks in place, as if on a treadmill, with a natural relaxed walking cycle: legs stepping and arms "
        "swinging in alternation, bag swaying slightly. He stays in exactly the same spot in the centre of the frame "
        "and keeps facing right in profile. Seamless loop. The camera is completely static: no pan, no zoom, no "
        "camera shake. The background stays a perfectly flat uniform green the whole time, with no floor, no "
        "shadow and nothing else appearing. Same hand-painted style throughout."
    ),
    "walk_side": (
        "The man walks in place, as if on a treadmill, with a natural relaxed walking cycle: legs stepping and arms "
        "swinging in alternation, the bag swaying slightly and his open blue jacket swinging a little, so the "
        "mustard-yellow T-shirt under it stays visible the whole time. He stays in exactly the same spot in the "
        "centre of the frame and keeps facing right in side view, exactly as in the first frame. Seamless loop. The "
        "camera is completely static: no pan, no zoom, no camera shake. The background stays a perfectly flat "
        "uniform green the whole time, with no floor, no shadow and nothing else appearing. Same hand-painted style "
        "throughout."
    ),
    "walk_toward": (
        "The man walks in place toward the camera, as if on a treadmill, with a natural relaxed walking cycle: legs "
        "stepping and arms swinging in alternation, bag swaying slightly. He stays in exactly the same spot and at "
        "the same size in the centre of the frame and keeps facing the viewer. Seamless loop. The camera is "
        "completely static: no pan, no zoom, no camera shake. The background stays a perfectly flat uniform green "
        "the whole time, with no floor, no shadow and nothing else appearing. Same hand-painted style throughout."
    ),
    "walk_away": (
        "The man walks in place away from the camera, as if on a treadmill, seen from behind, with a natural "
        "relaxed walking cycle: legs stepping and arms swinging in alternation, bag swaying slightly. He stays in "
        "exactly the same spot and at the same size in the centre of the frame and keeps his back to the viewer. "
        "Seamless loop. The camera is completely static: no pan, no zoom, no camera shake. The background stays a "
        "perfectly flat uniform green the whole time, with no floor, no shadow and nothing else appearing. Same "
        "hand-painted style throughout."
    ),
    "reach": (
        "The man, standing on the same spot, calmly raises his right arm and reaches forward at chest height as if "
        "to press a switch on a wall in front of him, a natural motion that ends exactly in the pose of the last "
        "frame and holds it. His feet do not move. The camera is completely static. The "
        "background stays a perfectly flat uniform green, nothing else appears. Same hand-painted style throughout."
    ),
    "reach_low": (
        "The man, standing on the same spot, calmly bends his knees, crouches down and reaches toward the floor "
        "just in front of his toes with his right hand, a natural motion that ends exactly in the pose of the last "
        "frame and holds it. His feet do not move. The camera is completely static. The background stays a "
        "perfectly flat uniform green, nothing else appears. Same hand-painted style throughout."
    ),
    "reach_high": (
        # first try named "a high shelf": Hailuo painted a ghost shelf into the green, touching the hand
        "The man, standing on the same spot, looks up and calmly stretches his right arm up above his head, the "
        "open hand reaching for something high up, a natural motion that ends exactly in the pose of the last frame "
        "and holds it. His feet do not move. The camera is completely static. The background stays a perfectly flat "
        "uniform green the whole time: no shelf, no furniture, no objects, no lines and nothing else appears. Same "
        "hand-painted style throughout."
    ),
    "use_tool": (
        "The man, standing on the same spot, raises both hands to chest height in front of him and works "
        "carefully with a small screwdriver in his right hand on something just in front of him, giving it two "
        "small turns, a natural motion that ends exactly in the pose of the last frame and holds it. His feet do "
        "not move. The camera is completely static. The background stays a perfectly flat uniform green, nothing "
        "else appears. Same hand-painted style throughout."
    ),
    "show_item": (
        "The man, standing on the same spot, calmly holds out his right hand in front of him at chest height, palm "
        "up, as if showing something small to a person in front of him, a natural motion that ends exactly in the "
        "pose of the last frame and holds it. His feet do not move. The camera is completely static. The background "
        "stays a perfectly flat uniform green, nothing else appears. Same hand-painted style throughout."
    ),
    "inventory_combine": (
        "The man, facing the viewer and standing on the same spot, raises both hands in front of his stomach, looks "
        "down and carefully fits two tiny parts together with his fingertips, a natural motion that ends exactly in "
        "the pose of the last frame and holds it. His feet do not move. The camera is completely static. The "
        "background stays a perfectly flat uniform green, nothing else appears. Same hand-painted style throughout."
    ),
    "idle": (
        "The man stands still in place, relaxed and alive: calm breathing, a natural blink, a tiny shift of weight "
        "from one foot to the other, hands relaxed. He keeps the same position, facing and scale. Seamless loop. The "
        "camera is completely static. The background stays a perfectly flat uniform green, nothing else appears. "
        "Same hand-painted style throughout."
    ),
}

NEGATIVE_VIDEO = (
    "camera movement, zoom, pan, walking out of frame, moving across the frame, background change, floor, shadow, "
    "extra people, extra limbs, morphing, text, watermark, blur"
)

VIDEO_ENGINES = {
    # engine: (endpoint, default resolution, supports tail/end image argument name)
    "kling": ("fal-ai/kling-video/v2.5-turbo/pro/image-to-video", "1080p", "tail_image_url"),
    "seedance": ("fal-ai/bytedance/seedance/v1/pro/fast/image-to-video", "720p", None),  # no end-frame input
    "hailuo": ("fal-ai/minimax/hailuo-02/standard/image-to-video", "768P", "end_image_url"),
    "hailuo_pro": ("fal-ai/minimax/hailuo-02/pro/image-to-video", "1080P", "end_image_url"),
    "wan": ("fal-ai/wan/v2.2-a14b/image-to-video", "720p", "end_image_url"),
}


def load_brief(char_id: str) -> dict:
    briefs = json.loads((CHAR_ROOT / "characters.json").read_text(encoding="utf-8"))
    if char_id not in briefs:
        sys.exit(f"{char_id} has no brief in art/characters/characters.json")
    return briefs[char_id]


def save_outputs(result: dict, out_base: Path, meta: dict) -> list[Path]:
    """Download every image/video of a fal result next to out_base and write the sidecar JSON."""
    paths: list[Path] = []
    if "video" in result:
        paths.append(fal_api.download(result["video"]["url"], out_base.with_suffix(".mp4")))
    for index, image in enumerate(result.get("images", [])):
        suffix = "" if index == 0 else f"_{index}"
        paths.append(fal_api.download(image["url"], out_base.with_name(out_base.name + suffix).with_suffix(".png")))
    meta = dict(meta, outputs=[p.name for p in paths], seed=result.get("seed", meta.get("seed")),
                description=result.get("description"))
    out_base.with_suffix(".json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    return paths


def image_inputs(refs: list[Path], style_ref: Path | None) -> list[str]:
    uris = [fal_api.image_data_uri(ref, max_side=2048) for ref in refs]
    if style_ref:
        uris.append(fal_api.image_data_uri(style_ref, max_side=1376, fmt="JPEG"))
    return uris


def edit_image(model_key: str, prompt: str, refs: list[Path], style_ref: Path | None, aspect: str, resolution: str,
               seed: int | None, asset: str, out_base: Path, budget: tuple[str, float]) -> list[Path]:
    model = IMAGE_MODELS[model_key]
    price = fal_api.IMAGE_PRICES[(model, resolution)]
    arguments = {
        "prompt": prompt,
        "image_urls": image_inputs(refs, style_ref),
        "aspect_ratio": aspect,
        "resolution": resolution,
        "output_format": "png",
        "num_images": 1,
    }
    if seed is not None:
        arguments["seed"] = seed
    result = fal_api.run(model, arguments, asset, price, budget=budget, timeout_s=600)
    meta = {"model": model, "usd": price, "prompt": prompt, "aspect_ratio": aspect, "resolution": resolution,
            "references": [str(r.relative_to(ART)) for r in refs],
            "style_reference": str(style_ref.relative_to(ART)) if style_ref else None, "seed": seed}
    return save_outputs(result, out_base, meta)


def cast_reference(keyed_sprite: Path, key: str, out_dir: Path) -> Path:
    """Composite an approved keyed sprite onto the target key colour, so the reference matches the new sheet."""
    from PIL import Image
    colour = {"green": (0, 255, 0), "magenta": (255, 0, 255)}[key]
    sprite = Image.open(keyed_sprite).convert("RGBA")
    pad = sprite.height // 10
    canvas = Image.new("RGBA", (sprite.width + 2 * pad, sprite.height + 2 * pad), colour + (255,))
    canvas.alpha_composite(sprite, (pad, pad))
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"cast_ref_{keyed_sprite.stem}_{key}.png"
    canvas.convert("RGB").save(path)
    return path


def cmd_view(args: argparse.Namespace) -> None:
    brief = load_brief(args.char)
    prompt = VIEW_PROMPTS[args.view].format(desc=brief["description"], name=args.char.title())
    # A background painting next to an identity reference leaks into the key background (seen on the first
    # turnaround test), so derived views (with --ref) get no style reference unless forced.
    # A cast reference (approved sprite of another character) also replaces the background painting: it already
    # carries style A and keeps the whole cast consistent (NB2 + background only drifted to a flat cartoon look).
    use_style_ref = not args.no_style_ref and ((not args.ref and not args.cast_ref) or args.force_style_ref)
    style_ref = Path(args.style_ref).resolve() if use_style_ref else None
    cast_note = ""
    refs_extra: list[Path] = []
    if args.cast_ref:
        refs_extra.append(cast_reference(Path(args.cast_ref).resolve(), args.key, CHAR_ROOT / args.char))
        cast_note = CAST_REF_NOTE
    prompt = " ".join([cast_note, STYLE_REF_NOTE if style_ref else "", prompt, SPRITE_RULES,
                       key_background(args.key), STYLE_FOR_CHARACTER + STYLE_A]).strip()
    prompt = recolour_key_words(prompt, args.key)
    aspect = args.aspect or ("16:9" if args.view == "turnaround" else "3:4")
    name = args.out or f"sheet_{args.view}" + (f"_{args.model}" if args.model != "pro" else "")
    out_base = CHAR_ROOT / args.char / name
    refs = refs_extra + [Path(r).resolve() for r in args.ref]
    paths = edit_image(args.model, prompt, refs, style_ref, aspect, args.res, args.seed,
                       f"characters/{args.char}/{name}", out_base, (args.budget_scope, args.budget))
    print("\n".join(str(p) for p in paths))


# The style line mentions "dappled shadows under the trees"; on pose edits NB2 once painted sun spots onto the
# jacket and lightened the hair (ADAM use_tool, first try), so every pose edit carries this guard.
POSE_GUARD = (
    "Keep his face, hair colour, skin tone and the soft even lighting exactly as in the first image: no dappled "
    "light spots or sun patches on him or his clothes."
)


def cmd_pose(args: argparse.Namespace) -> None:
    load_brief(args.char)
    prompt = " ".join([POSE_PROMPTS[args.pose], POSE_GUARD, key_background(args.key), STYLE_FOR_CHARACTER + STYLE_A])
    prompt = recolour_key_words(prompt, args.key)
    name = args.out or f"pose_{args.pose}_{args.model}"
    out_base = CHAR_ROOT / args.char / name
    refs = [Path(args.base).resolve()] + [Path(r).resolve() for r in args.ref]
    paths = edit_image(args.model, prompt, refs, None, args.aspect, args.res, args.seed,
                       f"characters/{args.char}/{name}", out_base, (args.budget_scope, args.budget))
    print("\n".join(str(p) for p in paths))


def cmd_video(args: argparse.Namespace) -> None:
    load_brief(args.char)
    endpoint, default_res, end_key = VIDEO_ENGINES[args.engine]
    resolution = args.res or default_res
    image_uri = fal_api.image_data_uri(Path(args.image), fmt="PNG")
    prompt = MOTION_PROMPTS[args.motion]
    arguments: dict = {"prompt": prompt, "image_url": image_uri}
    seconds = float(args.seconds)
    if args.engine == "kling":
        arguments.update(duration=str(int(seconds)), negative_prompt=NEGATIVE_VIDEO, cfg_scale=0.6)
        price_res = resolution
    elif args.engine == "seedance":
        arguments.update(duration=str(int(seconds)), resolution=resolution, camera_fixed=True, aspect_ratio="1:1")
        price_res = resolution
    elif args.engine == "hailuo":
        seconds = 6.0 if seconds <= 6 else 10.0  # the endpoint only accepts 6 or 10 s
        arguments.update(duration=str(int(seconds)), resolution=resolution, prompt_optimizer=False)
        price_res = resolution
    elif args.engine == "hailuo_pro":
        seconds = 6.0  # documented price example: 6 s = $0.48
        arguments.update(prompt_optimizer=False)
        price_res = resolution
    elif args.engine == "wan":
        frames = int(round(seconds * 16)) + 1
        arguments.update(num_frames=min(frames, 121), frames_per_second=16, resolution=resolution,
                         negative_prompt=NEGATIVE_VIDEO, aspect_ratio="auto")
        seconds = arguments["num_frames"] / 16
        price_res = resolution
    else:
        raise ValueError(args.engine)
    if args.tail or args.end:
        if end_key is None:
            sys.exit(f"{args.engine} has no end-frame input; run without --tail/--end")
        arguments[end_key] = fal_api.image_data_uri(Path(args.end), fmt="PNG") if args.end else image_uri
    price = fal_api.video_price(endpoint, seconds, price_res)
    name = args.out or f"video_{args.motion}_{args.engine}" + ("_loop" if args.tail else "")
    out_base = CHAR_ROOT / args.char / name
    result = fal_api.run(endpoint, arguments, f"characters/{args.char}/{name}", price,
                         budget=(args.budget_scope, args.budget), timeout_s=1500, poll_s=8)
    meta = {"model": endpoint, "usd": round(price, 4), "prompt": prompt, "input": str(Path(args.image).name),
            "tail_image": bool(args.tail), "end_image": Path(args.end).name if args.end else None,
            "seconds": seconds, "resolution": resolution,
            "arguments": {k: v for k, v in arguments.items() if not str(v).startswith("data:")}}
    paths = save_outputs(result, out_base, meta)
    print("\n".join(str(p) for p in paths))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--budget", type=float, default=DEFAULT_BUDGET[1], help="USD cap for the budget scope")
    parser.add_argument("--budget-scope", default=DEFAULT_BUDGET[0], help="spend-log asset prefix the cap covers")
    sub = parser.add_subparsers(dest="cmd", required=True)

    view = sub.add_parser("view")
    view.add_argument("char")
    view.add_argument("view", choices=VIEW_PROMPTS)
    view.add_argument("--model", choices=IMAGE_MODELS, default="pro")
    view.add_argument("--res", default="2K")
    view.add_argument("--aspect")
    view.add_argument("--ref", action="append", default=[], help="character reference image(s), first = identity")
    view.add_argument("--style-ref", default=str(STYLE_REF_DEFAULT))
    view.add_argument("--no-style-ref", action="store_true")
    view.add_argument("--force-style-ref", action="store_true", help="also send the style painting with --ref")
    view.add_argument("--cast-ref", help="approved keyed sprite of another character, used as the cast style anchor")
    view.add_argument("--seed", type=int, default=1985)
    view.add_argument("--key", choices=KEY_COLOURS, default="green", help="magenta for characters wearing green")
    view.add_argument("--out")
    view.set_defaults(func=cmd_view)

    pose = sub.add_parser("pose")
    pose.add_argument("char")
    pose.add_argument("pose", choices=POSE_PROMPTS)
    pose.add_argument("--base", required=True)
    pose.add_argument("--ref", action="append", default=[])
    pose.add_argument("--model", choices=IMAGE_MODELS, default="nb2")
    pose.add_argument("--res", default="2K")
    pose.add_argument("--aspect", default="3:4")
    pose.add_argument("--seed", type=int, default=1985)
    pose.add_argument("--key", choices=KEY_COLOURS, default="green")
    pose.add_argument("--out")
    pose.set_defaults(func=cmd_pose)

    video = sub.add_parser("video")
    video.add_argument("char")
    video.add_argument("--image", required=True)
    video.add_argument("--engine", choices=VIDEO_ENGINES, default="kling")
    video.add_argument("--motion", choices=MOTION_PROMPTS, default="walk")
    video.add_argument("--seconds", default="5")
    video.add_argument("--res")
    video.add_argument("--tail", action="store_true", help="use the input image as the end frame too (loop)")
    video.add_argument("--end", help="explicit end-frame image (pose transition)")
    video.add_argument("--out")
    video.set_defaults(func=cmd_video)

    args = parser.parse_args()
    try:
        args.func(args)
    except fal_api.BudgetExceeded as exc:
        sys.exit(f"BUDGET: {exc}")


if __name__ == "__main__":
    main()
