# Identity, access, and secrets

## Service accounts (least privilege)

Each part of the system has its own machine identity with only the permissions it needs.

| Service account | Used by | Allowed | Explicitly not allowed |
|---|---|---|---|
| `invoicematch-intake` | Mailbox / e-invoice connector | Read the AP mailbox folder; write to the intake queue and document store | Read decisions; call the ERP |
| `invoicematch-app` | InvoiceMatch service | Read the intake queue; read/write its database; append to the audit store; read its own secrets; call the AI gateway | Delete audit records; read other applications' secrets |
| `invoicematch-erp` | ERP integration (used by the app) | ERP API: **read** vendors, POs, contracts, invoice history; **write only** the invoice approval status | Create or change POs, vendors, bank details; run payments (N-5) |
| `invoicematch-audit-reader` | Internal Audit, Compliance | Read the audit store and decision reports | Write anything |
| `invoicematch-deployer` | CI/CD pipeline | Push images; update the service | Read production data or secrets' values |

## People and roles

Roles come from Silverbrook's identity provider groups (SSO + MFA). The approval matrix is in [../design/security_plan.md](../design/security_plan.md#1-identity-and-access-management-iam). Two rules matter most:
- **Administrators cannot approve invoices**, and approvers cannot change configuration (segregation of duties).
- Changes to approval limits (`AUTO_APPROVE_LIMIT`, `AP_MANAGER_LIMIT`, `CONTROLLER_LIMIT`) need Compliance sign-off and go through the normal change process.

## Secrets

| Secret | Stored in | Rotation | Notes |
|---|---|---|---|
| AI gateway key (`SHAREDLLM_KEY`) | Cloud secrets manager | Every 90 days, and immediately if exposed | The app never holds the AI provider's key: it lives in the gateway (bring-your-own-key, private) |
| ERP API credentials | Cloud secrets manager | Every 90 days | Scoped to the `invoicematch-erp` permissions above |
| Database credentials | Cloud secrets manager (managed rotation) | Automatic | |
| TLS certificates | Cloud certificate manager | Automatic renewal | |

**Rules for secrets**
- Injected as environment variables at start-up; never in code, images, logs, or the repository. `.env` is git-ignored; `.env.example` holds only placeholders.
- The app prints keys only in shortened form (for example `sk-sharedllm-...EfAE`); tested by `test_key_is_never_shown_in_full`.
- The gateway key has a monthly spend limit, so a leaked key cannot run up unlimited cost.
- **If a key is exposed:** revoke it in the gateway (API Keys → Revoke), create a new one, update the secrets manager, restart the service. Under 15 minutes; no code change. During the swap, invoices are read by rules and nothing is auto-approved that would not pass all checks.

## In this repository and demo

| Production | Here |
|---|---|
| Secrets manager | `.env` on the laptop (git-ignored); Render environment settings for the demo |
| SSO roles | Persona selector in the demo's review queue |
| ERP service account | `DemoERP` class: only `set_approval_status()` writes |
