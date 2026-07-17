from unittest.mock import patch

import pytest

from commitcraft.config.models import CommitcraftConfig, ProviderName
from commitcraft.config.store import config_path, get_provider, load_config, save_config


def test_config_path_is_in_home(tmp_path):
    with patch("commitcraft.config.store.CONFIG_DIR", tmp_path / ".commitcraft"):
        p = config_path()
        assert p.name == "config.yaml"


def test_save_and_load_roundtrip(tmp_path):
    cfg = CommitcraftConfig(
        provider=ProviderName.OPENAI, openai_api_key="sk-test", complexity_threshold=45
    )
    config_dir = tmp_path / ".commitcraft"

    with patch("commitcraft.config.store.CONFIG_DIR", config_dir):
        save_config(cfg)
        loaded = load_config()

    assert loaded.provider == ProviderName.OPENAI
    assert loaded.openai_api_key == "sk-test"
    assert loaded.complexity_threshold == 45


def test_load_config_returns_defaults_when_missing(tmp_path):
    with patch("commitcraft.config.store.CONFIG_DIR", tmp_path / ".commitcraft"):
        cfg = load_config()
    assert cfg.provider == ProviderName.OLLAMA
    assert cfg.complexity_threshold == 30


def test_get_provider_returns_ollama():
    from commitcraft.providers.ollama_provider import OllamaProvider
    cfg = CommitcraftConfig(provider=ProviderName.OLLAMA)
    provider = get_provider(cfg)
    assert isinstance(provider, OllamaProvider)


def test_get_provider_returns_anthropic():
    from commitcraft.providers.anthropic_provider import AnthropicProvider
    cfg = CommitcraftConfig(provider=ProviderName.ANTHROPIC, anthropic_api_key="key")
    with patch("anthropic.Anthropic"):
        provider = get_provider(cfg)
    assert isinstance(provider, AnthropicProvider)


def test_get_provider_raises_for_unknown():
    cfg = CommitcraftConfig()
    cfg.provider = "unknown"  # type: ignore
    with pytest.raises(ValueError, match="Unknown provider"):
        get_provider(cfg)
