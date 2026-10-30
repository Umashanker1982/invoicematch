# Interview notes (synthesized)

Six interviews were held in week 1, using [interview_template.md](interview_template.md). All people and quotes are fictional sample data. Answers are numbered by template question (Q1–Q7).

---

## 1. Diana Reyes, CFO (executive sponsor)

| Q | Synthesized answer |
|---|---|
| Q1 Role | Owns the finance budget; signs invoices above $100,000 under the Delegation of Authority. |
| Q2 Breaks | AP cost grows with volume. A 15% volume increase next year would need one more hire. Late-payment fees and missed early-payment discounts show up in every quarter's report. |
| Q3 Trust data | Weekly numbers: invoices processed, hours saved, errors caught. "Show me money, not model accuracy." |
| Q4 Delegate | If Compliance and Internal Audit sign off, and the savings are measured, not estimated. |
| Q5 Mistakes | A wrong payment is recoverable but embarrassing. A pattern of errors would end the project. |
| Q6 Who else | Marcus (Compliance), Priya (AP), Grace (Internal Audit). |
| Q7 Success in 3 months | A pilot showing the team handles more invoices with the same people, and a clear yes/no for full rollout. |

> "I don't need the cleverest AI. I need the AP team to stop working weekends at month-end."

## 2. Marcus Oyelaran, Chief Compliance Officer

| Q | Synthesized answer |
|---|---|
| Q1 Role | Owns SOX controls over payments and the Delegation of Authority (who can approve what amount). |
| Q2 Breaks | Approval evidence is scattered across emails. Reconstructing *why* an invoice was paid takes hours during an audit. |
| Q3 Trust data | For every decision: the invoice, the PO, the contract terms used, the rule applied, and who or what approved it. |
| Q4 Delegate | Deterministic, written rules for approval. "The AI can read the invoice. It cannot decide to pay." Existing approval limits must not change. |
| Q5 Mistakes | Each one must be traceable to its cause within a day, and fixable by changing a rule, not by retraining something. |
| Q6 Who else | Kevin (InfoSec), Grace (Internal Audit). |
| Q7 Success in 3 months | Zero control findings in the pilot and a complete audit trail for 100% of decisions. |

> "If I can't explain a payment to the auditor in two minutes, it's a control failure, whoever made it."

## 3. Priya Natarajan, AP Operations Manager (process owner)

| Q | Synthesized answer |
|---|---|
| Q1 Role | Runs the 6-person AP team; approves invoices from $10,000 to $25,000; handles escalations. |
| Q2 Breaks | Manual typing from PDFs into the ERP; searching for contract prices; waiting on Procurement to fix POs (4.5 days on average); duplicates caught only "by memory". |
| Q3 Trust data | Side-by-side view: what the invoice says, what the PO says, and the difference. |
| Q4 Delegate | Start with low-value, clean invoices from regular vendors, with a weekly spot check. |
| Q5 Mistakes | Her team fixes it, so errors must be rare and *visible early*, not discovered at payment run. |
| Q6 Who else | Tom (senior specialist), Lena (Procurement). |
| Q7 Success in 3 months | Month-end closed without overtime; exception backlog under 2 days. |

> "My people spend half their day copying numbers from one screen to another. That's not what I hired accountants for."

## 4. Tom Becker, Senior AP Specialist

| Q | Synthesized answer |
|---|---|
| Q1 Role | Processes about 650 invoices a month; trains new staff; knows the vendor quirks. |
| Q2 Breaks | Vendors write PO numbers in different places ("PO", "Order ref", "Your ref"); dates in different formats; freight added without warning; the same invoice sent twice by email and by post. |
| Q3 Trust data | To see where each extracted value came from, and to be able to correct it. |
| Q4 Delegate | If the tool shows its work, and he can overrule it. |
| Q5 Mistakes | "Right now, if I make a mistake, I get blamed. I don't want to be blamed for the robot's mistakes either." |
| Q6 Who else | The other specialists, especially the two newest hires. |
| Q7 Success in 3 months | No more copy-typing for regular vendors; time to work on the difficult cases properly. |

> "Is this going to replace me? Honestly, if it takes the copy-typing, I'm fine. If it takes my job, I'm not."

## 5. Lena Fischer, Procurement Lead

| Q | Synthesized answer |
|---|---|
| Q1 Role | Her buyers create the purchase orders (POs) and negotiate contract prices. |
| Q2 Breaks | AP emails "your PO is wrong" without saying what is wrong. Many mismatches are actually vendor errors, but Procurement gets the blame. |
| Q3 Trust data | The exact difference (line, quantity, price, amount) and whether the contract allows it (for example, agreed freight). |
| Q4 Delegate | If mismatch messages are factual and routed to the right buyer automatically. |
| Q5 Mistakes | A wrongly blocked invoice delays a vendor payment and damages the vendor relationship. |
| Q6 Who else | Two high-volume vendors' account managers (out of scope for interviews; consulted in the pilot). |
| Q7 Success in 3 months | Fewer back-and-forth emails; mismatches resolved in one round. |

> "Tell me *which* line is off and by how much. Don't just tell me it doesn't match."

## 6. Kevin Osei (Information Security) and Raj Malhotra (ERP and Integration), joint session

| Q | Synthesized answer |
|---|---|
| Q1 Role | Kevin approves new systems that handle financial data. Raj owns the ERP and its integrations. |
| Q2 Breaks | Shadow tools: staff paste invoice data into personal AI chat tools to save time. Nobody can see or control this. |
| Q3 Trust data | Data-flow diagram; where data is stored; which outside services see it; how keys are managed. |
| Q4 Delegate | Runs in the company's cloud account (same region); calls to the AI model go through an approved, logged gateway; no data used for model training; read-only ERP access plus one approved API to set the approval status. |
| Q5 Mistakes | Integration failures must never corrupt ERP data; the system must fail safe (send to a human). |
| Q6 Who else | Grace (Internal Audit) for the audit-log format. |
| Q7 Success in 3 months | Security review passed; no new ERP incidents. |

> Kevin: "People are already pasting invoices into chatbots. A controlled tool is *safer* than what we have today."

---

## Themes across all interviews

| Theme | Heard from | What it means for the solution |
|---|---|---|
| **Effort**: copy-typing and searching | Priya, Tom, Diana | Extract invoice fields automatically; pre-fetch the PO and contract |
| **Exceptions**: unclear, slow to resolve | Priya, Lena, Tom | Explain each mismatch precisely (line, field, amount, rule) and route it to the right person |
| **Control**: approvals and audit | Marcus, Grace, Diana | Deterministic rules decide; AI only reads; full audit trail; existing approval limits kept |
| **Trust**: show the work | Tom, Marcus, Priya | Side-by-side evidence; people can overrule; every overrule is logged |
| **People**: fear of replacement or blame | Tom, Lena | Position as an assistant; neutral wording; no layoffs; staff own the hard cases |
| **Security**: data and integration | Kevin, Raj | Company cloud; approved gateway; bank details removed before AI calls; read-only ERP |
