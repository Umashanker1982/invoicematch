# Benchmark: holdout set, rules mode

Run at 2026-10-30T18:32:57+00:00

| Metric | Value |
|---|---|
| Invoices | 12 |
| Field accuracy | 39.2% |
| Invoices read completely right | 0/12 |
| Correct decisions | 0/12 (0.0%) |
| **Wrong auto-approvals (must be 0)** | **0** |
| Missed exceptions | 0 |
| False exceptions (sent to a person unnecessarily) | 7 |
| No-touch rate on this set | 0% |
| Read by | rules: 12 (fallbacks: 0) |
| AI cost | $0.0000 total, $0.00000 per invoice |
| AI latency p50 / p95 | 0 / 0 ms |

| Invoice | Read by | Expected | Got | Fields wrong | Result |
|---|---|---|---|---|---|
| H01 Pipe table, 'Customer PO: PO 7712' with a space, date 2026/10/20 | rules | auto_approve | review (M-10) | vendor, invoice_number, invoice_date, po_number, subtotal, freight, total_amount, lines | wrong |
| H02 Prose statement, quantities in words, PO as 'purchase order 7702' | rules | auto_approve | review (M-10) | invoice_number, invoice_date, po_number, tax, freight, total_amount, lines | wrong |
| H03 Service invoice, 'Your order reference', date 15-Oct-2026, 'VAT/Sales tax' | rules | auto_approve | review (M-10) | invoice_number, invoice_date, freight, total_amount, lines | wrong |
| H04 Tab-separated columns, 'P/O:', date 'Oct. 22 2026' | rules | auto_approve | review (M-10) | vendor, invoice_number, invoice_date, subtotal, tax, freight, total_amount, lines | wrong |
| H05 Upper-case labels, quantity first, 'SHIPPING AND HANDLING' within the cap | rules | auto_approve | review (M-10) | tax, freight, total_amount, lines | wrong |
| H06 Dotted leader lines, no currency symbol, 'Delivery charge' at the cap | rules | auto_approve | review (M-10) | invoice_number, invoice_date, subtotal, tax, freight, total_amount, lines | wrong |
| H07 'Statement of charges' wording, unit cost above contract | rules | review (M-4) | review (M-10) | invoice_number, invoice_date, tax, total_amount, lines | wrong |
| H08 'Freight & insurance' charged to a vendor whose contract does not allow freight | rules | review (M-5) | review (M-10) | invoice_number, subtotal, tax, freight, total_amount, lines | wrong |
| H09 Professional services: 'Days worked' and 'Day rate', $16,000 | rules | approval_ap_manager | review (M-10) | invoice_number, subtotal, lines | wrong |
| H10 One-line layout re-sending an invoice that was already paid | rules | review (M-7) | review (M-10) | invoice_number, invoice_date, tax, freight, total_amount, lines | wrong |
| H11 'Please note our new bank account' (possible fraud) | rules | security_review (M-9) | review (M-10) | vendor, invoice_number, invoice_date, tax, freight, total_amount, lines | wrong |
| H12 Arrow notation, quantity above the PO | rules | review (M-3) | review (M-10) | vendor, invoice_number, invoice_date, tax, freight, total_amount, lines | wrong |
