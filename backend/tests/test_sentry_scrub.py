"""Error reports sent to Sentry carry no query, headers or body."""
from app.main import scrub_error_report


def test_scrub_keeps_only_method_and_path():
    event = {"request": {"method": "POST", "url": "http://x/api/v1/bp", "query_string": "user_id=u1",
                         "headers": {"Authorization": "Bearer t"}, "data": {"systolic": 150}}}
    assert scrub_error_report(event, {}) == {"request": {"method": "POST", "url": "http://x/api/v1/bp"}}
