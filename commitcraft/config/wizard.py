from rich.console import Console
from rich.prompt import Prompt

from commitcraft.config.models import CommitcraftConfig, ProviderName
from commitcraft.config.store import save_config

console = Console()

_PROVIDER_CHOICES = {
    "1": (ProviderName.OLLAMA, "Ollama (free, runs locally — requires Ollama installed)"),
    "2": (ProviderName.OPENAI, "OpenAI (requires your own API key)"),
    "3": (ProviderName.GEMINI, "Google Gemini (requires your own API key)"),
    "4": (ProviderName.ANTHROPIC, "Anthropic Claude (requires your own API key)"),
}


def run_wizard() -> CommitcraftConfig:
    console.print("\n[bold cyan]Welcome to commitcraft![/bold cyan]\n")
    console.print("Which provider would you like to use?\n")

    for key, (_, label) in _PROVIDER_CHOICES.items():
        console.print(f"  [bold]{key})[/bold] {label}")

    choice = Prompt.ask("\nEnter choice", choices=list(_PROVIDER_CHOICES.keys()), default="1")
    provider, _ = _PROVIDER_CHOICES[choice]

    cfg = CommitcraftConfig(provider=provider)

    if provider == ProviderName.OPENAI:
        cfg.openai_api_key = Prompt.ask("Enter your OpenAI API key", password=True)
        cfg.openai_model = Prompt.ask("Model", default="gpt-4o-mini")
    elif provider == ProviderName.ANTHROPIC:
        cfg.anthropic_api_key = Prompt.ask("Enter your Anthropic API key", password=True)
        cfg.anthropic_model = Prompt.ask("Model", default="claude-haiku-4-5-20251001")
    elif provider == ProviderName.GEMINI:
        cfg.gemini_api_key = Prompt.ask("Enter your Gemini API key", password=True)
        cfg.gemini_model = Prompt.ask("Model", default="gemini-1.5-flash")
    elif provider == ProviderName.OLLAMA:
        cfg.ollama_base_url = Prompt.ask("Ollama base URL", default="http://localhost:11434")
        cfg.ollama_model = Prompt.ask("Model", default="llama3.2")

    save_config(cfg)
    console.print(f"\n[green]✓[/green] Config saved. Provider: [bold]{provider.value}[/bold]")
    return cfg
