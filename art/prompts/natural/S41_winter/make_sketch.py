"""Writes art/prompts/natural/S41.sketch.json: the winter S41 blocking traced from the owner's friend's photo
(imgur_TXI6i3E aligned to the game frame: game = (orig - (244, 124)) * 1.15). Flat colour blocks only."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]   # repo root
shapes = []


def rect(box, fill, note=None, **kw):
    shapes.append({"type": "rect", "box": box, "fill": fill, **({"note": note} if note else {}), **kw})


def poly(points, fill, note=None, **kw):
    shapes.append({"type": "poly", "points": points, "fill": fill, **({"note": note} if note else {}), **kw})


def line(points, color, width, note=None):
    shapes.append({"type": "line", "points": points, "color": color, "width": width, **({"note": note} if note else {})})


def ellipse(box, fill, note=None, **kw):
    shapes.append({"type": "ellipse", "box": box, "fill": fill, **({"note": note} if note else {}), **kw})


SNOW = "#f2f6fa"
SNOW_SHADE = "#c9d6e4"
SPRUCE = "#2e4a40"
SPRUCE_SNOW = "#6f8a80"

# --- sky (clear cold winter sky, lighter towards the horizon)
rect([0, 0, 1920, 110], "#7fb1e2", "deep clear winter sky")
rect([0, 110, 1920, 90], "#9cc3ea")
rect([0, 200, 1920, 140], "#bfd8ef", "pale sky near the horizon")
# distant snowy summit behind the hotel
poly([[470, 302], [530, 264], [575, 249], [622, 257], [662, 280], [705, 302]], "#e9eff6", "distant snowy summit")
poly([[575, 249], [598, 276], [584, 302], [662, 302], [622, 257]], "#b3c3d8")

# --- spruce forest (snow on the branches)
poly([[0, 300], [0, 140], [25, 108], [50, 130], [78, 98], [105, 132], [135, 112], [165, 140], [200, 128],
      [235, 152], [265, 150], [300, 178], [345, 190], [390, 204], [430, 218], [470, 228], [510, 238],
      [560, 252], [600, 300]], SPRUCE, "left forested hillside, dark spruces with snow on the branches")
poly([[990, 335], [995, 252], [1035, 240], [1080, 226], [1125, 232], [1180, 214], [1240, 224], [1300, 212],
      [1360, 220], [1420, 204], [1500, 198], [1560, 188], [1620, 184], [1690, 172], [1720, 335]], SPRUCE,
     "spruce forest behind the station")
poly([[1130, 214], [1180, 212], [1262, 332], [1205, 336]], "#e8eef5",
     "groomed ski piste cut through the forest, coming down to the station")
# --- rocky slope with snow (right)
poly([[1380, 334], [1440, 292], [1520, 262], [1600, 236], [1700, 206], [1800, 182], [1920, 150], [1920, 345],
      [1380, 345]], "#e4eaf1", "steep rocky slope under snow, grey boulders showing")
for b in ([1490, 286, 34, 15], [1560, 268, 26, 12], [1636, 248, 36, 15], [1700, 282, 30, 13],
          [1772, 230, 38, 17], [1846, 258, 32, 15], [1880, 196, 28, 13], [1606, 304, 24, 10], [1520, 316, 30, 11]):
    ellipse(b, "#8f969e")
poly([[1846, 205], [1876, 104], [1906, 205]], SPRUCE, "spruce on the slope top")
poly([[1890, 190], [1912, 118], [1920, 190]], SPRUCE)

# --- left: low modern building with a glass ribbon, a small wooden hut
rect([0, 290, 442, 18], SNOW, "snow on the flat roof")
rect([0, 308, 442, 108], "#d3d8de", "low white modern building")
rect([110, 330, 262, 78], "#5d7a93", "glass ribbon")
rect([0, 296, 110, 14], SNOW)
rect([0, 310, 110, 42], "#c6a888")
poly([[112, 382], [170, 344], [238, 382]], SNOW, "snowy roof of the small wooden hut")
rect([124, 382, 102, 58], "#6c4b31", "small wooden hut")
poly([[330, 472], [372, 336], [418, 300], [466, 318], [518, 380], [562, 472]], "#4b6a5c",
     "young snow-laden spruces and shrubs")
poly([[372, 336], [418, 300], [466, 318], [490, 350], [440, 330], [400, 345]], SNOW)

# --- Hotel Posta (steep-gabled wooden chalet, snowy roofs)
poly([[560, 432], [560, 362], [622, 346], [702, 350], [762, 364], [790, 432]], "#e6ecf3",
     "snow-covered hedge in front of the hotel")
poly([[606, 308], [644, 256], [782, 251], [798, 306]], SNOW, "snow on the left wing roof")
line([[606, 309], [798, 307]], "#4f3d2e", 5)
rect([614, 310, 182, 54], "#e5d4b0", "left wing: cream walls, timber")
rect([624, 323, 166, 24], "#4a3a2e", "window row")
for x in (656, 676, 728):
    rect([x, 244, 9, 16], "#8a7c6e", "chimney")
    rect([x - 2, 240, 13, 6], SNOW)
poly([[770, 262], [912, 202], [1008, 298], [986, 306], [912, 226], [834, 302], [800, 302]], SNOW,
     "main chalet: very steep snowy gable roof")
poly([[834, 302], [912, 226], [986, 306]], "#c6925a", "timber gable front")
rect([862, 262, 98, 9], "#5a3b26", "timber balcony")
rect([850, 284, 124, 10], "#5a3b26", "timber balcony")
rect([834, 302, 156, 62], "#b5844d", "ground floor")
rect([846, 318, 82, 11], "#5a3b26", "entrance canopy")
rect([852, 330, 70, 34], "#3c3a39", "glazed entrance")
poly([[962, 294], [1012, 268], [1074, 318], [1060, 324], [1012, 288], [976, 302]], SNOW, "right wing roof")
poly([[976, 302], [1012, 288], [1060, 324], [1060, 364], [976, 364]], "#c6925a", "right wing gable")
poly([[796, 364], [820, 192], [846, 364]], "#2b4538", "tall spruce in front of the hotel")
poly([[1062, 332], [1083, 214], [1104, 332]], "#2b4538", "tall spruce")
poly([[740, 396], [772, 368], [982, 366], [962, 394]], "#8b9199", "ploughed forecourt in front of the hotel")

# --- the road (ploughed asphalt) and the left snow bank
poly([[0, 1080], [0, 925], [200, 805], [380, 695], [500, 615], [560, 550], [650, 470], [745, 398], [962, 394],
      [958, 402], [975, 450], [1010, 510], [1050, 570], [1095, 650], [1130, 700], [1170, 750], [1205, 800],
      [1270, 900], [1340, 1000], [1396, 1080]], "#767d85", "ploughed asphalt access road, walkable")
poly([[0, 925], [200, 805], [380, 695], [500, 615], [560, 550], [650, 470], [745, 398], [732, 396],
      [600, 456], [570, 470], [480, 528], [420, 556], [300, 618], [200, 646], [100, 686], [0, 716]], SNOW,
     "left verge: ploughed snow bank")
line([[0, 925], [200, 805], [380, 695], [500, 615], [560, 550], [650, 470], [745, 398]], SNOW_SHADE, 7,
     "toe of the snow bank")

# --- stream, snowy boulders, wooden footbridge (left)
poly([[0, 716], [100, 686], [200, 646], [282, 622], [262, 640], [150, 690], [40, 742], [0, 760]], "#3a5662",
     "dark mountain stream")
for b in ([0, 628, 80, 42], [86, 604, 64, 32], [0, 742, 86, 44], [150, 648, 52, 26], [60, 676, 58, 26]):
    ellipse(b, "#e8eef5")
rect([268, 566, 142, 60], "#b5bcc5", "concrete bridge abutment")
rect([268, 558, 142, 10], SNOW)
for x in (8, 92, 176, 258, 330):
    line([[x, 470 if x < 300 else 476], [x, 586 if x < 300 else 574]], "#5d4330", 8)
for a, b in (((8, 476), (92, 584)), ((92, 470), (176, 582)), ((176, 466), (258, 580)), ((258, 468), (330, 574)),
             ((8, 584), (92, 470)), ((92, 582), (176, 466)), ((176, 580), (258, 468)), ((258, 578), (330, 472))):
    line([list(a), list(b)], "#5d4330", 7)
line([[0, 486], [80, 471], [160, 463], [250, 463], [330, 473], [400, 489]], "#5d4330", 10,
     "arched top rail of the wooden footbridge")
line([[0, 479], [80, 464], [160, 456], [250, 456], [330, 466], [400, 482]], SNOW, 6, "snow on the rail")
line([[0, 590], [330, 575]], "#5d4330", 12, "bridge deck beam")
line([[330, 490], [600, 447]], "#946437", 7, "timber railing along the stream")
line([[330, 484], [600, 441]], SNOW, 5)
line([[330, 546], [570, 520]], "#946437", 7)
for a, b in (((330, 490), (420, 540)), ((420, 476), (510, 530)), ((510, 462), (570, 520)),
             ((330, 546), (420, 476)), ((420, 540), (510, 462)), ((510, 530), (600, 447))):
    line([list(a), list(b)], "#946437", 6)

# --- the field above the wall: groomed snow, fence, pylon foundation
poly([[962, 392], [1005, 430], [1060, 480], [1130, 535], [1215, 600], [1330, 690], [1510, 800], [1700, 920],
      [1840, 1000], [1920, 1050], [1920, 345], [1380, 345], [1250, 362], [960, 376]], SNOW,
     "groomed snow field (piste run-out) above the retaining wall")
for a, b in (((1010, 408), (1920, 520)), ((1060, 452), (1920, 610)), ((1130, 510), (1920, 720)),
             ((1220, 580), (1920, 840)), ((1330, 668), (1920, 960))):
    line([list(a), list(b)], "#dfe7f0", 4)
line([[1240, 380], [1920, 450]], "#5a4232", 5, "wooden fence, upper rail")
line([[1246, 400], [1920, 474]], "#5a4232", 5, "lower rail, half in the snow")
for x in (1270, 1335, 1405, 1485, 1565, 1655, 1745, 1835, 1912):
    y0 = 380 + (x - 1240) * 70 / 680
    line([[x, y0 - 6], [x, y0 + 36]], "#5a4232", 6)

# --- gondola station (bullwheel housing + low hall with a dark glass roof and a thin orange band)
rect([1430, 304, 330, 17], "#2c3a4a", "dark glass roof of the station hall")
rect([1430, 300, 330, 6], SNOW)
rect([1430, 321, 330, 4], "#e07a2e", "thin orange band")
rect([1430, 325, 330, 70], "#edf0f3", "station hall, white walls, no posters")
poly([[1255, 302], [1272, 280], [1322, 268], [1420, 272], [1442, 300], [1432, 346], [1260, 346]], "#dce1e7",
     "white-grey bullwheel housing at the station end")
poly([[1272, 280], [1322, 268], [1420, 272], [1410, 280], [1322, 276]], SNOW)
rect([1260, 346, 172, 32], "#46505b", "boarding level under the housing")
rect([1300, 348, 40, 30], "#d9652b", "a parked gondola cabin")

# --- the steel pylon and the two ropes with two cabins
poly([[1752, 0], [1842, 0], [1856, 470], [1760, 470]], "#bac2ca", "steel tube pylon")
poly([[1814, 0], [1842, 0], [1856, 470], [1832, 470]], "#8c959e")
for y in range(20, 460, 36):
    line([[1822, y], [1842, y]], "#6f7880", 3)
rect([1718, 462, 144, 36], "#a8afb7", "pylon foundation")
rect([1712, 456, 156, 10], SNOW)
line([[1495, 0], [1365, 236]], "#343a42", 4, "gondola rope (uphill)")
line([[1762, 0], [1522, 222]], "#343a42", 4, "gondola rope (downhill)")
line([[1438, 104], [1440, 128]], "#343a42", 4)
shapes.append({"type": "rect", "box": [1414, 126, 54, 58], "fill": "#d9652b", "radius": 12,
               "note": "gondola cabin hanging on the rope (unbranded)"})
rect([1418, 136, 46, 22], "#3a4d5d")
line([[1655, 99], [1657, 128]], "#343a42", 4)
shapes.append({"type": "rect", "box": [1626, 126, 64, 70], "fill": "#d9652b", "radius": 14,
               "note": "second cabin, closer"})
rect([1631, 138, 54, 26], "#3a4d5d")

# --- the stone retaining wall along the right side of the road (a gap with steps at x ~1110-1255)
poly([[958, 402], [975, 450], [1010, 510], [1050, 570], [1095, 650], [1130, 700], [1170, 750], [1205, 800],
      [1270, 900], [1340, 1000], [1396, 1080], [1920, 1080], [1920, 1050], [1840, 1000], [1700, 920], [1510, 800], [1330, 690],
      [1215, 600], [1130, 535], [1060, 480], [1005, 430], [962, 392]], "#8b847d",
     "stone-clad retaining wall (irregular grey-brown stones)")
for b in ([1000, 440, 22, 12], [1040, 500, 26, 14], [1090, 545, 30, 16], [1290, 720, 44, 26], [1350, 800, 52, 30],
          [1420, 760, 46, 26], [1400, 880, 60, 34], [1480, 840, 56, 30], [1540, 930, 70, 40], [1620, 900, 60, 34],
          [1600, 1000, 74, 44], [1700, 980, 70, 40], [1780, 1030, 70, 40], [1460, 960, 60, 36]):
    ellipse(b, "#6f6862")
# gap in the wall: far edge foot (1130, 700) / top (1182, 574), near edge foot (1205, 800) / top (1262, 637)
poly([[1130, 700], [1182, 574], [1262, 637], [1205, 800]], "#a9afb6", "three granite steps up through a gap in the wall")
for a, b in (((1143, 668), (1219, 759)), ((1156, 637), (1233, 718)), ((1169, 605), (1248, 678))):
    line([list(a), list(b)], SNOW, 6)
line([[962, 392], [1005, 430], [1060, 480], [1130, 535], [1182, 574]], "#eef2f6", 14, "snow on the concrete coping")
line([[1262, 637], [1330, 690], [1510, 800], [1700, 920], [1840, 1000], [1920, 1050]], "#eef2f6", 16)
line([[958, 404], [975, 452], [1010, 512], [1050, 572], [1095, 652], [1130, 702]], SNOW, 14,
     "low ploughed snow ridge at the wall foot")
line([[1205, 802], [1270, 902], [1340, 1002], [1396, 1082]], SNOW, 20)

# --- interactive props (each fills its blocking rect)
# S41.gate: ticket gate in the gap mouth (reader pillar on the road side, turnstile wings across the mouth)
rect([1108, 552, 26, 166], "#2b3036", "card reader pillar")
ellipse([1113, 566, 16, 11], "#63e08a")
rect([1146, 590, 20, 140], "#c4ccd4", "stainless gate post")
rect([1192, 625, 22, 165], "#c4ccd4", "stainless gate post")
poly([[1166, 640], [1192, 668], [1192, 742], [1166, 714]], "#a8cde0", "glass gate wings")
# S41.ambient 2: signpost on the wall top at the far edge of the gap
line([[1184, 282], [1184, 576]], "#6b4a30", 9, "signpost post standing on the wall top")
poly([[1100, 288], [1252, 288], [1272, 303], [1252, 318], [1100, 318]], "#4a3424", "arrow board PRIEHYBA")
poly([[1124, 322], [1270, 322], [1270, 352], [1124, 352], [1104, 337]], "#4a3424", "arrow board BIELA PUT")
poly([[1100, 356], [1252, 356], [1272, 371], [1252, 386], [1100, 386]], "#4a3424", "arrow board CHOPOK")
rect([1100, 282, 172, 6], SNOW)
# time node: the fictional Atlas exhibition stand
rect([452, 446, 56, 190], "#d8ba8b", "slim light-wood exhibition pillar")
ellipse([446, 452, 68, 68], "#2fb3b0", "round turquoise clock ring")
ellipse([456, 462, 48, 48], "#f4f1e8", "clock face")
rect([440, 632, 80, 12], "#8d949c", "base plate")
ellipse([450, 436, 60, 18], SNOW)
# S41.ambient 1: two benches on the cleared verge
rect([214, 622, 152, 24], "#8a5a35", "far bench backrest")
rect([214, 652, 152, 14], "#8a5a35", "far bench seat")
rect([214, 616, 152, 8], SNOW)
rect([214, 648, 152, 6], SNOW)
for x in (222, 356):
    line([[x, 666], [x, 690]], "#3e3a36", 6)
rect([40, 664, 186, 32], "#8a5a35", "near bench backrest")
rect([40, 704, 186, 18], "#8a5a35", "near bench seat")
rect([40, 656, 186, 10], SNOW)
rect([40, 700, 186, 7], SNOW)
for x in (50, 214):
    line([[x, 722], [x, 760]], "#3e3a36", 7)

spec = {"background": "#a9cbe9", "note": (
    "S41 winter (owner photos 2026-10-06): blocking traced from the friend's photo of the access road at Biela Put "
    "(aligned: game = (photo - (244, 124)) * 1.15); horizon y ~347, camera ~2.8 m. Flat colour blocks only."),
    "shapes": shapes}
out = ROOT / "art" / "prompts" / "natural" / "S41.sketch.json"
out.write_text(json.dumps(spec, indent=1, ensure_ascii=False), encoding="utf-8")
print(out, len(shapes), "shapes")
