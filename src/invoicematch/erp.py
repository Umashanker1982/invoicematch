"""Demo ERP: stands in for Silverbrook's finance system (vendors, contracts, purchase orders, invoice history).

Access rules from discovery (non-negotiable N-6): the ERP stays the system of record. InvoiceMatch may
**read** vendors, contracts, POs, and history, and may **only write one thing**: an invoice's approval
status, through `set_approval_status()` (in production, the ERP's existing approval-status API).
It can never create or change POs, vendors, or bank details (segregation of duties, N-5).

Each instance is an isolated in-memory copy of the sample data, so tests, the benchmark, and every
web visitor work on their own copy.
"""
from __future__ import annotations

import copy
import difflib
import json
import re
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

from invoicematch.config import ROOT

DATA_DIR = ROOT / "data"
_SUFFIXES = r"\b(inc|llc|ltd|limited|co|corp|corporation|company|plc)\b"


def normalize_name(name: str | None) -> str:
    if not name:
        return ""
    s = re.sub(r"[^a-z0-9 ]", " ", name.lower().replace("&", " and "))
    s = re.sub(_SUFFIXES, " ", s)
    return re.sub(r"\s+", " ", s).strip()


@lru_cache(maxsize=1)
def _load_seed(data_dir: str) -> dict:
    d = Path(data_dir)
    read = lambda name: json.loads((d / name).read_text(encoding="utf-8"))  # noqa: E731
    return {
        "vendors": read("vendors.json")["vendors"],
        "contracts": read("contracts.json")["contracts"],
        "purchase_orders": read("purchase_orders.json")["purchase_orders"],
        "history": read("invoice_history.json")["invoices"],
    }


class DemoERP:
    def __init__(self, data_dir: Path = DATA_DIR):
        seed = copy.deepcopy(_load_seed(str(data_dir)))
        self.vendors: dict = seed["vendors"]
        self.contracts: dict = seed["contracts"]
        self.purchase_orders: dict = seed["purchase_orders"]
        self.history: list = seed["history"]
        self.status_updates: list[dict] = []   # what InvoiceMatch wrote through the approval-status API

    # ------------------------------------------------------------------ reads
    def find_vendor(self, name: str | None) -> tuple[str | None, float]:
        """Match an invoice's vendor name to the vendor master. Returns (vendor_id, similarity)."""
        target = normalize_name(name)
        if not target:
            return None, 0.0
        best_id, best = None, 0.0
        for vid, v in self.vendors.items():
            score = difflib.SequenceMatcher(None, target, normalize_name(v["name"])).ratio()
            if score > best:
                best_id, best = vid, score
        return (best_id, round(best, 3)) if best >= 0.85 else (None, round(best, 3))

    def get_po(self, po_number: str | None) -> dict | None:
        return self.purchase_orders.get(po_number) if po_number else None

    def get_contract(self, vendor_id: str | None) -> dict | None:
        return self.contracts.get(vendor_id) if vendor_id else None

    # ------------------------------------------------------------------ the one permitted write
    def set_approval_status(self, *, vendor_id: str | None, invoice_number: str | None, po_number: str | None,
                            invoice_date: str | None, total: float | None, lines: list[dict], status: str,
                            actor: str) -> dict:
        """Simulates the ERP's approval-status API. 'approved' invoices are released to the normal payment run."""
        update = {"at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "vendor_id": vendor_id,
                  "invoice_number": invoice_number, "po_number": po_number, "status": status, "actor": actor}
        self.status_updates.append(update)
        if status == "approved":
            # The ERP records the invoice, so later duplicates and PO balances are detected.
            self.history.append({"vendor_id": vendor_id, "invoice_number": invoice_number,
                                 "invoice_date": invoice_date, "po_number": po_number, "total": total})
            po = self.get_po(po_number)
            if po:
                for line in lines:
                    for po_line in po["lines"]:
                        if po_line["sku"] == line.get("sku"):
                            po_line["qty_invoiced"] += line.get("quantity") or 0
        return update
