"""
Environmental readings from Open-Meteo.

Air quality, UV index and pollen were being generated in this app, which is
worse than having no feature: those are numbers people act on with asthma, hay
fever or a sun allergy. Open-Meteo serves all three for free with no API key
and no account, so they can be real.

Every function returns either a reading or an explicit unavailability. None of
them fall back to a plausible-looking number, which is the whole point.

Coverage is not uniform: the pollen model covers Europe only, and outside it
the API returns nulls rather than zeros. That distinction is preserved —
"no data here" is not "no pollen today".
"""
import time
from typing import Any, Dict, Optional

import httpx

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

TIMEOUT_SECONDS = 15.0

# Named as the API names them, mapped to what this app calls them.
POLLUTANTS = {
    "pm2_5": "pm25",
    "pm10": "pm10",
    "ozone": "ozone",
    "nitrogen_dioxide": "no2",
    "sulphur_dioxide": "so2",
    "carbon_monoxide": "co",
}

POLLEN_TYPES = {
    "alder_pollen": "alder",
    "birch_pollen": "birch",
    "grass_pollen": "grass",
    "mugwort_pollen": "mugwort",
    "olive_pollen": "olive",
    "ragweed_pollen": "ragweed",
}

# Locations resolve to the same coordinates for a long time; the requests are
# free but not instant, and a screen refresh should not re-geocode.
_GEOCODE_TTL_SECONDS = 24 * 3600
_geocode_cache: Dict[str, Dict[str, Any]] = {}


def _unavailable(reason: str, detail: str) -> Dict[str, Any]:
    return {"status": "unavailable", "reason": reason, "message": detail}


async def _get(url: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """The JSON body, or None when the request could not be completed."""
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
    except (httpx.HTTPError, ValueError):
        return None


async def geocode(location: str) -> Dict[str, Any]:
    """Coordinates for a place name."""
    key = location.strip().lower()
    cached = _geocode_cache.get(key)
    if cached and time.time() - cached["cached_at"] < _GEOCODE_TTL_SECONDS:
        return cached["value"]

    body = await _get(GEOCODING_URL, {"name": location, "count": 1, "format": "json"})
    if body is None:
        return _unavailable("provider_unreachable", "Could not reach the geocoding service.")
    results = body.get("results") or []
    if not results:
        return _unavailable("unknown_location", f"No place found matching {location!r}.")

    top = results[0]
    value = {
        "status": "ok",
        "name": top.get("name"),
        "country": top.get("country"),
        "latitude": top["latitude"],
        "longitude": top["longitude"],
        "timezone": top.get("timezone"),
    }
    _geocode_cache[key] = {"value": value, "cached_at": time.time()}
    return value


async def _coordinates(location: str, latitude: Optional[float], longitude: Optional[float]):
    """Resolve to coordinates, preferring ones the caller already has."""
    if latitude is not None and longitude is not None:
        return {"status": "ok", "latitude": latitude, "longitude": longitude, "name": location}
    return await geocode(location)


async def air_quality(
    location: str, latitude: Optional[float] = None, longitude: Optional[float] = None
) -> Dict[str, Any]:
    """Current US AQI and pollutant concentrations for a location."""
    place = await _coordinates(location, latitude, longitude)
    if place.get("status") != "ok":
        return place

    body = await _get(AIR_QUALITY_URL, {
        "latitude": place["latitude"],
        "longitude": place["longitude"],
        "current": ",".join(["us_aqi", *POLLUTANTS]),
        "timezone": "auto",
    })
    if body is None:
        return _unavailable("provider_unreachable", "Could not reach the air quality service.")

    current = body.get("current") or {}
    aqi = current.get("us_aqi")
    if aqi is None:
        return _unavailable("no_coverage", "The air quality model has no data for this location.")

    return {
        "status": "ok",
        "location": place.get("name") or location,
        "latitude": place["latitude"],
        "longitude": place["longitude"],
        "aqi": int(aqi),
        "pollutants": {
            name: current[key] for key, name in POLLUTANTS.items()
            if current.get(key) is not None
        },
        "observed_at": current.get("time"),
        "source": "Open-Meteo air quality (CAMS)",
    }


async def uv_index(
    location: str, latitude: Optional[float] = None, longitude: Optional[float] = None
) -> Dict[str, Any]:
    """Current UV index for a location."""
    place = await _coordinates(location, latitude, longitude)
    if place.get("status") != "ok":
        return place

    body = await _get(FORECAST_URL, {
        "latitude": place["latitude"],
        "longitude": place["longitude"],
        "current": "uv_index",
        "timezone": "auto",
    })
    if body is None:
        return _unavailable("provider_unreachable", "Could not reach the forecast service.")

    current = body.get("current") or {}
    value = current.get("uv_index")
    if value is None:
        return _unavailable("no_coverage", "No UV data for this location.")

    return {
        "status": "ok",
        "location": place.get("name") or location,
        "uv_index": float(value),
        "observed_at": current.get("time"),
        "source": "Open-Meteo forecast",
    }


async def pollen(
    location: str, latitude: Optional[float] = None, longitude: Optional[float] = None
) -> Dict[str, Any]:
    """
    Current pollen concentrations in grains per cubic metre.

    The model covers Europe. Elsewhere the API returns nulls, which this
    reports as no coverage rather than as zero counts — telling someone with
    hay fever that the count is zero is the failure mode that matters.
    """
    place = await _coordinates(location, latitude, longitude)
    if place.get("status") != "ok":
        return place

    body = await _get(AIR_QUALITY_URL, {
        "latitude": place["latitude"],
        "longitude": place["longitude"],
        "current": ",".join(POLLEN_TYPES),
        "timezone": "auto",
    })
    if body is None:
        return _unavailable("provider_unreachable", "Could not reach the pollen service.")

    current = body.get("current") or {}
    counts = {
        name: current[key] for key, name in POLLEN_TYPES.items()
        if current.get(key) is not None
    }
    if not counts:
        return _unavailable(
            "no_coverage",
            "The pollen model covers Europe only, and has no data for this location.",
        )

    return {
        "status": "ok",
        "location": place.get("name") or location,
        "counts": counts,
        "observed_at": current.get("time"),
        "source": "Open-Meteo pollen (CAMS, Europe)",
    }
