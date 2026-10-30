# Phase 1: Discovery

**Goal:** understand the people, the process, and the constraints at Silverbrook Financial *before* designing anything.

Silverbrook Financial is a fictional mid-sized financial services company created for this project. All names, numbers, and quotes are sample data.

## What we did
- Mapped **8 stakeholders** by influence and concern → [stakeholder_map.md](stakeholder_map.md)
- Ran **6 structured interviews** using one template → [interview_template.md](interview_template.md), [interview_notes.md](interview_notes.md)
- Shadowed the Accounts Payable (AP) team for two days and drew the **current workflow** → [current_state_workflow.md](current_state_workflow.md)
- Pulled 3 months of invoice data from the ERP (the company's finance system) to get **baseline numbers** → used in [../scoping/business_case.md](../scoping/business_case.md)
- Wrote the **problem as a measurable business outcome** → [problem_statement.md](problem_statement.md)
- Listed **risks, constraints, and non-negotiables** → [risks_and_constraints.md](risks_and_constraints.md)

## Five things we learned

1. **The team is at full capacity.** Six AP specialists spend about **910 hours a month** on 4,000 invoices. That is all of their time. Month-end means overtime, and next year's volume is expected to grow 15%.
2. **Most of the effort goes to a minority of invoices.** Only 22% of PO-backed invoices have a problem, but they take **55% of the time**, mostly spent chasing Procurement by email.
3. **Money leaks today.** Last year's audit found **$210,000** in duplicate payments and overpayments. Only $90,000 was recovered.
4. **Trust depends on explanations, not accuracy alone.** Compliance and the AP team both said they will only accept automation if every decision shows *which rule* was applied and *what evidence* was used.
5. **People fear for their jobs.** AP specialists and Procurement worry the tool will be used to judge or replace them. Adoption depends on positioning it as an assistant that removes the boring work.

## How discovery shaped the scope
| Finding | Scope decision (see [../scoping/scope.md](../scoping/scope.md)) |
|---|---|
| Exceptions eat most of the time | The system must *explain* every exception and pre-assemble the evidence, not just flag it |
| Compliance needs auditability | Every decision is written to an audit log with the rule ids and evidence |
| Existing approval limits are non-negotiable | The system only auto-approves matched invoices up to **$10,000**; above that, the existing approval chain applies |
| Fear of replacement | Release 1 removes the routine work and keeps people in charge of every non-routine decision |
| Scanned paper invoices are only 9% of volume and are hard | Release 1 covers digital invoices only; scanned invoices come later |
