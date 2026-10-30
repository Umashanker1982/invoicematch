# Executive communication plan and metrics dashboard

## Who hears what, and when

| Audience | Format | Cadence | Owner | Purpose |
|---|---|---|---|---|
| CFO (sponsor) | **One-page update** (template below) | Weekly during pilot, then monthly | FDE lead → AP Manager after handover | Progress against the business case; decisions needed |
| Steering group: CFO, Compliance, AP Manager, InfoSec, Internal Audit | 30-minute meeting with the dashboard | Every 2 weeks during pilot | FDE lead | Gate decisions (see [pilot_rollout.md](pilot_rollout.md)); risks |
| AP team | Team meeting + "you said, we did" | Weekly | AP Manager | Adoption; feedback acted on |
| Procurement | Short report on mismatch reasons by buyer and vendor | Monthly | AP Manager | Fix root causes (wrong POs, vendor price drift) |
| Whole finance department | Short note from the CFO | At kick-off, wave 2, full rollout | CFO | Why, what changes, the no-layoff commitment |

**Principles:** numbers before stories; always show the guardrail and quality metrics next to the savings; bad news early; every update ends with any decision needed.

## Metrics dashboard

The dashboard shows the five success metrics from [../scoping/success_metrics.md](../scoping/success_metrics.md), each with target and status (green, amber, red).

| Metric | Definition | Green | Amber | Red |
|---|---|---|---|---|
| **No-touch invoices** (primary) | Auto-approved share of PO-backed invoices, weekly | At or above the stage target | Within 10 points below | More than 10 points below |
| **Exception rate** (guardrail) | Share sent to people | ≤ target | Up to 5 points above | > 5 points above, or < 15% |
| **Auditor agreement** (quality) | Weekly sample of 50 | ≥ 98% | 95–98% | < 95%, or any wrong auto-approval |
| **Adoption** | Active specialists; share of volume through InvoiceMatch | ≥ target | Slightly below | Far below or falling |
| **Hours saved and cost** (business) | Versus the 790-hour baseline, at $48/hour | On track for 448 h/month by month 6 | Behind plan | Flat or worse |

Supporting panels: exception reasons (which rules fail most), top vendors with problems, queue age, AI cost, duplicates and overpayments caught.

The demo website's **Metrics** tab is a small version of this dashboard.

## One-page weekly update (template)

> **InvoiceMatch: week [N] of pilot [wave]. Overall status: [green/amber/red]**
>
> **Headline:** [one sentence, for example "No-touch rate reached X% with zero wrong approvals; on track for the wave 2 gate on [date]."]
>
> | Metric | This week | Target | Status |
> |---|---|---|---|
> | No-touch invoices | __% | __% | |
> | Exception rate | __% | ≤ __% | |
> | Auditor agreement (sample of 50) | __/50 | ≥ 49/50 | |
> | Active specialists / volume through tool | __ / __% | __ / __% | |
> | Hours saved this week (est.) | __ h | __ h | |
> | Duplicates and overpayments caught | $__ | - | |
>
> **What went well:** [1–2 bullets]
> **Issues and actions:** [1–3 bullets with owner and date]
> **Decision needed from you:** [none / specific ask with a recommended option]

## Key messages by stakeholder

| Stakeholder | Their question (from discovery) | Our answer, with evidence |
|---|---|---|
| CFO | "Will this pay back within a year?" | ~7 months at the target; even the conservative case pays back in ~8 months (business case) |
| Compliance | "Can I explain every payment?" | Every decision has rule ids, evidence, and a tamper-evident audit record; AI never decides |
| InfoSec | "What leaves our environment?" | Only invoice text with bank details removed, through the approved gateway |
| AP team | "Is this going to replace me?" | No layoffs; the tool takes the copy-typing, people own the judgment calls |
| Procurement | "Will it be used to police us?" | Messages state facts per line; the monthly report targets root causes, not people |
