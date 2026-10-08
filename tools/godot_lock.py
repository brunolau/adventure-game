"""Serialise Godot processes between parallel agents working in the same project folder.

Two Godot processes importing or exporting the same project at once can corrupt .godot/imported. Every agent that
starts Godot (import, export, headless tests, tools/qa_godot.py) while another agent may be working runs it through
this wrapper:

    python tools/godot_lock.py run --label ports -- <command ...>
    python tools/godot_lock.py status

The lock is the file build/locks/godot.lock (created atomically, holds label, pid and start time). A lock older than
MAX_AGE_S or whose process no longer exists is treated as stale and taken over.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / "build" / "locks" / "godot.lock"
MAX_AGE_S = 3 * 3600
POLL_S = 10


def _alive(pid: int) -> bool:
    if sys.platform == "win32":
        out = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"], capture_output=True, text=True).stdout
        return str(pid) in out
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _read() -> dict | None:
    try:
        return json.loads(LOCK.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def acquire(label: str) -> None:
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    waited = 0
    while True:
        try:
            fd = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            with os.fdopen(fd, "w", encoding="utf-8") as h:
                json.dump({"label": label, "pid": os.getpid(), "since": time.time()}, h)
            return
        except FileExistsError:
            info = _read()
            stale = info is None or time.time() - info.get("since", 0) > MAX_AGE_S or not _alive(int(info.get("pid", 0)))
            if stale:
                LOCK.unlink(missing_ok=True)
                continue
            if waited % 300 == 0:
                print(f"[godot_lock] waiting for '{info.get('label')}' (pid {info.get('pid')})", flush=True)
            time.sleep(POLL_S)
            waited += POLL_S


def release() -> None:
    info = _read()
    if info and info.get("pid") == os.getpid():
        LOCK.unlink(missing_ok=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--label", required=True)
    r.add_argument("command", nargs=argparse.REMAINDER)
    sub.add_parser("status")
    a = ap.parse_args()
    if a.cmd == "status":
        print(_read() or "free")
        return 0
    cmd = a.command[1:] if a.command[:1] == ["--"] else a.command
    if not cmd:
        ap.error("give the command after --")
    acquire(a.label)
    try:
        return subprocess.run(cmd).returncode
    finally:
        release()


if __name__ == "__main__":
    raise SystemExit(main())
