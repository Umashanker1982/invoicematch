# InvoiceMatch: AI invoice-to-PO matching

**Client:** Silverbrook Financial (a fictional company created for this project)
**Engagement:** Capstone 2, Full Forward Deployed Engineering (FDE) Engagement Simulation
**Author:** Umashanker

InvoiceMatch reads supplier invoices, checks them against purchase orders (POs) and contract terms, and decides whether each invoice can be approved automatically or needs a person to review it. Every decision is explained and recorded in an audit log.

> **Status:** work in progress. This README is completed in the final step.

## Repository layout

| Folder | Engagement phase | Contents |
|---|---|---|
| `discovery/` | 1. Discovery | Stakeholders, interviews, current workflow, problem statement, risks |
| `scoping/` | 2. Scoping and success metrics | Scope, SMART metrics, business case |
| `design/` | 3. Solution design | Architecture, components, technology choices, security, evaluation plan |
| `deployment/` | 4. Deployment and operations | Deployment model, IAM, secrets, observability, rollback, ownership |
| `adoption/` | 5. Adoption and change management | Training, pilot rollout, executive communication, feedback loop, demo script |
| `productization/` | 6. Productization review | Reusable components, product opportunities, platform gaps, roadmap |
| `src/invoicematch/` | Implementation | Extraction agent, matching engine, approvals, audit log |
| `data/` | Implementation | Sample invoices and purchase orders (sample data, no real company data) |
| `eval/` | Evaluation | Test set and benchmark |
| `tests/` | Evaluation | Automated tests |
| `scripts/` | Tooling | Setup and check scripts |

## Quick setup (Windows PowerShell)

```powershell
git clone https://github.com/Umashanker1982/invoicematch.git
cd invoicematch
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env      # then add your SharedLLM key to .env
python scripts/check_setup.py
python -m pytest -q
```

The AI model (Claude) is reached through the course's **SharedLLM** gateway. Without a key, the project still runs using deterministic rules.
