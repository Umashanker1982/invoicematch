# Current-state workflow (today, before InvoiceMatch)

Observed by shadowing the AP team for two days and confirmed with the AP Manager. Numbers come from 3 months of ERP data (see [../scoping/business_case.md](../scoping/business_case.md)).

## Flow and handoffs

```mermaid
flowchart TD
    V([Vendor]) -->|PDF by email, sometimes paper by post| INBOX[Shared AP inbox]
    INBOX --> A1["AP specialist opens the PDF<br/>and types the fields into the ERP<br/>(vendor, invoice no., date, lines, total, PO no.)"]
    A1 --> A2[Looks up the PO in the ERP]
    A2 --> A3[Finds the contract prices<br/>in the contract folder]
    A3 --> A4{Do invoice, PO,<br/>and contract match?}
    A4 -- "No (22%)" --> P1["Emails Procurement:<br/>'PO doesn't match'"]
    P1 --> P2[Buyer checks with the vendor]
    P2 -->|"avg 4.5 days, often 2-3 email rounds"| A4
    A4 -- Yes --> L{Invoice amount?}
    L -- "up to $10,000" --> AP[AP specialist approves]
    L -- "$10,000 to $25,000" --> M1[Email to AP Manager] --> AP2[Manager approves]
    L -- "over $25,000" --> M2[Email to Finance Controller<br/>or CFO above $100,000] --> AP3[Approver signs]
    AP --> PAY[Payment run in the ERP]
    AP2 --> PAY
    AP3 --> PAY
    PAY --> ARCH[Evidence left in emails<br/>and personal folders]

    classDef pain fill:#fde2e1,stroke:#c0392b,color:#000
    class A1,A3,P1,P2,ARCH pain
```

Red boxes are the main pain points.

## Data that moves between people

| From | To | What | How | Problem |
|---|---|---|---|---|
| Vendor | AP inbox | Invoice | PDF by email (82%), scanned paper (9%), e-invoice portal (9%) | Formats differ for every vendor |
| AP specialist | ERP | Invoice fields | Manual typing | Typing errors; about 8 minutes per invoice |
| Contract folder | AP specialist | Agreed prices and terms | Manual search | Often outdated copies; slow |
| AP specialist | Procurement | Mismatch question | Email | Vague; no exact difference stated |
| Procurement | Vendor | Correction request | Email or phone | Slow; 4.5 days on average |
| AP | Approvers | Approval request | Email | Evidence scattered; hard to audit |

## Measured pain points

| Pain point | Measurement (3-month ERP sample) |
|---|---|
| Manual typing and lookup | ~8 minutes per clean PO invoice |
| Exceptions | 22% of PO invoices; ~35 minutes of total handling each; 4.5 days to resolve |
| Duplicates and overpayments | $210,000 found by last year's audit; $90,000 recovered |
| Late payments | $38,000 in late-payment fees last year |
| Month-end backlog | Up to 600 invoices waiting; regular overtime |
| Audit evidence | 2–3 hours to rebuild the approval trail for one sampled invoice |
