# Technology choices

Every choice below is justified by a customer constraint or a measured result, not by preference. Measured numbers come from [`eval/results/`](../eval/results), produced by `python eval/benchmark.py --set all`.

## Summary

| Area | Choice | Main reason |
|---|---|---|
| AI model | **Claude Haiku 5.5** (`claude-haiku-5-5`) | 100% field accuracy on both test sets at ~$0.0002 per invoice and ~2 s |
| AI access | **Behind an AI gateway** (SharedLLM here; the company-approved gateway in production) | One controlled, logged, metered path; no provider key inside the app |
| Agent framework | **Anthropic Python SDK + pydantic**, no agent framework | One model call per invoice with a typed output; explicit control and few dependencies |
| Decisions | **Deterministic Python rules** | Compliance requires exact, explainable, testable approvals |
| Web / API | **FastAPI** + plain JavaScript | Small, typed, fast; no front-end build step for the customer to maintain |
| Database (production) | **PostgreSQL** for queue and decisions; **write-once object storage** for the audit log | Transactions for approvals; tamper-proof, 7-year retention for audit |
| Deployment (production) | **Containers in Silverbrook's own cloud account (VPC)** | Data residency (N-1) and the company's existing cloud controls |
| Demo hosting | **Render** (one container) | A public, zero-maintenance demo for reviewers; not the production target |

## 1. Why Claude Haiku 5.5, and not a bigger or cheaper model?

The extraction task is reading, not reasoning: find about ten fields and the line items in one invoice. That suits a small, fast model.

| Measured (40 invoices) | Claude Haiku 5.5 | Rules reader (no AI) |
|---|---|---|
| Field accuracy, sample layouts (28) | **100%** | 100% (built for these layouts) |
| Field accuracy, **new layouts** (12) | **100%** | 39% |
| Correct decisions, new layouts | **12/12** | 0/12 (all safely sent to a person) |
| Wrong auto-approvals | **0** | 0 |
| Cost per invoice | **~$0.0002** | $0 |
| Median time per invoice | **~2 s** | under 1 ms |

- **A bigger model** would cost several times more and be slower, and accuracy has no room to improve on these tests. Money decisions are not made by the model, so extra reasoning power buys nothing here. Re-evaluate only if a future test set (for example scanned invoices) shows Haiku falling below the 97% field-accuracy gate.
- **A cheaper or open model** (for example the gateway's pool models) is possible. The gateway makes switching a configuration change (`CLAUDE_MODEL`), and the benchmark is the switching gate: a candidate must match the accuracy and safety numbers above on the same test sets before it is used.
- **At production volume** (3,400 invoices a month) the AI cost is under **$1 a month**. Model cost is irrelevant to the business case; accuracy and control are what matter.

## 2. Why behind an AI gateway?

The course asks: *why does this tool run locally, remotely, or behind a gateway?*

| Need (from discovery) | How the gateway helps |
|---|---|
| CFO: cost control | Every call is metered (tokens and dollars) and spend limits can be set per key |
| Compliance: auditability | A second, independent log of every AI call, outside the application |
| InfoSec: no shadow AI, key control | The provider key stays in the gateway's pool (bring-your-own-key); the app holds only a revocable gateway key |
| Operations: resilience | The model or provider can be switched without a code change |

**Integration findings** (real problems found and fixed while connecting through SharedLLM):

| Finding | Fix |
|---|---|
| The gateway's compressed responses could not be decoded by the Python HTTP client | Send `Accept-Encoding: identity` |
| Anthropic SDK 2.x removed the `temperature` parameter; the call failed before reaching the gateway | Removed it; the test fake now rejects unsupported parameters like the real SDK |
| The model sometimes returned null for tax, freight, or currency | Deterministic defaults in code, covered by tests |

## 3. Why no agent framework?

The brief's example uses an agent with instructions and a typed `output_type`. InvoiceMatch uses exactly that pattern (`InvoiceFields`, `extract_invoice_async`) with the Anthropic SDK directly:

- There is **one model call per invoice** and no tool use: a framework adds layers without adding capability.
- **Typed output** is enforced by pydantic validation plus grounding checks, which also catch values that are valid JSON but wrong.
- Fewer dependencies mean fewer things for Silverbrook's security team to review and patch.
- If Silverbrook later standardizes on a framework, only `extraction.py` changes; the schema, rules, and tests stay.

## 4. Why deterministic rules for decisions?

Compliance's condition for delegating anything was: *"The AI can read the invoice. It cannot decide to pay."* Rules give:
- the same answer every time, for the same input;
- a rule id for every decision, explainable to an auditor in two minutes;
- changes through configuration and code review, not retraining;
- 100% unit-test coverage of every rule, run on every change in CI.

## 5. Data stores (production)

| Data | Store | Why |
|---|---|---|
| Review queue, decisions, overrides | PostgreSQL (managed, encrypted) | Transactions prevent double approval; easy reporting |
| Audit log | Write-once object storage with 7-year retention, plus the hash chain | Cannot be edited even by administrators; chain verified nightly |
| Invoice documents | Encrypted object storage, 7-year retention | Evidence for audit; never sent outside the account except redacted text to the AI |
| ERP data | Stays in the ERP; read through its API | ERP remains the system of record (N-6) |

This repository keeps these in memory (or a JSON Lines file for the audit log), which is enough to demonstrate the behavior.

## Alternatives considered

| Option | Why not chosen (for release 1) |
|---|---|
| Template-based OCR products | Need a template per vendor layout; new layouts fail, as the rules reader shows (0/12 on new layouts) |
| A larger model for higher accuracy | No measurable gain; more cost and latency |
| Letting the AI make the decision | Fails Compliance's non-negotiable; harder to audit and test |
| Fully managed SaaS AP automation | Data would leave Silverbrook's cloud account (N-1); less control over rules |
| Calling the AI provider directly | Loses central metering, logging, and key control; the gateway is the approved path |
