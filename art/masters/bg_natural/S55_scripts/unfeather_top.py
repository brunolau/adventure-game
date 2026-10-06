"""Free fix of a variant overlay cut by `paint_natural.py patch` at y 0: the tool feathers every side of the box, also the
side on the frame edge, so the base painting's sky showed as a thin light line along the top of the S55 E10 crown
(in-engine shot 2026-10-06). This copies the alpha of the first fully opaque row up to the frame edge (top side only).

    python art/masters/bg_natural/S55_scripts/unfeather_top.py src/game/assets/variants_natural/S55_linden_and_wall.webp
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image

path = Path(sys.argv[1])
im = Image.open(path).convert("RGBA")
a = np.asarray(im).copy()
alpha = a[..., 3].astype(np.int32)
row = 24                                   # below the 6 px feather + blur
a[:row, :, 3] = np.maximum(alpha[:row], alpha[row][None, :]).astype(np.uint8)
Image.fromarray(a, "RGBA").save(path, "WEBP", quality=95, alpha_quality=100, method=6)
print("unfeathered top of", path, "min alpha row 0 (x 100-1300):", a[0, 100:1300, 3].min())
