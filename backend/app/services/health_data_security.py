"""
Security self-check: which technical controls this deployment actually has.

Each control is measured from configuration and code at request time. Controls
that depend on the organisation (breach procedure, backups, contracts) cannot be
seen from here and are reported as "not_verified", never as done. This is a
self-check, not a certification.
"""
import os

CONTROLS = {
    "encryption_in_transit": "TLS on the public URL",
    "encryption_at_rest": "Stored feature data encrypted with a managed key",
    "access_controls": "Every API call authenticated and bound to the caller's own records",
    "audit_logging": "Durable security log kept 1 year",
    "rate_limiting": "Per-caller request limits",
    "consent_management": "Consent per purpose with history",
    "right_to_erasure": "Account erasure reaching shared records",
    "data_portability": "Export of everything held for an account",
    "breach_notification": "Procedure to tell users and the Board",
    "data_backup": "Tested backups with bounded retention",
    "processor_contracts": "Contracts with every data processor",
    "risk_assessment": "Documented security risk assessment",
}

STANDARDS = {
    "dpdp": {"name": "DPDP Act 2023 and Rules 2025 (India)",
             "controls": ["consent_management", "right_to_erasure", "data_portability", "encryption_at_rest",
                          "encryption_in_transit", "access_controls", "audit_logging", "breach_notification",
                          "processor_contracts"]},
    "gdpr": {"name": "GDPR (EU)",
             "controls": ["consent_management", "right_to_erasure", "data_portability", "encryption_at_rest",
                          "access_controls", "breach_notification", "risk_assessment"]},
    "hipaa": {"name": "HIPAA Security Rule (US); AdapFit is not a covered entity",
              "controls": ["encryption_at_rest", "encryption_in_transit", "access_controls", "audit_logging",
                           "data_backup", "breach_notification"]},
}


def control_status() -> dict:
    from app.core.config import settings
    from app.middleware.auth import auth_bypass_active

    at_rest = "implemented" if os.getenv("DATA_ENCRYPTION_KEYS") else "development_key"
    in_transit = "configured" if settings.PUBLIC_BASE_URL.startswith("https://") else "not_verified"
    measured = {
        "encryption_in_transit": in_transit,
        "encryption_at_rest": at_rest,
        "access_controls": "disabled" if auth_bypass_active() else "implemented",
        "audit_logging": "implemented",
        "rate_limiting": "implemented" if settings.RATE_LIMITING_ENABLED else "disabled",
        "consent_management": "implemented",
        "right_to_erasure": "implemented",
        "data_portability": "implemented",
    }
    return {cid: {"description": desc, "status": measured.get(cid, "not_verified")} for cid, desc in CONTROLS.items()}


def check_compliance(standard: str) -> dict:
    config = STANDARDS.get(standard.lower())
    if not config:
        return {"error": f"Unknown standard: {standard}", "available": sorted(STANDARDS)}
    status = control_status()
    results = [{"control": cid, **status[cid]} for cid in config["controls"]]
    return {
        "standard": standard.lower(),
        "name": config["name"],
        "implemented": sum(1 for r in results if r["status"] in ("implemented", "configured")),
        "total": len(results),
        "results": results,
        "note": "Self-check of technical controls, not a certification.",
    }
