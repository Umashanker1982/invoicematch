# Pilot rollout and expansion criteria

Start small, prove it with numbers, then expand. Each stage has entry criteria, exit criteria, and a way back. The rollback switch at every stage is `AUTO_APPROVE_LIMIT=0` (everything goes to people; see [../deployment/runbook.md](../deployment/runbook.md)).

## Stages

| Stage | Weeks | Scope | Auto-approval limit | Who uses it |
|---|---|---|---|---|
| **0. Shadow mode** | 5–6 | All PO-backed digital invoices from the **top 10 vendors** (~35% of volume). The system decides, but **people still process every invoice the old way**; decisions are compared | **$0** (off) | AP Manager reviews comparisons |
| **1. Pilot wave 1** | 7–9 | Top 10 vendors | **$2,500** | 2 pilot specialists (Tom Becker + 1) |
| **2. Pilot wave 2** | 10–12 | Top 40 vendors (~70% of PO-backed volume) | **$10,000** (the agreed release-1 limit) | All 6 specialists |
| **3. Full rollout** | Month 4 onward | All PO-backed digital USD invoices | $10,000 | Whole AP team |
| Later | Release 2+ | Scanned invoices, other currencies, 3-way match | Decided on evidence | - |

Weeks 1–4 are the build and test phase (this repository).

## Gates: criteria to move to the next stage

All must be true for **2 consecutive weeks**:

| Criterion | Shadow → Wave 1 | Wave 1 → Wave 2 | Wave 2 → Full |
|---|---|---|---|
| Wrong auto-approvals (or, in shadow mode, would-be wrong) | 0 | 0 | 0 |
| Auditor agreement on the weekly sample | ≥ 98% | ≥ 98% | ≥ 98% |
| Exception rate | ≤ 50% | ≤ 45% | ≤ 40% |
| Exception resolution time | - | < 3 days | < 2 days |
| Pilot users' confidence (1–5 survey) | - | ≥ 3.5 | ≥ 4.0 |
| Open high-severity issues | 0 | 0 | 0 |
| Sign-off | AP Manager + Compliance | AP Manager + Compliance | CFO + Compliance |

## Stop and roll back if

- Any wrong auto-approval is confirmed → `AUTO_APPROVE_LIMIT=0`, investigate, re-run the gate from the start of the stage.
- Auditor agreement falls below 95% in any week.
- The exception rate goes above 60% (the tool is creating work), or suddenly below 15% (possible failure).
- The AP Manager or Compliance asks to pause. Either can stop the pilot at any time.

## Why this sequence

- **Shadow mode** gives real evidence on real invoices with zero risk: nothing changes for vendors or payments.
- **A low first limit ($2,500)** means early mistakes, if any, are small and caught by the auditor sample.
- **Starting with the top 10 vendors** covers a third of the volume with few layouts to learn.
- **Pilot users are volunteers** (Tom asked to be first), which turns the most worried group into champions.
