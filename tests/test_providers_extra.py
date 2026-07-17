from unittest.mock import MagicMock, patch

import pytest

from commitcraft.config.models import CommitcraftConfig, ProviderName

# --- AnthropicProvider ---

@pytest.fixture
def anthropic_config():
    return CommitcraftConfig(provider=ProviderName.ANTHROPIC, anthropic_api_key="test-key")


def _anthropic_response(text):
    block = MagicMock()
    block.text = text
    resp = MagicMock()
    resp.content = [block]
    return resp


def test_anthropic_generate_commit_message(anthropic_config):
    from commitcraft.providers.anthropic_provider import AnthropicProvider
    with patch("anthropic.Anthropic") as mock_cls:
        mock_cls.return_value.messages.create.return_value = _anthropic_response("feat: add auth")
        result = AnthropicProvider(anthropic_config).generate_commit_message("ctx")
    assert result == "feat: add auth"


def test_anthropic_generate_pr_description(anthropic_config):
    from commitcraft.providers.anthropic_provider import AnthropicProvider
    with patch("anthropic.Anthropic") as mock_cls:
        mock_cls.return_value.messages.create.return_value = _anthropic_response("## Summary")
        result = AnthropicProvider(anthropic_config).generate_pr_description("ctx")
    assert "Summary" in result


def test_anthropic_generate_release_notes(anthropic_config):
    from commitcraft.providers.anthropic_provider import AnthropicProvider
    with patch("anthropic.Anthropic") as mock_cls:
        mock_cls.return_value.messages.create.return_value = _anthropic_response("## Features")
        result = AnthropicProvider(anthropic_config).generate_release_notes("ctx")
    assert "Features" in result


def test_anthropic_health_check_success(anthropic_config):
    from commitcraft.providers.anthropic_provider import AnthropicProvider
    with patch("anthropic.Anthropic") as mock_cls:
        mock_cls.return_value.messages.create.return_value = MagicMock()
        assert AnthropicProvider(anthropic_config).health_check() is True


def test_anthropic_health_check_failure(anthropic_config):
    from commitcraft.providers.anthropic_provider import AnthropicProvider
    with patch("anthropic.Anthropic") as mock_cls:
        mock_cls.return_value.messages.create.side_effect = Exception("auth error")
        assert AnthropicProvider(anthropic_config).health_check() is False


# --- OpenAIProvider ---

@pytest.fixture
def openai_config():
    return CommitcraftConfig(provider=ProviderName.OPENAI, openai_api_key="test-key")


def _openai_response(text):
    msg = MagicMock()
    msg.content = text
    choice = MagicMock()
    choice.message = msg
    resp = MagicMock()
    resp.choices = [choice]
    return resp


def test_openai_generate_commit_message(openai_config):
    from commitcraft.providers.openai_provider import OpenAIProvider
    with patch("commitcraft.providers.openai_provider.OpenAI") as mock_cls:
        mock_cls.return_value.chat.completions.create.return_value = _openai_response("feat: login")
        result = OpenAIProvider(openai_config).generate_commit_message("ctx")
    assert result == "feat: login"


def test_openai_generate_pr_description(openai_config):
    from commitcraft.providers.openai_provider import OpenAIProvider
    with patch("commitcraft.providers.openai_provider.OpenAI") as mock_cls:
        mock_cls.return_value.chat.completions.create.return_value = _openai_response("## Summary")
        result = OpenAIProvider(openai_config).generate_pr_description("ctx")
    assert "Summary" in result


def test_openai_health_check_success(openai_config):
    from commitcraft.providers.openai_provider import OpenAIProvider
    with patch("commitcraft.providers.openai_provider.OpenAI") as mock_cls:
        mock_cls.return_value.models.list.return_value = []
        assert OpenAIProvider(openai_config).health_check() is True


def test_openai_health_check_failure(openai_config):
    from commitcraft.providers.openai_provider import OpenAIProvider
    with patch("commitcraft.providers.openai_provider.OpenAI") as mock_cls:
        mock_cls.return_value.models.list.side_effect = Exception("rate limit")
        assert OpenAIProvider(openai_config).health_check() is False


# --- GeminiProvider ---

@pytest.fixture
def gemini_config():
    return CommitcraftConfig(provider=ProviderName.GEMINI, gemini_api_key="test-key")


def test_gemini_generate_commit_message(gemini_config):
    from commitcraft.providers.gemini_provider import GeminiProvider
    mock_model = MagicMock()
    mock_model.generate_content.return_value.text = "feat: gemini commit"
    genai_path = "commitcraft.providers.gemini_provider.genai"
    with patch(f"{genai_path}.configure"), \
         patch(f"{genai_path}.GenerativeModel", return_value=mock_model):
        result = GeminiProvider(gemini_config).generate_commit_message("ctx")
    assert result == "feat: gemini commit"


def test_gemini_generate_pr_description(gemini_config):
    from commitcraft.providers.gemini_provider import GeminiProvider
    mock_model = MagicMock()
    mock_model.generate_content.return_value.text = "## Summary"
    genai_path = "commitcraft.providers.gemini_provider.genai"
    with patch(f"{genai_path}.configure"), \
         patch(f"{genai_path}.GenerativeModel", return_value=mock_model):
        result = GeminiProvider(gemini_config).generate_pr_description("ctx")
    assert "Summary" in result


def test_gemini_health_check_success(gemini_config):
    from commitcraft.providers.gemini_provider import GeminiProvider
    genai_path = "commitcraft.providers.gemini_provider.genai"
    with patch(f"{genai_path}.configure"), \
         patch(f"{genai_path}.list_models", return_value=[]):
        assert GeminiProvider(gemini_config).health_check() is True


def test_gemini_health_check_failure(gemini_config):
    from commitcraft.providers.gemini_provider import GeminiProvider
    genai_path = "commitcraft.providers.gemini_provider.genai"
    with patch(f"{genai_path}.configure"), \
         patch(f"{genai_path}.list_models", side_effect=Exception("quota")):
        assert GeminiProvider(gemini_config).health_check() is False
