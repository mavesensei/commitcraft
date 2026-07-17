from enum import Enum

from pydantic import BaseModel, Field


class ProviderName(str, Enum):
    OLLAMA = "ollama"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"


class CommitcraftConfig(BaseModel):
    provider: ProviderName = ProviderName.OLLAMA
    ollama_model: str = "llama3.2"
    ollama_base_url: str = "http://localhost:11434"
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-haiku-4-5-20251001"
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-1.5-flash"
    complexity_threshold: int = Field(default=30, ge=0, le=100)
    ignore_patterns: list[str] = Field(default_factory=list)
    show_cost: bool = False
