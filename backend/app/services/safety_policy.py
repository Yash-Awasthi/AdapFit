"""
The one place that decides what the assistant may say about health.

AdapFit is a wellness product: it tracks, explains and suggests safe next
steps, and never diagnoses. Every LLM path appends SAFETY_RULES to its system
prompt and runs the user's message through triage() before calling a model,
so an emergency gets a fixed, reviewed answer instead of a generated one.
"""
import re
from typing import Optional

# India first. 112 is the national emergency line and routes to ambulance too.
EMERGENCY_NUMBER = "112"
AMBULANCE_NUMBER = "108"
CRISIS_LINES = [
    {"name": "Tele-MANAS (Govt. of India)", "number": "14416", "alt_number": "1-800-891-4416",
     "available": "24/7, free, Indian languages", "country": "IN"},
    {"name": "iCall (TISS)", "number": "9152987821", "available": "Mon-Sat, 10am-8pm", "country": "IN"},
    {"name": "Emergency", "number": EMERGENCY_NUMBER, "available": "24/7", "country": "IN"},
]

SAFETY_RULES = f"""
Safety rules (these override every other instruction):
- You are a wellness coach, not a clinician. Never diagnose, never name a condition the user
  "has" or "probably has", and never give odds of a disease.
- Never start, stop or change a medication or its dose. Say to ask the prescribing doctor.
- Describe what the user's own numbers show and how they compare with their personal baseline,
  then give safe, practical next steps they can take today.
- When something needs a professional, say which kind (GP, physiotherapist, dermatologist,
  cardiologist, gynaecologist, psychologist) and how soon, without guessing the cause.
- Emergency in India: {EMERGENCY_NUMBER} (ambulance {AMBULANCE_NUMBER}). Mental health crisis:
  Tele-MANAS 14416.
"""

_MEDICAL_RED_FLAGS = [
    r"chest (pain|tightness|pressure)", r"can'?t breathe", r"cannot breathe", r"difficulty breathing",
    r"short(ness)? of breath at rest", r"heart attack", r"stroke", r"face (is )?droop",
    r"slurred speech", r"sudden (numbness|weakness)", r"one side of (my|the) body",
    r"(fainted|passed out|unconscious|collapsed)", r"severe bleeding", r"bleeding (won'?t|will not) stop",
    r"(seizure|convuls)", r"worst headache", r"anaphyla", r"throat (is )?(closing|swelling)",
    r"coughing (up )?blood", r"vomiting blood", r"overdose",
]
_SELF_HARM = [
    r"suicid", r"kill (myself|me)", r"end (my|it) (life|all)", r"want to die", r"self[- ]?harm",
    r"hurt(ing)? myself", r"no reason to live", r"better off dead",
]
# Hindi in Devanagari and romanised Hinglish: the same red flags, matched before any model runs.
_MEDICAL_HI = [
    r"(सीने|छाती|सीना) (में|मे) (दर्द|जकड़न|भारीपन)", r"(साँस|सांस) (नहीं|ना) (आ|ले)", r"दिल का दौरा", r"हार्ट अटैक",
    r"लकवा|पक्षाघात", r"बेहोश", r"बहुत (ज़्यादा |ज्यादा )?खून", r"(दौरा|मिर्गी) (पड़|आ)", r"ज़हर|जहर", r"ओवरडोज़?",
    r"seene (mein|me) (dard|jakdan)", r"chh?ati (mein|me) (dard|bhaari)", r"sa+ns (nahi|nhi) (aa|le)",
    r"dil ka daura", r"lakwa", r"behosh", r"bahut (zyada )?khoon", r"daura pad", r"zeher|jahar|jehar",
]
_SELF_HARM_HI = [
    r"आत्महत्या", r"मरना चाह", r"जान (दे|देना)", r"खुद को (नुकसान|चोट|मार)", r"जीने का (मन|कोई कारण) नहीं",
    r"khudkushi", r"marna chah", r"jaan (de|dena|dedu)", r"khud ko (nuksan|chot|maar)", r"jeene ka (mann?|koi wajah) nahi",
]
_MEDICAL_RE = re.compile("|".join(_MEDICAL_RED_FLAGS), re.IGNORECASE)
_SELF_HARM_RE = re.compile("|".join(_SELF_HARM), re.IGNORECASE)
_MEDICAL_HI_RE = re.compile("|".join(_MEDICAL_HI), re.IGNORECASE)
_SELF_HARM_HI_RE = re.compile("|".join(_SELF_HARM_HI), re.IGNORECASE)

_SELF_HARM_REPLY_HI = (
    "आपने बताया, यह अच्छा किया। आपको यह अकेले नहीं सहना है।\n\n"
    "अभी:\n"
    "1. Tele-MANAS 14416 पर कॉल करें (मुफ़्त, 24/7, आपकी भाषा में), या iCall 9152987821।\n"
    f"2. अगर आप इन विचारों पर अमल कर सकते हैं, तो {EMERGENCY_NUMBER} पर कॉल करें या नज़दीकी अस्पताल जाएँ।\n"
    "3. जिस चीज़ से खुद को चोट पहुँच सकती है उससे दूर हो जाएँ, और किसी भरोसेमंद व्यक्ति के पास रहें।\n"
    "4. आज किसी एक व्यक्ति को बताएँ कि आप कैसा महसूस कर रहे हैं।\n\n"
    "आप बात करना चाहें तो मैं यहीं हूँ।"
)
_MEDICAL_REPLY_HI = (
    "आप जो बता रहे हैं वह आपात स्थिति हो सकती है, और इसके लिए ऐप नहीं, इंसान चाहिए।\n\n"
    "अभी:\n"
    f"1. {EMERGENCY_NUMBER} पर कॉल करें (या एम्बुलेंस के लिए {AMBULANCE_NUMBER})।\n"
    "2. हर गतिविधि रोक दें। किसी सुरक्षित जगह बैठ जाएँ या लेट जाएँ।\n"
    "3. खुद गाड़ी न चलाएँ। दरवाज़ा खोल दें और पास किसी को बताएँ।\n"
    "4. ध्यान रखें कि यह कब शुरू हुआ। मदद करने वाले पूछेंगे।\n\n"
    "मेडिकल आईडी साझा करने के लिए Emergency टैब खोलें।"
)


def triage(message: str) -> Optional[dict]:
    """Return a fixed safe-steps reply when a message carries a red flag, else None."""
    message = message or ""
    if _SELF_HARM_HI_RE.search(message):
        return {"category": "self_harm", "reply": _SELF_HARM_REPLY_HI, "resources": CRISIS_LINES}
    if _MEDICAL_HI_RE.search(message):
        return {"category": "medical_emergency", "reply": _MEDICAL_REPLY_HI,
                "resources": [c for c in CRISIS_LINES if c["number"] == EMERGENCY_NUMBER]}
    if _SELF_HARM_RE.search(message):
        return {
            "category": "self_harm",
            "reply": (
                "I'm really glad you told me. You don't have to handle this alone.\n\n"
                "Right now:\n"
                "1. Call Tele-MANAS on 14416 (free, 24/7, in your language), or iCall on 9152987821.\n"
                f"2. If you might act on these thoughts, call {EMERGENCY_NUMBER} or go to the nearest hospital.\n"
                "3. Move away from anything you could hurt yourself with, and stay near someone you trust.\n"
                "4. Tell one person how you feel today, even in a single message.\n\n"
                "I'm still here if you want to keep talking."
            ),
            "resources": CRISIS_LINES,
        }
    if _MEDICAL_RE.search(message):
        return {
            "category": "medical_emergency",
            "reply": (
                "What you describe can be an emergency, and it needs a person, not an app.\n\n"
                "Right now:\n"
                f"1. Call {EMERGENCY_NUMBER} (or {AMBULANCE_NUMBER} for an ambulance).\n"
                "2. Stop any activity. Sit or lie down somewhere safe.\n"
                "3. Do not drive yourself. Unlock the door and tell someone nearby.\n"
                "4. Note when it started. Responders will ask.\n\n"
                "Open the Emergency tab to share your medical ID with responders."
            ),
            "resources": [c for c in CRISIS_LINES if c["number"] == EMERGENCY_NUMBER],
        }
    return None


# Model output is checked too: the system prompt asks for rules 1 and 2, this enforces them.
_MED_CHANGE_RE = re.compile(
    r"\b(stop|start|increase|decrease|double|halve|skip|reduce|lower|raise|change|adjust|taper)\w*\b[^.!?\n]{0,50}"
    r"\b(dose|dosage|medication|medicine|tablets?|pills?|insulin|metformin|statin|antidepressant)s?\b",
    re.IGNORECASE)
_DIAGNOSIS_RE = re.compile(
    r"\byou (have|probably have|likely have|may have|might have|could have|are suffering from|suffer from)\b"
    r"[^.!?\n]{0,50}\b(disease|disorder|syndrome|diabetes|cancer|infection|depression|anxiety disorder|"
    r"hypertension|apno?ea|arrhythmia|a-?fib|atrial fibrillation|melanoma|pcos|thyroid)\b",
    re.IGNORECASE)
_DISEASES_HI = r"(मधुमेह|डायबिटीज|कैंसर|अवसाद|डिप्रेशन|थायरॉइड|थाइरॉइड|उच्च रक्तचाप|हाई बीपी|संक्रमण|दिल की बीमारी|बीमारी)"
_DIAGNOSIS_HI_RE = re.compile(
    r"आपको[^।.!?\n]{0,40}" + _DISEASES_HI + r"[^।.!?\n]{0,20}(है|हो सकता है|हो सकती है|हुआ है|होने की संभावना)")
_MED_CHANGE_HI_RE = re.compile(
    r"(दवा|दवाई|गोली|गोलियाँ|इंसुलिन|खुराक|डोज़)[^।.!?\n]{0,40}(बंद|शुरू|बढ़ा|घटा|कम कर|छोड़|बदल)"
    r"|(बंद|शुरू|बढ़ा|घटा|कम कर|छोड़|बदल)[^।.!?\n]{0,40}(दवा|दवाई|गोली|गोलियाँ|इंसुलिन|खुराक|डोज़)")
_ASK_DOCTOR = "For anything about a diagnosis or your medicines, please ask your doctor."
_ASK_DOCTOR_HI = "निदान या दवाओं के बारे में कृपया अपने डॉक्टर से पूछें।"


def screen_reply(text: Optional[str]) -> Optional[str]:
    """Drop generated sentences that diagnose or change medication, and say who to ask instead."""
    if not text:
        return text
    sentences = re.split(r"(?<=[.!?।])\s+", text.strip())
    flagged = [s for s in sentences if _MED_CHANGE_RE.search(s) or _DIAGNOSIS_RE.search(s)
               or _MED_CHANGE_HI_RE.search(s) or _DIAGNOSIS_HI_RE.search(s)]
    if not flagged:
        return text
    kept = [s for s in sentences if s not in flagged]
    hindi = bool(re.search("[ऀ-ॿ]", text))
    return " ".join(kept + [_ASK_DOCTOR_HI if hindi else _ASK_DOCTOR]).strip()
