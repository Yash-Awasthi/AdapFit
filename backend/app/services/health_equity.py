"""
Health Equity — Community health scoring, intervention recommendations, resource optimization
Addresses social determinants of health for underserved communities.
"""
from datetime import datetime
from typing import Dict, List, Optional
import uuid


class HealthEquityService:
    SDOH_CATEGORIES = {
        "economic_stability": {"name": "Economic Stability", "weight": 0.20, "indicators": ["income_level", "employment_status", "financial_strain", "housing_cost_burden"]},
        "education_access": {"name": "Education Access & Quality", "weight": 0.15, "indicators": ["education_level", "literacy_score", "school_quality", "digital_access"]},
        "healthcare_access": {"name": "Healthcare Access & Quality", "weight": 0.25, "indicators": ["insurance_status", "provider_availability", "transportation_access", "wait_times"]},
        "neighborhood_environment": {"name": "Neighborhood & Built Environment", "weight": 0.15, "indicators": ["air_quality", "food_desert", "walkability", "safety_score"]},
        "social_community": {"name": "Social & Community Context", "weight": 0.15, "indicators": ["social_support", "community_engagement", "discrimination_experience", "civic_participation"]},
        "food_security": {"name": "Food Security", "weight": 0.10, "indicators": ["food_access", "nutrition_quality", "hunger_risk", "diet_diversity"]},
    }

    INTERVENTION_LIBRARY = {
        "food_access": [
            {"name": "SNAP Enrollment Assistance", "impact": "high", "cost": "low", "description": "Help families enroll in food assistance programs"},
            {"name": "Community Garden Program", "impact": "moderate", "cost": "moderate", "description": "Establish community gardens in food deserts"},
            {"name": "Mobile Food Pantry", "impact": "high", "cost": "moderate", "description": "Regular mobile food distribution in underserved areas"},
        ],
        "healthcare_access": [
            {"name": "Telehealth Bridge Program", "impact": "high", "cost": "low", "description": "Provide telehealth access for remote communities"},
            {"name": "Community Health Worker", "impact": "high", "cost": "moderate", "description": "Deploy CHWs for health education and navigation"},
            {"name": "Transportation Vouchers", "impact": "moderate", "cost": "low", "description": "Provide ride vouchers to medical appointments"},
        ],
        "economic_stability": [
            {"name": "Job Training Partnership", "impact": "high", "cost": "moderate", "description": "Partner with employers for health-sector jobs"},
            {"name": "Financial Literacy Workshop", "impact": "moderate", "cost": "low", "description": "Teach budgeting, savings, and benefits navigation"},
            {"name": "Emergency Assistance Fund", "impact": "high", "cost": "moderate", "description": "Emergency funds for medical expenses"},
        ],
        "education": [
            {"name": "Digital Literacy Program", "impact": "moderate", "cost": "low", "description": "Teach technology skills for health management"},
            {"name": "Health Literacy Workshops", "impact": "high", "cost": "low", "description": "Teach health navigation and self-advocacy"},
        ],
        "social_support": [
            {"name": "Peer Support Groups", "impact": "moderate", "cost": "low", "description": "Connect individuals with similar health challenges"},
            {"name": "Mentorship Program", "impact": "moderate", "cost": "low", "description": "Pair community members with health mentors"},
        ],
    }

    RESOURCE_TYPES = ["food_bank", "health_clinic", "mental_health_center", "housing_assistance", "job_center", "legal_aid", "pharmacy", "dental_clinic", "urgent_care", "community_center"]

    def __init__(self):
        self.community_profiles: Dict[str, dict] = {}
        self.interventions: Dict[str, List[dict]] = {}
        self.resources: Dict[str, List[dict]] = {}
        self.outcomes: Dict[str, List[dict]] = {}

    def create_community_profile(self, community_id: str, name: str, population: int, demographics: dict = None) -> dict:
        profile = {
            "id": community_id,
            "name": name,
            "population": population,
            "demographics": demographics or {},
            "sdoh_scores": {},
            "overall_score": 0,
            "created_at": datetime.now().isoformat(),
        }
        self.community_profiles[community_id] = profile
        return profile

    def calculate_sdoh_score(self, community_id: str, category_scores: Dict[str, float]) -> dict:
        profile = self.community_profiles.get(community_id)
        if not profile:
            return {"error": "Community not found"}
        
        weighted_total = 0
        total_weight = 0
        category_results = {}
        
        for cat_key, cat_config in self.SDOH_CATEGORIES.items():
            raw_score = category_scores.get(cat_key, 50)
            normalized = min(max(raw_score, 0), 100)
            weighted = normalized * cat_config["weight"]
            weighted_total += weighted
            total_weight += cat_config["weight"]
            category_results[cat_key] = {"name": cat_config["name"], "score": normalized, "weight": cat_config["weight"], "weighted_score": round(weighted, 2)}
        
        overall = round(weighted_total / max(total_weight, 0.01), 1)
        profile["sdoh_scores"] = category_results
        profile["overall_score"] = overall
        profile["equity_grade"] = "A" if overall >= 80 else "B" if overall >= 65 else "C" if overall >= 50 else "D" if overall >= 35 else "F"
        
        return {"community_id": community_id, "overall_score": overall, "grade": profile["equity_grade"], "categories": category_results, "calculated_at": datetime.now().isoformat()}

    def get_interventions(self, category: str = None) -> List[dict]:
        interventions = []
        for cat, items in self.INTERVENTION_LIBRARY.items():
            if category and cat != category:
                continue
            for item in items:
                interventions.append({**item, "category": cat})
        return interventions

    def recommend_interventions(self, community_id: str) -> List[dict]:
        profile = self.community_profiles.get(community_id)
        if not profile or not profile.get("sdoh_scores"):
            return []
        
        weak_categories = [k for k, v in profile["sdoh_scores"].items() if v["score"] < 60]
        recommendations = []
        for cat in weak_categories:
            cat_name = cat.replace("_", " ")
            for intervention in self.INTERVENTION_LIBRARY.get(cat, []):
                recommendations.append({**intervention, "target_category": cat, "priority": "high" if intervention["impact"] == "high" else "medium"})
        
        return sorted(recommendations, key=lambda x: {"high": 3, "moderate": 2, "low": 1}.get(x["impact"], 0), reverse=True)[:10]

    def add_resource(self, community_id: str, name: str, resource_type: str, address: str, phone: str, hours: str = "") -> dict:
        resource = {"id": str(uuid.uuid4()), "name": name, "type": resource_type, "address": address, "phone": phone, "hours": hours, "added_at": datetime.now().isoformat()}
        self.resources.setdefault(community_id, []).append(resource)
        return resource

    def get_resources(self, community_id: str, resource_type: str = None) -> List[dict]:
        resources = self.resources.get(community_id, [])
        if resource_type:
            resources = [r for r in resources if r["type"] == resource_type]
        return resources

    def log_intervention_outcome(self, community_id: str, intervention_name: str, metric: str, before: float, after: float) -> dict:
        outcome = {"id": str(uuid.uuid4()), "intervention": intervention_name, "metric": metric, "before": before, "after": after, "improvement": round(after - before, 2), "improvement_pct": round((after - before) / max(before, 0.01) * 100, 1), "recorded_at": datetime.now().isoformat()}
        self.outcomes.setdefault(community_id, []).append(outcome)
        return outcome


health_equity = HealthEquityService()
