"""Every API path the mobile app calls exists on the server.

A screen that calls a path the server does not have renders as empty, not as
an error, so the break is invisible until someone notices missing data.
"""
import pathlib
import re

import pytest

from app.main import app
from tests.conftest import iter_api_routes

MOBILE = pathlib.Path(__file__).resolve().parents[2] / "mobile"
CALLER = re.compile(r"\b(getJson|postJson|patchJson|putJson|deleteJson|request|authedFetch|fetch|api|get|post)\s*(?=[<(])")
FIRST_ARG = re.compile(r"""\(\s*[`'"]([^`'"]*)[`'"]""")
TABLE_ENTRY = re.compile(r"""^\s*[a-zA-Z_]+:\s*[`'"](/[a-z][^`'"]*)[`'"],?\s*$""")
# Paths built at run time that a static scan cannot resolve, and the server's root health check.
KNOWN = {"/api/v1/music/X", "/api/v1/wearable/X/import", "/api/v1/health"}


def _skip_generic(text: str, i: int) -> int:
    """Index just past a type argument list starting at text[i] == '<', nested ones and `=>` included."""
    depth = 0
    while i < len(text):
        if text.startswith("=>", i):
            i += 2
            continue
        depth += {"<": 1, ">": -1}.get(text[i], 0)
        i += 1
        if depth == 0:
            return i
    return i


HELPER_METHOD = {"getJson": "GET", "postJson": "POST", "patchJson": "PATCH", "putJson": "PUT",
                 "deleteJson": "DELETE", "get": "GET", "post": "POST"}
OPTION_METHOD = re.compile(r"""method:\s*['"](\w+)['"]""")


def _method(name: str, text: str, open_paren: int) -> str:
    """The HTTP method of a call: from the helper's name, else a `method:` option inside its parentheses, else GET."""
    if name in HELPER_METHOD:
        return HELPER_METHOD[name]
    depth, i = 0, open_paren
    while i < len(text):
        depth += {"(": 1, ")": -1}.get(text[i], 0)
        if depth == 0:
            break
        i += 1
    m = OPTION_METHOD.search(text, open_paren, i)
    return m.group(1).upper() if m else "GET"


def _calls(text: str, with_method: bool = False):
    for m in CALLER.finditer(text):
        i = m.end()
        if text[i] == "<":
            i = _skip_generic(text, i)
        arg = FIRST_ARG.match(text, i)
        if arg:
            yield (arg.group(1), _method(m.group(1), text, arg.start())) if with_method else arg.group(1)


def _called_paths():
    for path in list(MOBILE.glob("app/**/*.tsx")) + list(MOBILE.glob("src/**/*.ts*")):
        text = path.read_text(encoding="utf-8")
        found = list(_calls(text, with_method=True))
        if "useApis" in text:
            found += [(m.group(1), "GET") for m in map(TABLE_ENTRY.match, text.splitlines()) if m]
        for raw, method in found:
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
                yield path.relative_to(MOBILE).as_posix(), f"{method} {raw}", p, method


def test_calls_with_nested_and_multiline_generics_are_seen():
    text = """getJson<{ data: Record<string, any> }>('/a/b'); request<{
      fn: () => void; list: Array<{ id: string }>;
    }>(
      `/api/v1/c/${id}`)"""
    assert list(_calls(text)) == ["/a/b", "/api/v1/c/${id}"]
    fetch = """authedFetch(`${API}/workouts/generate`, {
        method: 'POST', body: x }); getJson('/w'); fetch(`/x`); foo(); bar({ method: 'DELETE' })"""
    assert list(_calls(fetch, with_method=True)) == [("${API}/workouts/generate", "POST"), ("/w", "GET"), ("/x", "GET")]


@pytest.mark.skipif(not MOBILE.exists(), reason="mobile app not in this checkout")
def test_every_mobile_api_call_has_a_route():
    routes = [(re.compile("^" + re.sub(r"\{[^}]+\}", "[^/]+", path) + "$"), methods)
              for path, methods, _e in iter_api_routes(app) if path.startswith("/api/v1")]
    missing = sorted({f"{f}: {raw}" for f, raw, p, method in _called_paths()
                      if p not in KNOWN and not any(rx.match(p) and method in methods for rx, methods in routes)})
    assert missing == [], "Mobile calls with no server route for that method:\n  " + "\n  ".join(missing)
