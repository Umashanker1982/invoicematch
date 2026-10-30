"""Checks that the sample data is complete, consistent, and matches its generator."""
import json
from collections import Counter
from pathlib import Path

from scripts.make_sample_data import CASES, build_invoice

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def test_files_on_disk_match_the_generator():
    for case in CASES:
        text, _ = build_invoice(case)
        on_disk = (ROOT / "data" / "invoices" / f"invoice_{case['id']:02d}.txt").read_text(encoding="utf-8")
        assert on_disk == text, f"invoice_{case['id']:02d}.txt is out of date: run python scripts/make_sample_data.py"


def test_golden_set_covers_every_invoice_and_every_rule():
    golden = load("eval/golden_set.json")["cases"]
    assert len(golden) == 28
    assert all((ROOT / g["file"]).exists() for g in golden)
    failed = {r for g in golden for r in g["expected_failed_rules"]}
    assert failed == {f"M-{i}" for i in range(1, 11)}, "every matching rule M-1..M-10 is tested at least once"
    routes = Counter(g["expected_route"] for g in golden)
    assert set(routes) == {"auto_approve", "approval_ap_manager", "approval_finance_controller",
                           "approval_cfo", "review", "security_review"}


def test_reference_data_is_consistent():
    vendors = load("data/vendors.json")["vendors"]
    contracts = load("data/contracts.json")["contracts"]
    for po, rec in load("data/purchase_orders.json")["purchase_orders"].items():
        assert rec["vendor_id"] in vendors, po
        for line in rec["lines"]:
            price = contracts[rec["vendor_id"]]["prices"][line["sku"]]["unit_price"]
            assert line["unit_price"] == price, f"{po} {line['sku']} price differs from contract"
            assert 0 <= line["qty_invoiced"] <= line["qty_ordered"]


def test_totals_add_up_except_the_deliberate_error():
    for g in load("eval/golden_set.json")["cases"]:
        f = g["expected_fields"]
        if f["total"] is None:
            continue
        computed = round(sum(l["quantity"] * l["unit_price"] for l in f["lines"]) + f["tax"] + f["freight"], 2)
        if "M-6" in g["expected_failed_rules"]:
            assert computed != f["total"]
        else:
            assert computed == f["total"], g["id"]


def test_no_real_looking_bank_numbers():
    for v in load("data/vendors.json")["vendors"].values():
        assert v["bank"]["routing"].startswith("999"), "sample routing numbers use the fake 999 range"
