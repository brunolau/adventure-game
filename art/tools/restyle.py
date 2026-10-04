"""Restyle source photos into adventure-game backgrounds via fal.ai (Nano Banana Pro edit).

Usage:
  python restyle.py [--style painted-90s] [--out backgrounds] [scene ...]
With no scenes given, every scene in SCENES is rendered.
Outputs go to art/<out>/, spend is appended to art/spend-log.csv.
"""
import argparse
import base64
import csv
import datetime
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests
from PIL import Image

ART = Path(__file__).resolve().parent.parent
SRC = ART / "source"
LOG = ART / "spend-log.csv"

MODEL = "fal-ai/nano-banana-pro/edit"
PRICE_PER_IMAGE = 0.15  # USD, 1K-2K resolution
SEED = 1987

COMMON = (
    "Transform this photo into a background screen for a point-and-click adventure game. "
    "Keep the real place recognisable: {scene} "
    "Widen the composition to 16:9 by extending the scene naturally on both sides. "
    "Remove all people and graffiti. {extra}"
    "{walk} must stay open and unobstructed - it is where the player character will walk. "
    "Do not add any characters, UI, text overlays or watermarks. "
)

# name: (source file, what must stay recognisable, walkable area, extra instructions[, full prompt template])
SCENES = {
    "entrance": (
        "sokolikova2_02.jpg",
        "the long two-storey 1970s school building with a white and grey mosaic-tiled facade, rows of white-framed "
        "windows, the glass main entrance with its slanted metal-and-glass canopy, the ramp, the steps and the small "
        "flower planters, the white sign above the entrance reading 'ZŠ Sokolíkova 2 Bratislava, M. č. Dúbravka', "
        "and the leafy trees framing the scene.",
        "The paved area in the foreground",
        "Remove cars. Thin out foreground foliage so the building and entrance are clearly visible. ",
    ),
    "side-path": (
        "sokolikova2_04.jpg",
        "the long two-storey 1970s school building seen in perspective, white and grey mosaic-tiled facade, rows of "
        "white-framed windows with blinds, the glass double doors under a grey steel-frame canopy, the concrete steps, "
        "the asphalt path running along the building, a pine tree on the left and a blue sky with white clouds.",
        "The asphalt path in the foreground",
        "Remove cars. ",
    ),
    "school-street-entrance": (
        "sokolikova2_03.jpg",
        "the street side of the ZŠ Sokolíkova school building on Sokolíkova street in Dúbravka: a two-storey white and "
        "grey mosaic-tiled facade with rows of white-framed windows, the entrance under a long flat glass canopy with "
        "concrete steps and flower planters, the small sign reading 'ZÁKLADNÁ ŠKOLA' next to the Slovak coat of arms, "
        "the street lamp with a round white globe, pine trees and garden shrubs with pink roses.",
        "The paved courtyard path in the foreground",
        "Remove cars. Pull the pine branches back so they only frame the top and sides; the entrance, canopy and sign "
        "must be clearly visible. ",
    ),
    "sokolikova-street": (
        "sokolikova-block_flickr.jpg",
        "Sokolíkova street in Dúbravka, Bratislava: a long row of four-storey 1970s prefab panel apartment blocks "
        "(paneláky) with deep loggias and faded red-brown balcony panels, steel entrance staircases with railings in "
        "front of each doorway, a yellow block at the far left end, tall pines on the left and a big leafy tree on "
        "the right, the narrow residential street with a kerb and pavement.",
        "The street and pavement in the foreground",
        "Remove all parked cars except one small old hatchback parked far away in the background. Replace the "
        "overcast sky with a pleasant summer sky. ",
    ),
    "sokolikova-yard": (
        "sokolikova-yard_flickr.jpg",
        "the old sunken courtyard playground (ihrisko) between the panel blocks of Sokolíkova street in Dúbravka: a "
        "rectangular asphalt court enclosed by weathered grey precast concrete wall panels, a slim white birch, a tall "
        "blue spruce, a globe-topped lamp post, dense green trees and a panel block with balconies behind, grassy "
        "slopes in the foreground.",
        "The asphalt court and the grass in the foreground",
        "",
    ),
    # No usable photo exists: invented from the OpenStreetMap layout, the photo is only a reference for surroundings.
    "hurikan": (
        "sokolikova-block_flickr.jpg",
        None,
        "The paved path in the foreground",
        "",
        "Use this photo only as a reference for what the surrounding 1970s panel blocks of Dúbravka look like. Paint "
        "a new background screen for a point-and-click adventure game showing the Hurikán sports area on Hanulova "
        "street, just off Sokolíkova street in Dúbravka, Bratislava: on the left a small single-storey neighbourhood "
        "pub with a flat roof and a modest painted sign reading 'HURIKÁN', a small terrace with a few beer-garden "
        "tables and umbrellas under the trees; in the middle a clay tennis court enclosed by a tall green wire fence; "
        "on the right a small paved multi-purpose court with a basketball hoop and a children's playground with a "
        "slide and a climbing frame; behind everything tall leafy trees and the panel blocks with red-brown balconies. "
        "16:9 composition. {walk} must stay open and unobstructed - it is where the player character will walk. "
        "No people, no cars, no UI, no text overlays, no watermarks. ",
    ),
    "tram-stop": (
        "tram-stop_svantnerova.jpg",
        "the Švantnerova tram stop in Dúbravka, Bratislava: the platform with its glass shelter on the left, the "
        "electronic departure board reading 'ŠVANTNEROVA', a red Bratislava tram arriving on the tracks, the overhead "
        "tram wires and poles, tall panel-block housing estates and green trees under a big cloudy summer sky.",
        "The tram platform in the foreground",
        "Keep the tram. Recompose slightly so the platform runs along the bottom of the frame. ",
    ),
    "dom-kultury": (
        "dom-kultury.jpg",
        "Dom kultúry Dúbravka, the 1970s cultural house in Bratislava: a long low building with a ribbon of windows "
        "under a bright yellow angular roof structure, the lawn with young trees and footpaths in front of it, a tall "
        "panel-block tower on the right, the street and tram tracks in the foreground.",
        "The pavement and lawn in the foreground",
        "Remove cars. ",
    ),
    "stara-dubravka": (
        "stara-dubravka.jpg",
        "the old village street of Stará Dúbravka in Bratislava: a row of low whitewashed village houses with steep "
        "brown tiled roofs, wooden telegraph poles with sagging wires, the narrow asphalt lane with a grassy verge "
        "leading into the distance, and a large dark tree on the left.",
        "The lane in the foreground",
        "Remove cars. ",
    ),
    "kaverna": (
        "kaverna-1.jpg",
        "an old military cavern entrance ('kaverna') hidden in the Dúbravka forest: an arched stone tunnel mouth "
        "closed by a rusty iron grille, overgrown with ivy and tall grass, a gnarled old tree on the left with a "
        "small yellow hiking-trail sign nailed to it, the forest behind. Slightly mysterious mood.",
        "A small clearing of trampled earth in the foreground leading to the grille",
        "",
    ),
}

STYLES = {
    "painted-90s": (
        "Style: classic 1990s hand-painted adventure game background. Rich painterly brushwork, slightly exaggerated "
        "cartoon proportions with gently curved lines, warm late-afternoon sunlight, saturated but harmonious colours, "
        "soft dappled shadows under the trees."
    ),
    "illustrated": (
        "Style: modern illustrated indie adventure game. Clean ink outlines, flat cel-shaded colour with soft "
        "gradients, muted early-autumn palette with teal and orange accents, graphic-novel look, crisp and readable."
    ),
}


def fal_key():
    key = os.environ.get("FAL_KEY")
    if not key and sys.platform == "win32":
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as k:
            key, _ = winreg.QueryValueEx(k, "FAL_KEY")
    if not key:
        sys.exit("FAL_KEY not found")
    return key


def data_uri(path):
    return "data:image/jpeg;base64," + base64.b64encode(path.read_bytes()).decode()


def pixelate(path, width=480, height=270, colors=40):
    """Turn a painted background into true low-res pixel art (free, runs locally)."""
    from PIL import ImageEnhance
    small = Image.open(path).convert("RGB").resize((width, height), Image.Resampling.LANCZOS)
    small = ImageEnhance.Color(small).enhance(1.15)
    small = small.quantize(colors=colors, method=Image.Quantize.MAXCOVERAGE, dither=Image.Dither.FLOYDSTEINBERG)
    small = small.convert("RGB")
    small.save(path.with_name(path.stem + "-pixel-native.png"))
    small.resize((width * 4, height * 4), Image.Resampling.NEAREST).save(path.with_name(path.stem + "-pixel.png"))


def run(scene_name, style_name, out_dir, key):
    src_file, scene_desc, walk, extra, *template = SCENES[scene_name]
    template = template[0] if template else COMMON
    prompt = template.format(scene=scene_desc, walk=walk, extra=extra) + STYLES[style_name]
    r = requests.post(
        f"https://fal.run/{MODEL}",
        headers={"Authorization": f"Key {key}", "Content-Type": "application/json"},
        json={
            "prompt": prompt,
            "image_urls": [data_uri(SRC / src_file)],
            "aspect_ratio": "16:9",
            "resolution": "2K",
            "output_format": "png",
            "num_images": 1,
            "seed": SEED,
        },
        timeout=600,
    )
    if r.status_code != 200:
        return scene_name, None, f"HTTP {r.status_code}: {r.text[:300]}"
    out = out_dir / f"{scene_name}.png"
    out.write_bytes(requests.get(r.json()["images"][0]["url"], timeout=120).content)
    return scene_name, out, Image.open(out).size


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--style", default="painted-90s", choices=STYLES)
    ap.add_argument("--out", default="backgrounds")
    ap.add_argument("--pixel", action="store_true", help="also save a pixel-art conversion")
    ap.add_argument("scenes", nargs="*", help=f"any of: {', '.join(SCENES)}")
    args = ap.parse_args()
    unknown = set(args.scenes) - set(SCENES)
    if unknown:
        ap.error(f"unknown scene(s): {', '.join(sorted(unknown))}")

    out_dir = ART / args.out
    out_dir.mkdir(parents=True, exist_ok=True)
    key = fal_key()
    scenes = args.scenes or list(SCENES)
    with ThreadPoolExecutor(max_workers=len(scenes)) as pool:
        results = list(pool.map(lambda s: run(s, args.style, out_dir, key), scenes))

    new_log = not LOG.exists()
    with LOG.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new_log:
            w.writerow(["timestamp", "model", "asset", "usd"])
        now = datetime.datetime.now().isoformat(timespec="seconds")
        for scene, out, info in results:
            print(f"{scene:18} -> {out.relative_to(ART) if out else 'FAILED'}  {info}")
            if out:
                w.writerow([now, MODEL, f"{args.out}/{scene} ({args.style})", PRICE_PER_IMAGE])
                if args.pixel:
                    pixelate(out)


if __name__ == "__main__":
    main()
