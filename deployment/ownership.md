# Operational ownership

Who runs InvoiceMatch on day one, in week one, and at month six. The goal is a clean handover: by month six, Silverbrook runs it without the FDE team.

## Day one (go-live day, pilot vendors only)

| Activity | Owner | Support |
|---|---|---|
| Deployment and smoke test | FDE engineer | Silverbrook platform team |
| Watching alerts and dashboards | FDE engineer (on call all day) | Platform team shadowing |
| Processing and reviewing pilot invoices | AP pilot users (Tom Becker + 1) | FDE engineer next to them |
| Approvals above limits | AP Manager, Finance Controller (as today) | - |
| Go / no-go to keep auto-approval on at end of day | AP Manager + Compliance | FDE lead presents the day's numbers |

## Week one (hypercare)

| Activity | Owner |
|---|---|
| Daily 15-minute stand-up: issues, exception reasons, user feedback | FDE lead with the AP Manager |
| On call (business hours, plus out-of-hours for pages) | FDE engineer primary; platform team secondary |
| Fixes and test-case additions | FDE engineers, through CI gates |
| First weekly auditor sample (50 decisions) | Internal Audit |
| Weekly one-page update to the CFO | FDE lead |

## Month six (steady state)

| Area | Owner | Notes |
|---|---|---|
| Running the service (uptime, patching, scaling, backups) | Silverbrook platform team | Using this runbook and their standard tools |
| Business process and the review queue | AP Manager | Owns exception handling and vendor follow-up |
| Rules and approval limits | Compliance (approves) + AP Manager (requests) | Changes go through code review and CI gates |
| Weekly auditor sample and quality metric | Internal Audit | Reports monthly to Compliance |
| Accuracy, drift, and test-set growth | Platform team's AI owner (trained by the FDE team) | Monthly benchmark; layout drift alerts |
| Security review, keys, gateway access | Information Security | Quarterly access review |
| Escalation path for complex issues | FDE team (advisory, contracted hours) | Ends by agreement |

## RACI for key decisions

R = responsible, A = accountable, C = consulted, I = informed.

| Decision | AP Manager | Compliance | CFO | InfoSec | Platform team | FDE team |
|---|---|---|---|---|---|---|
| Raise the auto-approval limit | R | **A** | C | I | I | C |
| Add a pilot vendor group | **A** | C | I | I | R | C |
| Change a matching rule | R | **A** | I | I | R | C |
| Change the AI model | I | C | I | C | **A** | R |
| Release a new version | I | I | I | C | **A** | R |
| Respond to a security incident | I | C | I | **A** | R | C |

## Handover checklist (before the FDE team steps back)

- [ ] Platform team has deployed and rolled back a release on their own
- [ ] On-call engineers have walked through every runbook playbook
- [ ] AI owner has run the benchmark and added a new test case unaided
- [ ] Alerts route to Silverbrook's on-call rotation
- [ ] Compliance has signed off the rules, limits, and audit-log format
- [ ] Documentation reviewed and accepted by the AP Manager and platform lead
