import httpx

from commitcraft.config.models import CommitcraftConfig
from commitcraft.providers.base import Provider

_COMMIT_SYSTEM = (
    "You are an expert at writing conventional commit messages. "
    "Given a summary of code changes, write a single conventional commit message. "
    "Format: <type>(<optional scope>): <description>. "
    "Types: feat, fix, docs, style, refactor, test, chore, perf, ci, build. "
    "Output ONLY the commit message — no explanation, no markdown, no quotes."
)

_PR_SYSTEM = (
    "You are an expert at writing GitHub pull request descriptions. "
    "Given a summary of code changes, write a clear PR description in markdown with: "
    "a '## Summary' section (3-5 bullet points) and a '## Changes' section. "
    "Be concise and factual."
)

_RELEASE_SYSTEM = (
    "You are an expert at writing software release notes. "
    "Given a list of commits or change summaries, produce structured release notes "
    "grouped by: Features, Bug Fixes, Documentation, Other. Use markdown."
)

_DESCRIBE_SYSTEM = (
    "You are analyzing a single file's change. Given either a diff or file content, "
    "describe in one plain sentence what this file does or what changed. "
    "Output only the sentence — no markdown, no quotes, no explanation."
)


class OllamaProvider(Provider):
    def __init__(self, config: CommitcraftConfig) -> None:
        self._config = config
        self._base_url = config.ollama_base_url
        self._model = config.ollama_model

    @property
    def name(self) -> str:
        return "ollama"

    def _generate(self, system: str, prompt: str) -> str:
        response = httpx.post(
            f"{self._base_url}/api/generate",
            json={"model": self._model, "system": system, "prompt": prompt, "stream": False},
            timeout=60.0,
        )
        response.raise_for_status()
        return response.json()["response"].strip()

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
            httpx.get(f"{self._base_url}/api/tags", timeout=5.0).raise_for_status()
            return True
        except Exception:
            return False
