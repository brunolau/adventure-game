"""AT19 OS-level keyboard check: play the 2020 prologue from the main menu with real Windows key messages only.

    python tools/keyboard_os_check.py [--exe build/windows_debug/LastBell.exe] [--log build/m5/verify/logs/os_keys.txt]

The in-engine keyboard route (`--play-all --keyboard`, scripts/Diagnostics/KeyboardDriver.cs) injects Godot key events.
This script checks the same path one level lower: it starts a debug build hidden and unfocused (like tools/qa_godot.py),
with the game arguments `--menu --watch` (a player's start: main menu, first-start tips, autosave; the harness only
prints what it sees, `HARNESS watch ...`), and posts WM_KEYDOWN / WM_KEYUP messages to the game window. No mouse
message is ever sent and the real cursor is never moved. It decides each key from the watch lines, as a player decides
from the screen (focus ring = `focus=` / `gui=`).

Route: main menu (Nová hra) -> tips -> intro -> G01 ... G11 incl. P01 (one wrong answer first) -> CS01 -> S11 1995;
on the way Space held (markers), I / J / H / M (fast travel by keys), save into slot 1 from the pause menu, load it,
and quit from the pause menu. The player's saves and settings in %APPDATA%/LastBell are moved aside first and restored at the end.
Exit code 0 when every step reached its expected state.
"""
from __future__ import annotations

import argparse
import ctypes
import ctypes.wintypes as wt
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APPDATA = Path(os.environ["APPDATA"]) / "LastBell"

user32 = ctypes.WinDLL("user32", use_last_error=True)
WM_KEYDOWN, WM_KEYUP = 0x0100, 0x0101
VK = {"Tab": 0x09, "Enter": 0x0D, "Shift": 0x10, "Esc": 0x1B, "Space": 0x20, "Backspace": 0x08,
      "I": 0x49, "J": 0x4A, "M": 0x4D, "H": 0x48, "T": 0x54, "Down": 0x28, "Up": 0x26, "Left": 0x25, "Right": 0x27}

SW_HIDE = 0
CREATE_NO_WINDOW = 0x08000000
BELOW_NORMAL = 0x00004000


class Game:
    def __init__(self, exe: Path, log: Path, extra: list[str]):
        self.log = log.open("w", encoding="utf-8")
        args = [str(exe)]
        if exe.name.startswith("Godot"):
            args += ["--path", str(ROOT / "src" / "game")]
        args += ["--max-fps", "60", "--resolution", "1920x1080", *extra, "--", "--menu", "--watch"]
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = SW_HIDE
        env = dict(os.environ, LASTBELL_QA_LAUNCHER="1")
        self.proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                                     startupinfo=si, creationflags=CREATE_NO_WINDOW | BELOW_NORMAL, env=env, cwd=str(ROOT))
        self.state: dict[str, str] = {}
        self.lines: list[str] = []
        self.lock = threading.Lock()
        threading.Thread(target=self._pump, daemon=True).start()
        self.hwnd = None
        self.keys = 0
        self.steps: list[tuple[str, bool, str]] = []

    def _pump(self):
        for raw in iter(self.proc.stdout.readline, b""):
            line = raw.decode("utf-8", "replace").rstrip()
            self.log.write(line + "\n")
            self.log.flush()
            if line.startswith("HARNESS watch "):
                # values may contain spaces (button texts): split only in front of the known keys
                parts = re.split(r" (?=(?:room|era|mode|done|last|inv|sel|line|idle|labels|focus|gui|modal)=)",
                                 line[len("HARNESS watch "):])
                st = dict(p.split("=", 1) for p in parts if "=" in p)
                with self.lock:
                    self.state = st
                    self.lines.append(line)

    def note(self, text: str):
        print(text, flush=True)
        self.log.write("OSKEYS " + text + "\n")
        self.log.flush()

    def find_window(self, timeout=60):
        pid = self.proc.pid
        found = []
        proto = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)

        def cb(hwnd, _):
            p = wt.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(p))
            if p.value == pid:
                buf = ctypes.create_unicode_buffer(256)
                user32.GetClassNameW(hwnd, buf, 256)
                if buf.value == "Engine":
                    found.append(hwnd)
            return True

        end = time.time() + timeout
        while time.time() < end and not found:
            user32.EnumWindows(proto(cb), 0)
            time.sleep(0.3)
        if not found:
            raise SystemExit("game window not found")
        self.hwnd = found[0]

    def key(self, name: str, down=True, up=True, hold=0.0):
        vk = VK[name]
        scan = user32.MapVirtualKeyW(vk, 0)
        lp_down = 1 | (scan << 16)
        lp_up = 1 | (scan << 16) | (1 << 30) | (1 << 31)
        if down:
            user32.PostMessageW(self.hwnd, WM_KEYDOWN, vk, lp_down)
            self.keys += 1
        if hold:
            time.sleep(hold)
        else:
            time.sleep(0.06)
        if up:
            user32.PostMessageW(self.hwnd, WM_KEYUP, vk, lp_up)
        time.sleep(0.12)

    def shift_tab(self):
        self.key("Shift", up=False)
        self.key("Tab")
        self.key("Shift", down=False)

    def get(self, k: str) -> str:
        with self.lock:
            return self.state.get(k, "")

    def wait(self, cond, timeout=60.0, what="") -> bool:
        end = time.time() + timeout
        while time.time() < end:
            with self.lock:
                st = dict(self.state)
            if st and cond(st):
                return True
            if self.proc.poll() is not None:
                return False
            time.sleep(0.1)
        self.note(f"TIMEOUT waiting for {what}: {self.state}")
        return False

    def idle(self, timeout=120.0):
        ok = self.wait(lambda s: s.get("idle") == "True" and s.get("modal") == "-", timeout, "idle world")
        time.sleep(0.4)
        return ok

    def step(self, name: str, ok: bool, detail=""):
        self.steps.append((name, ok, detail))
        self.note(f"{'OK  ' if ok else 'FAIL'} {name} {detail}")

    # -------------------------------------------------- composite moves

    def focus_target(self, target: str, limit=30) -> int:
        """Tab until the world focus is on the target; returns the presses (-1 if never)."""
        for n in range(limit):
            if self.get("focus") == target:
                return n
            self.key("Tab")
            time.sleep(0.15)
        return limit if self.get("focus") == target else -1

    def focus_gui(self, pattern: str, limit=40, back=False) -> int:
        rx = re.compile(pattern)
        for n in range(limit):
            if rx.search(self.get("gui")):
                return n
            if back:
                self.shift_tab()
            else:
                self.key("Tab")
            time.sleep(0.15)
        return limit if rx.search(self.get("gui")) else -1

    def use_target(self, target: str, expect_done: int, name: str):
        n = self.focus_target(target)
        if n < 0:
            self.step(name, False, f"Tab never focused {target} (focus {self.get('focus')})")
            return False
        self.key("Enter")
        ok = self.wait(lambda s: int(s.get("done", 0)) >= expect_done, 60, f"{name} committed")
        self.idle()
        self.step(name, ok, f"Tab x{n} + Enter on {target}; done={self.get('done')} inv={self.get('inv')}")
        return ok

    def go(self, exit_id: str, room: str):
        n = self.focus_target(exit_id)
        if n < 0:
            self.step(f"exit {exit_id}", False, f"not focusable (focus {self.get('focus')})")
            return False
        self.key("Enter")
        ok = self.wait(lambda s: s.get("room") == room, 60, f"arrive {room}")
        self.idle()
        if not ok:
            self.step(f"exit {exit_id}", False, f"room {self.get('room')}")
        return ok

    def select_item(self, item: str) -> bool:
        self.key("I")
        if not self.wait(lambda s: s.get("mode") == "Inventory" and s.get("gui", "-").startswith("slot:"), 10, "bag open with a focused slot"):
            self.step(f"select {item}", False, "bag did not open with a focused slot")
            return False
        n = self.focus_gui(r"^slot:" + re.escape(item) + "$", 20)
        self.key("Enter")
        ok = self.wait(lambda s: s.get("sel") == item, 10, f"{item} selected")
        self.key("I")
        self.wait(lambda s: s.get("mode") == "World", 10, "bag closed")
        self.step(f"select {item}", ok, f"I, Tab x{n}, Enter, I")
        return ok

    def topic(self, npc: str, label_rx: str, expect_done: int, name: str):
        n = self.focus_target(npc)
        self.key("Enter")
        if not self.wait(lambda s: s.get("mode") == "Dialogue" and s.get("line") == "-" and s.get("gui") != "-", 60, "topic menu"):
            self.step(name, False, "topic menu did not open with a focused topic")
            return False
        m = self.focus_gui(label_rx, 12)
        self.key("Enter")
        ok = self.wait(lambda s: int(s.get("done", 0)) >= expect_done, 60, f"{name} committed")
        # The menu comes back after the topic's lines (PT-S17): Esc leaves the conversation.
        self.wait(lambda s: s.get("line") == "-" and s.get("mode") in ("Dialogue", "World"), 120, "topic lines over")
        time.sleep(0.5)
        if self.get("mode") == "Dialogue":
            self.key("Esc")
        self.idle()
        self.step(name, ok, f"Tab x{n} + Enter on {npc}, Tab x{m} + Enter on the topic, Esc")
        return ok


def run(g: Game) -> None:
    g.find_window()
    g.note(f"window {g.hwnd:#x}")
    # Main menu: a fresh profile has no save, so "Nová hra" starts at once.
    if not g.wait(lambda s: s.get("modal") == "MainMenuScreen", 90, "main menu"):
        g.step("main menu", False, "not shown")
        return
    time.sleep(1.0)
    g.key("Tab")  # a menu button takes the focus (UiRoot gives the default focus on the first Tab)
    n = g.focus_gui(r"Nov", 10)
    g.key("Enter")
    started = g.wait(lambda s: s.get("modal") != "MainMenuScreen", 20, "menu closed")
    if g.get("modal") == "ConfirmDialog":
        g.focus_gui(r"Áno|Nová|Prepísať|OK", 6)
        g.key("Enter")
    g.step("main menu: Nová hra", started, f"Tab x{n + 1} + Enter")
    # First-start tips (a UI modal): Enter steps through, Esc closes.
    if g.wait(lambda s: s.get("modal") == "TipsOverlay" or s.get("room") == "S01", 30, "tips or S01"):
        for _ in range(8):
            if g.get("modal") != "TipsOverlay":
                break
            g.key("Enter")
            time.sleep(0.6)
        if g.get("modal") == "TipsOverlay":
            g.key("Esc")
    g.idle(180)
    g.step("intro over", g.get("room") == "S01", f"room={g.get('room')} modal={g.get('modal')}")

    # Space held: markers on while held.
    g.key("Space", up=False)
    shown = g.wait(lambda s: s.get("labels") == "True", 5, "markers on")
    g.key("Space", down=False)
    hidden = g.wait(lambda s: s.get("labels") == "False", 5, "markers off")
    g.step("Space hold markers", shown and hidden, f"on={shown} off after release={hidden}")

    g.use_target("S01.tools", 1, "G01 take the service bag")
    g.go("S01.to_S02", "S02")
    g.go("S02.to_S03", "S03")
    g.topic("S03.ELA", r"", 2, "G02 Ela: shopping list")
    g.go("S03.to_S04", "S04")
    g.select_item("ORDER")
    g.use_target("S04.DANA", 3, "G03 list to Dana")
    g.go("S04.to_S03", "S03")
    g.go("S03.to_S02", "S02")
    g.go("S02.to_S05", "S05")
    g.select_item("GROCERIES")
    g.use_target("S05.tray", 4, "G04 groceries on the table")
    g.go("S05.to_S06", "S06")
    g.topic("S06.MIRA20", r"", 5, "G05 Mira: key")

    # Journal (J), hints (H), map (M) by keys; Shift+Tab inside a screen.
    g.key("J")
    j = g.wait(lambda s: s.get("mode") == "Journal", 5, "journal")
    g.key("Tab"); g.key("Tab"); g.shift_tab()
    jf = g.get("gui") != "-"
    g.key("J")
    jc = g.wait(lambda s: s.get("mode") == "World", 5, "journal closed")
    g.step("J journal", j and jf and jc, f"open={j} focus={g.get('gui') if not jf else 'yes'} closed by J={jc}")
    g.key("H")
    h = g.wait(lambda s: s.get("modal") == "HintScreen", 5, "hints")
    g.key("Tab")
    hf = g.get("gui") != "-"
    g.key("Esc")
    hc = g.wait(lambda s: s.get("modal") == "-", 5, "hints closed")
    g.step("H hints", h and hf and hc, f"open={h} focus={hf} closed by Esc={hc}")
    g.key("M")
    m = g.wait(lambda s: s.get("mode") == "Map", 5, "map")
    time.sleep(0.6)
    # Fast travel S06 -> S05 by keys: region card of the current region, then the room card.
    n1 = g.focus_gui(r"^Region_", 20)
    g.key("Enter")
    time.sleep(0.6)
    n2 = g.focus_gui(r"^Room_S05", 20)
    g.key("Enter")
    ft = g.wait(lambda s: s.get("room") == "S05", 30, "fast travel to S05")
    g.idle()
    g.step("M map fast travel S06 -> S05", m and ft, f"Tab x{n1} + Enter (region), Tab x{n2} + Enter (room)")
    if g.get("mode") == "Map":
        g.key("M")
        g.idle()

    g.select_item("SHEDKEY")
    g.use_target("S05.shed_door", 6, "G06 unlock the workshop")

    # Save to slot 1 from the pause menu, all by keys.
    g.key("Esc")
    p = g.wait(lambda s: s.get("mode") == "Pause", 5, "pause")
    time.sleep(0.4)
    g.key("Tab")
    a = g.focus_gui(r"'Uložiť hru'", 12)
    g.key("Enter")
    sv = g.wait(lambda s: s.get("modal") == "SaveLoadScreen", 5, "save screen")
    time.sleep(0.5)
    g.key("Tab")
    b = g.focus_gui(r"'Uložiť'@", 12)  # the first slot's save button (all slots say "Uložiť")
    g.key("Enter")
    time.sleep(1.0)
    if g.get("modal") == "ConfirmDialog":
        g.key("Enter")
        time.sleep(0.8)
    slots = sorted(p.name for p in (APPDATA / "saves").glob("slot*.json"))
    saved = len(slots) > 0
    g.key("Esc")
    time.sleep(0.4)
    if g.get("mode") == "Pause":
        g.key("Esc")
    g.idle()
    g.step("save from the pause menu", p and sv and saved, f"Esc, Tab x{a + 1} + Enter, Tab x{b + 1} + Enter; files={slots}")

    g.go("S05.to_S09", "S09")
    g.use_target("S09.case", 7, "G07 chronometer")

    # Load slot 1 (back to S05 after G06), then play on.
    g.key("Esc")
    g.wait(lambda s: s.get("mode") == "Pause", 5, "pause")
    time.sleep(0.4)
    g.key("Tab")
    a = g.focus_gui(r"'Načítať hru'", 12)
    g.key("Enter")
    g.wait(lambda s: s.get("modal") == "SaveLoadScreen", 5, "load screen")
    time.sleep(0.5)
    g.key("Tab")
    b = g.focus_gui(r"'Načítať'@", 12)
    g.key("Enter")
    time.sleep(0.8)
    if g.get("modal") == "ConfirmDialog":
        g.focus_gui(r"'Načítať'|Áno|OK", 6)
        g.key("Enter")
    loaded = g.wait(lambda s: s.get("done") == "6" and s.get("room") == "S05", 30, "loaded slot 1")
    g.idle()
    g.step("load from the pause menu", loaded, f"Tab x{a + 1} + Enter, Tab x{b + 1} + Enter; room={g.get('room')} done={g.get('done')}")

    g.go("S05.to_S09", "S09")
    g.use_target("S09.case", 7, "G07 chronometer (after the load)")
    g.go("S09.to_S10", "S10")
    g.select_item("TOOLS")
    g.use_target("S10.chrono", 8, "G08 tools on the cradle")
    g.go("S10.to_S09", "S09")
    g.go("S09.to_S05", "S05")
    g.go("S05.to_S02", "S02")
    g.go("S02.to_S01", "S01")
    g.use_target("S01.fuse", 9, "G09 fuse")
    g.go("S01.to_S02", "S02")
    g.go("S02.to_S05", "S05")
    g.go("S05.to_S09", "S09")
    g.go("S09.to_S10", "S10")
    g.select_item("FUSE")
    g.use_target("S10.chrono", 10, "G10 fuse in the cradle")

    # P01 by keys: one wrong pairing first, then the right one.
    n = g.focus_target("S10.panel")
    g.key("Enter")
    if not g.wait(lambda s: s.get("mode") == "Puzzle", 60, "puzzle"):
        g.step("P01 opens", False, "")
        return
    time.sleep(1.0)
    left = ["kruh", "trojuholník", "štvorec"]

    def pair(lname: str, rname: str):
        g.focus_gui(r"^\S*'" + lname + r"\s+→", 20)
        g.key("Enter")
        time.sleep(0.2)
        g.focus_gui(r"'" + rname + r"'", 20)
        g.key("Enter")
        time.sleep(0.2)

    for l, r in zip(left, ["štvorec", "kruh", "trojuholník"]):
        pair(l, r)
    g.focus_gui(r"Potvrdiť", 20)
    g.key("Enter")
    time.sleep(2.0)
    wrong_ok = g.get("done") == "10"
    g.wait(lambda s: s.get("mode") == "Puzzle" and s.get("line") == "-", 30, "wrong answer line over")
    for l in left:
        pair(l, l)
    g.focus_gui(r"Potvrdiť", 20)
    g.key("Enter")
    solved = g.wait(lambda s: s.get("done") == "11", 30, "P01 solved")
    g.step("P01 wrong answer then solved by keys", wrong_ok and solved, f"wrong consumed nothing={wrong_ok}")
    arrived = g.wait(lambda s: s.get("room") == "S11" and s.get("era") == "1995", 240, "CS01 and arrival in S11")
    g.idle(120)
    g.step("CS01 and arrival S11 1995", arrived, f"room={g.get('room')} era={g.get('era')} inv={g.get('inv')}")

    # Quit from the pause menu by keys.
    g.key("Esc")
    g.wait(lambda s: s.get("mode") == "Pause", 5, "pause")
    time.sleep(0.4)
    g.key("Tab")
    a = g.focus_gui(r"'Ukončiť hru'", 12)
    g.key("Enter")
    time.sleep(0.8)
    if g.get("modal") == "ConfirmDialog":
        g.focus_gui(r"Ukončiť|Áno", 6)
        g.key("Enter")
    try:
        g.proc.wait(20)
        quit_ok = True
    except subprocess.TimeoutExpired:
        quit_ok = False
    g.step("quit from the pause menu", quit_ok, f"Tab x{a + 1} + Enter")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--exe", default=str(ROOT / "build" / "windows_debug" / "LastBell.exe"))
    ap.add_argument("--log", default=str(ROOT / "build" / "m5" / "verify" / "logs" / "os_keys.txt"))
    a = ap.parse_args()
    # The player's saves and settings are moved aside (a fresh profile: no save, first-start tips) and put back at
    # the end; logs and caches stay (other Godot runs may be writing their logs there).
    backup = ROOT / "build" / "m5" / "verify" / "appdata_backup"
    run_profile = ROOT / "build" / "m5" / "verify" / "os_keys_profile"
    personal = ["saves", "settings.cfg"]
    if backup.exists():
        raise SystemExit(f"{backup} exists: restore it to {APPDATA} first")
    backup.mkdir(parents=True)
    for name in personal:
        if (APPDATA / name).exists():
            shutil.move(str(APPDATA / name), str(backup / name))
    g = None
    try:
        g = Game(Path(a.exe), Path(a.log), [])
        run(g)
    finally:
        if g is not None and g.proc.poll() is None:
            g.proc.kill()
            g.proc.wait()
        if run_profile.exists():
            shutil.rmtree(run_profile)
        run_profile.mkdir(parents=True)
        for name in personal:
            if (APPDATA / name).exists():
                shutil.move(str(APPDATA / name), str(run_profile / name))
            if (backup / name).exists():
                shutil.move(str(backup / name), str(APPDATA / name))
        backup.rmdir()
    fails = [s for s in g.steps if not s[1]] if g else ["no run"]
    g.note(f"SUMMARY {len(g.steps)} steps, {len(fails)} failed, {g.keys} key presses")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
