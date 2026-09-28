"""Registration checks trust only the NMC register, and nothing lists invented doctors."""
import asyncio

import httpx

from app.services.telemedicine import SERVICES, TelemedicineService

ROW = {"name": "ASHA   RAO", "registration_no": "DMC/R/12345", "state_medical_council": "Delhi Medical Council",
       "registration_date": "06-04-2015", "qualification": "MBBS", "removed_status": None,
       "dob": "1985-08-24", "permanent_address": "private"}


def _client(payload=None, fail=False):
    def handler(request):
        if fail:
            raise httpx.ConnectError("down")
        return httpx.Response(200, json=payload)
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


def _verify(**kw):
    client = kw.pop("client")
    return asyncio.run(TelemedicineService().verify_registration(client=client, **kw))


def test_found_returns_only_registration_fields():
    out = _verify(registration_no="12345", name="Dr. Asha Rao", client=_client({"success": True, "data": [ROW]}))
    assert out["status"] == "found"
    match = out["matches"][0]
    assert match["name"] == "ASHA RAO" and "dob" not in match and "permanent_address" not in match


def test_name_mismatch_is_not_found():
    out = _verify(registration_no="12345", name="Ravi Kumar", client=_client({"success": True, "data": [ROW]}))
    assert out["status"] == "not_found"


def test_removed_registration_is_flagged():
    out = _verify(registration_no="12345", client=_client({"success": True, "data": [{**ROW, "removed_status": "Removed"}]}))
    assert out["matches"][0]["removed"] and "removed" in out["message"]


def test_register_down_says_so():
    assert _verify(registration_no="12345", client=_client(fail=True))["status"] == "unavailable"


def test_bad_input_rejected_before_any_call():
    assert _verify(registration_no="<script>", client=_client(fail=True))["status"] == "invalid"


def test_directory_has_no_ratings_fees_or_named_doctors():
    for s in SERVICES:
        assert not {"rating", "reviews", "consultation_fee"} & s.keys()
        assert not s["name"].startswith("Dr")
