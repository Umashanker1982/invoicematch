"""Document parser: prepares raw invoice text before anything else sees it.

Responsibilities
* normalize the text (line endings, invisible characters, very long input);
* read bank details with fixed patterns, so the matching engine can compare them
  with the vendor master (rule M-9);
* **remove bank details from the text that is sent to the AI model** (InfoSec
  non-negotiable N-8);
* spot damaged documents (unreadable characters), for rule M-10.

In production this module would also turn PDFs and e-invoice XML into text. In this
project the sample invoices are already text.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

MAX_CHARS = 20_000
REDACTED = "[bank details removed]"

_ACCOUNT_RE = re.compile(r"\b(?:Payment)?Account(?:\s*(?:No\.?|Number))?\s*[:#]?\s*([0-9][0-9 -]{5,}[0-9])", re.I)
_ROUTING_RE = re.compile(r"\bRouting(?:\s*Number|Number)?\s*[:#]?\s*([0-9]{9})\b", re.I)
_INVISIBLE_RE = re.compile(r"[​-‏‪-‮⁠-⁤﻿]")


@dataclass
class ParsedDocument:
    text: str             # normalized full text (used by the rules reader and grounding checks)
    text_for_ai: str      # same text with bank details removed (the only text sent to the AI model)
    bank_account: str | None
    bank_routing: str | None
    damaged: bool
    truncated: bool


def parse(raw: str) -> ParsedDocument:
    text = _INVISIBLE_RE.sub("", raw.replace("\r\n", "\n").replace("\r", "\n"))
    truncated = len(text) > MAX_CHARS
    text = text[:MAX_CHARS]

    acct = _ACCOUNT_RE.search(text)
    routing = _ROUTING_RE.search(text)
    text_for_ai = _ACCOUNT_RE.sub(lambda m: m.group(0).replace(m.group(1), REDACTED), text)
    text_for_ai = _ROUTING_RE.sub(lambda m: m.group(0).replace(m.group(1), REDACTED), text_for_ai)

    # A damaged conversion shows up as runs of placeholder characters such as "###".
    damaged_marks = len(re.findall(r"#{2,}", text))
    return ParsedDocument(
        text=text,
        text_for_ai=text_for_ai,
        bank_account=acct.group(1).strip() if acct else None,
        bank_routing=routing.group(1) if routing else None,
        damaged=damaged_marks >= 3,
        truncated=truncated,
    )
