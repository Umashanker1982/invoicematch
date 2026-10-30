"""Typed data models shared by the extraction agent, the matching engine, and the web app.

`InvoiceFields` follows the course brief's example schema (vendor, invoice_number,
invoice_date, total_amount, po_number) and adds the fields needed for matching.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class InvoiceLine(BaseModel):
    sku: str | None = Field(None, description="Item code as printed on the invoice, e.g. CHR-450")
    description: str | None = None
    quantity: float | None = None
    unit_price: float | None = None
    amount: float | None = None


class InvoiceFields(BaseModel):
    """The structured fields read from one invoice. Missing values are null, never guessed."""

    vendor: str | None = Field(None, description="Seller's company name")
    invoice_number: str | None = None
    invoice_date: str | None = Field(None, description="ISO format YYYY-MM-DD")
    po_number: str | None = Field(None, description="Purchase order number, e.g. PO-7701")
    currency: str | None = Field(None, description="Three-letter code, e.g. USD")
    lines: list[InvoiceLine] = Field(default_factory=list)
    subtotal: float | None = None
    tax: float | None = Field(None, description="Sales tax; 0 if none shown")
    freight: float | None = Field(None, description="Freight, shipping, or delivery charge; 0 if none shown")
    total_amount: float | None = Field(None, description="Total amount payable")


class LLMUsage(BaseModel):
    model: str
    ok: bool
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    latency_ms: float = 0.0
    error: str | None = None


class ExtractionResult(BaseModel):
    """Everything the extraction step produced, including how it was produced."""

    fields: InvoiceFields
    method: Literal["claude", "rules"]
    bank_account: str | None = Field(None, description="Read by the document parser with fixed patterns; never sent to the AI")
    bank_routing: str | None = None
    issues: list[str] = Field(default_factory=list, description="Problems found while reading, in plain language")
    readable: bool = True
    llm: LLMUsage | None = None
    fallback_reason: str | None = None
