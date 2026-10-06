"""Voice casting per model. Stock voices only (no cloning, no imitation of a real person).

Gemini voices are prebuilt and steered by style_instructions (age, temperament, Slovak pronunciation);
ElevenLabs v4 uses its premade voices with language_code 'sk'; MiniMax uses its system voices with
language_boost 'Slovak'.
"""

SK = ("Speak natural, native Slovak (Bratislava region) with correct Slovak stress on the first syllable "
      "and clear long vowels; no foreign accent. Read the text verbatim. ")

GEMINI = {
    "ADAM": {"voice": "Iapetus", "style": SK + "A 35-year-old repairman: relaxed, dry understated humour, warm, "
             "conversational, medium pace, never theatrical."},
    "ELA": {"voice": "Kore", "style": SK + "A 40-year-old volunteer coordinator: brisk, matter-of-fact, quick pace, "
            "kind but busy, practical."},
    "DANA": {"voice": "Sulafat", "style": SK + "A 48-year-old shop assistant: calm, exact, deadpan, a little dry "
             "wisdom, unhurried."},
    "MIRA20": {"voice": "Gacrux", "style": SK + "An 80-year-old woman, a retired engineer: sharp, dry and warm, "
               "slightly older and thinner voice, precise diction, short sentences, no sentimentality."},
    "ROMAN": {"voice": "Achird", "style": SK + "A 29-year-old courier: relaxed, friendly, easy-going, never cynical."},
    "LENKA": {"voice": "Callirrhoe", "style": SK + "A 37-year-old neighbour walking her dog: economical with words, "
              "quietly amused, easy-going."},
    "JOZEF": {"voice": "Algenib", "style": SK + "A 73-year-old man: warm, a bit ceremonious and proud, slower, "
              "slightly gravelly older voice, polite."},
    "SYSTEM": {"voice": "Schedar", "style": SK + "A neutral synthetic device announcement: even, calm, precise, "
               "flat intonation, slightly mechanical."},
}

ELEVEN = {
    "ADAM": {"voice": "Chris"},
    "ELA": {"voice": "Alice"},
    "DANA": {"voice": "Matilda"},
    "MIRA20": {"voice": "Lily", "stability": 0.6},
    "ROMAN": {"voice": "Liam"},
    "LENKA": {"voice": "Sarah"},
    "JOZEF": {"voice": "Bill"},
    "SYSTEM": {"voice": "River", "stability": 0.85},
}

MINIMAX = {
    "ADAM": {"voice": "Casual_Guy"},
    "ELA": {"voice": "Calm_Woman", "speed": 1.08},
    "DANA": {"voice": "Friendly_Person"},
    "MIRA20": {"voice": "Wise_Woman"},
    "ROMAN": {"voice": "Young_Knight"},
    "LENKA": {"voice": "Lively_Girl"},
    "JOZEF": {"voice": "Imposing_Manner", "speed": 0.95},
    "SYSTEM": {"voice": "Deep_Voice_Man", "emotion": "neutral"},
}

MODELS = {
    "gemini": ("google/gemini-3.8-flash-tts", GEMINI),
    "eleven": ("elevenlabs/tts/eleven-v4", ELEVEN),
    "minimax": ("fal-ai/minimax/speech-2.8-hd", MINIMAX),
}


# --------------------------------------------------------------------------- recast 2026-10-06 (owner feedback)
# Owner after the trial: swap the voices of Adam and Roman (Roman's voice is the better one for Adam), make the
# four women clearly different from each other, and give the sarcastic lines a tiny touch more irony.
# GEMINI above stays as the v1 record; GEMINI_V2 is the current casting (art/voice/tools/recast.py).

GEMINI_V2 = {
    # Adam takes Roman's v1 voice and a direction close to Roman's (relaxed, friendly, easy-going) plus his own traits.
    "ADAM": {"voice": "Achird", "style": SK + "A 35-year-old repairman: relaxed, friendly, easy-going and warm, "
             "conversational, medium pace, dry understated humour, never theatrical, never cynical."},
    # Roman takes Adam's v1 voice, with the clear conversational pacing Adam's v1 direction had.
    "ROMAN": {"voice": "Iapetus", "style": SK + "A 29-year-old courier: relaxed, warm and friendly, conversational, "
              "medium pace, easy-going, never cynical."},
    # Four women, spread in pitch, timbre and pace (chosen by the audition in art/voice/recast/audition/).
    "ELA": {"voice": "Despina", "style": SK + "A woman in her mid-forties who runs the volunteer pick-up point: brisk "
            "and energetic, quick pace but every word clear, firm, crisp and matter-of-fact, kind but busy, practical; "
            "a bright, alert, slightly higher voice."},
    "DANA": {"voice": "Vindemiatrix", "style": SK + "A woman in her early fifties, a village shop assistant at a counter "
             "window: warm, lower and slightly husky voice with a little rasp, calm and unhurried, deadpan, dry "
             "counter wisdom, friendly underneath."},
    "MIRA20": {"voice": "Gacrux", "style": SK + "An 80-year-old grandmother, a retired engineer: an older woman's "
               "voice, a little thinner with age, but alert, sharp and quick-witted; crisp, precise diction, a "
               "steady natural pace (old, not slow), short sentences, dry and warm, no sentimentality."},
    "LENKA": {"voice": "Leda", "style": SK + "A cheerful woman in her mid-thirties walking her dog: a bright, "
              "light, youthful and higher voice, smiling and amused, lively intonation, easy-going, natural "
              "medium-quick pace."},
    "JOZEF": GEMINI["JOZEF"],
    "SYSTEM": GEMINI["SYSTEM"],
}

# Added to the style prompt of the lines classified as dry irony / sarcasm (recast.DELIVERY).
IRONY = (" Delivery for this line: a touch of dry irony, understated - just a slight knowing hint in the voice, "
         "never theatrical, never mocking.")
