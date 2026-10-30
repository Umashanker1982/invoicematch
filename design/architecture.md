# Architecture

## Future state: the same process, with InvoiceMatch

Compare with [../discovery/current_state_workflow.md](../discovery/current_state_workflow.md). People now handle only the invoices that need judgment, with the evidence already assembled.

```mermaid
flowchart TD
    V([Vendor]) -->|PDF or e-invoice| ING[Ingestion<br/>AP inbox + e-invoice portal]
    ING --> PAR[Document parser<br/>text + bank details read with fixed patterns<br/>bank details removed from AI text]
    PAR --> EXT[Extraction agent<br/>Claude via the approved AI gateway<br/>returns typed InvoiceFields]
    EXT --> GRD{Grounding and<br/>validation}
    GRD -- AI unavailable or invalid --> RUL[Rules reader<br/>fallback]
    RUL --> MAT
    GRD -- valid --> MAT[Matching engine<br/>checks M-1..M-10 against<br/>PO, contract, history]
    ERP[(ERP<br/>POs, vendors, contracts,<br/>invoice history)] -. read only .-> MAT
    MAT --> APR{Approval routing<br/>A-1..A-4}
    APR -- "all checks pass, up to $10,000" --> AUTO[Auto-approve]
    APR -- "all pass, above $10,000" --> APPQ[Approver queue<br/>AP Manager / Controller / CFO]
    APR -- "any check fails" --> REVQ[Human review queue<br/>side-by-side evidence]
    APR -- "bank details changed" --> SEC[Security review]
    AUTO --> STAT[Set approval status<br/>the one permitted ERP write]
    APPQ --> STAT
    REVQ --> STAT
    SEC --> STAT
    STAT --> ERP
    STAT --> PAY[Normal ERP payment run<br/>unchanged]
    EXT -.-> AUD[(Audit log<br/>append-only, hash-chained)]
    MAT -.-> AUD
    APR -.-> AUD
    STAT -.-> AUD

    classDef ai fill:#E2EBF2,stroke:#2E5674,color:#000
    classDef people fill:#F7EBD3,stroke:#A0650F,color:#000
    classDef store fill:#E3EFE8,stroke:#1E5B45,color:#000
    class EXT ai
    class APPQ,REVQ,SEC people
    class ERP,AUD store
```

Blue: the only AI step. Amber: where people decide. Green: systems of record.

## Production deployment inside Silverbrook's cloud account

Everything runs in Silverbrook's own cloud account and region (non-negotiable N-1). The only traffic that leaves the private network is the AI call, which carries invoice text with bank details removed and goes through the company-approved AI gateway.

```mermaid
flowchart LR
    subgraph VPC["Silverbrook cloud account, US region, private network"]
        direction TB
        INBOX[AP mailbox and<br/>e-invoice portal connector] --> Q[(Intake queue)]
        Q --> SVC[InvoiceMatch service<br/>containers, 2+ instances]
        SVC --> DB[(PostgreSQL<br/>review queue, decisions)]
        SVC --> LOG[(Audit store<br/>write-once, 7-year retention)]
        SVC --> OBJ[(Encrypted document store)]
        UI[Review web app<br/>behind company SSO + MFA] --> SVC
        SVC -->|read-only + approval-status API| ERPAPI[ERP integration layer]
        SVC --> MON[Logs, metrics, alerts]
        SEC[(Secrets manager)] -.-> SVC
    end
    SVC -->|HTTPS, redacted text only| GW[Approved AI gateway<br/>metering, logging, spend limits]
    GW --> LLM[Claude model]
    USERS([AP team, approvers,<br/>Compliance, Audit]) --> UI
```

## What this repository implements

| Production component | This repository | Status |
|---|---|---|
| Ingestion (mailbox, e-invoice portal) | Sample invoice text files in `data/invoices/` and `data/holdout/` | Simulated |
| Document parser | [`src/invoicematch/parser.py`](../src/invoicematch/parser.py) | Implemented (text input; PDF-to-text in production) |
| Extraction agent | [`src/invoicematch/extraction.py`](../src/invoicematch/extraction.py), [`llm.py`](../src/invoicematch/llm.py), [`models.py`](../src/invoicematch/models.py) | Implemented, live through SharedLLM |
| Matching engine | [`src/invoicematch/matching.py`](../src/invoicematch/matching.py) | Implemented |
| Approval workflow | [`src/invoicematch/approvals.py`](../src/invoicematch/approvals.py), [`pipeline.py`](../src/invoicematch/pipeline.py) | Implemented, with role checks |
| Human review UI | [`web/`](../web) | Implemented (demo login: choose a persona) |
| Audit log | [`src/invoicematch/audit.py`](../src/invoicematch/audit.py) | Implemented (hash chain; in-memory or file) |
| ERP update | [`src/invoicematch/erp.py`](../src/invoicematch/erp.py) `set_approval_status()` | Simulated with a demo ERP |
| AI gateway | SharedLLM (the course gateway), Anthropic Messages endpoint | Live |

## Request flow for one invoice

1. **Parse**: normalize the text; read the bank account and routing number with fixed patterns; produce a copy of the text with them removed.
2. **Read**: send only the redacted text to Claude through the gateway, wrapped in `<invoice>` tags and marked as untrusted data. Ask for JSON matching `InvoiceFields`.
3. **Validate and ground**: validate the JSON against the schema; normalize dates, PO numbers, and currency; discard any invoice number, PO number, or total that is not printed in the text. If the AI fails or answers invalidly, the rules reader takes over.
4. **Match**: run checks M-1 to M-10 against the ERP data.
5. **Decide**: apply approval rules A-1 to A-4 with the configured limits.
6. **Record**: write the decision to the audit log; set the ERP approval status (approved, or on hold for a person).
7. **Human step** (if needed): an authorized role approves or rejects with a reason; logged; ERP status updated.
