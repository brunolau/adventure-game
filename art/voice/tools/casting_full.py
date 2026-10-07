"""Full voice-over casting (2026-10-07): every speaker of every era, Gemini 3.8 Flash TTS stock voices only
(no cloning, no imitation of a real person). The prologue casting (casting.GEMINI_V2, approved after the recast) is
kept unchanged. The same person at different ages keeps the same stock voice with an age direction.

CAST[speaker] = {"voice", "style", "who", "age", "family"}; CHILD_CANDIDATES feeds audition_full.py; the voices
chosen by the audition are written into CAST (see the comments) and into art/voice/full/casting.json.
"""
from __future__ import annotations

from casting import GEMINI_V2, IRONY, SK  # noqa: F401

CHILD = (" A real child's voice: high, light and small, natural child intonation and pace; plain child speech, "
         "no baby talk, never an adult imitating a child.")


def c(voice: str, who: str, age, style: str, family: str | None = None) -> dict:
    return {"voice": voice, "who": who, "age": age, "style": SK + style, **({"family": family} if family else {})}


CAST: dict[str, dict] = {
    # ------------------------------------------------------------------ prologue casting (approved, unchanged)
    "ADAM": {**GEMINI_V2["ADAM"], "who": "Adam Hruška", "age": 35, "family": "Adam"},
    "MIRA20": {**GEMINI_V2["MIRA20"], "who": "Mira Hrušková (2020)", "age": 80, "family": "Mira"},
    "ELA": {**GEMINI_V2["ELA"], "who": "Ela Švecová", "age": 40},
    "DANA": {**GEMINI_V2["DANA"], "who": "Dana Valová", "age": 48},
    "ROMAN": {**GEMINI_V2["ROMAN"], "who": "Roman Kováč", "age": 29},
    "LENKA": {**GEMINI_V2["LENKA"], "who": "Lenka Bartošová", "age": 37},
    "JOZEF": {**GEMINI_V2["JOZEF"], "who": "Jozef Mlynár", "age": 73},
    "SYSTEM": {**GEMINI_V2["SYSTEM"], "who": "device texts (ZVON, Atlas, ticket gate, station)", "age": None},

    # ------------------------------------------------------------------ family at other ages
    "MIRA95": c("Gacrux", "Mira Hrušková (1995)", 55,
                "The same woman as the 80-year-old grandmother, but 25 years younger: a 55-year-old retired engineer "
                "who leads a school sound club. A fuller, stronger and more energetic voice than at eighty, a "
                "teacher's clarity, gives tasks in order; sharp, quick-witted, dry and warm; natural brisk pace.",
                "Mira"),
    "MIRA60": c("Gacrux", "Mira Hrušková (June 1962)", 22,
                "The same woman as the old grandmother, sixty years earlier: a 22-year-old young technical assistant. "
                "A young, light, bright voice with the crisp diction and rhythm she will keep all her life; quick, "
                "curious, direct, a little impatient with vague words; natural quick pace.", "Mira"),
    "TONO": c("Puck", "Anton „Tóno“ Farkaš (1995)", 25,
              "A 25-year-old school caretaker: practical, quick, friendly and a little teasing, dry humour, short "
              "practical sentences, natural medium-quick pace.", "Tóno"),
    "TONO20": c("Puck", "Anton „Tóno“ Farkaš (2020)", 50,
                "The same man at 50, a school caretaker: calmer, a little lower and warmer voice, deadpan, says "
                "important things briefly, unhurried; the same dry humour and cadence as in his youth.", "Tóno"),
    "TONO82": c("Leda", "Anton „Tóno“ Farkaš (1982)", 12,
                "A 12-year-old schoolboy whose voice has not broken yet: curious, concrete, direct questions, kid "
                "logic, bargains a little, quiet and serious when he promises something." + CHILD, "Tóno"),
    "OTO": c("Sadaltager", "Oto Bielik (1962)", 46,
             "A 46-year-old mechanic: calm, precise, understated, open to evidence; looks before he speaks; short "
             "workshop sentences; warm, steady, measured voice.", "Oto"),
    "OTO82": c("Sadaltager", "Oto Bielik (1982)", 66,
               "The same mechanic twenty years later, at 66: an older, slightly softer and slower voice, gently "
               "amused by time, grandfatherly, still precise and calm.", "Oto"),
    "JANA82": c("Erinome", "Jana Vargová (1982)", 12,
                "A 12-year-old schoolgirl: shy and careful at first, precise with words, lights up when she may "
                "explain her own schematic." + CHILD, "Jana"),
    "JANA95": c("Erinome", "Jana Vargová (1995)", 25,
                "A 25-year-old woman, a self-confident organiser: clear, precise word choice, quick and friendly, "
                "corrects near-synonyms with a smile.", "Jana"),
    "JANA20": c("Erinome", "Jana Vargová (2020)", 50,
                "A 50-year-old woman on a video call from a school office: clear, practical, calm and precise, a "
                "mature, slightly lower voice.", "Jana"),
    "JANA35": c("Erinome", "Jana Vargová (2035)", 65,
                "A 65-year-old woman visiting an exhibition: calm, gently amused, precise as always, a mature older "
                "voice, unhurried.", "Jana"),
    "ZUZANA": c("Sulafat", "Zuzana (June 1962)", 7,
                "A 7-year-old girl finishing first grade: lively once she trusts you, curious, very observant, a "
                "serious little face that warms up, literal child logic, short plain sentences, counts everything."
                + CHILD, "Zuzana"),
    "ZUZANA95": c("Sulafat", "Zuzana (1995)", 40,
                  "A 40-year-old woman: warm, gentle and calm, kind, quietly funny with dry understatement, short "
                  "sentences, unhurried; a soft, warm voice.", "Zuzana"),
    "ADAM10": c("Autonoe", "Adam at 10 (school tape 1995)", 10,
                "A 10-year-old boy speaking into a school microphone: spontaneous, a bit shy, curious." + CHILD,
                "Adam"),
    "LEA95": c("Achernar", "Lea Kormanová (1995)", 33,
               "A 33-year-old teacher: warm, natural and gentle, unhurried, lets a short pause finish a sentence, "
               "speaks to children as to people, never pedagogical.", "Lea"),
    "LEA_REC": c("Achernar", "Lea Kormanová, voice message 2032", 70,
                 "The same woman at seventy leaving a short voice message for her grown son: an older, softer, warm "
                 "voice, light and unhurried, a little tired but smiling; simple and natural, not sentimental, "
                 "not dramatic.", "Lea"),

    # ------------------------------------------------------------------ 1995 Bratislava
    "SONA": c("Laomedeia", "Soňa Urbanová", 11,
              "An 11-year-old girl: curious and factual, takes grown-up rules seriously, guards the team album."
              + CHILD),
    "KUBO": c("Zephyr", "Kubo", 7,
              "A 7-year-old boy, a first-grader: quick child speech, proud of what he can do, takes things "
              "literally." + CHILD),
    "ZITA": c("Pulcherrima", "Zita Ondrušová", 46,
              "A 46-year-old kiosk keeper: fast, observant, good-natured, the estate's news agency, lively."),
    "EMIL": c("Enceladus", "Emil Belan", 61,
              "A 61-year-old street musician: soft, slow and gentle, small musical images, a mellow older voice."),
    "PALI": c("Umbriel", "Pavol „Pali“ Drobný", 42,
              "A 42-year-old repairman: direct, blunt but friendly collegial humour, short verdicts, relaxed."),
    "VIERA": c("Vindemiatrix", "Viera Holubová", 64,
               "A 64-year-old second-hand bookseller: precise, cultivated, mildly ironic, an older measured voice."),
    "KAROL": c("Charon", "Karol Merta (archive)", 53,
               "A 53-year-old head of an archive reading room: formal, exact, a little pedantic but helpful, "
               "quiet library voice."),
    "ALENA": c("Callirrhoe", "Alena Svobodová (photo studio)", 38,
               "A 38-year-old photographer: calm, sure of her craft, friendly and unhurried."),
    "FERO": c("Algenib", "Fero Lánik (market)", 50,
              "A 50-year-old market seller of small electronics: earthy, short sentences, good-humoured, a little "
              "gravelly."),
    "MILADA": c("Despina", "Milada Kyselová (tailor)", 57,
                "A 57-year-old tailor: quick, lively, practical, explains everything with tailoring comparisons; a "
                "mature voice."),
    "JURO": c("Sadachbia", "Juro Kazeta", 26,
              "A 26-year-old cassette collector and sound enthusiast: lively, enthusiastic, explains like a human, "
              "not a manual."),
    "JURAJ": c("Zubenelgenubi", "Juraj Križan (painter)", 19,
               "A 19-year-old painter: quiet, curious, unforced, soft-spoken young man."),
    "DEZI": c("Rasalgethi", "Dezider Kováč (radio amateur)", 47,
              "A 47-year-old radio amateur: lively technical voice, translates every term into everyday speech at "
              "once, friendly and clear."),

    # ------------------------------------------------------------------ 1960 Ivanka (June 1962)
    "BOZO": c("Charon", "Božidar Fiala (station)", 45,
              "A 45-year-old railway station worker: thoughtful, calm, kind, likes clear destinations; a steady, "
              "slightly lower voice."),
    "BERTA": c("Pulcherrima", "Berta Kovárová", 68,
               "A 68-year-old village woman on the square: direct, curious, good-natured, an older countryside "
               "voice."),
    "ALOJZ": c("Algieba", "Alojz Baran (post office)", 54,
               "A 54-year-old post office clerk: formal and charming officialese with an occasional soft, warm "
               "aside; smooth, measured."),
    "LIDA": c("Aoede", "Lída Fialová (costumes)", 43,
              "A 43-year-old costume maker of an amateur theatre: organised, lively, quick, warm."),
    "RUDO": c("Fenrir", "Rudolf „Rudo“ Pavlík (actor)", 34,
              "A 34-year-old amateur actor: big theatrical stage diction when he declaims, shy and quieter off "
              "stage."),
    "STEFAN": c("Alnilam", "Štefan Haluška (store)", 51,
                "A 51-year-old keeper of a workshop store: curt but willing, firm, proud of knowing exactly what is "
                "missing."),
    "VERA60": c("Kore", "Vera Nemcová (draughtswoman)", 22,
                "A 22-year-old technical draughtswoman: calm, practical, matter-of-fact, a young clear voice."),
    "NARRATOR": c("Charon", "narrator (closing captions)", None,
                  "A calm narrator: reflective, warm and quiet, even pace, no drama, no jokes."),

    # ------------------------------------------------------------------ 1982 Dúbravka
    "DOBRO": c("Orus", "teacher Dobrovič", 39,
               "A 39-year-old teacher in 1982: formal and careful at first, then concrete and more human; clear "
               "classroom voice; never a caricature."),
    "RUZENA": c("Aoede", "Ružena Malá (shop 1982)", 49,
                "A 49-year-old shop assistant: direct, kind, practical, a warm mature voice."),
    "MARTA82": c("Kore", "Marta Dobiášová (store)", 56,
                 "A 56-year-old head of a maintenance store: exact, patient, calm, knows a rule from needless "
                 "trouble; a mature voice."),
    "SIMON": c("Algenib", "Šimon Rybár (gardener)", 60,
               "A 60-year-old school gardener: calm, concrete, unhurried, thinks in decades; a slightly gravelly "
               "older voice."),

    # ------------------------------------------------------------------ 2035 Jasná
    "NINA": c("Kore", "Nina Švecová", 30,
              "A 30-year-old curator: matter-of-fact, fast and clear, names the limits of her authority firmly, "
              "friendly but professional."),
    "NINA_REMOTE": c("Kore", "Nina over the service channel", 30,
                     "A 30-year-old curator speaking over a service radio channel: matter-of-fact, fast, clear, "
                     "short sentences, focused."),
    "VIKTOR": c("Orus", "Viktor Korman", 50,
                "A 50-year-old founder of a digital archive: serious, controlled and convinced, low and measured, "
                "quiet intensity; no humour, never hysterical."),
    "TAMARA": c("Aoede", "Tamara Kráľová (repairer)", 40,
                "A 40-year-old repairwoman of a travelling workshop: friendly, warm, easy colleague humour, relaxed."),
    "BORIS": c("Algieba", "Boris Urban (exhibition archivist)", 64,
               "A 64-year-old archivist: calm, dry, gentle, jokes like bibliographic footnotes, an older smooth "
               "voice, unhurried."),
    "SARA": c("Zephyr", "Sára Vrbová (client centre)", 28,
              "A 28-year-old contact person at a client centre: professional, pleasant, bright, clear."),
    "ROBOT": c("Iapetus", "delivery robot Očko", None,
               "A small polite delivery robot: a synthetic, even, precise voice, crisp and a little cheerful, "
               "literal, slightly mechanical rhythm."),
    "IVAN": c("Alnilam", "Ivan Horský (cable car)", 44,
              "A 44-year-old cable-car operator: matter-of-fact, friendly, calm, sure of himself."),
    "TURISTA": c("Umbriel", "Miloš Polák (fellow passenger)", 52,
                 "A 52-year-old hiker: easy-going, gentle humour, a little nostalgic."),
}

# Audition (audition_full.py): the child roles and young Mira, each spoken by the candidate stock voices.
CHILD_CANDIDATES = {
    "TONO82": ["Puck", "Leda", "Autonoe", "Laomedeia"],
    "ADAM10": ["Achird", "Autonoe", "Leda", "Zephyr"],
    "JANA82": ["Erinome", "Laomedeia", "Leda"],
    "SONA": ["Laomedeia", "Autonoe", "Zephyr"],
    "KUBO": ["Zephyr", "Autonoe", "Leda"],
    "ZUZANA": ["Sulafat", "Achernar", "Leda", "Autonoe"],
    "ZUZANA95": ["Sulafat", "Achernar"],
    "MIRA60": ["Gacrux", "Erinome", "Kore"],
    "MIRA95": ["Gacrux"],
}
