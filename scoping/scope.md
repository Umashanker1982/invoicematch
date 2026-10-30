# Phase 2: Scope for release 1

Release 1 is built and piloted in **12 weeks**. It is scoped tightly around the biggest, safest win found in discovery: **routine, PO-backed digital invoices**.

## In scope

| Area | Release 1 includes |
|---|---|
| **Invoices** | PO-backed supplier invoices, in **digital form** (text-based PDF or e-invoice), in **USD** |
| **Reading** | Extract vendor, invoice number, invoice date, PO number, currency, line items, subtotal, tax, extra charges, and total |
| **Matching** | Compare each invoice with its **purchase order (PO)** and the vendor's **contract terms** (agreed unit prices and allowed charges) |
| **Safety checks** | Duplicate detection; bank-detail change detection; arithmetic checks |
| **Decision** | Auto-approve, send for approval, or send for review, always with the rule ids and a plain-language reason |
| **Human review** | A review queue showing invoice vs PO vs contract side by side; reviewers approve, reject, or correct |
| **Audit** | Every decision, override, and approval logged with evidence |
| **ERP update** | Set the invoice's approval status through the ERP's existing API (simulated in this project) |
| **Reporting** | A metrics view for the five success metrics |

## Out of scope (and when it could come)

| Not in release 1 | Why | When |
|---|---|---|
| Scanned paper invoices (9% of volume) | Needs image reading (OCR) and a separate accuracy study | Release 2 |
| Goods-receipt matching ("3-way match") | Receiving data is not reliable in the ERP yet | Release 2 |
| Non-PO invoices (utilities, legal fees; 15%) | No PO to match against; different approval rules | Release 3 |
| Non-USD invoices (4%) | Exchange-rate rules not agreed yet | Release 2 |
| Credit notes | Low volume; different accounting treatment | Release 3 |
| Creating POs, changing vendor or bank data, running payments | **Never**, by design: segregation of duties | Not planned |
| Emailing vendors automatically | Procurement wants to keep the vendor relationship | To be discussed after the pilot |

Invoices outside the scope are not rejected. They go to a person exactly as today.

## Decision rules agreed in discovery

The rules below were agreed with Compliance and the AP Manager. **They are written, tested code. The AI does not decide.** Rule ids appear in every decision and in the audit log.

### Matching checks

| Rule | Check | If it fails |
|---|---|---|
| **M-1** | The PO exists and is open | Review: "PO not found or closed" |
| **M-2** | The vendor on the invoice is the PO's vendor | Review |
| **M-3** | Invoiced quantities do not exceed what was ordered and not yet invoiced | Review |
| **M-4** | Unit prices match the contract price (1% tolerance for rounding) | Review |
| **M-5** | Extra charges (e.g., freight) appear only if the contract allows them, up to the agreed cap | Review |
| **M-6** | Lines add up: lines + tax + allowed charges = invoice total (±$1.00) | Review |
| **M-7** | Not a duplicate: same vendor and invoice number, or same vendor, PO, and total within 14 days | Review: "possible duplicate" |
| **M-8** | Currency is USD | Review (out of scope for release 1) |
| **M-9** | Bank details on the invoice match the vendor master | **Security review** (possible fraud) |
| **M-10** | All required fields were read, with enough confidence | Review: "could not read invoice reliably" |

### Approval routing (Delegation of Authority, unchanged)

| Rule | Situation | Route |
|---|---|---|
| **A-1** | All checks pass and total **≤ $10,000** | **Auto-approve** (no human touch) |
| **A-2** | All checks pass and total **$10,000.01 – $25,000** | AP Manager, one-click approval |
| **A-3** | All checks pass and total **over $25,000** | Finance Controller (CFO over $100,000) |
| **A-4** | Any check fails | Human review queue with reasons. **High-value mismatches (over $25,000) also need the Finance Controller's sign-off.** |

The auto-approval limit of $10,000 is deliberately low. It is raised only when the weekly auditor sample shows at least 98% agreement for 8 weeks in a row, and only with Compliance's approval.

## Assumptions

- About **3,400 PO-backed invoices a month** (see [business_case.md](business_case.md)).
- The ERP's approval-status API is available to the project (confirmed by the ERP Lead).
- The AI model is reached through the company-approved gateway (SharedLLM in this project).
- Contract prices are available in a structured list for the top vendors. Vendors without one go to review under M-4.
