# AI voiceover trial: 2020 prologue (2026-10-06)

The owner asked whether AI voiceover is worth it for the dialogue. This trial voices **every spoken dialogue line
of the first part of the game** with synthetic Slovak voices, checks them automatically and puts them on a
listening page. **Recast 2026-10-06** (owner feedback after listening; section at the end): Adam and Roman swapped
voices, the four women were recast, the dry or sarcastic lines got a touch of irony, and 217 lines were regenerated.
The current files (v2 where recast, v1 elsewhere) are also in `src/game/assets/voice/`.

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

## Casting v1 (superseded for six characters by the recast at the end; one consistent stock voice per character, no imitation of a real person)

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
`manifest.json` `text` with the current `dialogue.csv`; for every line whose text changed, run
`extract_lines.py`, then regenerate. Since the recast (manifest version 2): for Adam, Roman, the four women and the
dry-irony lines delete `art/voice/raw/gemini_v2/<line_id>.json` and run
`python art/voice/tools/recast.py gen --only "<line_id>"`, then `recast.py finalize` and `recast.py install`; for
Jozef's other lines and SYSTEM use `gen_all.py gemini --only "<line_id>"` (it now skips recast lines) and copy the new
`art/voice/takes/gemini/<line_id>.ogg` into `art/voice/trial/` by hand. `finalize.py` refuses to overwrite the v2
manifest. A future pipeline step should store the text hash next to each OGG.

Repository note: `art/voice/raw/` holds all raw takes (≈ 75 MB, mostly WAV) and their JSON check records; it is
an intermediate folder and does not need to be committed (the JSON records are what `build_page.py` reads).

## Recast 2026-10-06

The owner listened to the trial and asked: swap the voices of Adam Hruška and Roman Kováč (Roman's voice is the
better one, so Adam gets it); give sarcastic lines a little more irony ("not too much, just a tiny bit"); make the
female voices more varied. Same model (Gemini 3.8 Flash TTS), same shared Slovak pronunciation prompt, same
post-processing. Tools: `art/voice/tools/recast.py` (casting in `casting.py` → `GEMINI_V2`, `IRONY`),
`audition.py`, `voice_features.py`, `recast_stats.py`.

### New casting

I cannot listen, so pitch, timbre and pace were measured on the raw takes (median per character; pitch by YIN,
timbre as spectral centroid). In v1 three of the women sat within 2 semitones of each other (Lenka 153 Hz, Dana
169 Hz, Ela 170 Hz), and Ela and Dana had the same pitch.

| character | v1 voice | **v2 voice** | v2 direction (after the shared Slovak prompt) | pitch v1 → v2 | timbre v1 → v2 | pace v1 → v2 (chars/s) |
|---|---|---|---|---|---|---|
| Adam (35) | Iapetus | **Achird** (Roman's v1 voice) | 35-year-old repairman: relaxed, friendly, easy-going and warm, conversational, medium pace, dry understated humour, never theatrical, never cynical (Roman's v1 direction plus Adam's traits) | 110 → 115 Hz | 896 → 986 Hz | 14.3 → 15.7 |
| Roman (29) | Achird | **Iapetus** (Adam's v1 voice) | 29-year-old courier: relaxed, warm and friendly, conversational, medium pace, easy-going, never cynical | 132 → 118 Hz | 901 → 992 Hz | 15.7 → 16.1 |
| Lenka (30s, cheerful) | Callirrhoe | **Leda** (youthful) | cheerful woman in her mid-thirties: bright, light, youthful, higher voice, smiling and amused, lively intonation, natural medium-quick pace | 153 → **184 Hz** | 1004 → 1279 Hz | 13.4 → 13.5 |
| Ela (40s, brisk) | Kore | **Despina** | woman in her mid-forties who runs the pick-up point: brisk and energetic, quick pace but every word clear, firm, crisp, matter-of-fact, kind but busy; bright, alert, slightly higher voice | 170 → **163 Hz** | 1118 → 1097 Hz | 18.5 → 16.9 |
| Dana (50s, warm, a bit raspy) | Sulafat | **Vindemiatrix** (darkest timbre in the audition) | woman in her early fifties, shop assistant at a counter window: warm, lower, slightly husky voice with a little rasp, calm and unhurried, deadpan, friendly underneath | 169 → **137 Hz** | 1249 → **936 Hz** | 12.0 → 12.1 |
| Mira 2020 (about 80, engineer) | Gacrux | **Gacrux** (kept: the only mature voice; new direction) | 80-year-old grandmother, retired engineer: older, a little thinner voice, but alert, sharp and quick-witted; crisp, precise diction, steady natural pace (old, not slow), short sentences, dry and warm | 129 → **124 Hz** | 1192 → 1177 Hz | 12.3 → 12.5 |
| Jozef, SYSTEM | Algenib, Schedar | unchanged | unchanged | | | |

The women now span 124–184 Hz, about 7 semitones. Lenka and Ela are 2 semitones apart, Ela and Dana 3. Dana and
Mira are only 1.7 apart, but their timbre differs a lot: Dana is the darkest voice, Mira the thinnest, and Mira's
lines outside S06 also have the phone EQ. Each woman also has her own pace. Ela is quick (16.9). Lenka is lively
(13.5, with the widest melody in the audition). Dana and Mira are unhurried (12.1 / 12.5).

**Audition** (`art/voice/recast/audition/`, playable on the page): one real line per role, spoken by each candidate
stock voice with the role's new direction, then measured and checked by Scribe.

- Lenka: Leda 211 Hz, Laomedeia 205, Aoede 193, Zephyr 173, Autonoe 173 → Leda (highest, widest melody).
- Ela: Despina 175 Hz, Erinome 164, Kore 162, Pulcherrima 126 → Despina (midway between Lenka and Dana).
- Dana: Sulafat 159 Hz, Achernar 155, Vindemiatrix 143 with the darkest timbre (852 Hz centroid) → Vindemiatrix.
- Mira: Gacrux 134 Hz, Vindemiatrix 153, Achernar 162 → Gacrux. Her first new direction ("measured pace, slightly
  creaky") made her too slow (9.3 chars/s against 12.5 in v1). I changed it to "steady natural pace (old, not
  slow)" and re-auditioned: 11.5 chars/s.

### Dry irony / sarcasm

I read and classified every scoped line. A line counts when its humour lives in a wry twist the speaker means:
self-irony, a dry comeback, mock-seriousness, an understatement or an ironic question. Set-up questions, sincere
lines, instructions and plain information do not count. The lines that count get one extra sentence in the style
prompt:

> Delivery for this line: a touch of dry irony, understated - just a slight knowing hint in the voice, never
> theatrical, never mocking.

**69 lines** count: Adam 32, Ela 12, Mira 9, Dana 5, Lenka 5, Roman 3, Jozef 3. The manifest lists them (`delivery`
per line, plus `recast.delivery_lines` with the kind of irony), and the page tags them "dry irony".

- Adam: entry.S01.001, action.G01.001, topic.ROMAN.extra 2.003, action.Q1A.x04, topic.LENKA.ambient 1.003,
  action.G02.003, topic.ELA.extra 2.003, topic.ELA.extra 2.005, topic.ELA.extra 3.005, action.G03.x04,
  topic.DANA.ambient 1.003, topic.DANA.ambient 2.002, entry.S06.001, action.G05.x01, action.G05.x05,
  topic.MIRA20.ambient 1.003, topic.MIRA20.ambient 2.002, action.G06.001, entry.S07.001, entry.S08.001,
  action.Q1B.001, action.Q1C.001, action.Q1C.004, action.Q1C.x02, entry.S09.001, entry.S10.001, action.G08.002,
  action.G09.002, action.G10.003, action.G11.002, cutscene.CS01.02.002, cutscene.CS01.03.001
- Mira: action.G04.x03, action.G05.x02, action.G05.x04, topic.MIRA20.ambient 1.x01 / 1.x03 / 2.003 / 2.x02,
  topic.MIRA20.extra 1.004 / 2.004
- Ela: action.G02.x03, action.G02.004, action.G02.x05, topic.ELA.ambient 1.x01 / 1.x03 / 2.x02 / 2.x04,
  topic.ELA.extra 1.006 / 2.002 / 3.004 / 3.006, action.Q2B.x03
- Dana: action.G03.004, topic.DANA.ambient 1.x01 / 1.x03, topic.DANA.extra 1.004 / 3.004
- Lenka: action.Q1A.001, action.Q1A.x02, topic.LENKA.extra 1.004 / 2.004, action.Q1C.x03
- Roman (wry, never cynical): topic.ROMAN.ambient 1.x01 / 2.x02, topic.ROMAN.extra 2.004
- Jozef (gentle irony about technology): action.Q2A.x02, topic.JOZEF.ambient 1.x03, action.Q2C.003

Measured effect: the irony lines are a little slower (13.7 against 15.4 chars/s on average; Adam 13.6 against
16.3). They also have a slightly longer beat before the punchline (Adam's mean longest pause 0.42 s against
0.17 s). No irony line pauses longer than 1.1 s. Jozef's three lines changed the most (9.4 against 11.0 chars/s). Only
an ear can tell whether that is "a tiny bit". The page has a Before / After switch and a "play before" button on
every recast line.

### Regeneration and check

Only the lines whose voice or delivery changed were regenerated: **217 of 237** (all 214 lines of Adam, Roman, Ela,
Dana, Mira and Lenka, plus Jozef's 3 ironic lines). Jozef's other 16 lines and the 4 SYSTEM lines stay v1.

- Each line got one Gemini take and one ElevenLabs Scribe v2 check (no Whisper). A transcript counts as different
  when a word is substituted, missing or garbled. Differences that are ignored: diacritics, punctuation, word
  boundaries ("poobede" / "po obede") and known STT spellings ("Botka", digits).
- 182 of the 217 first takes were transcribed verbatim. 19 lines got **exactly one retake**: the ones whose
  transcript differed, plus "My? Kto my?", which came back with a lengthened vowel. Short lines (≤ 6 words) got the
  v1 clarity hint "Pronounce every word fully and clearly, unhurried." The better take was kept. 14 of the 19
  retakes fixed the line.
- Result: 194 of 217 lines verbatim, Scribe WER 1.45 % (0.99 % ignoring diacritics). The same lines in v1: 1.24 %.
- Post-processing is the same as in v1: trim, DC removal, phone EQ for Mira's G04 and CS01 lines, −16 LUFS, soft
  limiter at −1.5 dBFS, fades, OGG q4. One change: Adam's new voice has sharper peaks, so a single limiter pass
  left many of his lines at −17 to −19 LUFS. `recast.finish` now repeats the loudness step until the line is
  within 0.3 LU of −16. Result: −16.0 to −16.9 LUFS (one 1.5 s line at −17.5), peaks ≤ −0.7 dBTP.

**Flagged for the owner (8 lines, tagged "check" on the page, `recast.flagged` in the manifest):**

Still different after the one retake (5):

- `topic.ROMAN.ambient 1.001` Adam: "Veľa adries dnes?" heard as "Veľádrie dnes". "adries" may be swallowed (short
  lines were a weak spot in v1 too).
- `topic.ELA.ambient 2.x01` Adam: "A vypila si ju?" heard as "A vybilas ju?". "si" is reduced, and p sounds like b.
- `topic.DANA.ambient 1.x03` Dana: "Lebo si ju šetrí na teba." heard as "Lebo si už šetrí".
- `action.Q2B.x03` Ela: "pripni" heard as "pripnij" in both takes (and in v1 with Kore). Probably a glide before
  "správne", but listen.
- `action.G08.001` Adam: "Poistka" heard as "Pojistka" in both takes. The other "poistka" lines are fine. If it
  sounds Czech, changing the spelling in the TTS input would fix it.

Meaning unchanged, so no retake, but listen (3):

- `topic.DANA.extra 2.001`: Scribe hears an extra "A" before Adam's question.
- `topic.DANA.extra 2.003`: an extra "No".
- `topic.MIRA20.ambient 2.002`: an extra "Hm," before the ironic question.

Spelling-only differences (no action): `topic.MIRA20.extra 1.003` "nezspajkoval" and `action.Q1B.001` "obhrizená"
(y and i sound the same). `action.Q2C.001` (Jozef, v1, not regenerated) keeps its v1 "check" tag.

**Also listen for:**

- Adam and Roman are now close in pitch: 116 Hz median on Adam's plain lines, 120 Hz for Roman. That matters in
  Roman's topics, where they alternate.
- Adam's Achird sits about 2 semitones lower than Roman's v1 lines in the same voice (132 Hz). The likely cause is
  the age and dry-humour cues in Adam's direction.

Possible fixes, if needed:

- If Adam should sound exactly like v1 Roman: regenerate his 120 lines with Roman's v1 wording only (about $0.30
  with Scribe).
- If Roman needs more contrast: a younger, brighter direction for his 12 lines (about $0.03).

### Files

- `art/voice/trial/<line_id>.ogg`: the current files (v2 for the 217 recast lines).
- `art/voice/trial/manifest.json`, fields per line: `version` (1 or 2), `voice`, `style_instructions`,
  `delivery`, `delivery_kind`, `stt` (Scribe only for v2, plus `flag`) and `before` (v1 voice, file and STT). Top
  level: `version: 2`, `versions` and `recast` (casting v1/v2, irony direction, delivery lines, flagged lines,
  spend).
- `art/voice/takes/gemini_v1/`: frozen v1 files of the 217 recast lines (the page's "Before").
- `art/voice/takes/gemini_v2/` and `art/voice/raw/gemini_v2/`: the new takes and their JSON check records.
- `art/voice/recast/`: audition, `flags.json`, measured features v1/v2, generation log.
- `docs/voice/trial.html`, rebuilt. New on the page:
  - a "Recast lines: Before / After" switch, and "play before/after" on each recast line;
  - the filters "only recast lines" and "only dry-irony lines";
  - the recast summary, the flags, casting v1 → v2, the measured features and the audition.
- **Game:** the 217 regenerated OGGs replaced the trial files of the same names in `src/game/assets/voice/`. All
  237 files there now match `art/voice/trial/`. Their `.ogg.import` files are unchanged; the next Godot import (not
  run here) reimports the changed sources.

Texts: all 237 lines were compared with `dialogue.csv` right before generation and again before the copy. No
differences.

### Cost

| | USD |
|---|---|
| Audition (16 short TTS takes + Scribe) | 0.07 |
| Gemini TTS for 217 lines + 19 retakes (11,645 chars) | 0.52 |
| Scribe v2 checks (236 takes) | 0.13 |
| **Recast total**, computed per call (art/spend-log.csv rounds each row to 3 decimals and shows 0.711 under `voice/recast/`) | **0.72** (cap 5) |
| Trial + recast | ≈ 4.43 |
