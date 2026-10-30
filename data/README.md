# Sample data

**All data here is sample data, made up for this project. No real company, person, or bank account.**
Silverbrook Financial and every vendor are fictional. Bank numbers use a fake 999 routing range.

Created by `python scripts/make_sample_data.py` (re-running it produces identical files).

| File | Plays the role of |
|---|---|
| `vendors.json` | Vendor master in the ERP (names, addresses, bank details) |
| `contracts.json` | Contract terms: agreed unit prices, whether freight may be charged, freight cap |
| `purchase_orders.json` | Purchase orders: vendor, status, ordered and already-invoiced quantities |
| `invoice_history.json` | Invoices already processed, used to detect duplicates |
| `invoices/*.txt` | 28 sample invoices as they arrive (text of digital PDFs and e-invoices) |
| `../eval/golden_set.json` | The correct answer for every invoice, used by the tests and the benchmark |

Invoices use **four different layouts** (classic table, compact, letter, e-invoice), different date formats
(`2026-10-08`, `October 15, 2026`, `14.10.2026`, `06 Oct 2026`, `10/27/2026`) and different labels for the
PO number ("PO Number", "Your ref", "Order No.", "P.O. #", ...), as real vendors do.

## Test cases

Each expected outcome was decided by hand from the rules in [../scoping/scope.md](../scoping/scope.md).

| # | File | Vendor | What it tests | Total | Expected route | Rule that should fail |
|---|---|---|---|---|---|---|
| 1 | `invoice_01.txt` | Northgate | Clean invoice, small amount | $2,185.00 | Auto-approve (A-1) | - |
| 2 | `invoice_02.txt` | Bluepeak | Clean IT invoice under $10,000 | $8,195.00 | Auto-approve (A-1) | - |
| 3 | `invoice_03.txt` | Cedarline | Monthly service invoice (same amount as last month, not a duplicate) | $4,200.00 | Auto-approve (A-1) | - |
| 4 | `invoice_04.txt` | Northgate | Freight charged, allowed by contract and under the cap | $813.50 | Auto-approve (A-1) | - |
| 5 | `invoice_05.txt` | Quayside | Unusual layout: PO given as 'Your ref', long date format | $928.00 | Auto-approve (A-1) | - |
| 6 | `invoice_06.txt` | Summit | E-invoice style with day.month.year date and 'Order No.' | $1,280.00 | Auto-approve (A-1) | - |
| 7 | `invoice_07.txt` | Brightwell | Invoice with sales tax and delivery fee | $2,134.40 | Auto-approve (A-1) | - |
| 8 | `invoice_08.txt` | Bluepeak | Matched, $10,000-$25,000: AP Manager approval | $14,080.00 | AP Manager approval (A-2) | - |
| 9 | `invoice_09.txt` | Lumen | Matched, over $25,000: Finance Controller approval | $48,000.00 | Finance Controller approval (A-3) | - |
| 10 | `invoice_10.txt` | Lumen | Matched, over $100,000: CFO approval | $126,400.00 | CFO approval (A-3) | - |
| 11 | `invoice_11.txt` | Summit | Unit price above contract price | $960.00 | Human review (A-4) | M-4 |
| 12 | `invoice_12.txt` | Northgate | Quantity above what was ordered | $5,400.00 | Human review (A-4) | M-3 |
| 13 | `invoice_13.txt` | Bluepeak | Shipping charged, but the contract does not allow it | $5,075.00 | Human review (A-4) | M-5 |
| 14 | `invoice_14.txt` | Northgate | Freight above the contract cap | $4,080.00 | Human review (A-4) | M-5 |
| 15 | `invoice_15.txt` | Brightwell | Lines do not add up to the total | $1,025.00 | Human review (A-4) | M-6 |
| 16 | `invoice_16.txt` | Quayside | PO number does not exist | $435.00 | Human review (A-4) | M-1 |
| 17 | `invoice_17.txt` | Brightwell | PO is already closed | $1,250.00 | Human review (A-4) | M-1 |
| 18 | `invoice_18.txt` | Summit | Invoice vendor is not the PO's vendor | $210.00 | Human review (A-4) | M-2 |
| 19 | `invoice_19.txt` | Cedarline | Exact duplicate: last month's invoice sent again | $4,200.00 | Human review (A-4) | M-7 |
| 20 | `invoice_20.txt` | Quayside | Possible duplicate: new number, same PO and total 4 days later | $1,087.50 | Human review (A-4) | M-7 |
| 21 | `invoice_21.txt` | Bluepeak | Invoice in euros (release 1 is USD only) | EUR 4,880.00 | Human review (A-4) | M-8 |
| 22 | `invoice_22.txt` | Summit | Bank account differs from the vendor master (possible fraud) | $2,340.00 | Security review (M-9) | M-9 |
| 23 | `invoice_23.txt` | Brightwell | No PO number on the invoice | $370.00 | Human review (A-4) | M-1 |
| 24 | `invoice_24.txt` | Summit | Damaged invoice: total and lines cannot be read | unreadable | Human review (A-4) | M-10 |
| 25 | `invoice_25.txt` | Northgate | Hidden instruction in the invoice text, plus a price above contract | $1,248.00 | Human review (A-4) | M-4 |
| 26 | `invoice_26.txt` | Lumen | High-value mismatch: day rate above contract on a $35,000 invoice | $35,000.00 | Human review (A-4) + Controller sign-off | M-4 |
| 27 | `invoice_27.txt` | Northgate | Partial delivery: 5 of 10 desks invoiced | $3,100.00 | Auto-approve (A-1) | - |
| 28 | `invoice_28.txt` | Bluepeak | Partial delivery: invoices more than is left on the PO | $1,240.00 | Human review (A-4) | M-3 |

**Mix:** Auto-approve: 8, AP Manager approval: 1, Finance Controller approval: 1, CFO approval: 1, Human review: 16, Security review: 1.
This mix is designed to test every rule, so it has far more problem invoices than real life (about 22%).
