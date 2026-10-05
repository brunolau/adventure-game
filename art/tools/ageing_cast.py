"""The ageing cast of LastBell (style A): one person, several ages, one recognisable face.

People and their per-age characters (game.json characters[]):
  TONO  Anton 'Tóno' Farkaš (born 1970)   TONO82 (12, S64), TONO (25, S13), TONO20 (50, S56)
  JANA  Jana Vargová (born 1970)          JANA82 (12, S60), JANA95 (25, S15), JANA20 (50, S54), JANA35 (65, S44)
  MIRA  Mira Hrušková (born 1940)         MIRA60 (20, S39), MIRA95 (55, S14); MIRA20 (80, S06) = approved anchor
  OTO   Oto Bielik (born 1916)            OTO (44, S36), OTO82 (66, S64)

Order of work (PIPELINE.md, plus a likeness step):
  1. lineup <PERSON>   one Pro 2K 16:9 age-progression sheet (all ages side by side, same scale, same 3/4 view);
                       split with `split <PERSON>`. It fixes the face, posture and colour progression.
  2. base <ID>         Pro 2K 3:4 per-age sheet, references = the person's lineup figure (identity) and the cast
                       anchor (ADAM keyed 3/4; for Mira the approved MIRA20 sheet), posed for the room's staging
                       (seated on a stool / chair, phone at the ear behind glass, webcam portrait ...).
  3. edit <ID> <kind>  NB2 edits of the base: blink / talk / talk_oh (1K), gesture / variant (2K).
  4. video <ID>        Hailuo-02 idle loop (start = end frame), standard 768p or --pro 1080p.
Everything after that is local and free: `build <ID>` (keying, still set with head-band transplants, video idle,
busts, breathing idles), `export <ID>` (WebP grids <= 4096 px + JSON + actor.json), `likeness <PERSON>` (contact
sheet of the shipped sprites at their real relative size plus enlarged heads).

Paid calls are logged to art/spend-log.csv by fal_api.run(); a task guard refuses a call once the spend of this
task (asset prefixes of these characters, counted from TASK_SINCE) would pass --budget.

Run from art/tools with PYTHONIOENCODING=utf-8 python -X utf8 ageing_cast.py ...
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import chars
import fal_api
import frames as fr

ART = fal_api.ART
REPO = ART.parent
CHAR_ROOT = ART / "characters"
LIKE_ROOT = CHAR_ROOT / "likeness"
GAME_ACTORS = REPO / "src" / "game" / "assets" / "actors"
CAST_ANCHOR = CHAR_ROOT / "ADAM" / "keyed" / "side_right_3q.png"
MIRA20_SHEET = CHAR_ROOT / "MIRA20" / "sheet_npc_3q.png"
DANA_SHEET = CHAR_ROOT / "DANA" / "sheet_npc_3q.png"  # approved painterly woman: cast anchor for Jana
STYLE_PAINTING = REPO / "src" / "game" / "assets" / "bg" / "S09.webp"

TASK_SINCE = "2026-10-05T04:34:00"
TASK_BUDGET = 22.0
IDS = ["TONO82", "TONO", "TONO20", "JANA82", "JANA95", "JANA20", "JANA35", "MIRA60", "MIRA95", "OTO", "OTO82"]
SCOPES = tuple(["characters/likeness/"] + [f"characters/{i}/" for i in IDS])

# ----------------------------------------------------------------------------- people (likeness)

PEOPLE = {
    "TONO": {
        "who": "Anton 'Tóno' Farkaš, a Slovak boy and later man born in 1970",
        "pronoun": "he",
        "core": ("a long, narrow face with high cheekbones, a long straight nose with a small bump on the bridge, thick "
                 "straight very dark eyebrows, deep-set dark brown eyes, ears that stick out a little, a wide mouth with "
                 "a lopsided dry half-smile, very dark brown (almost black) hair, a tall lanky build with long arms and "
                 "a slight forward stoop of the shoulders."),
        "ages": ["TONO82", "TONO", "TONO20"],
        "lineup": [
            "12 years old in December 1982: a thin, lanky schoolboy with a thick straight fringe down to his eyebrows; "
            "an oversized hand-knitted wool sweater in dark brick red with a cream zigzag band across the chest, the "
            "long sleeves rolled at the cuffs, a knitted navy-blue scarf, brown corduroy trousers, dark brown lace-up "
            "winter boots; he holds a small hand-carved wooden swallow model (unpainted light wood, pointed wings, "
            "forked tail) in both hands in front of his chest. No keys, no work coat.",
            "25 years old in June 1995: a young school caretaker, clean-shaven, his hair in a mid-1990s curtain "
            "haircut with a middle parting; an open knee-length brown cotton caretaker's work coat over a light "
            "blue-and-grey checked short-sleeved shirt, dark grey trousers, brown work shoes; a big bunch of keys on a "
            "steel ring hangs at his belt, with a small handmade swallow cut from tin hanging on the ring.",
            "50 years old in October 2020: the same school caretaker, still working and not retired, a little heavier "
            "at the waist; short neat hair with clearly greying temples, a few lines on the forehead and around the "
            "eyes, rectangular thin dark-framed glasses; a dark rust-brown knitted quarter-zip work sweater over a "
            "checked shirt collar, dark grey work trousers, brown shoes; a small single key in his near hand.",
        ],
        "child_note": "The boy on the left is clearly a child, about 150 cm tall, so about 85% of the men's height.",
    },
    "JANA": {
        "who": "Jana Vargová, a Slovak girl and later woman born in 1970",
        "pronoun": "she",
        "core": ("a heart-shaped face with a small pointed chin, large wide-set grey-blue eyes, straight light-brown "
                 "eyebrows, a small slightly upturned nose with light freckles across the nose and cheeks, a narrow "
                 "mouth with a shy but precise smile, light ash-brown hair, a slim build and a slightly reserved "
                 "posture with the head tilted a little forward."),
        "ages": ["JANA82", "JANA95", "JANA20", "JANA35"],
        "lineup": [
            "12 years old in December 1982, indoors at school: a schoolgirl with her hair in a ponytail and a short "
            "fringe; a hand-knitted sweater with horizontal stripes of navy blue, red and cream, a dark navy skirt, "
            "thick dark red woollen tights, white indoor school slippers; she holds a large sheet of drawing paper "
            "with a hand-drawn circuit diagram against her chest, a pencil in her hand. No neckerchief, no scarf.",
            "25 years old in June 1995: her hair cut short in a mid-1990s pixie cut; a thin dark navy-blue cotton "
            "sweater with the sleeves pushed up, high-waisted light blue jeans, white trainers; she holds a grey "
            "lever-arch file against her side.",
            "50 years old in October 2020: her hair in a short practical bob with a few grey strands, fine lines "
            "around the eyes, thin oval metal-framed glasses; a soft heather-grey cardigan over a dark blue top, dark "
            "trousers, comfortable shoes.",
            "65 years old in June 2035: short neat silver-grey hair, smile lines, the same kind of thin oval glasses; "
            "a light grey-blue scarf loosely around her neck, a light beige linen jacket over a cream top, dark blue "
            "trousers, comfortable shoes, a small flat dark brown document bag on a strap over her shoulder.",
        ],
        "child_note": "The girl on the left is clearly a child, about 150 cm tall, so about 88% of the women's height.",
    },
    "MIRA": {
        "who": "Mira Hrušková, a Slovak woman born in 1940",
        "pronoun": "she",
        "core": ("copy them from the approved 80-year-old Mira in the reference image: a round soft face with full "
                 "cheeks, a small rounded nose, alert intelligent eyes with a wry look, gently arched eyebrows, a small "
                 "knowing closed-mouth smile, round thin metal-framed glasses, short soft wavy hair, a short compact "
                 "build and an upright posture."),
        "ages": ["MIRA60", "MIRA95", "MIRA20"],
        "lineup": [
            "20 years old in June 1960: a young technical assistant; chestnut-brown hair in a short soft wavy 1960 "
            "hairstyle with a side parting, smooth young skin; a short-sleeved ochre (golden yellow-brown) cotton "
            "blouse with a small round collar tucked into a sturdy knee-length dark brown A-line skirt with a narrow "
            "belt, light stockings, low-heeled brown leather shoes; a yellow pencil in her near hand.",
            "55 years old in June 1995: a volunteer leader of a school club; short soft wavy hair, medium brown with "
            "many silver-grey streaks, a few fine lines; a mid-blue knitted cotton crew-neck sweater over a white "
            "blouse collar, the sleeves pushed up a little, a smudge of white chalk dust on the near sleeve, dark "
            "brown trousers, brown leather shoes.",
            "80 years old in October 2020: exactly the approved character of the reference image (white hair, ochre "
            "knitted sweater over a white blouse collar, dark brown trousers, house shoes), standing with both arms "
            "relaxed at her sides, no phone.",
        ],
        "child_note": "",
    },
    "OTO": {
        "who": "Oto Bielik, a Slovak civilian mechanic born in 1916",
        "pronoun": "he",
        "core": ("a broad, square face with a strong jaw, a large straight nose, bushy eyebrows, a neat full moustache, "
                 "kind attentive eyes behind round brass-rimmed glasses, a stocky build with broad shoulders and an "
                 "upright, precise posture."),
        "ages": ["OTO", "OTO82"],
        "lineup": [
            "44 years old in June 1960: dark brown hair combed back with a side parting and the first grey at the "
            "temples, a dark brown moustache; a knee-length mid-blue cotton work coat, buttoned, over a white shirt "
            "and a dark tie, a pencil and a small steel ruler in the breast pocket, dark grey trousers, black leather "
            "shoes.",
            "66 years old in December 1982: the same mechanic, older but sturdy and upright; grey hair, thinner and "
            "combed back, a grey moustache, deeper lines on the face, the same round brass-rimmed glasses; the same "
            "kind of knee-length blue work coat, buttoned, over a grey knitted sweater and a checked shirt collar, "
            "dark trousers, black shoes; a small flat metal file in his near hand.",
        ],
        "child_note": "",
    },
}

ORDINALS = ["Left", "Second from the left", "Third from the left", "Right"]


def position_words(n: int) -> list[str]:
    if n == 2:
        return ["Left", "Right"]
    if n == 3:
        return ["Left", "Middle", "Right"]
    return ORDINALS


# ----------------------------------------------------------------------------- per-age briefs

LIGHT = ("Even, soft, warm daylight from the front-left, no strong cast shadows, so the sprite fits many scenes.")
ADULT_RULES = ("Slightly exaggerated cartoon proportions as in classic 1990s adventure games (head a little large, "
               "about 1/6.5 of the height), but still a believable adult.")
CHILD_RULES = ("Slightly exaggerated cartoon proportions as in classic 1990s adventure games (head a little large, "
               "about 1/6 of the height), but a believable 12-year-old child, not a toddler and not an adult.")

BRIEFS: dict[str, dict] = {
    "TONO82": {
        "person": "TONO", "age": 12, "pronoun": "he", "room": "S64", "era": 1982, "masked": False,
        "staging": "seated", "child": True,
        "design_sk": "Dvanásťročný chlapec, tmavá ofina, veľký sveter, školská taška, drevený model lastovičky; "
                     "žiadny školnícky plášť ani zväzok služobných kľúčov.",
        "description": ("Tóno, a 12-year-old Slovak schoolboy in early December 1982, outdoors by the school's service "
                        "window: curious and concrete, a thin lanky boy with a long narrow face, a long straight nose, "
                        "thick straight very dark eyebrows, deep-set dark brown eyes, ears that stick out a little and "
                        "a thick straight fringe of very dark brown hair down to his eyebrows. He wears an oversized "
                        "hand-knitted wool sweater in dark brick red with a cream zigzag band across the chest (long "
                        "sleeves rolled at the cuffs), a knitted navy-blue scarf, brown corduroy trousers and dark "
                        "brown lace-up winter boots. He holds a small hand-carved wooden swallow model (unpainted light "
                        "wood, pointed wings, forked tail) in both hands. No keys, no work coat, no hat."),
        "pose": ("Pose: he sits on a low wooden three-legged stool (the seat a little below his knee height), in a "
                 "three-quarter view turned toward the right: body and face turned about 45 degrees toward the right "
                 "edge of the image, both eyes visible. Knees bent, both boots flat on the ground in front of the "
                 "stool, forearms resting on his thighs, the wooden swallow model held in both hands in his lap. A "
                 "brown leatherette 1980s school satchel with two buckles stands upright on the ground beside the "
                 "stool, on the left of it. Calm, curious expression, mouth closed. The complete boy, the complete "
                 "stool and the satchel are visible."),
        "gesture": ("He lifts the wooden swallow model up in front of his chest with both hands and turns it a little "
                    "between his fingers, looking at it proudly."),
        "idle_motion": ("The boy sits still on the low stool, relaxed and alive: calm breathing, a natural blink, he "
                        "turns the little wooden swallow very slightly in his hands, a small curious tilt of the head. "
                        "He stays seated; the stool and the satchel do not move."),
        "notes": ("S64: sits outside the open service window on a low stool (the stool and the satchel are part of "
                  "the sprite); his grandfather OTO82 works inside behind the window."),
    },
    "TONO": {
        "person": "TONO", "age": 25, "pronoun": "he", "room": "S13", "era": 1995, "masked": False,
        "staging": "seated",
        "design_sk": "Dvadsaťpäťročný muž, tmavé vlasy, hnedý pracovný plášť, zväzok kľúčov, vlastnoručná kovová "
                     "lastovička.",
        "description": ("Tóno (Anton Farkaš), a 25-year-old Slovak young school caretaker in June 1995: dry humour, "
                        "practical. A tall lanky young man with a long narrow face, a long straight nose with a small "
                        "bump on the bridge, thick straight very dark eyebrows, deep-set dark brown eyes, ears that "
                        "stick out a little, clean-shaven, very dark brown hair in a mid-1990s curtain haircut with a "
                        "middle parting. He wears an open knee-length brown cotton caretaker's work coat over a light "
                        "blue-and-grey checked short-sleeved shirt, dark grey trousers and brown work shoes. A big bunch "
                        "of keys on a steel ring hangs at his belt, and on the ring hangs a small handmade swallow cut "
                        "from tin."),
        "pose": ("Pose: he sits on a plain wooden school chair with a straight back, in a three-quarter view turned "
                 "toward the right: body and face turned about 45 degrees toward the right edge of the image, both "
                 "eyes visible. He sits upright but relaxed, thighs level, knees bent at a right angle, both shoes "
                 "flat on the floor; his near hand rests on his near thigh holding a ballpoint pen, his far hand rests "
                 "on his far knee; the bunch of keys hangs at his near hip. Calm, attentive, dry expression, mouth "
                 "closed. The complete man and the complete chair are visible."),
        "gesture": ("He raises his near hand to chest height and turns one small key between his thumb and index "
                    "finger (a single key, separate from the bunch at his belt), the pen now held in his other hand."),
        "idle_motion": ("He sits still on the chair, relaxed and attentive: calm breathing, a natural blink, a small "
                        "nod, his fingers move slightly on the pen. He stays seated; the chair does not move."),
        "notes": ("S13: art_brief 'Tóno sedí pri evidencii návštev'. The chair is part of the sprite; the visitor-log "
                  "desk belongs to the background, behind / left of him (ISSUES ART-AGE-01)."),
    },
    "TONO20": {
        "person": "TONO", "age": 50, "pronoun": "he", "room": "S56", "era": 2020, "masked": False,
        "staging": "window_glass",
        "design_sk": "Päťdesiatročný muž s mierne prešedivenými spánkami, okuliare, pracovný sveter, kovová "
                     "lastovička na okne.",
        "description": ("Tóno (Anton Farkaš), a 50-year-old Slovak school caretaker in late October 2020, still "
                        "working and not retired, calm, dry humour: a tall lanky man, a little heavier at the waist, "
                        "with a long narrow face, a long straight nose with a small bump on the bridge, thick straight "
                        "dark eyebrows, deep-set dark brown eyes, ears that stick out a little, short neat very dark "
                        "brown hair with clearly greying temples, a few lines on the forehead and around the eyes and "
                        "rectangular thin dark-framed glasses. He wears a dark rust-brown knitted quarter-zip work "
                        "sweater over a checked shirt collar, dark grey work trousers and brown shoes. He is indoors "
                        "alone behind his service window, so he wears no face mask. With his far hand he holds a plain "
                        "dark mobile phone (no logo) to his far ear, the phone on the far side of his head so his whole "
                        "face stays visible; his near hand holds a small single key at waist height."),
        "pose": ("Pose: standing relaxed in a three-quarter view turned toward the right: body and face turned about "
                 "45 degrees toward the right edge of the image, both eyes visible, both feet flat on the ground, "
                 "calm attentive expression, mouth closed, listening on the phone."),
        "gesture": ("Still holding the phone to his ear with his far hand, he raises his near hand to chest height and "
                    "turns the small key between his thumb and index finger."),
        "idle_motion": ("He stands still holding the phone to his ear, listening: calm breathing, a natural blink, a "
                        "small attentive nod, a tiny shift of weight. The phone stays at his ear."),
        "notes": ("S56: only ever behind the closed service window, on the phone with Adam. Default variant "
                  "window_glass (bust cut at the sill line, pivot = sill)."),
    },
    "JANA82": {
        "person": "JANA", "age": 12, "pronoun": "she", "room": "S60", "era": 1982, "masked": False,
        "staging": "standing", "child": True,
        "design_sk": "Pruhovaný sveter, pionierska šatka odložená vedľa výkresu, ceruzka.",
        "description": ("Jana, a 12-year-old Slovak schoolgirl at a school technical exhibition in early December "
                        "1982, indoors: quietly precise, lights up when she can explain her drawing. A slim girl with a "
                        "heart-shaped face and a small pointed chin, large wide-set grey-blue eyes, straight light-brown "
                        "eyebrows, a small slightly upturned nose with light freckles, light ash-brown hair in a "
                        "ponytail with a short fringe. She wears a hand-knitted sweater with horizontal stripes of navy "
                        "blue, red and cream, a dark navy skirt, thick dark red woollen tights and white indoor school "
                        "slippers. She holds a large sheet of drawing paper with a hand-drawn radio circuit diagram "
                        "(lines and small symbols only, no readable text) against her chest with her far hand, a "
                        "pencil in her near hand. She wears no neckerchief and no scarf."),
        "pose": ("Pose: standing in a three-quarter view turned toward the right, exactly like the approved character "
                 "in the reference: body and face turned about 45 degrees toward the right edge of the image, both "
                 "eyes visible, both feet flat on the ground, a slightly shy posture with the head tilted a little "
                 "forward, a small shy smile, mouth closed."),
        "gesture": ("She holds the drawing out a little in front of her with her far hand and points at a spot on it "
                    "with the pencil in her near hand, eager to explain."),
        "idle_motion": ("She stands still holding her drawing against her chest, a little shy: calm breathing, a "
                        "natural blink, a quick glance down at the drawing and back up, a tiny shift of weight."),
        "notes": ("S60: the red pioneer neckerchief lies on the desk next to her drawing (background prop), it is not "
                  "worn (design 'šatka odložená vedľa výkresu')."),
    },
    "JANA95": {
        "person": "JANA", "age": 25, "pronoun": "she", "room": "S15", "era": 1995, "masked": False,
        "staging": "standing",
        "design_sk": "Krátke vlasy, tmavomodrý sveter, šanón; po Q9C pribudne multimeter.",
        "description": ("Jana Vargová, a 25-year-old Slovak woman in June 1995 who helps the school organise its "
                        "exhibition: more confident, the same precise words. A slim young woman with a heart-shaped "
                        "face and a small pointed chin, large wide-set grey-blue eyes, straight light-brown eyebrows, a "
                        "small slightly upturned nose with light freckles, light ash-brown hair cut short in a "
                        "mid-1990s pixie cut. She wears a thin dark navy-blue cotton sweater with the sleeves pushed up, "
                        "high-waisted light blue jeans and white trainers. She holds a grey lever-arch file (binder, no "
                        "labels) against her side with her near arm; her far hand hangs relaxed."),
        "pose": ("Pose: standing relaxed in a three-quarter view turned toward the right: body and face turned about "
                 "45 degrees toward the right edge of the image, both eyes visible, both feet flat on the ground, "
                 "calm friendly expression, mouth closed."),
        "gesture": ("Keeping the file against her side with her near arm, she raises her far hand to chest height, "
                    "palm open, in a small explaining gesture."),
        "variant_q9c": ("In her far hand she now also holds a small yellow handheld multimeter (no brand, no text) with "
                        "its two red and black test leads coiled around it, held relaxed at hip height."),
        "variant_q9c_gesture": ("Keeping the file against her side with her near arm, she raises the small yellow "
                                "multimeter in her far hand to chest height to show it, the test leads hanging down."),
        "idle_motion": ("She stands still holding the file against her side: calm breathing, a natural blink, a small "
                        "nod, a tiny shift of weight."),
        "notes": "S15. Variant q9c (after Q9C, BF_JANA): she also carries a multimeter.",
    },
    "JANA20": {
        "person": "JANA", "age": 50, "pronoun": "she", "room": "S54", "era": 2020, "masked": False,
        "staging": "screen",
        "design_sk": "Videoportrét na notebooku, okuliare, domáce pracovné prostredie.",
        "description": ("Jana Vargová, a 50-year-old Slovak woman in late October 2020 who coordinates the school's "
                        "lending of equipment, on a video call from her home: clear and practical. A slim woman with a "
                        "heart-shaped face and a small pointed chin, large wide-set grey-blue eyes, straight light-brown "
                        "eyebrows, a small slightly upturned nose with faint freckles, light ash-brown hair in a short "
                        "practical bob with a few grey strands, fine lines around the eyes and thin oval metal-framed "
                        "glasses. She wears a soft heather-grey cardigan over a dark blue top. She is at home, so she "
                        "wears no face mask."),
        "pose": "",
        "gesture": ("She raises her near hand into the picture beside her chin, palm open, in a small explaining "
                    "gesture."),
        "variant_q9c": "",
        "idle_motion": ("She sits at her desk in a video call, listening attentively: calm breathing, a natural blink, "
                        "a small nod, a slight tilt of the head. A static webcam."),
        "notes": ("S54: she is not in the room; she is a live video portrait on a laptop on the bench. Default variant "
                  "'laptop' (an open laptop showing her); 'screen' = the flat portrait for compositing into a painted "
                  "screen. Variant q9c: refurbished laptops with labels on the shelf behind her."),
    },
    "JANA35": {
        "person": "JANA", "age": 65, "pronoun": "she", "room": "S44", "era": 2035, "masked": False,
        "staging": "standing",
        "design_sk": "Sivomodrý šál, okuliare, malá taška na dokumenty.",
        "description": ("Jana Vargová, a 65-year-old Slovak woman visiting an exhibition in a hotel salon in June "
                        "2035: calm, gently amused. A slim woman with a heart-shaped face and a small pointed chin, "
                        "large wide-set grey-blue eyes, straight light eyebrows, a small slightly upturned nose with "
                        "faint freckles, short neat silver-grey hair, smile lines and thin oval metal-framed glasses. "
                        "She wears a light grey-blue scarf loosely around her neck, a light beige linen jacket over a "
                        "cream top, dark blue trousers and comfortable shoes, and a small flat dark brown document bag "
                        "on a strap over her shoulder. Ordinary present-day clothes, nothing futuristic."),
        "pose": ("Pose: standing relaxed in a three-quarter view turned toward the right: body and face turned about "
                 "45 degrees toward the right edge of the image, both eyes visible, both feet flat on the ground, "
                 "hands relaxed, a calm gently amused expression, mouth closed."),
        "gesture": ("She raises her near hand to chest height in a small amused open-palm gesture, as if saying "
                    "'well, here we are'."),
        "variant_q9c": ("In both hands, in front of her waist, she now holds an old yellowed sheet of drawing paper "
                        "with a child's hand-drawn radio circuit diagram (lines and small symbols only, no readable "
                        "text)."),
        "variant_q9c_gesture": ("She lifts the old yellowed drawing in both hands to chest height and shows it, "
                                "smiling."),
        "idle_motion": ("She stands still, calm and gently amused: calm breathing, a natural blink, a small smile and "
                        "nod, a tiny shift of weight."),
        "notes": "S44. Variant q9c (after Q9C, BF_JANA): she holds her first drawing from 1982.",
    },
    "MIRA60": {
        "person": "MIRA", "age": 20, "pronoun": "she", "room": "S39", "era": 1960, "masked": False,
        "staging": "standing",
        "design_sk": "Okrová blúzka, pevná sukňa, okrúhle okuliare, ceruzka.",
        "description": ("Mira Hrušková, a 20-year-old Slovak technical assistant in a civilian research workshop in "
                        "June 1960: quick, curious, sharp. A petite, slim young woman (short, not stout) with a round soft face "
                        "and full cheeks, a small rounded nose, alert intelligent eyes with a wry look, gently arched "
                        "eyebrows, a small knowing closed-mouth smile, round thin metal-framed glasses and chestnut-brown "
                        "hair in a short soft wavy 1960 hairstyle with a side parting. She wears a short-sleeved ochre "
                        "(golden yellow-brown) cotton blouse with a small round collar tucked into a sturdy knee-length "
                        "dark brown A-line skirt with a narrow belt, light stockings and low-heeled brown leather shoes. "
                        "She holds a yellow pencil in her near hand."),
        "pose": ("Pose: standing upright in a three-quarter view turned toward the right: body and face turned about "
                 "45 degrees toward the right edge of the image, both eyes visible, both feet flat on the ground, "
                 "alert expression, mouth closed."),
        "gesture": ("She raises her near hand with the pencil to chest height, the index finger and the pencil lifted, "
                    "making a precise point."),
        "idle_motion": ("She stands still, alert and curious: calm breathing, a natural blink, a small tilt of the "
                        "head, the pencil turning slightly in her fingers, a tiny shift of weight."),
        "base_fix": ("Important: she wears round thin metal-framed glasses, although the first reference image shows "
                     "her without them; she is 20, a slim petite young woman with a youthful face and smooth young skin, "
                     "not matronly."),
        "notes": "S39 (1960). Likeness anchor: MIRA20.",
    },
    "MIRA95": {
        "person": "MIRA", "age": 55, "pronoun": "she", "room": "S14", "era": 1995, "masked": False,
        "staging": "standing",
        "design_sk": "Modrý sveter, okrúhle okuliare, krieda na rukáve.",
        "description": ("Mira Hrušková, a 55-year-old Slovak volunteer leader of a school memory club in June 1995, a "
                        "retired civil engineer: energetic, precise, tender under the practical tone. A woman of short "
                        "compact build with a round soft face and full cheeks, a few fine lines, a small rounded nose, "
                        "alert intelligent eyes with a wry look, gently arched eyebrows, a small knowing closed-mouth "
                        "smile, round thin metal-framed glasses and short soft wavy hair, medium brown with many "
                        "silver-grey streaks. She wears a mid-blue knitted cotton crew-neck sweater over a white blouse "
                        "collar, the sleeves pushed up a little, a smudge of white chalk dust on the near sleeve, dark "
                        "brown trousers and brown leather shoes."),
        "pose": ("Pose: standing upright in a three-quarter view turned toward the right: body and face turned about "
                 "45 degrees toward the right edge of the image, both eyes visible, both feet flat on the ground, "
                 "hands relaxed, lively attentive expression, mouth closed."),
        "gesture": ("She raises her near hand to chest height with the index finger lifted, making a precise point."),
        "idle_motion": ("She stands still, relaxed and lively: calm breathing, a natural blink, a small nod, a tiny "
                        "shift of weight."),
        "base_fix": ("Important: she is 55, a little younger-looking than in the first reference image: only a few "
                     "fine lines around the eyes and mouth, no deep wrinkles, the hair still mostly medium brown with "
                     "silver-grey streaks."),
        "notes": "S14 (1995), at the table with the tape recorder (background). Likeness anchor: MIRA20.",
    },
    "OTO": {
        "person": "OTO", "age": 44, "pronoun": "he", "room": "S36", "era": 1960, "masked": False,
        "staging": "standing",
        "design_sk": "Modrý pracovný plášť, mosadzné okuliare, jazva na palci.",
        "description": ("Oto Bielik, a 44-year-old Slovak civilian mechanic in his workshop in June 1960: precise, "
                        "open to evidence, not a mad scientist. A stocky man with broad shoulders and an upright "
                        "posture, a broad square face with a strong jaw, a large straight nose, bushy eyebrows, a neat "
                        "full dark brown moustache, kind attentive eyes behind round brass-rimmed glasses, dark brown "
                        "hair combed back with a side parting and the first grey at the temples. He wears a knee-length "
                        "mid-blue cotton work coat, buttoned, over a white shirt and a dark tie, with a pencil and a "
                        "small steel ruler in the breast pocket, dark grey trousers and black leather shoes. A small "
                        "pale scar runs across his near thumb."),
        "pose": ("Pose: standing upright in a three-quarter view turned toward the right: body and face turned about "
                 "45 degrees toward the right edge of the image, both eyes visible, both feet flat on the ground, "
                 "hands relaxed at his sides, attentive expression, mouth closed."),
        "gesture": ("He pushes his round brass-rimmed glasses up his nose with the index finger of his near hand."),
        "idle_motion": ("He stands still, relaxed and attentive: calm breathing, a natural blink, a small thoughtful "
                        "nod, a tiny shift of weight, hands relaxed."),
        "notes": "S36 (1960).",
    },
    "OTO82": {
        "person": "OTO", "age": 66, "pronoun": "he", "room": "S64", "era": 1982, "masked": False,
        "staging": "window",
        "design_sk": "Šedivé vlasy, modrý pracovný plášť, rovnaké mosadzné okuliare ako mladší Oto.",
        "description": ("Oto Bielik, a 66-year-old Slovak mechanic in early December 1982, the grandfather of Tóno: a "
                        "little softer than in 1960, still precise, sturdy and upright. A stocky man with broad "
                        "shoulders, a broad square face with a strong jaw and deeper lines, a large straight nose, bushy "
                        "grey eyebrows, a neat full grey moustache, kind attentive eyes behind the same round "
                        "brass-rimmed glasses, grey hair, thinner and combed back. He wears a knee-length blue cotton "
                        "work coat, buttoned, over a grey knitted sweater and a checked shirt collar, dark trousers and "
                        "black shoes. He holds a small flat metal file in his near hand."),
        "pose": ("Pose: standing upright in a three-quarter view turned toward the right: body and face turned about "
                 "45 degrees toward the right edge of the image, both eyes visible, both feet flat on the ground, "
                 "attentive kind expression, mouth closed."),
        "gesture": ("Still holding the small file in his other hand, he pushes his round brass-rimmed glasses up his "
                    "nose with the index finger of his near hand."),
        "idle_motion": ("He stands still holding the small file, relaxed and attentive: calm breathing, a natural "
                        "blink, a small nod, a quick glance down at the file and back up."),
        "notes": ("S64: works inside behind the open service window; default variant 'window' (bust cut at the sill, "
                  "no glass)."),
    },
}

# ----------------------------------------------------------------------------- prompts

LINEUP = (
    "Paint an age-progression character model sheet for a point-and-click adventure game. It shows ONE fictional "
    "person, {who}, {n} times side by side at {n} ages of {pos} life, from left to right in order of age, evenly "
    "spaced. Every figure is a full-body standing view from the top of the hair to the soles of the shoes, in the "
    "same three-quarter view turned toward the right: body and face turned about 45 degrees toward the right edge of "
    "the image, both eyes visible, arms relaxed, both feet flat on one common ground line. All figures are drawn at "
    "the same scale; the tallest figure fills about 80% of the image height. {child} It must be instantly obvious "
    "that all figures are the same person: the features that never change with age are {core} Keep exactly these "
    "features at every age; only the natural signs of age, the hairstyle and hair colour, a little weight and the "
    "clothes of the era change. {ages} No labels, no numbers, no text, no frames, no dividing lines, nothing on the "
    "ground."
)

IDENTITY_NOTE = (
    "The FIRST reference image shows our character at exactly this age, cut from the approved age-progression sheet "
    "of this person. Paint exactly this person: the same face (face shape, nose, eyes, eyebrows, ears, mouth), the "
    "same hair, build and clothes, as a new, larger and cleaner painting. "
)
CAST_SECOND = (
    "The SECOND reference image shows a different, already approved character from our game. Use it only as the "
    "reference for how characters are drawn and painted in this game: painting technique, soft outlines, body and "
    "head proportions, level of detail, lighting and colour palette. Do not copy his face, hair, clothes or bag. "
)
MIRA_SECOND = (
    "The SECOND reference image shows the same woman at 80, already approved for our game. Use it for the painting "
    "technique, the level of detail and the features that never change with age (face shape, nose, eyes, smile, "
    "glasses); her age, hair and clothes are those of the first image. "
)

FRAMING = ("The figure is centred and fills about 80% of the image height.")
PAINTERLY = ("Paint the face and the figure in the same painterly, semi-realistic way as the approved reference "
             "characters: natural-sized eyes, soft painted modelling and soft edges, no dark ink outlines, not a flat "
             "vector, anime or mobile-game look.")
FRAMING_SEATED = ("The seated figure with its seat is centred and fills about 70% of the image height.")


def sprite_rules(brief: dict) -> str:
    margin = ("The figure is a game sprite: the complete figure from the top of the hair to the soles of the shoes"
              + (" and the complete seat" if brief.get("staging") == "seated" else "")
              + " is visible, with green margin on every side; everything stands on the same invisible ground line. ")
    if brief.get("staging") == "seated":
        # 'head 1/6.5 of the height' read literally on a seated figure gives a small head on a long body (TONO v1/v2)
        rules = ("Slightly exaggerated cartoon proportions as in classic 1990s adventure games: the head is a little "
                 "large, about 1/6.5 of his standing height; because he is seated, the head is about one fifth of "
                 "the seated figure's height (from the top of the hair to the soles of the shoes), and thighs and "
                 "shins have normal, not elongated, length. " + ("A believable 12-year-old child." if brief.get("child")
                                                                else "A believable adult."))
        return margin + LIGHT + " " + rules
    return margin + LIGHT + " " + (CHILD_RULES if brief.get("child") else ADULT_RULES)


KEEP = ("Edit the first image: keep everything exactly the same (same character, same pose, same position and size "
        "in the frame, same clothes, same colours, same flat green background)")
FACE = {
    "blink": KEEP + " and change ONLY {pos} eyes: they are closed in a natural blink{glasses}. Do not move or redraw "
                    "anything else.",
    "talk": KEEP + " and change ONLY {pos} mouth and jaw: {subj} is in the middle of speaking, the mouth open as if "
                   "saying 'ah', the jaw lowered a little. {Pos} eyes, eyebrows, nose, hair and head position stay "
                   "exactly as they are. Do not move or redraw anything else.",
    "talk_oh": KEEP + " and change ONLY {pos} mouth: the lips form a small rounded 'oh' shape, as in mid-speech. {Pos} "
                      "eyes, eyebrows, nose, hair and head position stay exactly as they are. Do not move or redraw "
                      "anything else.",
}
GESTURE = (
    "Edit the first image: the same character, same face, same clothes, same colours, same scale, same flat green "
    "background, the same three-quarter view facing right, {anchor}. Change only the pose of the arms and hands: "
    "{gesture} Keep the head, the face, the hair, the body{legs} unchanged, and keep the whole figure inside the "
    "frame."
)
VARIANT = (
    "Edit the first image: keep everything exactly the same (same character, same face, same pose, same position and "
    "size in the frame, same clothes, same colours, same flat green background) and add only this: {change} Do not "
    "move or redraw the head, the face, the hair or the legs."
)
GUARD = ("Keep {pos} face, hair colour, skin tone and the soft even lighting exactly as in the first image: no "
         "dappled light spots or sun patches on {obj} or {pos} clothes.")
IDLE_SUFFIX = (
    " The character keeps the same position, facing and scale. Seamless loop. The camera is completely static. The "
    "background stays a perfectly flat uniform green, nothing else appears. Same hand-painted style throughout."
)

PRON = {"he": {"subj": "he", "pos": "his", "Pos": "His", "obj": "him"},
        "she": {"subj": "she", "pos": "her", "Pos": "Her", "obj": "her"}}

# JANA20 is a webcam portrait (S54): portrait on green, a home background plate and a laptop prop.
J20_PORTRAIT = (
    "{identity}Paint a head-and-shoulders portrait of {desc} She appears in a video call, seen by her laptop webcam: "
    "she sits at her desk at home and faces the camera, seen from the front with her head turned very slightly to the "
    "right, from just above the top of her head down to the middle of her chest; the bottom edge of the image cuts "
    "through her chest and upper arms. She is centred and her head fills about a third of the image height. Friendly, "
    "practical, attentive expression, looking into the camera, mouth closed. {light} Background: one perfectly flat, "
    "uniform, pure chroma-key green (#00FF00) behind her, edge to edge, no gradient, no shadow, no props, no text; "
    "crisp clean edges of her hair against the green, no green tint on her. "
)
J20_ROOM = (
    "The LAST reference image is a finished background painting from our game; use it only as the reference for the "
    "painting technique, brushwork and palette, do not copy its scene. Paint the background of a home video call in "
    "late October 2020, as seen by a laptop webcam behind a person sitting at a desk, but WITHOUT the person: an "
    "empty corner of a modest Bratislava flat at eye level of a seated person - a light wooden bookshelf with folders "
    "and a few books (no readable titles), a potted plant, a framed child's drawing on the wall, part of a window on "
    "the left with soft overcast late-autumn daylight, a warm desk lamp glow. Slightly soft focus like a webcam "
    "background. No people, no text, no logos. "
)
J20_ROOM_Q9C = (
    "Edit the first image: keep everything exactly the same (same room, same camera, same light, same style) and add "
    "only this: on the bookshelf and on a small side table, a neat stack of five or six old, used, refurbished "
    "laptops of different sizes and colours (no logos, no brands), each with a small white paper label with a "
    "handwritten number, and a small open box of screwdrivers. No people, no text except the tiny numbers."
)
LAPTOP = (
    "The LAST reference image is a finished background painting from our game; use it only as the reference for the "
    "painting technique, brushwork and palette, do not copy its scene. Paint a single prop for a point-and-click "
    "adventure game: an open, used laptop computer from about 2018 (dark grey, plain, no logo, no stickers, no text) "
    "standing on an invisible flat surface, seen from the front and slightly from the left at eye level of a standing "
    "person, the screen tilted back a little. The screen shows one uniform pure magenta (#FF00FF) colour filling the "
    "whole display area edge to edge inside a thin black bezel with a tiny webcam dot. The keyboard is visible in "
    "perspective. The laptop is centred and fills about 70% of the image width. Even soft warm light from the "
    "front-left, no cast shadow. Background: one perfectly flat, uniform, pure chroma-key green (#00FF00) filling "
    "the entire image edge to edge, no gradient, no shadow, no table, no text. "
)


# ----------------------------------------------------------------------------- budget and calls

def task_spend() -> float:
    if not fal_api.SPEND_LOG.exists():
        return 0.0
    with fal_api.SPEND_LOG.open(encoding="utf-8") as handle:
        return sum(float(row["usd"]) for row in csv.DictReader(handle)
                   if row["asset"].startswith(SCOPES) and row["timestamp"] >= TASK_SINCE)


def guard(asset: str, usd: float, budget: float) -> None:
    spent = task_spend()
    if spent + usd > budget + 1e-9:
        sys.exit(f"BUDGET: {asset}: {spent:.3f} + {usd:.3f} USD would exceed the {budget:.2f} USD task cap")
    print(f"[budget] {spent:.3f} spent of {budget:.2f}; this call {usd:.3f}", file=sys.stderr)


def image_call(args, model_key: str, prompt: str, refs: list[Path], aspect: str, resolution: str, asset: str,
               out_base: Path, style_ref: Path | None = None) -> list[Path]:
    model = chars.IMAGE_MODELS[model_key]
    price = fal_api.IMAGE_PRICES[(model, resolution)]
    guard(asset, price, args.budget)
    uris = chars.image_inputs(refs, None)
    if style_ref is not None:
        img = Image.open(style_ref).convert("RGB")
        uris.append(fal_api.image_data_uri(img, max_side=1376, fmt="JPEG"))
    arguments = {"prompt": prompt, "image_urls": uris, "aspect_ratio": aspect, "resolution": resolution,
                 "output_format": "png", "num_images": 1}
    if args.seed is not None:
        arguments["seed"] = args.seed
    out_base.parent.mkdir(parents=True, exist_ok=True)
    result = fal_api.run(model, arguments, asset, price, budget=None, timeout_s=600)
    meta = {"model": model, "usd": price, "prompt": prompt, "aspect_ratio": aspect, "resolution": resolution,
            "references": [str(r.relative_to(ART)) if r.is_relative_to(ART) else str(r) for r in refs],
            "style_reference": str(style_ref.relative_to(REPO)) if style_ref else None, "seed": args.seed}
    return chars.save_outputs(result, out_base, meta)


def key_bg() -> str:
    return chars.key_background("green")


def style() -> str:
    return chars.STYLE_FOR_CHARACTER + chars.STYLE_A


# ----------------------------------------------------------------------------- paid commands

def cmd_lineup(args) -> None:
    person = PEOPLE[args.person]
    n = len(person["ages"])
    words = position_words(n)
    ages = " ".join(f"{w}: {t}" for w, t in zip(words, person["lineup"]))
    body = LINEUP.format(who=person["who"], n=n, pos=PRON[person["pronoun"]]["pos"], child=person["child_note"],
                         core=person["core"], ages=ages)
    if args.person == "JANA":
        refs = [DANA_SHEET, chars.cast_reference(CAST_ANCHOR, "green", LIKE_ROOT / args.person)]
        note = ("The two reference images show two different, already approved characters from our game. Use them "
                "only as the reference for how characters are drawn and painted in this game: painting technique, "
                "soft painted edges, body and head proportions, level of detail, lighting and colour palette. Do not "
                "copy their faces, hair, clothes, face mask or bag. ")
    elif args.person == "MIRA":
        refs = [MIRA20_SHEET]
        note = ("The FIRST reference image is our approved character Mira at 80, painted in our game's style. The "
                "rightmost figure is exactly her; the younger figures are the same woman earlier in her life. Paint "
                "every figure in exactly the same technique as the reference. ")
    else:
        refs = [chars.cast_reference(CAST_ANCHOR, "green", LIKE_ROOT / args.person)]
        note = chars.CAST_REF_NOTE + " "
    prompt = " ".join([note + body, LIGHT, PAINTERLY, key_bg(), style()])
    name = args.out or "lineup"
    paths = image_call(args, "pro", prompt, refs, "16:9", "2K", f"characters/likeness/{args.person}/{name}",
                       LIKE_ROOT / args.person / name)
    print("\n".join(str(p) for p in paths))


def identity_ref(char_id: str) -> Path:
    """The person's lineup figure of this age, keyed and centred on a 3:4 green canvas."""
    brief = BRIEFS[char_id]
    person = PEOPLE[brief["person"]]
    index = person["ages"].index(char_id)
    src = LIKE_ROOT / brief["person"] / "split" / f"{index}_{char_id}.png"
    if not src.exists():
        sys.exit(f"missing {src}: run `split {brief['person']}` first")
    rgba = np.asarray(Image.open(src).convert("RGBA"))
    out = CHAR_ROOT / char_id / "identity_ref.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    fr.figure_on_canvas(rgba, (1536, 2048), 0.80, 0.90).save(out)
    return out


def cmd_base(args) -> None:
    brief = BRIEFS[args.char]
    ident = identity_ref(args.char)
    if brief["person"] == "MIRA":
        second, second_note = MIRA20_SHEET, MIRA_SECOND
    elif brief["person"] == "JANA":
        second, second_note = DANA_SHEET, CAST_SECOND.replace("his face, hair, clothes or bag",
                                                              "her face, hair, clothes or face mask")
    else:
        second, second_note = chars.cast_reference(CAST_ANCHOR, "green", CHAR_ROOT / args.char), CAST_SECOND
    if brief["staging"] == "screen":
        prompt = J20_PORTRAIT.format(identity=IDENTITY_NOTE + second_note, desc=brief["description"], light=LIGHT)
        prompt += PAINTERLY + " " + style()
        name = args.out or "portrait"
        paths = image_call(args, "pro", prompt, [ident, second], "16:9", "2K", f"characters/{args.char}/{name}",
                           CHAR_ROOT / args.char / name)
    else:
        framing = FRAMING_SEATED if brief["staging"] == "seated" else FRAMING
        if "image height" in brief.get("base_fix", ""):
            framing = ""
        prompt = " ".join([IDENTITY_NOTE + second_note, "Paint a single full-body character for a point-and-click "
                           "adventure game: " + brief["description"], brief["pose"], brief.get("base_fix", ""),
                           framing, sprite_rules(brief), PAINTERLY, key_bg(), style()])
        name = args.out or "sheet_3q"
        paths = image_call(args, "pro", prompt, [ident, second], "3:4", "2K", f"characters/{args.char}/{name}",
                           CHAR_ROOT / args.char / name)
    print("\n".join(str(p) for p in paths))


def cmd_edit(args) -> None:
    brief = BRIEFS[args.char]
    words = dict(PRON[brief["pronoun"]])
    words["glasses"] = " behind the glasses" if "glasses" in brief["description"] else ""
    seated = brief["staging"] == "seated"
    if args.kind in FACE:
        prompt = FACE[args.kind].format(**words)
        res = args.res or "1K"
    elif args.kind == "seat":
        prompt = ("Edit the first image: the same man, the same face, hair, clothes, colours and hand-painted style, "
                  "the same flat green background, the same three-quarter view facing right. Change only his "
                  "posture: " + brief["pose"].replace("Pose: he sits", "he now sits") + " Keep his head exactly "
                  "the same size as in the first image and keep his body proportions; seated, the figure is only "
                  "about three quarters of his standing height, so there is more green above his head. "
                  + brief.get("seat_extra", ""))
        res = args.res or "2K"
    elif args.kind in ("gesture", "variant_q9c", "variant_q9c_gesture"):
        text = brief.get(args.kind)
        if not text:
            sys.exit(f"{args.char} has no {args.kind}")
        if args.kind == "variant_q9c":
            prompt = VARIANT.format(change=text)
        else:
            if brief["staging"] == "screen":
                anchor, legs = "the same webcam framing, she stays seated at the same place", ""
            elif seated:
                anchor, legs = "sitting on the same seat in exactly the same place, the seat and the feet unchanged", \
                    ", the legs and the seat"
            else:
                anchor, legs = "standing on the same spot with the feet in exactly the same place", \
                    ", the legs and the feet"
            prompt = GESTURE.format(anchor=anchor, gesture=text, legs=legs)
        res = args.res or "2K"
    else:
        sys.exit(f"unknown edit kind {args.kind}")
    prompt = " ".join([prompt, GUARD.format(**words), key_bg(), style()])
    base = Path(args.base).resolve()
    aspect = args.aspect or ("16:9" if brief["staging"] == "screen" else "3:4")
    name = args.out or f"edit_{args.kind}"
    paths = image_call(args, "nb2", prompt, [base], aspect, res, f"characters/{args.char}/{name}",
                       CHAR_ROOT / args.char / name)
    print("\n".join(str(p) for p in paths))


def cmd_plate(args) -> None:
    """JANA20 home background plate (Pro) / its Q9C variant (NB2 edit) / the laptop prop (Pro)."""
    out_dir = CHAR_ROOT / "JANA20"
    if args.what == "room":
        paths = image_call(args, "pro", J20_ROOM + chars.STYLE_A, [], "16:9", "2K", "characters/JANA20/plate_room",
                           out_dir / "plate_room", style_ref=STYLE_PAINTING)
    elif args.what == "room_q9c":
        paths = image_call(args, "nb2", J20_ROOM_Q9C + " " + chars.STYLE_A, [out_dir / "plate_room.png"], "16:9",
                           "2K", "characters/JANA20/plate_room_q9c", out_dir / "plate_room_q9c")
    else:
        paths = image_call(args, "pro", LAPTOP + chars.STYLE_A, [], "1:1", "2K", "characters/JANA20/laptop",
                           out_dir / "laptop", style_ref=STYLE_PAINTING)
    print("\n".join(str(p) for p in paths))


def cmd_video(args) -> None:
    brief = BRIEFS[args.char]
    if args.pro:
        endpoint, resolution = "fal-ai/minimax/hailuo-02/pro/image-to-video", "1080P"
    else:
        endpoint, resolution = "fal-ai/minimax/hailuo-02/standard/image-to-video", "768P"
    suffix = IDLE_SUFFIX
    if brief["staging"] == "screen":
        suffix = suffix.replace("The background stays a perfectly flat uniform green, nothing else appears.",
                                "The background stays a perfectly flat uniform green, nothing else appears; the "
                                "bottom edge of the frame keeps cutting through her chest.")
    prompt = (args.prompt or brief["idle_motion"]) + suffix
    image_uri = fal_api.image_data_uri(Path(args.image), fmt="PNG")
    arguments = {"prompt": prompt, "image_url": image_uri, "end_image_url": image_uri, "prompt_optimizer": False}
    if not args.pro:
        arguments.update(duration="6", resolution=resolution)
    price = fal_api.video_price(endpoint, 6.0, resolution)
    name = args.out or ("video_idle_pro" if args.pro else "video_idle")
    asset = f"characters/{args.char}/{name}"
    guard(asset, price, args.budget)
    result = fal_api.run(endpoint, arguments, asset, price, budget=None, timeout_s=1800, poll_s=8)
    meta = {"model": endpoint, "usd": round(price, 4), "prompt": prompt, "input": Path(args.image).name,
            "tail_image": True, "seconds": 6.0, "resolution": resolution,
            "arguments": {k: v for k, v in arguments.items() if not str(v).startswith("data:")}}
    paths = chars.save_outputs(result, CHAR_ROOT / args.char / name, meta)
    print("\n".join(str(p) for p in paths))


# ----------------------------------------------------------------------------- free: split, briefs

def remove_ground_line(rgba: np.ndarray) -> np.ndarray:
    """Erase a painted ground line (thin, very wide horizontal stroke) outside the figures."""
    out = rgba.copy()
    a = out[..., 3] > 24
    h, w = a.shape
    wide = np.flatnonzero(a.sum(axis=1) > 0.45 * w)
    rows = sorted({min(h - 1, max(0, y + dy)) for y in wide for dy in range(-3, 4)})
    if not rows:
        return out
    y_top, y_bot = max(0, rows[0] - 4), min(h - 1, rows[-1] + 4)
    inside = a[y_top] & a[y_bot]  # columns where a figure (boot) continues through the line
    for yy in rows:
        out[yy, ~inside, 3] = 0
    return out


def cmd_split(args) -> None:
    person = PEOPLE[args.person]
    src = LIKE_ROOT / args.person / (args.src or "lineup.png")
    keyed = remove_ground_line(fr.chroma_key(fr.load_rgb(src)))
    views = fr.split_views(keyed, len(person["ages"]))
    out_dir = LIKE_ROOT / args.person / "split"
    out_dir.mkdir(parents=True, exist_ok=True)
    for i, (char_id, rgba) in enumerate(zip(person["ages"], views)):
        dst = out_dir / f"{i}_{char_id}.png"
        fr.save_rgba(rgba, dst)
        print(dst.name, rgba.shape[1::-1], fr.key_quality(rgba))


def cmd_briefs(args) -> None:
    """Add/refresh this task's entries in art/characters/characters.json (re-read right before writing)."""
    path = CHAR_ROOT / "characters.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    game = {c["id"]: c for c in json.loads((REPO / "src" / "game" / "data" / "game.json").read_text(
        encoding="utf-8"))["characters"]}
    for char_id in IDS:
        b = BRIEFS[char_id]
        person = PEOPLE[b["person"]]
        entry = {k: v for k, v in b.items() if k not in ("person",)}
        entry["likeness_group"] = b["person"]
        entry["likeness_core"] = person["core"]
        entry["key"] = "green"
        entry["design_sk"] = game[char_id]["design"]
        data[char_id] = entry
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print("characters.json:", ", ".join(IDS))


# ----------------------------------------------------------------------------- CLI

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--budget", type=float, default=TASK_BUDGET)
    parser.add_argument("--seed", type=int, default=1970)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("lineup")
    p.add_argument("person", choices=PEOPLE)
    p.add_argument("--out")
    p.set_defaults(func=cmd_lineup)
    p = sub.add_parser("split")
    p.add_argument("person", choices=PEOPLE)
    p.add_argument("--src")
    p.set_defaults(func=cmd_split)
    p = sub.add_parser("base")
    p.add_argument("char", choices=IDS)
    p.add_argument("--out")
    p.set_defaults(func=cmd_base)
    p = sub.add_parser("edit")
    p.add_argument("char", choices=IDS)
    p.add_argument("kind")
    p.add_argument("--base", required=True)
    p.add_argument("--res")
    p.add_argument("--aspect")
    p.add_argument("--out")
    p.set_defaults(func=cmd_edit)
    p = sub.add_parser("plate")
    p.add_argument("what", choices=["room", "room_q9c", "laptop"])
    p.set_defaults(func=cmd_plate)
    p = sub.add_parser("video")
    p.add_argument("char", choices=IDS)
    p.add_argument("--image", required=True)
    p.add_argument("--pro", action="store_true")
    p.add_argument("--prompt")
    p.add_argument("--out")
    p.set_defaults(func=cmd_video)
    p = sub.add_parser("briefs")
    p.set_defaults(func=cmd_briefs)
    p = sub.add_parser("spend")
    p.set_defaults(func=lambda a: print(f"task spend {task_spend():.3f} USD of {a.budget:.2f}"))
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
