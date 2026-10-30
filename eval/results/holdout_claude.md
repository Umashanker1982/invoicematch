# Benchmark: holdout set, claude mode

Run at 2026-10-30T18:16:55+00:00 with `claude-haiku-5-5` through SharedLLM

| Metric | Value |
|---|---|
| Invoices | 12 |
| Field accuracy | 100.0% |
| Invoices read completely right | 12/12 |
| Correct decisions | 12/12 (100.0%) |
| **Wrong auto-approvals (must be 0)** | **0** |
| Missed exceptions | 0 |
| False exceptions (sent to a person unnecessarily) | 0 |
| No-touch rate on this set | 50% |
| Read by | claude: 12 (fallbacks: 0) |
| AI cost | $0.0024 total, $0.00020 per invoice |
| AI latency p50 / p95 | 1793 / 2819 ms |

| Invoice | Read by | Expected | Got | Fields wrong | Result |
|---|---|---|---|---|---|
| H01 Pipe table, 'Customer PO: PO 7712' with a space, date 2026/10/20 | claude | auto_approve | auto_approve | - | OK |
| H02 Prose statement, quantities in words, PO as 'purchase order 7702' | claude | auto_approve | auto_approve | - | OK |
| H03 Service invoice, 'Your order reference', date 15-Oct-2026, 'VAT/Sales tax' | claude | auto_approve | auto_approve | - | OK |
| H04 Tab-separated columns, 'P/O:', date 'Oct. 22 2026' | claude | auto_approve | auto_approve | - | OK |
| H05 Upper-case labels, quantity first, 'SHIPPING AND HANDLING' within the cap | claude | auto_approve | auto_approve | - | OK |
| H06 Dotted leader lines, no currency symbol, 'Delivery charge' at the cap | claude | auto_approve | auto_approve | - | OK |
| H07 'Statement of charges' wording, unit cost above contract | claude | review (M-4) | review (M-4) | - | OK |
| H08 'Freight & insurance' charged to a vendor whose contract does not allow freight | claude | review (M-5) | review (M-5) | - | OK |
| H09 Professional services: 'Days worked' and 'Day rate', $16,000 | claude | approval_ap_manager | approval_ap_manager | - | OK |
| H10 One-line layout re-sending an invoice that was already paid | claude | review (M-7) | review (M-7) | - | OK |
| H11 'Please note our new bank account' (possible fraud) | claude | security_review (M-9) | security_review (M-9) | - | OK |
| H12 Arrow notation, quantity above the PO | claude | review (M-3) | review (M-3) | - | OK |
