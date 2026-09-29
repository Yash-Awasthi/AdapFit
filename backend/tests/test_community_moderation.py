"""Posts can be reported and authors blocked; both change what the reporter sees, and 3 reports hide a post."""
from fastapi.testclient import TestClient

from app.main import app

c = TestClient(app)


def _post(author):
    body = {"title": "Leg day", "caption": "hi", "is_public": True}
    r = c.post(f"/api/v1/community/share?user_id={author}", json=body)
    assert r.status_code == 201, r.text
    return r.json()["id"]


def _feed(viewer):
    return {s["id"] for s in c.get(f"/api/v1/community/feed?user_id={viewer}&limit=100").json()}


def test_report_hides_for_reporter_then_everyone_after_three():
    sid = _post("mod-author")
    assert c.post(f"/api/v1/community/{sid}/report?user_id=r1", json={"reason": "spam"}).status_code == 201
    assert sid not in _feed("r1") and sid in _feed("r9")
    c.post(f"/api/v1/community/{sid}/report?user_id=r2", json={"reason": "abuse"})
    out = c.post(f"/api/v1/community/{sid}/report?user_id=r3", json={"reason": "abuse"}).json()
    assert out["hidden_for_everyone"] and sid not in _feed("r9")


def test_block_hides_posts_and_comments_of_that_author():
    sid = _post("mod-other")
    c.post(f"/api/v1/community/{sid}/comments?user_id=mod-troll", json={"text": "rude"})
    c.post("/api/v1/community/block/mod-troll?user_id=v1")
    assert all(x["user_id"] != "mod-troll" for x in c.get(f"/api/v1/community/{sid}/comments?user_id=v1").json())
    assert any(x["user_id"] == "mod-troll" for x in c.get(f"/api/v1/community/{sid}/comments?user_id=v2").json())
    assert c.post("/api/v1/community/block/v1?user_id=v1").status_code == 400


def test_sign_up_needs_age_13():
    from datetime import date
    young = date(date.today().year - 12, 1, 1).isoformat()
    r = c.post("/api/v1/auth/register", json={"email": "kid@example.com", "username": "kid12", "password": "Str0ngPassw0rd9",
                                              "birth_date": young, "guardian_email": "mum@example.com",
                                              "consent": {"health_data": True}})
    assert r.status_code == 400 and "13" in r.text
