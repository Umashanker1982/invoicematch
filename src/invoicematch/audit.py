"""Append-only audit log with a tamper-evident hash chain.

Every decision, approval, rejection, and override is written here with who did it, why, and the
evidence used (Compliance non-negotiable N-4). Each record contains the hash of the previous
record, so editing or deleting an old record breaks the chain and `verify()` reports it.

Stored as JSON Lines (one record per line). In production this would go to write-once storage
with a 7-year retention policy.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

GENESIS = "0" * 64


def _hash(prev: str, record: dict) -> str:
    body = json.dumps(record, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256((prev + body).encode("utf-8")).hexdigest()


class AuditLog:
    def __init__(self, path: Path | None = None):
        self.path = path
        self.records: list[dict] = []
        if path and path.exists():
            self.records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

    @property
    def last_hash(self) -> str:
        return self.records[-1]["hash"] if self.records else GENESIS

    def write(self, *, action: str, actor: str, invoice_ref: str, details: dict) -> dict:
        record = {"seq": len(self.records) + 1, "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                  "action": action, "actor": actor, "invoice": invoice_ref, "details": details,
                  "prev_hash": self.last_hash}
        record["hash"] = _hash(record["prev_hash"], {k: v for k, v in record.items() if k != "hash"})
        self.records.append(record)
        if self.path:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8", newline="\n") as fh:
                fh.write(json.dumps(record, default=str) + "\n")
        return record

    def verify(self) -> tuple[bool, str]:
        """Recompute the chain. Returns (ok, message)."""
        prev = GENESIS
        for r in self.records:
            expected = _hash(prev, {k: v for k, v in r.items() if k != "hash"})
            if r["prev_hash"] != prev or r["hash"] != expected:
                return False, f"Audit log broken at record {r['seq']}: it was changed or a record is missing."
            prev = r["hash"]
        return True, f"Audit log intact: {len(self.records)} records verified."
