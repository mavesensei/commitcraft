from unittest.mock import MagicMock, patch

import pytest

from commitcraft.config.models import CommitcraftConfig, ProviderName
from commitcraft.providers.ollama_provider import OllamaProvider


@pytest.fixture
def config():
    return CommitcraftConfig(
        provider=ProviderName.OLLAMA,
        ollama_model="llama3.2",
        ollama_base_url="http://localhost:11434",
    )


def test_ollama_provider_name(config):
    p = OllamaProvider(config)
    assert p.name == "ollama"


def test_ollama_generate_commit_message(config):
    mock_response = MagicMock()
    mock_response.json.return_value = {"response": "feat: add user authentication"}
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.post", return_value=mock_response) as mock_post:
        p = OllamaProvider(config)
        result = p.generate_commit_message("context: added login function")
        assert result == "feat: add user authentication"
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert "llama3.2" in str(call_args)


def test_ollama_generate_pr_description(config):
    mock_response = MagicMock()
    mock_response.json.return_value = {"response": "## Summary\n- Added auth"}
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.post", return_value=mock_response):
        p = OllamaProvider(config)
        result = p.generate_pr_description("branch diff context")
        assert "Summary" in result


def test_ollama_health_check_success(config):
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.get", return_value=mock_response):
        p = OllamaProvider(config)
        assert p.health_check() is True


def test_ollama_health_check_failure(config):
    with patch("httpx.get", side_effect=Exception("Connection refused")):
        p = OllamaProvider(config)
        assert p.health_check() is False


def test_anthropic_provider_name():
    from commitcraft.providers.anthropic_provider import AnthropicProvider
    cfg = CommitcraftConfig(provider=ProviderName.ANTHROPIC, anthropic_api_key="test-key")
    with patch("anthropic.Anthropic"):
        p = AnthropicProvider(cfg)
        assert p.name == "anthropic"


def test_openai_provider_name():
    from commitcraft.providers.openai_provider import OpenAIProvider
    cfg = CommitcraftConfig(provider=ProviderName.OPENAI, openai_api_key="test-key")
    with patch("openai.OpenAI"):
        p = OpenAIProvider(cfg)
        assert p.name == "openai"


def test_gemini_provider_name():
    from commitcraft.providers.gemini_provider import GeminiProvider
    cfg = CommitcraftConfig(provider=ProviderName.GEMINI, gemini_api_key="test-key")
    with patch("google.generativeai.configure"):
        p = GeminiProvider(cfg)
        assert p.name == "gemini"


def test_all_providers_implement_interface():
    from commitcraft.providers.anthropic_provider import AnthropicProvider
    from commitcraft.providers.base import Provider
    from commitcraft.providers.gemini_provider import GeminiProvider
    from commitcraft.providers.openai_provider import OpenAIProvider

    cfg = CommitcraftConfig()
    with patch("httpx.post"), patch("httpx.get"):
        assert isinstance(OllamaProvider(cfg), Provider)

    cfg = CommitcraftConfig(provider=ProviderName.ANTHROPIC, anthropic_api_key="test-key")
    with patch("anthropic.Anthropic"):
        assert isinstance(AnthropicProvider(cfg), Provider)

    cfg = CommitcraftConfig(provider=ProviderName.OPENAI, openai_api_key="test-key")
    with patch("openai.OpenAI"):
        assert isinstance(OpenAIProvider(cfg), Provider)

    cfg = CommitcraftConfig(provider=ProviderName.GEMINI, gemini_api_key="test-key")
    with patch("google.generativeai.configure"):
        assert isinstance(GeminiProvider(cfg), Provider)


def test_ollama_describe_change(config):
    mock_response = MagicMock()
    mock_response.json.return_value = {"response": "Adds a login form to the login page"}
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.post", return_value=mock_response):
        p = OllamaProvider(config)
        result = p.describe_change("diff --git a/login.py ...")
        assert result == "Adds a login form to the login page"


def test_anthropic_describe_change():
    from commitcraft.providers.anthropic_provider import AnthropicProvider

    cfg = CommitcraftConfig(provider=ProviderName.ANTHROPIC, anthropic_api_key="test-key")
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text="Adds a login form to the login page")]

    with patch("anthropic.Anthropic") as mock_client_cls:
        mock_client_cls.return_value.messages.create.return_value = mock_message
        p = AnthropicProvider(cfg)
        result = p.describe_change("diff --git a/login.py ...")
        assert result == "Adds a login form to the login page"
