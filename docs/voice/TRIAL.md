# AI voiceover trial: 2020 prologue (2026-10-06)

The owner asked whether AI voiceover is worth it for the dialogue. This trial voices **every spoken dialogue line
of the first part of the game** with synthetic Slovak voices, checks them automatically and puts them on a
listening page. Nothing has been copied into the game yet.

- Listening page: `docs/voice/trial.html` (open it locally; it plays the OGG files by relative path)
- Final files: `art/voice/trial/<line_id>.ogg` (237 files, 15.4 min, 9.7 MB) + `art/voice/trial/manifest.json`
- Tools: `art/voice/tools/` (`extract_lines.py`, `casting.py`, `voice_lib.py`, `ab_test.py`, `gen_all.py`,
  `retake.py`, `finalize.py`, `build_page.py`)

## Scope

The CURRENT texts of `src/game/localization/dialogue.csv` (overrides and overlay lines included), speakers and
play order from the effective game (`tools/content_ext.load_effective_game`: game.json + `dialogue_ext.json`):

- first-entry lines of S01–S10
- all lines of the actions G01–G11 incl. their overlay lines (G02–G05 sequences)
- the 2020 Grob side quests Q1A–Q1C (Lenka, Bodka's ball) and Q2A–Q2C (Jozef's notice)
- all topics of Ela, Dana, Mira 2020 (window), Roman, Lenka, Jozef that are available in the prologue
  (game.json ambient topics, their overlay extensions and the new `extra` topics)
- the spoken lines of CS01

237 lines, 11,787 characters, 2,118 words. Speakers: Adam 120, Ela 23, Mira 21, Lenka 19, Dana 19, Jozef 19,
Roman 12, device (SYSTEM) 4.

Left out on purpose:

- the dog Bodka's three `Haf!` lines (`action.Q1C.002`, `action.Q1C.x04`, `topic.LENKA.ambient 1.x01`). **SFX
  note:** play a short single bark (e.g. a new `sfx.json` id `dog_bark_short`, 2–3 takes) when these lines show;
  AudioService looks only for `assets/voice/<line_id>.ogg`, so either generate a bark as
  `assets/voice/<line_id>.ogg` for those three ids or map them to the SFX in AudioService.
- topics gated by later progress: `MIRA20.after` (needs F17), `MIRA20.extra 3` and `JOZEF.extra 3` (need C01),
  the C-actions of the return to 2020, and the bus first-ride lines to Dúbravka (`travel.S07.to_S51.first.*`).
- looks, UI, journal.

## Models compared

Candidates were taken from the fal model catalogue (`api.fal.ai/v1/models`, category text-to-speech) and priced
with the fal pricing API on 2026-10-06:

| model (fal endpoint) | price / 1000 chars | Slovak support |
|---|---|---|
| Gemini 3.8 Flash TTS (`google/gemini-3.8-flash-tts`) | $0.045 | no language parameter; the language is read from the text; style prompt per character |
| ElevenLabs Eleven v4 (`elevenlabs/tts/eleven-v4`) | $0.08 | `language_code: "sk"` |
| MiniMax Speech 2.8 HD (`fal-ai/minimax/speech-2.8-hd`) | $0.10 | `language_boost: "Slovak"` (Slovak is in the list) |
| not tested: Qwen Audio 3 TTS, xAI TTS | $0.05 / $0.015 | Slovak not in their language lists |
| not tested: Eleven v4 Turbo, Gemini 3.8 Flash Lite, MiniMax 2.8 Turbo | cheaper variants | would follow the result of their big brothers |

I cannot hear audio, so every take was judged by measurement:

- a **speech-to-text round trip with two independent STT models**: ElevenLabs Scribe v2 (`language_code slk`)
  and Whisper v3 large (fal `wizper`, `language sk`); word error rate (WER) against the script, also without
  diacritics (to separate "wrong word" from "the STT dropped a háček");
- duration, speaking rate (characters per second of speech), leading/trailing silence, the longest pause inside
  the line, clipping and peak level.

### A/B: the same 6 lines (Adam ×2, Ela, Mira ×2, Jozef)

| | Gemini 3.8 Flash | ElevenLabs v4 | MiniMax 2.8 HD |
|---|---|---|---|
| WER Scribe / Whisper | 2.1 % / 6.3 % | 4.2 % / 13.7 % | 2.1 % / 6.3 % |
| real mispronunciations (heard by both STT) | none | "Dana **ďu** má" for "Dana ju má"; "**Ve** pondelok" for "V pondelok"; "Ľučný" | a sentence break inside "Tašku. Nechaj babke…" |
| speaking rate | 12.9 chars/s | 12.8 | 13.5 |

ElevenLabs v4 dropped out (its premade voices are English voices speaking Slovak and it was the only one with
real wrong sounds). Gemini and MiniMax tied, so **both voiced the whole prologue** (237 lines each) for a
statistically meaningful comparison (2,118 words):

| measure | Gemini 3.8 Flash TTS | MiniMax Speech 2.8 HD |
|---|---|---|
| WER Scribe v2, best take | **1.2 %** | 1.8 % |
| WER Whisper v3, best take | 7.0 % | **6.0 %** |
| WER first take only (Scribe / Whisper) | 2.7 % / 8.9 % | 3.1 % / 7.7 % |
| lines transcribed verbatim by Scribe | **214 / 237** | 207 / 237 |
| retakes needed (automatic) | 50 | 39 |
| lines still flagged after retakes | **10** | 14 |
| mean speaking rate | **14.2 chars/s** (natural conversational Slovak) | 12.5 chars/s (slow, 8 % more audio) |
| longest pause inside a line | 1.0 s | 1.1 s |
| clipped lines | 0 | 0 |
| TTS cost for the whole prologue incl. retakes | **$0.60** | $1.28 |

Whisper is the noisier judge for both (it writes "telefon", "prístrežkom", "9." for "deviatej" for every model);
Scribe agrees with the script much more often, and the two disagree mostly about word boundaries and numbers.

## Chosen model: Gemini 3.8 Flash TTS

Why:

1. **Intelligibility is at the top**: the best Scribe WER (1.2 %), the most verbatim lines, the fewest lines left
   flagged; on Whisper it is within one point of MiniMax. No wrong sounds of the ElevenLabs kind.
2. **Casting control**: every character gets a prebuilt voice *plus* a style prompt (age, temperament, pace,
   "native Slovak, stress on the first syllable"). That is the only way among the three to get an
   80-year-old Mira and a 73-year-old Jozef from stock voices; MiniMax's stock voices are ageless and its voice
   design costs $3 per voice.
3. **Natural pace**: 14.2 characters per second fits quick, dry dialogue; MiniMax is noticeably slower.
4. **Half the price** of MiniMax and cheaper than ElevenLabs.

MiniMax is a good second; its takes are kept in `art/voice/takes/minimax/` and the page has a "Takes from"
switch, so the owner can compare both on every line by ear. The final judgement must be by ear anyway: voice
age, warmth and humour cannot be measured.

## Casting (one consistent stock voice per character, no imitation of a real person)

| character | brief (VOICES.md, game.json) | Gemini voice + direction | MiniMax alternative |
|---|---|---|---|
| Adam | 35, repairman, dry, warm, self-irony | Iapetus; relaxed, dry understated humour, warm, conversational | Casual_Guy |
| Ela | 40, volunteer coordinator, brisk | Kore; brisk, matter-of-fact, quick, kind but busy | Calm_Woman (speed 1.08) |
| Dana | 48, shop assistant, deadpan | Sulafat; calm, exact, deadpan, unhurried | Friendly_Person |
| Mira 2020 | 80, grandmother, engineer, sharp | Gacrux; 80-year-old retired engineer, sharp, dry, warm, slightly older thinner voice | Wise_Woman |
| Roman | 29, courier, relaxed | Achird; relaxed, friendly, never cynical | Young_Knight |
| Lenka | 37, neighbour with the dog, few words | Callirrhoe; economical, quietly amused | Lively_Girl |
| Jozef | 73, ceremonious, analogue pride | Algenib; warm, a bit ceremonious and proud, slower, slightly gravelly | Imposing_Manner (speed 0.95) |
| SYSTEM (ZVON device) | neutral synthetic | Schedar; even, calm, flat, slightly mechanical | Deep_Voice_Man |

Every Gemini direction starts with "Speak natural, native Slovak (Bratislava region) with correct Slovak stress
on the first syllable and clear long vowels; no foreign accent. Read the text verbatim." The exact settings are
in `art/voice/tools/casting.py`.

**Phone EQ:** Mira outside S06 speaks by phone (staging rule in game.json): G04 (5 lines at the gate S05) and her
CS01 line got a light telephone colour (300–3400 Hz band, mid presence, soft saturation). Her S06 lines through
the window are clean. A slight "behind glass" low-pass for S06 is a possible next step.

## Post-processing (local, `voice_lib.finish`)

Trim silence (−42 dB below the line's peak, 60 ms pad before, 100 ms after) → DC removal → phone EQ where
needed → loudness to −16 LUFS integrated (ffmpeg ebur128) with a soft limiter at −1.5 dBFS → 8 ms fade in,
40 ms fade out → OGG Vorbis q4, mono, 44.1 kHz. Result: −16.0 to −17 LUFS per line, peaks ≤ −1.1 dBTP.

## Problems found

- **Names come out right**: "Hrušková / Hruškovej", "Čierna Voda / v Čiernej Vode", "Lúčny koník", "Jozef",
  "ZVON" were transcribed verbatim by Scribe for the Gemini takes. "Bodka" is transcribed "Botka" in some takes,
  which is the correct Slovak pronunciation (voicing assimilation d→t before k), not an error.
- **"Sokolíkova 1995"** (action.G07.001) is heard as "Sokolíková" by both STT models for all three TTS models:
  the final -a is probably lengthened or stressed. Listen; if wrong, write it as "Sokolíkova ulica" in the TTS
  text or retake.
- **All-caps words** (ZVON, NEPREPISOVAŤ, NEOTVÁRAŤ) would be spelled letter by letter; `tts_text()` sends them
  in normal case. Typographic quotes are dropped (Gemini then pauses a little: "nálepka. Sokolíkova").
- **Very short lines** (1–4 words: "A zapla ho?", "Veľa adries dnes?", "A vypila si ju?") are the weak spot of
  every model: they were mumbled or swallowed in some takes. Three got directed retakes ("pronounce every word
  fully, unhurried"); two are fine now, "A zapla ho?" is right for Scribe, Whisper joins it to "zaplaho".
- **Stress and intonation** cannot be measured by STT. The style prompt asks for first-syllable stress; listen
  to questions especially (the A/B and the "check" tags on the page).
- 10 lines keep a "check" tag (mostly STT disagreement, not necessarily wrong audio):
  `topic.ROMAN.extra 1.005`, `action.Q1A.x05`, `topic.LENKA.ambient 2.x02`, `topic.LENKA.extra 3.004`,
  `action.G02.x05` (fast: 22 chars/s, brisk Ela), `topic.ELA.extra 1.004` ("balí tu" vs "balitu"),
  `topic.MIRA20.extra 2.003`, `topic.JOZEF.ambient 2.x02`, `action.Q2C.001` (Whisper writes digits),
  `action.Q1B.001` ("obhryzená" heard as "obryzená").
- Numbers: both STT models give "1995" back as digits, so the year is spoken as a number, but whether it is read
  as a year (*tisícdeväťstodeväťdesiatpäť*) must be checked by ear; if a line needs a specific reading, write the
  number out in the TTS text.
- "Grob" alone (topic.ROMAN.extra 2.002) is heard as "Grób" by Scribe: a possible vowel lengthening, listen.
- Gemini has no seed: a retake is a new performance, so a fixed line may sound a little different from its
  neighbours. Keep the style prompts unchanged between batches for consistency.
- fal's file CDN timed out a few downloads under 28 parallel requests; the generator is resumable and the
  two-process run covered them.

## Cost

| | USD |
|---|---|
| Gemini, all 237 lines incl. 50 automatic + 6 directed retakes | 0.67 (some lines were generated twice by the two parallel workers) |
| MiniMax, all 237 lines incl. retakes | 1.48 |
| ElevenLabs v4 (A/B only) | 0.05 |
| STT checks: Scribe v2 (≈ $0.0005 per line) | 0.32 |
| STT checks: Whisper (logged at a conservative $0.002 per call) | 1.20 |
| **total logged under `voice/` in art/spend-log.csv** | **3.71** (budget 15) |

Per line with Gemini: about **$0.0025** (50 characters average, retakes included).

Full game estimate at the same average line length, +15 % retakes:

- 1,090 spoken lines: ≈ **$2.80** TTS (+ ≈ $0.60 Scribe check)
- ~2,500 lines (with the longer dialogues): ≈ **$6.50** TTS (+ ≈ $1.30 Scribe check, + ≈ $5 if the Whisper
  second opinion is kept); with the longer lines of later eras (1960/1995 dialogues are wordier) budget about
  **$10–15** in total.

Money is not the constraint. The real cost is listening: ~2,500 lines are roughly 2.7 hours of audio, and every
line that sounds wrong needs a retake or a text tweak. More characters also need casting (about 45 more
speakers; Mira, Tóno, Jana and Oto at several ages need related but distinct voices).

## How to put the files into the game

The AudioService already plays `res://assets/voice/<line_id>.ogg` on the Voice bus when the file exists
(`src/game/scripts/Audio/README.md`). After the current text apply finishes, the orchestrator:

1. copies `art/voice/trial/*.ogg` to `src/game/assets/voice/` (file names are the line ids, spaces included,
   e.g. `topic.ELA.ambient 1.001.ogg`);
2. runs a Godot import so the `.ogg.import` files are created;
3. checks with `-- --audio-report` that the lines play.

**Text changes invalidate audio.** The trial was made from the texts of 2026-10-06 ~22:00. Before copying, compare
`manifest.json` `text` with the current `dialogue.csv`; for every line whose text changed, regenerate
(`python art/voice/tools/gen_all.py gemini --only "<line_id>"` after deleting its `art/voice/raw/gemini/<line_id>.json`,
then `finalize.py gemini`). A future pipeline step should store the text hash next to each OGG.

Repository note: `art/voice/raw/` holds all raw takes (≈ 75 MB, mostly WAV) and their JSON check records; it is
an intermediate folder and does not need to be committed (the JSON records are what `build_page.py` reads).
