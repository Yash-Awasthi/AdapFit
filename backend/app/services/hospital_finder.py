"""
Hospitals, clinics and pharmacies near a point, from OpenStreetMap (Overpass API).

Free and keyless, with good coverage in Indian cities. Results are what the map
holds: phone numbers and emergency departments appear only where mappers
recorded them, so the app shows 108/112 alongside every list.
"""
import math
import time
from typing import Optional

import httpx

# The main server is often overloaded; public mirrors are tried in order.
OVERPASS_URLS = ("https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter",
                 "https://overpass.private.coffee/api/interpreter")
HEADERS = {"User-Agent": "AdapFit/2.0 (health app; hospital finder)"}
TIMEOUT_SECONDS = 20
CACHE_SECONDS = 600
_cache: dict[tuple, tuple[float, list[dict]]] = {}
KINDS = {"hospital": "hospital", "clinic": "clinic|doctors", "pharmacy": "pharmacy", "all": "hospital|clinic|doctors|pharmacy"}


def _distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(a))


def _query(lat: float, lon: float, radius_m: int, amenity: str) -> str:
    return (f'[out:json][timeout:{TIMEOUT_SECONDS}];('
            f'node["amenity"~"^({amenity})$"](around:{radius_m},{lat},{lon});'
            f'way["amenity"~"^({amenity})$"](around:{radius_m},{lat},{lon}););out center 60;')


def parse(elements: list[dict], lat: float, lon: float) -> list[dict]:
    out = []
    for e in elements:
        tags = e.get("tags", {})
        plat = e.get("lat") or e.get("center", {}).get("lat")
        plon = e.get("lon") or e.get("center", {}).get("lon")
        if plat is None or plon is None or not tags.get("name"):
            continue
        address = ", ".join(v for v in (tags.get("addr:housenumber"), tags.get("addr:street"),
                                        tags.get("addr:suburb"), tags.get("addr:city")) if v)
        out.append({
            "name": tags["name"],
            "type": tags.get("amenity"),
            "distance_km": round(_distance_km(lat, lon, plat, plon), 2),
            "lat": plat, "lon": plon,
            "phone": tags.get("phone") or tags.get("contact:phone"),
            "emergency_department": tags.get("emergency") == "yes" if "emergency" in tags else None,
            "open_24_7": tags.get("opening_hours") == "24/7" if "opening_hours" in tags else None,
            "address": address or None,
            "operator_type": tags.get("operator:type") or tags.get("healthcare:speciality"),
        })
    out.sort(key=lambda x: x["distance_km"])
    return out


async def find_nearby(lat: float, lon: float, kind: str = "all", radius_km: float = 5.0) -> dict:
    key = (round(lat, 3), round(lon, 3), kind, radius_km)
    hit = _cache.get(key)
    if hit and time.time() - hit[0] < CACHE_SECONDS:
        places = hit[1]
    else:
        places = None
        query = _query(lat, lon, int(radius_km * 1000), KINDS[kind])
        async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS, headers=HEADERS) as client:
            for url in OVERPASS_URLS:
                try:
                    r = await client.post(url, data={"data": query})
                    r.raise_for_status()
                    places = parse(r.json().get("elements", []), lat, lon)
                    break
                except (httpx.HTTPError, ValueError):
                    continue
        if places is None:
            return {"status": "unavailable", "places": [], "emergency_numbers": EMERGENCY,
                    "message": "The map service did not respond. In an emergency call 108 or 112."}
        _cache[key] = (time.time(), places)
    return {"status": "ok", "places": places[:40], "emergency_numbers": EMERGENCY,
            "source": "OpenStreetMap contributors", "radius_km": radius_km}


EMERGENCY = [{"name": "Ambulance", "number": "108"}, {"name": "Emergency", "number": "112"}]
