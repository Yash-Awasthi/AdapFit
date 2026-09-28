"""Drug lookup maps Indian names, validates input, and never calls the network in tests."""
from fastapi.testclient import TestClient

from app.main import app
from app.services import openfda_client as fda

c = TestClient(app)


def test_indian_names_map_to_us_names():
    assert fda.us_name("Paracetamol") == "acetaminophen"
    assert fda.us_name("metformin") == "metformin"


def test_lookup_uses_both_brand_and_generic(monkeypatch):
    seen = {}

    def fake(endpoint, params, api_key=None):
        seen[endpoint] = params
        return {"results": []}

    monkeypatch.setattr(fda, "_fda_request", fake)
    r = c.get("/api/v1/medication/drug-info?name=paracetamol")
    assert r.status_code == 200 and r.json()["searched_as"] == "acetaminophen"
    assert 'generic_name:"acetaminophen"' in seen["drug/label"]["search"]


def test_query_syntax_cannot_be_injected():
    assert c.get('/api/v1/medication/drug-info?name=x"+OR+"y').status_code == 422


def test_interaction_results_never_tell_the_user_to_change_a_dose():
    r = c.post("/api/v1/drug-interactions/check", json={"medications": ["warfarin", "aspirin", "digoxin", "amiodarone"]})
    items = r.json()["data"]["interactions"]
    assert items, "the fixture pair should interact"
    for item in items:
        assert "action" not in item
        assert "Do not stop or change" in item["next_step"]
