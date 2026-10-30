"""A fake Anthropic client so tests run offline, with no key and no cost."""
from __future__ import annotations

import json
from types import SimpleNamespace


class FakeMessages:
    def __init__(self, replies):
        self.replies = list(replies)
        self.calls: list[dict] = []

    # Parameters accepted by Anthropic SDK 2.x messages.create(). Anything else raises TypeError,
    # exactly like the real SDK (it removed `temperature`, `top_p`, and `top_k`).
    SUPPORTED = {"model", "max_tokens", "messages", "system", "stop_sequences", "metadata", "tools", "tool_choice",
                 "thinking", "output_config", "service_tier", "stream", "timeout", "extra_headers", "extra_body"}

    def create(self, **kwargs):
        unsupported = set(kwargs) - self.SUPPORTED
        if unsupported:
            raise TypeError(f"create() got an unexpected keyword argument {sorted(unsupported)[0]!r}")
        self.calls.append(kwargs)
        reply = self.replies.pop(0) if self.replies else ""
        if isinstance(reply, Exception):
            raise reply
        text = reply if isinstance(reply, str) else json.dumps(reply)
        return SimpleNamespace(content=[SimpleNamespace(type="text", text=text)],
                               usage=SimpleNamespace(input_tokens=900, output_tokens=250), stop_reason="end_turn")


class FakeAnthropic:
    def __init__(self, *replies):
        self.messages = FakeMessages(replies)
