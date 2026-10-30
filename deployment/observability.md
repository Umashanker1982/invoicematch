# Observability: logs, metrics, traces, alerts

The goal: at 2 AM, someone on call can tell within minutes whether InvoiceMatch is **up**, **reading correctly**, **deciding safely**, and **within budget**.

## Logs

| Log | Content | Already in this repository |
|---|---|---|
| **Decision log** | One structured JSON line per invoice: reference, route, rule ids, read by (Claude or rules), fallback, AI latency and cost, grounding discards, circuit-breaker state. **No invoice text, no bank details.** | Yes: `invoice_decided` lines in [`web/app.py`](../web/app.py) |
| **Audit log** | Every decision and human action with actor, reason, evidence; hash-chained | Yes: [`audit.py`](../src/invoicematch/audit.py) |
| **Gateway log** | Every AI call: tokens, cost, latency, status (independent of the app) | Yes: SharedLLM dashboard |
| **Application and access logs** | Errors with stack traces; HTTP requests | Yes (server logs) |

Example decision log line:
```json
{"event": "invoice_decided", "ref": "IM-0003", "route": "review", "rules": ["A-4", "M-4"], "read_by": "claude",
 "fallback": false, "ai_ok": true, "ai_ms": 1980.4, "ai_cost_usd": 0.00021, "grounding_discards": 0, "breaker": "closed"}
```

## Metrics

Derived from the decision and audit logs (production: exported to the cloud monitoring service).

| Metric | Why it matters | Linked success metric |
|---|---|---|
| Invoices processed per hour, by route | Volume and mix | Adoption |
| **No-touch rate** | Share auto-approved | Primary metric |
| **Exception rate** | Share sent to people | Guardrail metric |
| Fallback rate (read by rules because the AI failed) | Gateway or model health | - |
| Grounding discards and M-10 (unreadable) rate | Reading quality; new vendor layouts | Quality |
| AI latency p50 / p95 and errors | User experience; gateway health | - |
| AI cost per day | Budget | Business |
| Review queue size and **oldest item age** | People are keeping up | Exception resolution time |
| Audit chain verification result (nightly) | Tamper detection | Compliance |

## Traces

In production, each invoice gets one trace with a span per pipeline step: **parse → read (AI call) → ground → match → decide → record → ERP status**, tagged with the invoice reference (not its content). This shows where time goes and which step failed. The web demo shows the same steps as its progress strip. Implementation: OpenTelemetry (already a dependency of the Anthropic SDK) exporting to the cloud tracing service.

## Alerts

| Alert | Condition | Severity | First action (see [runbook.md](runbook.md)) |
|---|---|---|---|
| Service down | Health check (`/healthz`) failing 2 minutes | Page | Restart; roll back if after a release |
| AI gateway failing | Fallback rate > 20% for 15 minutes, or circuit breaker open | Warn | Check gateway status; invoices continue via rules and people |
| **Exception rate high** | > 45% for a day | Warn | Check reading quality and recent rule changes |
| **Exception rate suddenly low** | < 15% for a day | **Page** | Possible rule or data failure: set `AUTO_APPROVE_LIMIT=0` and investigate |
| Reading quality drop | Grounding discards or M-10 rate doubled week over week | Warn | Find the vendor; add the layout to the test set |
| Queue backlog | Oldest review item older than 2 business days | Warn | AP Manager reassigns work |
| Cost spike | AI cost per day > 3x the 7-day average | Warn | Check for abuse or loops; gateway spend limit is the backstop |
| **Audit chain broken** | Nightly verification fails | **Page** | Security incident: preserve evidence; see runbook |
| **Wrong auto-approval found** | Auditor sample finds one | **Page** | Set `AUTO_APPROVE_LIMIT=0`; see runbook |

## Dashboards

| Audience | Shows | Cadence |
|---|---|---|
| Executives (CFO) | No-touch rate, hours saved, cost, auditor agreement | Weekly one-pager (see the adoption plan) |
| AP Manager | Queue size and age, exception reasons, top vendors with problems | Live |
| On call | Health, fallback rate, latency, errors, alerts | Live |

The demo website's **Metrics** tab shows the session version of these numbers.
