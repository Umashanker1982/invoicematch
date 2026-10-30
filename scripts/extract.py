"""Try the extraction agent from the command line.

    python scripts/extract.py data/invoices/invoice_05.txt            # Claude via SharedLLM (if a key is set)
    python scripts/extract.py data/invoices/invoice_05.txt --rules    # rules only, no AI
    python scripts/extract.py --all                                   # all 28 invoices vs the expected answers
    python scripts/extract.py --all --rules
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from invoicematch.config import load_settings  # noqa: E402
from invoicematch.evaluation import compare_fields  # noqa: E402
from invoicematch.extraction import extract_invoice  # noqa: E402


def show(path: Path, mode: str) -> None:
    r = extract_invoice(path.read_text(encoding="utf-8"), mode=mode)
    f = r.fields
    print(f"File          : {path.name}")
    print(f"Read by       : {r.method}" + (f"  (fallback: {r.fallback_reason})" if r.fallback_reason else ""))
    if r.llm and r.llm.ok:
        print(f"AI call       : {r.llm.model}, {r.llm.input_tokens} in / {r.llm.output_tokens} out tokens, "
              f"${r.llm.cost_usd:.5f}, {r.llm.latency_ms:.0f} ms (via SharedLLM)")
    print(f"Vendor        : {f.vendor}")
    print(f"Invoice no.   : {f.invoice_number}")
    print(f"Invoice date  : {f.invoice_date}")
    print(f"PO number     : {f.po_number}")
    print(f"Currency      : {f.currency}")
    for i, l in enumerate(f.lines, 1):
        print(f"Line {i:<9}: {l.sku}  x{l.quantity:g}  @ {l.unit_price}  = {l.amount}")
    print(f"Subtotal      : {f.subtotal}")
    print(f"Tax / Freight : {f.tax} / {f.freight}")
    print(f"TOTAL         : {f.total_amount}")
    print(f"Bank account  : {r.bank_account} (read by the parser, NOT sent to the AI)")
    print(f"Readable      : {r.readable}")
    for issue in r.issues:
        print(f"Issue         : {issue}")


def check_all(mode: str) -> int:
    golden = json.loads((ROOT / "eval" / "golden_set.json").read_text(encoding="utf-8"))["cases"]
    fields_ok = fields_total = invoices_ok = 0
    cost = 0.0
    methods: dict[str, int] = {}
    for case in golden:
        r = extract_invoice((ROOT / case["file"]).read_text(encoding="utf-8"), mode=mode)
        result = compare_fields(r.fields.model_dump(), case["expected_fields"])
        wrong = [k for k, ok in result.items() if not ok]
        fields_ok += sum(result.values())
        fields_total += len(result)
        invoices_ok += not wrong
        methods[r.method] = methods.get(r.method, 0) + 1
        cost += r.llm.cost_usd if r.llm else 0.0
        print(f"invoice_{case['id']:02d}  {r.method:<6}  {'OK' if not wrong else 'WRONG: ' + ', '.join(wrong)}")
    print(f"\nField accuracy   : {fields_ok}/{fields_total} = {fields_ok / fields_total:.1%}")
    print(f"Invoices all-correct: {invoices_ok}/{len(golden)}")
    print(f"Read by          : {methods}")
    print(f"AI cost (total)  : ${cost:.4f}")
    return 0


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    mode = "rules" if "--rules" in sys.argv else load_settings().llm_mode
    if "--all" in sys.argv:
        return check_all(mode)
    if not args:
        print(__doc__)
        return 1
    show(Path(args[0]), mode)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
