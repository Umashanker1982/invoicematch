# Platform gaps

Things the product and platform teams should build once, so the next engagement does not rebuild them. Each gap is backed by something that actually happened in this engagement.

| # | Gap | What happened here | Recommendation | Priority |
|---|---|---|---|---|
| G-1 | **Gateway and SDK compatibility** | The gateway's compressed responses could not be decoded by the Python client (fixed with `Accept-Encoding: identity`); Anthropic SDK 2.x removed `temperature`, so calls failed before reaching the gateway | A maintained, tested client library for the gateway, pinned to supported SDK versions, with a compatibility test suite run against each SDK release | High |
| G-2 | **ERP connectors** | The ERP is simulated; every real customer needs read access to POs, vendors, contracts, and history plus one approval-status write | Certified connectors for the most common ERPs, with the read-only + one-write permission model built in | High |
| G-3 | **Rule configuration without code** | Rules and tolerances live in Python; changing a freight cap needs a developer | A rules configuration layer with versioning and an approval workflow for Compliance, still compiled into tested code | Medium |
| G-4 | **Evaluation as a service** | Golden sets, expected answers, gates, and drift checks were hand-built for this project | Shared tooling: labeling UI for expected answers, test-set versioning, scheduled benchmark runs, drift dashboards | High |
| G-5 | **Shared human-review queue** | The review queue, role checks, and written-reason rules were built into this app | A reusable human-in-the-loop service with SSO roles, delegation limits, SLAs, and audit integration | Medium |
| G-6 | **Write-once audit storage integration** | The hash chain is implemented; write-once storage and nightly verification are documented but not built | Standard module: WORM storage target + scheduled verification + alerting | Medium |
| G-7 | **Document ingestion** | Inputs here are text; production needs mailbox and e-invoice connectors, PDF text extraction, and later OCR | Shared ingestion service with retries, de-duplication of identical files, and redaction hooks | High |
| G-8 | **AI observability standard** | Tokens, cost, latency, fallbacks, and grounding discards are logged by this app's own code | Standard OpenTelemetry instrumentation for AI calls, with ready-made dashboards and alert rules | Medium |
| G-9 | **Model routing and evaluation gate** | Switching models is a configuration change, but nothing prevents switching to a model that has not passed the benchmark | Gateway-side policy: only models that passed a customer's benchmark can be selected for that workload | Low–medium |

## Feedback to the AI gateway team (SharedLLM)

1. Document the compressed-response behavior, or serve standard-compliant compression, so default HTTP clients work.
2. Show bring-your-own-key models in the model catalog and playground (the Anthropic key was usable for API calls but did not appear in either view, which caused confusion during setup).
3. Allow per-key model allow-lists and spend alerts, so a customer key can only call approved models.
