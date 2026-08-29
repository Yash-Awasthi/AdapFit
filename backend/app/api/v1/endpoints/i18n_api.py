"""Internationalization — translation strings, RTL support, locale formatting."""
from fastapi import APIRouter
from app.services.i18n import (
    get_translation, get_all_strings, is_rtl, format_number,
    get_locale_config, supported_locales,
)

router = APIRouter()


@router.get("/strings/{locale}")
async def get_strings(locale: str):
    """Get all translation strings for a locale."""
    return {"locale": locale, "strings": get_all_strings(locale)}


@router.get("/translate")
async def translate(key: str, locale: str = "en"):
    """Get a single translated string."""
    return {"key": key, "locale": locale, "translation": get_translation(key, locale)}


@router.get("/locale/{locale}")
async def locale_config(locale: str):
    """Get locale configuration (direction, formatting, etc.)."""
    return get_locale_config(locale)


@router.get("/locales")
async def locales():
    """List all supported locales."""
    return {"locales": supported_locales()}


@router.get("/format/number")
async def format_num(value: float, locale: str = "en", decimals: int = 1):
    """Format a number according to locale conventions."""
    return {"value": value, "locale": locale, "formatted": format_number(value, locale, decimals)}
