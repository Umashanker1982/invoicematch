# Product opportunities

What the engagement revealed that could become product, for Silverbrook and for similar finance customers.

## 1. The core product: AI-assisted accounts-payable matching

**Who:** mid-sized finance and services companies with 2,000–20,000 PO-backed invoices a month, an existing ERP, and strict approval rules.
**Why they buy:** the same pains appeared in every interview: full-capacity AP teams, slow exceptions, leakage through duplicates, scattered audit evidence.
**What makes it different:** deployed in the customer's own cloud; AI only reads; written, auditable rules decide; measured accuracy and safety on the customer's own documents before go-live.

## 2. Adjacent opportunities found in discovery

| Opportunity | Evidence from this engagement | Value | Effort | Priority |
|---|---|---|---|---|
| **Vendor bank-change verification** | M-9 caught "new bank account" invoices in both test sets; InfoSec called it the most expensive fraud | High: prevents large single losses | Low: the check exists; add a verification workflow | **1** |
| **3-way match (goods receipts)** | Out of scope for release 1; asked for by the AP Manager | High: catches "billed but not delivered" | Medium: needs reliable receiving data | **2** |
| **Contract price-drift analytics** | M-4 failures show vendors invoicing above contract (e.g. +14%, +9%) | Medium–high: negotiation leverage for Procurement | Low: data already in the decision log | **3** |
| **Early-payment discount capture** | Faster approval makes "2% in 10 days" terms reachable; $38,000 in late fees last year | Medium: working-capital gain | Low–medium | 4 |
| **Scanned invoices (OCR)** | 9% of volume today | Medium | Medium: accuracy study per layout | 5 |
| **Non-PO invoices (GL coding suggestions)** | 15% of volume; different rules | Medium | High: needs coding rules per company | 6 |
| **Shadow-AI replacement** | Staff pasting invoices into personal chatbots (InfoSec interview) | Risk reduction | Low: a governed alternative already exists | Positioning |

## 3. Packaging ideas

| Offer | Contents | For whom |
|---|---|---|
| **Pilot package** (fixed price, 12 weeks) | Discovery templates, sample data, benchmark harness, shadow-mode pilot, executive report | New customers who need proof first |
| **Product license + deployment** | Container image, connectors, review UI, runbooks, rule configuration | Customers who passed the pilot gates |
| **Accuracy and audit service** | Monthly benchmark, drift review, golden-set growth, audit-sample tooling | Regulated customers who must show ongoing control |

## 4. What we would need to learn first

- Willingness to pay: per-invoice pricing vs per-seat vs platform fee (interview 5 more finance leaders).
- ERP mix in the target market (determines the first connectors).
- Whether customers accept an external AI gateway, or require inference inside their cloud account (affects the deployment template).
