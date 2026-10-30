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


class AnswerKeyAnthropic(FakeAnthropic):
    """Replies like a perfect reader: finds which sample invoice it was sent and returns its expected fields.

    Used to test the web app and the pipeline end to end without a key. Unknown invoices get an empty answer.
    """

    def __init__(self):
        super().__init__()
        from pathlib import Path

        root = Path(__file__).resolve().parents[1]
        self.answers = {}
        for name in ("golden_set.json", "holdout_set.json"):
            for case in json.loads((root / "eval" / name).read_text(encoding="utf-8"))["cases"]:
                fields = {k: v for k, v in case["expected_fields"].items() if k != "bank_account"}
                self.answers[(fields["invoice_number"], fields["invoice_date"])] = fields
        outer = self

        class Messages(FakeMessages):
            def create(self, **kwargs):
                text = kwargs["messages"][0]["content"]
                match = [a for (num, _), a in outer.answers.items() if num and num in text]
                self.replies = [match[0] if len(match) == 1 else {"vendor": None, "lines": []}]
                return super().create(**kwargs)

        self.messages = Messages([])
