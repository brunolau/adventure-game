"""Shot specs for art/tools/cutscenes.py: one entry per cutscene beat (<CS>_<n>) and epilogue shot (EPILOGUE_<n>).

Each shot: refs = [(reference spec, role sentence)], shot = what the frame shows (English, from game.json
cutscenes[].beats[].shot / epilogue[].shot), characters = ids whose approved brief is appended, light = time and
light, camera = optional pan/zoom (visible 16:9 source rects [x, y, w, h] in the 1920x1080 frame, at the start and
at the end of the beat). Reference specs: char:ID, item:ID, bg:ROOM, photo:ROOM/file, frame:SHOT (an exported
frame of another shot), crop:<path>@x0,y0,x1,y1, style:<art/backgrounds name>, or a repo path.
"""

ADAM = ("char:ADAM", "character reference: our hero Adam (front and side view)")


def char(cid: str, who: str) -> tuple[str, str]:
    return (f"char:{cid}", f"character reference: {who}")


STYLE_INTERIOR = ("bg:S10", "a finished interior painting from our game; use it only for the painting technique, "
                  "brushwork, palette and line quality, not for its content")
STYLE_EXTERIOR = ("bg:S07", "a finished exterior painting from our game; use it only for the painting technique, "
                  "brushwork, palette and line quality, not for its content")

SHOTS: dict[str, dict] = {}


def shot(shot_id: str, **spec) -> None:
    spec["id"] = shot_id
    SHOTS[shot_id] = spec


# ----------------------------------------------------------------------------------------------- CS01 (G11, S10 2020)
shot("CS01_1",
     refs=[("bg:S10", "place reference: the ZVON workshop (our painting of room S10, autumn 2020), seen out of focus "
                      "behind the phone"),
           ("crop:src/game/assets/bg/S06.webp@135,165,240,245",
            "the old family photograph that hangs in grandmother Mira's house: grandmother Mira and the boy Adam at "
            "the sea, with a slightly crooked horizon"),
           ("item:PHONE", "prop reference: Adam's smartphone"),
           ADAM],
     shot=("Extreme close-up over Adam's shoulder: his hand (blue work-jacket cuff) holds his smartphone in the dim "
           "workshop. The phone screen fills the centre of the frame and shows a photo preview of the old family "
           "photograph (image 2): the white-haired grandmother and the small boy at the sea, crooked horizon. Below each "
           "of the two people there is a tiny name tag drawn as a short blank white label. Something is wrong: the "
           "grandmother's figure and her label are smearing and flaking away like wet paint running down and chips of "
           "paint missing, revealing blank grey, while the boy and his label stay perfectly crisp. The screen glow lights "
           "his fingers; behind, out of focus, the workbench and the cold blue glow of the round brass ring on the wall."),
     light="Late afternoon in October, warm low sunbeams through the small window mixed with the cold blue glow of the ring; shallow depth of field.",
     characters=[])

shot("CS01_2",
     refs=[("bg:S10", "place reference: the ZVON workshop, room S10 of our game; keep its walls, shelf, workbench, "
                      "the round brass-framed ring on the wall, the small window and the floor"),
           ADAM,
           ("item:TOOLS", "prop reference: Adam's brown leather messenger bag")],
     shot=("Medium-wide, slightly low camera in the ZVON workshop. The round brass-framed ring on the wall lights up "
           "with soft, bright milky-white light that floods the room, throwing long shadows across the plank floor. "
           "Adam stands in front of it in three-quarter view, a step back, his face lit, one hand half raised against "
           "the glow, more puzzled than afraid. Adam and his messenger bag both carry a thin, brief glowing brass-gold "
           "outline, like a rim of light tracing his silhouette and the bag. Dust motes float in the light."),
     light="The workshop is dim; the ring's soft white light is the key light, a warm brass-gold rim on Adam and the bag.",
     characters=["ADAM"])

shot("CS01_3",
     refs=[("bg:S11", "place reference: the Dubravka tram stop in June 1995 (room S11 of our game); keep the shelter, the "
                      "platform, the clock post, the railing and the tracks"),
           ("photo:S11/period-tram-t6a5-red-cream_felix-o-1993.jpg", "vehicle reference: the period red-and-cream tram"),
           ADAM],
     shot=("Wide shot of the 1995 tram stop. A red-and-cream tram (no line number, no advertising) is pulling away to "
           "the right, its rear end just leaving the frame, and reveals Adam standing alone on the platform where it "
           "stood: in his blue work jacket with his bag, turned to look after the tram, bewildered. Behind him the "
           "shelter, the paper timetable and the clock on its post. People of 1995 are absent; it is quiet. The tram's "
           "motion is suggested by a slight blur and a gust that lifts a few leaves and a paper ticket."),
     light="Warm June late-afternoon sun, long soft shadows; the edges of the frame slightly darker, as if just faded in from black.",
     characters=["ADAM"])

# ----------------------------------------------------------------------------------------------- CS02 (B12, S16 1995)
shot("CS02_1",
     refs=[("photo:S16/tesla_sp210_cassette_deck.jpg", "prop reference: a period 1990s cassette deck mechanism (repaint it "
                                                       "unbranded, no logo)"),
           ("photo:S16/tesla_audio_mixer_olomouc.jpg", "prop reference: the school radio mixing desk and microphone"),
           ("item:TAPE", "prop reference: the school cassette"),
           ("item:PHONE", "prop reference: Adam's smartphone"),
           STYLE_INTERIOR],
     shot=("Close-up detail in the small school radio room in June 1995: a silver-and-black cassette deck on the radio "
           "desk, its cassette window in the centre of the frame; behind the window the cream-labelled cassette's two "
           "reels turn calmly. The deck's red record button is NOT pressed, only play. Beside the deck on the desk lies "
           "Adam's modern smartphone; its screen shows a soft blue audio waveform. Next to the phone a sheet of lined "
           "paper with a neat handwritten transcript (the writing is small and not readable at this distance). A "
           "microphone on a stand and the mixing desk are soft in the background."),
     light="Warm afternoon sunlight from a window at the left, dust motes in the beam, shallow depth of field on the turning reels.",
     characters=[])

shot("CS02_2",
     refs=[("photo:S16/small_room_window_brno_reckovice.jpg", "place reference: a small school room with a window, for "
                                                              "the room's shape and the window (no computer in our 1995 room)"),
           ("photo:S17/walled-courtyard-sokolikova_carl-eric-2012_NC.jpg", "place reference: the real school yard of ZS "
                                                                          "Sokolikova seen through the window"),
           ("photo:S16/tesla_audio_mixer_olomouc.jpg", "prop reference: the school radio mixing desk"),
           ADAM, STYLE_INTERIOR],
     shot=("Medium shot inside the small school radio room in 1995: adult Adam stands silently by the radio desk with "
           "the cassette deck, three-quarter view, one hand rubbing the back of his neck, eyes lowered, moved and "
           "quiet. Behind him a window looks down onto the school yard; far away in the yard, small and distant, a "
           "10-year-old boy with short dark hair in a yellow T-shirt and shorts makes exactly the same gesture, his hand "
           "on the back of his neck, not looking up. The boy is tiny in the frame and only a background detail."),
     light="Warm June afternoon light through the window, the room in soft shade, the yard outside bright.",
     characters=["ADAM"])

# ----------------------------------------------------------------------------------------------- CS03 (B22, S30 1995)
shot("CS03_1",
     refs=[("photo:S30/tyrsovo-nabrezie_path_railing_castle-view_2008.jpg", "place reference: the real Danube "
                                                                            "embankment path and railing in Bratislava"),
           ("photo:S30/petrzalka-bank_view-across-danube_2008.jpg", "place reference: the view across the Danube"),
           ("item:CHRONO", "prop reference: the brass ZVON chronometer with its mechanical digit counter and four lights"),
           ADAM, STYLE_EXTERIOR],
     shot=("Close-up: Adam's hand holds the brass chronometer in the foreground, filling the left-centre of the frame; "
           "its mechanical digit counter has just clicked over and reads exactly 1962, the four small lights glowing "
           "softly. Behind it, slightly out of focus, a small wooden riverside service shelter with a mechanical coil "
           "on a stand that is slowing to a stop, a paper map pinned inside the shelter with two places circled; "
           "beyond the railing the wide Danube and the far bank of Bratislava in 1995."),
     light="Golden evening sun low over the river, glints on the water and on the brass.",
     characters=[])

shot("CS03_2",
     refs=[("item:REGISTERED", "prop reference for paper and ink in our style"),
           ("photo:S14/classroom_green_board_brno_reckovice.jpg", "place reference: a school classroom, seen only out "
                                                                  "of focus behind the book"),
           STYLE_INTERIOR],
     shot=("Low, grazing close-up of an old school class register lying open on a wooden teacher's desk in 1995, seen "
           "from a low angle across the page so that the writing is foreshortened and cannot be read: a ruled grid of "
           "rows filled with tiny dark-blue ink scribbles (abstract wavy pen strokes, NOT letters, no words, no headings, "
           "no numbers). Exactly ONE row in the middle of the page has just gone empty: its ink is lifting off the paper "
           "as a few faint cold-blue sparks and wisps, leaving a clean blank line, while every other row stays full of "
           "dark ink. A pen lies beside the book. The classroom behind is soft, empty and out of focus."),
     light="Quiet afternoon light, a cold blue glimmer on the blank line as the only unusual light.",
     characters=[])

# ----------------------------------------------------------------------------------------------- CS04 (I17, S40 era 1960, shown as June 1962)
shot("CS04_1",
     refs=[("photo:S40/type_ref_attic_skanzen_doubrava_lipova.jpg", "place reference: a safe wooden attic with a "
                                                                   "plank floor and beams"),
           ("photo:S40/type_ref_attic_cluttered_krovkrov.jpg", "place reference: attic beams and roof light"),
           char("MIRA60", "Mira at 22, in June 1962"),
           ADAM,
           ("item:ORIGIN", "prop reference: the paper imprint with the four symbols that Adam keeps"),
           STYLE_INTERIOR],
     shot=("Medium shot in the archive attic above a workshop in June 1962: young Mira (22, round glasses, ochre "
           "blouse) kneels at a dented grey-green metal archive box with brass corners on a small table and closes its "
           "lid with both hands, decided and calm. Adam stands beside her, slightly behind, holding a sheet of waxed paper "
           "with a pale relief imprint of four simple symbols (circle, cross, square, triangle) against his chest. "
           "An old trunk, wax paper rolls and roof beams around them."),
     light="A shaft of warm dusty sunlight from a small roof window falls across the box and Mira's hands.",
     characters=["MIRA60", "ADAM"])

shot("CS04_2",
     refs=[("frame:CS04_1", "the metal archive box from the previous frame: paint exactly this box in all three panels"),
           ("bg:S03", "place reference for the right panel: the volunteer point in autumn 2020 (our painting)"),
           STYLE_INTERIOR],
     shot=("A short visual montage in ONE image: a horizontal triptych of three tall panels side by side, separated by "
           "thin dark gutters, each showing the same grey-green metal archive box with brass corners from the same angle. "
           "Left panel: the box on a home shelf in a private archive of the 1960s, between folders and a desk lamp. "
           "Middle panel: the box on a metal shelf of a school archive in 1995, with a handwritten index card tucked "
           "under its handle. Right panel: the box packed in a blue plastic crate at a volunteer pick-up point in 2020, "
           "with a pump bottle of hand sanitizer and a stack of paper lists beside it. Three different hands rest on "
           "the box in the three panels: a young woman's hand, an older woman's hand, a man's hand."),
     light="Each panel in the light of its era: warm lamp light, afternoon school light, cool autumn daylight.",
     characters=[])

# ----------------------------------------------------------------------------------------------- CS05 (C05, S10 2020)
shot("CS05_1",
     refs=[("bg:S10", "place reference: the ZVON workshop, room S10 of our game (the workbench, the shelf, the round "
                      "brass ring on the wall)"),
           ("item:CHRONO", "prop reference: the portable brass chronometer: pocket-watch shaped, a hinged lid with a bell "
                           "emblem, a mechanical four-digit counter and four small coloured lights; it is NOT a clock "
                           "and has no clock face or hands"),
           ("item:TAPE", "prop reference: the school cassette"),
           ("crop:src/game/assets/bg/S06.webp@135,165,240,245", "the family photograph of grandmother Mira and the boy")],
     shot=("Close shot on the workbench of the ZVON workshop at evening: the open brass chronometer (image 2) lies in "
           "the middle of a low wooden cradle wired to the bench; around it lie the three records it reads - the "
           "cassette, a cardboard folder with a pale paper imprint of four symbols (circle, cross, square, triangle), "
           "and a paper form on a small clipboard - each glowing with the same soft, even golden light that does not "
           "consume them. Leaning against the cradle stands the small framed family photograph (image 4): the "
           "grandmother's figure in it is solid and coloured again, her face fully painted, but a few tiny specks "
           "along her outline are still blank, just slightly incomplete; the boy next to her is crisp. No numbers, "
           "no labels, no captions, no text on anything."),
     light="Warm workshop lamp light and the soft light of the records; October evening outside the small window.",
     characters=[])

shot("CS05_2",
     refs=[("bg:S10", "place reference: the ZVON workshop, room S10 of our game"),
           ADAM,
           ("item:TOOLS", "prop reference: Adam's brown leather messenger bag"),
           ("item:CHRONO", "prop reference: the brass chronometer with its digit counter")],
     shot=("Close-up on the workbench: Adam's hands (blue jacket cuffs) close the flap of his brown leather messenger "
           "bag and fasten the buckle. Next to the bag lies the brass chronometer; its mechanical digit counter shows "
           "2035 and one small new light on it is glowing. The workshop and the round brass ring are soft behind."),
     light="Warm evening lamp light, a little cool blue from the ring in the background.",
     characters=[])

# ----------------------------------------------------------------------------------------------- CS06 (F11, S49 2035)
CHAMBER = ("A fictional, modest interior of a temporary exhibition pavilion on the Chopok summit in June 2035: light "
           "wooden wall panels, a plain work table, a wall console with exactly four port slots in a row (each marked "
           "only by a small engraved symbol: circle, cross, square, triangle; no text labels) and a large switch, a "
           "small dark screen, a small amber emergency lamp. Through a wide window, about fifty metres away across the "
           "bare stony summit plateau, the real Rotunda building as in the summit photos: a squat round tower with a "
           "stone-clad base, a ring of tall dark glass windows under a bright red band and a flat cone roof, joined to "
           "long low dark-blue angular cable-car station buildings; low rounded Tatra ridges behind. It is a modern "
           "building, not a chapel or a castle; paint no sculpture on its roof and no lettering on it. Not science "
           "fiction: ordinary near-future technology.")

shot("CS06_1",
     refs=[("photo:S48/chopok-summit_plateau-rotunda-from-east_2016-09.jpg", "place reference: the real Rotunda and "
                                                                             "the cable-car stations on the Chopok summit plateau, the view from our pavilion's window"),
           ("photo:S48/rotunda-chopok_exterior_2016-09.jpg", "place reference: the real Rotunda close up (its shape and "
                                                             "materials only; do not paint its lettering)"),
           char("VIKTOR", "Viktor, 50"),
           ("item:READER", "prop reference: the handheld audio reader: a small cream-and-wood device with a teal screen "
                           "showing a waveform, teal buttons and a round speaker grille"),
           STYLE_INTERIOR],
     shot=(CHAMBER + " Close shot: Viktor sits at the table, leaning forward on his forearms, listening to the round "
           "speaker of the handheld audio reader (image 4) lying in front of him. His face is restrained, eyes wet but composed; he "
           "has not slept. A full glass of water stands untouched beside the reader. Behind him through the window the "
           "Rotunda on the ridge. No hospital, no illness, nothing dramatic - only a man listening to a voice."),
     light="Cool early-morning mountain light from the window, warm small desk lamp on his hands and the reader.",
     characters=["VIKTOR"])

shot("CS06_2",
     refs=[("frame:CS06_1", "the same room from the previous frame (keep the table, window, console and light)"),
           char("VIKTOR", "Viktor, 50"),
           ADAM,
           ("frame:CS09_1", "Adam as already painted in another cutscene of the game: copy his face and hair from here")],
     shot=(CHAMBER + " Medium-wide shot of the same room as image 1, a little later: Viktor has got up from the table "
           "and now STANDS at the wall console on the left side of the room, seen in three-quarter view from behind and "
           "the side, his right hand on the large lever switch, pulling it down; the small screen and the indicator "
           "lights of the console go dark. The handheld reader lies on the table, abandoned, the glass of water beside "
           "it still full. Adam stands on the right by the window, a few steps away, hands at rest, not interfering, "
           "giving him silence. Each person has exactly two arms; nobody sits at the table now."),
     light="Cool morning light from the window; the console lights dying out.",
     characters=["VIKTOR", "ADAM"])

# ----------------------------------------------------------------------------------------------- CS07 (F17, S49 -> S06)
shot("CS07_1",
     refs=[("frame:CS06_2", "the chronochamber as painted in the previous frames: the light wooden wall panels, the steel "
                            "console plate on the left wall with the four engraved symbols (circle, cross, square, "
                            "triangle) and the rocker switch, the amber lamp; paint exactly this console"),
           ("item:TAPE", "prop reference: the school cassette"),
           ("item:ORIGIN", "prop reference: the imprint folder with the four symbols"),
           ("item:HANDOVER", "prop reference: the handover form"),
           ("item:TOOLS", "prop reference: Adam's brown leather messenger bag"),
           ADAM],
     shot=("Close-up on the steel console plate on the light wooden wall of the chronochamber (image 1): directly under "
           "each of its four engraved symbols there is now one slim port slot with a small round indicator light, and "
           "all four lights have just turned a calm, steady soft white. From the slots small shallow metal trays have "
           "slid out, and Adam's hand (blue work-jacket cuff) takes the evidence back - the cassette, the imprint folder "
           "and the handover form - into his open brown leather messenger bag, held just below the plate. Above the "
           "plate a small dark screen shows one short glowing line that is breaking up into fading specks of light "
           "(no letters, no words). Through the edge of the window, soft daylight. Paint no text, no labels, no "
           "computer monitor and no other device."),
     light="Soft calm white light from the four ports, cool daylight from the window.",
     characters=[])

shot("CS07_2",
     refs=[("frame:CS06_1", "the chronochamber from the previous frames (keep the table, window and light)"),
           char("VIKTOR", "Viktor, 50"),
           char("NINA", "Nina, 30, who appears on a small video screen")],
     shot=("Medium close shot: Viktor sits at the plain table and signs a printed incident report with a pen, "
           "unhurried, serious, alone. On the table a small tablet stands on a stand, showing Nina on a video call, "
           "watching him, matter-of-fact. The glass of water. No crowd, no applause."),
     light="Bright mountain daylight from the window now, calmer and clearer than before.",
     characters=["VIKTOR", "NINA"])

shot("CS07_3",
     refs=[("bg:S06", "place reference: the side path under grandmother Mira's closed window (room S06 of our game); "
                      "keep the house wall, the three windows, the hanging geranium, the vine, the fence"),
           char("MIRA20", "grandmother Mira, 80, behind the window glass"),
           ADAM,
           ("crop:src/game/assets/bg/S06.webp@135,165,240,245", "the family photograph hanging inside")],
     shot=("Medium shot outside Mira's house: Adam stands on the paved side path close to the big closed window, his "
           "phone at his ear, smiling tiredly. Behind the closed window glass, inside, Mira (white hair, round glasses, "
           "ochre sweater) holds her phone to her ear and smiles back, the glass reflecting a little of the garden. In "
           "the upper pane of the window the framed family photograph hangs inside, complete and clear, including its "
           "crooked horizon. The window stays closed; there is glass between them."),
     light="Golden October evening light, long soft shadows, falling leaves.",
     characters=["ADAM", "MIRA20"])

shot("CS07_4",
     refs=[("bg:S06", "place reference: the side path, the window and the garden (room S06 of our game); keep this "
                      "exact house: salmon-pink plaster wall, red tile roof edge, three white-framed windows with lace "
                      "curtains, the hanging red geranium, the drainpipe, the vine on its wooden frame and the green picket fence"),
           ("frame:CS07_3", "the previous frame of this cutscene: the same house, Adam and Mira as already painted; "
                            "keep their faces, hair and clothes exactly"),
           char("MIRA20", "grandmother Mira, 80"),
           ADAM],
     shot=("Wider, calm shot of the same place a little later, the camera further back and slightly to the right so the "
           "whole house wall and the garden beyond the green fence are in view. Adam (exactly as in image 2: short dark "
           "brown hair, blue work jacket, mustard T-shirt) sits on a simple wooden bench placed on the paved path "
           "against the wall below the big middle window, outside, relaxed for the first time, his bag beside him. "
           "Inside, behind the closed glass of the big window, Mira sits on a chair close to the window, facing him "
           "through the glass. Both hold their phones in their laps. The glass remains between them. The vine with "
           "grapes and the tree in golden leaves on the right."),
     light="Late golden hour turning to dusk, a warm lamp lit inside the room.",
     characters=["ADAM", "MIRA20"])

shot("CS07_5",
     refs=[("bg:S05", "place reference: grandmother Mira's garden gate (room S05 of our game), its brick gate post, "
                      "the wooden gate, the fence and the house behind")],
     shot=("A quiet closing image at dusk: a close view of the brick gate post of Mira's garden with an ordinary old "
           "doorbell button in a small metal plate, placed in the right third of the frame; behind it, soft and out of "
           "focus, the garden, the fence and the house with one warm lit window. The left and middle of the frame are "
           "calm and dark-ish (evening sky and soft garden) so a title can be laid over them. No people."),
     light="Blue dusk with the last warm glow on the horizon; the lit window and a faint warm light on the bell button.",
     characters=[])

# ----------------------------------------------------------------------------------------------- CS08 (E10, school yard)
shot("CS08_1",
     refs=[("photo:S17/walled-courtyard-sokolikova_carl-eric-2012_NC.jpg", "place reference: the real walled school "
                                                                          "yard of ZS Sokolikova in Bratislava-Dubravka"),
           ("item:PHOTO2020", "prop reference: the phone screenshot of the yard before the change: bare asphalt"),
           ("item:PHONE", "prop reference: Adam's smartphone"),
           STYLE_EXTERIOR],
     shot=("The same school yard from the same fixed camera in three times, in ONE wide image that changes seamlessly "
           "from left to right like a time-lapse panorama (soft vertical transitions, no hard borders): on the left "
           "early December 1982 - thin snow, bare branches, a thin young linden sapling protected by a fresh square "
           "enclosure of wooden laths, a new low red-brick wall beside it; in the middle June 1995 - the linden has a "
           "young green crown, children's chalk on the ground; on the right autumn 2020 - a big mature linden with a "
           "wide golden crown shading a bench and the old low brick wall, with green grass where asphalt used to be. "
           "In the lower right corner Adam's hand holds his phone; its screen shows the old screenshot of the same "
           "corner as bare hot asphalt without a tree."),
     light="Each part in the light of its season: cold white December, warm June, golden October; the light blends across the image.",
     characters=[])

shot("CS08_2",
     refs=[("crop:src/game/assets/cutscenes/CS08_1.webp@1150,0,1920,1080", "the school yard in autumn 2020 from the previous "
                                                                        "frame: the big linden, the bench and the old wall"),
           ("photo:S17/walled-courtyard-sokolikova_carl-eric-2012_NC.jpg", "place reference: the real school yard"),
           STYLE_EXTERIOR],
     shot=("Close detail at the foot of the big linden in autumn 2020: the preserved low wall of old red bricks, worn and "
           "mossy, golden linden leaves lying on its top; in the second row from the top, third brick from the left, "
           "one stone is a slightly different colour, a small cover that closes a dry cavity. The thick trunk and its "
           "roots rise at the edge of the frame; the yard is soft behind: grass, the bench and the old yard wall in autumn "
           "2020. No snow anywhere, no wooden lath fence, no sapling: this is only the autumn of 2020."),
     light="Golden late-afternoon light filtering through the leaves, dappled on the bricks.",
     characters=[])

# ----------------------------------------------------------------------------------------------- CS09 (J02, Jasna 2035)
shot("CS09_1",
     # Jasna 2035 is in winter (owner 2026-10-06) and S41 was repainted from the owner's friend's photos: the view
     # through the windows is the new winter S41 seen from the departing cabin (art/tools/frame_reconcile.py, v6).
     refs=[("src/game/assets/bg_natural/S41.webp", "place reference: our finished painting of the valley station at "
                                                   "Biela Put in winter (room S41), seen from the road; the cabin has "
                                                   "just left exactly this place"),
           ("src/game/assets/ambient/S41/natural/cabin_winter.webp", "the line's cabins: rounded, orange-red, "
                                                                     "unbranded, a dark window band, snow on the roof"),
           ADAM,
           ("frame:CS02_2", "Adam as already painted in another cutscene of the game: copy his face, short dark brown "
                            "hair and build from here (not this room)"),
           ("src/game/assets/actors/ADAM/idle_front_coat1982.webp", "Adam's winter outfit: dark charcoal wool coat, "
                                                                    "mustard knitted scarf, brown messenger bag"),
           ("item:LIFT_TICKET", "prop reference: the lift ticket"),
           STYLE_EXTERIOR],
     shot=("Inside a small modern eight-seat gondola cabin of the Biela Put - Priehyba cable car on 6 February 2035, just "
           "after the doors have closed: Adam in his winter coat and mustard scarf sits by the window, holding his paper "
           "lift ticket, looking out. Through the large cabin windows we look down and back onto the valley station of "
           "image 1 in deep snow: Hotel Posta (a steep timber A-frame chalet with two wooden balconies and its lower "
           "cream-coloured wing with three chimneys), the ploughed road with the grey stone-clad retaining wall, in the "
           "wall's gap the dark card-reader pillar with its green light next to the stainless turnstile with glass "
           "wings, the arched wooden footbridge with its X-lattice railing over the dark stream, the curved dark-glass "
           "rope housing with its orange band and an orange-red cabin parked in it, the low white hall with an orange "
           "stripe, the station's wooden fence, the light-grey steel tube pylon with its ladder close outside, and one "
           "more orange-red cabin with snow on its roof coming down on the other rope. Above the door inside the cabin "
           "a small plain plate reads exactly: BIELA PÚŤ – PRIEHYBA. No other lettering, no signposts, no logos, no "
           "brand names. No reflections of Adam in the glass. Adam's face is our approved painted hero: a normal "
           "adult face, not a caricature. The character brief below describes his everyday clothes; in this winter "
           "frame he wears the coat and scarf of image 5 over them."),
     light="Clear cold February day in the mountains: deep blue sky, low sun, crisp blue shadows on the snow, frost "
           "rims on the cabin windows, warm sunlight on the cabin floor.",
     characters=["ADAM"])

shot("CS09_2",
     refs=[("photo:S67/priehyba_funitel-boarding-hall_2015.jpg", "place reference: the real Priehyba transfer station "
                                                                 "boarding hall with the large funitel cabins"),
           ("photo:S67/priehyba_funitel-station-exterior_2015.jpg", "place reference: the Priehyba station exterior"),
           ADAM, STYLE_EXTERIOR],
     shot=("Adam steps out of the small gondola onto the platform of the Priehyba transfer station, seen from behind at "
           "three-quarter view. Ahead of him, in the station hall, a large clear wayfinding sign with an arrow reads "
           "exactly: FUNITEL PRIEHYBA – CHOPOK; under it the big wide funitel cabins wait at the boarding platform. "
           "Steel structure, rope wheels overhead, mountain light through the open side. No logos, no brand names, "
           "no other text."),
     light="Bright mountain daylight from the open side of the hall, cool shade inside.",
     characters=["ADAM"])

# ----------------------------------------------------------------------------------------------- EPILOGUE (Q1-Q9)
shot("EPILOGUE_1", kind="epilogue",
     refs=[("bg:S02", "place reference: the residential street of our game (room S02, autumn 2020)"),
           char("LENKA", "Lenka and her dog Bodka (the white dog with black spots)"),
           ("item:BALL", "prop reference: the chewed red ball")],
     shot=("Low, close shot on the pavement of the street: Bodka, the white short-haired dog with her black spots, lies "
           "contentedly on the warm pavement with the chewed red ball between her front paws, chin on the ball, tail "
           "mid-wag. Beside her stand Lenka's legs in jeans and brown ankle boots, the leash slack, and Lenka bends a "
           "little, smiling above her blue face mask. Fallen leaves."),
     light="Warm golden October afternoon sun, long soft shadows.",
     characters=["LENKA"])

shot("EPILOGUE_2", kind="epilogue",
     refs=[("bg:S07", "place reference: the stop shelter and the community notice board at Cierna Voda (room S07)"),
           char("JOZEF", "Jozef, 73")],
     shot=("Medium shot at the wooden community notice board by the stop shelter: Jozef (long brown overcoat, blue "
           "face mask) points with his unfolded pocket magnifier at a big new notice pinned in the middle of the board: "
           "a white sheet with exactly two lines in huge bold black capitals, 'SUSEDSKÁ POMOC' and below it "
           "'9.00 – 17.00', and nothing else on it (the other small notes on the board only have unreadable squiggles) - and "
           "reads it aloud to an elderly neighbour beside him: a small woman in a beige coat and a headscarf, also "
           "masked, leaning in and nodding. Autumn trees behind."),
     light="Soft warm autumn afternoon light.",
     characters=["JOZEF"])

GALLERY = ("The 2035 Atlas exhibition gallery inside the real Rotunda building on the Chopok summit: a round room with "
           "big panoramic windows onto the mountains, temporary white gallery panels with framed works and soft spotlights.")

shot("EPILOGUE_3", kind="epilogue",
     refs=[("photo:S47/rotunda-chopok_interior-lounge_2016-09.jpg", "place reference: the real Rotunda interior with its "
                                                                    "panoramic windows (repaint the furniture as a gallery)"),
           ("item:TEAMPHOTO", "the school team photograph from 1995, with a boy in the back row"),
           ADAM, STYLE_INTERIOR],
     shot=(GALLERY + " A large enlarged print of the 1995 school team photograph hangs framed on a white panel, lit by "
           "a spotlight: the whole team of children in red shirts, two rows, and the boy in the back row clearly visible "
           "too. Adam stands in front of it, seen from behind at three-quarter view, looking up at it with a quiet smile. "
           "A small blank caption plate beside the frame. The mountains through the windows."),
     light="Bright high-mountain daylight from the windows, warm spotlight on the photograph.",
     characters=["ADAM"])

LOBBY = ("The lobby of the real Grand Jasna hotel imagined in 2035: an alpine hotel lounge with wood, stone and warm "
         "lamps, a small cafe corner with a coffee machine, and Tamara's temporary repair table 'Second Life' with tools, "
         "parts in small drawers and a repaired old radio.")

shot("EPILOGUE_4", kind="epilogue",
     refs=[("photo:S43/alpine-hotel-lounge_chedi-andermatt.jpg", "place reference: an alpine hotel lounge (type reference)"),
           ("photo:S43/alpine-hotel-reception_gasthaus-schwarzenstein.jpg", "place reference: an alpine reception and wood details"),
           char("TAMARA", "Tamara, 40, the repairwoman"),
           STYLE_INTERIOR],
     shot=(LOBBY + " Medium close shot: Tamara sits at her repair table, a small screwdriver still in her hand, and has "
           "stopped working for a moment: her eyes half closed, head slightly tilted, she listens to a gentle melody "
           "coming from the old repaired radio on the table. A cup of coffee steams beside it. Guests are soft "
           "shapes in the background."),
     light="Warm lamp light and soft daylight from tall windows; a calm, golden mood.",
     characters=["TAMARA"])

shot("EPILOGUE_5", kind="epilogue",
     refs=[("photo:S47/rotunda-chopok_interior-lounge_2016-09.jpg", "place reference: the real Rotunda interior "
                                                                    "(repaint it as the gallery)"),
           ("photo:S14/window_view_galbaveho_tower.jpg", "reference for the subject of the mural: a Bratislava "
                                                         "prefabricated concrete panel tower block"),
           char("NINA", "Nina, 30, the curator"),
           STYLE_INTERIOR],
     shot=(GALLERY + " A large reproduction of a 1995 underpass mural hangs on a gallery panel: a naive, loosely painted "
           "wall mural showing three tall grey prefabricated concrete panel apartment blocks of Petrzalka against a deep "
           "blue evening sky, their facades a regular grid of many small windows, and dozens of those windows lit, each "
           "lit window a slightly different warm colour - amber, rose, pale green, gold, orange - so that no two lights "
           "are the same. Nina stands beside it in her dark green coat, turned half to the "
           "viewer, one hand gesturing toward the windows of the mural as she explains it to a visitor."),
     light="Soft gallery spotlights, mountain daylight from the windows.",
     characters=["NINA"])

shot("EPILOGUE_6", kind="epilogue",
     refs=[("photo:S33/type_ref_post_office_counter_1956_fortepan103926.jpg", "place reference: a period post office "
                                                                              "counter (repaint in colour)"),
           ("photo:S33/type_ref_post_office_window_1956_fortepan103922.jpg", "place reference: the small post office window"),
           char("POSTA", "Alojz Baran, 54, the post office clerk"),
           STYLE_INTERIOR],
     shot=("A small village post office in Ivanka pri Dunaji in June 1962: on the outer sill of the small open window "
           "beside the counter sits Bela, a grey homing pigeon with an iridescent neck, looking in. Behind the wooden "
           "counter Alojz (white shirt, black clerk's oversleeves, grey waistcoat) calmly closes a big bound ledger with "
           "both hands, without any hurry, a faint satisfied smile. Rubber stamps, an ink pad and a wall calendar showing "
           "the year 1962 above the month grid of June 1962 with the Slovak weekday row Po Ut St Št Pi So Ne (1 June on "
           "Friday, Sundays in red)."),
     light="Warm late-afternoon sun through the window, dust in the beam.",
     characters=["POSTA"])

shot("EPILOGUE_7", kind="epilogue",
     refs=[("photo:S34/type_ref_hall_stage_curtain_1976_fortepan88710.jpg", "place reference: a village culture hall "
                                                                           "stage with a curtain (repaint in colour, no people)"),
           ("photo:S34/type_ref_wooden_stage_1948_fortepan27906.jpg", "place reference: a small wooden stage (no people)"),
           char("RUDO", "Rudo, 34, the amateur actor in his oversized stage costume"),
           char("LIDA", "Lida, 43, the costume maker"),
           STYLE_INTERIOR],
     shot=("Rehearsal in an empty village culture hall in June 1962: on the small wooden stage in front of a painted cloth "
           "forest backdrop, Rudo in his far too big checked jacket and low bowler hat stands with one arm flung out "
           "and chest forward, delivering his first line grandly and completely for the first time. In the front row "
           "below the stage Lida sits on a wooden chair, a hand pressed over her mouth, eyes squeezed, shoulders "
           "shaking as she holds back her laughter. Rows of empty chairs."),
     light="Warm stage lights on Rudo, the hall in soft afternoon shade.",
     characters=["RUDO", "LIDA"])

shot("EPILOGUE_8", kind="epilogue",
     refs=[("photo:S43/alpine-hotel-lounge_chedi-andermatt.jpg", "place reference: an alpine hotel lounge (type reference)"),
           char("ROBOT", "Ocko, the small delivery robot"),
           char("TAMARA", "Tamara, 40, the repairwoman"),
           STYLE_INTERIOR],
     shot=(LOBBY + " By the cafe corner, Tamara crouches down to the little delivery robot Ocko and hands it a small "
           "folded paper card on which is handwritten exactly: ĎAKUJEM. Ocko's lid is open with a delivered parcel "
           "inside, its light eyes curved upward in a happy look. A delivered cardboard box stands on her repair table."),
     light="Warm lamp light and soft daylight; friendly mood.",
     characters=["TAMARA", "ROBOT"])

shot("EPILOGUE_9", kind="epilogue",
     refs=[char("JANA82", "Jana at 12 in 1982 with her drawing"),
           char("JANA20", "Jana at 50 in 2020, on a laptop video call"),
           char("JANA35", "Jana at 65 in 2035"),
           ("item:JANA_DRAWING", "prop reference: Jana's 1982 drawing of a radio schematic"),
           STYLE_INTERIOR],
     shot=("A horizontal triptych of three tall panels side by side, separated by thin dark gutters, each showing Jana "
           "making exactly the same gesture: her near hand raised to chest height, palm open and turned up, explaining "
           "her own idea. Left panel, December 1982: 12-year-old Jana (exactly as image 1: light brown hair in a ponytail "
           "with a short fringe, grey-blue eyes, freckles; NOT grey or green hair) in her striped sweater at a school classroom "
           "desk beside her pencil drawing of a small radio schematic. Middle panel, 2020: 50-year-old Jana with glasses "
           "and a grey cardigan seen on the screen of an open laptop on a desk at home, the same gesture on the video "
           "call. Right panel, 2035: 65-year-old Jana with silver hair, glasses and a grey-blue scarf beside a glass "
           "display case in the Grand Jasna hotel salon in which the same old drawing is exhibited (the drawing lies the "
           "right way up, its corner date reads 1982)."),
     light="Each panel in its era: cool December classroom light, warm home lamp light, bright mountain daylight.",
     characters=["JANA82", "JANA20", "JANA35"])


# ----------------------------------------------------------------------------------------------- camera moves
# Simple pan / zoom for the cutscene player (src/game/data/cutscene_camera.json, written by `cutscenes.py camera`).
# Rects are [x, y, w, h] of the 1920x1080 frame, 16:9, zoom at most 1.33 (w >= 1440) so the 1920 px painting stays
# sharp. A rect may reach into the letterbox margin (y down to -0.1 h) to lift something out from under the top bar
# (CS09_1: the cabin sign). Moves run over the beat's duration_min_s unless 'seconds' is given; ease in_out.
FULL = [0, 0, 1920, 1080]
CAMERA = {
    "CS01_1": {"from": FULL, "to": [240, 120, 1440, 810]},              # push in on the phone photo
    "CS01_2": {"from": [480, 60, 1440, 810], "to": FULL},                # from Adam and the glowing ring out to the room
    "CS01_3": {"from": [480, 220, 1440, 810], "to": [0, 220, 1440, 810]},  # follow the leaving tram back to Adam
    "CS02_1": {"from": FULL, "to": [0, 150, 1440, 810]},                # push in on the turning reels
    "CS02_2": {"from": [0, 100, 1440, 810], "to": [480, 100, 1440, 810]},  # from adult Adam to the boy in the yard
    "CS03_1": {"from": FULL, "to": [0, 250, 1440, 810]},                # push in on the counter reading 1962
    "CS03_2": {"from": FULL, "to": [480, 160, 1440, 810]},              # push in on the emptied row
    "CS05_1": {"from": [0, 160, 1440, 810], "to": [480, 100, 1440, 810]},  # records -> the photograph
    "CS05_2": {"from": FULL, "to": [480, 270, 1440, 810]},              # towards the counter reading 2035
    "CS06_1": {"from": FULL, "to": [240, 100, 1440, 810]},              # slow push in on Viktor listening
    "CS07_3": {"from": FULL, "to": [240, 60, 1440, 810]},               # closer to Adam and Mira at the glass
    "CS07_4": {"from": [0, 120, 1440, 810], "to": FULL},                # pull back to the calm wide view
    "CS08_1": {"from": [0, 270, 1440, 810], "to": [480, 270, 1440, 810]},  # pan through 1982 -> 1995 -> 2020
    "CS08_2": {"from": FULL, "to": [400, 270, 1440, 810]},              # settle on the preserved bricks
    "CS09_1": {"from": [0, -108, 1920, 1080], "to": [480, 200, 1440, 810]},  # the cabin sign, then Adam
    "CS09_2": {"from": FULL, "to": [160, 60, 1440, 810]},               # follow Adam towards the funitel
    "CS07_5": {"from": FULL, "to": [0, 90, 1600, 900]},                 # drift the bell right, away from the end title
}
for _shot_id, _cam in CAMERA.items():
    SHOTS[_shot_id]["camera"] = _cam
