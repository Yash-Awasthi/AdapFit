"""
Tests for the startup configuration validation.

Verifies:
  - Production mode fails fast on missing JWT_SECRET_KEY
  - Dev mode logs warnings but doesn't exit
  - Insecure placeholder JWT keys are detected
  - Missing LLM keys produce warnings in dev, errors in prod
  - AUTH_DISABLED=True is an error in production
  - Missing DATABASE_URL is an error in production
"""
import os
import sys
from unittest.mock import patch, MagicMock


def _reload_settings(**env_overrides):
    """Reload the settings module with the given env vars."""
    # Patch env vars
    old_env = dict(os.environ)
    os.environ.update(env_overrides)
    try:
        # Force reimport of config + startup_checks
        for mod in list(sys.modules.keys()):
            if "config" in mod or "startup_checks" in mod:
                del sys.modules[mod]
        from app.core.startup_checks import validate_startup
        return validate_startup()
    finally:
        os.environ.clear()
        os.environ.update(old_env)
        # Re-reload to restore original settings
        for mod in list(sys.modules.keys()):
            if "config" in mod or "startup_checks" in mod:
                del sys.modules[mod]


def test_dev_mode_no_jwt_produces_warning_not_error():
    """In dev mode, missing JWT should NOT produce a fatal error."""
    errors = _reload_settings(
        ENVIRONMENT="development",
        JWT_SECRET_KEY="",
        AUTH_DISABLED="false",
    )
    # In dev, JWT missing is a warning, not an error
    jwt_errors = [e for e in errors if "JWT" in e]
    assert len(jwt_errors) == 0, "dev mode should not error on missing JWT"


def test_prod_mode_missing_jwt_produces_error():
    """In production, missing JWT_SECRET_KEY should produce an error."""
    errors = _reload_settings(
        ENVIRONMENT="production",
        JWT_SECRET_KEY="",
        AUTH_DISABLED="false",
        DATABASE_URL="postgresql://localhost/db",
        GEMINI_API_KEY="test-key",
    )
    jwt_errors = [e for e in errors if "JWT" in e]
    assert len(jwt_errors) == 1, "prod should error on missing JWT"


def test_prod_mode_short_jwt_produces_error():
    """In production, a short JWT_SECRET_KEY should produce an error."""
    errors = _reload_settings(
        ENVIRONMENT="production",
        JWT_SECRET_KEY="short",
        AUTH_DISABLED="false",
        DATABASE_URL="postgresql://localhost/db",
        GEMINI_API_KEY="test-key",
    )
    jwt_errors = [e for e in errors if "JWT" in e]
    assert len(jwt_errors) == 1, "prod should error on short JWT"


def test_prod_mode_placeholder_jwt_produces_error():
    """In production, a placeholder JWT_SECRET_KEY should produce an error."""
    errors = _reload_settings(
        ENVIRONMENT="production",
        JWT_SECRET_KEY="change-me",
        AUTH_DISABLED="false",
        DATABASE_URL="postgresql://localhost/db",
        GEMINI_API_KEY="test-key",
    )
    jwt_errors = [e for e in errors if "JWT" in e]
    assert len(jwt_errors) == 1, "prod should error on placeholder JWT"


def test_prod_mode_valid_jwt_passes():
    """In production, a valid JWT_SECRET_KEY should NOT produce a JWT error."""
    errors = _reload_settings(
        ENVIRONMENT="production",
        JWT_SECRET_KEY="a" * 32,  # 32-char secure key
        AUTH_DISABLED="false",
        DATABASE_URL="postgresql://localhost/db",
        GEMINI_API_KEY="test-key",
    )
    jwt_errors = [e for e in errors if "JWT" in e]
    assert len(jwt_errors) == 0, "valid JWT should not error"


def test_prod_mode_no_llm_keys_produces_error():
    """In production, no LLM keys should produce an error."""
    errors = _reload_settings(
        ENVIRONMENT="production",
        JWT_SECRET_KEY="a" * 32,
        AUTH_DISABLED="false",
        DATABASE_URL="postgresql://localhost/db",
        GEMINI_API_KEY="",
        GROQ_API_KEY="",
    )
    llm_errors = [e for e in errors if "LLM" in e or "provider" in e.lower()]
    assert len(llm_errors) == 1, "prod should error on no LLM keys"


def test_prod_mode_auth_disabled_produces_error():
    """In production, AUTH_DISABLED=True should produce an error."""
    errors = _reload_settings(
        ENVIRONMENT="production",
        JWT_SECRET_KEY="a" * 32,
        AUTH_DISABLED="true",
        DATABASE_URL="postgresql://localhost/db",
        GEMINI_API_KEY="test-key",
    )
    auth_errors = [e for e in errors if "AUTH_DISABLED" in e]
    assert len(auth_errors) == 1, "prod should error on AUTH_DISABLED=True"


def test_prod_mode_no_database_url_produces_error():
    """In production, missing DATABASE_URL should produce an error."""
    errors = _reload_settings(
        ENVIRONMENT="production",
        JWT_SECRET_KEY="a" * 32,
        AUTH_DISABLED="false",
        DATABASE_URL="",
        GEMINI_API_KEY="test-key",
    )
    db_errors = [e for e in errors if "DATABASE_URL" in e]
    assert len(db_errors) == 1, "prod should error on missing DATABASE_URL"


def test_dev_mode_no_errors():
    """In dev mode with all optional settings missing, no errors should be produced."""
    errors = _reload_settings(
        ENVIRONMENT="development",
        JWT_SECRET_KEY="",
        AUTH_DISABLED="false",
        DATABASE_URL="",
        GEMINI_API_KEY="",
        GROQ_API_KEY="",
    )
    assert len(errors) == 0, "dev mode should produce no errors (warnings only)"


def test_run_startup_checks_dev_mode_does_not_exit():
    """run_startup_checks in dev mode should not call sys.exit."""
    with patch.dict(os.environ, {"ENVIRONMENT": "development", "JWT_SECRET_KEY": ""}):
        for mod in list(sys.modules.keys()):
            if "config" in mod or "startup_checks" in mod:
                del sys.modules[mod]
        from app.core.startup_checks import run_startup_checks
        # Should not raise SystemExit in dev mode
        try:
            run_startup_checks()
        except SystemExit:
            assert False, "run_startup_checks should not exit in dev mode"
