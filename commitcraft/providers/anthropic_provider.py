import anthropic

from commitcraft.config.models import CommitcraftConfig
from commitcraft.providers.base import Provider
from commitcraft.providers.ollama_provider import (
    _COMMIT_SYSTEM,
    _DESCRIBE_SYSTEM,
    _PR_SYSTEM,
    _RELEASE_SYSTEM,
)


class AnthropicProvider(Provider):
    def __init__(self, config: CommitcraftConfig) -> None:
        self._config = config
        self._client = anthropic.Anthropic(api_key=config.anthropic_api_key)
        self._model = config.anthropic_model

    @property
    def name(self) -> str:
        return "anthropic"

    def _generate(self, system: str, prompt: str) -> str:
        message = self._client.messages.create(
            model=self._model,
            max_tokens=512,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text.strip()

    def generate_commit_message(self, context: str) -> str:
        return self._generate(_COMMIT_SYSTEM, context)

    def generate_pr_description(self, context: str) -> str:
        return self._generate(_PR_SYSTEM, context)

    def generate_release_notes(self, context: str) -> str:
        return self._generate(_RELEASE_SYSTEM, context)

    def describe_change(self, context: str) -> str:
        return self._generate(_DESCRIBE_SYSTEM, context)

    def health_check(self) -> bool:
        try:
            self._client.messages.create(
                model=self._model, max_tokens=1,
                messages=[{"role": "user", "content": "ping"}],
            )
            return True
        except Exception:
            return False
