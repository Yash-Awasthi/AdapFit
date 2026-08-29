"""
Internationalization (i18n) Service

Translation keys for all UI strings, RTL support detection,
locale-aware date/number formatting.
"""
from dataclasses import dataclass, field
from typing import Optional


# RTL languages
RTL_LANGUAGES = {"ar", "he", "fa", "ur", "ps", "sd", "yi", "ku", "ckb"}

# Locale formatting rules
LOCALE_FORMATS = {
    "en":    {"decimal": ".", "thousands": ",", "date": "MM/DD/YYYY", "time": "hh:mm A"},
    "en-GB": {"decimal": ".", "thousands": ",", "date": "DD/MM/YYYY", "time": "HH:mm"},
    "de":    {"decimal": ",", "thousands": ".", "date": "DD.MM.YYYY", "time": "HH:mm"},
    "fr":    {"decimal": ",", "thousands": " ", "date": "DD/MM/YYYY", "time": "HH:mm"},
    "es":    {"decimal": ",", "thousands": ".", "date": "DD/MM/YYYY", "time": "HH:mm"},
    "pt":    {"decimal": ",", "thousands": ".", "date": "DD/MM/YYYY", "time": "HH:mm"},
    "ja":    {"decimal": ".", "thousands": ",", "date": "YYYY年MM月DD日", "time": "HH:mm"},
    "ko":    {"decimal": ".", "thousands": ",", "date": "YYYY년 MM월 DD일", "time": "HH:mm"},
    "zh":    {"decimal": ".", "thousands": ",", "date": "YYYY年MM月DD日", "time": "HH:mm"},
    "ar":    {"decimal": "٫", "thousands": "٬", "date": "DD/MM/YYYY", "time": "hh:mm"},
    "hi":    {"decimal": ".", "thousands": ",", "date": "DD/MM/YYYY", "time": "hh:mm A"},
    "ru":    {"decimal": ",", "thousands": " ", "date": "DD.MM.YYYY", "time": "HH:mm"},
    "default": {"decimal": ".", "thousands": ",", "date": "YYYY-MM-DD", "time": "HH:mm"},
}


# Translation strings — English base, other locales overlay
TRANSLATIONS = {
    "en": {
        # Navigation
        "nav.home": "Home",
        "nav.workouts": "Workouts",
        "nav.nutrition": "Nutrition",
        "nav.sleep": "Sleep",
        "nav.recovery": "Recovery",
        "nav.profile": "Profile",
        "nav.settings": "Settings",
        # Workouts
        "workout.start": "Start Workout",
        "workout.pause": "Pause",
        "workout.resume": "Resume",
        "workout.finish": "Finish",
        "workout.cancel": "Cancel",
        "workout.set_complete": "Set Complete",
        "workout.rest_timer": "Rest Timer",
        "workout.next_exercise": "Next Exercise",
        "workout.difficulty": "Difficulty",
        "workout.reps": "Reps",
        "workout.sets": "Sets",
        "workout.weight": "Weight",
        "workout.rpe": "Rate of Exertion",
        # Recovery
        "recovery.score": "Recovery Score",
        "recovery.state": "Readiness State",
        "recovery.optimal": "Optimal",
        "recovery.moderate": "Moderate",
        "recovery.reduced": "Reduced",
        "recovery.depleted": "Depleted",
        # Nutrition
        "nutrition.calories": "Calories",
        "nutrition.protein": "Protein",
        "nutrition.carbs": "Carbs",
        "nutrition.fat": "Fat",
        "nutrition.water": "Water",
        "nutrition.add_meal": "Add Meal",
        # Sleep
        "sleep.quality": "Sleep Quality",
        "sleep.duration": "Duration",
        "sleep.deep": "Deep Sleep",
        "sleep.rem": "REM Sleep",
        "sleep.debt": "Sleep Debt",
        # Onboarding
        "onboard.welcome": "Welcome to AdapFit",
        "onboard.profile": "Create Your Profile",
        "onboard.goals": "Set Your Goals",
        "onboard.connect": "Connect a Device",
        "onboard.first_workout": "Your First Workout",
        # Accessibility
        "access.standing": "Standing",
        "access.seated": "Seated",
        "access.wheelchair": "Wheelchair",
        "access.low_impact": "Low Impact",
        "access.alternative": "Show Alternative",
        # General
        "general.save": "Save",
        "general.cancel": "Cancel",
        "general.delete": "Delete",
        "general.edit": "Edit",
        "general.loading": "Loading...",
        "general.error": "Something went wrong",
        "general.retry": "Try Again",
    },
    "es": {
        "nav.home": "Inicio",
        "nav.workouts": "Entrenamientos",
        "nav.nutrition": "Nutrición",
        "nav.sleep": "Sueño",
        "nav.recovery": "Recuperación",
        "workout.start": "Iniciar Entrenamiento",
        "workout.pause": "Pausar",
        "workout.finish": "Finalizar",
        "general.save": "Guardar",
        "general.cancel": "Cancelar",
        "onboard.welcome": "Bienvenido a AdapFit",
    },
    "de": {
        "nav.home": "Startseite",
        "nav.workouts": "Workouts",
        "nav.nutrition": "Ernährung",
        "nav.sleep": "Schlaf",
        "nav.recovery": "Erholung",
        "workout.start": "Workout starten",
        "workout.pause": "Pause",
        "workout.finish": "Beenden",
        "general.save": "Speichern",
        "general.cancel": "Abbrechen",
    },
    "ja": {
        "nav.home": "ホーム",
        "nav.workouts": "ワークアウト",
        "nav.nutrition": "栄養",
        "nav.sleep": "睡眠",
        "nav.recovery": "回復",
        "workout.start": "ワークアウト開始",
        "general.save": "保存",
        "general.cancel": "キャンセル",
    },
}


def get_translation(key: str, locale: str = "en") -> str:
    """Get a translated string by key and locale, falling back to English."""
    locale_dict = TRANSLATIONS.get(locale, TRANSLATIONS["en"])
    return locale_dict.get(key, TRANSLATIONS["en"].get(key, key))


def get_all_strings(locale: str = "en") -> dict:
    """Get all translation strings for a locale, merged with English fallback."""
    base = dict(TRANSLATIONS["en"])
    if locale != "en" and locale in TRANSLATIONS:
        base.update(TRANSLATIONS[locale])
    return base


def is_rtl(locale: str) -> bool:
    """Check if a locale uses right-to-left text direction."""
    lang = locale.split("-")[0].lower()
    return lang in RTL_LANGUAGES


def format_number(value: float, locale: str = "en", decimals: int = 1) -> str:
    """Format a number according to locale conventions."""
    fmt = LOCALE_FORMATS.get(locale, LOCALE_FORMATS["default"])
    dec_sep = fmt["decimal"]
    thou_sep = fmt["thousands"]

    # Format with Python then replace separators
    if decimals > 0:
        parts = f"{value:,.{decimals}f}".split(".")
    else:
        parts = [f"{value:,.0f}"]

    integer_part = parts[0].replace(",", thou_sep)
    if len(parts) > 1:
        decimal_part = parts[1].replace(".", dec_sep)
        return f"{integer_part}{dec_sep}{decimal_part}"
    return integer_part


def get_locale_config(locale: str) -> dict:
    """Get full locale configuration (formatting, direction, etc.)."""
    fmt = LOCALE_FORMATS.get(locale, LOCALE_FORMATS["default"])
    return {
        "locale": locale,
        "rtl": is_rtl(locale),
        "direction": "rtl" if is_rtl(locale) else "ltr",
        "decimal_separator": fmt["decimal"],
        "thousands_separator": fmt["thousands"],
        "date_format": fmt["date"],
        "time_format": fmt["time"],
    }


def supported_locales() -> list[dict]:
    """List all supported locales with their configurations."""
    locales = set(TRANSLATIONS.keys()) | set(LOCALE_FORMATS.keys())
    locales.discard("default")
    return [get_locale_config(loc) for loc in sorted(locales)]
