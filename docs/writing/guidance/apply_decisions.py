"""Apply Claude's decisions on GPT's flags to the guidance draft (docs/writing/guidance/guidance_std.draft.csv)."""
import csv, json, sys
from pathlib import Path
draft = Path("docs/writing/guidance/guidance_std.draft.csv")
decisions = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
rows = list(csv.DictReader(draft.open(encoding="utf-8")))
n = 0
for r in rows:
    base = r["keys"][:-4]
    if base in decisions:
        r["sk"], r["note"] = decisions[base], r["note"] + "; GPT flag decided (Claude)"
        n += 1
with draft.open("w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["keys", "sk", "note"], lineterminator="\n"); w.writeheader(); w.writerows(rows)
print("applied", n, "of", len(decisions))
