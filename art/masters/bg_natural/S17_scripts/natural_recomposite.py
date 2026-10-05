"""bg_helpers.py recomposite on the NATURAL masters (paint_natural.install() first, so paths point to bg_natural)."""
import sys
from pathlib import Path
ROOT = Path(r"C:\Users\klatt\Desktop\adventura")
sys.path.insert(0, str(ROOT / "art" / "tools"))
import paint_natural
paint_natural.install()
import bg_helpers
sys.argv = ["bg_helpers.py", "recomposite"] + sys.argv[1:]
bg_helpers.main()
