# Product-owner location feedback — 2026-10-05 (binding for the rooms listed)

The product owner grew up in Dúbravka and knows these places. Where this file and the register disagree, this
file wins. Reference images the owner supplied are in `art/source/owner_refs/` (git-ignored, not redistributed).

**How to use owner references (copyright):** most are copyrighted web/press photos and two are Google Street
View screenshots. LOOK at them to understand the real place, its layout, materials, colours and proportions,
and write that understanding into the blocking, layout sketch and prompt. Do **not** pass them to the image
generator as image inputs and do not copy their exact framing. Image inputs stay freely licensed photos
(register), OSM reconstructions, our own layout sketches and our approved paintings. Search again for freely
licensed photos of the exact views below (Commons geosearch, Openverse, KartaView, Panoramax).

| room | feedback | owner reference(s) |
|---|---|---|
| **S04** Potraviny cez okienko | OC Monar is a **quarter-circle (arc) shopping centre**: one-storey arc of shop units under a continuous green metal arcade canopy, orange/red tiled roofs with dormers above, glazed shopfronts, a paved courtyard inside the arc with benches/tables and lawn. The grocery store is **in the middle of the arc**. Paint the camera in the courtyard facing the mid-arc grocery unit with its window sale (2020 covid). Fictional shop name; no real brand signs (Monar logo, dm, chains). | `S04_monar_thumb.jpg` (aerial: the arc), `S04_monar_shop.jpg` (the exact shopfront) |
| **S05** Mirkina bránka | Pathways are **narrower** in reality: a narrow pavement/path along the fence, more grass verge, the street itself modest. Repaint the natural pilot accordingly (walk polygon follows the narrow path + verge). | — |
| **S07** Čierna Voda pri výveske | Use the real **roadside bus stop on the long straight road at the edge of Čierna Voda**: two-lane road running into the distance, a lay-by with a small red-framed glass shelter on the right, low modern flat-roofed white/grey building behind young trees, wide grass verges, young trees along the road. Community notice board next to the shelter per the brief. | `imgur_wrRxN8x.jpg` (**Google Street View: location pointer only**) |
| **S08** Chodník pri retenčnej nádrži | The view is **from the pump track**: a natural pond with reeds and pale water in hummocky dry-grass scrubland, a winding packed-dirt pump-track trail in the foreground (walkable), **no fence** around the pond, distant houses and low hills. | `imgur_2tyAMxf.jpg` |
| **S11** Dúbravská zastávka 1995 (L_STOP base) | 1995 must show the **old Dúbravka tram stop**: a long curved brown/burgundy steel-tube shelter with a solid brown back wall and a translucent blue roof, the platform with a light edge strip, and an old **red-cream Tatra T3** tram (no line number/destination text, per brief). 2020 (S51) gets the modern stop; 1982 (S57) the bus + line under construction. Keep L_STOP anchors. | `S11_old_stop_T3.jpg` |
| **S12** Pred ZŠ Sokolíkova | "Kinda ok." The pre-production style test `art/backgrounds/entrance.png` may be used as a reference. | `art/backgrounds/entrance.png` |
| **ZŠ Sokolíkova (all school rooms)** | The **other side of the school** (the yard side) is a long two/three-storey building with ribbon windows facing a big lawn, a fenced multi-sport court and the athletics track; the owner's class **used that side as their entrance** — incorporate a working entrance door on the yard side. **In the 1980s and 1990s the walls were not painted with murals: one single colour, yellowish.** (The colourful murals are post-2000s: only possibly in 2020.) The real entry hall looked different from the generic type-references (details pending from the owner). | `SCHOOL_other_side.jpg`, `SCHOOL_far_playground.jpg` |
| **S17** Školský dvor (L_YARD base) | Use the yard-side photos above as the basis: big lawn, fenced court, athletics track, the long building with ribbon windows and the yard entrance; yellowish plain walls in 1982/1995. Linden, bench and art panel per the brief. | `SCHOOL_other_side.jpg`, `SCHOOL_far_playground.jpg` |
| **S18** Sídliskový dvor s kioskom | Use **`art/source/rooms/S18/panel-blocks-sokolikova_carl-eric-2012_NC.jpg`** as the main base ("that one is cool, great"). | (licensed, NC) |
| **S21** Kamenné námestie | What people picture: the open square with the white modernist **department store** (1968; in 1995 a "Prior" store — paint as a generic "OBCHODNÝ DOM" without brand), the tall white **Hotel Kyjev** tower behind it, the round-roofed pavilion, trees and lawns, tram/bus traffic at the edge, busy pedestrians. Ground-level camera for the walk band; remove post-1995 billboards and brands. | `S21_kamenne_namestie.jpg` |
| **S28** Petržalský podchod | Only **`type-ref_housing-estate-underpass_stairs.jpg`** (the third photo) represents a real Petržalka underpass; base the room on it, not the other two. | (licensed) |
| **S43** Lobby hotela Grand Jasná | The current type-references are wrong. The real lobby: a grey stone-textured feature wall with RECEPTION lettering, a long white curved reception counter, grey stone floor tiles, flowers on the counter; the lobby bar is a long bright room with rows of beige upholstered armchairs around small round tables, colourful paintings on the walls, light curtains. Plain "Grand Jasná" name allowed; no logos. | `S43_reception.jpg`, `S43_lobby_bar.jpg` |
| **S41** Biela Púť pri dolnej stanici | Base the Jasná arrival screen on the real view **in front of Hotel Pošta near the gondola (lanovka) station at Biela Púť**: the access road with a wooden bridge railing on the left, the gondola line and a steel pylon overhead, the station building, the steep-gabled wooden chalet of Hotel Pošta in the middle distance, spruce forest and hills, a rocky slope on the right. | `imgur_d7UwYm6.jpg` (**Google Street View: location pointer only**) |

Open questions sent back to the owner: are the imgur photos the owner's own (then usable directly)? What did the
real entry hall (S13/S53/S59) look like?

## Update 2026-10-05 (owner): permission for the imgur photos

The owner granted permission to use all imgur photos he supplied. Applied as follows:
- `imgur_2tyAMxf.jpg` (S08, pond from the pump track): **may be used directly** as a reference image input.
- `imgur_d7UwYm6.jpg` (S41) is a **Google Street View screenshot** (Street View logo, "Aug 2019 / See latest date",
  compass and zoom controls visible). `imgur_wrRxN8x.jpg` (S07) shows **no** Street View UI (only a dark strip at the
  top); its origin is unconfirmed — treat it as a pointer until the owner confirms its source, then it may be used directly. The owner's permission cannot cover Google's imagery, whose terms forbid derived content,
  so they stay **location pointers only**. S07 was matched to licensed KartaView frames of the same stop.
- The images stay out of the public repository (`art/source/owner_refs/` is git-ignored) unless the owner confirms
  he took them himself and releases them under a free licence.

## Update 2026-10-06 (owner): replacements and provenance

- `imgur_efnmLuG.jpg` is a crop of the same Google Street View capture as `imgur_d7UwYm6.jpg` (identical pixels without
  the UI) → still Google imagery, **location pointer only**.
- `imgur_jweYNjd.jpg` (= the same picture as `imgur_wrRxN8x.jpg`, S07 Čierna Voda bus stop): the owner states it
  comes from a friend's hard drive and the friend **allowed its use** → may be used **directly** as a reference image
  input for S07. Credit: "reference photo: a friend of the product owner, used with permission" (no name). It stays
  local (not redistributed in the public repo) unless the owner asks otherwise.

## Update 2026-10-06 (owner): new S41 references

- `imgur_TXI6i3E.jpg` and `imgur_8l08ndF.jpg` (Biela Púť: access road with the wooden bridge railing, gondola pylon,
  Hotel Pošta chalet and the gondola station; summer): the owner states they come from **another friend's private
  archive, used with permission** → may be used **directly** as reference image inputs for S41 (painted in winter).
  Credit: "reference photos: a friend of the product owner, used with permission" (no name). Kept local only.
- S41 must look like that real view: road leading in with the wooden bridge railing on the left, the steel pylon and
  rope overhead, the gondola station building, the Hotel Pošta chalet in the middle distance, spruces, the rocky slope
  with the stone retaining wall on the right — in WINTER (owner decision: Jasná is winter).

## Update 2026-10-06 (owner): Dúbravka corrections

- **S17 school yard (and S55 2020, S61 1982):** layout per the owner's satellite view (`imgur_vLrYd9c.jpg`, map
  screenshot → layout pointer only): the red clay running track ("antuka") is on the LEFT, with grass inside it; the
  fence must be turned 90°; behind that fence: in 2020 a football pitch (artificial turf), in 1995 and earlier a
  concrete playground with basketball baskets. School walls plain yellowish in 1982/1995 (earlier note).
- **S18 / S62:** use the owner-loved style-test painting `art/backgrounds/sokolikova-street.png` (Sokolíkova panel
  row, sunset, red car) as the base, keeping its look; add Zita's kiosk (1995) / the larger shop window (1982).
- **`art/backgrounds/sokolikova-yard.png`** (walled courtyard ihrisko between the blocks) must be in the game: a new
  walk-through room next to the school yard / kiosk courtyard (needs the content-overlay room support; follow-up).
- **S11 / S51 / S57 = Švantnerova stop on M. Schneidra-Trnavského:** the road rises slightly uphill; tram tracks to
  the right of the road (1995: on concrete panels); panel-block layout as in the references; on the right a bluish
  low **medical centre** (there since the early 1980s → also in 1982). References: `imgur_gnv1VFF.jpg` (a friend's
  photo, **usable directly**), `imhd_svantnerova_1995.jpg` and `imhd_svantnerova_7951.jpg` (imhd.sk, copyrighted →
  look only; no brands Lukoil/Tesco/Dr.Max).

## Update 2026-10-06 (owner): S08 and S03

- **S08:** the real pumptrack (a raised, hummocky dirt mound with a winding track) lies on the FAR side of the pond,
  instead of houses. Reference `web_pumptrack_cierna_voda_2020.jpg` (blog photo, look only).
- **S03:** based on the real playground **"Lúčny koník"** in Čierna Voda (hip-roofed timber shelter with a stone
  chimney, wooden playground, meadow); the name Lúčny koník is used in the game texts. Reference
  `web_lucny_konik_2018.jpg` (blog photo, look only).

## Update 2026-10-06 (owner): S17 family refinements

- Replace the concrete footpath on the LEFT side of the fence with grass (S17, S55, S61).
- Right of the school's yard entrance the ground floor is an open **underpass ("podlubie")** through the building,
  leading to the three blocks behind — paint it as a covered passage with columns, not as a wall.
- References: `imgur_fNEtUPs.jpg` (**highest priority**; owner-supplied imgur photo, covered by the owner's blanket
  permission for his imgur photos, not Street View → may be a generator input), `web_school_thumb.jpg` (Google image
  thumbnail of an unknown photo → look only), `SCHOOL_other_side.jpg` (dubravska4liga.sk → look only).
- Era detail: the colourful ground-floor murals in the 2020-era photos are post-2000 → 2020 only; 1982/1995 plain
  yellowish walls (earlier note).
