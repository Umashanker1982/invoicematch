from invoicematch.config import load_dotenv, load_settings


def _clear(monkeypatch):
    for name in ("LLM_MODE", "SHAREDLLM_KEY", "LLM_BASE_URL", "CLAUDE_MODEL", "LLM_TIMEOUT_S", "LLM_MAX_RETRIES"):
        monkeypatch.delenv(name, raising=False)


def test_without_key_falls_back_to_rules(monkeypatch):
    _clear(monkeypatch)
    s = load_settings(dotenv=False)
    assert s.llm_mode == "rules"
    assert not s.claude_enabled
    assert "SHAREDLLM_KEY" in (s.warning or "")


def test_with_key_uses_claude_through_gateway(monkeypatch):
    _clear(monkeypatch)
    monkeypatch.setenv("SHAREDLLM_KEY", "sk-sharedllm-abcdefghijklmnopqrstuvwxyz")
    s = load_settings(dotenv=False)
    assert s.claude_enabled
    assert s.llm_base_url == "https://api.sharedllm.com/anthropic"
    assert s.model == "claude-haiku-5-5"


def test_key_is_never_shown_in_full(monkeypatch):
    _clear(monkeypatch)
    key = "sk-sharedllm-abcdefghijklmnopqrstuvwxyz"
    monkeypatch.setenv("SHAREDLLM_KEY", key)
    masked = load_settings(dotenv=False).masked_key()
    assert key not in masked and masked.endswith("wxyz")


def test_invalid_mode_and_numbers_are_safe(monkeypatch):
    _clear(monkeypatch)
    monkeypatch.setenv("LLM_MODE", "banana")
    monkeypatch.setenv("LLM_TIMEOUT_S", "not-a-number")
    s = load_settings(dotenv=False)
    assert s.llm_mode == "rules" and s.llm_timeout_s == 20.0


def test_dotenv_file_does_not_override_real_environment(monkeypatch, tmp_path):
    _clear(monkeypatch)
    env = tmp_path / ".env"
    env.write_text("# comment\nCLAUDE_MODEL=from-file\nLLM_MODE='rules'\n", encoding="utf-8")
    monkeypatch.setenv("CLAUDE_MODEL", "from-environment")
    load_dotenv(env)
    import os
    assert os.environ["CLAUDE_MODEL"] == "from-environment"
    assert os.environ["LLM_MODE"] == "rules"
