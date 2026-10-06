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
