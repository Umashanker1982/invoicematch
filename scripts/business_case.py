"""Recompute every number in scoping/business_case.md from the stated assumptions.

    python scripts/business_case.py
"""
from __future__ import annotations

# Baseline assumptions (3-month ERP sample and time study; sample data)
PO_INVOICES = 3_400            # PO-backed invoices per month
NON_PO_INVOICES = 600
EXCEPTION_SHARE = 0.22
CLEAN_MIN, EXCEPTION_MIN, NON_PO_MIN = 8, 35, 12
HOURLY_COST = 48
GROWTH = 0.15

# Target-state assumptions (month 6)
ONE_CLICK_SHARE, ONE_CLICK_MIN = 0.10, 2
EXCEPTION_WITH_EVIDENCE_MIN = 20

LEAKAGE_AVOIDED = 100_000
RUN_COST = 14_400 + 100 + 30_000
BUILD_COST = 180_000


def baseline_hours() -> float:
    exceptions = PO_INVOICES * EXCEPTION_SHARE
    clean = PO_INVOICES - exceptions
    return (clean * CLEAN_MIN + exceptions * EXCEPTION_MIN) / 60


def target_hours(no_touch_share: float) -> float:
    exceptions = PO_INVOICES * EXCEPTION_SHARE
    one_click = PO_INVOICES * ONE_CLICK_SHARE
    no_touch = PO_INVOICES * no_touch_share
    manual = PO_INVOICES - exceptions - one_click - no_touch
    return (one_click * ONE_CLICK_MIN + manual * CLEAN_MIN + exceptions * EXCEPTION_WITH_EVIDENCE_MIN) / 60


def scenario(no_touch_share: float) -> dict[str, float]:
    saved = baseline_hours() - target_hours(no_touch_share)
    time_value = saved * HOURLY_COST * 12
    net = time_value + LEAKAGE_AVOIDED - RUN_COST
    return {
        "no_touch": no_touch_share,
        "hours_after": target_hours(no_touch_share),
        "hours_saved": saved,
        "saved_pct": saved / baseline_hours(),
        "hours_saved_week": saved * 12 / 52,
        "time_value": time_value,
        "net": net,
        "payback_months": BUILD_COST / net * 12,
    }


def main() -> None:
    base = baseline_hours()
    team = base + NON_PO_INVOICES * NON_PO_MIN / 60
    print(f"Baseline hours on PO invoices : {base:,.0f} per month")
    print(f"Whole team hours (incl. non-PO): {team:,.0f} per month")
    print(f"Exception share of PO time    : {PO_INVOICES * EXCEPTION_SHARE * EXCEPTION_MIN / 60 / base:.0%}")
    print(f"Extra hours for {GROWTH:.0%} growth   : {team * GROWTH:,.0f} per month")
    print(f"Running cost                  : ${RUN_COST:,.0f} per year\n")
    print(f"{'Scenario':<13}{'No-touch':>9}{'Hours after':>13}{'Saved/month':>13}{'Saved %':>9}"
          f"{'Saved/week':>12}{'Time value':>12}{'Net/year':>11}{'Payback':>9}")
    for name, share in (("Conservative", 0.35), ("Target", 0.50), ("Optimistic", 0.60)):
        s = scenario(share)
        print(f"{name:<13}{s['no_touch']:>9.0%}{s['hours_after']:>13,.0f}{s['hours_saved']:>13,.0f}"
              f"{s['saved_pct']:>9.0%}{s['hours_saved_week']:>12,.0f}{s['time_value']:>12,.0f}"
              f"{s['net']:>11,.0f}{s['payback_months']:>8.1f}m")


if __name__ == "__main__":
    main()
