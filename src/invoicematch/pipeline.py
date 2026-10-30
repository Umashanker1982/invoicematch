"""InvoiceMatch pipeline: extract -> match -> decide -> audit -> approve or queue -> ERP status.

`InvoiceMatch` holds one isolated workspace: a demo ERP copy, a review queue, and an audit log.
The benchmark creates a fresh one per invoice; the web app creates one per visitor.
"""
from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel

from invoicematch.approvals import ROUTE_ROLES, Decision, decide
from invoicematch.audit import AuditLog
from invoicematch.config import Settings, load_settings
from invoicematch.erp import DemoERP
from invoicematch.extraction import extract_invoice
from invoicematch.llm import GatewayClient
from invoicematch.matching import MatchResult, match_invoice
from invoicematch.models import ExtractionResult

ROLE_LABELS = {"ap_specialist": "AP Specialist", "ap_manager": "AP Manager", "finance_controller": "Finance Controller",
               "cfo": "CFO", "security": "Information Security"}


class ApprovalError(Exception):
    """Raised when an action is not allowed (wrong role, missing reason, already decided)."""


class ProcessedInvoice(BaseModel):
    ref: str
    extraction: ExtractionResult
    match: MatchResult
    decision: Decision
    status: Literal["approved", "pending", "rejected"]
    resolved_by: str | None = None
    resolution_note: str | None = None

    @property
    def summary(self) -> str:
        f = self.extraction.fields
        total = f"${f.total_amount:,.2f}" if f.total_amount is not None else "unreadable total"
        return f"{self.ref} {self.vendor_name} {f.invoice_number or '?'} {total}"

    @property
    def vendor_name(self) -> str:
        """The vendor master name when the vendor was recognised, otherwise the name as printed."""
        return self.match.vendor_master_name or self.extraction.fields.vendor or "unknown vendor"


class InvoiceMatch:
    def __init__(self, settings: Settings | None = None, client: GatewayClient | None = None,
                 audit_path: Path | None = None):
        self.settings = settings or load_settings()
        self.client = client or GatewayClient(self.settings)
        self.erp = DemoERP()
        self.audit = AuditLog(audit_path)
        self.invoices: dict[str, ProcessedInvoice] = {}

    # ------------------------------------------------------------------ processing
    def process(self, text: str, mode: str | None = None) -> ProcessedInvoice:
        ref = f"IM-{len(self.invoices) + 1:04d}"
        ex = extract_invoice(text, mode=mode, settings=self.settings, client=self.client)
        m = match_invoice(ex, self.erp)
        d = decide(m, ex.fields.total_amount, self.settings)
        item = ProcessedInvoice(ref=ref, extraction=ex, match=m, decision=d,
                                status="approved" if d.route == "auto_approve" else "pending")
        self.invoices[ref] = item

        self.audit.write(action="decided", actor="InvoiceMatch", invoice_ref=item.summary, details={
            "read_by": ex.method, "fallback_reason": ex.fallback_reason,
            "ai": ex.llm.model_dump() if ex.llm else None,
            "vendor_id": m.vendor_id, "po_number": m.po_number, "route": d.route, "rule_ids": d.rule_ids,
            "reasons": d.reasons, "checks": {c.rule: c.status for c in m.checks},
            "extraction_issues": ex.issues,
        })
        self._erp_status(item, "approved" if item.status == "approved" else "on_hold",
                         actor="InvoiceMatch (rule A-1)" if item.status == "approved" else "InvoiceMatch")
        return item

    def _erp_status(self, item: ProcessedInvoice, status: str, actor: str) -> None:
        f = item.extraction.fields
        self.erp.set_approval_status(vendor_id=item.match.vendor_id, invoice_number=f.invoice_number,
                                     po_number=f.po_number, invoice_date=f.invoice_date, total=f.total_amount,
                                     lines=[l.model_dump() for l in f.lines], status=status, actor=actor)
        self.audit.write(action="erp_status_set", actor=actor, invoice_ref=item.summary, details={"status": status})

    # ------------------------------------------------------------------ human decisions
    def pending(self) -> list[ProcessedInvoice]:
        return [i for i in self.invoices.values() if i.status == "pending"]

    def _check_allowed(self, item: ProcessedInvoice, role: str, note: str, action: str) -> None:
        if item.status != "pending":
            raise ApprovalError(f"{item.ref} is already {item.status}.")
        allowed = set(ROUTE_ROLES[item.decision.route])
        if item.decision.controller_signoff:
            allowed &= {"finance_controller", "cfo"}
        if role not in allowed:
            names = ", ".join(ROLE_LABELS[r] for r in sorted(allowed))
            who = ROLE_LABELS.get(role, role)
            article = "An" if who[:1].upper() in "AEIOU" else "A"
            raise ApprovalError(f"{article} {who} cannot {action} {item.ref} ({item.decision.label}). Allowed: {names}.")
        needs_reason = action == "reject" or item.decision.route in {"review", "security_review"}
        if needs_reason and len(note.strip()) < 10:
            raise ApprovalError("A written reason of at least 10 characters is required for the audit log.")

    def approve(self, ref: str, *, actor: str, role: str, note: str = "") -> ProcessedInvoice:
        item = self._get(ref)
        self._check_allowed(item, role, note, "approve")
        item.status, item.resolved_by, item.resolution_note = "approved", f"{actor} ({ROLE_LABELS[role]})", note or None
        override = item.decision.route in {"review", "security_review"}
        self.audit.write(action="override_approved" if override else "approved", actor=item.resolved_by,
                         invoice_ref=item.summary, details={"route": item.decision.route,
                                                            "failed_rules": item.decision.failed_rules, "note": note})
        self._erp_status(item, "approved", actor=item.resolved_by)
        return item

    def reject(self, ref: str, *, actor: str, role: str, note: str) -> ProcessedInvoice:
        item = self._get(ref)
        self._check_allowed(item, role, note, "reject")
        item.status, item.resolved_by, item.resolution_note = "rejected", f"{actor} ({ROLE_LABELS[role]})", note
        self.audit.write(action="rejected", actor=item.resolved_by, invoice_ref=item.summary,
                         details={"route": item.decision.route, "note": note})
        self._erp_status(item, "rejected", actor=item.resolved_by)
        return item

    def _get(self, ref: str) -> ProcessedInvoice:
        if ref not in self.invoices:
            raise ApprovalError(f"No invoice {ref} in this workspace.")
        return self.invoices[ref]
