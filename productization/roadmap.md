# Roadmap and long-term value

## For Silverbrook

| Horizon | Release | Scope | Value added | Gate to start |
|---|---|---|---|---|
| **Now** (months 1–3) | Release 1 pilot | PO-backed digital USD invoices; shadow mode → wave 1 → wave 2 | ~50% no-touch; exceptions explained; full audit trail | Compliance sign-off (done in the engagement plan) |
| **Next** (months 4–6) | Release 1 full rollout + bank-change workflow | All PO-backed digital USD invoices; phone-verification workflow for M-9 | 448 h/month saved; fraud protection | Wave 2 gates met |
| **Next** (months 6–9) | Release 2 | Scanned invoices (OCR), EUR/GBP, 3-way match with goods receipts, price-drift report for Procurement | +9% of volume covered; "billed but not delivered" caught; negotiation leverage | Accuracy ≥ 97% on a scanned-invoice test set; receiving data quality agreed |
| **Later** (months 9–15) | Release 3 | Non-PO invoices with GL coding suggestions; credit notes; early-payment discount optimization | Most of the remaining 15% of volume; working-capital gains | Release 2 stable for 3 months |

The auto-approval limit is reviewed each quarter, and raised only with 8+ weeks of ≥ 98% auditor agreement and Compliance approval.

## Long-term value creation

| Stage | From | To |
|---|---|---|
| 1. **Efficiency** | 790 hours a month of manual matching | Half the invoices untouched; people on exceptions |
| 2. **Control** | Evidence scattered in email | Every payment explainable in two minutes; fraud and duplicates caught before payment |
| 3. **Insight** | No view of why invoices fail | Vendor and contract performance data for Procurement (price drift, wrong POs, late vendors) |
| 4. **Working capital** | Late fees and missed discounts | Approved invoices ready early enough to take payment-term discounts |

## Recommendations

1. **Proceed to the pilot** using the gates in [../adoption/pilot_rollout.md](../adoption/pilot_rollout.md).
2. **Fund the bank-change verification workflow next:** highest value for the lowest effort.
3. **Start collecting receiving data quality now**, so 3-way match can start in release 2.
4. **Grow the golden set from real invoices from week one:** it is the asset that keeps the system trustworthy.
5. For the product team: prioritize the platform gaps **G-1** (gateway client), **G-2** (ERP connectors), **G-4** (evaluation as a service), and **G-7** (ingestion). They block every similar engagement.
