"""B21 state art for S30 (old Stary most 1995): Emil's wooden metronome on the round table (free composite).

The metronome is the same object as on Emil's table in S19: cut from src/game/assets/bg_natural/S19.webp (pyramid
body plus the tilted pendulum rod and its weight), scaled, given a soft contact shadow and saved as an RGBA patch
src/game/assets/variants_natural/S30_metronome_placed.webp. Its bottom centre sits on the painted white rhythm mark of
the table top (bg_natural/S30.webp, master S30_v1). Prints the patch position for the blocking file.

Usage: PYTHONIOENCODING=utf-8 python -X utf8 art/prompts/natural/S30_starymost/metronome_patch.py
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[4]
ASSETS = ROOT / "src" / "game" / "assets"
SRC_BOX = (860, 576, 930, 664)                     # S19 game px around the metronome
BODY = [(869, 660), (921, 660), (902, 585), (887, 585)]   # pyramid outline in S19 game px
ROD = [(899, 645), (904, 646), (921, 596), (916, 594)]    # tilted pendulum rod
WEIGHT = (911, 587, 923, 600)                      # sliding weight on the rod
SCALE = 1.05
FOOT = (705, 674)                                  # bottom centre on the S30 table's rhythm mark


def main() -> None:
    s19 = Image.open(ASSETS / "bg_natural" / "S19.webp").convert("RGBA")
    crop = s19.crop(SRC_BOX)
    ox, oy = SRC_BOX[:2]
    mask = Image.new("L", crop.size, 0)
    d = ImageDraw.Draw(mask)
    d.polygon([(x - ox, y - oy) for x, y in BODY], fill=255)
    # rod and weight: only their golden pixels (the S19 background behind them is green bush and grey fence)
    rod = Image.new("L", crop.size, 0)
    dr = ImageDraw.Draw(rod)
    dr.polygon([(x - ox, y - oy) for x, y in ROD], fill=255)
    dr.rectangle([WEIGHT[0] - ox, WEIGHT[1] - oy, WEIGHT[2] - ox, WEIGHT[3] - oy], fill=255)
    px, rp, mp = crop.load(), rod.load(), mask.load()
    for yy in range(crop.height):
        for xx in range(crop.width):
            r, g, b, _ = px[xx, yy]
            if rp[xx, yy] and r > 130 and r >= g and r - b > 55:
                mp[xx, yy] = 255
            elif mp[xx, yy] and g > r + 6:          # green bush pixels at the body's edge
                mp[xx, yy] = 0
    crop.putalpha(mask.filter(ImageFilter.GaussianBlur(0.6)))
    w, h = round(crop.width * SCALE), round(crop.height * SCALE)
    sprite = crop.resize((w, h), Image.Resampling.LANCZOS)
    pad = 12
    canvas = Image.new("RGBA", (w + 2 * pad, h + pad), (0, 0, 0, 0))
    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    base_y = pad + round((660 - oy) * SCALE)       # bottom of the body inside the canvas
    left = pad + round((869 - ox) * SCALE)
    right = pad + round((922 - ox) * SCALE)
    ImageDraw.Draw(shadow).ellipse([left - 6, base_y - 5, right + 10, base_y + 6], fill=(45, 28, 14, 120))
    canvas = Image.alpha_composite(canvas, shadow.filter(ImageFilter.GaussianBlur(3)))
    canvas.alpha_composite(sprite, (pad, pad))
    out = ASSETS / "variants_natural" / "S30_metronome_placed.webp"
    canvas.save(out, "WEBP", quality=95)
    cx = (left + right) // 2
    pos = (FOOT[0] - cx, FOOT[1] - base_y)
    bg = Image.open(ASSETS / "bg_natural" / "S30.webp").convert("RGBA")
    bg.alpha_composite(canvas, pos)
    preview = ROOT / "art" / "review" / "natural" / "S30_metronome_placed_preview.png"
    bg.crop((560, 540, 860, 840)).resize((600, 600), Image.Resampling.LANCZOS).save(preview)
    print(f"{out.relative_to(ROOT)} {canvas.size} pos {list(pos)}; preview {preview.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
