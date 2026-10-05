"""yard painter: derive_era.py for two rooms that show the SAME real place with the same camera but are not one
game.json location family (S18 1995 kiosk -> S62 1982 shop; register: S62 'uses the S18 files'). Identical to
`derive_era.py run BASE TARGET --from N` except that the family check is skipped; writes the normal per-room master
art/masters/bg_natural/<TARGET>_v<N>.png + sidecar (kind "derive"), review and export; scope bg_natural/<TARGET>/."""
import sys
from pathlib import Path
sys.path.insert(0, r"C:\Users\klatt\Desktop\adventura\art\tools")
import derive_era  # noqa: E402
derive_era.check_pair = lambda base, target, test: None
sys.argv = ["derive_era.py"] + sys.argv[1:]
derive_era.main()
