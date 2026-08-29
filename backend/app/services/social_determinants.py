"""
Social Determinants of Health (SDOH) — Screening & Community Resources
Food security, transportation, housing, social needs assessment
"""
from datetime import datetime
from typing import Dict, List
import random


class SocialDeterminantsService:
    """SDOH screening and community resource finder"""

    def __init__(self):
        self.screening_categories = {
            "food_security": {
                "questions": [
                    {"id": 1, "text": "Within the past 12 months, were you worried about running out of food?", "options": ["Never", "Sometimes", "Often", "Always"]},
                    {"id": 2, "text": "Within the past 12 months, did you eat less than you should because there wasn't enough money for food?", "options": ["Never", "Sometimes", "Often", "Always"]},
                    {"id": 3, "text": "Within the past 12 months, were you hungry but didn't eat because there wasn't enough money for food?", "options": ["Never", "Sometimes", "Often", "Always"]},
                ],
                "scoring": {"Never": 0, "Sometimes": 1, "Often": 2, "Always": 3},
                "risk_thresholds": {"low": 0, "moderate": 3, "high": 6},
            },
            "transportation": {
                "questions": [
                    {"id": 1, "text": "In the past 12 months, have you missed or delayed medical appointments due to transportation?", "options": ["Yes", "No"]},
                    {"id": 2, "text": "Do you have reliable transportation to medical appointments?", "options": ["Yes", "No", "Sometimes"]},
                    {"id": 3, "text": "How far is your nearest medical facility?", "options": ["<1 mile", "1-5 miles", "5-10 miles", ">10 miles"]},
                ],
            },
            "housing": {
                "questions": [
                    {"id": 1, "text": "Are you currently housed?", "options": ["Yes", "No", "Temporarily staying with someone"]},
                    {"id": 2, "text": "Do you have concerns about losing your housing?", "options": ["Yes", "No"]},
                    {"id": 3, "text": "Is your housing safe and in good condition?", "options": ["Yes", "No", "Somewhat"]},
                ],
            },
            "social_support": {
                "questions": [
                    {"id": 1, "text": "Do you have someone you can count on for help in an emergency?", "options": ["Yes", "No"]},
                    {"id": 2, "text": "How often do you feel lonely or isolated?", "options": ["Never", "Sometimes", "Often", "Always"]},
                    {"id": 3, "text": "Do you have family or friends you see regularly?", "options": ["Yes", "No"]},
                ],
            },
            "financial_strain": {
                "questions": [
                    {"id": 1, "text": "Are you having trouble paying for necessities (rent, utilities, food)?", "options": ["Yes", "No"]},
                    {"id": 2, "text": "Do you have health insurance coverage?", "options": ["Yes", "No", "Partial"]},
                    {"id": 3, "text": "Have you delayed or avoided medical care due to cost?", "options": ["Yes", "No"]},
                ],
            },
        }

        self.community_resources = {
            "food": [
                {"name": "Local Food Bank", "type": "food_distribution", "address": "123 Main St", "phone": "(555) 111-2222", "hours": "Mon-Fri 9am-4pm", "eligibility": "Income-based"},
                {"name": "Meals on Wheels", "type": "meal_delivery", "phone": "(555) 222-3333", "eligibility": "Homebound individuals"},
                {"name": "SNAP Benefits Office", "type": "government_assistance", "phone": "(555) 333-4444", "eligibility": "Income-based"},
                {"name": "Community Kitchen", "type": "hot_meals", "address": "456 Oak Ave", "hours": "Daily 11am-2pm", "eligibility": "Open to all"},
            ],
            "transportation": [
                {"name": "Medical Transport Service", "type": "medical_transport", "phone": "(555) 444-5555", "eligibility": "Medicaid patients"},
                {"name": "Senior Ride Program", "type": "senior_transport", "phone": "(555) 555-6666", "eligibility": "Age 65+"},
                {"name": "Volunteer Driver Network", "type": "volunteer_transport", "phone": "(555) 666-7777", "eligibility": "Low-income"},
            ],
            "housing": [
                {"name": "Emergency Shelter", "type": "emergency_shelter", "phone": "(555) 777-8888", "hours": "24/7", "eligibility": "Immediate need"},
                {"name": "Housing Authority", "type": "affordable_housing", "phone": "(555) 888-9999", "eligibility": "Income-based"},
                {"name": "Rental Assistance Program", "type": "rental_aid", "phone": "(555) 999-0000", "eligibility": "At-risk of homelessness"},
            ],
            "social_support": [
                {"name": "Senior Center", "type": "social_center", "address": "789 Elm St", "hours": "Mon-Sat 8am-6pm"},
                {"name": "Mental Health Support Group", "type": "support_group", "phone": "(555) 111-0000", "hours": "Weekly meetings"},
                {"name": "211 Helpline", "type": "crisis_line", "phone": "211", "hours": "24/7"},
            ],
            "financial": [
                {"name": "Medicaid Office", "type": "insurance", "phone": "(555) 222-0000"},
                {"name": "LIHEAP (Utility Assistance)", "type": "utility_aid", "phone": "(555) 333-0000"},
                {"name": "Community Action Agency", "type": "general_assistance", "phone": "(555) 444-0000"},
            ],
        }

    def screen_sdoh(self, patient_id: str, responses: Dict) -> Dict:
        """Screen for social determinants of health"""
        results = {}
        overall_risk = "low"
        needs = []

        for category, data in self.screening_categories.items():
            cat_responses = responses.get(category, [])
            if cat_responses:
                # Score the category
                if "scoring" in data:
                    score = sum(data["scoring"].get(r, 0) for r in cat_responses)
                    max_score = len(data["questions"]) * 3
                    risk = "low"
                    if score >= data["risk_thresholds"].get("high", max_score * 0.6):
                        risk = "high"
                        needs.append(category)
                    elif score >= data["risk_thresholds"].get("moderate", max_score * 0.3):
                        risk = "moderate"
                        needs.append(category)
                else:
                    risk = "moderate" if "No" in cat_responses else "low"

                results[category] = {
                    "risk": risk,
                    "score": score if "scoring" in data else None,
                }

        # Determine overall risk
        if any(r["risk"] == "high" for r in results.values()):
            overall_risk = "high"
        elif any(r["risk"] == "moderate" for r in results.values()):
            overall_risk = "moderate"

        return {
            "patient_id": patient_id,
            "screening_date": datetime.now().isoformat(),
            "results": results,
            "overall_risk": overall_risk,
            "needs_identified": needs,
            "recommendations": self._get_recommendations(needs),
            "resources": self._get_relevant_resources(needs),
        }

    def _get_recommendations(self, needs: List[str]) -> List[str]:
        """Get recommendations based on identified needs"""
        recs = []
        if "food_security" in needs:
            recs.append("Connect with local food bank and apply for SNAP benefits")
        if "transportation" in needs:
            recs.append("Arrange medical transport services for upcoming appointments")
        if "housing" in needs:
            recs.append("Refer to housing authority for emergency or affordable housing")
        if "social_support" in needs:
            recs.append("Connect with community support groups and social activities")
        if "financial_strain" in needs:
            recs.append("Apply for Medicaid and utility assistance programs")
        return recs

    def _get_relevant_resources(self, needs: List[str]) -> List[Dict]:
        """Get relevant community resources"""
        resources = []
        for need in needs:
            category_resources = self.community_resources.get(need, [])
            resources.extend(category_resources[:3])
        return resources

    def find_resources(self, resource_type: str, location: str = None) -> List[Dict]:
        """Find community resources by type"""
        all_resources = []
        for category, resources in self.community_resources.items():
            for resource in resources:
                if resource_type in resource.get("type", "") or resource_type in category:
                    all_resources.append(resource)
        return all_resources


social_determinants_service = SocialDeterminantsService()
