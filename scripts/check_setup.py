"""Check that the project is set up correctly.

    python scripts/check_setup.py          # versions and configuration (no network)
    python scripts/check_setup.py --ping   # also sends one tiny request through SharedLLM
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from invoicematch.config import ROOT, load_settings  # noqa: E402


def main() -> int:
    ok = True
    print(f"Python        : {sys.version.split()[0]}")
    for pkg in ("anthropic", "pydantic", "pytest"):
        try:
            mod = __import__(pkg)
            print(f"{pkg:<14}: {getattr(mod, '__version__', 'installed')}")
        except ImportError:
            print(f"{pkg:<14}: MISSING  -> run: pip install -r requirements.txt")
            ok = False

    s = load_settings()
    print(f".env file     : {'found' if (ROOT / '.env').exists() else 'not found (copy .env.example to .env)'}")
    print(f"LLM mode      : {s.llm_mode}")
    print(f"SharedLLM key : {s.masked_key()}")
    print(f"Gateway URL   : {s.llm_base_url}")
    print(f"Model         : {s.model}")
    if s.warning:
        print(f"Warning       : {s.warning}")

    if "--ping" in sys.argv:
        if not s.claude_enabled:
            print("Ping          : skipped (Claude mode is not enabled)")
            ok = False
        else:
            import anthropic

            client = anthropic.Anthropic(
                api_key="via-gateway",  # the gateway supplies the provider key (BYOK in the Resource Pool)
                base_url=s.llm_base_url,
                timeout=s.llm_timeout_s,
                max_retries=0,
                # Accept-Encoding: identity works around a compressed-response decoding error seen with the gateway.
                default_headers={"X-SharedLLM-Key": s.sharedllm_key, "Accept-Encoding": "identity"},
            )
            try:
                r = client.messages.create(model=s.model, max_tokens=20,
                                           messages=[{"role": "user", "content": "Reply with exactly: InvoiceMatch ready"}])
                text = "".join(getattr(b, "text", "") for b in r.content).strip()
                print(f"Ping          : OK -> {text!r} ({r.usage.input_tokens} in / {r.usage.output_tokens} out tokens)")
            except Exception as exc:  # show the type and message, never the key
                print(f"Ping          : FAILED -> {type(exc).__name__}: {exc}")
                ok = False

    print("\nRESULT        :", "ALL GOOD" if ok else "SOMETHING NEEDS ATTENTION (see above)")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
