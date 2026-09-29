"""Each URL prefix belongs to one route module, and registration is repeatable."""
from collections import defaultdict

from app.main import app
from tests.conftest import iter_api_routes


# Modules that extend one feature under its prefix without overlapping paths.
COMPANIONS = {
    "auth": {"auth", "auth_api"},
    "chat": {"chat", "ws_chat"},
    "challenges": {"fitness_challenges", "challenges_ws"},
    "workouts": {"workouts", "auto_scale", "adaptive_workouts_api"},
    "wearable": {"wearable_api", "wearos"},
}


def test_no_two_modules_share_a_prefix():
    owners = defaultdict(set)
    for path, _methods, endpoint in iter_api_routes(app):
        if not endpoint or not path.startswith("/api/v1/"):
            continue
        segment = path.split("/")[3]
        owners[segment].add(endpoint.__module__.rsplit(".", 1)[-1])
    shared = {seg: sorted(mods) for seg, mods in owners.items()
              if len(mods) > 1 and not mods <= COMPANIONS.get(seg, set())}
    assert shared == {}, f"Prefixes owned by more than one module: {shared}"


def test_no_method_and_path_is_registered_twice():
    seen = set()
    dupes = []
    for path, methods, _endpoint in iter_api_routes(app):
        for method in methods:
            key = (method, path)
            if key in seen:
                dupes.append(key)
            seen.add(key)
    assert dupes == []


def test_registering_twice_gives_the_same_routes():
    from fastapi import FastAPI

    from app.core.registry import register_endpoints

    first, second = FastAPI(), FastAPI()
    assert register_endpoints(first)["errors"] == 0
    register_endpoints(second)
    paths = lambda a: sorted(p for p, _m, _e in iter_api_routes(a))
    assert paths(first) == paths(second)
