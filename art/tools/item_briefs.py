"""Briefs for the inventory icons after the prologue (70 items), grouped into generation sheets.

Each brief describes one era-correct object for items.py (style A, one 4 x 2 sheet per group). Eras follow the
item's origin action in game.json: B* 1995 Bratislava, I* 1960 Ivanka, C*/D* 2020, E* 1982 Dubravka,
F* 2035 Jasna, Q* side quests (era of their room). Objects never contain green parts (green key canvas);
glass, film and foil are painted milky so the key never shows through them.
"""
from __future__ import annotations

# --- shared object descriptions (combination chains must look like the same physical object) -------------------
_CASSETTE = ("a 1990s compact audio cassette in a dark grey plastic shell with a cream paper label and a clear "
             "window showing two reels of brown tape; no brand, no logo")
_ADAPTER = ("a short crossed audio adapter cable: grey round cable with a round silver five-pin DIN plug at one end; "
            "at the other end the cable splits into two short wires, one red and one white, that cross over each "
            "other")
_DOC_1960 = "a yellowed 1960s typewritten form sheet with printed form lines"
_WAXSHEET = "a soft, slightly translucent cream-ivory waxed paper sheet with a gentle sheen"
_JAR = ("a 1980s clip-top preserving jar: a squat glass jar painted slightly milky with bright white highlights, "
        "with a glass lid, an orange rubber sealing ring and a steel wire clip")
_BRIDGE = ("a small white porcelain terminal block (a ceramic bridge) the size of a matchbox, with three short copper "
           "leads of different shapes (one straight, one bent, one looped) and a tiny swallow bird mark painted "
           "in blue on its side")
_CLIPBOARD = ("a printed white A4 handover form on a brown hardboard clipboard with a steel clip: thin table lines, "
              "a printed box number 'Z-17' in a small frame at the top, and two signature lines at the bottom")
_SLIP_2035 = ("a 2035 courier delivery slip: a thin pale-grey printed card with a turquoise header stripe, a small "
              "parcel pictogram and a tiny pictogram of a park bench with a dog")
_GADGET_2035 = "light natural wood and matte grey, with small turquoise accents"

BRIEFS: dict[str, str] = {
    # ---- 1995: school tape recorder chain ----
    "BELT_OLD": ("A worn-out rubber drive belt from a cassette recorder, shown large: a thin flat black rubber band, "
                 "snapped in one place, cracked, limp and stretched out of shape, lying in a loose irregular loop "
                 "with its two torn ends clearly visible."),
    "BELT_NEW": ("A brand-new rubber drive belt for a cassette recorder, shown large: a clean glossy black rubber "
                 "ring forming a neat perfect circle, with a small blank cream cardboard tag tied to it with thin "
                 "string."),
    "TAPE_RAW": ("A school audio cassette with a problem: " + _CASSETTE + "; the label has a few short illegible "
                 "pencil strokes, and a loop of the brown tape has been pulled out of the shell and hangs in a "
                 "crinkled tangle."),
    "TAPE": ("The original school audio cassette, safe and sound: " + _CASSETTE + "; the label has a few short "
             "illegible pencil strokes, the tape is neatly wound inside, and the cassette lies half inside an "
             "opened clear plastic cassette case painted milky with white highlights."),
    "ADAPTER": ("An unfinished audio adapter: " + _ADAPTER + "; the ends of both wires are stripped, showing bare "
                "copper, and each wire carries a tiny white paper flag, one marked with a circle and one with a "
                "triangle. No connector on these ends yet."),
    "CONNECTOR": ("A small two-pole electrical connector from the 1990s: a chunky black bakelite plug block with two "
                  "brass contacts on the front, a tiny white painted circle next to one contact and a tiny white "
                  "painted triangle next to the other."),
    "BRAID": ("A short cut piece of woven textile insulation sleeve for a cable: a flexible braided cloth tube in "
              "beige with thin dark-blue threads, both cut ends slightly frayed, lying in a gentle S-curve."),
    "LINK_OPEN": ("The audio adapter, connected but not insulated: " + _ADAPTER + "; their ends are now plugged into "
                  "a small chunky black bakelite two-pole connector block, but a short section of bare copper wire "
                  "is still exposed between the cable and the connector."),
    "STEREOLINK": ("The finished audio link cable: " + _ADAPTER + "; their ends run into a small chunky black "
                   "bakelite two-pole connector block, and the wires between the cable and the connector are fully "
                   "covered by a beige braided cloth insulation sleeve with thin dark-blue threads."),
    # ---- 1995: archive, maps, photo studio, radio amateur ----
    "DIAGRAM": ("A technical base map sheet from an archive: a large cream paper sheet, slightly curled at one "
                "corner, printed with thin grey street lines and a faint grid, three small circled measuring "
                "points marked in red ink, and nothing else on it."),
    "OVERLAY": ("A transparent map overlay foil: a sheet of drafting film painted as milky, frosted, slightly "
                "bluish-white semi-clear plastic with bright white highlights (the background never shows through), "
                "printed with thin red lines and exactly three black registration marks: a small punched round "
                "hole, a double cross and a small square."),
    "NODEMAP": ("A completed node map: the same cream paper base map with thin grey street lines and three red "
                "circled measuring points, with a frosted milky drafting-film overlay laid exactly on top; thin red "
                "lines on the film now connect the three points into a clear triangle network, and the black "
                "registration marks (hole, double cross, square) line up."),
    "NEGATIVE": ("A technical photographic negative: a short strip of 35 mm film negative in dark orange-brown, "
                 "three frames with sprocket holes along both edges, the frames showing an inverted image of a "
                 "laboratory apparatus, and a small cream paper tag attached with a paper clip."),
    "CALPHOTO": ("A black-and-white glossy photograph print with a white border, slightly curled: it shows a "
                 "laboratory table with a brass-framed calibration stand apparatus and a sheet of paper lying on "
                 "the table beside it."),
    "COIL": ("A hand-made measuring coil: a flat round loop of copper wire, about the size of a saucer, tightly "
             "wrapped in red cotton insulation tape, with two short black leads ending in small brass banana "
             "plugs."),
    "METRONOME": ("A classic mechanical metronome: a wooden pyramid case in warm reddish-brown varnish, its front "
                  "cover open, showing an ivory tempo scale and a steel pendulum rod with a small brass weight, "
                  "tilted to one side."),
    # ---- 1995 + side quests ----
    "LETTER": ("Mira's letter of authorisation from 1995: a white typed sheet of paper, folded in thirds and half "
               "pulled out of an opened cream paper envelope; a few lines of grey typewritten text (illegible), a "
               "handwritten blue-ink signature and a round violet rubber stamp are visible."),
    "TEAMNEG": ("A 1990s photo-lab envelope: a yellow-orange paper envelope with a blank white label area, its flap "
                "open, with a strip of orange-brown film negatives sticking out of it."),
    "TEAMPHOTO": ("A 1995 colour photograph print with a white border and warm slightly faded colours: a school "
                  "football team of about ten children posing in two rows on a sports field, in red jerseys, the "
                  "faces small and simple."),
    "SCORE": ("Handwritten sheet music: a cream manuscript-paper sheet with printed staff lines and four bars of "
              "black ink music notes, with a short illegible pencil title above, one corner curled up."),
    "CHALK": ("One stick of white school chalk, shown large and diagonally, one end rounded from use, a little "
              "white chalk dust on it, painted with a clear darker outline so it reads well."),
    "KEEPERNOTE": ("Tono's small handwritten note from 1995: a slightly crumpled pale-yellow sheet torn from a "
                   "pocket notebook, with a ragged torn top edge and soft shading in its creases; on it a firm dark "
                   "graphite pencil sketch of a wall section: one rectangle divided into a grid of 3 rows and 4 "
                   "columns of stone blocks, and the block in the second row from the top and the third column from "
                   "the left boldly circled in red pencil. No words, no letters, no numbers."),
    "BALL": ("A dog's well-used red rubber ball, shown large: a small round bright red ball with a moulded curved "
             "seam line around it like a tennis ball, scuffed and dusty from the dry bank, with a few small tooth "
             "punctures and bite scratches; still perfectly round."),
    "FLYER": ("A large printed neighbourhood notice from 2020: a white A4 sheet with two strips of clear tape at "
              "the top corners, a big bold dark-blue headline 'SUSEDSKÁ POMOC', below it a large '9–17', and a "
              "simple dark-blue telephone handset pictogram; nothing else written on it."),
    # ---- 1960: leather cuff for the demonstration pump ----
    "SUPPLYSLIP": ("A 1960 workshop supply slip: a small stiff ochre manila card slip with a few lines of violet "
                   "typewritten text (illegible), a round violet rubber stamp, a pencil tick, and a hole punched "
                   "at the top where it hung on a spike."),
    "LEATHER": ("A pre-cut leather strip for a pump seal cuff: a flat curved band of tan vegetable-tanned leather "
                "with neatly cut rounded ends, and a row of small pencil dots marking where holes will be punched; "
                "no holes yet."),
    "RIVETS": ("Two hollow brass rivets with their matching caps, shown large: shiny golden brass, simple and "
               "sturdy, lying side by side."),
    "PUNCH": ("A 1960s revolving leather hole punch: steel pliers with a rotating wheel of six punch tubes of "
              "different sizes at the jaw, worn red-painted handles and a steel spring between them."),
    "CUFF_OPEN": ("The punched leather strip: the same flat curved band of tan leather with neatly cut rounded ends, "
                  "now with a clean row of small punched round holes along both ends; not yet closed."),
    "CUFF": ("A finished leather pump seal cuff: the tan leather band now bent into a closed ring, its two ends "
             "overlapping and joined by two shiny brass rivets."),
    "PUMPKEY": ("A 1960s room key: a plain dark blued-steel door key with a simple bit, on a steel ring with a "
                "round aluminium tag stamped with a small number 3."),
    "STYLUS": ("A blunt embossing stylus: a short turned wooden handle in honey-brown with a brass ferrule and a "
               "polished steel shaft ending in a small rounded ball tip, shown large and diagonally."),
    # ---- 1960: registration and the impression of the calibration plate ----
    "REGFORM": ("A 1960 technical registration form: " + _DOC_1960 + ", a few lines of black typewritten text "
                "(illegible), a typed date line and a handwritten blue-black ink signature at the bottom."),
    "CARBON": ("A sheet of 1960s carbon copy paper: a thin dark violet-blue sheet with a soft waxy sheen, one corner "
               "slightly curled up showing its lighter grey back."),
    "REGDOUBLE": ("Two copies of the same registration form, fanned out one over the other: " + _DOC_1960 + " with "
                  "black typewritten lines and a blue-black signature, and behind it its carbon copy with the same "
                  "lines and signature in violet-blue carbon ink."),
    "REGISTERED": ("The registered form: " + _DOC_1960 + " with black typewritten lines and a blue-black "
                   "signature, now with a round black postmark stamp and a small red-and-white registered-mail "
                   "label with a large letter R stuck in the top corner."),
    "WAXPAPER": "A waxed paper sheet: " + _WAXSHEET + ", one corner folded over.",
    "PRESSED": ("An embossed waxed sheet: " + _WAXSHEET + ", with the faint colourless relief of four simple "
                "symbols (a circle, a cross, a square and a triangle) pressed into it, only visible by soft light "
                "and shadow."),
    "ORIGIN_RAW": ("A readable impression: " + _WAXSHEET + ", with the relief of four simple symbols (a circle, a "
                   "cross, a square and a triangle) now clearly traced in dark graphite, and two small handwritten "
                   "signatures in ink below them."),
    "ORIGIN": ("The verified impression of 1960: " + _WAXSHEET + " with four dark graphite symbols (a circle, a "
               "cross, a square and a triangle) and two small signatures, placed in an opened buff cardboard "
               "folder, with a small stamped registration slip attached by a steel paper clip."),
    # ---- 2020: handover chain, school + 1960 side quests ----
    "HANDOVER": ("A handover protocol, not yet signed: " + _CLIPBOARD + ", both signature lines empty, and a blue "
                 "ballpoint pen clipped to the board."),
    "HANDOVER_R": ("A handover protocol with one signature: " + _CLIPBOARD + "; the first signature line now carries "
                   "a handwritten blue-ink signature, the second is still empty."),
    "CHAIN": ("The completed handover protocol: " + _CLIPBOARD + "; both signature lines carry handwritten blue-ink "
              "signatures, a big blue tick mark is drawn next to them, and a small yellow sticky note with a "
              "telephone handset doodle is stuck on the corner."),
    "PHOTO2020": ("A wide panoramic photo print from 2020 with rounded corners and a glossy sheen: an autumn school "
                  "courtyard corner with grey asphalt and no tree, a low wall, and beside it a small side service "
                  "window with a little metal swallow ornament."),
    "SCHOOLPASS": ("A 2020 school permit: a printed white sheet in a clear punched plastic sleeve (painted milky "
                   "with white highlights), with a round blue school stamp and a signature, and a bright yellow "
                   "sticky note on it."),
    "LOG1982": ("A 2020 photocopy of an old service log page: a grey-toned photocopy sheet with dark copier edges, "
                "showing a handwritten date line at the top and a pencil sketch of a small ceramic block with three "
                "leads, with short illegible notes."),
    "SEEDS": ("A small twisted cone of brown paper filled with bird seed: golden wheat grains, striped sunflower "
              "seeds and millet, a few grains spilled beside it."),
    "PLAY": ("A 1960 amateur theatre script: a stack of typewritten pages bound with a cord through punched holes, "
             "a grey-blue cardboard cover with a hand-lettered illegible title, dog-eared corners and a few pencil "
             "notes in the margin."),
    # ---- 1982: return bridge, jar and cache; 2020 retrieval ----
    "PARTSNOTE": ("A 1982 school material requisition slip: a small pale-pink printed form with a table, filled in "
                  "with blue ballpoint pen, a violet rubber stamp and a signature."),
    "CERAMICPARTS": ("Parts for a ceramic bridge, loose: a small white porcelain terminal base the size of a "
                     "matchbox with three holes, and next to it three short loose copper connecting strips of "
                     "different shapes (straight, bent, looped), each with a tiny coloured paper band."),
    "BRIDGE_NEW": "A newly assembled ceramic return bridge: " + _BRIDGE + "; clean and new.",
    "JAR": ("An empty clean preserving jar: " + _JAR + ", the lid open, and a folded sheet of brown wrapping paper "
            "leaning against it."),
    "SEALED_NEW": ("A sealed jar: " + _JAR + ", the lid closed and the clip locked; inside it a small bundle wrapped "
                   "in brown paper tied with string."),
    "SEALED_OLD": ("An old jar recovered after 38 years: " + _JAR + ", now dusty and dull, with an aged cracked "
                   "dark rubber ring, a rusty wire clip and specks of earth; inside it the small brown paper bundle "
                   "is still dry."),
    "RETURNBRIDGE": ("The preserved ceramic return bridge, 38 years old: " + _BRIDGE + "; the porcelain is slightly "
                     "ivory with age but intact, and the copper contacts are freshly cleaned and shiny."),
    "TREEGUARD": ("Three finished wooden panels of a protective guard for a young tree, stacked: simple slatted "
                  "frames of pale pine laths, tied together with a twist of wire."),
    # ---- 1982 + 2035 ----
    "CACHEMAP": ("A child's drawing in coloured pencils on squared school notebook paper: a wall of rounded stones "
                 "in rows, the third stone from the left in the second row from the top marked with a red cross, "
                 "and a tiny blue swallow drawn in the corner instead of a signature."),
    "JANA_DRAWING": ("A pupil's electronics schematic from 1982: a squared paper sheet with a neat ruler-drawn "
                     "pencil circuit diagram (zigzag resistors, a few circles and lines) and short illegible "
                     "handwritten explanation notes."),
    "JANA_APPROVED": ("The approved schematic: the same squared paper sheet with the neat pencil circuit diagram and "
                      "notes, now with a big red teacher's tick mark, a small red signature, and a small red-and-white "
                      "ribbon rosette pinned to the corner."),
    "READER": ("A compact handheld audio reader from 2035, " + _GADGET_2035 + ": rounded light-wood casing, a grey "
               "fabric speaker grille, a small turquoise screen showing a sound waveform, and a short cable with a "
               "jack plug; no brand."),
    "CATALOG": ("A museum catalogue card: a cream index card with a turquoise header stripe, a few lines of grey "
                "typed text (illegible), the code 'Z-17' printed large in the top corner, and a small round hole "
                "at the bottom edge."),
    "PASS": ("A service visitor pass from 2035: a white plastic card with a turquoise stripe and a plain grey person "
             "silhouette in the photo box, in a clip holder on a grey fabric lanyard; no text, no logo."),
    "LIFT_TICKET": ("A return cable-car ticket from 2035: a rounded white plastic card with a deep-blue stylised "
                    "mountain with a little cable-car cabin on a rope, and a two-way arrow below it; no text, no "
                    "logo."),
    "FILTER_PHOTO": ("Adam's smartphone showing a photo: a plain dark graphite modern smartphone in a thin dark "
                     "bumper case, seen at a slight angle; on its screen a photo of a grey control panel with one "
                     "row circled in red. No brand, no logo."),
    # ---- 2035: Atlas service pavilion, delivery side quest ----
    "LEA_MESSAGE": ("A small audio memory pebble from 2035, " + _GADGET_2035 + ": a smooth rounded light-wood "
                    "pebble with a grey fabric speaker grille and a softly glowing turquoise ring, and a little "
                    "cream paper tag tied to it with string."),
    "DIAGNOSTIC": ("A printed diagnostic protocol from 2035: a thin pale-grey sheet, slightly curled, stapled at the "
                   "corner, with turquoise bar charts, a few grey lines of tiny text (illegible) and one row "
                   "highlighted in amber."),
    "PULSE": ("A captured reference pulse: a round palm-sized glass capsule with a brass rim, the glass painted "
              "milky with bright highlights, and inside it a softly glowing turquoise-blue regular wave line like "
              "ripples on a lake."),
    "PATCH": ("A signed restore package from 2035: a flat service cartridge of " + _GADGET_2035 + ", with a "
              "turquoise contact strip, wrapped by a cream paper band that carries two handwritten ink "
              "signatures."),
    "DELIVERY_NOTE": "A delivery request: " + _SLIP_2035 + ", and a few grey lines of tiny printed text (illegible).",
    "DELIVERY_OK": ("A confirmed delivery request: " + _SLIP_2035 + ", now with a big round turquoise check-mark "
                    "stamp and a handwritten ink signature."),
}

# Generation order: one 4 x 2 sheet per row (chains kept on the same sheet where possible).
SHEETS: list[list[str]] = [
    ["BELT_OLD", "BELT_NEW", "TAPE_RAW", "TAPE", "ADAPTER", "CONNECTOR", "BRAID", "LINK_OPEN"],
    ["STEREOLINK", "DIAGRAM", "OVERLAY", "NODEMAP", "NEGATIVE", "CALPHOTO", "COIL", "METRONOME"],
    ["LETTER", "TEAMNEG", "TEAMPHOTO", "SCORE", "CHALK", "KEEPERNOTE", "BALL", "FLYER"],
    ["SUPPLYSLIP", "LEATHER", "RIVETS", "PUNCH", "CUFF_OPEN", "CUFF", "PUMPKEY", "STYLUS"],
    ["REGFORM", "CARBON", "REGDOUBLE", "REGISTERED", "WAXPAPER", "PRESSED", "ORIGIN_RAW", "ORIGIN"],
    ["HANDOVER", "HANDOVER_R", "CHAIN", "PHOTO2020", "SCHOOLPASS", "LOG1982", "SEEDS", "PLAY"],
    ["PARTSNOTE", "CERAMICPARTS", "BRIDGE_NEW", "JAR", "SEALED_NEW", "SEALED_OLD", "RETURNBRIDGE", "TREEGUARD"],
    ["CACHEMAP", "JANA_DRAWING", "JANA_APPROVED", "READER", "CATALOG", "PASS", "LIFT_TICKET", "FILTER_PHOTO"],
    ["LEA_MESSAGE", "DIAGNOSTIC", "PULSE", "PATCH", "DELIVERY_NOTE", "DELIVERY_OK"],
]

assert len(BRIEFS) == 70 and sorted(BRIEFS) == sorted(i for s in SHEETS for i in s)
