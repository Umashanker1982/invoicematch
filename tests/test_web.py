from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import web.app as webapp
from tests.fakes import AnswerKeyAnthropic, FakeAnthropic

ROOT = Path(__file__).resolve().parents[1]
V1, V2 = "a" * 32, "b" * 32


def text(name: str) -> str:
    folder = "holdout" if name.startswith("holdout") else "invoices"
    return (ROOT / "data" / folder / f"{name}.txt").read_text(encoding="utf-8")


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(webapp.CLIENT, "_client", AnswerKeyAnthropic())
    monkeypatch.setattr(webapp, "AI_AVAILABLE", True)
    monkeypatch.setattr(webapp, "AI_BREAKER", webapp.CircuitBreaker())
    monkeypatch.setattr(webapp, "AI_CAP", webapp.DailyCap(100))
    monkeypatch.setattr(webapp, "MANAGER", webapp.WorkspaceManager(webapp.SETTINGS, webapp.CLIENT))
    webapp._ip_hits.clear()
    return TestClient(webapp.app)


def post(c, path, body=None, visitor=V1):
    return c.post(path, json=body or {}, headers={"X-Visitor": visitor})


def test_page_has_security_headers(client):
    r = client.get("/")
    assert r.status_code == 200 and "InvoiceMatch" in r.text
    assert "script-src 'self'" in r.headers["content-security-policy"]
    assert r.headers["x-frame-options"] == "DENY"
    assert client.get("/healthz").json() == {"status": "ok"}


def test_config_and_samples(client):
    cfg = client.get("/api/config").json()
    assert cfg["ai_available"] and cfg["gateway"] == "SharedLLM" and cfg["author"]
    samples = client.get("/api/samples").json()
    assert len(samples) == 40 and {s["group"] for s in samples} == {"sample", "new_layout"}


def test_clean_invoice_is_read_by_claude_and_auto_approved(client):
    r = post(client, "/api/process", {"text": text("invoice_01"), "mode": "claude"}).json()
    assert r["read_by"] == "claude" and r["llm"]["ok"]
    assert r["decision"]["route"] == "auto_approve" and r["status"] == "approved"
    assert r["audit"]["seq"] == 1 and len(r["checks"]) == 10


def test_new_layout_needs_claude(client):
    with_ai = post(client, "/api/process", {"text": text("holdout_02"), "mode": "claude"}).json()
    rules = post(client, "/api/process", {"text": text("holdout_02"), "mode": "rules"}, visitor=V2).json()
    assert with_ai["decision"]["route"] == "auto_approve"
    assert rules["decision"]["route"] == "review" and rules["read_by"] == "rules"


def test_review_queue_enforces_roles(client):
    item = post(client, "/api/process", {"text": text("invoice_22"), "mode": "claude"}).json()
    assert item["decision"]["route"] == "security_review" and item["allowed_roles"] == ["security"]
    queue = client.get("/api/queue", headers={"X-Visitor": V1}).json()
    assert [i["ref"] for i in queue["pending"]] == [item["ref"]]
    blocked = post(client, f"/api/queue/{item['ref']}/approve", {"actor": "Diana Reyes", "role": "cfo", "note": "Looks fine to me."})
    assert blocked.status_code == 403 and blocked.json()["blocked"]
    done = post(client, f"/api/queue/{item['ref']}/reject",
                {"actor": "Kevin Osei", "role": "security", "note": "Vendor confirmed by phone: not changed."})
    assert done.status_code == 200 and done.json()["status"] == "rejected"
    assert client.get("/api/queue", headers={"X-Visitor": V1}).json()["pending"] == []


def test_audit_log_verifies_and_detects_tampering(client):
    post(client, "/api/process", {"text": text("invoice_11"), "mode": "claude"})
    a = client.get("/api/audit", headers={"X-Visitor": V1}).json()
    assert a["verified"] and a["total"] == 2
    t = post(client, "/api/audit/tamper").json()
    assert not t["verified"] and "broken" in t["message"]


def test_workspaces_are_private_and_resettable(client):
    post(client, "/api/process", {"text": text("invoice_08"), "mode": "claude"})
    assert client.get("/api/queue", headers={"X-Visitor": V2}).json()["pending"] == []
    assert client.get("/api/metrics", headers={"X-Visitor": V1}).json()["session"]["processed"] == 1
    post(client, "/api/reset")
    assert client.get("/api/metrics", headers={"X-Visitor": V1}).json()["session"]["processed"] == 0


def test_gateway_failure_falls_back_to_rules_with_a_notice(client, monkeypatch):
    monkeypatch.setattr(webapp.CLIENT, "_client", FakeAnthropic(*[ConnectionError("gateway down")] * 5))
    r = post(client, "/api/process", {"text": text("invoice_01"), "mode": "claude"}).json()
    assert r["read_by"] == "rules" and r["notice"] and r["decision"]["route"] == "auto_approve"


def test_circuit_breaker_pauses_ai_after_repeated_failures(client, monkeypatch):
    monkeypatch.setattr(webapp.CLIENT, "_client", FakeAnthropic(*[ConnectionError("gateway down")] * 5))
    for _ in range(3):
        post(client, "/api/process", {"text": text("invoice_01"), "mode": "claude"})
    assert webapp.AI_BREAKER.state == "open"
    r = post(client, "/api/process", {"text": text("invoice_01"), "mode": "claude"}).json()
    assert "paused" in r["notice"] and r["llm"] is None


def test_input_limits_and_rate_limits(client, monkeypatch):
    assert post(client, "/api/process", {"text": "x" * 9000}).status_code in (400, 413)
    assert post(client, "/api/process", {"text": "hello"}, visitor="not-valid").status_code == 400
    big = client.post("/api/process", content=b"{" + b" " * 40000 + b"}",
                      headers={"X-Visitor": V1, "Content-Type": "application/json"})
    assert big.status_code == 413
    monkeypatch.setattr(webapp, "REQUESTS_PER_WINDOW", 2)
    codes = [post(client, "/api/process", {"text": text("invoice_01"), "mode": "rules"}, visitor=V2).status_code
             for _ in range(3)]
    assert codes == [200, 200, 429]


def test_browser_errors_get_a_branded_page(client, monkeypatch):
    r = client.get("/no-such-page", headers={"Accept": "text/html"})
    assert r.status_code == 404 and "InvoiceMatch" in r.text and "Page not found" in r.text
    monkeypatch.setattr(webapp, "MAINTENANCE", True)
    assert client.get("/", headers={"Accept": "text/html"}).status_code == 503
    assert client.get("/healthz").status_code == 200


def test_metrics_include_benchmark_results(client):
    post(client, "/api/process", {"text": text("invoice_01"), "mode": "claude"})
    m = client.get("/api/metrics", headers={"X-Visitor": V1}).json()
    assert m["session"]["no_touch_rate"] == 1.0 and m["session"]["read_by_ai"] == 1
    assert isinstance(m["benchmarks"], list)
