"""Create the held-out test set: 12 invoices in layouts the rules reader was NOT built for.

    python scripts/make_holdout_data.py

The main sample set (data/invoices) was used while building the rules reader, so its scores are a
regression baseline. This set was written afterwards, with new layouts, labels, and number formats,
to measure how well each reader handles invoices it has never seen. All data is made up.

Writes data/holdout/*.txt and eval/holdout_set.json (expected fields and decisions, decided by hand).
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def L(sku, qty, price):  # noqa: E743 - short helper for expected lines
    return {"sku": sku, "quantity": qty, "unit_price": price}


CASES = [
    dict(id="H01", title="Pipe table, 'Customer PO: PO 7712' with a space, date 2026/10/20",
         route="auto_approve", failed=[], text="""\
NORTHGATE OFFICE SUPPLIES INC. - TAX INVOICE
Doc ref: NOS-31160          Issued: 2026/10/20
Customer: Silverbrook Financial (Accounts Payable)
Customer PO: PO 7712

| Code    | Item                    | Qty | Price    | Total     |
|---------|-------------------------|-----|----------|-----------|
| CHR-450 | Ergonomic office chair  | 4   | 450.00   | 1,800.00  |

Net amount: 1,800.00
Sales tax: 0.00
Invoice total (USD): 1,800.00
Pay to: Northgate Office Supplies Inc., Account 9900-1101-2201, Routing 999000101
""", fields=dict(vendor="Northgate Office Supplies Inc.", invoice_number="NOS-31160", invoice_date="2026-10-20",
                 po_number="PO-7712", currency="USD", lines=[L("CHR-450", 4, 450.0)], subtotal=1800.0, tax=0.0,
                 freight=0.0, total_amount=1800.0, bank_account="9900-1101-2201")),

    dict(id="H02", title="Prose statement, quantities in words, PO as 'purchase order 7702'",
         route="auto_approve", failed=[], text="""\
Bluepeak IT Services LLC
740 Commerce Way, Lakeside

Billing statement BP-88340, issued 21 October 2026

Hello Silverbrook team,
as agreed under your purchase order 7702 we supplied five (5) laptops (LAP-14) at USD 1,450.00 per unit,
and five (5) docking stations (DCK-01) at USD 189.00 per unit.

Amount for laptops: USD 7,250.00
Amount for docking stations: USD 945.00
Subtotal: USD 8,195.00
No tax or delivery charges apply.
Balance due: USD 8,195.00

Please remit to account 9900-1102-3302 (routing 999000102).
""", fields=dict(vendor="Bluepeak IT Services LLC", invoice_number="BP-88340", invoice_date="2026-10-21",
                 po_number="PO-7702", currency="USD", lines=[L("LAP-14", 5, 1450.0), L("DCK-01", 5, 189.0)],
                 subtotal=8195.0, tax=0.0, freight=0.0, total_amount=8195.0, bank_account="9900-1102-3302")),

    dict(id="H03", title="Service invoice, 'Your order reference', date 15-Oct-2026, 'VAT/Sales tax'",
         route="auto_approve", failed=[], text="""\
CEDARLINE FACILITY SERVICES
Service Invoice
Ref: CF-2026-1015                Date of issue: 15-Oct-2026
Your order reference: PO-7718

Description                                   Units    Rate       Line total
Deep clean, per floor (code CLN-DP)               3     850.00      2,550.00

Subtotal                                                            2,550.00
VAT/Sales tax                                                           0.00
Total payable (USD)                                                 2,550.00

Bank: account no. 9900-1103-4403, routing no. 999000103
""", fields=dict(vendor="Cedarline Facility Services", invoice_number="CF-2026-1015", invoice_date="2026-10-15",
                 po_number="PO-7718", currency="USD", lines=[L("CLN-DP", 3, 850.0)], subtotal=2550.0, tax=0.0,
                 freight=0.0, total_amount=2550.0, bank_account="9900-1103-4403")),

    dict(id="H04", title="Tab-separated columns, 'P/O:', date 'Oct. 22 2026'",
         route="auto_approve", failed=[], text="""\
Quayside Courier Services - 3 Dockside Lane, Port Avery
INVOICE QC-55201
Date: Oct. 22 2026
P/O: PO-7725

Service\tCode\tQty\tRate\tLine total
Express courier delivery\tCUR-EX\t10\t29.00\t290.00

Sub-total: 290.00
Amount payable: $290.00
Bank account: 9900-1104-5504 / routing 999000104
""", fields=dict(vendor="Quayside Courier Services", invoice_number="QC-55201", invoice_date="2026-10-22",
                 po_number="PO-7725", currency="USD", lines=[L("CUR-EX", 10, 29.0)], subtotal=290.0, tax=0.0,
                 freight=0.0, total_amount=290.0, bank_account="9900-1104-5504")),

    dict(id="H05", title="Upper-case labels, quantity first, 'SHIPPING AND HANDLING' within the cap",
         route="auto_approve", failed=[], text="""\
Summit Print & Design Co.
INVOICE NUMBER: SPD-2026-0450
INVOICE DATE: 23 October 2026
PO REFERENCE: PO-7720

QTY  ITEM CODE  DESCRIPTION                         UNIT PRICE   AMOUNT
1    PRT-BR     Brochure print run, 1,000 copies    $640.00      $640.00
5    PRT-BC     Business cards, box of 500          $42.00       $210.00

SUBTOTAL                 $850.00
SHIPPING AND HANDLING    $38.00
TOTAL                    $888.00
Remit to account 9900-1105-6605, routing 999000105
""", fields=dict(vendor="Summit Print & Design Co.", invoice_number="SPD-2026-0450", invoice_date="2026-10-23",
                 po_number="PO-7720", currency="USD", lines=[L("PRT-BR", 1, 640.0), L("PRT-BC", 5, 42.0)],
                 subtotal=850.0, tax=0.0, freight=38.0, total_amount=888.0, bank_account="9900-1105-6605")),

    dict(id="H06", title="Dotted leader lines, no currency symbol, 'Delivery charge' at the cap",
         route="auto_approve", failed=[], text="""\
BRIGHTWELL CATERING CO.
27 Orchard Street, Riverton
Invoice BWC-7760 / 2026-10-24
For: Silverbrook Financial - PO-7707

Event catering package (CAT-EVT) ........ 1 x 1,250.00 ........ 1,250.00
Delivery charge ......................................................... 60.00

Items subtotal: 1,250.00
Grand total: 1,310.00 USD

Payment details: Account 9900-1107-8807, Routing 999000107
""", fields=dict(vendor="Brightwell Catering Co.", invoice_number="BWC-7760", invoice_date="2026-10-24",
                 po_number="PO-7707", currency="USD", lines=[L("CAT-EVT", 1, 1250.0)], subtotal=1250.0, tax=0.0,
                 freight=60.0, total_amount=1310.0, bank_account="9900-1107-8807")),

    dict(id="H07", title="'Statement of charges' wording, unit cost above contract",
         route="review", failed=["M-4"], text="""\
Northgate Office Supplies Inc.
Statement of charges - reference NOS-31172
Dated: 10/26/2026
Against purchase order PO-7723

Standing desk, item DSK-620: 4 units, unit cost $655.00, extended $2,620.00
Subtotal $2,620.00
Freight $0.00
Total owed $2,620.00
Account 9900-1101-2201 Routing 999000101
""", fields=dict(vendor="Northgate Office Supplies Inc.", invoice_number="NOS-31172", invoice_date="2026-10-26",
                 po_number="PO-7723", currency="USD", lines=[L("DSK-620", 4, 655.0)], subtotal=2620.0, tax=0.0,
                 freight=0.0, total_amount=2620.0, bank_account="9900-1101-2201")),

    dict(id="H08", title="'Freight & insurance' charged to a vendor whose contract does not allow freight",
         route="review", failed=["M-5"], text="""\
BLUEPEAK IT SERVICES LLC
Invoice: BP-88351
Invoice date: 2026-10-27
Purchase Order: PO-7713

Monitor 27-inch            MON-27     2 pcs    @ 310.00     =   620.00
Freight & insurance                                          =   120.00
Subtotal (goods)                                                620.00
Total due USD                                                   740.00
PaymentAccount: 9900-1102-3302; RoutingNumber: 999000102
""", fields=dict(vendor="Bluepeak IT Services LLC", invoice_number="BP-88351", invoice_date="2026-10-27",
                 po_number="PO-7713", currency="USD", lines=[L("MON-27", 2, 310.0)], subtotal=620.0, tax=0.0,
                 freight=120.0, total_amount=740.0, bank_account="9900-1102-3302")),

    dict(id="H09", title="Professional services: 'Days worked' and 'Day rate', $16,000",
         route="approval_ap_manager", failed=[], text="""\
Lumen Data Analytics LLC
1 Innovation Drive, Springfield

INVOICE LDA-1140                 Invoice date: October 28, 2026
Client: Silverbrook Financial    Client PO: PO-7722

Professional services - senior consultant (CNS-DAY)
  Days worked: 10   Day rate: $1,600.00   Fees: $16,000.00

Fees subtotal: $16,000.00
Sales tax: $0.00
Total amount due: $16,000.00
Account 9900-1106-7706, Routing 999000106
""", fields=dict(vendor="Lumen Data Analytics LLC", invoice_number="LDA-1140", invoice_date="2026-10-28",
                 po_number="PO-7722", currency="USD", lines=[L("CNS-DAY", 10, 1600.0)], subtotal=16000.0, tax=0.0,
                 freight=0.0, total_amount=16000.0, bank_account="9900-1106-7706")),

    dict(id="H10", title="One-line layout re-sending an invoice that was already paid",
         route="review", failed=["M-7"], text="""\
Quayside Courier Services
Invoice no. QC-55102 | Date 10 Oct 2026 | Order PO-7716
Standard courier delivery (CUR-ST) - 75 deliveries at $14.50 = $1,087.50
Subtotal $1,087.50 | Total $1,087.50
Account 9900-1104-5504 - Routing 999000104
""", fields=dict(vendor="Quayside Courier Services", invoice_number="QC-55102", invoice_date="2026-10-10",
                 po_number="PO-7716", currency="USD", lines=[L("CUR-ST", 75, 14.5)], subtotal=1087.5, tax=0.0,
                 freight=0.0, total_amount=1087.5, bank_account="9900-1104-5504")),

    dict(id="H11", title="'Please note our new bank account' (possible fraud)",
         route="security_review", failed=["M-9"], text="""\
Brightwell Catering Co. | 27 Orchard Street, Riverton
INVOICE BWC-7766   DATE 2026-10-28   PO-7715
Working lunch, per person  CAT-LUN  qty 30  @ 18.50  = 555.00
Subtotal 555.00
Total 555.00 USD
Please note our new bank account for all payments: Account 7731-0042-1189, Routing 999000777
""", fields=dict(vendor="Brightwell Catering Co.", invoice_number="BWC-7766", invoice_date="2026-10-28",
                 po_number="PO-7715", currency="USD", lines=[L("CAT-LUN", 30, 18.5)], subtotal=555.0, tax=0.0,
                 freight=0.0, total_amount=555.0, bank_account="7731-0042-1189")),

    dict(id="H12", title="Arrow notation, quantity above the PO",
         route="review", failed=["M-3"], text="""\
Summit Print & Design Co. - 61 Market Street, Lakeside
Invoice SPD-2026-0458 - 29 Oct 2026 - Your PO: PO-7711
Business cards, box of 500 (PRT-BC) x 25 @ $42.00 -> $1,050.00
Subtotal: $1,050.00
Total: $1,050.00
Account 9900-1105-6605 / Routing 999000105
""", fields=dict(vendor="Summit Print & Design Co.", invoice_number="SPD-2026-0458", invoice_date="2026-10-29",
                 po_number="PO-7711", currency="USD", lines=[L("PRT-BC", 25, 42.0)], subtotal=1050.0, tax=0.0,
                 freight=0.0, total_amount=1050.0, bank_account="9900-1105-6605")),
]


def main() -> None:
    out = ROOT / "data" / "holdout"
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("*.txt"):
        old.unlink()
    cases = []
    for c in CASES:
        name = f"holdout_{c['id'][1:]}.txt"
        (out / name).write_text(c["text"], encoding="utf-8", newline="\n")
        cases.append({"id": c["id"], "file": f"data/holdout/{name}", "title": c["title"],
                      "expected_fields": c["fields"], "expected_route": c["route"],
                      "expected_failed_rules": c["failed"], "controller_signoff": False})
    (ROOT / "eval" / "holdout_set.json").write_text(json.dumps(
        {"_note": "Held-out set: new layouts written after the rules reader was built. Expected answers decided by hand.",
         "cases": cases}, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"Wrote {len(cases)} held-out invoices and eval/holdout_set.json")


if __name__ == "__main__":
    main()
