# Reusable components

What from this engagement can be reused for the next customer, and how much work each needs. "As-is" means no code change; "configure" means settings or data only; "adapt" means customer-specific code.

| Component | Where | Reuse | What a new customer changes |
|---|---|---|---|
| **AI gateway client** (metering, cost, latency, never-raise fallback, SDK-compatibility guard) | [`llm.py`](../src/invoicematch/llm.py) | As-is | Gateway URL, model, keys |
| **Document parser with redaction** (reads and removes bank details before AI) | [`parser.py`](../src/invoicematch/parser.py) | Configure | Patterns for local bank formats (IBAN, sort codes) |
| **Typed extraction agent + grounding** (schema validation, values must be printed, deterministic defaults, rules fallback) | [`extraction.py`](../src/invoicematch/extraction.py), [`models.py`](../src/invoicematch/models.py) | As-is for invoices; the pattern works for any document | Schema fields for new document types |
| **Rules engine with rule ids and evidence** | [`matching.py`](../src/invoicematch/matching.py) | Configure (tolerances, windows), adapt (new rules) | Tolerances; customer-specific rules |
| **Approval routing from a Delegation of Authority** | [`approvals.py`](../src/invoicematch/approvals.py), [`config.py`](../src/invoicematch/config.py) | Configure | Limits and role names |
| **Hash-chained audit log** | [`audit.py`](../src/invoicematch/audit.py) | As-is | Storage target (write-once bucket) |
| **Review queue and UI** (role checks, written reasons, side-by-side evidence) | [`pipeline.py`](../src/invoicematch/pipeline.py), [`web/`](../web) | Adapt | SSO integration; branding |
| **Public-demo protections** (per-visitor workspaces, rate limits, AI cap, circuit breaker, security headers) | [`web/sandbox.py`](../web/sandbox.py), [`web/app.py`](../web/app.py) | As-is | Limits |
| **Evaluation harness** (golden + held-out sets, safety and regression gates, drift check, reports) | [`eval/benchmark.py`](../eval/benchmark.py), [`evaluation.py`](../src/invoicematch/evaluation.py) | As-is | The customer's own test documents |
| **Sample-data generators** with hand-decided expected answers | [`scripts/make_sample_data.py`](../scripts/make_sample_data.py), [`make_holdout_data.py`](../scripts/make_holdout_data.py) | Adapt | Vendors, contracts, layouts |
| **Fake AI clients for offline tests** (strict SDK-like fake, answer-key fake) | [`tests/fakes.py`](../tests/fakes.py) | As-is | - |
| **Business-case calculator** | [`scripts/business_case.py`](../scripts/business_case.py) | Configure | Volumes, times, costs |
| **Engagement templates** (interview template, stakeholder map, SMART metrics, runbook, ownership/RACI, pilot gates, demo script) | `discovery/`, `scoping/`, `deployment/`, `adoption/` | Configure | Names, numbers, constraints |

## What made these reusable

- **Clear boundaries:** reading, matching, routing, audit, and UI are separate modules with typed data between them.
- **Configuration over code:** limits, model, gateway, and tolerances come from environment variables.
- **Tests travel with the components:** each reusable part has tests that run offline without a key.

## Estimated effort to deploy for a similar customer

| Activity | With these assets | From scratch (estimate) |
|---|---|---|
| Discovery and scoping | 2 weeks (templates) | 3–4 weeks |
| Build and test | 3–4 weeks (mostly ERP connector and rules) | 10–12 weeks |
| Pilot | 6 weeks (same gates) | 6–8 weeks |
