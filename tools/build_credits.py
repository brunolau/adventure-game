#!/usr/bin/env python3
"""Compile the in-game credits data (src/game/assets/ui/credits.json).

Reads the attribution tables of the reference photos in art/source/CREDITS.md and
art/source/rooms/CREDITS_*.md (markdown tables; column names vary: "Commons file" or
"Title", "Author", "Licence"/"License", "URL" or a markdown link) and adds the fonts and the
engine. Every photo is listed once (deduplicated by URL, else by title + author).

The credits screen (src/game/scripts/UI/Menus/CreditsScreen.cs) shows sections in this order;
section titles are ui.csv keys, entries are attribution data (names, titles, licences, URLs)
and are shown verbatim.

Usage:
    python tools/build_credits.py [--check]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "src" / "game" / "assets" / "ui" / "credits.json"
SOURCES = [ROOT / "art" / "source" / "CREDITS.md", *sorted((ROOT / "art" / "source" / "rooms").glob("CREDITS_*.md"))]
LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


def clean(cell: str) -> str:
    cell = cell.strip().strip("`").strip()
    cell = re.sub(r"\*\*(.+?)\*\*", r"\1", cell)
    return cell


def split_row(line: str) -> list[str]:
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [c.strip() for c in line.split("|")]


def parse_tables(path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    header: list[str] | None = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip().startswith("|"):
            header = None
            continue
        cells = split_row(raw)
        if header is None:
            header = [c.lower() for c in cells]
            continue
        if all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
            continue
        rows.append({header[i]: cells[i] for i in range(min(len(header), len(cells)))})
    return rows


def entry_from(row: dict[str, str]) -> dict[str, str] | None:
    def first(*names: str) -> str:
        for name in names:
            for key, value in row.items():
                if key == name:
                    return value
        return ""

    title_cell = first("title", "commons title", "commons file", "file")
    url = clean(first("url", "source"))
    link = LINK.search(title_cell)
    if link:
        title = link.group(1)
        url = url or link.group(2)
    else:
        title = clean(title_cell)
    url = url.split("?utm_source")[0]
    author = clean(first("author", "authors", "creator"))
    licence = clean(first("licence", "license"))
    if not title and not author:
        return None
    return {"title": clean(title), "author": author, "license": licence, "url": url}


def build() -> dict:
    photos: list[dict[str, str]] = []
    seen: set[str] = set()
    for source in SOURCES:
        if not source.exists():
            continue
        for row in parse_tables(source):
            entry = entry_from(row)
            if entry is None:
                continue
            key = entry["url"] or (entry["title"] + "|" + entry["author"])
            if key in seen:
                continue
            seen.add(key)
            photos.append(entry)
    photos.sort(key=lambda e: (e["author"].lower(), e["title"].lower()))
    fonts = [
        {"title": "Alegreya", "author": "Juan Pablo del Peral, Huerta Tipográfica (The Alegreya Project Authors)",
         "license": "SIL Open Font License 1.1", "url": "https://github.com/huertatipografica/Alegreya"},
        {"title": "Alegreya Sans", "author": "Juan Pablo del Peral, Huerta Tipográfica (The Alegreya Sans Project Authors)",
         "license": "SIL Open Font License 1.1", "url": "https://github.com/huertatipografica/Alegreya-Sans"},
    ]
    engine = [
        {"title": "Godot Engine", "author": "Juan Linietsky, Ariel Manzur and contributors",
         "license": "MIT", "url": "https://godotengine.org/license"},
    ]
    return {
        "generated_by": "tools/build_credits.py",
        "sources": [str(p.relative_to(ROOT)).replace("\\", "/") for p in SOURCES if p.exists()],
        "sections": [
            {"id": "photos", "title_key": "ui.credits.photo_sources", "entries": photos},
            {"id": "fonts", "title_key": "ui.credits.fonts", "entries": fonts},
            {"id": "engine", "title_key": "ui.credits.engine", "entries": engine},
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", help="exit 1 when credits.json is out of date")
    args = parser.parse_args()
    data = build()
    text = json.dumps(data, ensure_ascii=False, indent=1) + "\n"
    if args.check:
        current = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
        if current != text:
            print("credits.json is out of date: run python tools/build_credits.py")
            return 1
        print("credits.json is up to date")
        return 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}: {len(data['sections'][0]['entries'])} photo credits from {len(data['sources'])} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
