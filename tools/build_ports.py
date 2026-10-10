"""Build the ports of Posledny zvonec (LastBell): Linux, macOS, Android and iOS (docs/PORTS.md).

Windows stays with build.bat (build/windows/). This script writes everything to build/ports/<platform>/:

    python tools/build_ports.py                    all ports this host can build (Windows host: linux, linux-arm64,
                                                   macos, android, android-aab; macOS host: also ios)
    python tools/build_ports.py linux macos        only these targets
    python tools/build_ports.py android-qa         the x86_64 debug APK for the emulator smoke test
    python tools/build_ports.py stage              only refresh the mobile staging copy (mobile texture set) + import
    python tools/build_ports.py keystores          create the local Android keystores (once; kept out of git)
    python tools/build_ports.py verify             check the artifacts in build/ports/ (structure, sizes, signatures)
    python tools/build_ports.py texture-report     estimated texture memory of the desktop and the mobile texture set

Targets: linux (x86_64), linux-arm64, macos (universal .app in a zip), android (signed release APK, arm64-v8a),
android-aab (Google Play bundle, gradle build), android-qa (debug APK, x86_64, for an emulator), ios (Xcode project;
macOS host only: C# on iOS is compiled ahead of time with Xcode tools).
Options: --skip-import (the projects are already imported), --no-lock (do not wait for tools/godot_lock.py),
--keep-stage (Android / iOS: export the staging copy as it is, without refreshing it from src/game; for trying a change
in the copy first).

How it works:
- Desktop ports export from src/game with the same release settings as Windows: release template (the QA harness is
  off, ISSUES BUILD-03), version 0.3.0, Lossy texture import and the release export filter (tools/release_assets.py).
- Android and iOS export from a staging copy of the project, build/ports/_stage/src/game (git-ignored), in which
  the large painted textures (backgrounds, actor sheets, cutscenes, ambient cut-outs) are imported as Basis
  Universal instead of Lossy WebP: the GPU keeps them block-compressed (ASTC 4x4 / ETC2, 1 byte per pixel instead of
  4), which is what phones need (ISSUES BUILD-06). The desktop project and its imports are never changed. The copy
  keeps its own .godot/imported, so a second run only re-imports what changed.
- Every Godot process on src/game runs under tools/godot_lock.py (label "ports"): parallel agents share the project
  folder. Godot processes on the staging copy use their own lock (build/locks/godot_stage.lock) and run at
  below-normal priority (the first Basis Universal import keeps every core busy for a long time).
- Android toolchain (docs/PORTS.md "Android"): a JDK 17 in .tools/android/jdk-17 and the Android SDK in
  .tools/android/sdk (platform-tools, build-tools 36.1.0, platforms;android-36) are preferred; JAVA_HOME /
  ANDROID_HOME and the usual install folders are the fallback. Godot reads both paths only from its EDITOR settings
  (export/android/java_sdk_path, android_sdk_path), and every Godot editor process rewrites that file when it
  exits, so on Windows the Android exports get their own Godot configuration: .tools/android/godot_appdata is passed
  as APPDATA and holds editor_settings-4.7.tres (written here: the two paths and the debug keystore) and a
  directory junction to the installed export templates. The user's own editor settings are never changed.
- Android signing: the release keystore and its password live in .tools/android/keystore.json (git-ignored, made
  by "keystores"); they are handed to Godot through GODOT_ANDROID_KEYSTORE_RELEASE_* environment variables, never
  written into export_presets.cfg.
Needs: Godot 4.7.2 .NET + its export templates (see build.bat), .NET SDK 8+ (9 for Android), Python 3, for Android a
JDK 17 and the Android SDK (see above), internet access for the first .NET Android restore and for the AAB (Gradle).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import plistlib
import re
import shutil
import struct
import subprocess
import sys
import tarfile
import time
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
GAME = SRC / "game"
OUT = ROOT / "build" / "ports"
LOGS = OUT / "logs"
STAGE = OUT / "_stage" / "src"
STAGE_GAME = STAGE / "game"
TOOLS = ROOT / ".tools"
ANDROID_TOOLS = TOOLS / "android"                 # jdk-17/, sdk/, keystores, keystore.json, godot_appdata/
GODOT_APPDATA = ANDROID_TOOLS / "godot_appdata"   # private Godot editor configuration of the Android exports
VERSION = "0.3.0"
APP = "PoslednyZvonec"
GODOT_VERSION = "4.7.2.stable.mono"

sys.path.insert(0, str(ROOT / "tools"))
import godot_lock  # noqa: E402

# ------------------------------------------------------------------ mobile texture set (staging copy only)

# Folders whose textures the mobile build imports as Basis Universal (UASTC, RDO + zstd). Everything else keeps the
# desktop import (lossless UI, cursors, icons, item icons, fonts).
MOBILE_BASIS_FOLDERS = (
    "assets/bg_natural/", "assets/cutscenes/", "assets/actors/", "assets/ambient/",
    "assets/variants_natural/", "assets/fg_natural/",
)
MOBILE_PARAMS = {
    "compress/mode": "4",            # Basis Universal
    "compress/uastc_level": "2",     # UASTC level (0 fastest .. 4 slowest/best)
    "compress/rdo_quality_loss": "0.75",  # RDO: smaller files, nearly invisible on painted art
    "mipmaps/generate": "false",
}
MOBILE_POLICY = "basis-uastc2-rdo0.75-v1"  # change when MOBILE_PARAMS change: the staging copy re-imports


def is_windows() -> bool:
    return os.name == "nt"


def is_macos() -> bool:
    return sys.platform == "darwin"


def log(msg: str) -> None:
    print(f"[ports] {msg}", flush=True)


def human(n: float) -> str:
    return f"{n / 1e6:.1f} MB"


def godot_exe() -> Path:
    env = os.environ.get("GODOT_EXE")
    if env:
        return Path(env)
    if is_windows():
        return TOOLS / "godot" / "Godot_v4.7.2-stable_mono_win64" / "Godot_v4.7.2-stable_mono_win64_console.exe"
    if is_macos():
        return TOOLS / "godot" / "Godot_mono.app" / "Contents" / "MacOS" / "Godot"
    return TOOLS / "godot" / "Godot_v4.7.2-stable_mono_linux_x86_64" / "Godot_v4.7.2-stable_mono_linux.x86_64"


def templates_dir() -> Path:
    if os.environ.get("GODOT_TEMPLATES"):
        return Path(os.environ["GODOT_TEMPLATES"])
    if is_windows():
        return Path(os.environ["APPDATA"]) / "Godot" / "export_templates" / GODOT_VERSION
    if is_macos():
        return Path.home() / "Library" / "Application Support" / "Godot" / "export_templates" / GODOT_VERSION
    return Path.home() / ".local" / "share" / "godot" / "export_templates" / GODOT_VERSION


def run(cmd: list[str], log_file: Path | None = None, env: dict | None = None, cwd: Path | None = None, check: bool = True,
        low_priority: bool = False) -> int:
    shown = " ".join(str(c) for c in cmd)
    log(f"$ {shown}" + (f"  (log: {log_file.relative_to(ROOT)})" if log_file else ""))
    full_env = dict(os.environ, **(env or {}))
    extra: dict = {}
    if low_priority and is_windows():
        extra["creationflags"] = 0x00004000  # BELOW_NORMAL_PRIORITY_CLASS (inherited by the dotnet / Gradle children)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        with log_file.open("w", encoding="utf-8", errors="replace") as fh:
            rc = subprocess.run([str(c) for c in cmd], stdout=fh, stderr=subprocess.STDOUT, env=full_env, cwd=cwd, **extra).returncode
    else:
        rc = subprocess.run([str(c) for c in cmd], env=full_env, cwd=cwd, **extra).returncode
    if check and rc != 0:
        tail = log_file.read_text(encoding="utf-8", errors="replace").splitlines()[-30:] if log_file else []
        print("\n".join(tail))
        raise SystemExit(f"[ports] command failed with exit code {rc}: {shown}")
    return rc


class Lock:
    """tools/godot_lock.py around one Godot process (re-entrant within this script). src/game shares the agents'
    lock; the staging copy has its own lock file, so a mobile import never waits for (or blocks) work on src/game."""

    enabled = True
    depth: dict[Path, int] = {}

    def __init__(self, stage: bool = False):
        self.path = godot_lock.LOCK.with_name("godot_stage.lock") if stage else godot_lock.LOCK

    def _call(self, fn, *args):
        main_lock = godot_lock.LOCK
        godot_lock.LOCK = self.path
        try:
            return fn(*args)
        finally:
            godot_lock.LOCK = main_lock

    def __enter__(self):
        if Lock.enabled and Lock.depth.get(self.path, 0) == 0:
            self._call(godot_lock.acquire, "ports")
        Lock.depth[self.path] = Lock.depth.get(self.path, 0) + 1
        return self

    def __exit__(self, *exc):
        Lock.depth[self.path] -= 1
        if Lock.enabled and Lock.depth[self.path] == 0:
            self._call(godot_lock.release)


def is_stage(project: Path) -> bool:
    return STAGE.resolve() in project.resolve().parents


# Godot's console wrapper waits for every process of its job, also for the build servers a C# export can leave behind
# (the Roslyn compiler server and MSBuild worker nodes stay alive for 10 to 15 minutes; seen 2026-10-08: the export was
# done, the script waited for VBCSCompiler). The C# build of a Godot run therefore uses no shared servers.
NO_BUILD_SERVERS = {"UseSharedCompilation": "false", "MSBUILDDISABLENODEREUSE": "1", "DOTNET_CLI_USE_MSBUILD_SERVER": "0"}


def godot(project: Path, args: list[str], log_name: str, env: dict | None = None, check: bool = True) -> int:
    stage = is_stage(project)
    with Lock(stage):
        return run([godot_exe(), "--headless", "--path", project, *args], LOGS / f"{log_name}.log",
                   env={**NO_BUILD_SERVERS, **(env or {})}, check=check, low_priority=stage)


# ------------------------------------------------------------------ prerequisites

def prechecks(need_android: bool) -> None:
    exe = godot_exe()
    if not exe.exists():
        raise SystemExit(f"Godot 4.7.2 .NET not found at {exe} (set GODOT_EXE). See docs/BUILD.md.")
    tpl = templates_dir()
    if not (tpl / "version.txt").exists():
        raise SystemExit(f"Export templates {GODOT_VERSION} not found in {tpl} (set GODOT_TEMPLATES). See docs/BUILD.md.")
    if shutil.which("dotnet") is None:
        raise SystemExit("The .NET SDK (8 or newer; 9 for Android) is required: https://dotnet.microsoft.com/download")
    py = [sys.executable, "-X", "utf8"]
    run(py + [str(ROOT / "tools" / "release_assets.py"), "imports"])
    run(py + [str(ROOT / "tools" / "release_assets.py"), "filter", "--check"])
    run(py + [str(ROOT / "art" / "tools" / "regrid_sheets.py"), "--check"])
    if need_android and java_home() is None:
        raise SystemExit("A JDK 17 is required for Android: unpack one into .tools/android/jdk-17 (docs/PORTS.md), or set JAVA_HOME.")
    if need_android and android_sdk() is None:
        raise SystemExit("The Android SDK is required for Android: .tools/android/sdk with platform-tools, build-tools;36.1.0 and "
                         "platforms;android-36 (docs/PORTS.md), or set ANDROID_HOME.")


def java_home() -> Path | None:
    """The JDK 17 for keytool, apksigner and Gradle: the one in .tools first, then JAVA_HOME and the usual places."""
    for cand in [str(ANDROID_TOOLS / "jdk-17"), os.environ.get("JAVA_HOME"), r"C:\Program Files\Java\jdk-17",
                 "/usr/lib/jvm/java-17-openjdk-amd64", "/Library/Java/JavaVirtualMachines/jdk-17.jdk/Contents/Home",
                 str(TOOLS / "jdk-17")]:
        if cand and (Path(cand) / "bin" / ("keytool.exe" if is_windows() else "keytool")).exists():
            return Path(cand)
    return None


def build_csharp(project_dir: Path) -> None:
    run(["dotnet", "build", str(project_dir / "LastBell.csproj"), "-c", "Debug", "-nologo", "-v", "q"])


# ------------------------------------------------------------------ desktop

def export(project: Path, preset: str, target: Path, log_name: str, debug: bool = False, env: dict | None = None,
           extra: list[str] | None = None) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    godot(project, [*(extra or []), "--export-debug" if debug else "--export-release", preset, str(target)], log_name, env=env)
    if not target.exists():
        raise SystemExit(f"[ports] export of '{preset}' produced no {target}")


def build_linux(arch: str) -> Path:
    folder = OUT / f"linux_{arch}"
    app = folder / APP
    if folder.exists():
        shutil.rmtree(folder)
    binary = app / f"LastBell.{arch}"
    export(GAME, f"Linux {arch}", binary, f"export_linux_{arch}")
    readme = app / "README.txt"
    readme.write_text(
        f"Posledny zvonec {VERSION} (Linux {arch})\n\n"
        f"Start: ./LastBell.{arch}   (keep LastBell.pck and data_LastBell_linuxbsd_{arch}/ next to it)\n"
        "Saves and settings: ~/.local/share/LastBell/\n"
        "Needs a 64-bit Linux with glibc 2.31+ and OpenGL 3.3 (or OpenGL ES 3.0) graphics.\n", encoding="utf-8")
    archive = OUT / f"{APP}-{VERSION}-linux-{arch}.tar.gz"
    with tarfile.open(archive, "w:gz", compresslevel=6) as tar:
        for path in sorted(app.rglob("*")):
            info = tar.gettarinfo(str(path), arcname=f"{APP}/{path.relative_to(app).as_posix()}")
            if path.is_file():
                executable = path == binary or path.suffix == ".so" or path.name.endswith(".so")
                info.mode = 0o755 if path == binary else (0o755 if executable else 0o644)
                with path.open("rb") as fh:
                    tar.addfile(info, fh)
            else:
                info.mode = 0o755
                tar.addfile(info)
    log(f"Linux {arch}: {archive.relative_to(ROOT)} {human(archive.stat().st_size)}")
    return archive


def build_macos() -> Path:
    folder = OUT / "macos"
    if folder.exists():
        shutil.rmtree(folder)
    archive = folder / f"{APP}-{VERSION}-macos.zip"
    export(GAME, "macOS", archive, "export_macos")
    final = OUT / archive.name
    shutil.copy2(archive, final)
    log(f"macOS: {final.relative_to(ROOT)} {human(final.stat().st_size)}")
    return final


# ------------------------------------------------------------------ mobile staging copy

def mirror(src: Path, dst: Path, exclude_dirs: list[str], exclude_files: list[str], only_new: bool = False) -> None:
    """Copy src to dst. Windows: robocopy (fast, incremental); elsewhere: a small Python mirror."""
    dst.mkdir(parents=True, exist_ok=True)
    if is_windows():
        cmd = ["robocopy", str(src), str(dst), "/E" if only_new else "/MIR", "/NFL", "/NDL", "/NJH", "/NJS", "/NP", "/R:2", "/W:1", "/MT:16"]
        if only_new:
            cmd += ["/XC", "/XN", "/XO"]
        if exclude_dirs:
            cmd += ["/XD", *exclude_dirs]
        if exclude_files:
            cmd += ["/XF", *exclude_files]
        rc = subprocess.run(cmd).returncode
        if rc >= 8:
            raise SystemExit(f"[ports] robocopy failed ({rc}): {src} -> {dst}")
        return
    from fnmatch import fnmatch
    for path in src.rglob("*"):
        rel = path.relative_to(src)
        if any(part in exclude_dirs for part in rel.parts[:-1] if True) or (path.is_dir() and path.name in exclude_dirs):
            continue
        if path.is_file() and any(fnmatch(path.name, p) for p in exclude_files):
            continue
        target = dst / rel
        if path.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        elif not target.exists() or (not only_new and (target.stat().st_mtime < path.stat().st_mtime or target.stat().st_size != path.stat().st_size)):
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)


def mobile_import_text(source_rel: str, text: str) -> str:
    if not source_rel.startswith(MOBILE_BASIS_FOLDERS) or 'importer="texture"' not in text:
        return text
    new = text
    for key, value in MOBILE_PARAMS.items():
        pattern = re.compile(rf"^{re.escape(key)}=.*$", re.M)
        new = pattern.sub(f"{key}={value}", new) if pattern.search(new) else new.replace("[params]\n", f"[params]\n\n{key}={value}\n", 1)
    return new


IMPORTED_BASE = re.compile(r'res://\.godot/imported/([^"/]+?-[0-9a-f]{32})\.')


def import_params(text: str) -> str:
    return text.split("[params]", 1)[1].strip() if "[params]" in text else ""


def staged_import_is_basis(import_text: str) -> bool:
    """True when every imported file of a staged texture is a Basis Universal .ctex."""
    folder = STAGE_GAME / ".godot" / "imported"
    bases = set(IMPORTED_BASE.findall(import_text))
    for base in bases:
        files = [f for f in (folder / (base + ext) for ext in (".ctex", ".s3tc.ctex", ".bptc.ctex", ".etc2.ctex", ".astc.ctex")) if f.exists()]
        if not files or not (folder / f"{base}.md5").exists():
            return False
        for ctex in files:
            info = ctex_info(ctex)
            if info is None or info[2] != 3:
                return False
    return bool(bases)


def forget_staged_import(import_text: str) -> None:
    """Make Godot import a staged resource again. Godot trusts its file cache (modification times) and the stored
    md5s; it never notices changed [params] in a .import file. A missing imported file is what makes it look again
    (project setting editor/import/reimport_missing_imported_files, on by default), and without the .md5 it imports."""
    folder = STAGE_GAME / ".godot" / "imported"
    for base in set(IMPORTED_BASE.findall(import_text)):
        for ext in (".md5", ".ctex", ".s3tc.ctex", ".bptc.ctex", ".etc2.ctex", ".astc.ctex"):
            (folder / (base + ext)).unlink(missing_ok=True)


def stage_mobile(skip_import: bool) -> None:
    """Refresh build/ports/_stage/src (project copy with the mobile texture set) and import it."""
    log("mobile staging copy: " + str(STAGE_GAME.relative_to(ROOT)))
    STAGE.mkdir(parents=True, exist_ok=True)
    mirror(SRC / "LastBell.Core", STAGE / "LastBell.Core", ["bin", "obj"], [])
    shutil.copy2(SRC / "LastBell.sln", STAGE / "LastBell.sln")
    # The game: everything but the editor cache, build outputs, the stage-only Android build template and the
    # .import files (written below, with the mobile import policy for the painted textures).
    mirror(GAME, STAGE_GAME, [".godot", "bin", "obj", "android"], ["*.import"])
    # Imported resources: only files the copy does not have yet (its own re-imports are kept).
    if (GAME / ".godot" / "imported").exists():
        mirror(GAME / ".godot" / "imported", STAGE_GAME / ".godot" / "imported", [], [], only_new=True)
    for name in ("uid_cache.bin", "global_script_class_cache.cfg"):
        if (GAME / ".godot" / name).exists():
            shutil.copy2(GAME / ".godot" / name, STAGE_GAME / ".godot" / name)
    manifest_path = STAGE.parent / "import_manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        manifest = {}
    if manifest.get("_policy") != MOBILE_POLICY:
        manifest = {"_policy": MOBILE_POLICY}
    wanted: set[str] = set()
    written = basis = queued = 0
    for imp in GAME.rglob("*.import"):
        rel = imp.relative_to(GAME).as_posix()
        if rel.startswith((".godot/", "android/")) or "/bin/" in rel or "/obj/" in rel:
            continue
        wanted.add(rel)
        text = imp.read_text(encoding="utf-8")
        mobile = mobile_import_text(rel[: -len(".import")], text)
        in_set = mobile != text
        if in_set:
            basis += 1
        digest = hashlib.sha1(text.encode("utf-8")).hexdigest()
        target = STAGE_GAME / rel
        if manifest.get(rel) == digest and target.exists():
            # Unchanged since the last staging: keep the copy's own (re-imported) .import file. A texture of the mobile
            # set whose imported file is still the desktop one (seeded copy, interrupted import) is queued again.
            if in_set and not staged_import_is_basis(mobile):
                forget_staged_import(mobile)
                queued += 1
            continue
        old = target.read_text(encoding="utf-8") if target.exists() else None
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(mobile, encoding="utf-8", newline="\n")
        manifest[rel] = digest
        written += 1
        # The imported files seeded from the desktop project fit every .import that is used as it is. They do not fit
        # the mobile texture set, and a staged resource whose import parameters changed must be imported again too.
        if (in_set and not staged_import_is_basis(mobile)) or (old is not None and import_params(old) != import_params(mobile)):
            forget_staged_import(mobile)
            queued += 1
    for rel in [k for k in manifest if k != "_policy" and k not in wanted]:
        (STAGE_GAME / rel).unlink(missing_ok=True)
        del manifest[rel]
    manifest_path.write_text(json.dumps(manifest, indent=0, sort_keys=True), encoding="utf-8")
    log(f"mobile staging: {len(wanted)} .import files, {basis} in the mobile texture set (Basis Universal), {written} (re)written, "
        f"{queued} queued for a new import")
    build_csharp(STAGE_GAME)
    if not skip_import:
        t0 = time.time()
        godot(STAGE_GAME, ["--import"], "import_stage")
        log(f"mobile staging imported in {time.time() - t0:.0f} s")


# ------------------------------------------------------------------ Android

KEYSTORE_JSON = ANDROID_TOOLS / "keystore.json"


def keytool() -> Path:
    home = java_home()
    if home is None:
        raise SystemExit("JDK 17 not found (JAVA_HOME)")
    return home / "bin" / ("keytool.exe" if is_windows() else "keytool")


def make_keystores() -> dict:
    """Debug + release keystores in .tools/android/ (git-ignored). Never overwrites an existing release keystore."""
    folder = ANDROID_TOOLS
    folder.mkdir(parents=True, exist_ok=True)
    if KEYSTORE_JSON.exists():
        info = json.loads(KEYSTORE_JSON.read_text(encoding="utf-8"))
    else:
        import secrets
        info = {
            "note": "Android signing for Posledny zvonec. KEEP THIS FILE AND THE RELEASE KEYSTORE SAFE AND OUT OF GIT: an app "
                    "on Google Play can only be updated with the same key (or via Play App Signing upload-key reset).",
            "release": {"path": str(folder / "lastbell-release.keystore"), "alias": "lastbell", "password": secrets.token_urlsafe(18)},
            "debug": {"path": str(folder / "lastbell-debug.keystore"), "alias": "androiddebugkey", "password": "android"},
        }
    dname = "CN=Posledny zvonec, OU=LastBell, O=LastBell, C=SK"
    for kind in ("debug", "release"):
        ks = info[kind]
        if Path(ks["path"]).exists():
            continue
        # The password goes through the environment, so it is neither in the printed command line nor in a process list.
        run([keytool(), "-genkeypair", "-v", "-keystore", ks["path"], "-alias", ks["alias"], "-keyalg", "RSA", "-keysize", "2048",
             "-validity", "10000", "-storepass:env", "LASTBELL_KEYSTORE_PASSWORD", "-keypass:env", "LASTBELL_KEYSTORE_PASSWORD",
             "-dname", dname], LOGS / f"keytool_{kind}.log", env={"LASTBELL_KEYSTORE_PASSWORD": ks["password"]})
        log(f"created the {kind} keystore {ks['path']}")
    KEYSTORE_JSON.write_text(json.dumps(info, indent=2), encoding="utf-8")
    return info


def godot_string(value: object) -> str:
    return '"' + str(value).replace("\\", "/").replace('"', '\\"') + '"'


def android_godot_config(info: dict) -> dict:
    """The Godot editor configuration of the Android exports (see the module docstring): returns the environment that
    selects it. Windows hosts only; elsewhere Godot's own editor settings must name the JDK and the SDK."""
    jdk, sdk = java_home(), android_sdk()
    if not is_windows() or jdk is None or sdk is None:
        return {}
    config = GODOT_APPDATA / "Godot"
    config.mkdir(parents=True, exist_ok=True)
    link = config / "export_templates" / GODOT_VERSION
    if not (link / "version.txt").exists():
        link.parent.mkdir(parents=True, exist_ok=True)
        rc = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(templates_dir())], stdout=subprocess.DEVNULL).returncode
        if rc != 0 or not (link / "version.txt").exists():
            raise SystemExit(f"[ports] could not link the export templates into {link}")
    wanted = {
        "export/android/java_sdk_path": godot_string(jdk),
        "export/android/android_sdk_path": godot_string(sdk),
        "export/android/debug_keystore": godot_string(info["debug"]["path"]),
        "export/android/debug_keystore_user": godot_string(info["debug"]["alias"]),
        "export/android/debug_keystore_pass": godot_string(info["debug"]["password"]),
    }
    major_minor = ".".join(GODOT_VERSION.split(".")[:2])
    settings = config / f"editor_settings-{major_minor}.tres"
    lines = settings.read_text(encoding="utf-8").splitlines() if settings.exists() else ['[gd_resource type="EditorSettings" format=3]', "", "[resource]"]
    lines = [l for l in lines if l.split(" = ", 1)[0] not in wanted]
    lines += [f"{k} = {v}" for k, v in wanted.items()]
    settings.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return {"APPDATA": str(GODOT_APPDATA)}


def android_env() -> dict:
    info = make_keystores()
    rel, dbg = info["release"], info["debug"]
    env = {
        "GODOT_ANDROID_KEYSTORE_RELEASE_PATH": rel["path"], "GODOT_ANDROID_KEYSTORE_RELEASE_USER": rel["alias"],
        "GODOT_ANDROID_KEYSTORE_RELEASE_PASSWORD": rel["password"],
        "GODOT_ANDROID_KEYSTORE_DEBUG_PATH": dbg["path"], "GODOT_ANDROID_KEYSTORE_DEBUG_USER": dbg["alias"],
        "GODOT_ANDROID_KEYSTORE_DEBUG_PASSWORD": dbg["password"],
        "GRADLE_USER_HOME": str(TOOLS / "gradle"),
        "ANDROID_USER_HOME": str(ANDROID_TOOLS / "home"),  # Gradle plugin state, not the user's ~/.android
        # The Godot editor polls "adb devices" while it runs and stops the adb server when it exits: on a port of its
        # own, so neither the user's adb server (5037) nor the one of tools/android_qa.py (5039) is ever touched.
        "ANDROID_ADB_SERVER_PORT": "5041",
    }
    (ANDROID_TOOLS / "home").mkdir(parents=True, exist_ok=True)
    # No Gradle daemon: it would stay alive for three hours, and Godot's console wrapper waits for every child process
    # (seen 2026-10-08: the AAB was written, the script waited for the daemon).
    (TOOLS / "gradle").mkdir(parents=True, exist_ok=True)
    (TOOLS / "gradle" / "gradle.properties").write_text("org.gradle.daemon=false\n", encoding="utf-8")
    jh, sdk = java_home(), android_sdk()
    if jh:
        env["JAVA_HOME"] = str(jh)
    if sdk:
        env["ANDROID_HOME"] = env["ANDROID_SDK_ROOT"] = str(sdk)
    env.update(android_godot_config(info))
    return env


def build_android(kind: str, skip_import: bool, staged: list[bool]) -> Path:
    if not staged[0]:
        stage_mobile(skip_import)
        staged[0] = True
    build_csharp(STAGE_GAME)  # also with --keep-stage: the exported assemblies come from this build
    env = android_env()
    folder = OUT / ("android_qa" if kind == "qa" else "android")
    folder.mkdir(parents=True, exist_ok=True)
    if kind == "apk":
        target = folder / f"{APP}-{VERSION}.apk"
        export(STAGE_GAME, "Android", target, "export_android_apk", env=env)
    elif kind == "aab":
        # The Gradle build needs Godot's Android build template in <project>/android/build. The option that installs it
        # only works together with an export (alone it starts the editor and never returns).
        extra = [] if (STAGE_GAME / "android" / "build" / "build.gradle").exists() else ["--install-android-build-template"]
        target = folder / f"{APP}-{VERSION}.aab"
        export(STAGE_GAME, "Android AAB", target, "export_android_aab", env=env, extra=extra)
    else:
        target = folder / "LastBell-qa-x86_64.apk"
        export(STAGE_GAME, "Android (QA x86_64)", target, "export_android_qa", debug=True, env=env)
    final = OUT / target.name if kind != "qa" else target
    if final != target:
        shutil.copy2(target, final)
    log(f"Android {kind}: {final.relative_to(ROOT)} {human(final.stat().st_size)}")
    return final


# ------------------------------------------------------------------ iOS

def build_ios(skip_import: bool, staged: list[bool]) -> Path | None:
    if not is_macos():
        log("iOS: skipped. Godot exports C# for iOS only on macOS (NativeAOT + xcodebuild). Run "
            "'python3 tools/build_ports.py ios' on a Mac with Xcode (docs/PORTS.md, iOS).")
        return None
    if not staged[0]:
        stage_mobile(skip_import)
        staged[0] = True
    folder = OUT / "ios" / "xcode"
    if folder.exists():
        shutil.rmtree(folder)
    target = folder / "LastBell.xcodeproj"
    export(STAGE_GAME, "iOS", target, "export_ios")
    archive = OUT / f"{APP}-{VERSION}-ios-xcode.zip"
    shutil.make_archive(str(archive.with_suffix("")), "zip", folder)
    log(f"iOS: {archive.relative_to(ROOT)} {human(archive.stat().st_size)}")
    return archive


# ------------------------------------------------------------------ verification

def macho_archs(data: bytes) -> list[str]:
    names = {0x01000007: "x86_64", 0x0100000C: "arm64", 7: "i386", 12: "arm"}
    magic = struct.unpack(">I", data[:4])[0]
    if magic in (0xCAFEBABE, 0xCAFEBABF):
        n = struct.unpack(">I", data[4:8])[0]
        size = 20 if magic == 0xCAFEBABE else 32
        return [names.get(struct.unpack(">i", data[8 + i * size: 12 + i * size])[0], "?") for i in range(n)]
    if magic in (0xCFFAEDFE, 0xCEFAEDFE):
        return [names.get(struct.unpack("<i", data[4:8])[0], "?")]
    return []


def verify_macos(path: Path) -> list[str]:
    notes, errors = [], []
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        apps = sorted({n.split(".app/")[0] + ".app" for n in names if ".app/" in n})
        if len(apps) != 1:
            errors.append(f"expected one .app, found {apps}")
            return errors
        app = apps[0]
        plist = plistlib.loads(z.read(f"{app}/Contents/Info.plist"))
        exe = plist.get("CFBundleExecutable")
        notes.append(f"{app}: CFBundleIdentifier={plist.get('CFBundleIdentifier')} version={plist.get('CFBundleShortVersionString')} "
                     f"build={plist.get('CFBundleVersion')} min macOS={plist.get('LSMinimumSystemVersion')} icon={plist.get('CFBundleIconFile')}")
        binary = z.read(f"{app}/Contents/MacOS/{exe}")
        archs = macho_archs(binary)
        notes.append(f"main executable {exe}: {human(len(binary))}, architectures {archs}")
        if set(archs) != {"x86_64", "arm64"}:
            errors.append(f"main executable is not universal: {archs}")
        info = z.getinfo(f"{app}/Contents/MacOS/{exe}")
        mode = (info.external_attr >> 16) & 0o777
        notes.append(f"unix mode of the executable in the zip: {oct(mode)}")
        if not mode & 0o100:
            errors.append("the executable has no exec bit in the zip")
        if not any(n.startswith(f"{app}/Contents/_CodeSignature/") for n in names):
            errors.append("no _CodeSignature (not even ad-hoc)")
        else:
            notes.append("bundle has a code signature (_CodeSignature/CodeResources)")
        icns = [n for n in names if n.endswith(".icns")]
        notes.append(f"icons: {icns}")
        pck = [n for n in names if n.endswith(".pck")]
        notes.append(f"pck: {[(n, human(z.getinfo(n).file_size)) for n in pck]}")
        for arch in ("arm64", "x86_64"):
            dlls = [n for n in names if f"_{arch}/" in n and n.endswith(("LastBell.dll", "LastBell.Core.dll"))]
            native = [n for n in names if f"_{arch}/" in n and n.endswith(("libhostfxr.dylib", "libcoreclr.dylib"))]
            notes.append(f"{arch}: game assemblies {len(dlls)} {dlls[:2]}, .NET runtime dylibs {len(native)}")
            if len(dlls) < 2 or len(native) < 2:
                errors.append(f"C# assemblies / .NET runtime for osx-{arch} missing")
            for n in native[:1]:
                got = macho_archs(z.read(n))
                notes.append(f"  {Path(n).name}: {got}")
    for n in notes:
        log("macOS verify: " + n)
    return errors


def verify_linux(archive: Path, arch: str) -> list[str]:
    errors = []
    with tarfile.open(archive) as tar:
        members = {m.name: m for m in tar.getmembers()}
        binary = members.get(f"{APP}/LastBell.{arch}")
        if binary is None:
            return [f"{archive.name}: no {APP}/LastBell.{arch}"]
        head = tar.extractfile(binary).read(20)
        machine = struct.unpack("<H", head[18:20])[0]
        want = {"x86_64": 62, "arm64": 183}[arch]
        if head[:4] != b"\x7fELF" or machine != want:
            errors.append(f"LastBell.{arch} is not an ELF for {arch} (e_machine {machine})")
        if not binary.mode & 0o100:
            errors.append("binary without exec bit")
        dlls = [n for n in members if n.endswith(("/LastBell.dll", "/LastBell.Core.dll"))]
        runtime = [n for n in members if n.endswith("libcoreclr.so")]
        log(f"Linux {arch} verify: ELF machine {machine}, mode {oct(binary.mode)}, game assemblies {len(dlls)}, libcoreclr {runtime}")
        if len(dlls) < 2 or not runtime:
            errors.append("C# assemblies or the .NET runtime missing")
    return errors


def aapt() -> Path | None:
    sdk = android_sdk()
    if sdk is None:
        return None
    tools = sorted((sdk / "build-tools").glob("*"), key=lambda p: [int(x) if x.isdigit() else 0 for x in p.name.split(".")])
    for t in reversed(tools):
        exe = t / ("aapt2.exe" if is_windows() else "aapt2")
        if exe.exists():
            return exe
    return None


def android_sdk() -> Path | None:
    """The Android SDK: the one in .tools first, then ANDROID_HOME / ANDROID_SDK_ROOT and the usual places."""
    for cand in [str(ANDROID_TOOLS / "sdk"), os.environ.get("ANDROID_HOME"), os.environ.get("ANDROID_SDK_ROOT"),
                 str(Path(os.environ.get("LOCALAPPDATA", "")) / "Android" / "Sdk"), str(Path.home() / "Library/Android/sdk"),
                 str(Path.home() / "Android" / "Sdk")]:
        if cand and Path(cand, "platform-tools").exists():
            return Path(cand)
    return None


def verify_apk(path: Path) -> list[str]:
    errors = []
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        libs = sorted({n.split("/")[1] for n in names if n.startswith("lib/")})
        pck = [n for n in names if n.endswith(".pck")]
        assets = sum(z.getinfo(n).file_size for n in names if n.startswith("assets/"))
        dotnet = [n for n in names if "LastBell.dll" in n or "LastBell.Core.dll" in n]
        log(f"APK verify {path.name}: ABIs {libs}, pck {pck}, assets {human(assets)} uncompressed, C# {dotnet[:3]}")
        if not dotnet:
            errors.append("no LastBell.dll in the APK")
    tool = aapt()
    if tool:
        out = subprocess.run([str(tool), "dump", "badging", str(path)], capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
        for line in out.splitlines():
            if line.startswith(("package:", "sdkVersion", "targetSdkVersion", "launchable-activity", "native-code", "application-label:", "uses-permission")):
                log(f"  aapt2: {line.strip()}")
        m = re.search(r"launchable-activity: name='([^']+)'", out)
        if m:
            log(f"  activity {m.group(1)}")
        xml = subprocess.run([str(tool), "dump", "xmltree", str(path), "--file", "AndroidManifest.xml"], capture_output=True, text=True,
                             encoding="utf-8", errors="replace").stdout
        orient = re.findall(r"screenOrientation.*?=(\S+)", xml)
        log(f"  manifest screenOrientation {orient[:2]}")
    sdk = android_sdk()
    if sdk:
        signer = sorted((sdk / "build-tools").glob("*/lib/apksigner.jar"))
        if signer and java_home():
            java = java_home() / "bin" / ("java.exe" if is_windows() else "java")
            res = subprocess.run([str(java), "-jar", str(signer[-1]), "verify", "--print-certs", str(path)], capture_output=True, text=True)
            first = [l for l in res.stdout.splitlines() if "certificate DN" in l][:1]
            log(f"  apksigner verify: rc={res.returncode} {first}")
            if res.returncode != 0:
                errors.append("apksigner verify failed: " + res.stderr[:300])
    return errors


def cmd_verify() -> int:
    errors: list[str] = []
    for arch in ("x86_64", "arm64"):
        a = OUT / f"{APP}-{VERSION}-linux-{arch}.tar.gz"
        if a.exists():
            errors += verify_linux(a, arch)
    m = OUT / f"{APP}-{VERSION}-macos.zip"
    if m.exists():
        errors += verify_macos(m)
    for apk in [OUT / f"{APP}-{VERSION}.apk", OUT / "android_qa" / "LastBell-qa-x86_64.apk"]:
        if apk.exists():
            errors += verify_apk(apk)
    aab = OUT / f"{APP}-{VERSION}.aab"
    if aab.exists():
        with zipfile.ZipFile(aab) as z:
            mods = sorted({n.split("/")[0] for n in z.namelist() if "/" in n})
            log(f"AAB verify {aab.name}: modules/folders {mods}, {human(aab.stat().st_size)}")
    write_artifact_list()
    for e in errors:
        print("ERROR", e)
    return 1 if errors else 0


def write_artifact_list() -> None:
    rows = []
    for p in sorted(OUT.glob(f"{APP}-*")):
        if p.is_file():
            h = hashlib.sha256()
            with p.open("rb") as fh:
                for chunk in iter(lambda: fh.read(1 << 20), b""):
                    h.update(chunk)
            rows.append(f"{p.name}\t{p.stat().st_size}\t{human(p.stat().st_size)}\tsha256 {h.hexdigest()}")
    (OUT / "ARTIFACTS.txt").write_text("\n".join(rows) + "\n", encoding="utf-8")
    for r in rows:
        log("artifact " + r)


# ------------------------------------------------------------------ texture memory estimate

CTEX_FORMATS = {  # Godot Image::Format -> bytes per pixel (x8 for block formats: bits per pixel)
    4: 3, 5: 4,  # RGB8, RGBA8
    17: 0.5, 18: 1, 19: 1,  # DXT1, DXT3, DXT5
    22: 1, 23: 1,  # BPTC
    29: 0.5, 30: 1, 31: 1,  # ETC2_RGB8, ETC2_RGBA8, ETC2_RGB8A1
    35: 1,  # ASTC_4x4
}


def ctex_info(path: Path) -> tuple[int, int, int, int] | None:
    """(width, height, data_format, image_format) of a Godot 4 .ctex."""
    with path.open("rb") as f:
        head = f.read(56)
    if head[:4] != b"GST2":
        return None
    _ver, w, h, _flags, _limit = struct.unpack("<5I", head[4:24])
    data_format, _w2, _h2, _mips, image_format = struct.unpack("<IHHII", head[36:52])
    return w, h, data_format, image_format


def cmd_texture_report() -> int:
    """Decoded GPU memory of the textures under assets/ for the desktop import and the mobile staging import."""
    def report(project: Path, label: str, basis_bpp: float) -> dict[str, float]:
        totals: dict[str, float] = {}
        for imp in (project / "assets").rglob("*.import"):
            text = imp.read_text(encoding="utf-8", errors="replace")
            if 'importer="texture"' not in text:
                continue
            m = re.search(r'^path(?:\.[a-z0-9]+)?="res://(\.godot/imported/[^"]+)"', text, re.M)
            if not m:
                continue
            ctex = project / m.group(1)
            info = ctex_info(ctex) if ctex.exists() else None
            if info is None:
                continue
            w, h, data_format, image_format = info
            if data_format == 3:  # Basis Universal: transcoded on load to ASTC 4x4 / ETC2 / BC7 (1 B/px)
                bpp = basis_bpp
            elif data_format in (1, 2):  # PNG / WebP payload: decoded to RGB8 / RGBA8
                bpp = CTEX_FORMATS.get(image_format, 4)
            else:
                bpp = CTEX_FORMATS.get(image_format, 4)
            folder = "/".join(imp.relative_to(project).parts[:2])
            totals[folder] = totals.get(folder, 0) + w * h * bpp
        print(f"{label}:")
        for k, v in sorted(totals.items(), key=lambda kv: -kv[1]):
            print(f"  {v / 1e6:8.1f} MB  {k}")
        print(f"  {sum(totals.values()) / 1e6:8.1f} MB  all textures under assets/ (if all were loaded at once)")
        return totals
    report(GAME, "desktop import (src/game)", 4)
    if STAGE_GAME.exists():
        report(STAGE_GAME, "mobile import (build/ports/_stage), Basis transcoded to ASTC 4x4 / ETC2 (1 byte per pixel)", 1)
    return 0


# ------------------------------------------------------------------ main

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("targets", nargs="*", help="linux linux-arm64 macos android android-aab android-qa ios | stage keystores verify texture-report")
    ap.add_argument("--skip-import", action="store_true")
    ap.add_argument("--no-lock", action="store_true")
    ap.add_argument("--keep-stage", action="store_true")
    a = ap.parse_args()
    Lock.enabled = not a.no_lock
    OUT.mkdir(parents=True, exist_ok=True)
    targets = a.targets or (["linux", "linux-arm64", "macos", "android", "android-aab"] + (["ios"] if is_macos() else []))
    if targets == ["verify"]:
        return cmd_verify()
    if targets == ["texture-report"]:
        return cmd_texture_report()
    if targets == ["keystores"]:
        info = make_keystores()
        log(f"keystores: {info['release']['path']} (alias {info['release']['alias']}), password in {KEYSTORE_JSON}")
        return 0
    known = {"linux", "linux-arm64", "macos", "android", "android-aab", "android-qa", "ios", "stage"}
    unknown = [t for t in targets if t not in known]
    if unknown:
        ap.error(f"unknown target(s): {unknown}")
    android = any(t.startswith("android") for t in targets)
    t0 = time.time()
    prechecks(android)
    desktop = [t for t in targets if t in ("linux", "linux-arm64", "macos")]
    if desktop:
        build_csharp(GAME)
        if not a.skip_import:
            godot(GAME, ["--import"], "import_desktop")
    staged = [a.keep_stage and STAGE_GAME.exists()]
    built: list[Path] = []
    for t in targets:
        if t == "linux":
            built.append(build_linux("x86_64"))
        elif t == "linux-arm64":
            built.append(build_linux("arm64"))
        elif t == "macos":
            built.append(build_macos())
        elif t == "android":
            built.append(build_android("apk", a.skip_import, staged))
        elif t == "android-aab":
            built.append(build_android("aab", a.skip_import, staged))
        elif t == "android-qa":
            built.append(build_android("qa", a.skip_import, staged))
        elif t == "ios":
            if (p := build_ios(a.skip_import, staged)) is not None:
                built.append(p)
        elif t == "stage":
            stage_mobile(a.skip_import)
            staged[0] = True
    rc = cmd_verify()
    log(f"done in {time.time() - t0:.0f} s: " + ", ".join(f"{p.name} ({human(p.stat().st_size)})" for p in built))
    return rc


if __name__ == "__main__":
    sys.exit(main())
