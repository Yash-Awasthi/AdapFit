"""Lab values are read against the report's range first."""
from app.services.lab_results import LabResults


def test_report_range_wins_over_typical():
    lr = LabResults()
    r = lr.add("vitamin_d", 25, "2026-01-10", ref_low=20, ref_high=100)
    assert r["status"] == "in_range" and r["range_source"] == "your report"


def test_typical_range_used_only_when_report_has_none():
    lr = LabResults()
    assert lr.add("vitamin_d", 25, "2026-01-10")["status"] == "below_range"
    assert lr.add("hemoglobin", 11, "2026-01-10")["status"] == "no_range"


def test_trend_and_next_step():
    lr = LabResults()
    lr.add("hba1c", 6.1, "2026-01-01")
    lr.add("hba1c", 5.8, "2026-06-01")
    t = lr.summary()[0]
    assert t["change"] == -0.3 and t["next_step"] == "Show this result to your doctor."
