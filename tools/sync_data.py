#!/usr/bin/env python3
"""Copy the canonical game data into the Godot project.

design-doc/game.json is the canonical handoff data and must never be edited by
hand inside the game project. This tool copies it byte for byte to
src/game/data/game.json, verifies that both files parse as UTF-8 JSON and prints
a SHA-256 hash so builds and agents can tell which data revision they use.

Usage:
    python tools/sync_data.py            copy and verify
    python tools/sync_data.py --check    only verify that the copy is in sync
                                         (exit code 1 when it is missing or stale)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE = REPO_ROOT / "design-doc" / "game.json"
TARGET = REPO_ROOT / "src" / "game" / "data" / "game.json"

# Top-level collections whose sizes are printed as a quick sanity check.
SUMMARY_COLLECTIONS = ("rooms", "characters", "items", "actions", "puzzles", "quests", "cutscenes", "connections")


def sha256_of(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def normalize_newlines(data: bytes) -> bytes:
    """Git with core.autocrlf may turn LF into CRLF on checkout; treat both as equal."""
    return data.replace(b"\r\n", b"\n")


def parse_json(path: Path) -> dict:
    """Parse a JSON file strictly as UTF-8 (a BOM is reported as an error)."""
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        raise ValueError(f"{path}: starts with a UTF-8 BOM; the game expects plain UTF-8")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError(f"{path}: not valid UTF-8 ({error})") from error
    try:
        data = json.loads(text)
    except json.JSONDecodeError as error:
        raise ValueError(f"{path}: invalid JSON at line {error.lineno}, column {error.colno}: {error.msg}") from error
    if not isinstance(data, dict):
        raise ValueError(f"{path}: top-level value must be a JSON object")
    return data


def describe(data: dict) -> str:
    parts = [f"version {data.get('version', '?')}"]
    for name in SUMMARY_COLLECTIONS:
        value = data.get(name)
        if isinstance(value, list):
            parts.append(f"{name} {len(value)}")
    return ", ".join(parts)


def is_in_sync() -> bool:
    if not TARGET.exists():
        return False
    return normalize_newlines(SOURCE.read_bytes()) == normalize_newlines(TARGET.read_bytes())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", help="verify only, do not copy")
    args = parser.parse_args()

    if not SOURCE.exists():
        print(f"ERROR: canonical data not found: {SOURCE}", file=sys.stderr)
        return 2
    try:
        source_data = parse_json(SOURCE)
    except ValueError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2

    if args.check:
        if not is_in_sync():
            state = "missing" if not TARGET.exists() else "out of date"
            print(f"ERROR: {TARGET.relative_to(REPO_ROOT).as_posix()} is {state}; run tools/sync_data.py", file=sys.stderr)
            return 1
    else:
        TARGET.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(SOURCE, TARGET)

    try:
        target_data = parse_json(TARGET)
    except ValueError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2
    if target_data != source_data:
        print("ERROR: the copied file parses to different data than the source", file=sys.stderr)
        return 2

    raw = TARGET.read_bytes()
    action = "in sync" if args.check else "copied"
    print(f"{action}: {SOURCE.relative_to(REPO_ROOT).as_posix()} -> {TARGET.relative_to(REPO_ROOT).as_posix()}")
    print(f"size: {len(raw)} bytes")
    print(f"sha256: {sha256_of(raw)}")
    print(f"sha256 (LF-normalized): {sha256_of(normalize_newlines(raw))}")
    print(f"content: {describe(target_data)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
