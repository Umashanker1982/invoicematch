"""Matching engine: checks one extracted invoice against the PO, the contract, and the history.

Deterministic, written rules agreed with Compliance (scoping/scope.md). The AI is not involved here.
Every check returns a factual, neutral message (Procurement asked for "which line, by how much")
and the evidence used, so a reviewer or auditor can see exactly why.

Rule order and gates
* M-10 (readable) first: if the invoice could not be read, other checks are skipped (except M-9).
* M-1 (PO found and open) and M-2 (vendor matches PO) gate the line checks M-3..M-5.
* M-8 (currency) gates the price checks M-4 and M-5 (prices are agreed in USD).
* M-6 (arithmetic), M-7 (duplicates), and M-9 (bank details) always run when the invoice is readable.
"""
from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

from invoicematch.erp import DemoERP
from invoicematch.models import ExtractionResult

PRICE_TOLERANCE = 0.01      # M-4: unit price may exceed the contract price by at most 1% (rounding)
TOTAL_TOLERANCE = 1.00      # M-6: lines + tax + charges must equal the total within $1.00
DUPLICATE_WINDOW_DAYS = 14  # M-7: same vendor, PO, and total within 14 days = possible duplicate

RULE_NAMES = {
    "M-1": "PO found and open", "M-2": "Vendor matches the PO", "M-3": "Quantities within the PO",
    "M-4": "Prices match the contract", "M-5": "Extra charges allowed by the contract", "M-6": "Lines add up to the total",
    "M-7": "Not a duplicate", "M-8": "Currency is USD", "M-9": "Bank details match the vendor master",
    "M-10": "Invoice could be read reliably",
}


FAIL_LABELS = {
    "M-1": "PO problem", "M-2": "Vendor does not match the PO", "M-3": "Quantity problem",
    "M-4": "Price above contract", "M-5": "Extra charge not allowed", "M-6": "Totals do not add up",
    "M-7": "Possible duplicate", "M-8": "Currency not supported", "M-9": "Bank details changed",
    "M-10": "Invoice could not be read",
}


class Check(BaseModel):
    rule: str
    name: str
    status: Literal["pass", "fail", "skipped"]
    message: str
    evidence: dict = Field(default_factory=dict)


class LineEvidence(BaseModel):
    sku: str | None
    invoice_qty: float | None
    po_ordered: float | None = None
    po_already_invoiced: float | None = None
    po_remaining: float | None = None
    invoice_unit_price: float | None
    contract_unit_price: float | None = None
    price_difference_pct: float | None = None


class MatchResult(BaseModel):
    vendor_id: str | None
    vendor_master_name: str | None
    po_number: str | None
    checks: list[Check]
    lines: list[LineEvidence]

    @property
    def failed(self) -> list[str]:
        return [c.rule for c in self.checks if c.status == "fail"]


def _days_between(a: str | None, b: str | None) -> int | None:
    try:
        return abs((date.fromisoformat(a) - date.fromisoformat(b)).days)
    except (TypeError, ValueError):
        return None


def match_invoice(ex: ExtractionResult, erp: DemoERP) -> MatchResult:
    f = ex.fields
    checks: list[Check] = []

    def add(rule: str, status: str, message: str, **evidence) -> None:
        checks.append(Check(rule=rule, name=RULE_NAMES[rule], status=status, message=message, evidence=evidence))

    vendor_id, similarity = erp.find_vendor(f.vendor)
    vendor = erp.vendors.get(vendor_id) if vendor_id else None
    po = erp.get_po(f.po_number)
    contract = erp.get_contract(vendor_id)
    line_evidence = [LineEvidence(sku=l.sku, invoice_qty=l.quantity, invoice_unit_price=l.unit_price) for l in f.lines]

    # M-10: readable
    if not ex.readable:
        add("M-10", "fail", "The invoice could not be read reliably: " + "; ".join(ex.issues or ["unknown reason"]) + ".",
            issues=ex.issues)
    else:
        add("M-10", "pass", "All required fields were read" + (f" (notes: {'; '.join(ex.issues)})" if ex.issues else "."))
    readable = ex.readable

    # M-1: PO found and open
    po_ok = False
    if not readable:
        add("M-1", "skipped", "Skipped: the invoice could not be read.")
    elif not f.po_number:
        add("M-1", "fail", "No PO number was found on the invoice.")
    elif po is None:
        add("M-1", "fail", f"{f.po_number} does not exist in the ERP.", po_number=f.po_number)
    elif po["status"] != "open":
        add("M-1", "fail", f"{f.po_number} is {po['status']}; no further invoices can be booked against it.",
            po_number=f.po_number, po_status=po["status"])
    else:
        po_ok = True
        add("M-1", "pass", f"{f.po_number} is open.", po_number=f.po_number)

    # M-2: vendor matches PO
    vendor_ok = False
    if not po_ok:
        add("M-2", "skipped", "Skipped: no open PO to compare with.")
    elif vendor_id is None:
        add("M-2", "fail", f"Vendor '{f.vendor}' is not in the vendor master (closest match {similarity:.0%}).",
            invoice_vendor=f.vendor)
    elif vendor_id != po["vendor_id"]:
        add("M-2", "fail", f"The invoice is from {vendor['name']}, but {f.po_number} was issued to "
                           f"{erp.vendors[po['vendor_id']]['name']}.", invoice_vendor_id=vendor_id,
            po_vendor_id=po["vendor_id"])
    else:
        vendor_ok = True
        add("M-2", "pass", f"Vendor matches {f.po_number}: {vendor['name']} ({vendor_id}).", vendor_id=vendor_id)

    usd = (f.currency or "USD") == "USD"
    # M-8: currency
    if not readable:
        add("M-8", "skipped", "Skipped: the invoice could not be read.")
    elif usd:
        add("M-8", "pass", "Currency is USD.")
    else:
        add("M-8", "fail", f"Invoice currency is {f.currency}; release 1 handles USD invoices only.", currency=f.currency)

    # M-3: quantities, M-4: prices
    if not (po_ok and vendor_ok):
        add("M-3", "skipped", "Skipped: no matching PO.")
        add("M-4", "skipped", "Skipped: no matching PO.")
    else:
        qty_problems, price_problems = [], []
        po_lines = {l["sku"]: l for l in po["lines"]}
        for ev, line in zip(line_evidence, f.lines):
            pl = po_lines.get(line.sku)
            if pl is None:
                qty_problems.append(f"{line.sku or 'an unidentified item'} is not on {f.po_number}")
            else:
                remaining = pl["qty_ordered"] - pl["qty_invoiced"]
                ev.po_ordered, ev.po_already_invoiced, ev.po_remaining = pl["qty_ordered"], pl["qty_invoiced"], remaining
                if (line.quantity or 0) > remaining:
                    qty_problems.append(f"{line.sku}: invoiced {line.quantity:g}, but only {remaining:g} of "
                                        f"{pl['qty_ordered']:g} remain on {f.po_number}")
            price = (contract or {}).get("prices", {}).get(line.sku, {}).get("unit_price")
            ev.contract_unit_price = price
            if price is None:
                price_problems.append(f"{line.sku or 'an unidentified item'} has no agreed contract price")
            elif line.unit_price is not None:
                ev.price_difference_pct = round((line.unit_price - price) / price * 100, 1)
                if line.unit_price > price * (1 + PRICE_TOLERANCE):
                    price_problems.append(f"{line.sku}: invoiced ${line.unit_price:,.2f} each, contract "
                                          f"{contract['contract_id']} price is ${price:,.2f} "
                                          f"(+{ev.price_difference_pct:.1f}%, tolerance {PRICE_TOLERANCE:.0%})")
        if qty_problems:
            add("M-3", "fail", "; ".join(qty_problems) + ".")
        else:
            add("M-3", "pass", f"All quantities are within what remains on {f.po_number}.")
        if not usd:
            add("M-4", "skipped", "Skipped: contract prices are in USD.")
        elif price_problems:
            add("M-4", "fail", "; ".join(price_problems) + ".")
        else:
            add("M-4", "pass", "All unit prices match the contract (within 1%).")

    # M-5: extra charges
    freight = f.freight or 0.0
    if not (po_ok and vendor_ok and usd):
        add("M-5", "skipped", "Skipped: no matching USD PO and contract.")
    elif freight <= 0:
        add("M-5", "pass", "No extra charges.")
    elif not contract or not contract["freight_allowed"]:
        add("M-5", "fail", f"Freight of ${freight:,.2f} was charged, but contract "
                           f"{(contract or {}).get('contract_id', '(none)')} does not allow freight charges.",
            freight=freight)
    elif freight > contract["freight_cap"]:
        add("M-5", "fail", f"Freight of ${freight:,.2f} is above the ${contract['freight_cap']:,.2f} cap in contract "
                           f"{contract['contract_id']}.", freight=freight, cap=contract["freight_cap"])
    else:
        add("M-5", "pass", f"Freight of ${freight:,.2f} is allowed (cap ${contract['freight_cap']:,.2f}).")

    # M-6: arithmetic
    if not readable:
        add("M-6", "skipped", "Skipped: the invoice could not be read.")
    else:
        lines_sum = round(sum((l.amount if l.amount is not None else (l.quantity or 0) * (l.unit_price or 0))
                              for l in f.lines), 2)
        expected = round(lines_sum + (f.tax or 0) + freight, 2)
        diff = round((f.total_amount or 0) - expected, 2)
        if abs(diff) <= TOTAL_TOLERANCE:
            add("M-6", "pass", f"Lines ${lines_sum:,.2f} + tax ${f.tax or 0:,.2f} + charges ${freight:,.2f} = "
                               f"total ${f.total_amount:,.2f}.")
        else:
            add("M-6", "fail", f"Lines ${lines_sum:,.2f} + tax ${f.tax or 0:,.2f} + charges ${freight:,.2f} = "
                               f"${expected:,.2f}, but the invoice total is ${f.total_amount:,.2f} "
                               f"(difference ${diff:+,.2f}).", expected_total=expected, invoice_total=f.total_amount)

    # M-7: duplicates
    if not readable or vendor_id is None:
        add("M-7", "skipped", "Skipped: vendor or invoice could not be identified.")
    else:
        exact = [h for h in erp.history if h["vendor_id"] == vendor_id and h["invoice_number"] == f.invoice_number]
        similar = [h for h in erp.history if h["vendor_id"] == vendor_id and f.po_number and h["po_number"] == f.po_number
                   and abs((h["total"] or 0) - (f.total_amount or 0)) < 0.005
                   and (d := _days_between(h["invoice_date"], f.invoice_date)) is not None and d <= DUPLICATE_WINDOW_DAYS]
        if exact:
            add("M-7", "fail", f"Invoice {f.invoice_number} from this vendor was already processed "
                               f"(dated {exact[0]['invoice_date']}).", previous=exact[0])
        elif similar:
            h = similar[0]
            add("M-7", "fail", f"Invoice {h['invoice_number']} for the same PO and the same total "
                               f"(${h['total']:,.2f}) was processed {_days_between(h['invoice_date'], f.invoice_date)} "
                               f"days apart.", previous=h)
        else:
            add("M-7", "pass", "No earlier invoice with the same number, or the same PO and total within 14 days.")

    # M-9: bank details (always checked when the vendor is known)
    if vendor is None:
        add("M-9", "skipped", "Skipped: vendor not identified.")
    elif not ex.bank_account:
        add("M-9", "pass", "No bank details printed on the invoice; payment uses the vendor master.")
    elif ex.bank_account.replace(" ", "") != vendor["bank"]["account"].replace(" ", "") or (
            ex.bank_routing and ex.bank_routing != vendor["bank"]["routing"]):
        add("M-9", "fail", "The bank details on the invoice differ from the vendor master. Possible payment fraud: "
                           "verify with the vendor by phone using the number on file, never the one on the invoice.",
            invoice_account_last4=ex.bank_account[-4:], master_account_last4=vendor["bank"]["account"][-4:])
    else:
        add("M-9", "pass", "Bank details match the vendor master.")

    order = ["M-10", "M-1", "M-2", "M-3", "M-4", "M-5", "M-6", "M-7", "M-8", "M-9"]
    checks.sort(key=lambda c: order.index(c.rule))
    return MatchResult(vendor_id=vendor_id, vendor_master_name=vendor["name"] if vendor else None,
                       po_number=f.po_number, checks=checks, lines=line_evidence)
