"""
Validated self-report questionnaires: PHQ-9 (low mood), GAD-7 (worry and
anxiety) and WHO-5 (wellbeing).

A score places the answers in the questionnaire's published range and gives a
safe next step. It is a screening result for the user to act on, not a
diagnosis, and it never suggests medication.
"""
from app.services.safety_policy import CRISIS_LINES

FREQUENCY = ["Not at all", "Several days", "More than half the days", "Nearly every day"]
WHO5_OPTIONS = ["At no time", "Some of the time", "Less than half of the time",
                "More than half of the time", "Most of the time", "All of the time"]

SEE_SOMEONE = "Talk to a doctor, psychologist or counsellor in the next two weeks and show them this score."
SEE_SOMEONE_SOON = "Please book a doctor, psychologist or psychiatrist this week and show them this score."

QUESTIONNAIRES = {
    "phq9": {
        "title": "PHQ-9",
        "about": "Low mood over the last two weeks",
        "prompt": "Over the last 2 weeks, how often have you been bothered by:",
        "options": FREQUENCY,
        "questions": [
            "Little interest or pleasure in doing things",
            "Feeling down, depressed, or hopeless",
            "Trouble falling or staying asleep, or sleeping too much",
            "Feeling tired or having little energy",
            "Poor appetite or overeating",
            "Feeling bad about yourself, or that you are a failure or have let yourself or your family down",
            "Trouble concentrating on things, such as reading or watching television",
            "Moving or speaking so slowly that other people could have noticed, or being so fidgety or restless that you have been moving around a lot more than usual",
            "Thoughts that you would be better off dead, or of hurting yourself",
        ],
        # (lowest score, range label, next step)
        "ranges": [
            (20, "severe", SEE_SOMEONE_SOON),
            (15, "moderately severe", SEE_SOMEONE_SOON),
            (10, "moderate", SEE_SOMEONE),
            (5, "mild", "Keep logging mood, move daily and protect sleep. Repeat this in two weeks."),
            (0, "minimal", "No action needed. Repeat this whenever your mood changes."),
        ],
    },
    "gad7": {
        "title": "GAD-7",
        "about": "Worry and anxiety over the last two weeks",
        "prompt": "Over the last 2 weeks, how often have you been bothered by:",
        "options": FREQUENCY,
        "questions": [
            "Feeling nervous, anxious, or on edge",
            "Not being able to stop or control worrying",
            "Worrying too much about different things",
            "Trouble relaxing",
            "Being so restless that it is hard to sit still",
            "Becoming easily annoyed or irritable",
            "Feeling afraid as if something awful might happen",
        ],
        "ranges": [
            (15, "severe", SEE_SOMEONE_SOON),
            (10, "moderate", SEE_SOMEONE),
            (5, "mild", "Try daily slow breathing (the HRV breathing coach) and limit caffeine. Repeat this in two weeks."),
            (0, "minimal", "No action needed."),
        ],
    },
    "who5": {
        "title": "WHO-5",
        "about": "Wellbeing over the last two weeks",
        "prompt": "Over the last 2 weeks:",
        "options": WHO5_OPTIONS,
        "questions": [
            "I have felt cheerful and in good spirits",
            "I have felt calm and relaxed",
            "I have felt active and vigorous",
            "I woke up feeling fresh and rested",
            "My daily life has been filled with things that interest me",
        ],
        # WHO-5 is reported as a percentage (raw x 4); 50 or below warrants a closer look.
        "ranges": [
            (76, "high", "Keep doing what you are doing."),
            (52, "good", "Look after the basics: sleep, movement and people you like."),
            (29, "low", "Your wellbeing is low. Take the PHQ-9 and consider talking to someone you trust."),
            (0, "very low", SEE_SOMEONE),
        ],
    },
}


def questionnaire(key: str) -> dict:
    q = QUESTIONNAIRES[key]
    return {"id": key, "title": q["title"], "about": q["about"], "prompt": q["prompt"],
            "options": q["options"], "questions": q["questions"]}


def score(key: str, answers: list[int]) -> dict:
    q = QUESTIONNAIRES[key]
    top = len(q["options"]) - 1
    if len(answers) != len(q["questions"]) or any(not 0 <= a <= top for a in answers):
        raise ValueError(f"{q['title']} needs {len(q['questions'])} answers between 0 and {top}")
    raw = sum(answers)
    value = raw * 4 if key == "who5" else raw
    label, next_step = next((lab, step) for low, lab, step in q["ranges"] if value >= low)
    result = {
        "questionnaire": key, "title": q["title"], "score": value,
        "max_score": 100 if key == "who5" else top * len(q["questions"]),
        "range": label, "next_step": next_step,
        "note": "A screening score, not a diagnosis.",
    }
    if key == "phq9" and answers[8] > 0:
        result["crisis"] = {
            "message": "You said you have had thoughts of being better off dead or of hurting yourself. "
                       "Please talk to someone today.",
            "resources": CRISIS_LINES,
        }
    return result
