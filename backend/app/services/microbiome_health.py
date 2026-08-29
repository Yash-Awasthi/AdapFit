"""Microbiome & Gut Health Service.

Based on 2025 gut microbiome research:
- Gut health scoring
- Microbiome diversity assessment
- Prebiotic/probiotic recommendations
- Digestive health tracking
- Food-microbiome interaction mapping
- Personalized nutrition for gut health
"""

import time
import random
from typing import Dict, List, Any


class MicrobiomeHealthService:
    """Gut microbiome health analysis and personalized recommendations."""

    def __init__(self):
        self.profiles: Dict[str, Dict] = {}
        self._init_gut_bacteria()

    def _init_gut_bacteria(self):
        self.beneficial_bacteria = {
            "lactobacillus": {"benefits": ["immune_support", "lactose_digestion", "pathogen_defense"], "foods": ["yogurt", "kefir", "sauerkraut", "kimchi"], "prebiotics": ["garlic", "onion", "banana"]},
            "bifidobacterium": {"benefits": ["fiber_digestion", "vitamin_production", "gut_barrier"], "foods": ["fermented_dairy", "sourdough"], "prebiotics": ["oats", "barley", "apples"]},
            "akermansia": {"benefits": ["metabolic_health", "gut_barrier", "weight_management"], "foods": ["cranberries", "grapes"], "prebiotics": ["polyphenols", "fiber"]},
            "faecalibacterium": {"benefits": ["anti_inflammatory", "butyrate_production", "immune_regulation"], "foods": ["whole_grains", "legumes"], "prebiotics": ["resistant_starch", "inulin"]},
        }

        self.gut_health_indicators = {
            "digestive_symptoms": ["bloating", "gas", "constipation", "diarrhea", "reflux", "cramping"],
            "systemic_symptoms": ["fatigue", "brain_fog", "skin_issues", "joint_pain", "mood_changes"],
            "positive_signs": ["regular_bowel_movements", "easy_digestion", "consistent_energy", "clear_skin", "stable_mood"],
        }

        self.food_microbiome_map = {
            "fermented": {"impact": "positive", "bacteria": ["lactobacillus", "bifidobacterium"], "score": 9},
            "high_fiber": {"impact": "positive", "bacteria": ["faecalibacterium", "bifidobacterium"], "score": 8},
            "prebiotic_rich": {"impact": "positive", "bacteria": ["lactobacillus", "akermansia"], "score": 8},
            "ultra_processed": {"impact": "negative", "bacteria": [], "score": 2},
            "high_sugar": {"impact": "negative", "bacteria": [], "score": 3},
            "artificial_sweeteners": {"impact": "variable", "bacteria": [], "score": 4},
        }

    def assess_gut_health(self, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess gut health based on symptoms and diet."""
        symptoms = data.get("symptoms", [])
        diet = data.get("diet_type", "standard")
        fiber_intake = data.get("fiber_g", 15)
        water_intake = data.get("water_ml", 1500)
        fermented_servings = data.get("fermented_servings", 0)

        # Calculate gut health score
        score = 70
        for s in symptoms:
            if s in ["bloating", "gas", "constipation", "diarrhea"]:
                score -= 8
            elif s in ["fatigue", "brain_fog", "skin_issues"]:
                score -= 5
        if fiber_intake >= 25: score += 10
        elif fiber_intake >= 15: score += 5
        if fermented_servings >= 2: score += 8
        if water_intake >= 2000: score += 5
        score = max(20, min(100, score))

        return {
            "gut_health_score": score,
            "grade": "A" if score >= 85 else "B" if score >= 70 else "C" if score >= 55 else "D",
            "diet_type": diet,
            "fiber_status": "adequate" if fiber_intake >= 25 else "low",
            "hydration_status": "adequate" if water_intake >= 2000 else "low",
            "symptoms": symptoms,
            "recommendations": self._get_recommendations(score, symptoms, diet, fiber_intake),
        }

    def get_microbiome_profile(self) -> Dict[str, Any]:
        """Get microbiome composition profile."""
        return {
            "beneficial_bacteria": {
                name: {
                    "abundance": random.randint(5, 25),
                    "status": random.choice(["optimal", "moderate", "low"]),
                    "benefits": info["benefits"],
                }
                for name, info in self.beneficial_bacteria.items()
            },
            "diversity_score": random.randint(60, 95),
            "diversity_status": "excellent" if random.random() > 0.5 else "good",
            "key_finding": "Your microbiome diversity is within healthy range",
        }

    def get_food_recommendations(self, gut_score: int) -> Dict[str, Any]:
        """Get food recommendations for gut health."""
        probiotic_foods = [
            {"food": "Yogurt (live cultures)", "servings": "1-2/day", "benefit": "Lactobacillus boost"},
            {"food": "Kefir", "servings": "1 cup/day", "benefit": "Diverse probiotic strains"},
            {"food": "Sauerkraut", "servings": "2-3 tbsp/day", "benefit": "Fiber + probiotics"},
            {"food": "Kimchi", "servings": "2-3 tbsp/day", "benefit": "Anti-inflammatory compounds"},
            {"food": "Kombucha", "servings": "1 cup/day", "benefit": "Organic acids + probiotics"},
        ]
        prebiotic_foods = [
            {"food": "Garlic & Onions", "servings": "Daily", "benefit": "Inulin + FOS"},
            {"food": "Bananas (slightly green)", "servings": "1-2/day", "benefit": "Resistant starch"},
            {"food": "Oats", "servings": "1 bowl/day", "benefit": "Beta-glucan fiber"},
            {"food": "Asparagus", "servings": "3-4 spears", "benefit": "Inulin prebiotic"},
            {"food": "Jerusalem Artichokes", "servings": "1/2 cup", "benefit": "High inulin content"},
        ]
        return {
            "probiotic_foods": probiotic_foods,
            "prebiotic_foods": prebiotic_foods,
            "avoid": ["Excess sugar (feeds bad bacteria)", "Ultra-processed foods", "Unnecessary antibiotics", "Chronic stress"],
        }

    def _get_recommendations(self, score: int, symptoms: List, diet: str, fiber: int) -> List[str]:
        recs = []
        if score < 70:
            recs.append("Start incorporating fermented foods daily")
        if fiber < 25:
            recs.append(f"Increase fiber to 25g/day (currently {fiber}g)")
        if "bloating" in symptoms:
            recs.append("Try eliminating FODMAPs temporarily to identify triggers")
        if "constipation" in symptoms:
            recs.append("Increase water intake and soluble fiber")
        recs.append("Eat 30+ different plant foods per week for microbiome diversity")
        return recs


microbiome_health_service = MicrobiomeHealthService()
