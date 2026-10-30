# Components

The six components the brief asks for, plus the AI gateway. Each has one job, so each can be tested, owned, and replaced on its own.

## 1. Document parser
| | |
|---|---|
| **Job** | Turn an incoming document into clean text; read bank details; protect sensitive data before AI |
| **Input** | Invoice document (production: PDF or e-invoice XML; this repo: text) |
| **Output** | Full text (for rules and grounding), redacted text (for AI), bank account and routing number, "damaged" flag |
| **Key rule** | Bank details are read with fixed patterns and **removed from the AI's copy** (InfoSec N-8) |
| **Code** | [`parser.py`](../src/invoicematch/parser.py) |
| **Production** | Add PDF text extraction (for example pdfplumber) and e-invoice XML parsing; scanned paper (OCR) in release 2 |

## 2. Extraction agent
| | |
|---|---|
| **Job** | Read one invoice and return typed fields: vendor, invoice number, date, PO number, currency, lines, subtotal, tax, freight, total |
| **Input** | Redacted invoice text |
| **Output** | `ExtractionResult`: the `InvoiceFields`, how it was read (Claude or rules), AI tokens/cost/latency, issues |
| **Key rules** | Typed schema validated with pydantic; grounding check; deterministic defaults; rules reader as fallback; no tools, cannot act |
| **Code** | [`extraction.py`](../src/invoicematch/extraction.py), [`models.py`](../src/invoicematch/models.py), [`llm.py`](../src/invoicematch/llm.py) |
| **Pattern** | Same as the brief's example: an agent with instructions and a typed `output_type` (`InvoiceFields`), awaited with `extract_invoice_async(text)` |

## 3. Matching engine
| | |
|---|---|
| **Job** | Compare the invoice with the PO, the contract, and invoice history |
| **Input** | Extraction result; ERP data (read-only) |
| **Output** | Ten check results (pass, fail, or skipped), each with a factual message and evidence; line-by-line comparison |
| **Key rules** | M-1..M-10 from [../scoping/scope.md](../scoping/scope.md); deterministic; neutral wording ("which line, by how much") |
| **Code** | [`matching.py`](../src/invoicematch/matching.py), demo ERP in [`erp.py`](../src/invoicematch/erp.py) |

## 4. Approval workflow
| | |
|---|---|
| **Job** | Turn check results into one route, and enforce who may approve what |
| **Routes** | Auto-approve (A-1), AP Manager (A-2), Finance Controller or CFO (A-3), review or security review (A-4) |
| **Key rules** | Limits come from configuration (Delegation of Authority); high-value mismatches need the Finance Controller; bank changes only Security; overrides and rejections need a written reason |
| **Code** | [`approvals.py`](../src/invoicematch/approvals.py), [`pipeline.py`](../src/invoicematch/pipeline.py) |

## 5. Human review UI
| | |
|---|---|
| **Job** | Show reviewers and approvers exactly why an invoice is waiting, with the evidence side by side, and let them act |
| **Features** | Stamp and reasons; invoice vs PO vs contract table; who can act; approve or reject with a reason; audit view |
| **Code** | [`web/`](../web) (FastAPI + plain JavaScript) |
| **Production** | Company SSO + MFA instead of persona selection; role from the identity provider, never chosen by the user |

## 6. Audit log
| | |
|---|---|
| **Job** | Record every decision and human action with inputs, rule ids, evidence, actor, and reason |
| **Key rule** | Append-only; each record holds the hash of the previous one, so edits or deletions are detected by `verify()` |
| **Code** | [`audit.py`](../src/invoicematch/audit.py) |
| **Production** | Write-once object storage (WORM) with 7-year retention; nightly chain verification; Internal Audit has read access |

## 7. AI gateway (SharedLLM)
| | |
|---|---|
| **Job** | One controlled path to the AI model: metering, logging, spend limits, key management |
| **How used** | Anthropic Messages endpoint `https://api.sharedllm.com/anthropic` with header `X-SharedLLM-Key`. The provider key lives in the gateway (bring-your-own-key), not in the app. |
| **Code** | [`llm.py`](../src/invoicematch/llm.py) |
| **Production** | Silverbrook's approved gateway, or Claude on a cloud provider's managed service inside the same cloud account |
