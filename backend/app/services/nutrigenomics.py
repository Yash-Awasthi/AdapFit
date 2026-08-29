"""
Nutrigenomics & DNA-Based Personalized Nutrition Service
Genetic variation analysis for dietary recommendations
"""
from datetime import datetime
from typing import Dict, List, Optional, Any
import random


class NutrigenomicsService:
    """DNA-based personalized nutrition platform"""

    def __init__(self):
        self.gene_variants = {
            "MTHFR": {
                "full_name": "Methylenetetrahydrofolate Reductase",
                "function": "Folate metabolism and methylation",
                "common_variants": ["C677T", "A1298C"],
                "health_implications": ["elevated homocysteine", "cardiovascular risk", "neural tube defects", "depression"],
                "nutrient_focus": ["folate", "B12", "B6", "riboflavin", "choline", "betaine"],
                "food_recommendations": [
                    "Leafy greens (spinach, kale, romaine)",
                    "Legumes (lentils, chickpeas, black beans)",
                    "Asparagus, broccoli, Brussels sprouts",
                    "Liver (chicken, beef) — in moderation",
                    "Eggs",
                    "Citrus fruits",
                    "Beets"
                ],
                "foods_to_limit": [
                    "Folic acid fortified foods (if MTHFR homozygous)",
                    "Excessive alcohol (increases folate need)",
                    "Refined grains"
                ],
                "supplements": ["methylfolate (5-MTHF)", "methylcobalamin (B12)", "pyridoxal-5-phosphate (B6)"]
            },
            "FTO": {
                "full_name": "Fat Mass and Obesity-associated",
                "function": "Appetite regulation, energy homeostasis",
                "common_variants": ["rs9939609"],
                "health_implications": ["increased obesity risk", "higher caloric intake", "increased appetite"],
                "nutrient_focus": ["protein", "fiber", "omega-3"],
                "food_recommendations": [
                    "High-protein breakfast (eggs, Greek yogurt, cottage cheese)",
                    "High-fiber foods (beans, whole grains, vegetables)",
                    "Omega-3 rich fish (salmon, sardines, mackerel)",
                    "Nuts and seeds (almonds, walnuts, chia seeds)",
                    "Lean proteins (chicken breast, turkey, tofu)",
                    "Non-starchy vegetables"
                ],
                "foods_to_limit": [
                    "Highly processed foods",
                    "Sugary beverages",
                    "Refined carbohydrates",
                    "Large portion sizes"
                ],
                "supplements": ["omega-3 fish oil", "glucomannan (pre-meal fiber)"]
            },
            "APOE": {
                "full_name": "Apolipoprotein E",
                "function": "Cholesterol transport, lipid metabolism",
                "common_variants": ["ε2", "ε3", "ε4"],
                "health_implications": ["Alzheimer's risk (ε4)", "cardiovascular disease", "cholesterol metabolism"],
                "nutrient_focus": ["healthy fats", "antioxidants", "omega-3"],
                "food_recommendations": [
                    "Fatty fish 3-4x per week",
                    "Extra virgin olive oil (daily)",
                    "Berries (blueberries, strawberries)",
                    "Nuts (walnuts especially)",
                    "Dark leafy greens",
                    "Whole grains",
                    "Green tea"
                ],
                "foods_to_limit": [
                    "Saturated fats (red meat, butter, cheese)",
                    "Trans fats",
                    "Excessive alcohol",
                    "Coconut oil (high in saturated fat)"
                ],
                "supplements": ["omega-3 DHA/EPA", "coenzyme Q10", "vitamin D"]
            },
            "CYP1A2": {
                "full_name": "Cytochrome P450 1A2",
                "function": "Caffeine metabolism",
                "common_variants": ["rs762551"],
                "health_implications": ["slow/fast caffeine metabolism", "cardiovascular risk with caffeine"],
                "nutrient_focus": ["caffeine management", "antioxidants"],
                "food_recommendations": [
                    "Green tea (if slow metabolizer)",
                    "Herbal teas (chamomile, peppermint)",
                    "Dark chocolate (limited)",
                    "Water-rich foods"
                ],
                "foods_to_limit": [
                    "Coffee (if slow metabolizer: <2 cups/day)",
                    "Energy drinks",
                    "Pre-workout supplements with caffeine",
                    "Cola beverages"
                ],
                "supplements": ["L-theanine (to offset caffeine effects)"]
            },
            "VDR": {
                "full_name": "Vitamin D Receptor",
                "function": "Vitamin D absorption and utilization",
                "common_variants": ["FokI", "BsmI", "TaqI"],
                "health_implications": ["reduced vitamin D absorption", "bone health", "immune function"],
                "nutrient_focus": ["vitamin D", "calcium", "magnesium"],
                "food_recommendations": [
                    "Fatty fish (salmon, mackerel, sardines)",
                    "Fortified dairy or plant milks",
                    "Egg yolks",
                    "Mushrooms (UV-exposed)",
                    "Cod liver oil",
                    "Cheese"
                ],
                "foods_to_limit": [],
                "supplements": ["vitamin D3 (higher doses may be needed)", "calcium", "magnesium K2"]
            },
            "AMY1": {
                "full_name": "Salivary Amylase",
                "function": "Starch digestion",
                "common_variants": ["copy number variation"],
                "health_implications": ["starch sensitivity", "blood sugar response", "dental health"],
                "nutrient_focus": ["carbohydrate quality", "fiber"],
                "food_recommendations": [
                    "Complex carbohydrates (sweet potatoes, quinoa, oats)",
                    "Resistant starch (cooled rice, green bananas)",
                    "High-fiber foods",
                    "Legumes"
                ],
                "foods_to_limit": [
                    "Refined starches (white bread, pastries)",
                    "Sugary snacks",
                    "Processed cereal"
                ],
                "supplements": ["alpha-amylase digestive enzyme (if needed)"]
            },
            "COMT": {
                "full_name": "Catechol-O-Methyltransferase",
                "function": "Dopamine and catecholamine metabolism",
                "common_variants": ["Val158Met"],
                "health_implications": ["stress resilience", "pain sensitivity", "cognitive performance under stress"],
                "nutrient_focus": ["magnesium", "vitamin C", "B vitamins", "catecholamines"],
                "food_recommendations": [
                    "Green tea (L-theanine for calm focus)",
                    "Dark leafy greens",
                    "Citrus fruits (vitamin C)",
                    "Nuts and seeds (magnesium)",
                    "Fermented foods (gut-brain axis)",
                    "Omega-3 fatty acids"
                ],
                "foods_to_limit": [
                    "Excessive caffeine (if Val/Val fast metabolizer)",
                    "Chocolate in excess (catecholamine load)",
                    "Highly processed foods"
                ],
                "supplements": ["magnesium glycinate", "vitamin C", "L-theanine"]
            },
            "LCT": {
                "full_name": "Lactase Persistence",
                "function": "Lactose digestion",
                "common_variants": ["-13910C>T"],
                "health_implications": ["lactose intolerance", "calcium absorption", "dairy tolerance"],
                "nutrient_focus": ["calcium", "vitamin D", "alternative dairy"],
                "food_recommendations": [
                    "Lactose-free dairy products",
                    "Hard aged cheeses (naturally low lactose)",
                    "Fermented dairy (yogurt, kefir)",
                    "Calcium-set tofu",
                    "Fortified plant milks",
                    "Leafy greens (kale, bok choy)"
                ],
                "foods_to_limit": [
                    "Regular milk (if lactose intolerant)",
                    "Ice cream",
                    "Soft cheeses"
                ],
                "supplements": ["calcium", "vitamin D3", "lactase enzyme (pre-dairy)"]
            },
            "FADS1": {
                "full_name": "Fatty Acid Desaturase 1",
                "function": "Omega-3 and omega-6 fatty acid conversion",
                "common_variants": ["rs174546"],
                "health_implications": ["reduced EPA/DHA conversion", "inflammation", "brain health"],
                "nutrient_focus": ["preformed EPA/DHA", "anti-inflammatory foods"],
                "food_recommendations": [
                    "Fatty fish (salmon, mackerel, sardines) 3-4x/week",
                    "Algae-based omega-3",
                    "Walnuts, flaxseeds, chia seeds",
                    "Avocado",
                    "Olive oil"
                ],
                "foods_to_limit": [
                    "Vegetable oils high in omega-6 (soybean, corn, sunflower)",
                    "Fried foods",
                    "Processed snack foods"
                ],
                "supplements": ["preformed EPA/DHA (fish oil or algae)", "avoid relying on flaxseed alone"]
            }
        }

        self.dietary_patterns = {
            "mediterranean": {
                "genes_supported": ["APOE", "MTHFR", "COMT"],
                "benefits": ["cardiovascular health", "cognitive function", "inflammation reduction"],
                "components": ["olive oil", "fish", "whole grains", "fruits", "vegetables", "moderate wine", "nuts"]
            },
            "dash": {
                "genes_supported": ["VDR", "MTHFR"],
                "benefits": ["blood pressure", "bone health", "heart health"],
                "components": ["low sodium", "high potassium", "dairy", "whole grains", "lean protein"]
            },
            "anti_inflammatory": {
                "genes_supported": ["FADS1", "COMT", "FTO"],
                "benefits": ["reduced inflammation", "pain management", "autoimmune support"],
                "components": ["turmeric", "ginger", "fatty fish", "berries", "leafy greens", "green tea"]
            },
            "low_carb": {
                "genes_supported": ["FTO", "AMY1"],
                "benefits": ["weight management", "blood sugar control", "metabolic health"],
                "components": ["non-starchy vegetables", "lean protein", "healthy fats", "limited grains"]
            }
        }

        self.food_gene_interactions = {
            "broccoli": {"positive_genes": ["MTHFR"], "compounds": ["sulforaphane", "folate"], "benefit": "Supports methylation, detoxification"},
            "salmon": {"positive_genes": ["FADS1", "APOE", "VDR"], "compounds": ["EPA/DHA", "vitamin D"], "benefit": "Anti-inflammatory, brain health, cardiovascular"},
            "spinach": {"positive_genes": ["MTHFR", "VDR"], "compounds": ["folate", "magnesium", "vitamin K"], "benefit": "Methylation support, bone health"},
            "blueberries": {"positive_genes": ["APOE", "COMT"], "compounds": ["anthocyanins", "quercetin"], "benefit": "Cognitive function, neuroprotection"},
            "turmeric": {"positive_genes": ["COMT", "FADS1"], "compounds": ["curcumin"], "benefit": "Anti-inflammatory, neuroprotective"},
            "walnuts": {"positive_genes": ["APOE", "FADS1"], "compounds": ["ALA omega-3", "polyphenols"], "benefit": "Brain health, cardiovascular"},
            "eggs": {"positive_genes": ["MTHFR", "VDR"], "compounds": ["choline", "B12", "vitamin D"], "benefit": "Methylation, bone health"},
            "fermented_foods": {"positive_genes": ["COMT"], "compounds": ["probiotics", "postbiotics"], "benefit": "Gut-brain axis, mood regulation"},
            "green_tea": {"positive_genes": ["COMT", "CYP1A2"], "compounds": ["L-theanine", "EGCG"], "benefit": "Calm focus, antioxidant, metabolism"},
            "avocado": {"positive_genes": ["FTO", "FADS1"], "compounds": ["monounsaturated fats", "potassium"], "benefit": "Satiety, anti-inflammatory, blood pressure"},
            "oats": {"positive_genes": ["AMY1", "FTO"], "compounds": ["beta-glucan fiber", "magnesium"], "benefit": "Blood sugar control, cholesterol reduction"},
            "sardines": {"positive_genes": ["FADS1", "VDR", "MTHFR"], "compounds": ["EPA/DHA", "vitamin D", "B12"], "benefit": "Brain health, bone health, methylation"},
            "beets": {"positive_genes": ["MTHFR"], "compounds": ["nitrate", "betaine"], "benefit": "Nitric oxide production, methylation support"},
            "dark_chocolate": {"positive_genes": ["COMT", "FADS1"], "compounds": ["flavanols", "magnesium"], "benefit": "Mood, cardiovascular, cognitive"}
        }

    def analyze_genetic_profile(self, genetic_data: Dict) -> Dict:
        """Analyze genetic data and provide personalized nutrition recommendations"""
        profile = {
            "assessment_date": datetime.now().isoformat(),
            "genetic_markers": {},
            "dietary_recommendations": [],
            "foods_to_emphasize": [],
            "foods_to_limit": [],
            "supplements_recommended": [],
            "optimal_diet_pattern": None,
            "risk_factors": [],
            "strengths": []
        }

        genes_present = []
        for gene, variant in genetic_data.items():
            if gene in self.gene_variants:
                gene_info = self.gene_variants[gene]
                profile["genetic_markers"][gene] = {
                    "name": gene_info["full_name"],
                    "variant": variant,
                    "implications": gene_info["health_implications"],
                    "focus_nutrients": gene_info["nutrient_focus"]
                }
                genes_present.append(gene)
                profile["foods_to_emphasize"].extend(gene_info["food_recommendations"])
                profile["foods_to_limit"].extend(gene_info["foods_to_limit"])
                profile["supplements_recommended"].extend(gene_info["supplements"])

        # Deduplicate
        profile["foods_to_emphasize"] = list(set(profile["foods_to_emphasize"]))
        profile["foods_to_limit"] = list(set(profile["foods_to_limit"]))
        profile["supplements_recommended"] = list(set(profile["supplements_recommended"]))

        # Determine optimal diet pattern
        best_pattern = None
        best_score = 0
        for pattern_name, pattern_data in self.dietary_patterns.items():
            score = len(set(genes_present) & set(pattern_data["genes_supported"]))
            if score > best_score:
                best_score = score
                best_pattern = pattern_name

        if best_pattern:
            profile["optimal_diet_pattern"] = {
                "name": best_pattern,
                "details": self.dietary_patterns[best_pattern]
            }

        # Food-gene interactions
        profile["personalized_food_insights"] = []
        for food, interaction in self.food_gene_interactions.items():
            relevant_genes = [g for g in interaction["positive_genes"] if g in genes_present]
            if relevant_genes:
                profile["personalized_food_insights"].append({
                    "food": food,
                    "relevance_score": len(relevant_genes) / len(interaction["positive_genes"]),
                    "relevant_genes": relevant_genes,
                    "compounds": interaction["compounds"],
                    "benefit": interaction["benefit"]
                })

        # Sort by relevance
        profile["personalized_food_insights"].sort(key=lambda x: x["relevance_score"], reverse=True)

        return profile

    def get_meal_plan(self, genetic_data: Dict, dietary_restrictions: List[str] = None, calorie_target: int = 2000) -> Dict:
        """Generate a personalized meal plan based on genetics"""
        profile = self.analyze_genetic_profile(genetic_data)

        meals = {
            "breakfast": [
                {
                    "name": "Omega-3 Power Breakfast",
                    "items": ["Smoked salmon on whole grain toast", "Avocado slices", "Poached egg", "Mixed berries", "Green tea"],
                    "calories": 450,
                    "genes_addressed": ["FADS1", "APOE", "MTHFR"],
                    "key_nutrients": ["EPA/DHA", "folate", "choline", "anthocyanins"]
                },
                {
                    "name": "Methylation Support Smoothie",
                    "items": ["Spinach", "Beet powder", "Blueberries", "Greek yogurt", "Flaxseed", "Almond milk"],
                    "calories": 380,
                    "genes_addressed": ["MTHFR", "FADS1"],
                    "key_nutrients": ["folate", "betaine", "ALA omega-3", "probiotics"]
                },
                {
                    "name": "Anti-Inflammatory Oat Bowl",
                    "items": ["Steel-cut oats", "Walnuts", "Turmeric golden milk", "Banana", "Cinnamon"],
                    "calories": 420,
                    "genes_addressed": ["COMT", "AMY1", "FADS1"],
                    "key_nutrients": ["beta-glucan", "curcumin", "ALA omega-3", "magnesium"]
                }
            ],
            "lunch": [
                {
                    "name": "Mediterranean Power Bowl",
                    "items": ["Grilled chicken", "Quinoa", "Roasted vegetables", "Feta cheese", "Olive oil dressing", "Hummus"],
                    "calories": 550,
                    "genes_addressed": ["APOE", "MTHFR", "VDR"],
                    "key_nutrients": ["protein", "folate", "vitamin D", "monounsaturated fats"]
                },
                {
                    "name": "Brain-Boosting Salad",
                    "items": ["Sardines", "Kale", "Avocado", "Hard-boiled egg", "Sunflower seeds", "Lemon-tahini dressing"],
                    "calories": 520,
                    "genes_addressed": ["FADS1", "APOE", "MTHFR", "VDR"],
                    "key_nutrients": ["EPA/DHA", "vitamin K", "choline", "folate"]
                }
            ],
            "dinner": [
                {
                    "name": "Anti-Inflammatory Salmon Dinner",
                    "items": ["Wild-caught salmon", "Steamed broccoli", "Brown rice", "Ginger-turmeric sauce", "Side salad"],
                    "calories": 600,
                    "genes_addressed": ["FADS1", "MTHFR", "COMT"],
                    "key_nutrients": ["EPA/DHA", "sulforaphane", "curcumin", "folate"]
                },
                {
                    "name": "Heart-Healthy Stir Fry",
                    "items": ["Tofu", "Bok choy", "Bell peppers", "Mushrooms", "Brown noodles", "Low-sodium soy sauce"],
                    "calories": 500,
                    "genes_addressed": ["VDR", "MTHFR", "FTO"],
                    "key_nutrients": ["calcium", "vitamin D", "fiber", "folate"]
                }
            ],
            "snacks": [
                {
                    "name": "Gene-Support Snack Box",
                    "items": ["Handful of walnuts", "Blueberries", "Dark chocolate square", "Green tea"],
                    "calories": 200,
                    "genes_addressed": ["APOE", "COMT", "FADS1"]
                },
                {
                    "name": "Folate-Rich Snack",
                    "items": ["Edamame", "Cherry tomatoes", "Hummus", "Whole grain crackers"],
                    "calories": 250,
                    "genes_addressed": ["MTHFR", "FTO"]
                }
            ]
        }

        return {
            "calorie_target": calorie_target,
            "diet_pattern": profile["optimal_diet_pattern"]["name"] if profile["optimal_diet_pattern"] else "balanced",
            "meals": meals,
            "daily_supplements": profile["supplements_recommended"],
            "key_foods_to_include_daily": profile["foods_to_emphasize"][:5],
            "foods_to_avoid": profile["foods_to_limit"][:5]
        }

    def get_supplement_guide(self, genetic_data: Dict) -> List[Dict]:
        """Generate personalized supplement recommendations"""
        supplements = []
        profile = self.analyze_genetic_profile(genetic_data)

        for gene in genetic_data:
            if gene in self.gene_variants:
                gene_info = self.gene_variants[gene]
                for supp in gene_info.get("supplements", []):
                    existing = next((s for s in supplements if s["name"] == supp), None)
                    if existing:
                        existing["reasons"].append(gene)
                        existing["priority"] = max(existing["priority"], "high" if len(existing["reasons"]) > 1 else "medium")
                    else:
                        supplements.append({
                            "name": supp,
                            "reasons": [gene],
                            "priority": "medium",
                            "gene": gene,
                            "related_health": gene_info["health_implications"]
                        })

        supplements.sort(key=lambda x: len(x["reasons"]), reverse=True)
        return supplements


nutrigenomics_service = NutrigenomicsService()
