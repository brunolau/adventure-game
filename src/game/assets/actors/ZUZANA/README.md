# ZUZANA (S37, manor park of Ivanka pri Dunaji, June 1962)

A seven-year-old village girl. Likeness from a family photo supplied by the owner. Style A, three-quarter view
facing right (mirror for left), ADAM's approved sprite as the cast anchor. Masters and tools:
`art/characters/ZUZANA/`, `art/tools/zuzana_set.py` (paid), `art/tools/zuzana_build.py` (local).

Height: 350 px standing at scale 1 (adults 512 px = 1.70-1.75 m, so about 118-120 cm, 0.68 of Adam; SONA at 11
is 420 px). Crouched (drawing): 204.3 px, same head size.

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
