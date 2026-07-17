from unittest.mock import MagicMock, patch

import pytest

from commitcraft.config.models import CommitcraftConfig, ProviderName


@pytest.fixture
def ollama_config():
    return CommitcraftConfig(
        provider=ProviderName.OLLAMA,
        ollama_model="llama3.2",
        ollama_base_url="http://localhost:11434",
    )

def test_pr_generator_calls_provider(ollama_config):
    from commitcraft.generators.pr import generate_pr_description
    mock_provider = MagicMock()
    mock_provider.generate_pr_description.return_value = "## Summary\n- Added auth"
    with patch("commitcraft.generators.pr.get_current_branch", return_value="feature/auth"), \
         patch("commitcraft.generators.pr.get_branch_commits", return_value=["feat: add login"]), \
         patch("commitcraft.generators.pr.get_provider", return_value=mock_provider):
        result = generate_pr_description(ollama_config)
    assert "Summary" in result
    mock_provider.generate_pr_description.assert_called_once()

def test_pr_generator_passes_branch_name_in_context(ollama_config):
    from commitcraft.generators.pr import generate_pr_description
    mock_provider = MagicMock()
    mock_provider.generate_pr_description.return_value = "PR description"
    with patch("commitcraft.generators.pr.get_current_branch", return_value="feature/my-feature"), \
         patch("commitcraft.generators.pr.get_branch_commits", return_value=[]), \
         patch("commitcraft.generators.pr.get_provider", return_value=mock_provider):
        generate_pr_description(ollama_config)
    call_args = mock_provider.generate_pr_description.call_args[0][0]
    assert "my-feature" in call_args

def test_pr_generator_returns_string(ollama_config):
    from commitcraft.generators.pr import generate_pr_description
    mock_provider = MagicMock()
    mock_provider.generate_pr_description.return_value = "some description"
    with patch("commitcraft.generators.pr.get_current_branch", return_value="main"), \
         patch("commitcraft.generators.pr.get_branch_commits", return_value=[]), \
         patch("commitcraft.generators.pr.get_provider", return_value=mock_provider):
        result = generate_pr_description(ollama_config)
    assert isinstance(result, str)

def test_release_notes_calls_provider(ollama_config):
    from commitcraft.generators.release_notes import generate_release_notes
    mock_provider = MagicMock()
    mock_provider.generate_release_notes.return_value = "## Features\n- OAuth login"
    rn_path = "commitcraft.generators.release_notes"
    with patch(f"{rn_path}._get_commits_in_range", return_value=["feat: oauth"]), \
         patch("commitcraft.generators.release_notes.get_tag_diff", return_value="diff content"), \
         patch("commitcraft.generators.release_notes.get_provider", return_value=mock_provider):
        result = generate_release_notes("v1.0.0..v1.1.0", ollama_config)
    assert "Features" in result
    mock_provider.generate_release_notes.assert_called_once()

def test_release_notes_includes_commits_in_context(ollama_config):
    from commitcraft.generators.release_notes import generate_release_notes
    mock_provider = MagicMock()
    mock_provider.generate_release_notes.return_value = "notes"
    with patch("commitcraft.generators.release_notes._get_commits_in_range",
               return_value=["feat: add payments", "fix: auth bug"]), \
         patch("commitcraft.generators.release_notes.get_tag_diff", return_value=""), \
         patch("commitcraft.generators.release_notes.get_provider", return_value=mock_provider):
        generate_release_notes("v1.0..v1.1", ollama_config)
    context_sent = mock_provider.generate_release_notes.call_args[0][0]
    assert "feat: add payments" in context_sent
    assert "fix: auth bug" in context_sent

def test_release_notes_returns_string(ollama_config):
    from commitcraft.generators.release_notes import generate_release_notes
    mock_provider = MagicMock()
    mock_provider.generate_release_notes.return_value = "release output"
    with patch("commitcraft.generators.release_notes._get_commits_in_range", return_value=[]), \
         patch("commitcraft.generators.release_notes.get_tag_diff", return_value=""), \
         patch("commitcraft.generators.release_notes.get_provider", return_value=mock_provider):
        result = generate_release_notes("v1.0..v1.1", ollama_config)
    assert isinstance(result, str)
