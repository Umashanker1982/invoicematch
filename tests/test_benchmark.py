import json
from pathlib import Path

from invoicematch.config import Settings
from invoicematch.extraction import normalize_po
from invoicematch.llm import GatewayClient
from invoicematch.pipeline import InvoiceMatch
from scripts.make_holdout_data import CASES as HOLDOUT_CASES
from eval.benchmark import run, to_markdown
from tests.fakes import FakeAnthropic

ROOT = Path(__file__).resolve().parents[1]
RULES = Settings(llm_mode="rules", sharedllm_key=None, llm_base_url="x", model="claude-haiku-5-5",
                 llm_timeout_s=5, llm_max_retries=0)
CLAUDE = Settings(llm_mode="claude", sharedllm_key="sk-sharedllm-test-key-1234567890", llm_base_url="https://gw.example",
                  model="claude-haiku-5-5", llm_timeout_s=5, llm_max_retries=0)


def test_benchmark_on_the_main_set_in_rules_mode_passes_the_gate():
    s = run("golden", "rules", settings=RULES)["summary"]
    assert s["decision_accuracy"] == 1.0 and s["field_accuracy"] == 1.0
    assert s["wrong_auto_approvals"] == 0 and s["invoices"] == 28


def test_rules_reader_fails_safely_on_new_layouts():
    s = run("holdout", "rules", settings=RULES)["summary"]
    assert s["wrong_auto_approvals"] == 0 and s["missed_exceptions"] == 0   # unreadable -> a person, never payment
    assert s["decision_accuracy"] < 0.5                                     # and it really cannot read them


def test_holdout_decisions_are_right_when_the_fields_are_read_correctly():
    cases = json.loads((ROOT / "eval" / "holdout_set.json").read_text(encoding="utf-8"))["cases"]
    for case in cases:
        reply = {k: v for k, v in case["expected_fields"].items() if k != "bank_account"}
        im = InvoiceMatch(settings=CLAUDE, client=GatewayClient(CLAUDE, client=FakeAnthropic(json.dumps(reply))))
        item = im.process((ROOT / case["file"]).read_text(encoding="utf-8"), mode="claude")
        assert item.extraction.method == "claude", case["id"]
        assert item.extraction.bank_account == case["expected_fields"]["bank_account"], case["id"]
        assert (item.decision.route, sorted(item.decision.failed_rules)) == \
               (case["expected_route"], sorted(case["expected_failed_rules"])), case["id"]


def test_holdout_files_match_their_generator():
    for c in HOLDOUT_CASES:
        on_disk = (ROOT / "data" / "holdout" / f"holdout_{c['id'][1:]}.txt").read_text(encoding="utf-8")
        assert on_disk == c["text"]


def test_holdout_totals_add_up():
    for c in HOLDOUT_CASES:
        f = c["fields"]
        lines = sum(l["quantity"] * l["unit_price"] for l in f["lines"])
        assert round(lines + f["tax"] + f["freight"], 2) == f["total_amount"], c["id"]


def test_markdown_report_flags_safety():
    md = to_markdown(run("golden", "rules", settings=RULES))
    assert "Wrong auto-approvals (must be 0)" in md and "| 28 |" in md


def test_po_number_spellings_are_normalized():
    for raw in ("PO-7712", "PO 7712", "po#7712", "P.O. 7712", "7712", " po-7712 "):
        assert normalize_po(raw) == "PO-7712"
    assert normalize_po("ABC-12") == "ABC-12"
