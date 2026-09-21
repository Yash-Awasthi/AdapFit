"""
Environmental readings come from the provider, or say they could not.

Air quality, UV and pollen were generated before this; the point of the
provider is that the numbers are real, and the point of these tests is that a
provider failure produces an explicit unavailability rather than a fallback
number that looks the same as a reading.

The provider itself is stubbed: a test suite that depends on a live API fails
for reasons that have nothing to do with the code.
"""
import pytest

from app.services import open_meteo
from app.services.allergy_tracker import AllergyTrackerService
from app.services.environmental_health import EnvironmentalHealthService

BOSTON = {"status": "ok", "name": "Boston", "latitude": 42.36, "longitude": -71.06}


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def stub_get(monkeypatch, by_url):
    """Serve a canned body per endpoint, keyed by a fragment of its URL."""
    async def _get(url, params):
        for fragment, payload in by_url.items():
            if fragment in url:
                return payload
        return None

    monkeypatch.setattr(open_meteo, "_get", _get)


@pytest.fixture(autouse=True)
def _no_geocode_cache():
    open_meteo._geocode_cache.clear()


@pytest.mark.anyio
async def test_an_unreachable_provider_is_reported_as_unavailable(monkeypatch):
    async def _fail(url, params):
        return None

    monkeypatch.setattr(open_meteo, "_get", _fail)
    result = await open_meteo.air_quality("Boston")
    assert result["status"] == "unavailable"
    assert result["reason"] == "provider_unreachable"
    assert "aqi" not in result


@pytest.mark.anyio
async def test_an_unknown_place_is_not_guessed(monkeypatch):
    stub_get(monkeypatch, {"geocoding": {"results": []}})
    result = await open_meteo.air_quality("Nowhere-at-all")
    assert result["status"] == "unavailable"
    assert result["reason"] == "unknown_location"


@pytest.mark.anyio
async def test_air_quality_returns_the_providers_numbers(monkeypatch):
    stub_get(monkeypatch, {
        "geocoding": {"results": [{
            "name": "Boston", "latitude": 42.36, "longitude": -71.06,
            "country": "United States", "timezone": "America/New_York",
        }]},
        "air-quality": {"current": {"time": "2026-09-22T04:00", "us_aqi": 34, "pm2_5": 4.6, "ozone": 53.0}},
    })
    result = await open_meteo.air_quality("Boston")
    assert result["status"] == "ok"
    assert result["aqi"] == 34
    assert result["pollutants"] == {"pm25": 4.6, "ozone": 53.0}
    assert result["observed_at"] == "2026-09-22T04:00"


@pytest.mark.anyio
async def test_a_location_outside_the_pollen_model_is_not_reported_as_zero(monkeypatch):
    """Telling someone with hay fever the count is zero is the failure that matters."""
    stub_get(monkeypatch, {
        "geocoding": {"results": [{"name": "Boston", "latitude": 42.36, "longitude": -71.06}]},
        "air-quality": {"current": {"time": "2026-09-22T04:00", "grass_pollen": None, "birch_pollen": None}},
    })
    result = await open_meteo.pollen("Boston")
    assert result["status"] == "unavailable"
    assert result["reason"] == "no_coverage"
    assert "counts" not in result


@pytest.mark.anyio
async def test_pollen_counts_are_returned_where_the_model_covers(monkeypatch):
    stub_get(monkeypatch, {
        "geocoding": {"results": [{"name": "Berlin", "latitude": 52.52, "longitude": 13.41}]},
        "air-quality": {"current": {"time": "2026-09-22T10:00", "grass_pollen": 0.0, "ragweed_pollen": 3.0}},
    })
    result = await open_meteo.pollen("Berlin")
    assert result["status"] == "ok"
    assert result["counts"] == {"grass": 0.0, "ragweed": 3.0}


@pytest.mark.anyio
async def test_a_fetched_reading_becomes_the_advice_for_that_location(monkeypatch):
    stub_get(monkeypatch, {
        "geocoding": {"results": [{"name": "Boston", "latitude": 42.36, "longitude": -71.06}]},
        "air-quality": {"current": {"time": "2026-09-22T04:00", "us_aqi": 168, "pm2_5": 90.0}},
    })
    service = EnvironmentalHealthService()
    result = await service.fetch_air_quality("Boston")
    assert result["status"] == "ok"
    assert result["aqi"] == 168
    assert result["level"] == "unhealthy"
    # Recorded, so a second read needs no request.
    assert service.get_air_quality("Boston")["aqi"] == 168


@pytest.mark.anyio
async def test_species_counts_are_summed_into_the_tracked_categories(monkeypatch):
    """A species with no category would otherwise read as a zero count."""
    stub_get(monkeypatch, {
        "geocoding": {"results": [{"name": "Berlin", "latitude": 52.52, "longitude": 13.41}]},
        "air-quality": {"current": {
            "time": "2026-09-22T10:00",
            "alder_pollen": 4.0, "birch_pollen": 6.0,
            "grass_pollen": 0.0, "ragweed_pollen": 3.0, "mugwort_pollen": 2.0,
        }},
    })
    result = await AllergyTrackerService().fetch_pollen("Berlin")
    assert result["status"] == "ok"
    levels = result["pollen_levels"]
    assert levels["tree"]["count"] == 10
    assert levels["weed"]["count"] == 5
    assert levels["grass"]["count"] == 0
    assert levels["grass"]["level"] == "none"


@pytest.mark.anyio
async def test_outdoor_safety_needs_both_readings(monkeypatch):
    stub_get(monkeypatch, {
        "geocoding": {"results": [{"name": "Boston", "latitude": 42.36, "longitude": -71.06}]},
        "air-quality": {"current": {"time": "2026-09-22T04:00", "us_aqi": 30}},
        "forecast": {"current": {"time": "2026-09-22T04:00"}},  # no uv_index
    })
    service = EnvironmentalHealthService()
    result = await service.fetch_outdoor_exercise_safety("Boston")
    assert result["status"] == "unavailable"
    assert "UV index" in result["missing"]
