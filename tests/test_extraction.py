import json
from pathlib import Path

import pytest

from invoicematch.config import Settings
from invoicematch.evaluation import compare_fields
from invoicematch.extraction import SYSTEM_PROMPT, extract_invoice, normalize_date
from invoicematch.llm import GatewayClient
from invoicematch.parser import parse
from tests.fakes import FakeAnthropic

ROOT = Path(__file__).resolve().parents[1]
GOLDEN = json.loads((ROOT / "eval" / "golden_set.json").read_text(encoding="utf-8"))["cases"]
CLAUDE = Settings(llm_mode="claude", sharedllm_key="sk-sharedllm-test-key-1234567890", llm_base_url="https://gw.example/anthropic",
                  model="claude-haiku-5-5", llm_timeout_s=5, llm_max_retries=0)
RULES = Settings(llm_mode="rules", sharedllm_key=None, llm_base_url="x", model="claude-haiku-5-5",
                 llm_timeout_s=5, llm_max_retries=0)


def invoice(n: int) -> str:
    return (ROOT / "data" / "invoices" / f"invoice_{n:02d}.txt").read_text(encoding="utf-8")


def claude_reply_for(n: int, **overrides) -> dict:
    """What a correct Claude answer for invoice n looks like (taken from the expected answers)."""
    expected = dict(GOLDEN[n - 1]["expected_fields"])
    expected.pop("bank_account")
    expected.update(overrides)
    return expected


# --------------------------------------------------------------------------- document parser
def test_parser_reads_bank_details_and_removes_them_from_ai_text():
    doc = parse(invoice(22))
    assert doc.bank_account == "5512-0099-4471" and doc.bank_routing == "999000999"
    assert "5512-0099-4471" not in doc.text_for_ai and "999000999" not in doc.text_for_ai
    assert "[bank details removed]" in doc.text_for_ai
    assert "5512-0099-4471" in doc.text          # the full text keeps them for the M-9 check


def test_parser_flags_damaged_documents():
    assert parse(invoice(24)).damaged
    assert not parse(invoice(1)).damaged


@pytest.mark.parametrize("raw,iso", [("2026-10-08", "2026-10-08"), ("October 15, 2026", "2026-10-15"),
                                     ("14.10.2026", "2026-10-14"), ("10/27/2026", "2026-10-27"),
                                     ("06 Oct 2026", "2026-10-06"), ("31.02.2026", None), ("soon", None)])
def test_dates_are_normalized(raw, iso):
    assert normalize_date(raw) == iso


# --------------------------------------------------------------------------- rules reader
def test_rules_reader_matches_every_expected_field_on_the_sample_layouts():
    for case in GOLDEN:
        r = extract_invoice((ROOT / case["file"]).read_text(encoding="utf-8"), mode="rules", settings=RULES)
        assert r.method == "rules"
        wrong = [k for k, ok in compare_fields(r.fields.model_dump(), case["expected_fields"]).items() if not ok]
        assert not wrong, f"invoice {case['id']}: {wrong}"
        assert r.bank_account == case["expected_fields"]["bank_account"]


def test_damaged_invoice_is_marked_unreadable():
    r = extract_invoice(invoice(24), mode="rules", settings=RULES)
    assert not r.readable and r.fields.total_amount is None
    assert any("damaged" in i for i in r.issues)


# --------------------------------------------------------------------------- Claude through the gateway (faked)
def test_claude_answer_is_validated_and_used():
    fake = FakeAnthropic(json.dumps(claude_reply_for(5)))
    r = extract_invoice(invoice(5), mode="claude", settings=CLAUDE, client=GatewayClient(CLAUDE, client=fake))
    assert r.method == "claude" and r.fallback_reason is None
    assert all(compare_fields(r.fields.model_dump(), GOLDEN[4]["expected_fields"]).values())
    assert r.llm.ok and r.llm.input_tokens == 900 and r.llm.cost_usd > 0


def test_bank_details_are_never_sent_to_the_ai():
    fake = FakeAnthropic(json.dumps(claude_reply_for(22)))
    extract_invoice(invoice(22), mode="claude", settings=CLAUDE, client=GatewayClient(CLAUDE, client=fake))
    sent = fake.messages.calls[0]["messages"][0]["content"]
    assert "5512-0099-4471" not in sent and "999000999" not in sent
    assert sent.startswith("<invoice>") and sent.rstrip().endswith("</invoice>")


def test_prompt_treats_invoice_text_as_untrusted_data():
    fake = FakeAnthropic(json.dumps(claude_reply_for(25)))
    extract_invoice(invoice(25), mode="claude", settings=CLAUDE, client=GatewayClient(CLAUDE, client=fake))
    call = fake.messages.calls[0]
    assert call["system"] == SYSTEM_PROMPT and "untrusted" in SYSTEM_PROMPT
    assert "ignore all previous instructions" in call["messages"][0]["content"]  # passed as data, inside <invoice>
    assert "tools" not in call                                                     # the model cannot act


def test_made_up_po_number_and_total_are_discarded():
    reply = claude_reply_for(1, po_number="PO-9999", total_amount=9999.99)
    fake = FakeAnthropic(json.dumps(reply))
    r = extract_invoice(invoice(1), mode="claude", settings=CLAUDE, client=GatewayClient(CLAUDE, client=fake))
    assert r.method == "claude"
    assert r.fields.po_number is None and r.fields.total_amount is None
    assert any("PO-9999" in i for i in r.issues) and not r.readable


def test_messy_ai_formats_are_normalized():
    reply = claude_reply_for(6, invoice_date="14.10.2026", po_number=" po-7706 ", currency="usd")
    fake = FakeAnthropic("Here is the JSON:\n```json\n" + json.dumps(reply) + "\n```")
    r = extract_invoice(invoice(6), mode="claude", settings=CLAUDE, client=GatewayClient(CLAUDE, client=fake))
    assert r.method == "claude"
    assert (r.fields.invoice_date, r.fields.po_number, r.fields.currency) == ("2026-10-14", "PO-7706", "USD")


@pytest.mark.parametrize("bad_reply", ["Sorry, I can't help with that.", '{"vendor": ["not", "a", "string"]}',
                                       TimeoutError("gateway timeout")])
def test_invalid_reply_or_outage_falls_back_to_rules(bad_reply):
    fake = FakeAnthropic(bad_reply)
    r = extract_invoice(invoice(2), mode="claude", settings=CLAUDE, client=GatewayClient(CLAUDE, client=fake))
    assert r.method == "rules" and r.fallback_reason
    assert all(compare_fields(r.fields.model_dump(), GOLDEN[1]["expected_fields"]).values())


def test_gateway_client_uses_sharedllm_url_key_and_headers(monkeypatch):
    import anthropic

    captured = {}
    monkeypatch.setattr(anthropic, "Anthropic", lambda **kw: captured.update(kw) or FakeAnthropic())
    GatewayClient(CLAUDE)
    assert captured["base_url"] == "https://gw.example/anthropic"
    assert captured["default_headers"]["X-SharedLLM-Key"] == CLAUDE.sharedllm_key
    assert captured["default_headers"]["Accept-Encoding"] == "identity"
    assert captured["api_key"] == "via-gateway"            # no provider key inside the app


def test_rules_mode_makes_no_ai_call():
    fake = FakeAnthropic()
    r = extract_invoice(invoice(3), mode="rules", settings=CLAUDE, client=GatewayClient(CLAUDE, client=fake))
    assert r.method == "rules" and fake.messages.calls == [] and r.llm is None


def test_ai_call_uses_only_parameters_supported_by_the_sdk():
    fake = FakeAnthropic(json.dumps(claude_reply_for(1)))
    r = extract_invoice(invoice(1), mode="claude", settings=CLAUDE, client=GatewayClient(CLAUDE, client=fake))
    assert r.method == "claude", r.fallback_reason                 # the strict fake rejects e.g. temperature
    assert "temperature" not in fake.messages.calls[0]


def test_fallback_reason_explains_the_error():
    fake = FakeAnthropic(TypeError("create() got an unexpected keyword argument 'temperature'"))
    r = extract_invoice(invoice(1), mode="claude", settings=CLAUDE, client=GatewayClient(CLAUDE, client=fake))
    assert r.method == "rules" and "temperature" in r.fallback_reason


def test_empty_tax_freight_and_currency_get_safe_defaults():
    # Seen in integration testing: Claude returned null tax/freight on invoice 8 and null currency on invoice 24.
    fake = FakeAnthropic(json.dumps(claude_reply_for(8, tax=None, freight=None)),
                         json.dumps(claude_reply_for(24, currency=None)))
    client = GatewayClient(CLAUDE, client=fake)
    r8 = extract_invoice(invoice(8), mode="claude", settings=CLAUDE, client=client)
    r24 = extract_invoice(invoice(24), mode="claude", settings=CLAUDE, client=client)
    assert (r8.fields.tax, r8.fields.freight) == (0.0, 0.0)
    assert r24.fields.currency == "USD"
    assert r24.fields.tax is None                      # unreadable invoice: tax stays unknown
    assert all(compare_fields(r8.fields.model_dump(), GOLDEN[7]["expected_fields"]).values())
    assert all(compare_fields(r24.fields.model_dump(), GOLDEN[23]["expected_fields"]).values())


def test_euro_invoice_is_not_defaulted_to_usd():
    fake = FakeAnthropic(json.dumps(claude_reply_for(21, currency=None)))
    r = extract_invoice(invoice(21), mode="claude", settings=CLAUDE, client=GatewayClient(CLAUDE, client=fake))
    assert r.fields.currency is None                    # no "$" on a EUR invoice: left unknown
