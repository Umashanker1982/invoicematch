"""Client for Claude through the SharedLLM gateway (the course's AI gateway).

Why a gateway: one place to meter cost, log every AI call, rotate keys, and enforce
spend limits, without any provider key inside this application. The provider key
(Anthropic) is stored in the gateway's Resource Pool; this app only holds its own
gateway key.

Design rules
* Never raises: on any failure it returns None plus an LLMUsage record with the
  error, and the caller falls back to rules.
* Records tokens, cost, and latency for every call (shown in the web app and logs).
* Sends `Accept-Encoding: identity`: the gateway's compressed responses could not
  be decoded by the Python HTTP client during integration testing.
* Uses only parameters supported by the Anthropic SDK 2.x (`temperature` was removed
  there; passing it raised a TypeError during integration testing).
"""
from __future__ import annotations

import time
from typing import Any

from invoicematch.config import Settings
from invoicematch.models import LLMUsage


class GatewayClient:
    def __init__(self, settings: Settings, client: Any | None = None):
        self.settings = settings
        self._client = client
        if self._client is None and settings.claude_enabled:
            import anthropic

            self._client = anthropic.Anthropic(
                api_key="via-gateway",  # the gateway injects the provider key (BYOK in the Resource Pool)
                base_url=settings.llm_base_url,
                timeout=settings.llm_timeout_s,
                max_retries=settings.llm_max_retries,
                default_headers={"X-SharedLLM-Key": settings.sharedllm_key or "", "Accept-Encoding": "identity"},
            )

    @property
    def enabled(self) -> bool:
        return self._client is not None

    def cost(self, input_tokens: int, output_tokens: int) -> float:
        s = self.settings
        return round((input_tokens * s.price_input_per_mtok + output_tokens * s.price_output_per_mtok) / 1_000_000, 6)

    def complete(self, *, system: str, user: str, max_tokens: int = 1200) -> tuple[str | None, LLMUsage]:
        """Send one message. Returns (text or None, usage record)."""
        model = self.settings.model
        if not self.enabled:
            return None, LLMUsage(model=model, ok=False, error="AI is not enabled (no SharedLLM key)")
        t0 = time.perf_counter()
        try:
            resp = self._client.messages.create(
                model=model, max_tokens=max_tokens, system=system,
                messages=[{"role": "user", "content": user}],
            )
        except Exception as exc:  # network, gateway, quota, timeout: all handled the same way
            return None, LLMUsage(model=model, ok=False, error=f"{type(exc).__name__}: {str(exc)[:160]}",
                                  latency_ms=round((time.perf_counter() - t0) * 1000, 1))
        usage = getattr(resp, "usage", None)
        in_tok = int(getattr(usage, "input_tokens", 0) or 0)
        out_tok = int(getattr(usage, "output_tokens", 0) or 0)
        text = "".join(getattr(b, "text", "") for b in getattr(resp, "content", []) if getattr(b, "type", "text") == "text")
        return text.strip(), LLMUsage(model=model, ok=True, input_tokens=in_tok, output_tokens=out_tok,
                                      cost_usd=self.cost(in_tok, out_tok),
                                      latency_ms=round((time.perf_counter() - t0) * 1000, 1))
