"""Keeps the numbers quoted in the documents in sync with the business-case calculation."""
from scripts.business_case import baseline_hours, scenario, target_hours


def test_baseline_matches_documents():
    assert round(baseline_hours()) == 790


def test_target_scenario_matches_documents():
    s = scenario(0.50)
    assert round(target_hours(0.50)) == 342
    assert round(s["hours_saved"]) == 448
    assert s["saved_pct"] >= 0.50           # problem statement: at least 50% less effort
    assert target_hours(0.50) <= 395         # problem statement: under 395 hours a month
    assert 300_000 < s["net"] < 320_000      # "~$313,000"
    assert s["payback_months"] < 12          # CFO: payback within a year


def test_even_conservative_case_pays_back_within_a_year():
    assert scenario(0.35)["payback_months"] < 12
