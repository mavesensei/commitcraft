import google.generativeai as genai

from commitcraft.config.models import CommitcraftConfig
from commitcraft.providers.base import Provider
from commitcraft.providers.ollama_provider import (
    _COMMIT_SYSTEM,
    _DESCRIBE_SYSTEM,
    _PR_SYSTEM,
    _RELEASE_SYSTEM,
)


class GeminiProvider(Provider):
    def __init__(self, config: CommitcraftConfig) -> None:
        self._config = config
        genai.configure(api_key=config.gemini_api_key)
        self._model_name = config.gemini_model

    @property
    def name(self) -> str:
        return "gemini"

    def _generate(self, system: str, prompt: str) -> str:
        model = genai.GenerativeModel(
            model_name=self._model_name,
            system_instruction=system,
        )
        response = model.generate_content(prompt)
        return response.text.strip()

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
            genai.list_models()
            return True
        except Exception:
            return False
