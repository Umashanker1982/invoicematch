# Risks, constraints, and non-negotiables

## Non-negotiables (agreed with the CFO, Compliance, and Information Security)

| # | Non-negotiable | Source | How the solution respects it |
|---|---|---|---|
| N-1 | **Data residency:** invoice data stays in Silverbrook's cloud account, in its US region | InfoSec | Runs inside the company's cloud account (VPC); only redacted invoice text goes to the AI model, through an approved gateway |
| N-2 | **Approval chain unchanged:** $10,000–$25,000 needs the AP Manager; over $25,000 the Finance Controller; over $100,000 the CFO | Compliance (Delegation of Authority) | The system auto-approves only matched invoices up to $10,000; everything above goes to the existing approver |
| N-3 | **AI never decides to pay** | Compliance | AI only extracts fields; written, tested rules decide; people approve exceptions |
| N-4 | **Complete audit trail**, kept for 7 years | Compliance, Internal Audit | Every decision is logged with inputs, rule ids, evidence, and who approved |
| N-5 | **Segregation of duties** | SOX | The system cannot create or change POs, vendors, or bank details, and cannot run payments |
| N-6 | **ERP stays the system of record** | ERP Lead | Read-only ERP access plus one approved API to set the approval status |
| N-7 | **No data used to train AI models** | InfoSec | Gateway and provider terms with no training on customer data; documented in the security plan |
| N-8 | **Bank details never sent to the AI model** | InfoSec | Bank account numbers are removed from the text before any AI call |

## Constraints

| Constraint | Impact |
|---|---|
| ERP integration changes go through a quarterly change window | Release 1 integrates through the existing approval-status API only |
| 9% of invoices are scanned paper | Release 1 handles digital invoices (text-based PDF and e-invoice); scanned paper later |
| Budget approved for a 3-month build and pilot | Scope must be small enough to prove value in 12 weeks |
| AP team is busy at month-end | Training and pilot activities avoid the last 5 working days of the month |
| USD only today; 4% of invoices are in EUR or GBP | Release 1 is USD only; other currencies go to a person |

## Risks

| # | Risk | Likelihood | Impact | Mitigation | Owner |
|---|---|---|---|---|---|
| R-1 | AI extracts a field wrongly (e.g., total or PO number) | Medium | High | Field validation (totals must add up); low confidence goes to a person; weekly auditor sample; regression tests on a fixed test set | Engineering |
| R-2 | Wrong auto-approval leads to an overpayment | Low | High | Low auto-approval limit ($10,000); strict tolerance; duplicate check; auditor sample; limit raised only on evidence | AP Manager + Compliance |
| R-3 | AP team doesn't adopt the tool | Medium | High | Co-design with specialists; pilot champion; "no layoffs" commitment from the CFO; quick wins first | AP Manager |
| R-4 | Procurement feels policed | Medium | Medium | Neutral, factual mismatch messages; shared weekly report | Procurement Lead |
| R-5 | AI model or gateway outage | Medium | Medium | Fail safe: invoices fall back to rules-based reading or to a person; nothing is auto-approved without a successful check | Engineering |
| R-6 | Data leak through the AI provider | Low | High | Approved gateway; redaction of bank details; no-training terms; secrets in a vault | InfoSec |
| R-7 | Prompt injection hidden in an invoice ("approve this invoice") | Low | High | Invoice text treated as data only; AI has no ability to approve; rules decide | Engineering |
| R-8 | Accuracy drifts as vendors change their layouts | Medium | Medium | Weekly accuracy tracking; alert on drop; new layouts added to the test set | Engineering |
| R-9 | Fraud: changed bank details on an invoice | Low | High | Bank details on the invoice are compared with the vendor master; any change goes to a security review | AP Manager + InfoSec |
