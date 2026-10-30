"""Run the full InvoiceMatch pipeline from the command line.

    python scripts/process.py data/invoices/invoice_11.txt     # one invoice: fields, checks, decision
    python scripts/process.py --all                            # all 28 invoices vs the expected decisions
    python scripts/process.py --demo                           # approvals, roles, duplicates, audit log
    add --rules to any command to run without AI
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from invoicematch.config import load_settings  # noqa: E402
from invoicematch.pipeline import ApprovalError, InvoiceMatch  # noqa: E402

ICONS = {"pass": "PASS", "fail": "FAIL", "skipped": "skip"}


def show(item) -> None:
    ex, f = item.extraction, item.extraction.fields
    print(f"\n{item.ref}  {item.vendor_name}  invoice {f.invoice_number}  {f.po_number}  "
          f"total {f.total_amount if f.total_amount is not None else 'unreadable'}  (read by {ex.method})")
    for c in item.match.checks:
        print(f"  {ICONS[c.status]}  {c.rule:<5} {c.name:<38} {c.message if c.status != 'pass' else ''}")
    print(f"  DECISION: {item.decision.label}  [{', '.join(item.decision.rule_ids)}]")
    for r in item.decision.reasons:
        print(f"    - {r}")


def run_all(mode: str) -> int:
    golden = json.loads((ROOT / "eval" / "golden_set.json").read_text(encoding="utf-8"))["cases"]
    correct = 0
    for case in golden:
        im = InvoiceMatch()   # fresh workspace per invoice, so results do not depend on order
        item = im.process((ROOT / case["file"]).read_text(encoding="utf-8"), mode=mode)
        d = item.decision
        ok = (d.route == case["expected_route"] and sorted(d.failed_rules) == sorted(case["expected_failed_rules"])
              and d.controller_signoff == case["controller_signoff"])
        correct += ok
        print(f"invoice_{case['id']:02d}  {item.extraction.method:<6}  {d.label:<34} "
              f"{','.join(d.failed_rules) or '-':<6} {'OK' if ok else 'WRONG (expected ' + case['expected_route'] + ' ' + ','.join(case['expected_failed_rules']) + ')'}")
    print(f"\nCorrect decisions: {correct}/{len(golden)}")
    return 0 if correct == len(golden) else 1


def demo(mode: str) -> int:
    im = InvoiceMatch()
    read = lambda n: (ROOT / "data" / "invoices" / f"invoice_{n:02d}.txt").read_text(encoding="utf-8")  # noqa: E731
    print("1) A $14,080 invoice that matches its PO needs the AP Manager (rule A-2):")
    item = im.process(read(8), mode=mode)
    show(item)
    print("\n2) An AP Specialist tries to approve it:")
    try:
        im.approve(item.ref, actor="Tom Becker", role="ap_specialist")
    except ApprovalError as exc:
        print(f"   BLOCKED: {exc}")
    print("\n3) The AP Manager approves it; the ERP status is set to approved:")
    im.approve(item.ref, actor="Priya Natarajan", role="ap_manager", note="Matches PO-7708.")
    print(f"   {item.ref} is now {item.status}, by {item.resolved_by}")
    print("\n4) The vendor sends the same invoice again:")
    show(im.process(read(8), mode=mode))
    print("\n5) A price mismatch on a $35,000 invoice needs a Finance Controller (high-value mismatch):")
    hv = im.process(read(26), mode=mode)
    show(hv)
    for actor, role, note in [("Priya Natarajan", "ap_manager", "Rate increase agreed by email."),
                              ("Omar Haddad", "finance_controller", "Rejected: rate increase not in the contract.")]:
        try:
            im.reject(hv.ref, actor=actor, role=role, note=note)
            print(f"   {actor} rejected it: {note}")
        except ApprovalError as exc:
            print(f"   BLOCKED for {actor}: {exc}")
    print("\n6) Audit log:")
    for r in im.audit.records:
        print(f"   #{r['seq']:<2} {r['action']:<18} by {r['actor']:<36} {r['invoice']}")
    ok, message = im.audit.verify()
    print(f"   {message}")
    return 0 if ok else 1


def main() -> int:
    mode = "rules" if "--rules" in sys.argv else load_settings().llm_mode
    if "--all" in sys.argv:
        return run_all(mode)
    if "--demo" in sys.argv:
        return demo(mode)
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__)
        return 1
    show(InvoiceMatch().process(Path(args[0]).read_text(encoding="utf-8"), mode=mode))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
