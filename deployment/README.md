# Phase 4: Deployment and operations

How InvoiceMatch runs inside Silverbrook's infrastructure, safely and with clear ownership.

| Document | What it covers |
|---|---|
| [deployment_model.md](deployment_model.md) | SaaS vs VPC vs on-premise vs hybrid, the choice and why, environments and release path |
| [iam_and_secrets.md](iam_and_secrets.md) | Service accounts with least privilege, people's roles, where secrets live and how they rotate |
| [observability.md](observability.md) | Logs, metrics, traces, alerts, and dashboards |
| [runbook.md](runbook.md) | Safety switches, rollback, incident playbooks, the 2 AM checklist |
| [ownership.md](ownership.md) | Who runs it on day one, in week one, and at month six; RACI; handover checklist |

**In one line:** single-tenant in Silverbrook's own cloud account; only redacted invoice text leaves it, through the approved AI gateway; one switch (`AUTO_APPROVE_LIMIT=0`) sends everything to people within minutes.
