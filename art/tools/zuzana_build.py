"""Free local build stages of the ZUZANA set (called through zuzana_set.py; see its docstring).

build         standing still set (idle | blink | talk_a | talk_b | gesture) via npc_batch.build_stills, review
idle          video idle loop (Hailuo standard, start = end) -> idle_hailuo/
hop           hopscotch 'playing' loop (Hailuo Pro, start = end) -> play_hop/; keeps the video's vertical motion
              (fixed feet line of the standing first frame), scale from that frame (350 px standing)
crouch_build  crouching chalk-drawing stills (idle | blink | talk_a | talk_b | gesture) at the standing scale
draw          crouched drawing loop (Hailuo standard) -> draw_chalk/
export        WebP sheets + JSON + actor.json into src/game/assets/actors/ZUZANA/
preview       game-scale line-up and an S37 mock (local review images, never shipped)
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import frames as fr
import npc_batch as nb

CID = "ZUZANA"
D = nb.CHAR_ROOT / CID
GAME = nb.GAME_ACTORS / CID
REVIEW = D / "review"


def brief() -> dict:
    return nb.brief_of(CID)


def stand_geometry() -> dict:
    """Source-px geometry of the standing base (figure box, scale to the shipped height, head box)."""
    base = nb._CHROMA_KEY(fr.load_rgb(nb.base_path(CID)))
    x0, y0, x1, y1 = fr.alpha_bbox(base)
    target = int(brief()["height_px"])
    return {"box": [x0, y0, x1, y1], "height": y1 - y0, "scale": target / (y1 - y0), "target": target,
            "hair_width": hair_width(fr.load_rgb(nb.base_path(CID)), 0.3)}


def hair_width(rgb: np.ndarray, top_frac: float = 0.45) -> float:
    """Width of the light-brown hair bob (largest hair-coloured component in the top part of the figure): a head
    size measure that holds when the body pose changes. A row-width scan merged the head with the collar and the
    shoulders in the crouch (no narrowing at the neck) and gave 2.07 instead of ~1.49."""
    key = nb._CHROMA_KEY(rgb)
    x0, y0, x1, y1 = fr.alpha_bbox(key)
    c = rgb.astype(np.int16)
    r, g, b = c[..., 0], c[..., 1], c[..., 2]
    lum = (r + g + b) / 3
    mask = (key[..., 3] > 200) & (r - b > 45) & (lum < 175) & (lum > 60) & (r > g)
    mask[y0 + int((y1 - y0) * top_frac):] = False
    labels, sizes = fr.label_components(mask)
    xs = np.nonzero(labels == int(np.argmax(sizes)) + 1)[1]
    return float(xs.max() - xs.min())


# ----------------------------------------------------------------------------- standing stills

def build() -> None:
    meta = nb.build_stills(CID)
    print(json.dumps({k: meta[k] for k in ("cell", "pivot", "scale")}), json.dumps(meta["face_landmarks"]["bands_frac"]))
    print(json.dumps({k: (v.get("colour_fit"), v.get("mean_abs_diff_outside_band_after_fit"))
                      for k, v in meta["edit_reports"].items()}))
    nb.review(CID)


# ----------------------------------------------------------------------------- video loops

def video_frames(video: Path) -> tuple[list[Path], dict]:
    raw = D / "_frames" / video.stem
    info = fr.video_info(video)
    return fr.extract_frames(video, raw), info


def canvas_meta(name: str) -> dict:
    return json.loads((D / name).with_suffix(".json").read_text(encoding="utf-8"))


def build_video_loop(video_name: str, out_name: str, canvas_name: str, target_h: float, frames_out: int,
                     fixed_feet: bool, frame_range: tuple[int, int] | None = None) -> dict:
    """Whole start=end clip as a loop, mapped to the shipped scale through the canvas transform."""
    video = D / video_name
    paths, info = video_frames(video)
    fps = info.get("fps", 24.0)
    end = nb.closure_frame(paths) if frame_range is None else frame_range[1]
    start = 0 if frame_range is None else frame_range[0]
    first = nb._CHROMA_KEY(fr.load_rgb(paths[start]))
    fb = fr.alpha_bbox(first)
    ref_h = fb[3] - fb[1]
    picks = [start + round(i * (end - start) / frames_out) for i in range(frames_out)] + [end]
    tmp = D / "_frames" / (video.stem + "_picks")
    tmp.mkdir(parents=True, exist_ok=True)
    for old in tmp.glob("f_*.png"):
        old.unlink()
    for j, src in enumerate(picks):
        shutil.copy(paths[src], tmp / f"f_{j:04d}.png")
    meta = fr.build_loop(sorted(tmp.glob("f_*.png")), D / out_name, fps, frames_out, (1, 2), 0, 0, False,
                         target_h, None, None, out_name.split("_")[0], choke=1, frame_range=(0, frames_out),
                         ref_height=ref_h, playback_fps=frames_out / ((end - start) / fps),
                         fixed_baseline=float(fb[3]) if fixed_feet else None)
    meta.update(source_frames=picks[:-1], cycle_frames=end - start, cycle_seconds=round((end - start) / fps, 3),
                video=video_name)
    (D / out_name / f"{meta['name']}_sheet.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return meta


def idle(video: str = "video_idle_loop.mp4") -> None:
    meta = nb.build_idle(CID, video_name=video, out_name="idle_hailuo")
    print(json.dumps({k: meta.get(k) for k in ("frames", "cell", "pivot", "cycle_frames", "playback_fps",
                                               "height_px_range")}))
    nb.idle_strip(CID)


def hop(video: str = "video_hop_loop_r2.mp4", frames_out: int = 70, rng: tuple[int, int] | None = None) -> None:
    meta = build_video_loop(video, "play_hop", "video_in_hop.png", brief()["height_px"], frames_out, True, rng)
    # the folder name gives 'play' as the sheet name
    print(json.dumps({k: meta.get(k) for k in ("frames", "cell", "pivot", "cycle_frames", "cycle_seconds",
                                               "playback_fps", "height_px_range", "baseline_from_feet")}))
    strip(D / "play_hop" / "play_sheet.png", D / "play_hop" / "play_sheet.json", REVIEW / "play_strip.jpg")


def strip(sheet_png: Path, sheet_json: Path, out: Path, step: int = 2) -> None:
    meta = json.loads(sheet_json.read_text(encoding="utf-8"))
    sheet = Image.open(sheet_png).convert("RGBA")
    cw, ch = meta["cell"]
    n = meta["frames"]
    cells = [sheet.crop((i * cw, 0, (i + 1) * cw, ch)) for i in range(0, n, step)]
    out.parent.mkdir(exist_ok=True)
    fr.contact_sheet(cells, out, cell_h=min(ch, 420), labels=[str(i) for i in range(0, n, step)])


# ----------------------------------------------------------------------------- crouch (drawing) set

def crouch_prep(src: str = "pose_crouch_pro.png") -> dict:
    """Crouch base on the standing base's canvas size; measures its scale against the standing head."""
    rgb = fr.load_rgb(D / src)
    stand = stand_geometry()
    key = nb._CHROMA_KEY(rgb)
    hw = hair_width(rgb, 0.45)
    k = hw / stand["hair_width"]
    Image.fromarray(rgb).save(D / "crouch_base.png")
    meta = {"source": src, "hair_width_src": hw, "stand_hair_width_src": stand["hair_width"],
            "head_scale_vs_standing": round(k, 4), "crouch_height_src": int(fr.alpha_bbox(key)[3] - fr.alpha_bbox(key)[1])}
    meta["shipped_height_px"] = round(meta["crouch_height_src"] * stand["scale"] / k, 1)
    (D / "crouch_build.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(json.dumps(meta))
    return meta


def crouch_landmarks(base_rgb: np.ndarray, blink_rgb: np.ndarray, talk_rgb: np.ndarray, head_px: float) -> dict:
    base_key = nb._CHROMA_KEY(base_rgb)
    x0, y0, x1, y1 = fr.alpha_bbox(base_key)
    h = y1 - y0
    head_bottom = y0 + int(head_px * 1.3)
    skull = base_key[y0:y0 + int(head_px * 0.6), :, 3] > 128
    hc = np.flatnonzero(skull.any(axis=0))
    pad = int(head_px * 0.15)
    cols = (max(0, int(hc.min()) - pad), int(hc.max()) + pad)
    blink = nb.changed_rows(base_rgb, base_key, blink_rgb, y0, head_bottom, cols)
    blink[: int(head_px * 0.3)] = 0
    blink[int(head_px * 0.95):] = 0
    eye = nb.centroid_of_peak(blink, y0)
    talk = nb.changed_rows(base_rgb, base_key, talk_rgb, y0, head_bottom, cols)
    if eye is not None:
        talk[: max(0, int(eye - y0 + head_px * 0.15))] = 0
    mouth = nb.centroid_of_peak(talk, y0)
    if eye is None:
        eye = y0 + 0.6 * head_px
    if mouth is None or not (eye + 0.12 * head_px <= mouth <= eye + 0.6 * head_px):
        mouth = eye + 0.33 * head_px
    gap = mouth - eye
    bands = {"eyes": [eye - 0.6 * gap, eye + 0.4 * gap], "mouth": [eye + 0.45 * gap, mouth + 1.05 * gap]}
    frac = {k: [round((a - y0) / h, 4), round((b - y0) / h, 4)] for k, (a, b) in bands.items()}
    return {"figure_box": [x0, y0, x1, y1], "eye_y": round(eye, 1), "mouth_y": round(mouth, 1),
            "bands_px": {k: [round(a), round(b)] for k, (a, b) in bands.items()}, "bands_frac": frac}


def crouch_build(gesture: str | None = "crouch_gesture_nb2.png") -> dict:
    cm = json.loads((D / "crouch_build.json").read_text(encoding="utf-8"))
    stand = stand_geometry()
    base_rgb = fr.load_rgb(D / "crouch_base.png")
    base_key = nb._CHROMA_KEY(base_rgb)
    head_px = stand["hair_width"] * cm["head_scale_vs_standing"] * 1.05
    lm = crouch_landmarks(base_rgb, fr.load_rgb(D / "crouch_blink_nb2.png"), fr.load_rgb(D / "crouch_talk_a_nb2.png"),
                          head_px)
    layers, reports, sources = [base_key], {}, ["key:crouch_base.png"]
    for label, src, band in (("blink", "crouch_blink_nb2.png", "eyes"), ("talk_a", "crouch_talk_a_nb2.png", "mouth"),
                             ("talk_b", "crouch_talk_o_nb2.png", "mouth")):
        rgba, rep = nb.patch_face(base_rgb, fr.load_rgb(D / src), tuple(lm["bands_frac"][band]))
        layers.append(rgba)
        reports[label] = rep
        sources.append(f"patch[{band} {lm['bands_frac'][band]}]:{src}")
    names = ["idle", "blink", "talk_a", "talk_b"]
    if gesture and (D / gesture).exists():
        rgba, rep = fr.patch_pose(base_rgb, fr.load_rgb(D / gesture), (0.0, 1.0), feather=10)
        layers.append(rgba)
        reports["gesture"] = rep
        sources.append(f"patch:{gesture}")
        names.append("gesture")
    target_h = cm["shipped_height_px"]
    cells, geo = nb.build_cells(base_rgb, layers, int(round(target_h)))
    meta = {"name": "crouch", "frames": names, **geo, "height_px": target_h, "playback_fps": 8, "sources": sources,
            "face_landmarks": lm, "edit_reports": reports, "standing_scale_note":
            "same head size as the standing set (scale from the hair-bob width)"}
    gif = [(0, 1400), (1, 110), (0, 900), (2, 125), (3, 125), (2, 125), (0, 125), (3, 125), (2, 125), (0, 700)]
    if "gesture" in names:
        gif += [(4, 1200), (0, 600)]
    fr.export_cells(cells, D / "crouch_set", "crouch", meta, names, gif, names=names)
    fr.save_rgba(fr.crop_to_figure(base_key), D / "keyed" / "crouch_3q.png")
    faces = nb.face_crop_strip(cells, names, lm["bands_frac"], int(round(target_h)))
    REVIEW.mkdir(exist_ok=True)
    faces.save(REVIEW / "crouch_faces.jpg", quality=90)
    print(json.dumps({k: geo[k] for k in ("cell", "pivot", "scale")}), json.dumps(lm["bands_frac"]),
          json.dumps({k: v.get("mean_abs_diff_outside_band_after_fit", v.get("changed_px")) for k, v in reports.items()}))
    return meta


def draw(video: str = "video_draw_loop.mp4", frames_out: int = 36) -> None:
    cm = json.loads((D / "crouch_build.json").read_text(encoding="utf-8"))
    meta = build_video_loop(video, "draw_chalk", "video_in_crouch.png", cm["shipped_height_px"], frames_out, False)
    print(json.dumps({k: meta.get(k) for k in ("frames", "cell", "pivot", "cycle_frames", "cycle_seconds",
                                               "playback_fps", "height_px_range")}))
    strip(D / "draw_chalk" / "draw_sheet.png", D / "draw_chalk" / "draw_sheet.json", REVIEW / "draw_strip.jpg", 3)


# ----------------------------------------------------------------------------- export

SHEETS = {   # key: (master sheet, lossless)
    "npc": ("npc_set/npc_sheet.png", True),
    "idle": ("idle_hailuo/idle_sheet.png", False),
    "play": ("play_hop/play_sheet.png", False),
    "crouch": ("crouch_set/crouch_sheet.png", True),
    "draw": ("draw_chalk/draw_sheet.png", False),
}


def still_anims(sheet: str, gesture: bool = True) -> dict:
    out = {
        "idle_still": {"sheet": sheet, "frames": ["idle"]},
        "blink": {"sheet": sheet, "frames": ["blink"], "hold_ms": 110, "every_s": [2.5, 6.0],
                  "note": "only while the still idle is shown (the video loops blink by themselves)"},
        "talk": {"sheet": sheet, "frames": ["talk_a", "talk_b", "talk_a", "idle", "talk_b", "talk_a", "idle"],
                 "fps": 8, "loop": True},
    }
    if gesture:
        out["gesture"] = {"sheet": sheet, "frames": ["gesture"], "hold_ms": 1200, "oneshot": True,
                          "note": "PlayGesture: hold, then return to idle (pointing; no in-betweens)"}
        out["point"] = dict(out["gesture"], note="alias of gesture")
    return out


def export() -> dict:
    GAME.mkdir(parents=True, exist_ok=True)
    b = brief()
    sheets = {}
    for key, (rel, lossless) in SHEETS.items():
        src = D / rel
        meta = json.loads(src.with_suffix(".json").read_text(encoding="utf-8"))
        out = dict(meta)
        if isinstance(meta.get("frames"), list):
            out["frame_names"] = meta["frames"]
            out["frames"] = len(meta["frames"])
        for drop in ("source_frames", "sources", "face_landmarks", "edit_reports", "pingpong_source_frames",
                     "standing_scale_note"):
            out.pop(drop, None)
        out.setdefault("oneshot", False)
        out["stride_px_per_s"] = None
        out["loop"] = not lossless
        out.setdefault("pivot_is_sill_line", False)
        strip_img = Image.open(src).convert("RGBA")
        packed, cols, rows = nb.grid_pack(strip_img, tuple(out["cell"]), out["frames"])
        name = f"{key}_sheet.webp"
        out["file"], out["columns"], out["rows"] = name, cols, rows
        if lossless:
            packed.save(GAME / name, "WEBP", lossless=True, quality=100, method=6)
        else:
            packed.save(GAME / name, "WEBP", quality=92, alpha_quality=100, method=6)
        check = Image.open(GAME / name)
        assert check.size == packed.size and max(check.size) <= nb.MAX_TEX, (name, check.size)
        (GAME / f"{key}_sheet.json").write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n",
                                                encoding="utf-8", newline="\n")
        sheets[key] = {"file": name, "json": f"{key}_sheet.json", "size": list(packed.size), "cell": out["cell"],
                       "pivot": out["pivot"], "frames": out["frames"], "columns": cols, "rows": rows}
    crouch_h = json.loads((D / "crouch_build.json").read_text(encoding="utf-8"))["shipped_height_px"]
    base = {"idle": {"sheet": "idle", "loop": True}, **still_anims("npc")}
    manifest = {
        "id": CID,
        "source": f"art/characters/{CID}",
        "view": "three-quarter, facing right (mirror for facing left)",
        "era": 1962,
        "room": "S37",
        "height_px": int(b["height_px"]),
        "pivot": "feet centre, 4 px above the cell bottom (play: the standing feet line; the hops rise above it; "
                 "drawing: the lowest point of the crouch, the chalk tip just in front of her sandals)",
        "staging": "standing; variants: playing (default), full, drawing",
        "sheets": sheets,
        "animations": base,
        "variants": {
            "playing": {
                "height_px": int(b["height_px"]),
                "note": "default in the park: hopscotch hops on the spot (a 5.9 s loop with two hop rounds and a "
                        "short pause; cell 0 = the standing still idle, so talk and gesture cut in cleanly at the "
                        "loop boundary). The hopscotch squares belong to the background or a ground decal.",
                "animations": {"idle": {"sheet": "play", "loop": True}},
            },
            "full": {
                "height_px": int(b["height_px"]),
                "note": "standing: calm video idle; every 12-25 s one hopscotch round as the idle fidget",
                "animations": {"idle_fidget": {"sheet": "play", "loop": False, "every_s": [12, 25],
                                               "note": "one pass of the hopscotch loop; starts and ends on the "
                                                       "first cell of the idle loop"}},
            },
            "drawing": {
                "height_px": crouch_h,
                "note": "crouched, drawing with chalk on the ground in front of her toes (same head size as the "
                        "standing set); talk, blink and the pointing gesture are crouched too",
                "animations": {"idle": {"sheet": "draw", "loop": True}, **still_anims("crouch")},
            },
        },
        "default_variant": "playing",
        "switching": ("Video loops (idle, play, draw) start and end on the still idle pose of their set: start "
                      "talking at a loop boundary or cross-fade ~80 ms. Do not switch between the standing and the "
                      "drawing sets on screen (no stand-up transition)."),
        "notes": b.get("notes", ""),
    }
    (GAME / "actor.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8",
                                     newline="\n")
    (GAME / "README.md").write_text(README.format(h=int(b["height_px"]), ch=crouch_h), encoding="utf-8",
                                    newline="\n")
    return manifest


README = """# ZUZANA (S37, manor park of Ivanka pri Dunaji, June 1962)

A seven-year-old village girl. Likeness from a family photo supplied by the owner. Style A, three-quarter view
facing right (mirror for left), ADAM's approved sprite as the cast anchor. Masters and tools:
`art/characters/ZUZANA/`, `art/tools/zuzana_set.py` (paid), `art/tools/zuzana_build.py` (local).

Height: {h} px standing at scale 1 (adults 512 px = 1.70-1.75 m, so about 118-120 cm, 0.68 of Adam; SONA at 11
is 420 px). Crouched (drawing): {ch} px, same head size.

| sheet | cells | content |
|---|---|---|
| npc_sheet | idle, blink, talk_a, talk_b, gesture | standing stills; blink and mouth frames are transplanted eye / mouth bands, the body is pixel-identical; gesture = pointing ahead with the free arm |
| idle_sheet | 36 at 6.1 fps | calm standing video idle (breathing, blink), loop |
| play_sheet | 70 at 11.9 fps | hopscotch hops on the spot, two rounds and a pause, 5.9 s loop; keeps the vertical hop motion (fixed feet line) |
| crouch_sheet | idle, blink, talk_a, talk_b, gesture | crouched stills, chalk on the ground; gesture = pointing ahead from the crouch |
| draw_sheet | 36 at 6.1 fps | crouched, drawing small chalk strokes, loop |

Variants: `playing` (default: idle = play loop; talk and gesture standing), `full` (standing video idle, one
hopscotch round as idle_fidget every 12-25 s), `drawing` (the crouched set). Select with `variant` in
`data/blocking/S37.json`. Chalk marks and hopscotch squares are not part of the sprite.
"""


# ----------------------------------------------------------------------------- previews (local review only)

def _cell(folder: str, name: str, index: int | str = 0) -> tuple[Image.Image, list[int]]:
    meta = json.loads((D / folder / f"{name}_sheet.json").read_text(encoding="utf-8"))
    sheet = Image.open(D / folder / f"{name}_sheet.png").convert("RGBA")
    if isinstance(index, str):
        index = meta["frames"].index(index)
    cw, ch = meta["cell"]
    return sheet.crop((index * cw, 0, (index + 1) * cw, ch)), meta["pivot"]


def _place(canvas: Image.Image, cell: Image.Image, pivot: list[int], feet: tuple[int, int], scale: float,
           mirror: bool = False) -> None:
    if mirror:
        cell = cell.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        pivot = [cell.width - pivot[0], pivot[1]]
    img = cell.resize((max(1, round(cell.width * scale)), max(1, round(cell.height * scale))), Image.Resampling.LANCZOS)
    canvas.alpha_composite(img, (round(feet[0] - pivot[0] * scale), round(feet[1] - pivot[1] * scale)))


def _room_scale(y: float) -> float:
    return (y - 520) / 495          # data/blocking/S37.json: hero 512 px at y 1015


def preview() -> None:
    """S37 mock-ups at the room's perspective (Adam, Vera on her bench, Zuzana playing / drawing) + a GIF of
    the hopscotch loop in the park; and a game-scale line-up with SONA and ADAM."""
    REVIEW.mkdir(exist_ok=True)
    bg = Image.open(nb.REPO / "src" / "game" / "assets" / "bg_natural" / "S37.webp").convert("RGBA")
    vera, vera_p = Image.open(nb.GAME_ACTORS / "VERA60" / "npc_sheet.webp").convert("RGBA"), None
    vmeta = json.loads((nb.GAME_ACTORS / "VERA60" / "npc_sheet.json").read_text(encoding="utf-8"))
    vcell = vera.crop((0, 0, vmeta["cell"][0], vmeta["cell"][1]))
    adam = Image.open(nb.CHAR_ROOT / "ADAM" / "keyed" / "side_right_3q.png").convert("RGBA")
    adam_scale = 512 / adam.height
    adam_cell = adam.resize((round(adam.width * adam_scale), 512), Image.Resampling.LANCZOS)
    adam_p = [adam_cell.width // 2, 512]

    def scene(z_cell: Image.Image, z_pivot: list[int], z_feet: tuple[int, int], mirror: bool) -> Image.Image:
        frame = bg.copy()
        _place(frame, vcell, vmeta["pivot"], (600, 800), _room_scale(800))
        _place(frame, z_cell, z_pivot, z_feet, _room_scale(z_feet[1]), mirror)
        _place(frame, adam_cell, adam_p, (980, 930), _room_scale(930))
        return frame

    stand, sp = _cell("npc_set", "npc", "idle")
    hop_cell, hp = _cell("play_hop", "play", 10)
    crouch, cp = _cell("crouch_set", "crouch", "idle")
    shots = [scene(stand, sp, (1250, 900), True), scene(hop_cell, hp, (1250, 900), True),
             scene(crouch, cp, (1250, 900), True)]
    for i, shot in enumerate(shots):
        shot.convert("RGB").save(REVIEW / f"S37_mock_{['talk', 'playing', 'drawing'][i]}.jpg", quality=90)
    # GIF: the hopscotch loop in the park (crop around her), at the room's scale
    meta = json.loads((D / "play_hop" / "play_sheet.json").read_text(encoding="utf-8"))
    sheet = Image.open(D / "play_hop" / "play_sheet.png").convert("RGBA")
    cw, ch = meta["cell"]
    frames_gif = []
    for i in range(meta["frames"]):
        frame = bg.copy()
        _place(frame, sheet.crop((i * cw, 0, (i + 1) * cw, ch)), meta["pivot"], (1250, 900), _room_scale(900), True)
        _place(frame, adam_cell, adam_p, (980, 930), _room_scale(930))
        crop = frame.crop((880, 520, 1480, 980)).convert("RGB")
        crop = crop.resize((450, 345), Image.Resampling.LANCZOS)
        frames_gif.append(crop.quantize(colors=255, method=Image.Quantize.MEDIANCUT))
    screens = nb.REPO / "build" / "screens" / "zuzana"     # git-ignored (5-6 MB GIF)
    screens.mkdir(parents=True, exist_ok=True)
    frames_gif[0].save(screens / "S37_playing.gif", save_all=True, append_images=frames_gif[1:],
                       duration=round(1000 / meta["playback_fps"]), loop=0, disposal=2)
    # game-scale line-up: Zuzana (still, mid-hop, crouch), SONA (11), ADAM
    sona = Image.open(nb.GAME_ACTORS / "SONA" / "npc_sheet.webp").convert("RGBA")
    smeta = json.loads((nb.GAME_ACTORS / "SONA" / "npc_sheet.json").read_text(encoding="utf-8"))
    scell = sona.crop((0, 0, smeta["cell"][0], smeta["cell"][1]))
    items = [(stand, sp), (hop_cell, hp), (crouch, cp), (scell, smeta["pivot"]), (adam_cell, adam_p)]
    width = sum(c.width for c, _ in items) + 20 * (len(items) + 1)
    line = Image.new("RGBA", (width, 560), (120, 130, 140, 255))
    x = 20
    draw_ = ImageDraw.Draw(line)
    for c, p in items:
        _place(line, c, p, (x + p[0], 540), 1.0)
        x += c.width + 20
    for h, label in ((512, "512 Adam"), (420, "420 Sona (11)"), (350, "350 Zuzana (7)")):
        draw_.line([(0, 540 - h), (width, 540 - h)], fill=(255, 255, 255, 90), width=1)
        draw_.text((4, 540 - h - 12), label, fill=(255, 255, 255, 255))
    line.convert("RGB").save(REVIEW / "lineup_game_scale.png")
    print("review images in", REVIEW)


def run(args) -> None:
    cmd = args.cmd
    if cmd == "build":
        build()
    elif cmd == "idle":
        idle()
    elif cmd == "hop":
        hop()
    elif cmd == "crouch_prep":
        crouch_prep()
    elif cmd == "crouch_build":
        crouch_build()
    elif cmd == "draw":
        draw()
    elif cmd == "export":
        m = export()
        print({k: (v["size"], v["frames"], v["columns"], v["rows"]) for k, v in m["sheets"].items()})
    elif cmd == "preview":
        preview()
    else:
        raise SystemExit(f"unknown command {cmd}")
