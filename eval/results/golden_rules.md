# Benchmark: golden set, rules mode

Run at 2026-10-30T18:14:49+00:00

| Metric | Value |
|---|---|
| Invoices | 28 |
| Field accuracy | 100.0% |
| Invoices read completely right | 28/28 |
| Correct decisions | 28/28 (100.0%) |
| **Wrong auto-approvals (must be 0)** | **0** |
| Missed exceptions | 0 |
| False exceptions (sent to a person unnecessarily) | 0 |
| No-touch rate on this set | 29% |
| Read by | rules: 28 (fallbacks: 0) |
| AI cost | $0.0000 total, $0.00000 per invoice |
| AI latency p50 / p95 | 0 / 0 ms |

| Invoice | Read by | Expected | Got | Fields wrong | Result |
|---|---|---|---|---|---|
| 1 Clean invoice, small amount | rules | auto_approve | auto_approve | - | OK |
| 2 Clean IT invoice under $10,000 | rules | auto_approve | auto_approve | - | OK |
| 3 Monthly service invoice (same amount as last month, not a duplicate) | rules | auto_approve | auto_approve | - | OK |
| 4 Freight charged, allowed by contract and under the cap | rules | auto_approve | auto_approve | - | OK |
| 5 Unusual layout: PO given as 'Your ref', long date format | rules | auto_approve | auto_approve | - | OK |
| 6 E-invoice style with day.month.year date and 'Order No.' | rules | auto_approve | auto_approve | - | OK |
| 7 Invoice with sales tax and delivery fee | rules | auto_approve | auto_approve | - | OK |
| 8 Matched, $10,000-$25,000: AP Manager approval | rules | approval_ap_manager | approval_ap_manager | - | OK |
| 9 Matched, over $25,000: Finance Controller approval | rules | approval_finance_controller | approval_finance_controller | - | OK |
| 10 Matched, over $100,000: CFO approval | rules | approval_cfo | approval_cfo | - | OK |
| 11 Unit price above contract price | rules | review (M-4) | review (M-4) | - | OK |
| 12 Quantity above what was ordered | rules | review (M-3) | review (M-3) | - | OK |
| 13 Shipping charged, but the contract does not allow it | rules | review (M-5) | review (M-5) | - | OK |
| 14 Freight above the contract cap | rules | review (M-5) | review (M-5) | - | OK |
| 15 Lines do not add up to the total | rules | review (M-6) | review (M-6) | - | OK |
| 16 PO number does not exist | rules | review (M-1) | review (M-1) | - | OK |
| 17 PO is already closed | rules | review (M-1) | review (M-1) | - | OK |
| 18 Invoice vendor is not the PO's vendor | rules | review (M-2) | review (M-2) | - | OK |
| 19 Exact duplicate: last month's invoice sent again | rules | review (M-7) | review (M-7) | - | OK |
| 20 Possible duplicate: new number, same PO and total 4 days later | rules | review (M-7) | review (M-7) | - | OK |
| 21 Invoice in euros (release 1 is USD only) | rules | review (M-8) | review (M-8) | - | OK |
| 22 Bank account differs from the vendor master (possible fraud) | rules | security_review (M-9) | security_review (M-9) | - | OK |
| 23 No PO number on the invoice | rules | review (M-1) | review (M-1) | - | OK |
| 24 Damaged invoice: total and lines cannot be read | rules | review (M-10) | review (M-10) | - | OK |
| 25 Hidden instruction in the invoice text, plus a price above contract | rules | review (M-4) | review (M-4) | - | OK |
| 26 High-value mismatch: day rate above contract on a $35,000 invoice | rules | review (M-4) | review (M-4) | - | OK |
| 27 Partial delivery: 5 of 10 desks invoiced | rules | auto_approve | auto_approve | - | OK |
| 28 Partial delivery: invoices more than is left on the PO | rules | review (M-3) | review (M-3) | - | OK |
