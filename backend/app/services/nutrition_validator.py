"""Nutrition Validator.

Extracted from wger (inspiration).
Validates ingredient data with macro checks, energy plausibility,
and nutritional completeness scoring.

All pure functions — no DB, no async.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


# Energy factors (kcal per gram)
ENERGY_FACTORS = {
    "protein": 4,
    "carbohydrates": 4,
    "fat": 9,
    "fiber": 2,
    "alcohol": 7,
}

# EU Regulation tolerances
ENERGY_CHECK_MIN_KCAL = 50
ENERGY_CHECK_TOLERANCE_RELATIVE = 0.20  # 20%
ENERGY_CHECK_TOLERANCE_ABSOLUTE_KCAL = 50


@dataclass
class IngredientData:
    """Nutritional ingredient data."""
    name: str
    energy: float  # kcal per 100g
    protein: float  # g per 100g
    carbohydrates: float  # g per 100g
    carbohydrates_sugar: Optional[float] = None
    fat: float = 0.0
    fat_saturated: Optional[float] = None
    fiber: Optional[float] = None
    sodium: Optional[float] = None
    brand: Optional[str] = None
    serving_size_gram: Optional[int] = None
    nutriscore: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of ingredient validation."""
    is_valid: bool
    errors: list[str]
    warnings: list[str]
    nutrition_score: float = 0.0
    completeness: float = 0.0


@dataclass
class MacroBreakdown:
    """Macronutrient breakdown for a food item."""
    protein_pct: float = 0.0
    carbohydrate_pct: float = 0.0
    fat_pct: float = 0.0
    protein_kcal: float = 0.0
    carbohydrate_kcal: float = 0.0
    fat_kcal: float = 0.0
    total_kcal: float = 0.0


# --- Validation ---

def validate_ingredient(ingredient: IngredientData) -> ValidationResult:
    """Validate ingredient data for correctness and plausibility.

    Args:
        ingredient: Ingredient data to validate

    Returns:
        Validation result with errors and warnings
    """
    errors = []
    warnings = []

    # Name validation
    if not ingredient.name:
        errors.append("Name is empty")
    elif len(ingredient.name) > 200:
        errors.append("Name exceeds 200 characters")

    # Brand validation
    if ingredient.brand and len(ingredient.brand) > 200:
        warnings.append("Brand name exceeds 200 characters, will be truncated")

    # Energy validation
    if ingredient.energy < 0:
        errors.append("Energy cannot be negative")
    if ingredient.energy > 1000:
        warnings.append("Energy exceeds 1000 kcal per 100g, verify accuracy")

    # Macro validation
    macros = ["protein", "carbohydrates", "fat"]
    for macro in macros:
        value = getattr(ingredient, macro)
        if value < 0:
            errors.append(f"{macro} cannot be negative")
        if value > 100:
            errors.append(f"{macro} exceeds 100g per 100g of product")

    # Saturated fat <= total fat
    if ingredient.fat_saturated is not None:
        if ingredient.fat_saturated < 0:
            errors.append("Saturated fat cannot be negative")
        if ingredient.fat_saturated > ingredient.fat:
            errors.append(
                f"Saturated fat ({ingredient.fat_saturated}) exceeds total fat ({ingredient.fat})"
            )

    # Sugar <= total carbs
    if ingredient.carbohydrates_sugar is not None:
        if ingredient.carbohydrates_sugar < 0:
            errors.append("Sugar cannot be negative")
        if ingredient.carbohydrates_sugar > ingredient.carbohydrates:
            errors.append(
                f"Sugar ({ingredient.carbohydrates_sugar}) exceeds carbohydrates ({ingredient.carbohydrates})"
            )

    # Total macros check (EU tolerance: 105g per 100g)
    total_macros = ingredient.protein + ingredient.carbohydrates + ingredient.fat
    if total_macros > 105:
        errors.append(
            f"Total macronutrients ({total_macros:.1f}g) exceeds 105g per 100g (EU tolerance)"
        )

    # Sodium validation
    if ingredient.sodium is not None:
        if ingredient.sodium < 0:
            errors.append("Sodium cannot be negative")
        if ingredient.sodium > 100:
            errors.append("Sodium exceeds 100g per 100g of product")

    # Fiber validation
    if ingredient.fiber is not None:
        if ingredient.fiber < 0:
            errors.append("Fiber cannot be negative")
        if ingredient.fiber > 100:
            errors.append("Fiber exceeds 100g per 100g of product")

    # Nutriscore validation
    if ingredient.nutriscore is not None:
        if ingredient.nutriscore not in ("a", "b", "c", "d", "e"):
            errors.append(f"Invalid nutriscore: {ingredient.nutriscore}")

    # Energy plausibility check
    energy_computed = compute_energy_from_macros(ingredient)
    if energy_computed > 0 or ingredient.energy > ENERGY_CHECK_MIN_KCAL:
        energy_lower = (
            ingredient.energy * (1 - ENERGY_CHECK_TOLERANCE_RELATIVE)
            - ENERGY_CHECK_TOLERANCE_ABSOLUTE_KCAL
        )
        energy_upper = (
            ingredient.energy * (1 + ENERGY_CHECK_TOLERANCE_RELATIVE)
            + ENERGY_CHECK_TOLERANCE_ABSOLUTE_KCAL
        )
        if not (energy_lower <= energy_computed <= energy_upper):
            warnings.append(
                f"Computed energy ({energy_computed:.0f} kcal) differs from declared ({ingredient.energy:.0f} kcal)"
            )

    # Serving size validation
    if ingredient.serving_size_gram is not None:
        if ingredient.serving_size_gram <= 0:
            errors.append("Serving size must be positive")

    # Calculate scores
    nutrition_score = calculate_nutrition_score(ingredient)
    completeness = calculate_completeness(ingredient)

    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        nutrition_score=nutrition_score,
        completeness=completeness,
    )


# --- Energy Calculation ---

def compute_energy_from_macros(ingredient: IngredientData) -> float:
    """Compute energy from macronutrients.

    Args:
        ingredient: Ingredient data

    Returns:
        Computed energy in kcal
    """
    energy = 0.0
    energy += ingredient.protein * ENERGY_FACTORS["protein"]
    energy += ingredient.carbohydrates * ENERGY_FACTORS["carbohydrates"]
    energy += ingredient.fat * ENERGY_FACTORS["fat"]
    if ingredient.fiber:
        energy += ingredient.fiber * ENERGY_FACTORS["fiber"]
    return energy


# --- Macro Breakdown ---

def calculate_macro_breakdown(ingredient: IngredientData) -> MacroBreakdown:
    """Calculate macronutrient breakdown.

    Args:
        ingredient: Ingredient data

    Returns:
        Macro breakdown with percentages and kcal
    """
    protein_kcal = ingredient.protein * ENERGY_FACTORS["protein"]
    carb_kcal = ingredient.carbohydrates * ENERGY_FACTORS["carbohydrates"]
    fat_kcal = ingredient.fat * ENERGY_FACTORS["fat"]
    total_kcal = protein_kcal + carb_kcal + fat_kcal

    if total_kcal == 0:
        return MacroBreakdown(total_kcal=0)

    return MacroBreakdown(
        protein_pct=round(protein_kcal / total_kcal * 100, 1),
        carbohydrate_pct=round(carb_kcal / total_kcal * 100, 1),
        fat_pct=round(fat_kcal / total_kcal * 100, 1),
        protein_kcal=round(protein_kcal, 1),
        carbohydrate_kcal=round(carb_kcal, 1),
        fat_kcal=round(fat_kcal, 1),
        total_kcal=round(total_kcal, 1),
    )


# --- Scoring ---

def calculate_nutrition_score(ingredient: IngredientData) -> float:
    """Calculate nutrition score (0-100).

    Based on a simplified FSA scoring model:
    - Negative points: energy, sugar, saturated fat, sodium
    - Positive points: fiber, protein, fruit/vegetable content (not available)

    Args:
        ingredient: Ingredient data

    Returns:
        Nutrition score 0-100
    """
    score = 50.0  # Start at neutral

    # Energy penalty (per 100g)
    if ingredient.energy > 335:
        score -= min(20, (ingredient.energy - 335) / 50)

    # Sugar penalty
    if ingredient.carbohydrates_sugar is not None:
        if ingredient.carbohydrates_sugar > 45:
            score -= 20
        elif ingredient.carbohydrates_sugar > 15:
            score -= 10

    # Saturated fat penalty
    if ingredient.fat_saturated is not None:
        if ingredient.fat_saturated > 5:
            score -= 15
        elif ingredient.fat_saturated > 1.5:
            score -= 8

    # Sodium penalty (convert g to mg for scoring)
    if ingredient.sodium is not None:
        sodium_mg = ingredient.sodium * 1000
        if sodium_mg > 900:
            score -= 15
        elif sodium_mg > 300:
            score -= 8

    # Fiber bonus
    if ingredient.fiber is not None:
        if ingredient.fiber > 6:
            score += 15
        elif ingredient.fiber > 3:
            score += 8

    # Protein bonus
    if ingredient.protein > 8:
        score += 10
    elif ingredient.protein > 4:
        score += 5

    # Nutriscore adjustment
    if ingredient.nutriscore:
        nutriscore_adj = {"a": 15, "b": 8, "c": 0, "d": -8, "e": -15}
        score += nutriscore_adj.get(ingredient.nutriscore, 0)

    return round(max(0, min(100, score)), 1)


def calculate_completeness(ingredient: IngredientData) -> float:
    """Calculate data completeness (0-1).

    Args:
        ingredient: Ingredient data

    Returns:
        Completeness score 0-1
    """
    fields = [
        ingredient.name,
        ingredient.energy,
        ingredient.protein,
        ingredient.carbohydrates,
        ingredient.fat,
        ingredient.fat_saturated,
        ingredient.fiber,
        ingredient.sodium,
        ingredient.brand,
        ingredient.nutriscore,
    ]

    filled = sum(1 for f in fields if f is not None and f != "" and f != 0)
    return round(filled / len(fields), 2)


# --- Serving Size Calculations ---

def scale_to_serving(
    ingredient: IngredientData,
    serving_grams: float,
) -> dict:
    """Scale nutritional values to a serving size.

    Args:
        ingredient: Ingredient data (per 100g)
        serving_grams: Serving size in grams

    Returns:
        Scaled nutritional values
    """
    factor = serving_grams / 100.0

    return {
        "name": ingredient.name,
        "serving_grams": serving_grams,
        "energy": round(ingredient.energy * factor, 1),
        "protein": round(ingredient.protein * factor, 1),
        "carbohydrates": round(ingredient.carbohydrates * factor, 1),
        "carbohydrates_sugar": (
            round(ingredient.carbohydrates_sugar * factor, 1)
            if ingredient.carbohydrates_sugar is not None
            else None
        ),
        "fat": round(ingredient.fat * factor, 1),
        "fat_saturated": (
            round(ingredient.fat_saturated * factor, 1)
            if ingredient.fat_saturated is not None
            else None
        ),
        "fiber": (
            round(ingredient.fiber * factor, 1)
            if ingredient.fiber is not None
            else None
        ),
        "sodium": (
            round(ingredient.sodium * factor, 1)
            if ingredient.sodium is not None
            else None
        ),
    }
