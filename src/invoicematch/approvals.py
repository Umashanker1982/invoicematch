"""Approval routing (rules A-1..A-4): turns the check results into one decision.

The approval limits come from configuration (Delegation of Authority). They are not changed by
this code, and auto-approval only happens when every check passed AND the total is within the
auto-approval limit.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from invoicematch.config import Settings
from invoicematch.matching import FAIL_LABELS, MatchResult

Route = Literal["auto_approve", "approval_ap_manager", "approval_finance_controller", "approval_cfo",
                "review", "security_review"]

ROUTE_LABELS = {
    "auto_approve": "Auto-approved",
    "approval_ap_manager": "Needs AP Manager approval",
    "approval_finance_controller": "Needs Finance Controller approval",
    "approval_cfo": "Needs CFO approval",
    "review": "Sent to human review",
    "security_review": "Sent to security review",
}

# Who may complete each route (Delegation of Authority + segregation of duties)
ROUTE_ROLES = {
    "approval_ap_manager": {"ap_manager", "finance_controller", "cfo"},
    "approval_finance_controller": {"finance_controller", "cfo"},
    "approval_cfo": {"cfo"},
    "review": {"ap_specialist", "ap_manager", "finance_controller", "cfo"},
    "security_review": {"security"},
}


class Decision(BaseModel):
    route: Route
    label: str
    rule_ids: list[str]          # approval rule + any failed matching rules, e.g. ["A-4", "M-4"]
    failed_rules: list[str]
    reasons: list[str]           # plain-language, neutral reasons
    controller_signoff: bool     # high-value mismatch: Finance Controller must also sign off
    total: float | None


def decide(match: MatchResult, total: float | None, settings: Settings) -> Decision:
    failed = match.failed
    if failed:
        reasons = [f"{c.rule} {FAIL_LABELS[c.rule]}: {c.message}" for c in match.checks if c.status == "fail"]
        high_value = (total or 0) > settings.ap_manager_limit
        if "M-9" in failed:
            route, rule_ids = "security_review", ["A-4"] + failed
        else:
            route, rule_ids = "review", ["A-4"] + failed
        if high_value:
            reasons.append(f"A-4 High-value mismatch: the total is above ${settings.ap_manager_limit:,.0f}, so the "
                           "Finance Controller must also sign off.")
        return Decision(route=route, label=ROUTE_LABELS[route], rule_ids=rule_ids, failed_rules=failed,
                        reasons=reasons, controller_signoff=high_value, total=total)

    t = total or 0.0
    if t <= settings.auto_approve_limit:
        route, rule, why = "auto_approve", "A-1", f"All checks passed and the total is within the ${settings.auto_approve_limit:,.0f} auto-approval limit."
    elif t <= settings.ap_manager_limit:
        route, rule, why = "approval_ap_manager", "A-2", f"All checks passed; totals from ${settings.auto_approve_limit:,.0f} to ${settings.ap_manager_limit:,.0f} need the AP Manager's approval."
    elif t <= settings.controller_limit:
        route, rule, why = "approval_finance_controller", "A-3", f"All checks passed; totals over ${settings.ap_manager_limit:,.0f} need the Finance Controller's approval."
    else:
        route, rule, why = "approval_cfo", "A-3", f"All checks passed; totals over ${settings.controller_limit:,.0f} need the CFO's approval."
    return Decision(route=route, label=ROUTE_LABELS[route], rule_ids=[rule], failed_rules=[], reasons=[why],
                    controller_signoff=False, total=total)
