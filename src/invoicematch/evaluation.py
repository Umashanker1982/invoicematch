"""Field-level comparison between extracted fields and the expected answers (eval/golden_set.json)."""
from __future__ import annotations

import re
from typing import Any

SCALAR_FIELDS = ("vendor", "invoice_number", "invoice_date", "po_number", "currency",
                 "subtotal", "tax", "freight", "total_amount")


def _norm(value: Any) -> Any:
    if isinstance(value, str):
        return re.sub(r"[^a-z0-9]", "", value.lower())
    if isinstance(value, (int, float)):
        return round(float(value), 2)
    return value


def compare_fields(got: dict, expected: dict) -> dict[str, bool]:
    """Return {field: correct?} for every scalar field plus 'lines' (sku, quantity, unit price)."""
    result = {name: _norm(got.get(name)) == _norm(expected.get(name)) for name in SCALAR_FIELDS}
    got_lines = [(_norm(l.get("sku")), _norm(l.get("quantity")), _norm(l.get("unit_price"))) for l in got.get("lines", [])]
    exp_lines = [(_norm(l.get("sku")), _norm(l.get("quantity")), _norm(l.get("unit_price"))) for l in expected.get("lines", [])]
    result["lines"] = got_lines == exp_lines
    return result
