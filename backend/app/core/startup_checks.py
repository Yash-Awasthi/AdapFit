"""
Startup configuration validation for AdapFit.

Runs at application startup (inside the lifespan context) and validates that
critical settings are present and secure. In development, missing settings
produce warnings. In production, missing/weak critical settings cause a
fail-fast exit with a clear error message — so a misconfigured deploy
can never start silently and break on the first request.

Checks:
  1. JWT_SECRET_KEY must be set and >= 16 chars in production
  2. At least one LLM provider key should be set (Gemini or Groq)
  3. DATABASE_URL should be set in production (warns if missing → in-memory)
  4. AUTH_DISABLED must be False in production
  5. ENVIRONMENT should not be "development" in a production deploy
"""
from __future__ import annotations

import sys
from typing import Any

from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger("adapfit.startup_checks")

# Known insecure placeholder values that must never reach production.
_INSECURE_PLACEHOLDERS = {
    "", "change-me", "changeme", "secret", "your-secret-here",
    "default", "test", "password", "adapfit-secret",
}


def _is_insecure(value: str) -> bool:
    """True if the value is empty, a known placeholder, or too short."""
    return value.lower().strip() in _INSECURE_PLACEHOLDERS or len(value.strip()) < 16


def validate_startup() -> list[str]:
    """Validate critical settings at startup.

    Returns a list of error messages. An empty list means all checks passed.
    In production, any error causes a fail-fast exit.
    In development, errors are logged as warnings.
    """
    is_prod = settings.ENVIRONMENT.lower().strip() == "production"
    errors: list[str] = []

    # ── 1. JWT_SECRET_KEY ──────────────────────────────────────────────────
    jwt_key = settings.JWT_SECRET_KEY
    if _is_insecure(jwt_key):
        if is_prod:
            errors.append(
                "JWT_SECRET_KEY is missing, a placeholder, or too short (<16 chars). "
                "Generate one: python -c \"import secrets; print(secrets.token_hex(32))\""
            )
        else:
            logger.warning(
                "⚠ JWT_SECRET_KEY not set or too short — auth will fail. "
                "Set JWT_SECRET_KEY in .env (min 16 chars)."
            )

    # ── 2. LLM Provider Keys ───────────────────────────────────────────────
    llm_keys = {
        "GEMINI_API_KEY": settings.GEMINI_API_KEY,
        "GROQ_API_KEY": settings.GROQ_API_KEY,
    }
    configured = [name for name, key in llm_keys.items() if key and key.strip()]
    if not configured:
        if is_prod:
            errors.append(
                "No LLM provider keys configured (GEMINI_API_KEY, GROQ_API_KEY all empty). "
                "At least one is required for AI Coach and NLP features."
            )
        else:
            logger.warning(
                "⚠ No LLM provider keys set — AI Coach and NLP will use rule-based fallbacks. "
                "Set GEMINI_API_KEY or GROQ_API_KEY for full AI functionality."
            )

    # ── 3. DATABASE_URL ─────────────────────────────────────────────────────
    db_url = settings.DATABASE_URL
    if not db_url and is_prod:
        errors.append(
            "DATABASE_URL is not set — production requires PostgreSQL. "
            "The in-memory store does not persist across restarts."
        )
    elif not db_url:
        logger.info("ℹ DATABASE_URL not set — using in-memory storage (data won't persist).")

    # ── 4. AUTH_DISABLED must be False in production ────────────────────────
    if settings.AUTH_DISABLED and is_prod:
        errors.append(
            "AUTH_DISABLED=True in production — this disables ALL authentication. "
            "Set AUTH_DISABLED=false or remove it from .env."
        )

    # ── 5. Rate limiting should be enabled in production ────────────────────
    if is_prod and not settings.RATE_LIMITING_ENABLED:
        logger.warning(
            "⚠ RATE_LIMITING_ENABLED is False in production — "
            "all endpoints are unthrottled. Enable for protection against abuse."
        )

    # ── 6. Encryption at rest needs a real key in production ───────────────
    if is_prod:
        import os
        from app.core import crypto
        try:
            if not os.getenv("DATA_ENCRYPTION_KEYS"):
                raise ValueError("DATA_ENCRYPTION_KEYS is not set")
            crypto.keyring()
        except Exception as exc:
            errors.append(f"{exc}. Generate a key: python -c \"from app.core.crypto import new_key; "
                          f"print('k1:' + new_key())\"")
        if not settings.PUBLIC_BASE_URL.startswith("https://"):
            errors.append("PUBLIC_BASE_URL must be https in production: reset and guardian links carry tokens.")

    return errors


def run_startup_checks() -> None:
    """Run all startup checks. In production, exit on any error.

    Called from the lifespan context in main.py.
    """
    logger.info("Running startup configuration checks...")
    errors = validate_startup()

    if errors:
        is_prod = settings.ENVIRONMENT.lower().strip() == "production"
        if is_prod:
            logger.error("=" * 70)
            logger.error("STARTUP VALIDATION FAILED — refusing to start in production:")
            for err in errors:
                logger.error(f"  ✗ {err}")
            logger.error("=" * 70)
            logger.error("Fix the above errors in your .env or environment and restart.")
            sys.exit(1)
        else:
            for err in errors:
                logger.warning(f"  ⚠ {err}")
            logger.warning("Startup validation produced warnings — continuing in dev mode.")

    logger.info("Startup checks completed ✓")
