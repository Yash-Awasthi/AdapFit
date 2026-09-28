"""
No service invents a number it reports as a measurement.

Twenty-odd services filled in their own inputs with `random`, which is how the
app came to report atrial fibrillation, melanoma suspicion, breathing pauses,
air quality, ER wait times and an employee wellness score that nobody had
measured. Each is fixed; this test is what stops the pattern coming back,
because a fabricated reading is invisible in review — it looks exactly like a
real one.

Generating an identifier is not a measurement, so those uses are listed
explicitly rather than matched by shape.
"""
import ast
import pathlib

import pytest

APP = pathlib.Path(__file__).resolve().parent.parent / "app"
SERVICES = APP / "services"
ENDPOINTS = APP / "api" / "v1" / "endpoints"

# Uses of `random` that produce an id or pick between equivalent phrasings,
# neither of which claims anything about the user. Each entry is one file.
ALLOWED = {
    # Identifiers.
    "ambient_health.py": {"randint"},
    "peer_support.py": {"randint"},
    # Wording and content variety: choosing which tip, recipe or phrasing to
    # show makes no claim about a measurement.
    "ai_coach.py": {"choice"},
    "habit_coach.py": {"choice"},
    "recipe_generator.py": {"choice"},
    "workplace_ergonomics.py": {"choice", "sample"},
    # Labelled synthetic data for exercising the pipeline in development.
    "simulator.py": {"uniform", "randint"},
}

# Functions that produce a number or a verdict rather than choosing wording.
MEASURING = {"randint", "uniform", "random", "gauss", "normalvariate", "betavariate", "expovariate"}


def _random_calls(path: pathlib.Path):
    """Every `random.<fn>` called in the file, with its line number."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:  # pragma: no cover - a broken file fails elsewhere
        return []
    found = []
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "random"
        ):
            found.append((node.func.attr, node.lineno))
    return found


ALL_SERVICES = sorted(SERVICES.glob("*.py")) + sorted(ENDPOINTS.glob("*.py"))


@pytest.mark.parametrize("path", ALL_SERVICES, ids=lambda p: p.name)
def test_no_service_generates_a_measurement(path):
    allowed = ALLOWED.get(path.name, set())
    offenders = [
        f"{path.name}:{line} random.{fn}"
        for fn, line in _random_calls(path)
        if fn in MEASURING and fn not in allowed
    ]
    assert offenders == [], (
        "These produce a number that reaches the user as a measurement:\n  "
        + "\n  ".join(offenders)
        + "\n\nDerive it from real input, or report that the input is missing. "
        "If it genuinely picks between equivalent options, add the file to ALLOWED."
    )


def test_the_sweep_actually_covers_the_services():
    """A guard on the guard: an empty file list would make this vacuous."""
    assert len(ALL_SERVICES) > 300


def test_the_allowlist_has_no_stale_entries():
    """An entry left behind after a fix would quietly re-open the hole."""
    stale = []
    for name, allowed in ALLOWED.items():
        path = SERVICES / name if (SERVICES / name).exists() else ENDPOINTS / name
        if not path.exists():
            stale.append(f"{name} (no such file)")
            continue
        used = {fn for fn, _ in _random_calls(path)}
        unused = allowed - used
        if unused:
            stale.append(f"{name} no longer uses {', '.join(sorted(unused))}")
    assert stale == [], "Stale allowlist entries: " + "; ".join(stale)
