from openai import OpenAI

from commitcraft.config.models import CommitcraftConfig
from commitcraft.providers.base import Provider
from commitcraft.providers.ollama_provider import (
    _COMMIT_SYSTEM,
    _DESCRIBE_SYSTEM,
    _PR_SYSTEM,
    _RELEASE_SYSTEM,
)


class OpenAIProvider(Provider):
    def __init__(self, config: CommitcraftConfig) -> None:
        self._config = config
        self._client = OpenAI(api_key=config.openai_api_key)
        self._model = config.openai_model

    @property
    def name(self) -> str:
        return "openai"

    def _generate(self, system: str, prompt: str) -> str:
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            max_tokens=512,
        )
        return (response.choices[0].message.content or "").strip()

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
            self._client.models.list()
            return True
        except Exception:
            return False
