# Runbook: rollback and incident response

## Safety switches (no code change, minutes to apply)

| Switch | Setting | Effect | Use when |
|---|---|---|---|
| **Stop auto-approval** | `AUTO_APPROVE_LIMIT=0` | Every invoice goes to a person; reading and matching continue, so people still get the evidence | Any doubt about decision quality; wrong auto-approval found; exception rate suddenly low |
| **Stop using AI** | `LLM_MODE=rules` | Invoices are read by the rules reader; unreadable ones go to people | AI gateway or model problem; suspected data issue with the provider |
| **Maintenance page** | `MAINTENANCE_MODE=1` | Review app shows a "back shortly" page; health check stays up | Planned work; serious incident |
| Gateway key | Revoke in the gateway | All AI calls stop; the app falls back to rules | Key exposed |

The system **fails safe**: when something is unknown, the invoice goes to a person, never to payment.

## Rollback

1. Identify the last good image tag (each image is tagged with its git commit).
2. Redeploy that tag to the service (one command in the container service; about 5 minutes).
3. If the problem came from configuration (a limit or the model name), revert the setting instead; no redeploy needed.
4. Decisions already made are in the audit log. Run the decision report for the affected time window and send any questionable approvals to the AP Manager for re-check.
5. Write a short incident note: what happened, impact, fix, and the test case added so it cannot happen again.

## Incident playbooks

### 1. AI gateway down or slow
- **Signals:** fallback-rate alert; circuit breaker "open" in the decision log; gateway status page.
- **Impact:** low. Invoices in known layouts are still read by rules; others go to people. Nothing unsafe is approved.
- **Steps:** confirm on the gateway dashboard → tell the AP Manager that more invoices will need review → if longer than 4 hours, set `LLM_MODE=rules` so the service stops trying → switch back and watch the fallback rate return to normal.

### 2. Reading quality dropped (drift)
- **Signals:** grounding-discard or M-10 alert; review rate up for one vendor; benchmark below baseline.
- **Steps:** find the vendors affected in the decision log → get example invoices → add them (anonymized) to the golden set with correct answers → run the benchmark → fix (prompt, parser, or vendor contact) → release through the normal gates.

### 3. A wrong auto-approval is found (for example by the auditor sample)
- **Severity:** high. **Immediately** set `AUTO_APPROVE_LIMIT=0`.
- **Steps:** check whether the payment has gone out (ERP payment run) and stop or recover it with the AP Manager → find the cause from the audit record (which values were read, which rules passed) → add a test case reproducing it → fix → run all gates → Compliance approves turning auto-approval back on, starting with the pilot vendors.

### 4. Suspected payment fraud (M-9 bank-detail change)
- **Steps:** Information Security owns it → contact the vendor by phone using the number on file, **never** the one on the invoice → if fraudulent, reject with the reason, alert Treasury, and check other invoices from the same sender → if genuine, the vendor master is updated through the normal ERP process (not by InvoiceMatch).

### 5. Audit chain verification failed
- **Severity:** high (possible tampering or storage fault).
- **Steps:** preserve the store and logs; stop changes to it → compare with the write-once copy → identify the first broken record and who had access → involve Compliance and Information Security → restore from the write-once copy.

### 6. Secret exposed
- Revoke the key in the gateway or system that issued it → create a new one → update the secrets manager → restart → review the gateway's usage log for misuse in the exposure window.

## The 2 AM checklist

1. Is the service up? (`/healthz`, error rate)
2. Is it reading? (fallback rate, circuit breaker state)
3. Is it deciding safely? (exception rate in the normal band; no wrong-approval alerts)
4. Is the audit chain intact? (last nightly verification)
5. If unsure about 3: `AUTO_APPROVE_LIMIT=0`, then investigate in the morning. Nothing is lost: invoices wait for people.
