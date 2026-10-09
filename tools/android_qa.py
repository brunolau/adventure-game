"""Android QA on a headless emulator, without disturbing the person at the computer (docs/PORTS.md "Android").

Everything is private to this repository: the SDK and JDK in .tools/android, the AVD in .tools/android/avd, the
emulator / adb state in .tools/android/home, and an adb server of its own on port 5039 (ANDROID_ADB_SERVER_PORT), so an
Android Studio or adb of the user is never touched. The emulator always runs with -no-window -no-audio -no-boot-anim.

    python tools/android_qa.py create                 the AVD "lastbell_qa" (Pixel 7 profile 1080x2400, API 36, x86_64)
    python tools/android_qa.py start [--gpu MODE] [--cold] [--normal-priority]
                                                      boot the emulator and wait for Android. Default GPU mode "host":
                                                      the GPU of the PC renders off-screen (no window). The software
                                                      mode (swiftshader_indirect) cannot run the game: its GLES allows
                                                      261 fragment uniform vectors, the canvas shader of Godot needs more.
                                                      --cold: do not load the quick-boot snapshot (a start that loads it
                                                      can hang: the device is listed but no shell command answers, seen
                                                      2026-10-09). --normal-priority: when other work keeps the CPU busy
                                                      (the default is below normal).
    python tools/android_qa.py stop                   shut the emulator and the private adb server down
    python tools/android_qa.py install [apk]          default: build/ports/android_qa/LastBell-qa-x86_64.apk
    python tools/android_qa.py launch [-- QA args]    start the game; QA harness arguments after -- (debug APK only)
    python tools/android_qa.py kill                   force-stop the game
    python tools/android_qa.py shot NAME              build/screens/android/NAME.png (adb exec-out screencap)
    python tools/android_qa.py tap X Y                X Y in canvas px (1920x1080), mapped to the letterboxed screen
    python tools/android_qa.py doubletap X Y
    python tools/android_qa.py hold X Y [MS]          long press (default 800 ms)
    python tools/android_qa.py swipe X1 Y1 X2 Y2 [MS]
    python tools/android_qa.py back | home | resume   system back, home (app to the background), bring the app back
    python tools/android_qa.py size [WxH | reset]     override the display size (landscape), e.g. 2048x1536 for 4:3
    python tools/android_qa.py cutout [none|corner|double|tall|hole|waterfall]   emulate a display cutout
    python tools/android_qa.py log [--all] [--clear]  the game's log lines from logcat (godot / LastBell / crashes)
    python tools/android_qa.py meminfo                dumpsys meminfo of the game
    python tools/android_qa.py adb ARGS...            raw adb against the emulator
    python tools/android_qa.py smoke [--keep-data]    the touch smoke test (phone profile, debug APK installed): title
                                                      screen, Back, scrolling a list, new game, slide label, tap = take the tool bag, eye
                                                      markers, long press = look, inventory, item in hand, pause by Back,
                                                      double tap through the exit, Home + return (autosave, pause menu).
                                                      Screenshots build/screens/android/smoke_*.png; exit code 1 on a
                                                      failed check. Coordinates are those of room S01 at 200 % HUD scale.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / ".tools" / "android"
SDK = TOOLS / "sdk"
JDK = TOOLS / "jdk-17"
AVD_NAME = "lastbell_qa"
IMAGE = "system-images;android-36;default;x86_64"
PACKAGE = "eu.inviton.lastbell"
ACTIVITY = "com.godot.game.GodotAppLauncher"  # the exported launcher alias of com.godot.game.GodotApp
CONSOLE_PORT = 5582
SERIAL = f"emulator-{CONSOLE_PORT}"
ADB_PORT = "5039"
SHOTS = ROOT / "build" / "screens" / "android"
DEFAULT_APK = ROOT / "build" / "ports" / "android_qa" / "LastBell-qa-x86_64.apk"
CANVAS = (1920, 1080)
NO_WINDOW = 0x08000000 if os.name == "nt" else 0  # CREATE_NO_WINDOW: never a console window


def env() -> dict:
    e = dict(os.environ)
    e.update({
        "JAVA_HOME": str(JDK), "ANDROID_HOME": str(SDK), "ANDROID_SDK_ROOT": str(SDK),
        "ANDROID_AVD_HOME": str(TOOLS / "avd"), "ANDROID_USER_HOME": str(TOOLS / "home"),
        "ANDROID_EMULATOR_HOME": str(TOOLS / "home"), "ANDROID_ADB_SERVER_PORT": ADB_PORT,
    })
    e["PATH"] = os.pathsep.join([str(JDK / "bin"), str(SDK / "platform-tools"), e.get("PATH", "")])
    return e


def exe(name: str) -> str:
    return name + (".exe" if os.name == "nt" else "")


ADB = SDK / "platform-tools" / exe("adb")
EMULATOR = SDK / "emulator" / exe("emulator")


def adb(*args: str, capture: bool = True, binary: bool = False, check: bool = False, timeout: float | None = 120):
    cmd = [str(ADB), "-s", SERIAL, *args]
    res = subprocess.run(cmd, env=env(), capture_output=capture, timeout=timeout, creationflags=NO_WINDOW, stdin=subprocess.DEVNULL)
    if check and res.returncode != 0:
        raise SystemExit(f"adb {' '.join(args)} failed: {res.stderr.decode(errors='replace')[:400]}")
    if not capture:
        return res.returncode
    return res.stdout if binary else res.stdout.decode("utf-8", errors="replace")


def shell(command: str, **kw):
    return adb("shell", command, **kw)


def cmd_create() -> int:
    (TOOLS / "avd").mkdir(parents=True, exist_ok=True)
    (TOOLS / "home").mkdir(parents=True, exist_ok=True)
    manager = SDK / "cmdline-tools" / "latest" / "bin" / ("avdmanager.bat" if os.name == "nt" else "avdmanager")
    res = subprocess.run([str(manager), "create", "avd", "-n", AVD_NAME, "-k", IMAGE, "-d", "pixel_7", "--force"],
                         env=env(), input=b"no\n", capture_output=True, creationflags=NO_WINDOW)
    print(res.stdout.decode(errors="replace")[-600:], res.stderr.decode(errors="replace")[-600:])
    config = TOOLS / "avd" / f"{AVD_NAME}.avd" / "config.ini"
    text = config.read_text(encoding="utf-8")
    for key, value in {"hw.ramSize": "4096", "hw.gpu.enabled": "yes", "hw.gpu.mode": "host",
                       "disk.dataPartition.size": "6G", "vm.heapSize": "512M"}.items():
        text = re.sub(rf"^{re.escape(key)}=.*$", f"{key}={value}", text, flags=re.M)
    config.write_text(text, encoding="utf-8")
    return res.returncode


def running() -> bool:
    out = subprocess.run([str(ADB), "devices"], env=env(), capture_output=True, creationflags=NO_WINDOW, stdin=subprocess.DEVNULL).stdout.decode()
    return bool(re.search(rf"^{SERIAL}\s+device", out, re.M))


def cmd_start(args: list[str]) -> int:
    gpu = args[args.index("--gpu") + 1] if "--gpu" in args else "host"
    if running():
        print(f"{SERIAL} is already running")
        return 0
    log = ROOT / "build" / "ports" / "logs" / "emulator.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    cmd = [str(EMULATOR), "-avd", AVD_NAME, "-no-window", "-no-audio", "-no-boot-anim", "-no-metrics",
           "-gpu", gpu, "-port", str(CONSOLE_PORT), "-netfast"]
    if "--cold" in args:
        cmd.append("-no-snapshot-load")
    priority = 0x00000020 if "--normal-priority" in args else 0x00004000  # normal / below normal
    flags = NO_WINDOW | (priority if os.name == "nt" else 0)
    with log.open("wb") as fh:
        subprocess.Popen(cmd, env=env(), stdout=fh, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, creationflags=flags)
    print(f"emulator starting (log: {log.relative_to(ROOT)}), waiting for Android to boot ...", flush=True)
    t0 = time.time()
    while time.time() - t0 < 600:
        time.sleep(5)
        if running() and shell("getprop sys.boot_completed").strip() == "1":
            # Quiet device for tests: no animations, screen stays on, no lock screen.
            for c in ("settings put global window_animation_scale 0", "settings put global transition_animation_scale 0",
                      "settings put global animator_duration_scale 0", "svc power stayon true", "wm dismiss-keyguard",
                      "settings put secure immersive_mode_confirmations confirmed"):
                shell(c)
            print(f"booted in {time.time() - t0:.0f} s: Android {shell('getprop ro.build.version.release').strip()} "
                  f"(API {shell('getprop ro.build.version.sdk').strip()}), {shell('wm size').strip()}, {shell('wm density').strip()}")
            return 0
    print("the emulator did not boot within 10 minutes; see the log")
    return 1


def cmd_stop() -> int:
    if running():
        adb("emu", "kill")
        for _ in range(30):
            time.sleep(1)
            if not running():
                break
    subprocess.run([str(ADB), "kill-server"], env=env(), capture_output=True, creationflags=NO_WINDOW, stdin=subprocess.DEVNULL)
    print("emulator and the private adb server stopped")
    return 0


def screen() -> tuple[int, int]:
    """Size of the screen as the landscape game sees it (the long side is the width)."""
    out = shell("wm size")
    m = re.findall(r"(\d+)x(\d+)", out)
    w, h = (int(m[-1][0]), int(m[-1][1])) if m else (1080, 2400)
    return max(w, h), min(w, h)


def to_device(x: float, y: float) -> tuple[int, int]:
    """Canvas px (1920x1080, stretch aspect keep = centred, letterboxed) -> device px in landscape. The game view is
    the whole screen (immersive mode); LASTBELL_VIEW=left,top,right,bottom overrides it (a build that shows the bars)."""
    w, h = screen()
    left, top, right, bottom = 0, 0, w, h
    if os.environ.get("LASTBELL_VIEW"):
        left, top, right, bottom = (int(v) for v in os.environ["LASTBELL_VIEW"].split(","))
    vw, vh = right - left, bottom - top
    s = min(vw / CANVAS[0], vh / CANVAS[1])
    return round(left + (vw - CANVAS[0] * s) / 2 + x * s), round(top + (vh - CANVAS[1] * s) / 2 + y * s)


def cmd_shot(name: str) -> int:
    SHOTS.mkdir(parents=True, exist_ok=True)
    path = SHOTS / (name if name.endswith(".png") else name + ".png")
    data = adb("exec-out", "screencap", "-p", binary=True)
    if not data.startswith(b"\x89PNG"):
        print("screencap returned no PNG")
        return 1
    path.write_bytes(data)
    print(f"{path.relative_to(ROOT)} ({len(data) / 1e6:.2f} MB)")
    return 0


def cmd_log(args: list[str]) -> int:
    if "--clear" in args:
        adb("logcat", "-c")
        return 0
    out = adb("logcat", "-d", "-v", "time")
    keep = re.compile(r"godot|LastBell|HARNESS|FATAL|AndroidRuntime|DEBUG   :|libc    :|mono|monodroid|lowmemory|ActivityManager: (Process|Killing).*lastbell", re.I)
    for line in out.splitlines():
        if "--all" in args or keep.search(line):
            print(line)
    return 0


def game_log() -> str:
    return chr(10).join(l for l in adb("logcat", "-d", "-v", "time").splitlines() if "godot" in l.lower())


def wait_log(pattern: str, seconds: float) -> bool:
    t0 = time.time()
    while time.time() - t0 < seconds:
        if re.search(pattern, game_log()):
            return True
        time.sleep(2)
    return False


def autosave() -> dict:
    """The autosave of the installed debug build (run-as), or {}."""
    import json
    text = shell(f"run-as {PACKAGE} cat files/saves/autosave.json")
    try:
        return json.loads(text)
    except ValueError:
        return {}


def cmd_smoke(args: list[str]) -> int:
    results: list[tuple[str, bool, str]] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        results.append((name, ok, detail))
        print(("PASS " if ok else "FAIL ") + name + (f"  ({detail})" if detail else ""), flush=True)

    def tap(x: float, y: float, wait: float = 1.0) -> None:
        dx, dy = to_device(x, y)
        shell(f"input touchscreen tap {dx} {dy}")
        time.sleep(wait)

    def hold(x: float, y: float, ms: int = 900, wait: float = 0.6) -> None:
        dx, dy = to_device(x, y)
        shell(f"input touchscreen swipe {dx} {dy} {dx} {dy} {ms}")
        time.sleep(wait)

    def back(wait: float = 1.2) -> None:
        shell("input keyevent KEYCODE_BACK")
        time.sleep(wait)

    w, h = screen()
    if (w, h) != (2400, 1080):
        print(f"the smoke test expects the phone profile 2400x1080, the display is {w}x{h} (android_qa.py size reset)")
        return 2
    shell(f"am force-stop {PACKAGE}")
    if "--keep-data" not in args:
        shell(f"pm clear {PACKAGE}")
    adb("logcat", "-c")
    shell(f"am start -W -n {PACKAGE}/{ACTIVITY}")
    check("the game starts and draws its first frame", wait_log(r"LastBell: first frame drawn", 120))
    time.sleep(4)
    cmd_shot("smoke_01_title")
    back()
    cmd_shot("smoke_02_back_asks_to_quit")
    check("Back on the title screen is one request", len(re.findall(r"Back request, mode", game_log())) == 1)
    back()  # closes the question
    # Lists: a finger that slides over a column of buttons scrolls it (UI/Common/TouchScroller; owner report
    # 2026-10-09: nothing scrolled, because a press on a button never reaches Godot's scroll container). Here: the
    # tabs of the settings, a column of seven buttons with room for five; the slide starts on the "Display" tab and
    # must not press it.
    tap(1350, 538, 1.5)  # Settings (a fresh install has no Continue button above it)
    cmd_shot("smoke_02b_settings")
    x1, y1 = to_device(350, 790)
    x2, y2 = to_device(380, 360)
    shell(f"input touchscreen swipe {x1} {y1} {x2} {y2} 450")
    time.sleep(2.5)
    cmd_shot("smoke_02c_settings_scrolled")
    ends = re.findall(r"touch scroll of \S+ ended at (\d+),(\d+)", game_log())
    check("a finger slide over buttons scrolls the list", bool(ends) and int(ends[-1][1]) > 0, f"scroll ended at {ends[-1] if ends else None}")
    back()  # closes the settings
    tap(1350, 225, 2.5)  # New game
    cmd_shot("smoke_03_new_game")
    tap(1470, 968, 1.0)  # Start game
    check("a new game builds the first room", wait_log(r"LastBell: first room S01 built", 90))
    time.sleep(7)
    for _ in range(3):
        tap(960, 300, 0.8)  # the opening lines
    time.sleep(1.5)
    cmd_shot("smoke_04_room_s01")
    # A finger sliding across the picture: the names follow it, lifting does nothing.
    x1, y1 = to_device(300, 700)
    x2, y2 = to_device(1500, 620)
    slide = subprocess.Popen([str(ADB), "-s", SERIAL, "shell", f"input touchscreen swipe {x1} {y1} {x2} {y2} 3000"], env=env(),
                             creationflags=NO_WINDOW, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2.0)
    cmd_shot("smoke_05_slide_shows_names")
    slide.wait(timeout=30)
    time.sleep(1.0)
    check("a slide takes nothing", "TOOLS" not in autosave().get("inventory", []))
    tap(730, 817, 0.2)  # the tool bag on the chair
    cmd_shot("smoke_06_tap_label_and_walk")
    time.sleep(6)
    for _ in range(4):
        tap(960, 300, 0.8)
    time.sleep(1.0)
    save = autosave()
    check("a tap takes the tool bag (autosave: TOOLS, G01 done)", "TOOLS" in save.get("inventory", []) and "G01" in save.get("done", []),
          f"inventory {save.get('inventory')}")
    tap(361, 998, 0.8)  # the Eye button latches
    cmd_shot("smoke_07_eye_markers")
    time.sleep(6.5)
    hold(520, 650)  # the pot of screws: look
    cmd_shot("smoke_08_long_press_look")
    time.sleep(4)
    tap(960, 300, 0.8)
    tap(193, 998, 1.5)  # Inventory
    cmd_shot("smoke_09_inventory")
    hold(550, 840)  # the tool bag slot: look
    cmd_shot("smoke_10_inventory_long_press_look")
    time.sleep(2.5)
    tap(550, 840, 1.2)  # take it in hand: the drawer closes
    cmd_shot("smoke_11_item_in_hand")
    hold(1000, 950)  # hold on the floor: the selection is cancelled
    cmd_shot("smoke_12_hold_cancels_item")
    adb("logcat", "-c")
    back()
    cmd_shot("smoke_13_back_opens_pause")
    back()
    time.sleep(0.5)
    acted = re.findall(r"Back request, mode (\w+)", game_log())
    check("Back opens and closes the pause menu", acted == ["World", "Pause"], f"requests that acted, by mode: {acted}")
    dx, dy = to_device(1150, 600)
    shell(f"input touchscreen tap {dx} {dy} & input touchscreen tap {dx} {dy}")  # double tap on the exit: no walk
    time.sleep(6)
    for _ in range(3):
        tap(960, 300, 0.8)
    cmd_shot("smoke_14_double_tap_exit_s02")
    check("a double tap goes through the exit (autosave: room S02)", autosave().get("room") == "S02", f"room {autosave().get('room')}")
    adb("logcat", "-c")
    shell("input keyevent KEYCODE_HOME")
    time.sleep(4)
    shell(f"am start -n {PACKAGE}/{ACTIVITY}")
    time.sleep(3)
    cmd_shot("smoke_15_back_from_home_paused")
    log = game_log()
    check("Home: autosave written", "app to the background, autosave written" in log)
    check("return: the pause menu", "app back in the foreground, paused" in log)
    crashes = [l for l in adb("logcat", "-d", "-v", "time").splitlines() if re.search(r"FATAL EXCEPTION|SIGSEGV|signal 11 ", l)]
    check("no crash in logcat", not crashes, crashes[0][:100] if crashes else "")
    failed = [r for r in results if not r[1]]
    print(f"smoke test: {len(results) - len(failed)}/{len(results)} checks passed; screenshots in {SHOTS.relative_to(ROOT)}")
    return 1 if failed else 0


def main(argv: list[str]) -> int:
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    cmd, args = argv[0], argv[1:]
    if cmd == "create":
        return cmd_create()
    if cmd == "start":
        return cmd_start(args)
    if cmd == "stop":
        return cmd_stop()
    if cmd == "install":
        apk = Path(args[0]) if args else DEFAULT_APK
        print(adb("install", "-r", "-g", str(apk), timeout=1800).strip()[-300:])
        return 0
    if cmd == "launch":
        extra = args[args.index("--") + 1:] if "--" in args else []
        command = f"am start -W -n {PACKAGE}/{ACTIVITY}"
        if extra:
            # The Godot activity reads its command line from this string-array extra (debug builds honour QA flags).
            command += " --esa command_line_params " + ",".join(["--"] + extra)
        print(shell(command).strip())
        return 0
    if cmd == "kill":
        shell(f"am force-stop {PACKAGE}")
        return 0
    if cmd == "shot":
        return cmd_shot(args[0])
    if cmd == "tap":
        x, y = to_device(float(args[0]), float(args[1]))
        shell(f"input touchscreen tap {x} {y}")
        return 0
    if cmd == "doubletap":
        x, y = to_device(float(args[0]), float(args[1]))
        shell(f"input touchscreen tap {x} {y} & input touchscreen tap {x} {y}")  # two taps about 100 ms apart
        return 0
    if cmd == "hold":
        x, y = to_device(float(args[0]), float(args[1]))
        ms = int(args[2]) if len(args) > 2 else 800
        shell(f"input touchscreen swipe {x} {y} {x} {y} {ms}")
        return 0
    if cmd == "swipe":
        x1, y1 = to_device(float(args[0]), float(args[1]))
        x2, y2 = to_device(float(args[2]), float(args[3]))
        ms = int(args[4]) if len(args) > 4 else 600
        shell(f"input touchscreen swipe {x1} {y1} {x2} {y2} {ms}")
        return 0
    if cmd == "back":
        shell("input keyevent KEYCODE_BACK")
        return 0
    if cmd == "home":
        shell("input keyevent KEYCODE_HOME")
        return 0
    if cmd == "resume":
        print(shell(f"am start -n {PACKAGE}/{ACTIVITY}").strip())
        return 0
    if cmd == "size":
        if not args:
            print(shell("wm size").strip())
        elif args[0] == "reset":
            shell("wm size reset")
        else:
            w, h = (int(v) for v in args[0].lower().split("x"))
            shell(f"wm size {min(w, h)}x{max(w, h)}")  # the AVD's natural orientation is portrait
        return 0
    if cmd == "cutout":
        kind = args[0] if args else "none"
        overlays = [l.split()[-1] for l in shell("cmd overlay list").splitlines() if "display.cutout.emulation" in l]
        for o in overlays:
            shell(f"cmd overlay disable {o}")
        if kind != "none":
            match = [o for o in overlays if o.endswith("." + kind)]
            if not match:
                print("available:", ", ".join(o.rsplit(".", 1)[-1] for o in overlays))
                return 1
            shell(f"cmd overlay enable {match[0]}")
        return 0
    if cmd == "log":
        return cmd_log(args)
    if cmd == "meminfo":
        print(shell(f"dumpsys meminfo {PACKAGE}"))
        return 0
    if cmd == "adb":
        return adb(*args, capture=False, timeout=None)
    if cmd == "smoke":
        return cmd_smoke(args)
    print(f"unknown command {cmd}\n{__doc__}")
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
