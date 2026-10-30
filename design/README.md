# Phase 3: Solution design

A system that matches the scope in [../scoping/scope.md](../scoping/scope.md) and respects Silverbrook's constraints: data stays in its cloud account, the ERP stays the system of record, and the existing approval chain is unchanged.

| Document | What it covers |
|---|---|
| [architecture.md](architecture.md) | Future-state flow (ingestion, extraction, matching, approval, ERP update), production deployment diagram, what this repository implements |
| [components.md](components.md) | The six components (document parser, extraction agent, matching engine, approval workflow, human review UI, audit log) plus the AI gateway |
| [technology_choices.md](technology_choices.md) | Model, gateway, framework, database, and deployment choices, with measured evidence and alternatives |
| [security_plan.md](security_plan.md) | IAM, data handling, encryption, human approval for high-value mismatches, threat model mapped to tests |
| [evaluation_plan.md](evaluation_plan.md) | Golden and held-out sets, accuracy targets, measured results, regression gates, drift detection |

**Runnable code:** the extraction agent is in [`src/invoicematch/extraction.py`](../src/invoicematch/extraction.py) (typed `InvoiceFields` schema, as in the brief's example). Try it with `python scripts/extract.py data/invoices/invoice_05.txt`.

**Design principle in one line:** *AI reads; rules decide; people approve.*
