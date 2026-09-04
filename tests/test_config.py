import pytest
from pydantic import ValidationError
from src.config import Settings

def test_valid_config(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "anthropic")
    monkeypatch.setenv("LLM_MODEL", "claude-3")
    monkeypatch.setenv("API_KEY", "secret")
    
    settings = Settings()
    assert settings.llm_provider == "anthropic"
    assert settings.llm_model == "claude-3"
    assert settings.api_key == "secret"

def test_missing_required_config(monkeypatch):
    # Actually all have defaults except we might want to check behavior.
    # In this setup, none are strictly required since they have defaults in config.py
    # But if we made them required, we'd test it here.
    settings = Settings()
    assert settings.app_env == "development"
