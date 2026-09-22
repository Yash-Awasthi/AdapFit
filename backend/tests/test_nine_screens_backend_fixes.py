"""Defaulting/fabrication bugs found while wiring the nine remaining screens."""
from app.services.substance_use import SubstanceUseService
from app.services.fertility_tracker import FertilityTrackerService
from app.services.health_equity import HealthEquityService
from app.services.health_savings import HealthSavingsService
from app.services.ambient_health import AmbientHealthService
from app.services.genomics_insights import GenomicsInsightsService


def test_substance_use_clamps_do_not_crash():
    svc = SubstanceUseService()
    svc.create_recovery_profile("u1", "alcohol", "2026-01-01")
    assert svc.log_craving("u1", 15, "stress", "home", 10)["intensity"] == 10
    assert svc.log_craving("u1", -3, "stress", "home", 10)["intensity"] == 0
    assert svc.add_journal_entry("u1", 20, "ok")["mood"] == 10


def test_substance_use_support_contacts_round_trip():
    svc = SubstanceUseService()
    svc.create_recovery_profile("u1", "alcohol", "2026-01-01")
    assert svc.get_support_contacts("u1") == []
    svc.add_support_contact("u1", "Sam", "sponsor", "555-1000", True)
    contacts = svc.get_support_contacts("u1")
    assert len(contacts) == 1 and contacts[0]["name"] == "Sam"


def test_fertility_regularity_needs_real_cycles_not_a_fixed_claim():
    svc = FertilityTrackerService()
    assert svc._assess_regularity("nobody")["regular"] is None

    svc.daily_logs["u1"] = [
        {"date": "2026-01-01", "spotting": True},
        {"date": "2026-01-29", "spotting": True},
        {"date": "2026-02-26", "spotting": True},
    ]
    result = svc._assess_regularity("u1")
    assert result["regular"] is True
    assert result["variation_days"] == 0


def test_health_equity_score_ignores_uncontributed_categories():
    svc = HealthEquityService()
    svc.create_community_profile("c1", "Test", 1000)
    result = svc.calculate_sdoh_score("c1", {"economic_stability": 80})
    assert result["overall_score"] == 80
    assert list(result["categories"].keys()) == ["economic_stability"]


def test_health_savings_expense_eligibility_is_derived_not_hardcoded():
    svc = HealthSavingsService()
    svc.create_account("u1", "fsa")
    svc.contribute("u1", 1000)
    eligible = svc.expense("u1", 50, "Doctor Visit", "checkup")
    assert eligible["eligible"] is True
    ineligible = svc.expense("u1", 10, "Gym Membership", "monthly")
    assert ineligible["eligible"] is False


def test_ambient_health_reports_no_data_instead_of_a_fixed_fifty():
    svc = AmbientHealthService()
    home = svc.register_home("u1", {"name": "Home"})
    result = svc.get_environment_health(home["home_id"])
    assert result["status"] == "no_data"

    homes = svc.get_homes()
    assert len(homes) == 1 and homes[0]["home_id"] == home["home_id"]


def test_genomics_only_reports_genes_actually_uploaded():
    svc = GenomicsInsightsService()
    profile = svc.analyze_genetic_data("u1", {"variants": {"LCT": "tolerant"}})

    traits = {t["trait"]: t for t in profile["genetic_traits"]}
    assert list(traits.keys()) == ["Lactose Tolerance"]

    pgx = profile["pharmacogenomics"]
    assert pgx["CYP2D6"]["type"] == "not_tested"
