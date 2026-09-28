"""Overpass results are parsed, sorted by distance, and never invent missing details."""
from app.services.hospital_finder import parse

HERE = (12.9716, 77.5946)


def test_parse_sorts_and_keeps_only_named_places():
    elements = [
        {"type": "node", "lat": 12.99, "lon": 77.59, "tags": {"amenity": "hospital", "name": "Far Hospital", "emergency": "yes"}},
        {"type": "way", "center": {"lat": 12.972, "lon": 77.595}, "tags": {"amenity": "pharmacy", "name": "Near Pharmacy"}},
        {"type": "node", "lat": 12.973, "lon": 77.595, "tags": {"amenity": "clinic"}},
    ]
    places = parse(elements, *HERE)
    assert [p["name"] for p in places] == ["Near Pharmacy", "Far Hospital"]
    assert places[1]["emergency_department"] is True
    assert places[0]["emergency_department"] is None and places[0]["phone"] is None
