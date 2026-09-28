"""Every API path the mobile app calls exists on the server.

A screen that calls a path the server does not have renders as empty, not as
an error, so the break is invisible until someone notices missing data.
"""
import pathlib
import re

import pytest

from app.main import app

MOBILE = pathlib.Path(__file__).resolve().parents[2] / "mobile"
CALL = re.compile(
    r"""\b(getJson|postJson|patchJson|putJson|deleteJson|request|authedFetch|fetch|api|get|post)\s*(?:<[^>]*>)?\(\s*[`'"]([^`'"]*)[`'"]"""
)
TABLE_ENTRY = re.compile(r"""^\s*[a-zA-Z_]+:\s*[`'"](/[a-z][^`'"]*)[`'"],?\s*$""")
# Paths built at run time that a static scan cannot resolve, and the server's root health check.
KNOWN = {"/api/v1/music/X", "/api/v1/health"}


def _called_paths():
    for path in list(MOBILE.glob("app/**/*.tsx")) + list(MOBILE.glob("src/**/*.ts*")):
        text = path.read_text(encoding="utf-8")
        found = [m.group(2) for m in CALL.finditer(text)]
        if "useApis" in text:
            found += [m.group(1) for m in map(TABLE_ENTRY.match, text.splitlines()) if m]
        for raw in found:
            p = re.sub(r"\$\{(API_V1|API|API_BASE_URL)\}", "", raw)
            if p.startswith("http") and "/api/v1" not in p:
                continue
            p = p.split("?")[0]
            if not p.startswith("/"):
                continue
            if not p.startswith("/api/v1"):
                p = "/api/v1" + p
            # A trailing ${...} glued to a path segment is a query string built at run time.
            p = re.sub(r"(?<=[a-z])\$\{[^}]+\}$", "", p)
            p = re.sub(r"\$\{[^}]+\}", "X", p).rstrip("/")
            if p != "/api/v1":
                yield path.relative_to(MOBILE).as_posix(), raw, p


@pytest.mark.skipif(not MOBILE.exists(), reason="mobile app not in this checkout")
def test_every_mobile_api_call_has_a_route():
    routes = [re.compile("^" + re.sub(r"\{[^}]+\}", "[^/]+", r.path) + "$")
              for r in app.routes if getattr(r, "path", "").startswith("/api/v1")]
    missing = sorted({f"{f}: {raw}" for f, raw, p in _called_paths()
                      if p not in KNOWN and not any(rx.match(p) for rx in routes)})
    assert missing == [], "Mobile calls with no server route:\n  " + "\n  ".join(missing)
