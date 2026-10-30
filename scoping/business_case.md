# Business case

One set of numbers, used everywhere in this repository. All figures are sample data for the fictional Silverbrook Financial, based on a 3-month ERP sample and a two-day time study.

## Baseline (today)

| Item | Value |
|---|---|
| Invoices per month | 4,000 |
| PO-backed invoices | 3,400 (85%), **the release 1 target** |
| Non-PO invoices | 600 (15%), out of scope |
| Clean PO invoice handling time | 8 minutes |
| PO invoices with an exception | 22% (748 a month) |
| Exception handling time (total, incl. follow-up) | 35 minutes |
| Cost of an AP hour (fully loaded) | $48 |

**Hours on PO-backed invoices today**

| | Invoices | Minutes each | Hours a month |
|---|---|---|---|
| Clean | 2,652 | 8 | 354 |
| Exceptions | 748 | 35 | 436 |
| **Total** | **3,400** | | **790** |

Add 120 hours for non-PO invoices (600 × 12 minutes) and the team spends **~910 hours a month**, which is all the productive time of 6 specialists. Exceptions are 22% of invoices but **55%** of the PO-invoice time.

## Target state (month 6)

| Route | Share | Invoices | Minutes each | Hours a month |
|---|---|---|---|---|
| No-touch auto-approval (A-1) | 50% | 1,700 | 0 | 0 |
| One-click approval (A-2, A-3) | 10% | 340 | 2 | 11 |
| Handled manually as today (scanned, non-USD, low confidence) | 18% | 612 | 8 | 82 |
| Exceptions with evidence pre-assembled (A-4) | 22% | 748 | 20 | 249 |
| **Total** | **100%** | **3,400** | | **342** |

- **Hours saved:** 790 − 342 = **448 hours a month** (**57% less**, ~103 hours a week)
- **Value of time saved:** 448 × $48 × 12 = **~$258,000 a year**
- Next year's 15% volume growth needs ~136 extra hours a month, so it is absorbed **with no new hire** (an avoided cost of ~$100,000 a year, not added to the total to avoid double counting).

## Leakage avoided

| Item | Value |
|---|---|
| Duplicates and overpayments found by audit last year | $210,000 |
| Recovered | $90,000 |
| **Net loss** | **$120,000** |
| Target: catch ≥ 90% before payment (rules M-4, M-5, M-6, M-7) | **~$100,000 a year avoided** (rounded down) |

Late-payment fees ($38,000 last year) should also fall, but are **not counted**: an upside, not a promise.

## Costs

| Cost | One-time | Per year |
|---|---|---|
| Build and 12-week pilot (FDE team) | $180,000 | |
| Cloud hosting, monitoring, backups | | $14,400 |
| AI model usage (3,400 invoices × under $0.002) | | under $100 |
| Support and maintenance (0.25 engineer) | | $30,000 |
| **Total** | **$180,000** | **~$45,000** |

## Return

| | Per year (after go-live) |
|---|---|
| Time saved | $258,000 |
| Leakage avoided | $100,000 |
| Running cost | −$45,000 |
| **Net benefit** | **~$313,000** |
| **Payback of the $180,000 build** | **~7 months after go-live** |

This meets the CFO's requirement of payback within one year.

## Sensitivity: what if results are weaker?

| Scenario | No-touch rate | Hours saved a month | Net benefit a year | Payback |
|---|---|---|---|---|
| Conservative | 35% | ~380 (48%) | ~$274,000 | ~8 months |
| **Target** | **50%** | **448 (57%)** | **~$313,000** | **~7 months** |
| Optimistic | 60% | ~493 (62%) | ~$339,000 | ~6 months |

Even the conservative case pays back within a year. The no-touch rate is the number that matters most, which is why it is the **primary metric**.

**Reproduce every number:** `python scripts/business_case.py`. All assumptions are at the top of that script.

## Human impact

No layoffs. The CFO has committed that freed time goes to (1) resolving exceptions faster, (2) vendor management and early-payment discounts, and (3) absorbing growth. This commitment is part of the adoption plan.
