# Benchmark: golden set, claude mode

Run at 2026-10-30T18:16:31+00:00 with `claude-haiku-5-5` through SharedLLM

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
| Read by | claude: 28 (fallbacks: 0) |
| AI cost | $0.0059 total, $0.00021 per invoice |
| AI latency p50 / p95 | 1978 / 5851 ms |

| Invoice | Read by | Expected | Got | Fields wrong | Result |
|---|---|---|---|---|---|
| 1 Clean invoice, small amount | claude | auto_approve | auto_approve | - | OK |
| 2 Clean IT invoice under $10,000 | claude | auto_approve | auto_approve | - | OK |
| 3 Monthly service invoice (same amount as last month, not a duplicate) | claude | auto_approve | auto_approve | - | OK |
| 4 Freight charged, allowed by contract and under the cap | claude | auto_approve | auto_approve | - | OK |
| 5 Unusual layout: PO given as 'Your ref', long date format | claude | auto_approve | auto_approve | - | OK |
| 6 E-invoice style with day.month.year date and 'Order No.' | claude | auto_approve | auto_approve | - | OK |
| 7 Invoice with sales tax and delivery fee | claude | auto_approve | auto_approve | - | OK |
| 8 Matched, $10,000-$25,000: AP Manager approval | claude | approval_ap_manager | approval_ap_manager | - | OK |
| 9 Matched, over $25,000: Finance Controller approval | claude | approval_finance_controller | approval_finance_controller | - | OK |
| 10 Matched, over $100,000: CFO approval | claude | approval_cfo | approval_cfo | - | OK |
| 11 Unit price above contract price | claude | review (M-4) | review (M-4) | - | OK |
| 12 Quantity above what was ordered | claude | review (M-3) | review (M-3) | - | OK |
| 13 Shipping charged, but the contract does not allow it | claude | review (M-5) | review (M-5) | - | OK |
| 14 Freight above the contract cap | claude | review (M-5) | review (M-5) | - | OK |
| 15 Lines do not add up to the total | claude | review (M-6) | review (M-6) | - | OK |
| 16 PO number does not exist | claude | review (M-1) | review (M-1) | - | OK |
| 17 PO is already closed | claude | review (M-1) | review (M-1) | - | OK |
| 18 Invoice vendor is not the PO's vendor | claude | review (M-2) | review (M-2) | - | OK |
| 19 Exact duplicate: last month's invoice sent again | claude | review (M-7) | review (M-7) | - | OK |
| 20 Possible duplicate: new number, same PO and total 4 days later | claude | review (M-7) | review (M-7) | - | OK |
| 21 Invoice in euros (release 1 is USD only) | claude | review (M-8) | review (M-8) | - | OK |
| 22 Bank account differs from the vendor master (possible fraud) | claude | security_review (M-9) | security_review (M-9) | - | OK |
| 23 No PO number on the invoice | claude | review (M-1) | review (M-1) | - | OK |
| 24 Damaged invoice: total and lines cannot be read | claude | review (M-10) | review (M-10) | - | OK |
| 25 Hidden instruction in the invoice text, plus a price above contract | claude | review (M-4) | review (M-4) | - | OK |
| 26 High-value mismatch: day rate above contract on a $35,000 invoice | claude | review (M-4) | review (M-4) | - | OK |
| 27 Partial delivery: 5 of 10 desks invoiced | claude | auto_approve | auto_approve | - | OK |
| 28 Partial delivery: invoices more than is left on the PO | claude | review (M-3) | review (M-3) | - | OK |
