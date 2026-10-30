# Problem statement

## The problem, as a business outcome

> **Within 6 months, cut the Accounts Payable team's manual effort on PO-backed supplier invoices by at least 50%, from about 790 to under 395 hours a month, while matching a human auditor on at least 98% of sampled decisions and keeping a complete audit trail for 100% of decisions. This lets Silverbrook absorb next year's 15% volume growth without new hires.**

This is a business outcome, not a feature request. Success is measured in hours, accuracy, and auditability, not in "we built an AI".

## Why it matters

| Today | Cost |
|---|---|
| 6 AP specialists spend all their time on 4,000 invoices a month | ~910 hours a month; month-end overtime |
| PO-backed invoices alone take ~790 hours a month | The part this project addresses |
| 15% more volume expected next year | One extra hire (~$100,000 a year) if nothing changes |
| Duplicates and overpayments | $210,000 found last year; only $90,000 recovered |
| Late-payment fees | $38,000 last year |
| Audit evidence scattered in email | 2–3 hours to reconstruct one approval |

## What it is NOT
- Not a project to reduce headcount. Freed time goes to exceptions, vendor management, and growth.
- Not a project to change who can approve what. The Delegation of Authority stays the same.
- Not a project to let AI decide payments. AI reads invoices; written rules decide; people approve anything above the limits.

## How we will know
The five success metrics, with baselines and targets, are in [../scoping/success_metrics.md](../scoping/success_metrics.md). The numbers behind this statement are in [../scoping/business_case.md](../scoping/business_case.md).
