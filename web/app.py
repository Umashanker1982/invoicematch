"""InvoiceMatch web demo: a FastAPI server over the same pipeline the command-line tools use.

    uvicorn web.app:app --reload        (local: http://127.0.0.1:8000)

Pages: process an invoice, review queue (with role-based approvals), audit log (with a live
tamper test), metrics, and how it works. Every visitor gets an isolated workspace.

Protection for a public deployment: per-visitor workspaces, per-visitor and per-IP rate limits,
a daily cap on AI calls, a circuit breaker for gateway outages, a request size limit, security
headers, branded error pages, and a maintenance switch.
"""
from __future__ import annotations

import html
import json
import logging
import os
import re
import sys
import threading
import time
from collections import defaultdict, deque
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fastapi import FastAPI, Header, HTTPException, Request  # noqa: E402
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402
from starlette.exceptions import HTTPException as StarletteHTTPException  # noqa: E402

from invoicematch.approvals import ROUTE_ROLES  # noqa: E402
from invoicematch.config import load_settings  # noqa: E402
from invoicematch.llm import GatewayClient  # noqa: E402
from invoicematch.matching import RULE_NAMES  # noqa: E402
from invoicematch.pipeline import ROLE_LABELS, ApprovalError, ProcessedInvoice  # noqa: E402
from web.sandbox import VISITOR_ID, CircuitBreaker, DailyCap, WorkspaceManager  # noqa: E402

SETTINGS = load_settings()
AUTHOR = os.environ.get("DEMO_AUTHOR", "Umashanker")
REPO_URL = os.environ.get("DEMO_REPO_URL", "https://github.com/Umashanker1982/invoicematch")
REQUESTS_PER_WINDOW = int(os.environ.get("DEMO_REQUESTS_PER_10MIN", "40"))
IP_REQUESTS_PER_WINDOW = int(os.environ.get("DEMO_IP_REQUESTS_PER_10MIN", "120"))
WINDOW_S = 600
MAX_TEXT_CHARS = 8_000
MAX_BODY_BYTES = 32 * 1024
MAINTENANCE = os.environ.get("MAINTENANCE_MODE", "").strip().lower() in {"1", "true", "yes", "on"}

CLIENT = GatewayClient(SETTINGS)
AI_AVAILABLE = CLIENT.enabled
AI_CAP = DailyCap(int(os.environ.get("DEMO_DAILY_AI_REQUESTS", "400")))
AI_BREAKER = CircuitBreaker(threshold=3, window_s=120, cooldown_s=300)
MANAGER = WorkspaceManager(SETTINGS, CLIENT)
STATIC = Path(__file__).resolve().parent / "static"

log = logging.getLogger("invoicematch.web")
logging.basicConfig(stream=sys.stderr, level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
_ip_hits: dict[str, deque[float]] = defaultdict(deque)
_ip_lock = threading.Lock()

SECURITY_HEADERS = {
    "Content-Security-Policy": (
        "default-src 'self'; script-src 'self'; style-src 'self' https://fonts.googleapis.com; "
        "font-src https://fonts.gstatic.com; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; "
        "base-uri 'self'; form-action 'self'; object-src 'none'"
    ),
    "X-Frame-Options": "DENY",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=()",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Cross-Origin-Opener-Policy": "same-origin",
}

app = FastAPI(title="InvoiceMatch", docs_url=None, redoc_url=None, openapi_url=None)

# ---------------------------------------------------------------- error pages
ERROR_COPY = {
    404: ("Page not found", "No match", "This address doesn't lead anywhere in the demo. The link may be mistyped.", "Back to the demo"),
    429: ("Slow down a little", "On hold", "That was a lot of requests in a short time. Wait a minute and try again.", "Back to the demo"),
    500: ("Something went wrong on our side", "Exception", "The demo hit an unexpected problem. It has been logged and the site is still running.", "Try again"),
    503: ("Back shortly", "Closed for audit", "The demo is being updated right now. Please check back in a few minutes.", "Reload"),
}


def error_page(code: int) -> HTMLResponse:
    title, stamp, message, action = ERROR_COPY.get(code, ERROR_COPY[500])
    page = (STATIC / "error.html").read_text(encoding="utf-8")
    for key, value in {"code": str(code), "title": title, "stamp": stamp, "message": message, "action": action}.items():
        page = page.replace("{{" + key + "}}", html.escape(value))
    return HTMLResponse(page, status_code=code)


def _wants_html(request: Request) -> bool:
    return not request.url.path.startswith("/api/") and "text/html" in request.headers.get("accept", "")


@app.middleware("http")
async def guard(request: Request, call_next):
    """Maintenance switch, request size limit, and security headers on every response."""
    if MAINTENANCE and request.url.path != "/healthz":
        response = error_page(503) if _wants_html(request) else JSONResponse(
            {"error": "The demo is being updated. Please try again in a few minutes."}, status_code=503)
    elif int(request.headers.get("content-length") or 0) > MAX_BODY_BYTES:
        response = JSONResponse({"error": "Request too large."}, status_code=413)
    else:
        try:
            response = await call_next(request)
        except Exception:  # last-resort net: the server keeps running
            log.exception("unhandled error on %s", request.url.path)
            response = error_page(500) if _wants_html(request) else JSONResponse(
                {"error": "Something went wrong on our side. Please try again."}, status_code=500)
    for name, value in SECURITY_HEADERS.items():
        response.headers.setdefault(name, value)
    return response


@app.exception_handler(StarletteHTTPException)
async def http_errors(request: Request, exc: StarletteHTTPException):
    if _wants_html(request):
        return error_page(exc.status_code)
    return JSONResponse({"error": exc.detail if isinstance(exc.detail, str) else "Request failed."},
                        status_code=exc.status_code)


app.mount("/static", StaticFiles(directory=STATIC), name="static")


# ---------------------------------------------------------------- helpers
def _workspace(visitor: str | None):
    if not visitor or not VISITOR_ID.match(visitor):
        raise HTTPException(400, "Missing or invalid visitor id. Reload the page.")
    return MANAGER.get(visitor)


def _client_ip(request: Request) -> str:
    fwd = request.headers.get("x-forwarded-for", "")
    return fwd.split(",")[0].strip() or (request.client.host if request.client else "unknown")


def _ip_allowed(ip: str) -> bool:
    now = time.time()
    with _ip_lock:
        hits = _ip_hits[ip]
        while hits and now - hits[0] > WINDOW_S:
            hits.popleft()
        if len(hits) >= IP_REQUESTS_PER_WINDOW:
            return False
        hits.append(now)
        return True


def _load_cases(name: str, group: str) -> list[dict]:
    data = json.loads((ROOT / "eval" / name).read_text(encoding="utf-8"))["cases"]
    return [{"id": f"{c['id']:02d}" if isinstance(c["id"], int) else c["id"], "group": group, "title": c["title"],
             "file": c["file"], "expected_route": c["expected_route"]} for c in data]


SAMPLES = _load_cases("golden_set.json", "sample") + _load_cases("holdout_set.json", "new_layout")
SAMPLE_TEXT = {s["id"]: (ROOT / s["file"]).read_text(encoding="utf-8") for s in SAMPLES}


def view(item: ProcessedInvoice, audit_seq: int | None = None, audit_hash: str | None = None) -> dict[str, Any]:
    ex, f, m, d = item.extraction, item.extraction.fields, item.match, item.decision
    llm = ex.llm.model_dump() if ex.llm else None
    return {
        "ref": item.ref, "status": item.status, "resolved_by": item.resolved_by, "resolution_note": item.resolution_note,
        "vendor_name": item.vendor_name, "vendor_id": m.vendor_id,
        "fields": f.model_dump(), "read_by": ex.method, "fallback_reason": ex.fallback_reason, "llm": llm,
        "bank_found": ex.bank_account is not None, "issues": ex.issues, "readable": ex.readable,
        "checks": [c.model_dump() for c in m.checks],
        "lines": [l.model_dump() for l in m.lines],
        "decision": d.model_dump(),
        "allowed_roles": sorted(ROUTE_ROLES.get(d.route, set()) & ({"finance_controller", "cfo"} if d.controller_signoff else set(ROLE_LABELS))),
        "audit": {"seq": audit_seq, "hash": audit_hash[:12] if audit_hash else None},
    }


def _metrics(ws) -> dict[str, Any]:
    items = list(ws.im.invoices.values())
    n = len(items)
    ai = [i.extraction.llm for i in items if i.extraction.llm and i.extraction.llm.ok]
    routes: dict[str, int] = {}
    for i in items:
        routes[i.decision.route] = routes.get(i.decision.route, 0) + 1
    return {
        "processed": n, "routes": routes,
        "no_touch_rate": round(routes.get("auto_approve", 0) / n, 3) if n else None,
        "review_rate": round((routes.get("review", 0) + routes.get("security_review", 0)) / n, 3) if n else None,
        "read_by_ai": len(ai), "ai_cost_usd": round(sum(u.cost_usd for u in ai), 5),
        "ai_latency_ms_avg": round(sum(u.latency_ms for u in ai) / len(ai)) if ai else None,
        "pending": len(ws.im.pending()),
    }


def _benchmarks() -> list[dict]:
    out = []
    for path in sorted((ROOT / "eval" / "results").glob("*.json")):
        try:
            s = json.loads(path.read_text(encoding="utf-8"))["summary"]
        except (OSError, ValueError, KeyError):
            continue
        out.append({k: s.get(k) for k in ("set", "mode", "model", "run_at", "invoices", "field_accuracy",
                                          "correct_decisions", "decision_accuracy", "wrong_auto_approvals",
                                          "ai_cost_per_invoice_usd", "ai_latency_p50_ms")})
    return out


# ---------------------------------------------------------------- pages and API
@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(STATIC / "index.html")


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/config")
def config() -> dict[str, Any]:
    return {
        "author": AUTHOR, "repo_url": REPO_URL, "project": "Capstone 2: Full FDE Engagement Simulation",
        "client": "Silverbrook Financial", "model": SETTINGS.model, "gateway": "SharedLLM",
        "ai_available": AI_AVAILABLE, "ai_remaining_today": AI_CAP.remaining if AI_AVAILABLE else 0,
        "ai_breaker": AI_BREAKER.state,
        "limits": {"auto_approve": SETTINGS.auto_approve_limit, "ap_manager": SETTINGS.ap_manager_limit,
                   "controller": SETTINGS.controller_limit, "requests_per_10_min": REQUESTS_PER_WINDOW,
                   "max_chars": MAX_TEXT_CHARS},
        "roles": ROLE_LABELS, "rules": RULE_NAMES,
    }


@app.get("/api/samples")
def samples() -> list[dict]:
    return [{**s, "text": SAMPLE_TEXT[s["id"]]} for s in SAMPLES]


class ProcessIn(BaseModel):
    text: str = Field(min_length=1)
    mode: str = "claude"


@app.post("/api/process")
def process(body: ProcessIn, request: Request, x_visitor: str | None = Header(None)) -> dict[str, Any]:
    ws = _workspace(x_visitor)
    text = body.text.strip()
    if not text:
        raise HTTPException(400, "Paste or pick an invoice first.")
    if len(text) > MAX_TEXT_CHARS:
        raise HTTPException(400, f"Invoice text is too long (max {MAX_TEXT_CHARS:,} characters).")
    if not _ip_allowed(_client_ip(request)) or not ws.allow(REQUESTS_PER_WINDOW, WINDOW_S):
        raise HTTPException(429, "Too many invoices in a short time. Wait a minute and try again.")

    notice = None
    mode = "rules"
    if body.mode == "claude":
        if not AI_AVAILABLE:
            notice = "AI is not configured on this server, so the rules reader was used."
        elif not AI_BREAKER.allow():
            notice = "The AI gateway had repeated errors, so AI is paused for a few minutes. The rules reader was used."
        elif not AI_CAP.take():
            notice = "Today's AI budget for the public demo is used up. The rules reader was used."
        else:
            mode = "claude"
    with ws.lock:
        item = ws.im.process(text, mode=mode)
        record = ws.im.audit.records[-2] if len(ws.im.audit.records) >= 2 else None
    if mode == "claude" and item.extraction.llm is not None:
        AI_BREAKER.record(item.extraction.llm.ok)
    llm = item.extraction.llm
    # One structured log line per decision (no invoice text, no bank details): feeds dashboards and alerts.
    log.info(json.dumps({"event": "invoice_decided", "ref": item.ref, "route": item.decision.route,
                         "rules": item.decision.rule_ids, "read_by": item.extraction.method,
                         "fallback": bool(item.extraction.fallback_reason), "ai_ok": llm.ok if llm else None,
                         "ai_ms": llm.latency_ms if llm else None, "ai_cost_usd": llm.cost_usd if llm else 0.0,
                         "grounding_discards": sum("not found in the invoice text" in i for i in item.extraction.issues),
                         "breaker": AI_BREAKER.state}))
    result = view(item, record["seq"] if record else None, record["hash"] if record else None)
    result["notice"] = notice or (item.extraction.fallback_reason and
                                  "The AI could not be used for this invoice, so the rules reader took over.")
    return result


@app.get("/api/queue")
def queue(x_visitor: str | None = Header(None)) -> dict[str, Any]:
    ws = _workspace(x_visitor)
    items = list(ws.im.invoices.values())
    return {"pending": [view(i) for i in items if i.status == "pending"],
            "resolved": [view(i) for i in reversed(items) if i.status != "pending"][:30]}


class ActionIn(BaseModel):
    actor: str = Field(min_length=2, max_length=60)
    role: str
    note: str = Field("", max_length=300)


def _act(ref: str, body: ActionIn, x_visitor: str | None, action: str) -> dict[str, Any]:
    ws = _workspace(x_visitor)
    if body.role not in ROLE_LABELS:
        raise HTTPException(400, "Unknown role.")
    if not re.fullmatch(r"IM-\d{4}", ref):
        raise HTTPException(404, "Unknown invoice.")
    with ws.lock:
        try:
            fn = ws.im.approve if action == "approve" else ws.im.reject
            item = fn(ref, actor=body.actor.strip(), role=body.role, note=body.note.strip())
        except ApprovalError as exc:
            return JSONResponse({"error": str(exc), "blocked": True}, status_code=403)
    return view(item)


@app.post("/api/queue/{ref}/approve")
def approve(ref: str, body: ActionIn, x_visitor: str | None = Header(None)):
    return _act(ref, body, x_visitor, "approve")


@app.post("/api/queue/{ref}/reject")
def reject(ref: str, body: ActionIn, x_visitor: str | None = Header(None)):
    return _act(ref, body, x_visitor, "reject")


@app.get("/api/audit")
def audit(x_visitor: str | None = Header(None)) -> dict[str, Any]:
    ws = _workspace(x_visitor)
    ok, message = ws.im.audit.verify()
    return {"records": ws.im.audit.records[-60:], "total": len(ws.im.audit.records), "verified": ok, "message": message}


@app.post("/api/audit/tamper")
def tamper(x_visitor: str | None = Header(None)) -> dict[str, Any]:
    """Demo only, in the visitor's own workspace: quietly edit an old audit record, then verify."""
    ws = _workspace(x_visitor)
    with ws.lock:
        decided = [r for r in ws.im.audit.records if r["action"] == "decided"]
        if not decided:
            raise HTTPException(400, "Process an invoice first, so there is a record to tamper with.")
        target = decided[0]
        target["details"]["route"] = "auto_approve"
        target["details"]["tampered_demo"] = True
        ok, message = ws.im.audit.verify()
    return {"verified": ok, "message": message, "edited_record": target["seq"]}


@app.get("/api/metrics")
def metrics(x_visitor: str | None = Header(None)) -> dict[str, Any]:
    return {"session": _metrics(_workspace(x_visitor)), "benchmarks": _benchmarks()}


@app.post("/api/reset")
def reset(x_visitor: str | None = Header(None)) -> dict[str, str]:
    _workspace(x_visitor)
    MANAGER.reset(x_visitor)
    return {"status": "reset"}
