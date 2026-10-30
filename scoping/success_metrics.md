# Success metrics (SMART)

Each metric is **S**pecific, **M**easurable, **A**chievable, **R**elevant, and **T**ime-bound. Baselines come from 3 months of ERP data and a two-day time study (see [business_case.md](business_case.md)). All figures refer to **PO-backed invoices** (about 3,400 a month, ~785 a week).

| Type | Metric | Exact definition | Baseline | Target: pilot (week 12) | Target: month 6 | How measured | Frequency | Owner |
|---|---|---|---|---|---|---|---|---|
| **Primary** | **No-touch invoices** | Invoices auto-approved by rule A-1 with no human action, as a share of all PO-backed invoices | 0% (all manual) | ≥ 35% of pilot invoices | **≥ 50%** (~390 a week) | Audit log: decisions with route = auto-approve | Weekly | AP Manager |
| **Guardrail** | **Exception rate** | Invoices sent to human review (rule A-4 or out of scope), as a share of PO-backed invoices | 22% true exceptions, everything else manual | ≤ 45% | **≤ 40%** (alert if above **45%**) | Audit log: decisions with route = review | Weekly | AP Manager |
| **Quality** | **Auditor agreement** | Share of a weekly random sample of 50 system decisions where Internal Audit agrees with the outcome | n/a (new control) | ≥ 98% | **≥ 98%**, 8 weeks in a row | Internal Audit sample sheet; disagreements logged with the cause | Weekly | Internal Audit Lead |
| **Adoption** | **Active users and volume** | (a) AP specialists who handled at least one invoice in InvoiceMatch that week; (b) PO-backed invoices processed through InvoiceMatch | 0 of 6; 0 invoices | (a) 2 of 2 pilot users; (b) ≥ 90% of pilot vendors' invoices | (a) **≥ 5 of 6**; (b) **≥ 80%** of PO-backed volume | Login and audit-log counts | Weekly | AP Manager |
| **Business** | **Hours saved and cost** | AP hours per month on PO-backed invoices, vs the 790-hour baseline, valued at $48 an hour | 790 hours a month | ≥ 30% fewer hours on pilot vendors | **≥ 50% fewer** (≤ 395 hours; ~100 hours saved a week; ~$258,000 a year) | Time study at weeks 6 and 12, plus the volume mix from the audit log | Monthly | CFO office |

## Guardrail details

The exception rate protects against two failure modes:
- **Too high (above 45%):** the system sends work back to people instead of removing it. Check extraction quality and rule settings.
- **Suddenly too low (below 15%):** possibly a rule or data failure letting invoices through. Stop auto-approval and investigate.

## Supporting measures (tracked, not targets)

| Measure | Why |
|---|---|
| Extraction accuracy per field on the fixed test set | Early warning before decisions go wrong; release gate (≥ 97% of fields correct) |
| Exception resolution time | Discovery showed 4.5 days today; target under 2 days |
| Duplicates and overpayments caught before payment | Business case: avoid ~$100,000 a year |
| AI cost per invoice | Expected under $0.002; alert if it doubles |
| Reviewer overrides of system decisions | High overrides on one rule means the rule needs tuning |

## Release gates

Auto-approval is switched on for a vendor group only when:
1. The fixed test set passes (≥ 97% field accuracy, ≥ 98% correct decisions, 0 wrong auto-approvals), and
2. Compliance has signed off the rules and the audit log format.
