# Deployment model

## Options considered

| Model | What it means | Fit with Silverbrook's constraints | Verdict |
|---|---|---|---|
| **SaaS** (vendor-hosted) | InvoiceMatch runs in our cloud; Silverbrook sends invoices to us | Invoice data leaves Silverbrook's account: fails data residency (N-1); harder vendor-risk review | Not for release 1 |
| **Customer VPC** (single-tenant, in Silverbrook's cloud account) | Same container image deployed into Silverbrook's own account and region, managed with their tools | Meets N-1, N-6, N-7; uses Silverbrook's SSO, logging, KMS, and change process | **Chosen** |
| **On-premise** | Runs on Silverbrook's own servers | Meets residency, but Silverbrook's ERP and identity are already in the cloud; slower to operate and scale | Not needed |
| **Hybrid** | Processing in the VPC; the AI model reached through an approved gateway outside it | This is what "Customer VPC" means in practice: the only external call is redacted text to the AI gateway | Part of the chosen model |

**Decision:** single-tenant deployment in **Silverbrook's cloud account (VPC), US region**, with AI calls through the **company-approved AI gateway**. If InfoSec later requires inference inside the account, the gateway setting points to Claude on the cloud provider's managed AI service instead. That is a configuration change (`LLM_BASE_URL`, `CLAUDE_MODEL`), not a redesign.

## Production layout

See the diagram in [../design/architecture.md](../design/architecture.md#production-deployment-inside-silverbrooks-cloud-account).

| Part | Production choice |
|---|---|
| Compute | Containers (the repository's image) on a managed container service, at least 2 instances in 2 availability zones, private subnets only |
| Entry point | Internal load balancer behind company SSO + MFA; not reachable from the internet |
| Intake | Connector reads the AP mailbox and the e-invoice portal and puts documents on a queue (retries, no lost invoices) |
| Database | Managed PostgreSQL, encrypted, automated backups, point-in-time restore |
| Audit store | Write-once object storage, 7-year retention |
| Outbound | Only to the AI gateway (HTTPS) and the ERP API, through an egress allow-list |

## Environments and release path

| Environment | Data | Purpose |
|---|---|---|
| Development | Sample data (this repository) | Build and unit tests |
| Test | Anonymized copies of real invoices | Benchmark with Claude; reviewer acceptance; ERP integration tests against the ERP test system |
| Production | Real invoices | Pilot vendors first (see [../adoption](../adoption)), then full volume |

1. **Every push:** CI runs the full test suite, the regression gate, and the safety gate.
2. **Release candidate:** full Claude benchmark on both test sets, compared with the previous release (`--baseline`); Compliance reviews any rule or limit change.
3. **Deploy:** new image tagged with the git commit, rolled out to one instance first (canary), then all.
4. **Rollback:** redeploy the previous image tag. See [runbook.md](runbook.md).

## How the public demo is hosted (not the production model)

The reviewer demo runs the same image as a single container on Render's free plan, with sample data only, per-visitor workspaces, rate limits, and a daily AI cap. It exists so reviewers can try the system; it is not a production deployment. How to deploy it is described in the repository README.
