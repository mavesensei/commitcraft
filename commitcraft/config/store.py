from pathlib import Path

import yaml

from commitcraft.config.models import CommitcraftConfig, ProviderName
from commitcraft.providers.base import Provider

CONFIG_DIR = Path.home() / ".commitcraft"
_CONFIG_FILE = "config.yaml"


def config_path() -> Path:
    return CONFIG_DIR / _CONFIG_FILE


def load_config() -> CommitcraftConfig:
    path = config_path()
    if not path.exists():
        return CommitcraftConfig()
    with path.open() as f:
        data = yaml.safe_load(f) or {}
    return CommitcraftConfig(**data)


def save_config(config: CommitcraftConfig) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    path = config_path()
    with path.open("w") as f:
        yaml.safe_dump(config.model_dump(mode="json"), f, default_flow_style=False)


def get_provider(config: CommitcraftConfig) -> Provider:
    from commitcraft.providers.anthropic_provider import AnthropicProvider
    from commitcraft.providers.gemini_provider import GeminiProvider
    from commitcraft.providers.ollama_provider import OllamaProvider
    from commitcraft.providers.openai_provider import OpenAIProvider

    match config.provider:
        case ProviderName.OLLAMA:
            return OllamaProvider(config)
        case ProviderName.ANTHROPIC:
            return AnthropicProvider(config)
        case ProviderName.OPENAI:
            return OpenAIProvider(config)
        case ProviderName.GEMINI:
            return GeminiProvider(config)
        case _:
            raise ValueError(f"Unknown provider: {config.provider}")
