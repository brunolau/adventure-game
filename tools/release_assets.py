"""Release asset policy of the Godot project (src/game): texture import compression and the release export filter.
See docs/BUILD.md "Release size".

1. Texture compression (`imports`). Godot imports every texture "lossless" by default, which re-encodes the
   lossy WebP paintings as lossless images (5x larger; the exported PCK was 448 MB). Large painted images are
   imported "Lossy" (WebP inside the .ctex, decoded to RGBA8 on load, no VRAM compression, no mipmaps):
       assets/bg_natural, assets/bg, assets/bg_options, assets/cutscenes, assets/actors   -> Lossy, quality 0.90
   Everything else stays lossless: UI, cursors, icons, fonts, item icons (drawn 1:1 at small sizes), and the
   painting-matched overlays (assets/ambient cut-outs and masks, assets/variants*, assets/fg*), which sit
   pixel-exactly on top of the painting and must not get their own compression noise.
   New files get Godot's lossless default; `build.bat` runs `imports` before importing, so they follow the policy.

2. Release export filter (`filter`). Release presets do not ship what only the template mode, the QA harness or
   art reviews use (natural blocking is the default since milestone 3, every room has data/blocking/<room>.json):
       assets/bg/*, assets/variants/*, assets/fg/*           template paintings, overlays, masks
       assets/ambient/<room>/<file>                          ambient cut-outs of the template paintings (not natural/)
       data/ambient/S*.json                                  ambient layers of the template paintings
       assets/bg_options/*                                   painting options for review (style tests)
       data/debug/*                                          QA walkthrough (the harness is off in release, BUILD-03)
   The QA preset "Windows Desktop (QA)" (build.bat debug) keeps everything, so --blocking template still works there
   and in the editor. The filter is written into export_presets.cfg; `--check` fails when the file is out of date or
   when natural-mode data (data/blocking/**, data/audio, sheet/manifest JSON) references an excluded file.

3. `pck <file.pck>`: lists an exported PCK by folder (sizes) and fails if an excluded file is inside.

Usage: python tools/release_assets.py imports [--check]
       python tools/release_assets.py filter [--check]
       python tools/release_assets.py check                  (both checks; build.bat runs this)
       python tools/release_assets.py pck build/windows/LastBell.pck [--depth 2]
Exit code 1 on a failed check.
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import re
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GAME = ROOT / "src" / "game"
PRESETS = GAME / "export_presets.cfg"

LOSSY_QUALITY = 0.9
LOSSY_FOLDERS = ("assets/bg_natural/", "assets/bg/", "assets/bg_options/", "assets/cutscenes/", "assets/actors/")

# Preset name -> its own excludes; "release" = also the release excludes below.
PRESET_BASE = {
    "Windows Desktop": ("*.md, assets/ui/icon/icon_android_*", True),
    "Windows Desktop (QA)": ("*.md, assets/ui/icon/icon_android_*", False),
    "macOS (not built)": ("*.md, assets/ui/icon/icon_android_*", True),
    "Android arm64 (not built)": ("*.md, icon.ico", True),
    "iOS (not built)": ("*.md, icon.ico, assets/ui/icon/icon_android_*", True),
}
INCLUDE = "*.json, localization/*.translation, assets/ui/fonts/*.txt"
RELEASE_FOLDERS = ["assets/bg/*", "assets/variants/*", "assets/fg/*", "assets/bg_options/*", "data/debug/*", "data/ambient/S*.json"]


def rel(path: Path) -> str:
    return path.relative_to(GAME).as_posix()


# ---------------------------------------------------------------- imports

def texture_imports():
    for imp in sorted(GAME.joinpath("assets").rglob("*.import")):
        text = imp.read_text(encoding="utf-8")
        if 'importer="texture"' in text:
            yield imp, text


def wanted_params(source: str) -> dict[str, str]:
    if source.startswith(LOSSY_FOLDERS):
        return {"compress/mode": "1", "compress/lossy_quality": f"{LOSSY_QUALITY:g}"}
    return {"compress/mode": "0"}


def cmd_imports(check: bool) -> int:
    changed, lossy, lossless = [], 0, 0
    for imp, text in texture_imports():
        source = rel(imp)[: -len(".import")]
        params = wanted_params(source)
        new = text
        for key, value in params.items():
            pattern = re.compile(rf"^{re.escape(key)}=.*$", re.M)
            if pattern.search(new):
                new = pattern.sub(f"{key}={value}", new)
            else:
                new = new.replace("[params]\n", f"[params]\n\n{key}={value}\n", 1)
        if params["compress/mode"] == "1":
            lossy += 1
        else:
            lossless += 1
        if new != text:
            changed.append(source)
            if not check:
                imp.write_text(new, encoding="utf-8", newline="\n")
    verb = "need" if check else "set"
    print(f"imports: {lossy} lossy (quality {LOSSY_QUALITY:g}), {lossless} lossless; {len(changed)} file(s) {verb} a change")
    for s in changed[:20]:
        print("   ", s)
    if len(changed) > 20:
        print(f"    ... {len(changed) - 20} more")
    return 1 if check and changed else 0


# ---------------------------------------------------------------- filter

def template_ambient_cutouts() -> list[str]:
    out = []
    base = GAME / "assets" / "ambient"
    for room in sorted(p for p in base.iterdir() if p.is_dir() and re.fullmatch(r"S\d\d", p.name)):
        for f in sorted(room.iterdir()):
            if f.is_file() and f.suffix in (".webp", ".png") and not f.name.endswith(".import"):
                out.append(rel(f))
    return out


def release_excludes() -> list[str]:
    return RELEASE_FOLDERS + template_ambient_cutouts()


def is_excluded(path: str, patterns: list[str]) -> bool:
    from fnmatch import fnmatchcase
    return any(fnmatchcase(path, p) for p in patterns)


def natural_references() -> dict[str, set[str]]:
    """Asset paths named by natural-mode data, mapped to the files that name them."""
    refs: dict[str, set[str]] = collections.defaultdict(set)
    sources = list((GAME / "data" / "blocking").rglob("*.json")) + list((GAME / "data" / "audio").rglob("*.json"))
    sources += [p for p in (GAME / "assets").rglob("*.json") if rel(p) != "assets/ambient/manifest.json"]
    sources += [GAME / "data" / "cutscene_camera.json"]
    string_re = re.compile(r'"([^"\n]+\.(?:webp|png|ogg|wav|json))"')
    for src in sources:
        if not src.exists():
            continue
        text = src.read_text(encoding="utf-8")
        for m in string_re.finditer(text):
            value = m.group(1).removeprefix("res://")
            candidates = {value, "assets/" + value, "assets/ambient/" + value}
            for c in candidates:
                if (GAME / c).exists():
                    refs[c].add(rel(src))
    return refs


def read_presets() -> str:
    return PRESETS.read_text(encoding="utf-8")


def render_presets(text: str) -> tuple[str, list[str]]:
    notes = []
    excludes = release_excludes()
    sections = re.split(r"(?m)^(?=\[preset\.\d+\]\s*$)", text)
    out = []
    for sec in sections:
        m = re.search(r'(?m)^name="(.*)"$', sec)
        if m and re.match(r"\[preset\.\d+\]", sec) and m.group(1) in PRESET_BASE:
            base, release = PRESET_BASE[m.group(1)]
            value = base + (", " + ", ".join(excludes) if release else "")
            sec = re.sub(r'(?m)^exclude_filter=".*"$', f'exclude_filter="{value}"', sec)
            sec = re.sub(r'(?m)^include_filter=".*"$', f'include_filter="{INCLUDE}"', sec)
            notes.append(f"{m.group(1)}: {'release excludes' if release else 'QA (no release excludes)'}")
        elif m and re.match(r"\[preset\.\d+\]", sec):
            notes.append(f"{m.group(1)}: not managed")
        out.append(sec)
    return "".join(out), notes


def cmd_filter(check: bool) -> int:
    errors = 0
    excludes = release_excludes()
    refs = natural_references()
    for path, users in sorted(refs.items()):
        if is_excluded(path, excludes):
            print(f"ERROR {path} is excluded from release exports but natural-mode data uses it: {', '.join(sorted(users))}")
            errors += 1
    text = read_presets()
    if 'name="Windows Desktop (QA)"' not in text:
        print('ERROR export_presets.cfg has no "Windows Desktop (QA)" preset (build.bat debug)')
        errors += 1
    new, notes = render_presets(text)
    cutouts = len(template_ambient_cutouts())
    if new != text:
        if check:
            print("ERROR export_presets.cfg filters are out of date: run python tools/release_assets.py filter")
            errors += 1
        else:
            PRESETS.write_text(new, encoding="utf-8", newline="\n")
            print("filter: export_presets.cfg updated")
    for n in notes:
        print("   ", n)
    print(f"filter: {len(RELEASE_FOLDERS)} folder patterns + {cutouts} template ambient cut-outs excluded from release presets; "
          f"{len(refs)} natural-mode references checked, {errors} error(s)")
    return 1 if errors else 0


# ---------------------------------------------------------------- pck

def read_pck(path: Path) -> list[tuple[str, int]]:
    with path.open("rb") as f:
        data_start = 0
        magic = f.read(4)
        if magic != b"GDPC":
            raise SystemExit(f"{path}: not a Godot PCK")
        version, major, minor, patch, flags, file_base = struct.unpack("<IIIIIQ", f.read(28))
        if version >= 3:
            (dir_offset,) = struct.unpack("<Q", f.read(8))
            f.seek(data_start + dir_offset)
        else:
            f.read(16 * 4)
        if flags & 1:
            raise SystemExit(f"{path}: encrypted directory, cannot list")
        (count,) = struct.unpack("<I", f.read(4))
        files = []
        for _ in range(count):
            (n,) = struct.unpack("<I", f.read(4))
            name = f.read(n).rstrip(b"\0").decode("utf-8")
            offset, size = struct.unpack("<QQ", f.read(16))
            f.read(16)  # md5
            f.read(4)  # flags
            files.append((name.removeprefix("res://"), size))
        return files


def cmd_pck(pck: Path, depth: int) -> int:
    files = read_pck(pck)
    total = sum(s for _, s in files)
    imported = {}
    # Map .godot/imported/<name>-<hash>.ctex back to the source via the exported .import remaps is not possible
    # from the PCK alone; group imported files by their source extension and name instead.
    by_folder: dict[str, int] = collections.Counter()
    sources: set[str] = set()
    for name, size in files:
        if name.endswith(".import"):
            sources.add(name[: -len(".import")])
        if name.startswith(".godot/imported/"):
            imported[name] = size
            continue
        by_folder["/".join(name.split("/")[:depth])] += size
    print(f"{pck}: {len(files)} files, {total / 1e6:.1f} MB (file size {pck.stat().st_size / 1e6:.1f} MB)")
    # Attribute imported payloads to the folder of the .import that points at them.
    remap: dict[str, str] = {}
    for src in sources:
        imp = GAME / (src + ".import")
        if imp.exists():
            m = re.search(r'path="res://(.godot/imported/[^"]+)"', imp.read_text(encoding="utf-8"))
            if m:
                remap[m.group(1)] = src
    for name, size in imported.items():
        src = remap.get(name)
        key = "/".join(src.split("/")[:depth]) if src else ".godot/imported (unmatched)"
        by_folder[key] += size
    for key, size in sorted(by_folder.items(), key=lambda kv: -kv[1])[:40]:
        print(f"  {size / 1e6:8.1f} MB  {key}")
    excludes = release_excludes()
    leaked = sorted(s for s in sources if is_excluded(s, excludes))
    if leaked:
        print(f"note: {len(leaked)} release-excluded file(s) inside (fine for the QA build): {', '.join(leaked[:5])}{' ...' if len(leaked) > 5 else ''}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("imports"); p.add_argument("--check", action="store_true")
    p = sub.add_parser("filter"); p.add_argument("--check", action="store_true")
    sub.add_parser("check")
    p = sub.add_parser("pck"); p.add_argument("file", type=Path); p.add_argument("--depth", type=int, default=2)
    p.add_argument("--release", action="store_true", help="fail if a release-excluded file is inside")
    a = ap.parse_args()
    if a.cmd == "imports":
        return cmd_imports(a.check)
    if a.cmd == "filter":
        return cmd_filter(a.check)
    if a.cmd == "check":
        return max(cmd_imports(True), cmd_filter(True))
    if a.cmd == "pck":
        rc = cmd_pck(a.file, a.depth)
        if a.release:
            files = {n for n, _ in read_pck(a.file)}
            leaked = sorted(n[: -len(".import")] for n in files if n.endswith(".import") and is_excluded(n[: -len(".import")], release_excludes()))
            if leaked:
                print(f"ERROR {len(leaked)} release-excluded file(s) in a release PCK")
                return 1
        return rc
    return 0


if __name__ == "__main__":
    sys.exit(main())
