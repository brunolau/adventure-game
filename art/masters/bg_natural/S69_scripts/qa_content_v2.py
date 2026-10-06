"""QA of the content v2 art before the world overlay is live (free; nothing in the live tree changes).

  overlay              QA_DIR/content_ext/world_ext.json from the writing draft (validated by content_ext.py)
  blocking [ROOMS]     tools/check_blocking.py --strict on a copy of data/blocking with install_content_v2.py
                       applied, against game.json + the QA world overlay (default rooms S69 S18 S37 S32 S38 S17)
  tree                 QA_DIR/game: a copy of src/game (with its import cache) with the blocking installed, for
                       tools/qa_godot.py --path QA_DIR/game -- --content-ext QA_DIR/content_ext ...

QA_DIR defaults to build/qa_content_v2 (git-ignored build output).
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
QA_DIR = ROOT / "build" / "qa_content_v2"
DRAFT = ROOT / "docs" / "writing" / "out" / "content_v2_draft.json"
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(HERE))
import install_content_v2 as inst  # noqa: E402


def cmd_overlay(_args) -> Path:
    out = QA_DIR / "content_ext" / "world_ext.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([sys.executable, "-X", "utf8", str(ROOT / "tools" / "content_ext.py"), "merge-world", str(DRAFT),
                    "--out", str(out)], check=True, cwd=ROOT)
    return out


def cmd_blocking(args) -> int:
    world = QA_DIR / "content_ext" / "world_ext.json"
    if not world.exists():
        cmd_overlay(args)
    copy = QA_DIR / "blocking"
    if copy.exists():
        shutil.rmtree(copy)
    shutil.copytree(ROOT / "src" / "game" / "data" / "blocking", copy)
    print("\n".join(inst.apply(copy)))
    import content_ext
    import check_blocking as cb
    original = content_ext.load_effective_game

    def with_qa_world(game_path=content_ext.CANONICAL_GAME_JSON, dialogue=content_ext.DIALOGUE_EXT,
                      travel=content_ext.TRAVEL_EXT, use_overlays=True, world=None):
        return original(game_path, dialogue, travel, use_overlays, world or world_qa)
    world_qa = world
    content_ext.load_effective_game = with_qa_world
    cb.BLOCKING = copy
    res_original = cb.res_path

    def res_in_copy(value: str):
        if value.startswith("res://data/blocking/"):
            return copy / value[len("res://data/blocking/"):]
        return res_original(value)
    cb.res_path = res_in_copy
    rooms = args.rooms or ["S69", "S18", "S37", "S32", "S38", "S17"]
    return cb.main(["--strict"] + rooms)


def cmd_tree(_args) -> None:
    world = QA_DIR / "content_ext" / "world_ext.json"
    if not world.exists():
        cmd_overlay(_args)
    dst = QA_DIR / "game"
    src = ROOT / "src" / "game"
    if dst.exists():
        shutil.rmtree(dst)
    ignore = shutil.ignore_patterns("*.tmp", "export_presets.cfg.bak")
    shutil.copytree(src, dst, ignore=ignore)
    print("\n".join(inst.apply(dst / "data" / "blocking")))
    print(f"QA tree {dst.relative_to(ROOT)}; run tools/qa_godot.py --path {dst} -- --content-ext {world.parent} ...")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["overlay", "blocking", "tree"])
    ap.add_argument("rooms", nargs="*")
    args = ap.parse_args()
    if args.cmd == "overlay":
        print(cmd_overlay(args))
    elif args.cmd == "blocking":
        sys.exit(cmd_blocking(args))
    else:
        cmd_tree(args)


if __name__ == "__main__":
    main()
