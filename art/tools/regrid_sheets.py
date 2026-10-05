"""Re-pack shipped sprite sheets wider/taller than 4096 px into row-major grids (free, local).

Mobile GPUs (many Android devices, older iPhones) cannot sample textures above 4096 px. The game's sheet loader
(src/game/scripts/Living/Actors/ActorAnimationSet.cs SpriteSheet) reads frame i at column i % columns,
row i / columns; `columns` comes from the sheet JSON (written here), else from texture width / cell width.

  python art/tools/regrid_sheets.py            re-pack every oversized sheet under src/game/assets/{actors,ambient}
  python art/tools/regrid_sheets.py --check    list oversized textures only (exit 1 if any)

Pixels are taken from the lossless pipeline source when it exists and has the same size (hero: art/characters/
ADAM/anim/<name>/<name>_sheet.png; NPCs: the export_actors.py SHEETS map), else from the shipped file. Hero
sheets stay lossless WebP; NPC sheets use export_actors.py's encoding (RGB q92, lossless alpha). Idempotent.
Exporters that write new sheets can call `grid_pack()` before saving (or run this script afterwards).
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

from PIL import Image

ART = Path(__file__).resolve().parent.parent
REPO = ART.parent
ASSETS = REPO / "src" / "game" / "assets"
MAX_SIDE = 4096

NPC_SOURCES = {
    "npc_sheet": "npc_set/npc_sheet.png",
    "idle_sheet": "idle_hailuo/idle_sheet.png",
    "idle_checklist_sheet": "idle_checklist_hailuo/idle_checklist_sheet.png",
    "npc_bust_sheet": "window/npc_bust_sheet.png",
    "npc_bust_glass_sheet": "window/npc_bust_glass_sheet.png",
    "idle_bust_sheet": "window/idle_bust_sheet.png",
    "idle_bust_glass_sheet": "window/idle_bust_glass_sheet.png",
}


def grid_layout(cell_w: int, cell_h: int, frames: int, max_side: int = MAX_SIDE) -> tuple[int, int]:
    """(columns, rows) of the most compact row-major grid that fits max_side."""
    columns = max(1, min(frames, max_side // cell_w))
    rows = math.ceil(frames / columns)
    if rows * cell_h > max_side:
        raise ValueError(f"{frames} cells of {cell_w}x{cell_h} do not fit {max_side} px")
    # balance the rows (same row count, fewest columns) so the last row is not nearly empty
    columns = math.ceil(frames / rows)
    return columns, rows


def grid_pack(img: Image.Image, cell_w: int, cell_h: int, frames: int, columns: int) -> Image.Image:
    """Cells of a strip (or any row-major grid with `img.width // cell_w` columns) re-packed into `columns`."""
    src_cols = max(1, img.width // cell_w)
    rows = math.ceil(frames / columns)
    out = Image.new("RGBA", (columns * cell_w, rows * cell_h), (0, 0, 0, 0))
    for i in range(frames):
        sx, sy = (i % src_cols) * cell_w, (i // src_cols) * cell_h
        cell = img.crop((sx, sy, sx + cell_w, sy + cell_h))
        out.paste(cell, ((i % columns) * cell_w, (i // columns) * cell_h))
    return out


def oversized(root: Path) -> list[tuple[Path, tuple[int, int]]]:
    found = []
    for path in sorted(root.rglob("*")):
        if path.suffix.lower() in (".webp", ".png", ".jpg", ".jpeg"):
            size = Image.open(path).size
            if max(size) > MAX_SIDE:
                found.append((path, size))
    return found


def lossless_source(image: Path, size: tuple[int, int]) -> Path | None:
    char = image.parent.name
    if (src := NPC_SOURCES.get(image.stem)) is not None:
        cand = ART / "characters" / char / src
    else:
        cand = ART / "characters" / char / "anim" / image.stem / f"{image.stem}_sheet.png"
    if cand.exists() and Image.open(cand).size == size:
        return cand
    return None


def regrid(image: Path) -> str:
    meta_path = image.with_suffix(".json")
    if not meta_path.exists():
        return f"SKIP {image.relative_to(REPO)}: no JSON sidecar (not a sheet)"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    frames = int(meta["frames"]) if not isinstance(meta["frames"], list) else len(meta["frames"])
    cell_w, cell_h = (int(v) for v in meta["cell"])
    shipped = Image.open(image)
    size = shipped.size
    columns, rows = grid_layout(cell_w, cell_h, frames)
    src = lossless_source(image, size)
    pixels = Image.open(src if src else image).convert("RGBA")
    packed = grid_pack(pixels, cell_w, cell_h, frames, columns)
    lossless = bool(meta.get("image"))  # hero sheets ("image" key) ship lossless; NPC sheets ("file") lossy RGB
    if lossless:
        packed.save(image, "WEBP", lossless=True, quality=100, method=6, exact=False)
    else:
        packed.save(image, "WEBP", quality=92, alpha_quality=100, method=6)
    meta["columns"], meta["rows"] = columns, rows
    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    actor = image.parent / "actor.json"
    if actor.exists():
        manifest = json.loads(actor.read_text(encoding="utf-8"))
        for entry in manifest.get("sheets", {}).values():
            if entry.get("file") == image.name:
                entry["size"] = list(packed.size)
                entry["columns"] = columns
        actor.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    return (f"{image.relative_to(REPO)}: {size[0]}x{size[1]} -> {packed.width}x{packed.height} "
            f"({columns}x{rows} cells of {cell_w}x{cell_h}, from {'lossless source' if src else 'shipped file'})")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    found = oversized(ASSETS)
    if args.check:
        for path, size in found:
            print(f"{size[0]}x{size[1]} {path.relative_to(REPO)}")
        print(f"{len(found)} texture(s) over {MAX_SIDE} px")
        sys.exit(1 if found else 0)
    for path, _ in found:
        print(regrid(path))
    print(f"{len(found)} sheet(s) checked")


if __name__ == "__main__":
    main()
