"""All settings come from environment variables (optionally loaded from a .env file).

This is the only module that reads configuration, so configuration stays separate
from code, as the capstone overview requires. Secrets are never printed: use
`Settings.masked_key()` when a key has to be shown.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VALID_MODES = {"claude", "rules"}


def load_dotenv(path: Path | None = None) -> None:
    """Load KEY=VALUE lines from a .env file into os.environ.

    Real environment variables win over the file, so a hosting platform's secret
    settings always take precedence. No third-party package is needed.
    """
    path = path or ROOT / ".env"
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def _float(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, default))
    except ValueError:
        return default


def _int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    llm_mode: str
    sharedllm_key: str | None
    llm_base_url: str
    model: str
    llm_timeout_s: float
    llm_max_retries: int
    warning: str | None = None

    @property
    def claude_enabled(self) -> bool:
        return self.llm_mode == "claude" and bool(self.sharedllm_key)

    def masked_key(self) -> str:
        if not self.sharedllm_key:
            return "(not set)"
        k = self.sharedllm_key
        return f"{k[:13]}...{k[-4:]}" if len(k) > 20 else "(set)"


def load_settings(dotenv: bool = True) -> Settings:
    if dotenv:
        load_dotenv()
    mode = os.environ.get("LLM_MODE", "claude").strip().lower()
    warning = None
    if mode not in VALID_MODES:
        warning = f"Unknown LLM_MODE={mode!r}; using rules."
        mode = "rules"
    key = os.environ.get("SHAREDLLM_KEY", "").strip() or None
    if mode == "claude" and not key:
        warning = "LLM_MODE=claude but SHAREDLLM_KEY is not set; using rules only."
        mode = "rules"
    return Settings(
        llm_mode=mode,
        sharedllm_key=key,
        llm_base_url=os.environ.get("LLM_BASE_URL", "https://api.sharedllm.com/anthropic").strip(),
        model=os.environ.get("CLAUDE_MODEL", "claude-haiku-5-5").strip(),
        llm_timeout_s=_float("LLM_TIMEOUT_S", 20.0),
        llm_max_retries=_int("LLM_MAX_RETRIES", 1),
        warning=warning,
    )
