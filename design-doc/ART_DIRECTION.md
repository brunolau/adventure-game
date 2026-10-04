# Posledný zvonec — Art Direction (binding for all generated graphics)

Added 2026-10-05 by the product owner's decision. Extends `assets.csv`, `rooms[].art_brief`,
`characters[].design`, `location_families` and `landmark_layouts` in `game.json`; it never overrides
gameplay data. Where this file and the handoff disagree on *story or logic*, the handoff wins; on *how
things look*, this file wins.

## 1. One style only: "A — Hand-painted"

Every image in the game (backgrounds, overlays, characters, icons, cutscene frames, map, UI art) uses
style A, chosen by the product owner on 2026-10-04 from the style tests in `art/style-tests/`.

Canonical style prompt (append verbatim to every generation prompt):

> Style: classic 1990s hand-painted adventure game background. Rich painterly brushwork, slightly
> exaggerated cartoon proportions with gently curved lines, warm late-afternoon sunlight, saturated but
> harmonious colours, soft dappled shadows under the trees.

- Lighting may follow the scene's time and weather (night, December snow in 1982, autumn 2020, alpine
  June 2035) but brushwork, palette harmony and line quality stay the same.
- Reference images for the look: `art/backgrounds/entrance.png`, `side-path.png`, `tram-stop.png`,
  `dom-kultury.png`, `sokolikova-street.png`, `sokolikova-yard.png`, `hurikan.png`.
- Generator: fal.ai `fal-ai/nano-banana-pro/edit` (photo → painted) at 2K 16:9, downscaled to the
  asset size from `assets.csv`. Every paid call is appended to `art/spend-log.csv`.
- No other styles, no pixel art in the shipped game, no photo-real output.

## 2. Real locations rule

**Every exterior in the game is based on a real place.** This is binding:

1. If the handoff names a real place (ZŠ Sokolíkova, Biela Púť, Grand Jasná, Vrbické pleso, Rotunda,
   Priehyba, Funitel, Ivanka pri Dunaji kaštieľ…), find freely licensed photos of exactly that place
   and paint from them.
2. If the handoff describes an exterior as fictional, stylised or unspecified ("Fiktívna obytná ulica",
   "vymyslená zastávka", "štylizované trhovisko"…), **pick a real place in the stated district that fits
   the brief** and paint from it. The handoff's fiction boundaries still apply: invented shop names,
   no real house numbers, no real businesses' signage or logos, no claim about real institutions. The
   *geography and architecture* are real; the *story content* stays fictional.
3. When no usable photo of the place exists, use the **reconstruction approach** (proven on Hurikán):
   take the real layout from OpenStreetMap (buildings, courts, paths, trees), use freely licensed photos
   of the immediately surrounding real buildings as references, and paint the place from that.
   Mark it `basis = reconstruction` in the register.
4. Interiors: base them on a real building of the right type and period when a licensed photo exists
   (e.g. a real 1970s Bratislava school corridor). Invented interiors are allowed when the handoff says
   so, but their windows must show the real exterior of that location.
5. Eras: the same physical place in 1960/1982/1995/2020/2035 is painted from the same real base and the
   same camera (`location_families`, `landmark_layouts`). Era changes are made by editing the
   architecture, vehicles, signage, vegetation, clothing and weather — never by a colour filter alone.

Photo sources, in order of preference: Wikimedia Commons, Openverse (Flickr CC), KartaView, Panoramax,
Mapillary (needs a token). **Forbidden:** Google Maps / Street View / Earth imagery (Google's terms forbid
derived content), press or stock photos without a free licence, and identifiable faces of real
private people (paint people out or replace them with generic figures).

Licence handling: prefer CC0 / public domain / CC BY / CC BY-SA. **Decision 2026-10-05: the game is released
free and non-commercial**, so CC BY-NC(-SA) sources are allowed with attribution; every such use is still
flagged in the register so it can be replaced if that ever changes. Derived artwork inherits share-alike terms.

Other product decisions (2026-10-05): subtitles only for now (voice line ids stay ready for later AI voices);
AI-generated original music per era + free CC0 sound effects and ambience; the player-facing title stays
*Posledný zvonec* (an English localization would be *The Last Bell*), the code name is LastBell. All attributions go to `art/source/CREDITS.md` and the game's credits screen.

### Decisions taken during location research (2026-10-05)

- **Art licence:** backgrounds painted from CC BY-SA sources are adaptations; all game artwork is therefore
  released under **CC BY-SA 4.0** (code licence is separate). NC-derived pieces are additionally non-commercial.
- **Real place names as plain lettering are allowed** where the handoff names the real place (Grand Jasná,
  ROTUNDA, CHOPOK, ZŠ Sokolíkova, stop names). **Company logos and brands are not** (TMR, GOPASS, TESLA,
  shop chains, cabin liveries' logos): paint unbranded equivalents.
- **Third-party artworks** visible in reference photos (sculptures, murals, the Rotunda dragon) are omitted
  or replaced by neutral elements. Identifiable people in references are always painted out.
- **Post-era objects** visible in references are removed for earlier eras (newer towers, PVC windows,
  renovated cladding, red canopies of later date); see each register row's notes.
- Chorvátsky Grob exteriors are painted in **Čierna Voda** (a part of the municipality) where licensed
  imagery exists. The fictional Atlas pavilion stands on the gravel plateau ~50 m east of the Rotunda.
- Open for the product owner: the 1982 tram anachronism at the Dúbravka stop (ISSUES.md ART-DUBEXT).

## 3. Locations register (keep it current)

`design-doc/LOCATIONS_REGISTER.csv` records the real place behind every room. One row per room:

| column | meaning |
|---|---|
| room_id, room_name, era | from `game.json` |
| real_place | the real place used, e.g. "ZŠ Sokolíkova 2, main entrance" |
| area, lat, lon | district/street and coordinates of the camera position |
| basis | `photo`, `reconstruction`, `type-reference` (real building type, invented specifics) or `fictional-interior` |
| family | `location_families` id if the room shares a camera with other eras |
| source_files | local reference photos under `art/source/rooms/<room_id>/` |
| source_urls, license, author | for credits; NC licences flagged |
| fiction_notes | what is deliberately fictional (names, signage, house numbers…) |
| notes | anything future artists should know |

## 4. Composition and blocking

- 1920×1080 master, 16:9. The walkable band (`walk_polygon`) must read as open floor; nothing may
  block it.
- Hotspot `rect`s are binding blocking: each prop is painted inside its rect. Generation uses the real
  photo **plus a layout guide** (rects and walk band drawn and labelled) as a second reference image.
  After generation the image is checked against the rects; a prop that lands outside is regenerated.
  Small visual corrections (≤ 40 px) may be stored in `src/game/data/art_overrides.json`; logic
  coordinates in `game.json` are never edited.
- Foreground occluders (lamp posts, tree trunks, railings in front of the walk band) are cut out into a
  separate `foreground_mask` layer so actors can walk behind them.
- Camera families share architectural anchors pixel-for-pixel across eras (see `landmark_layouts`).

## 5. A living world — every scene animates

No room is a still image. Each room has at least **three ambient animations**, mixed from:

- **Nature:** wind in tree crowns and grass, falling leaves or snow, birds landing and taking off,
  pigeons pecking, clouds drifting, water ripples and glints, insects at lamps.
- **Mechanical:** trams and buses passing in the background, cars on far roads, a turning fan, clock
  hands, flickering fluorescent tubes, a blinking departure board, cable-car cabins moving on the rope.
- **People:** background passers-by, a child on a swing, a neighbour shaking a rug from a balcony,
  shadows moving behind windows. Non-interactive and never blocking the walk band.
- **Light and air:** dust motes in sunbeams, steam from a vent or tea cup, smoke from a chimney,
  heat shimmer, light from a passing car sweeping across a ceiling.

Implementation: ambient layers are data (`src/game/data/ambient/<room>.json`) rendered by the
`AmbientLayer` system as sprite loops, particles, shaders (wind sway, water) and tweened sprites on paths.
Ambient sprites are painted in style A and cut out with transparency. All ambient motion respects the
"reduced motion" accessibility setting (it then freezes or slows to a minimum). Ambient sound per room
comes from `rooms[].ambience`.

## 6. Characters

- Style A, consistent model sheets per character from `characters[].design`; age is locked per sheet
  (Tóno 12/25/50, Mira 20/60…).
- Feet on a baseline, up to 512 px tall at the front of the walk band; perspective scaling by feet y.
- Animation sets per `assets.csv`: NPCs `idle`, `talk`, `gesture`; the hero additionally `walk` (left,
  right, toward, away), `reach_low/mid/high`, `use_tool`, `show_item`, `inventory_combine`.
- Idle loops always have life: breathing, blinking, small weight shifts.
