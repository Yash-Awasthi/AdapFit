"""Each account gets a daily number of model calls; after that callers take their rule-based answer."""
from app.core import llm_quota
from tests.conftest import register_user


def test_calls_stop_at_the_daily_cap(monkeypatch):
    uid = register_user("quota@example.com", "quotauser")["user"]["id"]
    monkeypatch.setattr(llm_quota, "DAILY_CALLS", 3)
    assert [llm_quota.ai_call_allowed(uid) for _ in range(4)] == [True, True, True, False]
    assert llm_quota.remaining(uid) == 0
    llm_quota._used[uid] = ["2000-01-01", 3]  # a new day starts afresh
    assert llm_quota.ai_call_allowed(uid) and llm_quota.remaining(uid) == 2
