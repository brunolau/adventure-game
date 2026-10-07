# AI voiceover: the whole game (2026-10-07)

This voices every spoken line that the prologue trial did not cover. The method is the one the owner approved after
the prologue trial and its recast (`docs/voice/TRIAL.md`, section "Recast 2026-10-06"): Gemini 3.8 Flash TTS stock
voices with a Slovak direction per character, the same shared pronunciation prompt and the same post-processing. A
touch of dry irony goes only on the clearly sarcastic lines. Every take had one ElevenLabs Scribe v2 check. A line got
one retake only when its transcript differed in meaning. No Whisper and no GPT were used.

- **Listening page:** `docs/voice/full.html`. Open it locally, because it plays the OGGs by relative path. It is
  organised by era and scene in play order, and each scene has a "Play scene" button. The flagged lines come first,
  then the casting table and the child/age audition. There are filters for era, speaker, flagged only, dry irony only
  and hiding the prologue.
- **Files:** `art/voice/full/<line_id>.ogg` (1,983 new lines plus the 4 re-rendered prologue SYSTEM lines),
  `art/voice/full/manifest.json` (all 2,217 spoken lines, the prologue included), `casting.json`, `flags.json`,
  `lines.json` (the extracted script), `audition/`.
- **Game:** all new OGGs were copied into `src/game/assets/voice/` at the end (see "Install").
- **Tools** (`art/voice/tools/`):
  - `extract_full.py` writes the script.
  - `casting_full.py` holds the casting.
  - `irony_full.py` lists the dry-irony lines.
  - `audition_full.py` runs the child and age audition.
  - `gen_full.py` handles `gen`, `report`, `recheck`, `retake`, `rerender`, `finalize` and `install`.
  - `manifest_full.py` and `build_full_page.py` build the manifest and the page.
  - These reuse `voice_lib.py`, `recast.py` (text check) and `casting.py` (the prologue casting and the irony prompt).

## Text and scope

The text of each line is the approved final text. That is the live tables (`src/game/localization/dialogue.csv`,
including `src/game/data/content_ext/dialogue_ext.json` through `tools/content_ext.load_effective_game`) with
`docs/writing/out_v3/knowledge.csv` and `knowledge_ext.json` applied on top. A knowledge sequence or topic replaces the
live overlay entry with the same id, and new keys take their `sk` from the draft. Epilogue lines come from
`world.csv` (`epilogue.<n>.line`) and their speakers from game.json `epilogue[].line`. Right before the install, the
script was extracted again from the live tables and compared line by line: nothing had changed.

What was voiced:

- the first-entry lines of every room;
- every action line, including overlay sequences and inventory combinations;
- every NPC topic, including overlay extensions and the `extra` / `after` topics;
- the cutscene lines of CS02 to CS09;
- the first-ride travel lines;
- the 11 epilogue lines;
- every SYSTEM, NARRATOR, NINA_REMOTE, LEA_REC and ADAM10 line.

What was not voiced:

- the 234 prologue lines whose text is unchanged (they stay as approved);
- Bodka's 3 `Haf!` lines (non-verbal);
- looks, UI and the journal.

Three prologue lines changed in the knowledge drafts and were regenerated with the recast voices (Adam / Ela / Mira):
`topic.ELA.extra 2.001`, `topic.ELA.extra 2.002`, `action.G05.x04`.

| era | new lines |
|---|---|
| 2020 (return to Grob, Dúbravka 2020; plus 3 changed prologue lines) | 159 |
| 1995 | 662 |
| 1962 (game era 1960) | 451 |
| 2035 | 420 |
| 1982 | 280 |
| epilogue | 11 |
| **total** | **1,983** lines, 101,600 characters, **129 min** of audio |

The game now has 2,217 spoken lines in all, about 2 h 25 min of audio.

Nine lines are the **same take reused**, because the same person says the same words. Examples: Adam's tape line
`action.F13.002` is the very recording of `cutscene.CS02.01.002`, and short repeats such as "A vy?" or "Sú pracovné."
also reuse one take. The manifest marks these with `alias_of`.

## Casting

One stock voice per person. The same person at another age keeps that voice with an age direction. Every direction
starts with the shared prompt "Speak natural, native Slovak (Bratislava region) with correct Slovak stress on the
first syllable and clear long vowels; no foreign accent. Read the text verbatim." The full directions are in
`casting.json`, on the page, and in `casting_full.py`. No real person is imitated.

**Family (same voice, age direction):**

| person | ages and voice |
|---|---|
| Adam | 35, **Achird**, everywhere (the recast voice; 1,031 lines in total). Adam at 10 on the 1995 tape is a child voice (**Autonoe**), see the child note. |
| Mira | 80 in 2020: **Gacrux** (fixed by the trial). 55 in 1995: Gacrux, a fuller, energetic teacher's voice. 22 in June 1962: Gacrux, young, light and quick. Mira has no lines in 1982, so the 42-year-old voice was not needed. |
| Tóno | 25 in 1995: **Puck**, quick and teasing. 50 in 2020: Puck, calmer, lower, deadpan. 12 in 1982: **Leda** (child, see below). |
| Jana | **Erinome** at every age: 12 (child direction), 25 (confident organiser), 50 (a video call, light call colour), 65 (calm, gently amused). |
| Oto | **Sadaltager**: 46 in 1962 (calm, precise), 66 in 1982 (older, softer, amused by time). |
| Zuzana | **Sulafat**: 7 in June 1962 (child direction) and 40 in 1995 (warm, gentle, calm, quietly funny). No real person is imitated. |
| Lea | **Achernar**: 33 in 1995 (warm, unhurried teacher). Her 2032 voice message (`LEA_REC`, verbatim) uses the same voice, aged about 70, softer, with the telephone colour. |
| Nina | **Kore**, in person and over the service channel (`NINA_REMOTE`, light call colour). |

**Everyone else** (the voice in brackets is also used by someone in another era, never in the same scene):

| era | cast |
|---|---|
| 2020 | Ela Despina, Dana Vindemiatrix, Roman Iapetus, Lenka Leda, Jozef Algenib, SYSTEM Schedar. All unchanged from the trial. |
| 1995 | Soňa (11) Laomedeia, Kubo (7) Zephyr, Zita Pulcherrima, Emil Enceladus, Pali Umbriel, Viera Vindemiatrix, Karol (archive) Charon, Alena (photo) Callirrhoe, Fero (market) Algenib, Milada Despina, Juro Sadachbia, Juraj Zubenelgenubi, Dezider Rasalgethi |
| 1962 | Božo Charon, Berta Pulcherrima, Alojz (post office) Algieba, Lída Aoede, Rudo Fenrir, Štefan (store) Alnilam, Vera Kore, narrator Charon |
| 1982 | teacher Dobrovič Orus, Ružena Aoede, Marta Kore, Šimon Algenib |
| 2035 | Viktor **Orus** (serious, controlled, low; no humour, no irony direction), Tamara Aoede, Boris Algieba, Sára Zephyr, Ivan Alnilam, Miloš (fellow passenger) Umbriel, Očko the robot Iapetus (synthetic, polite, with the device colour) |

No two speakers share a voice within one scene. The manifest checks this (`voice_clashes_in_scene` is empty).

**Child voices and their limits.** Gemini has no child stock voices. A child is an adult stock voice with the
direction "a real child's voice: high, light and small …". The audition (`art/voice/full/audition/`, on the page)
measured the median pitch:

| role | result |
|---|---|
| Tóno 12 | Leda 243 Hz. Tóno's own adult voice (Puck) only reached 187 Hz and sounded like an adult, so the boy does not share his adult voice. |
| Adam 10 | Autonoe 266 Hz. Adam's Achird reached 195 Hz. |
| Kubo | Zephyr 205 Hz. |
| Soňa | Laomedeia 218 Hz. |
| Jana 12 | Erinome 204 Hz (her own voice, so it stays related). |
| Zuzana 7 | Sulafat 220 Hz (her own voice), with a narrow melody of about 4 semitones. |
| Mira 22 | Gacrux 149 Hz. That is about 3 semitones above Mira at 80, but no higher than Mira at 55, so the age difference lives in the delivery more than in the pitch. |

Expect the children to sound like a young woman speaking for a child, not like a real 7- to 12-year-old. That is the
quality limit of stock TTS. Only the ear can judge it. A better result would need real child actors or a dedicated
child voice model. If a child voice does not work, the fix is to change its voice in `casting_full.py` and
regenerate (about $0.05 per child role).

**Phone, recording and device colour** (light, the trial's telephone EQ or milder):

| colour | lines |
|---|---|
| telephone | Mira 2020 outside S06 (12 lines, 2020 and the 2035 ending), Lea's 2032 message |
| call / channel (220–5200 Hz, softer) | Nina over the service channel (22), Jana 2020 on the video call (15) |
| 1995 school tape (band-limited, warm, faint hiss) | Lea and Adam 10 in CS02, Adam 10 in F13 |
| device (180–7000 Hz, a little presence, a hint of metal) | every SYSTEM line (24) and Očko (23) |

The four prologue SYSTEM lines were re-rendered from their raw takes with the device colour, so that ZVON sounds the
same everywhere. This was free (no new take). Their uncoloured trial files remain in `art/voice/trial/`.

## Dry irony

Every new line was read and classified with the recast rule. A line counts when its humour lives in a wry twist the
speaker means: self-irony, a dry comeback or punchline, mock-seriousness, an understatement, or an ironic question.
Set-up questions, sincere lines, instructions and plain information do not count. Those lines get the recast's extra
sentence "a touch of dry irony, understated – just a slight knowing hint in the voice, never theatrical, never
mocking".

**491 of 1,983 new lines** (25 %) count; the recast had 29 %. That is Adam 175, Tóno 17, Oto 66 13, Pali 13, then
2–12 for each of the adults. The list is in `irony_full.py`; on the page, filter "only dry irony".

Not marked, on purpose:

- the children, whose humour is literal child logic said seriously;
- Očko the robot, whose comedy comes from being literal and deadpan;
- Viktor, Lea, the narrator and SYSTEM;
- Rudo's stage exclamations;
- the tender ending lines.

## Check, retakes, flags

| | |
|---|---|
| first takes | 1,974 (9 more lines reuse a take) |
| verbatim after take 1 | 1,617 |
| retakes (exactly one each) | **196** lines whose transcript differed in meaning. Longer lines got "say every word exactly as written, in standard Slovak"; lines of 6 words or fewer got the clarity hint "pronounce every word fully and clearly, unhurried". The better take was kept. |
| verbatim after retakes | **1,747 of 1,983** |
| flagged for the ear | **113**, tagged "check" on the page and listed first (`flags.json`) |
| loudness | −15.6 to −17.0 LUFS per line, OGG Vorbis q4 mono 44.1 kHz |

These differences are not counted as errors (the same tolerances as the recast, extended):

- diacritics, punctuation and word boundaries;
- numbers that Scribe gives back as digits ("šesťdesiat" / "60", years, "7. decembra");
- spellings of the same sounds: y/i ("rydlo" / "ridlo"), d–t assimilation ("odtlačok" / "otlačok"), "Oto" / "Otto",
  "percent" / "%".

Spoken forms sent to the TTS (the subtitle text is unchanged): "Z-17" → "zet sedemnásť", "K-17" → "ká sedemnásť",
"=" → "rovná sa", „cca“ → "cé cé á". All-caps words (MONITOR, PÔVOD, NEDOLIEVAŤ POLIEVKU) are sent in normal case.

**The flags break down as follows:**

- **58 still differ after the one retake.** Many are the STT, not the voice. Listen especially to these:
  - **"ako" heard as "jak"** in 4 lines, 2 of them Fero's (`topic.TRH.extra 1.004`, `action.D02.x03`,
    `action.B01.002`, `topic.TONO.extra 2.002`). The "earthy" direction may pull Gemini toward dialect. If it really
    says "jak", remove "earthy" from Fero's direction.
  - **"Grobu" heard as "hrobu"** (`travel.S51.to_S07.first.001`); "Tóno" heard as "To ono" or "Tónos" (`action.E06.002`,
    `topic.OTO82.ambient 2.002`).
  - **Very short lines**, the known weak spot: "Veci?", "S kým?", "Aj s mäkčeňom?", "A čo mu bolo?", "A čo z toho ťa
    naučili v škole?".
  - **Single words:** "kulisa" (`action.I03.001`), "škôlku" (`entry.S37.001`, `action.Q10D.007`), "z návsi"
    (`topic.ZUZANA.extra 2.003`), "tupé rydlo" (`action.I09.005`), "Otovho" (`action.E04.001`), "vyčistil" heard as
    "vyčítal" (`cutscene.CS06.02.001`), "Natreli aj tú" (`topic.ZITA.ambient 2.x03`).
  - **Gender or person** of a verb: "píše" / "píšem" (`topic.DEZI.ambient 2.x03`), "zhasnem" / "zhasne"
    (`topic.JURAJ.extra 2.002`), "Aký bol Oto" / "Aké bolo to" (`topic.MIRA20.extra 3.001`).
  - The full list with Scribe's transcript is on the page.
- **33 extra filler words.** Scribe heard an "A", "No", "Hm", "Eh" or "Ach" before the line. The meaning is unchanged,
  so there was no retake, but listen whether it sounds natural.
- **22 timing flags.**
  - Adam's quick short questions run at 22–24 characters per second.
  - The SYSTEM lines with years ("Pôvod 1962. Hlas 1995. Súhlas 2020 …") and Karol's "1948 až 1990" are slow by
    character count only, because the years are spoken in full. That is expected.
  - Six lines have a beat of 1.4–1.9 s (Emil's "Štyri zastávky, moja vlastná skladba." has the longest).

**Fixing a line:** delete `art/voice/raw/full/<line_id>.json`, then run `python art/voice/tools/gen_full.py gen
--only "<line_id>"`, then `gen_full.py finalize` and `install`. To change a spoken form, add it to `gen_full.SPOKEN`.

## Settings: voice-over on/off

- **Settings → Audio** has a new toggle **"Hovorené dialógy"** right under the Voice volume slider. It defaults to on
  and has the caption "Postavy hovoria nahlas. Keď sú vypnuté, titulky sa posúvajú podľa dĺžky textu."
- The setting is saved with the others in `user://settings.cfg` as `audio/voice_over`. "Reset defaults" turns it back
  on.
- The new UI strings are code fallbacks (`UiString` in `SettingsScreen.cs`). The draft rows are in
  `docs/writing/out_v4/ui_voice.csv`; `ui.csv` was not edited.
- **Off:** `AudioService` plays no voice line. Switching it off stops a line that is already speaking. The dialogue
  presenter only waits while a voice line plays (`AudioService.VoicePlaying`), so with voice-over off lines advance on
  the text timing alone. The presenter needed no change.
- **Epilogue:** the epilogue shots are shown by `EndingSequence`, not by the dialogue presenter. They now call the new
  `AudioService.PlayVoice("epilogue.<n>.line")`, and the voice stops when the credits roll. This also respects the
  setting.
- **Code changes:**
  - `UI/Settings/UiSettings.cs`: the `VoiceOver` property, load, save and reset.
  - `UI/Menus/SettingsScreen.cs`: the toggle row and its two `UiString` fallbacks.
  - `Audio/AudioService.cs`: `PlayVoice`, the setting check, and stopping on change.
  - `UI/Cutscenes/EndingSequence.cs`: the epilogue voice.
  - `Diagnostics/DebugHarness.cs`: a QA flag `--voice-over on|off` for one run, not saved.
  - `Audio/README.md`: the documentation.
- **Harness test** (headless, Debug build): `-- --replay 1 --act G02 --lines --voice-over on|off --quit-after 40`, and
  `--play 3`.
  - With the voice-over on, every line logs `AUDIO voice <id>`.
  - With it off, every line logs `AUDIO voice off <id>`, no voice plays, and the lines advance with the same text
    timing (the timestamps of all nine G02 lines matched within 0.15 s).
  - The headless audio driver does not show the "wait for the voice" pause, so that pause needs a check in a windowed
    run.

## Install

At the end, `gen_full.py install` re-extracted the text from the live tables and checked it against every generated
line (0 changed). It then copied the 1,987 OGGs (the new lines, the reused takes and the 4 re-rendered SYSTEM lines)
into `src/game/assets/voice/`. File names are the line ids, spaces included.

**Not done here** (because of the parallel release work): the Godot import that creates the `.ogg.import` files. The
orchestrator runs `<console exe> --headless --path src/game --import` after the release work, then checks with
`-- --audio-report` and a short `--play` run that lines log `AUDIO voice …`. Until that import runs, the new files do
not play in the game.

**Text changes invalidate audio.** Each manifest line stores `text_sha1`. After a later text change, run
`extract_full.py` and then `gen_full.py gen`. `gen` regenerates exactly the lines whose text or casting changed, and
`install` refuses to copy while any line is stale.

## Spend

| | USD |
|---|---|
| Audition (50 short takes + Scribe) | 0.20 |
| Gemini TTS: 1,974 first takes + 196 retakes (111,673 characters) | 5.02 |
| Scribe v2: 2,170 checks | 1.23 |
| **Total, computed per call** | **6.45** |
| Logged in `art/spend-log.csv` under `voice/full/` (each row rounded to 3 decimals; includes about 16 takes lost when a first run hit a post-processing bug and was stopped and resumed) | 6.48 |
| Cap | 15.00 |

Trial, recast and full voice-over together come to ≈ $10.9.
