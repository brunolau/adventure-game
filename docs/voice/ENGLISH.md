# English dub (2026-10-10)

Owner, 2026-10-10: "now make english dubbing, for the android version include only english dubbing".

Every key the Slovak dub speaks now has an English recording: the 2,217 dialogue lines, the 567 look bubbles (room
looks, item descriptions, locked exits, puzzle answers) and the 32 Standard/Hard variants. Each character keeps the
voice of the Slovak dub; only the language changed. Nobody has listened to it yet: the checks below are automatic, and
the owner's ear decides.

- **Listening page:** `docs/voice/en.html`. Open it from the repository folder, because it plays the recordings by
  relative path from `src/game/assets/`. "EN" plays the English take and "SK" the Slovak original beside it. The takes
  to listen to first are at the top, then one sample per voice, then every line by era and room with "Play room".
- **In the game:** `src/game/assets/voice_en/` (2,622 OGG files, 115.1 MB, and `aliases.json`). The Slovak original
  stays in `src/game/assets/voice/` (120 MB).
- **Record:** `art/voice/en/manifest.json` (every key: speaker, voice, English and Slovak text, the transcript and the
  check) and `art/voice/en/flags.json`. Raw takes and finished OGGs are in `art/voice/raw/en/` and
  `art/voice/takes/en/` (git-ignored; the game folder is the tracked copy).
- **Tools** (`art/voice/tools/`): `en_dub.py plan | gen | report | retake | recheck | rerender | finalize | install`,
  `en_dub_manifest.py`, `en_dub_page.py`. They reuse `voice_lib.py`, `casting_full.py` and the post-processing of
  `gen_full.py`.

## What plays when

| build | dubs in the build | what the player hears |
|---|---|---|
| Windows, Linux, macOS | Slovak and English | the dub of the text language: Slovak texts → Slovak voices, English texts → English voices. Settings → Sound has a new row „Jazyk dabingu“ / "Voice language": as the texts (default), Slovenčina, English. So English subtitles with the original Slovak voices are one click away, and the other way round. |
| Android (APK, Play bundle, emulator APK) | English only | English voices, with Slovak or English subtitles. The row is not shown, because there is nothing to choose. „Hovorené dialógy“ still switches the voices off. |

Rule in code (`AudioService.VoiceLanguage`): the player's choice, else the language of the texts; when the build does
not carry that dub, the one it carries. A build "carries" a dub when its folder has `aliases.json`. The Android
presets leave out `assets/voice/*` (`tools/release_assets.py`, `NO_SLOVAK_DUB`). iOS is not built; its preset still
has both.

The two new Slovak UI texts („Jazyk dabingu“, „Ako texty“) are drafts in `docs/writing/out_v7/ui_voice_language.csv`.
They show from code until the owner approves them, like the touch texts.

## Method

The same as the Slovak dub (`docs/voice/FULL.md`): Gemini 3.8 Flash TTS stock voices, one ElevenLabs Scribe v2
transcript per take, exactly one retake when the transcript differs in meaning, then trim, the call / tape / device
colour, −16 LUFS and OGG Vorbis q4 mono. No voice is cloned and no real person is imitated.

- **Script.** The keys, speakers, colours and the dry-irony marking come from the Slovak manifests
  (`art/voice/full/manifest.json`, `std_manifest.json`). The text is the `en` column of the live tables.
- **Casting.** Unchanged: all 58 speaker roles keep their stock voice and their character direction (age, temperament,
  child direction). Adam is Achird in both languages, Mira Gacrux, the narrator Callirrhoe, and so on
  (`casting_full.py`).
- **Language sentence.** The Slovak direction starts with "Speak natural, native Slovak (Bratislava region) …". The
  English one starts with: "Speak natural, native British English with a neutral, contemporary accent (standard
  southern British, neither posh nor regional); no foreign accent. Read the text verbatim." British, because the
  English texts are British (`docs/translation/README.md`).
- **Dry irony.** The same 681 takes carry the recast's sentence "a touch of dry irony, understated …".
- **Slovak names.** 113 takes contain a Slovak place name or word. Their direction says how to pronounce it:
  Ivanka (pri Dunaji), Dubravka, Karlova Ves, Cierna Voda, Biela Put, Chopok, Funitel, Priehyba, Jasna, Sokolikova,
  Svantnerova, Petrzalka, Ruzinov, Vrbicke, Mileticka, Kamenne, Grob, lángos, Druhý život, LEAL (a word, two
  syllables) and ZVON (a word). The list with the spoken hints is `en_dub.HINTS`.
- **Spoken forms** (the subtitle is unchanged): "Z-17" → "Zed-seventeen", "K-17" → "K-seventeen", "3–2–6" → "three,
  two, six", "0–9" → "zero to nine", "9–17" → "nine to five", "3 × 4" → "three by four". All-caps words are sent in
  normal case, so MONITOR and ZVON are read as words.
- **Same sentence, one take.** 194 keys share a recording with an earlier key of the same speaker and colour (178
  looks, mostly locked exits, and 16 dialogue lines). `voice_en/aliases.json` maps them.
- **Not voiced:** Dotty's "Woof!" lines, UI, the journal and the place names shown at exits, as in Slovak.

## Accent check

I cannot hear the takes. Before the full run, 23 pilot takes of 22 speakers were given to an audio-capable model
(Gemini 2.5 Flash through OpenRouter) with the question which accent the speaker has. All 23 came back "British,
native", with naturalness 4 or 5 of 5. That is a rough check of the accent only; its guesses of age and sex were
often off, and it says nothing about acting.

## Check, retakes, flags

| | |
|---|---|
| keys / recordings | 2,816 / 2,622 (2,201 dialogue, 389 looks, 32 variants) |
| audio | 195 min (3 h 15 min); the Slovak dub is about 3 h 2 min |
| characters sent | 173,587 |
| retaken once | 141 takes whose transcript differed in meaning |
| clean after that | 2,555 of 2,622 |
| flagged for the ear | **57**: 24 still differ, 27 have an added word, 6 timing |
| loudness | −16 LUFS per line, as the Slovak dub |

An English take is on average as long as its Slovak take (median 1.05 times), although the English text has 1.2 times
as many characters.

Not counted as differences: British and American spellings of one word (neighbour / neighbor, metres / meters, kerb /
curb), contractions written out (it'll / it will), numbers as digits, words that sound alike (write / right), a
weak "have" or "is" the transcript did not hear (I've / I), spoken short forms ('em, gonna; Frank the market seller
uses some), and the spellings the transcript invents for names (Dotty / Dottie, Gran / Graham, Paulie / Porly).

**The 24 that still differ.** Many are the transcript, not the voice. Listen to these first:

- `look.S39.plate.variant1`: "plate … rule" heard as "play … raw".
- `action.I01.003.std`: "Here's a slip" heard as "is a slip".
- `action.Q5B.x01`: "White, unused." heard as "Why unused?".
- `entry.S60.001`: "The pupils' technical exhibition" heard as "The People's Technical Exhibition".
- `topic.SIMON.ambient 2.002`: "give it a guard" heard as "give it a go".
- `action.B14.002`: "in the shot" heard as "in the shop".
- `action.I14.x02`: "record" heard as "recall".
- `look.S10.ambient 1`: "three eras" heard as "three erasers".
- `action.F09.x03`: "Both r's." heard as "Both ours."
- Very short lines, the known weak spot: "Up." heard as "Yep", "And he?" heard as "Annie?".
- The rest are one small word (a / the, a missing "it" or "and").

**27 added words.** The transcript has an "uh", "oh", "hm" or "and" that is not in the text. The meaning is the same,
so there was no retake; listen whether it sounds natural.

**6 timing flags.** Four takes have a pause of about 1.5 s (`entry.S05.001`, `action.F11.008`, `action.F17.x01`,
`look.S32.ambient 2`). Two are slow: "But that's silence." (`topic.LEA95.extra 1.003`, 2.9 s) and "I did. He ate it."

**Slovak names, 14 takes.** The transcript did not recognise the name, which says little about how it sounds:
"Cierna Voda" came back as "a churn of water" and "chain of order", "Vrbicke" as "Verbitske", "Vrbice" and
"Vrbitza", "Petrzalka" as "Petrijalka" and "Petrin", "Jasna" as "Jaszna", "Sokolikova" as "Sokolnikova", "zvon" once
as "one". These are listed on the page under the names; they are worth a listen in the game (the first one is in
Roman's talk in Grob and on the first bus ride back).

**Fixing a line:** delete `art/voice/raw/en/<line_id>.json`, run `python art/voice/tools/en_dub.py gen --only
"<line_id>"`, then `finalize` and `install`, then the Godot import (`build.bat` runs it). A changed English text is
taken again by `gen` on its own, and `install` refuses while a line is stale. To change how a name is said, edit
`en_dub.HINTS`.

## Spend

| | USD |
|---|---|
| Gemini TTS: 2,622 first takes and 141 retakes | 8.23 |
| Scribe v2: 2,763 transcripts | 1.78 |
| **Total, computed per call** | **10.00** |
| Logged in `art/spend-log.csv` under `voice/en/` (each row rounded to 3 decimals; three takes were charged but not logged, because the log file was locked for a moment) | 9.96 |
| Accent check (23 clips, audio model) | 0.01 |
| Cap of the run | 16.00 |

All fal spend of the project so far: USD 263.48 of about USD 350.
