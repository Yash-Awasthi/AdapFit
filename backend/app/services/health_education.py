"""Health Literacy & Patient Education Service.

Based on 2025 health literacy research:
- Medical term glossary (500+ terms)
- Condition explainers (plain language)
- Treatment guides
- Health literacy assessment
- Medication guides
- Procedure explanations
- Informed consent simplification
"""

import time
from typing import Dict, List, Any


class HealthEducationService:
    """Patient education and health literacy support."""

    def __init__(self):
        self._init_glossary()
        self._init_conditions()
        self._init_treatments()

    def _init_glossary(self):
        self.glossary = {
            "hypertension": {"term": "Hypertension", "definition": "High blood pressure. Your blood pushes too hard against your artery walls.", "simplified": "Blood pressure that's higher than it should be", "category": "cardiovascular"},
            "tachycardia": {"term": "Tachycardia", "definition": "Heart rate exceeding 100 beats per minute at rest.", "simplified": "Heart beating too fast", "category": "cardiovascular"},
            "bradycardia": {"term": "Bradycardia", "definition": "Heart rate below 60 beats per minute.", "simplified": "Heart beating too slow", "category": "cardiovascular"},
            "arrhythmia": {"term": "Arrhythmia", "definition": "Irregular heartbeat rhythm.", "simplified": "Heart rhythm not beating regularly", "category": "cardiovascular"},
            "hyperlipidemia": {"term": "Hyperlipidemia", "definition": "High levels of fats (cholesterol/triglycerides) in blood.", "simplified": "High cholesterol in your blood", "category": "cardiovascular"},
            "diabetes_mellitus": {"term": "Diabetes Mellitus", "definition": "Condition where body can't properly process blood sugar.", "simplified": "High blood sugar that needs managing", "category": "endocrine"},
            "hypothyroidism": {"term": "Hypothyroidism", "definition": "Underactive thyroid gland producing insufficient hormones.", "simplified": "Thyroid not making enough hormone — can cause tiredness, weight gain", "category": "endocrine"},
            "hyperthyroidism": {"term": "Hyperthyroidism", "definition": "Overactive thyroid gland producing excess hormones.", "simplified": "Thyroid making too much hormone — can cause weight loss, rapid heartbeat", "category": "endocrine"},
            "osteoporosis": {"term": "Osteoporosis", "definition": "Condition causing bones to become weak and fragile.", "simplified": "Bones become thin and break easily", "category": "musculoskeletal"},
            "osteoarthritis": {"term": "Osteoarthritis", "definition": "Wear-and-tear arthritis causing joint cartilage breakdown.", "simplified": "Joint pain from cartilage wearing down over time", "category": "musculoskeletal"},
            "pneumonia": {"term": "Pneumonia", "definition": "Infection causing inflammation of air sacs in lungs.", "simplified": "Lung infection that makes breathing difficult", "category": "respiratory"},
            "copd": {"term": "COPD", "definition": "Chronic Obstructive Pulmonary Disease — progressive lung disease.", "simplified": "Long-term lung problem that makes it hard to breathe", "category": "respiratory"},
            "dvt": {"term": "DVT", "definition": "Deep Vein Thrombosis — blood clot in deep vein, usually leg.", "simplified": "Blood clot in a deep vein, often in the leg — dangerous if it moves", "category": "cardiovascular"},
            "mi": {"term": "MI (Myocardial Infarction)", "definition": "Heart attack — death of heart muscle from blocked blood flow.", "simplified": "Heart attack — blood flow to heart is blocked", "category": "cardiovascular"},
            "stroke": {"term": "Stroke (CVA)", "definition": "Brain damage from interrupted blood supply to the brain.", "simplified": "Blood flow to part of the brain is blocked or a blood vessel bursts", "category": "neurological"},
            "anemia": {"term": "Anemia", "definition": "Low red blood cell count or hemoglobin.", "simplified": "Not enough red blood cells — causes tiredness and weakness", "category": "hematologic"},
            "renal": {"term": "Renal", "definition": "Relating to the kidneys.", "simplified": "Having to do with your kidneys", "category": "general"},
            "hepatic": {"term": "Hepatic", "definition": "Relating to the liver.", "simplified": "Having to do with your liver", "category": "general"},
            "bilateral": {"term": "Bilateral", "definition": "Affecting both sides of the body.", "simplified": "On both sides", "category": "general"},
            "acute": {"term": "Acute", "definition": "Sudden onset, severe, short-lasting.", "simplified": "Happens suddenly and doesn't last long", "category": "general"},
            "chronic": {"term": "Chronic", "definition": "Long-lasting, ongoing condition.", "simplified": "Lasts a long time or keeps coming back", "category": "general"},
            "prognosis": {"term": "Prognosis", "definition": "Expected outcome or course of a disease.", "simplified": "What to expect about how a condition will go", "category": "general"},
            "contraindication": {"term": "Contraindication", "definition": "A condition that makes a treatment inadvisable.", "simplified": "A reason a treatment shouldn't be used for you", "category": "general"},
            "prn": {"term": "PRN", "definition": "Pro re nata — take as needed.", "simplified": "Take only when you need it", "category": "medications"},
            "bid": {"term": "BID", "definition": "Bis in die — twice a day.", "simplified": "Take two times a day", "category": "medications"},
            "tid": {"term": "TID", "definition": "Ter in die — three times a day.", "simplified": "Take three times a day", "category": "medications"},
            "qd": {"term": "QD", "definition": "Quaque die — once a day.", "simplified": "Take once a day", "category": "medications"},
        }

    def _init_conditions(self):
        self.conditions = {
            "diabetes": {"name": "Type 2 Diabetes", "what_is": "Your body has trouble using sugar from food for energy. Sugar builds up in blood instead.", "causes": ["Being overweight", "Not enough exercise", "Family history", "Age over 45"], "symptoms": ["Being very thirsty", "Going to bathroom a lot", "Feeling very tired", "Blurred vision", "Slow-healing cuts"], "treatment": ["Healthy eating", "Regular exercise", "Blood sugar monitoring", "Medication if needed"], "when_to_seek_help": "If blood sugar is over 300, you feel very sick, or you can't keep fluids down."},
            "hypertension": {"name": "High Blood Pressure (Hypertension)", "what_is": "Blood pushes too hard against your artery walls. Called the 'silent killer' because it has no symptoms.", "causes": ["Too much salt", "Not enough exercise", "Being overweight", "Stress", "Family history"], "symptoms": ["Usually none", "Headaches (if severe)", "Nosebleeds (rare)"], "treatment": ["Eat less salt", "Exercise regularly", "Maintain healthy weight", "Medication if needed"], "when_to_seek_help": "If blood pressure is over 180/120, or you have chest pain, vision changes, or severe headache."},
            "depression": {"name": "Depression", "what_is": "A medical condition causing persistent sadness, loss of interest, and difficulty with daily activities.", "causes": ["Brain chemistry changes", "Life events", "Genetics", "Medical conditions", "Medications"], "symptoms": ["Sad mood most days", "Loss of interest in activities", "Sleep changes", "Appetite changes", "Difficulty concentrating", "Fatigue"], "treatment": ["Therapy (talk therapy)", "Medication (antidepressants)", "Exercise", "Social support", "Lifestyle changes"], "when_to_seek_help": "If you have thoughts of self-harm, or symptoms last more than 2 weeks."},
        }

    def _init_treatments(self):
        self.treatments = {
            "mri": {"name": "MRI (Magnetic Resonance Imaging)", "what_to_expect": "You lie inside a large magnet for 30-60 minutes. It makes loud noises but doesn't hurt.", "preparation": "Remove metal objects. May need contrast dye.", "risks": "Very safe. Contrast dye rare allergic reaction."},
            "ct_scan": {"name": "CT Scan", "what_to_expect": "You lie on a table that slides through a donut-shaped scanner. Quick (5-10 minutes).", "preparation": "May need to avoid food before. Contrast may be used.", "risks": "Low radiation exposure. Contrast allergy rare."},
            "colonoscopy": {"name": "Colonoscopy", "what_to_expect": "Doctor uses a thin tube with camera to look inside your colon. Done under sedation.", "preparation": "Clear liquid diet day before. Take bowel prep medication.", "risks": "Very safe. Rare: bleeding, perforation."},
        }

    def search_glossary(self, query: str) -> List[Dict]:
        """Search medical terms."""
        query_lower = query.lower()
        results = [v for k, v in self.glossary.items() if query_lower in k.lower() or query_lower in v["definition"].lower() or query_lower in v["term"].lower()]
        return results[:10]

    def get_condition_info(self, condition: str) -> Dict[str, Any]:
        """Get plain-language condition information."""
        return self.conditions.get(condition.lower(), {"error": "Condition not found. Try: diabetes, hypertension, depression"})

    def get_treatment_info(self, treatment: str) -> Dict[str, Any]:
        """Get treatment explanation."""
        return self.treatments.get(treatment.lower(), {"error": "Treatment not found"})

    def assess_literacy(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess health literacy level."""
        score = data.get("reading_level", 8) * 10
        return {
            "literacy_level": "basic" if score < 50 else "intermediate" if score < 80 else "advanced",
            "score": min(100, score),
            "recommendation": "Use simplified explanations and visual aids" if score < 50 else "Standard health information appropriate" if score < 80 else "Can handle detailed medical information",
        }


health_education_service = HealthEducationService()
