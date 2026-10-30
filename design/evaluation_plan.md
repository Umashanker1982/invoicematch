# Evaluation plan

How we know InvoiceMatch works before go-live, and how we know it **still** works after a prompt, model, rule, or vendor-layout change.

## 1. Test sets

| Set | Size | Purpose | Files |
|---|---|---|---|
| **Golden set** (sample invoices) | 28 | Covers every rule M-1..M-10 and every route; 4 layouts; also used to build the rules reader, so it is the **regression baseline** | [`eval/golden_set.json`](../eval/golden_set.json), [`data/invoices/`](../data/invoices) |
| **Held-out set** (new layouts) | 12 | Written afterwards, with layouts, labels, and number formats the rules reader was never built for; measures **generalization** | [`eval/holdout_set.json`](../eval/holdout_set.json), [`data/holdout/`](../data/holdout) |

Every expected answer (fields, route, failed rules) was decided **by hand** from the written rules, not computed by the code under test. Both sets are recreated by scripts (`scripts/make_sample_data.py`, `scripts/make_holdout_data.py`), and CI fails if the files drift from their generators.

In production, the golden set grows from real, anonymized invoices: every new vendor layout and every reviewer correction becomes a new test case.

## 2. What is measured

| Metric | Definition | Target (release gate) |
|---|---|---|
| Field accuracy | Correct fields / all fields (vendor, invoice no., date, PO, currency, subtotal, tax, freight, total, lines) | **≥ 97%** |
| Correct decisions | Route **and** the exact failed rules **and** sign-off flag all match | **≥ 98%** |
| **Wrong auto-approvals** | Invoices auto-approved that should not have been | **0, always** |
| Missed exceptions | Sent to an approver although a check should have failed | 0 |
| False exceptions | Sent to a person although it should have been approved | Tracked (cost of caution, not a safety issue) |
| AI cost per invoice | From token counts and prices | Under $0.002 |
| AI latency p50 / p95 | Per AI call | p95 under 6 s |

## 3. Results (measured)

Run on the engagement laptop with `python eval/benchmark.py --set all` (Claude through SharedLLM) and `--mode rules`. Full per-invoice tables: [`eval/results/`](../eval/results).

| Set | Reader | Field accuracy | Correct decisions | Wrong auto-approvals | Cost / invoice | AI time p50 / p95 |
|---|---|---|---|---|---|---|
| Golden (28) | **Claude Haiku 5.5 via SharedLLM** | **100%** | **28/28** | **0** | $0.00021 | ~2.0 / 3.2 s |
| Golden (28) | Rules only | 100% | 28/28 | 0 | $0 | - |
| Held-out (12) | **Claude Haiku 5.5 via SharedLLM** | **100%** | **12/12** | **0** | $0.00021 | ~2.2 / 3.0 s |
| Held-out (12) | Rules only | 39% | 0/12 | **0** | $0 | - |

**How to read this:**
- The rules reader's 100% on the golden set is a baseline, not proof: it was built on those layouts. On new layouts it reads 39% of fields and gets **no** decision right.
- It still **fails safely**: everything it cannot read goes to a person ("could not read invoice", M-10), never to payment. This is why the rules reader is acceptable as an outage fallback.
- Claude reads the new layouts perfectly at about 2 cents per 100 invoices, which is the measured reason the production design uses Claude for reading.
- **Safety held in every configuration:** zero wrong auto-approvals, because approval decisions are rules, not model output.

**What the evaluation caught during the build:** the first Claude runs scored 98.9% field accuracy (empty instead of zero tax/freight; no currency on a damaged invoice). The fix was deterministic defaults in code, with regression tests (see [technology_choices.md](technology_choices.md)).

## 4. Regression tests and gates (every change)

| Layer | What | Where |
|---|---|---|
| Unit and integration tests | The full test suite, offline, no key: parser, extraction (with a fake AI that behaves like SDK 2.x), every rule, every route, roles, audit chain, web app, limits | `tests/` |
| Regression gate | Golden set, rules mode: ≥ 95% correct decisions and 0 wrong auto-approvals | CI step `--gate` |
| Safety gate | Held-out set, rules mode: 0 wrong auto-approvals even when invoices cannot be read | CI step `--safety-gate` |
| Data integrity | Sample data identical to its generators | CI step `git diff --exit-code` |
| Pre-release (with AI) | Full benchmark in Claude mode on both sets, compared with the previous release | `python eval/benchmark.py --set all --baseline eval/results/golden_claude.json` |

CI runs on every push ([`.github/workflows/ci.yml`](../.github/workflows/ci.yml)). A prompt, model, or rule change cannot be merged if a gate fails.

## 5. Drift detection (in production)

Vendors change their invoice layouts, and models are updated. Drift is watched from four signals:

| Signal | Source | Alert threshold | Action |
|---|---|---|---|
| **Auditor agreement** on a weekly random sample of 50 decisions | Internal Audit sheet | Below 98% | Stop raising the auto-approval limit; analyze disagreements; add cases to the golden set |
| **Exception rate** | Audit log | Above 45%, or suddenly below 15% | Above: reading or rule problem. Below: possible rule or data failure; pause auto-approval |
| **Grounding discards and M-10 rate** | Extraction issues in the audit log | Doubling week over week, or concentrated on one vendor | Likely new layout; add it to the test set |
| **Benchmark vs baseline** | `eval/benchmark.py --baseline` (weekly scheduled run) | Field or decision accuracy down more than 2 points, or any new wrong auto-approval | Block releases; investigate the model or prompt change |

Per-vendor breakdowns make layout drift visible early: a jump in review rate for one vendor usually means that vendor changed its template.
