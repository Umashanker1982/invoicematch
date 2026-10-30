"""Per-visitor workspaces and the protections that keep a public demo safe and affordable.

* Every browser gets its own InvoiceMatch workspace (demo ERP copy, review queue, audit log),
  so visitors never see each other's invoices, and "Reset" just throws the workspace away.
* Per-visitor and per-IP rate limits, a daily cap on AI calls, and a circuit breaker that
  pauses AI calls after repeated gateway failures (the app keeps working with the rules reader).
"""
from __future__ import annotations

import re
import threading
import time
from collections import deque

from invoicematch.config import Settings
from invoicematch.llm import GatewayClient
from invoicematch.pipeline import InvoiceMatch

VISITOR_ID = re.compile(r"^[a-f0-9]{16,32}$")


class Workspace:
    def __init__(self, visitor_id: str, settings: Settings, client: GatewayClient):
        self.visitor_id = visitor_id
        self.lock = threading.Lock()
        self.last_used = time.time()
        self.request_times: deque[float] = deque()
        self.im = InvoiceMatch(settings=settings, client=client)

    def allow(self, limit: int, window_s: int) -> bool:
        now = time.time()
        while self.request_times and now - self.request_times[0] > window_s:
            self.request_times.popleft()
        if len(self.request_times) >= limit:
            return False
        self.request_times.append(now)
        return True


class WorkspaceManager:
    def __init__(self, settings: Settings, client: GatewayClient, max_items: int = 300, ttl_s: int = 2 * 3600):
        self.settings, self.client = settings, client
        self.max, self.ttl = max_items, ttl_s
        self._items: dict[str, Workspace] = {}
        self._lock = threading.Lock()

    def get(self, visitor_id: str) -> Workspace:
        with self._lock:
            now = time.time()
            for vid in [v for v, w in self._items.items() if now - w.last_used > self.ttl]:
                del self._items[vid]
            ws = self._items.get(visitor_id)
            if ws is None:
                while len(self._items) >= self.max:
                    oldest = min(self._items.values(), key=lambda w: w.last_used)
                    del self._items[oldest.visitor_id]
                ws = self._items[visitor_id] = Workspace(visitor_id, self.settings, self.client)
            ws.last_used = now
            return ws

    def reset(self, visitor_id: str) -> None:
        with self._lock:
            self._items.pop(visitor_id, None)

    def __len__(self) -> int:
        return len(self._items)


class DailyCap:
    """Global cap on AI calls per UTC day, protecting the API budget."""

    def __init__(self, limit: int):
        self.limit, self._day, self._count = limit, "", 0
        self._lock = threading.Lock()

    def take(self) -> bool:
        with self._lock:
            today = time.strftime("%Y-%m-%d", time.gmtime())
            if today != self._day:
                self._day, self._count = today, 0
            if self._count >= self.limit:
                return False
            self._count += 1
            return True

    @property
    def remaining(self) -> int:
        today = time.strftime("%Y-%m-%d", time.gmtime())
        return self.limit if today != self._day else max(0, self.limit - self._count)


class CircuitBreaker:
    """Pauses AI calls after repeated gateway failures.

    closed: AI is used. open: after `threshold` failures within `window_s`, AI is skipped for
    `cooldown_s` and invoices are read by rules. half-open: after the cool-down the next request
    tries the AI again; success closes the breaker, failure opens it again.
    """

    def __init__(self, threshold: int = 3, window_s: int = 120, cooldown_s: int = 300):
        self.threshold, self.window_s, self.cooldown_s = threshold, window_s, cooldown_s
        self._failures: deque[float] = deque()
        self._opened_at: float | None = None
        self._lock = threading.Lock()

    def allow(self) -> bool:
        with self._lock:
            return self._opened_at is None or time.time() - self._opened_at >= self.cooldown_s

    def record(self, ok: bool) -> None:
        with self._lock:
            now = time.time()
            if ok:
                self._failures.clear()
                self._opened_at = None
                return
            self._failures.append(now)
            while self._failures and now - self._failures[0] > self.window_s:
                self._failures.popleft()
            if len(self._failures) >= self.threshold or self._opened_at is not None:
                self._opened_at = now

    @property
    def state(self) -> str:
        if self._opened_at is None:
            return "closed"
        return "half-open" if time.time() - self._opened_at >= self.cooldown_s else "open"
