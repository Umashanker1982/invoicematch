"""InvoiceMatch benchmark: measures extraction, decisions, safety, cost, and speed on a fixed test set.

    python eval/benchmark.py                               # main sample set, current mode (Claude if a key is set)
    python eval/benchmark.py --set holdout                 # 12 new layouts never used to build the rules reader
    python eval/benchmark.py --set all --mode rules        # both sets, no AI
    python eval/benchmark.py --gate                        # exit 1 unless decisions >= 95% and 0 wrong auto-approvals
    python eval/benchmark.py --safety-gate                 # exit 1 if any invoice was wrongly auto-approved
    python eval/benchmark.py --baseline eval/results/golden_claude.json   # drift check vs an earlier run

Every invoice runs in a fresh workspace, so results never depend on the order of the invoices.
Results are saved to eval/results/<set>_<mode>.json and .md.
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from invoicematch.config import load_settings  # noqa: E402
from invoicematch.evaluation import compare_fields  # noqa: E402
from invoicematch.pipeline import InvoiceMatch  # noqa: E402

SETS = {"golden": ROOT / "eval" / "golden_set.json", "holdout": ROOT / "eval" / "holdout_set.json"}
APPROVAL_ROUTES = {"auto_approve", "approval_ap_manager", "approval_finance_controller", "approval_cfo"}
DRIFT_TOLERANCE = 0.02   # alert if accuracy drops by more than 2 percentage points vs the baseline


def percentile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int(round(q * (len(ordered) - 1))))]


def run(set_name: str, mode: str, settings=None) -> dict:
    cases = json.loads(SETS[set_name].read_text(encoding="utf-8"))["cases"]
    rows, field_hits, field_total, latencies = [], 0, 0, []
    started = time.perf_counter()
    for case in cases:
        im = InvoiceMatch(settings=settings) if settings else InvoiceMatch()
        t0 = time.perf_counter()
        item = im.process((ROOT / case["file"]).read_text(encoding="utf-8"), mode=mode)
        elapsed_ms = (time.perf_counter() - t0) * 1000
        ex, d = item.extraction, item.decision
        fields = compare_fields(ex.fields.model_dump(), case["expected_fields"])
        field_hits += sum(fields.values())
        field_total += len(fields)
        if ex.llm and ex.llm.ok:
            latencies.append(ex.llm.latency_ms)
        expected_route = case["expected_route"]
        decision_ok = (d.route == expected_route and sorted(d.failed_rules) == sorted(case["expected_failed_rules"])
                       and d.controller_signoff == case["controller_signoff"])
        rows.append({
            "id": case["id"], "title": case["title"], "read_by": ex.method, "fallback_reason": ex.fallback_reason,
            "fields_wrong": [k for k, ok in fields.items() if not ok],
            "bank_ok": ex.bank_account == case["expected_fields"].get("bank_account"),
            "expected_route": expected_route, "route": d.route,
            "expected_failed": case["expected_failed_rules"], "failed": d.failed_rules,
            "decision_ok": decision_ok,
            "wrong_auto_approval": d.route == "auto_approve" and expected_route != "auto_approve",
            "missed_exception": d.route in APPROVAL_ROUTES and expected_route not in APPROVAL_ROUTES,
            "false_exception": d.route not in APPROVAL_ROUTES and expected_route in APPROVAL_ROUTES,
            "cost_usd": ex.llm.cost_usd if ex.llm else 0.0, "ms": round(elapsed_ms, 1),
        })
    n = len(rows)
    methods: dict[str, int] = {}
    for r in rows:
        methods[r["read_by"]] = methods.get(r["read_by"], 0) + 1
    summary = {
        "set": set_name, "mode": mode, "model": (settings or load_settings()).model if mode == "claude" else None,
        "run_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "invoices": n,
        "field_accuracy": round(field_hits / field_total, 4),
        "invoices_fully_read": sum(not r["fields_wrong"] for r in rows),
        "bank_details_read": sum(r["bank_ok"] for r in rows),
        "decision_accuracy": round(sum(r["decision_ok"] for r in rows) / n, 4),
        "correct_decisions": sum(r["decision_ok"] for r in rows),
        "wrong_auto_approvals": sum(r["wrong_auto_approval"] for r in rows),
        "missed_exceptions": sum(r["missed_exception"] for r in rows),
        "false_exceptions": sum(r["false_exception"] for r in rows),
        "no_touch_rate": round(sum(r["route"] == "auto_approve" for r in rows) / n, 4),
        "review_rate": round(sum(r["route"] in {"review", "security_review"} for r in rows) / n, 4),
        "read_by": methods, "fallbacks": sum(bool(r["fallback_reason"]) for r in rows),
        "ai_cost_total_usd": round(sum(r["cost_usd"] for r in rows), 5),
        "ai_cost_per_invoice_usd": round(sum(r["cost_usd"] for r in rows) / n, 6),
        "ai_latency_p50_ms": round(percentile(latencies, 0.5)), "ai_latency_p95_ms": round(percentile(latencies, 0.95)),
        "total_seconds": round(time.perf_counter() - started, 1),
    }
    return {"summary": summary, "cases": rows}


def to_markdown(result: dict) -> str:
    s = result["summary"]
    lines = [f"# Benchmark: {s['set']} set, {s['mode']} mode", "",
             f"Run at {s['run_at']}" + (f" with `{s['model']}` through SharedLLM" if s["model"] else ""), "",
             "| Metric | Value |", "|---|---|",
             f"| Invoices | {s['invoices']} |",
             f"| Field accuracy | {s['field_accuracy']:.1%} |",
             f"| Invoices read completely right | {s['invoices_fully_read']}/{s['invoices']} |",
             f"| Correct decisions | {s['correct_decisions']}/{s['invoices']} ({s['decision_accuracy']:.1%}) |",
             f"| **Wrong auto-approvals (must be 0)** | **{s['wrong_auto_approvals']}** |",
             f"| Missed exceptions | {s['missed_exceptions']} |",
             f"| False exceptions (sent to a person unnecessarily) | {s['false_exceptions']} |",
             f"| No-touch rate on this set | {s['no_touch_rate']:.0%} |",
             f"| Read by | {', '.join(f'{k}: {v}' for k, v in s['read_by'].items())} (fallbacks: {s['fallbacks']}) |",
             f"| AI cost | ${s['ai_cost_total_usd']:.4f} total, ${s['ai_cost_per_invoice_usd']:.5f} per invoice |",
             f"| AI latency p50 / p95 | {s['ai_latency_p50_ms']} / {s['ai_latency_p95_ms']} ms |", "",
             "| Invoice | Read by | Expected | Got | Fields wrong | Result |", "|---|---|---|---|---|---|"]
    for r in result["cases"]:
        exp = r["expected_route"] + (f" ({', '.join(r['expected_failed'])})" if r["expected_failed"] else "")
        got = r["route"] + (f" ({', '.join(r['failed'])})" if r["failed"] else "")
        flag = "OK" if r["decision_ok"] else ("**WRONG AUTO-APPROVAL**" if r["wrong_auto_approval"] else "wrong")
        lines.append(f"| {r['id']} {r['title']} | {r['read_by']} | {exp} | {got} | "
                     f"{', '.join(r['fields_wrong']) or '-'} | {flag} |")
    return "\n".join(lines) + "\n"


def drift(current: dict, baseline_path: Path) -> list[str]:
    base = json.loads(baseline_path.read_text(encoding="utf-8"))["summary"]
    alerts = []
    for key in ("field_accuracy", "decision_accuracy"):
        drop = base[key] - current[key]
        print(f"  {key:<18} baseline {base[key]:.1%} -> now {current[key]:.1%} ({-drop:+.1%})")
        if drop > DRIFT_TOLERANCE:
            alerts.append(f"{key} dropped by {drop:.1%} (tolerance {DRIFT_TOLERANCE:.0%})")
    if current["wrong_auto_approvals"] > base["wrong_auto_approvals"]:
        alerts.append("new wrong auto-approvals")
    return alerts


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--set", choices=["golden", "holdout", "all"], default="golden")
    p.add_argument("--mode", choices=["claude", "rules"], default=None)
    p.add_argument("--gate", action="store_true", help="require >= 95%% correct decisions and 0 wrong auto-approvals")
    p.add_argument("--safety-gate", action="store_true", help="require 0 wrong auto-approvals")
    p.add_argument("--baseline", type=Path, help="earlier results file to compare with (drift check)")
    p.add_argument("--no-save", action="store_true")
    args = p.parse_args()
    mode = args.mode or load_settings().llm_mode

    failures: list[str] = []
    for set_name in (["golden", "holdout"] if args.set == "all" else [args.set]):
        result = run(set_name, mode)
        s = result["summary"]
        print(f"\n== {set_name} set, {mode} mode ==")
        for r in result["cases"]:
            if not r["decision_ok"] or r["fields_wrong"]:
                print(f"  {r['id']}: expected {r['expected_route']} {r['expected_failed']}, got {r['route']} {r['failed']}; "
                      f"fields wrong: {r['fields_wrong'] or '-'}" + (f"; {r['fallback_reason']}" if r["fallback_reason"] else ""))
        print(f"  Field accuracy        : {s['field_accuracy']:.1%}  ({s['invoices_fully_read']}/{s['invoices']} invoices fully right)")
        print(f"  Correct decisions     : {s['correct_decisions']}/{s['invoices']} ({s['decision_accuracy']:.1%})")
        print(f"  Wrong auto-approvals  : {s['wrong_auto_approvals']}   (missed exceptions {s['missed_exceptions']}, "
              f"false exceptions {s['false_exceptions']})")
        print(f"  Read by               : {s['read_by']}  fallbacks: {s['fallbacks']}")
        print(f"  AI cost               : ${s['ai_cost_total_usd']:.4f} total, ${s['ai_cost_per_invoice_usd']:.5f} per invoice")
        print(f"  AI latency p50 / p95  : {s['ai_latency_p50_ms']} / {s['ai_latency_p95_ms']} ms")
        if not args.no_save:
            out = ROOT / "eval" / "results"
            out.mkdir(parents=True, exist_ok=True)
            (out / f"{set_name}_{mode}.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
            (out / f"{set_name}_{mode}.md").write_text(to_markdown(result), encoding="utf-8", newline="\n")
            print(f"  Saved                 : eval/results/{set_name}_{mode}.json and .md")
        if args.baseline:
            print("  Drift check:")
            failures += [f"{set_name}: {a}" for a in drift(s, args.baseline)]
        if (args.gate or args.safety_gate) and s["wrong_auto_approvals"]:
            failures.append(f"{set_name}: {s['wrong_auto_approvals']} wrong auto-approval(s)")
        if args.gate and s["decision_accuracy"] < 0.95:
            failures.append(f"{set_name}: decision accuracy {s['decision_accuracy']:.1%} is below 95%")

    if failures:
        print("\nGATE FAILED:\n  " + "\n  ".join(failures))
        return 1
    if args.gate or args.safety_gate or args.baseline:
        print("\nGATE PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
