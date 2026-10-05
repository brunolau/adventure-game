"""App icon for Posledny zvonec (LastBell): one painted style-A master and the exported sizes.

  python art/tools/app_icon.py generate [--take N]    one paid nano-banana-pro call (USD 0.15, cap USD 1.00)
  python art/tools/app_icon.py export art/ui/icon/icon_master_vN.png

generate writes art/ui/icon/icon_master_v<N>.png (+ .json with prompt/seed).
export writes:
  src/game/icon.png (1024), src/game/icon.ico (16..256, Windows exe + window icon),
  src/game/assets/ui/icon/icon_<size>.png (16..1024, launcher/store sizes),
  src/game/assets/ui/icon/icon_android_fg_432.png / icon_android_bg_432.png (adaptive icon layers).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from PIL import Image, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fal_api  # noqa: E402

ART = Path(__file__).resolve().parent.parent
ROOT = ART.parent
GAME = ROOT / "src" / "game"
OUT = ART / "ui" / "icon"
BUDGET = ("ui/icon", 1.00)
MODEL = "fal-ai/nano-banana-pro/edit"
STYLE_REF = GAME / "assets" / "bg" / "S11.webp"

STYLE_A = (
    "Style: classic 1990s hand-painted adventure game background. Rich painterly brushwork, slightly "
    "exaggerated cartoon proportions with gently curved lines, warm late-afternoon sunlight, saturated but "
    "harmonious colours, soft dappled shadows under the trees."
)

PROMPT = (
    "A square application icon painting for a point-and-click adventure game called 'The Last Bell'. "
    "The attached image is a finished background painting from our game: use it ONLY as the reference for the "
    "painting style, brushwork and palette, do not copy its content or composition. "
    "Composition, bold and readable even when shrunk to 32 pixels: in the centre, large, filling about 60 % of "
    "the picture, an old polished brass school hand bell with a turned dark wooden handle, tilted slightly to the "
    "right as if it is just ringing, warm golden highlights on the brass. Directly behind the bell, a big round "
    "brass ring like the bezel of an old clock, engraved with four simple symbols spaced evenly around it at the "
    "12, 3, 6 and 9 o'clock positions: a small circle, a small triangle, a small square and a small four-pointed "
    "star. Inside the ring behind the bell, the sky changes like passing time: the left half a cool blue winter "
    "dusk with a few falling snowflakes, the right half a warm orange late-afternoon summer sky; along the lower "
    "edge a simple dark silhouette of 1970s concrete panel apartment blocks and two rounded trees. "
    "Outside the ring the background is a deep warm teal with soft painted texture, filling the whole square to "
    "the edges (full bleed, no border, no rounded corners, no frame, no drop shadow around the icon). "
    "No text, no letters, no numbers, no logos, no people. "
) + STYLE_A


def cmd_generate(args: argparse.Namespace) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    take = args.take or 1 + len(list(OUT.glob("icon_master_v*.png")))
    price = fal_api.IMAGE_PRICES[(MODEL, "1K")]
    style = Image.open(STYLE_REF).convert("RGB")
    arguments = {
        "prompt": PROMPT,
        "image_urls": [fal_api.image_data_uri(style, max_side=1376, fmt="JPEG")],
        "aspect_ratio": "1:1",
        "resolution": "1K",
        "output_format": "png",
        "num_images": 1,
    }
    result = fal_api.run(MODEL, arguments, f"ui/icon/master_v{take}", price, budget=BUDGET, timeout_s=600)
    path = fal_api.download(result["images"][0]["url"], OUT / f"icon_master_v{take}.png")
    meta = {"model": MODEL, "usd": price, "prompt": PROMPT, "aspect_ratio": "1:1", "resolution": "1K",
            "style_reference": "src/game/assets/bg/S11.webp", "seed": result.get("seed")}
    path.with_suffix(".json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    print(path)


def square(img: Image.Image) -> Image.Image:
    side = min(img.size)
    left, top = (img.width - side) // 2, (img.height - side) // 2
    return img.crop((left, top, left + side, top + side))


def sized(master: Image.Image, size: int) -> Image.Image:
    out = master.resize((size, size), Image.Resampling.LANCZOS)
    if size <= 64:  # small sizes lose the brushwork; a light sharpen keeps the bell's silhouette crisp
        out = out.filter(ImageFilter.UnsharpMask(radius=0.8, percent=60, threshold=1))
    return out


def cmd_export(args: argparse.Namespace) -> None:
    master = square(Image.open(args.master).convert("RGBA"))
    master = master.resize((1024, 1024), Image.Resampling.LANCZOS)
    ui = GAME / "assets" / "ui" / "icon"
    ui.mkdir(parents=True, exist_ok=True)
    master.save(GAME / "icon.png")
    for size in (16, 24, 32, 48, 64, 128, 180, 192, 256, 512, 1024):
        sized(master, size).save(ui / f"icon_{size}.png")
    ico_sizes = [16, 24, 32, 48, 64, 128, 256]
    big = sized(master, 256)
    big.save(GAME / "icon.ico", sizes=[(s, s) for s in ico_sizes])
    # Android adaptive icon (432 px, the inner 66 % circle is the safe zone): foreground = the master shrunk to
    # the safe zone over the background colour sampled from the master's corners; background = a blurred master.
    bg = master.resize((432, 432), Image.Resampling.LANCZOS).filter(ImageFilter.GaussianBlur(24))
    bg.convert("RGB").save(ui / "icon_android_bg_432.png")
    fg = Image.new("RGBA", (432, 432), (0, 0, 0, 0))
    inner = sized(master, 288)
    fg.paste(inner, (72, 72))
    fg.save(ui / "icon_android_fg_432.png")
    print("exported", GAME / "icon.png", GAME / "icon.ico", ui)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("generate")
    g.add_argument("--take", type=int)
    g.set_defaults(func=cmd_generate)
    e = sub.add_parser("export")
    e.add_argument("master")
    e.set_defaults(func=cmd_export)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
