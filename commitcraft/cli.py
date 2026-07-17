from pathlib import Path

import typer
from rich.console import Console

app = typer.Typer(
    name="commitcraft",
    help="Smart conventional commit messages — rule engine first, LLM only when needed.",
    no_args_is_help=True,
)
console = Console()


@app.command()
def init():
    """First-time setup: choose provider, store config."""
    from commitcraft.config.wizard import run_wizard
    run_wizard()


@app.command()
def commit(
    no_stage: bool = typer.Option(False, "--no-stage", help="Skip git add ."),
    split: bool = typer.Option(
        False, "--split", help="Group staged changes into multiple semantic commits"
    ),
):
    """Analyze staged diff and generate a conventional commit message."""
    import subprocess

    from rich.panel import Panel
    from rich.prompt import Prompt

    from commitcraft.config.store import load_config
    from commitcraft.generators.commit import generate_commit_message, should_offer_split
    from commitcraft.git.diff_parser import get_staged_diff
    from commitcraft.utils.token_estimator import estimate_tokens

    cfg = load_config()

    if not no_stage:
        console.print("[dim]Running git add .[/dim]")
        subprocess.run(["git", "add", "."], check=True)

    console.print("[dim]Analyzing staged changes...[/dim]")
    staged_diff = get_staged_diff()

    if not staged_diff.strip():
        console.print("[yellow]No staged changes found.[/yellow]")
        raise typer.Exit(1)

    if not split and should_offer_split(staged_diff, cfg):
        console.print("[cyan]This looks like a new project.[/cyan]")
        offer = Prompt.ask(
            "Generate individual commits per file?", choices=["y", "n"], default="y"
        )
        if offer == "y":
            split = True

    if split:
        _run_split_commit_flow(staged_diff, cfg)
        return

    message, source = generate_commit_message(staged_diff, cfg)

    if not message:
        console.print("[red]Could not generate a commit message.[/red]")
        raise typer.Exit(1)

    source_label = f"[dim](source: {source})[/dim]"
    if cfg.show_cost and source not in ("rule_engine", "none"):
        from commitcraft.analysis.filters import filter_diff
        from commitcraft.context.builder import build_commit_context
        from commitcraft.git.diff_parser import parse_diff
        parsed = parse_diff(staged_diff)
        filtered = filter_diff(parsed, extra_patterns=cfg.ignore_patterns)
        ctx = build_commit_context(filtered, [])
        tokens = estimate_tokens(ctx)
        source_label += f" [dim](~{tokens} tokens)[/dim]"

    console.print(Panel(f"[bold green]{message}[/bold green]", title="Suggested commit message"))
    console.print(source_label)

    choice = Prompt.ask("Accept?", choices=["y", "n", "e"], default="y")

    if choice == "n":
        console.print("[yellow]Cancelled.[/yellow]")
        raise typer.Exit(0)

    if choice == "e":
        message = _edit_message(message)

    subprocess.run(["git", "commit", "-m", message], check=True)
    console.print(f"[green]Committed: [bold]{message}[/bold][/green]")


def _edit_message(message: str) -> str:
    import os
    import subprocess
    import tempfile

    editor = os.environ.get("EDITOR", "vi")
    with tempfile.NamedTemporaryFile(suffix=".txt", mode="w", delete=False) as tmp:
        tmp.write(message)
        tmp_path = tmp.name
    subprocess.run([editor, tmp_path])
    edited = Path(tmp_path).read_text().strip()
    os.unlink(tmp_path)
    return edited


def _run_split_commit_flow(staged_diff: str, cfg) -> None:
    import subprocess

    from rich.panel import Panel
    from rich.prompt import Prompt
    from rich.table import Table

    from commitcraft.config.models import ProviderName
    from commitcraft.generators.commit import finish_split_groups, prepare_split_groups

    zero_cost_groups, remaining, use_content = prepare_split_groups(staged_diff, cfg)

    if remaining and cfg.provider != ProviderName.OLLAMA:
        console.print(
            f"[yellow]Split mode will make {len(remaining)} LLM call(s) "
            f"(one per changed file).[/yellow]"
        )
        proceed = Prompt.ask("Continue?", choices=["y", "n"], default="y")
        if proceed == "n":
            console.print("[yellow]Cancelled.[/yellow]")
            raise typer.Exit(0)

    groups = finish_split_groups(remaining, zero_cost_groups, cfg, use_content)

    if not groups:
        console.print("[yellow]Nothing to commit.[/yellow]")
        raise typer.Exit(0)

    results: list[tuple[str, str, str]] = []

    for i, group in enumerate(groups, start=1):
        paths = [f.path for f in group.files]
        console.print(
            Panel(
                f"[bold green]{group.message}[/bold green]",
                title=f"Group {i} ({', '.join(paths)})",
            )
        )
        choice = Prompt.ask("Accept?", choices=["y", "n", "e"], default="y")

        message = group.message
        if choice == "e":
            message = _edit_message(message)

        if choice == "n":
            console.print("[yellow]Skipped.[/yellow]")
            results.append((", ".join(paths), message, "skipped"))
            continue

        subprocess.run(["git", "add", *paths], check=True)
        subprocess.run(["git", "commit", "-m", message, "--", *paths], check=True)
        console.print(f"[green]Committed: [bold]{message}[/bold][/green]")
        results.append((", ".join(paths), message, "committed"))

    table = Table(title="Split commit summary")
    table.add_column("Files", style="cyan")
    table.add_column("Message")
    table.add_column("Status", justify="right")
    for paths_str, message, status in results:
        status_style = "green" if status == "committed" else "yellow"
        table.add_row(paths_str, message, f"[{status_style}]{status}[/{status_style}]")
    console.print(table)


@app.command()
def pr(base: str = typer.Option("main", "--base", "-b", help="Base branch to diff against")):
    """Generate a PR description from the current branch diff."""
    from rich.panel import Panel

    from commitcraft.config.store import load_config
    from commitcraft.generators.pr import generate_pr_description

    cfg = load_config()
    console.print("[dim]Generating PR description...[/dim]")
    description = generate_pr_description(cfg, base=base)
    console.print(Panel(description, title="PR Description"))
    console.print("\n[dim]Copy the above into your PR description.[/dim]")


@app.command("release-notes")
def release_notes(tag_range: str = typer.Argument(..., help="e.g. v1.0.0..v1.1.0")):
    """Categorize and summarize changes between two tags."""
    from rich.panel import Panel

    from commitcraft.config.store import load_config
    from commitcraft.generators.release_notes import generate_release_notes

    cfg = load_config()
    console.print(f"[dim]Generating release notes for {tag_range}...[/dim]")
    notes = generate_release_notes(tag_range, cfg)
    console.print(Panel(notes, title=f"Release Notes: {tag_range}"))


@app.command()
def history():
    """Analyze commit history for patterns and generic messages."""
    from rich.table import Table

    from commitcraft.git.history import (
        analyze_commit_patterns,
        detect_generic_commits,
        get_all_commits,
    )

    commits = get_all_commits(n=100)
    if not commits:
        console.print("[yellow]No commits found.[/yellow]")
        raise typer.Exit(0)

    generic = detect_generic_commits(commits)
    patterns = analyze_commit_patterns(commits)

    console.print(f"\n[bold]Analyzed {len(commits)} commits[/bold]\n")

    table = Table(title="Commit Type Distribution")
    table.add_column("Type", style="cyan")
    table.add_column("Count", justify="right")
    for ctype, count in sorted(patterns.items(), key=lambda x: -x[1]):
        table.add_row(ctype, str(count))
    console.print(table)

    if generic:
        console.print(f"\n[yellow]Found {len(generic)} generic commit message(s):[/yellow]")
        for g in generic:
            console.print(f"  [red]•[/red] {g}")
        console.print("\n[dim]Consider using commitcraft to write better commit messages.[/dim]")
    else:
        console.print("\n[green]✓[/green] No generic commit messages found. Great commit hygiene!")


@app.command()
def config():
    """Show or change current settings."""
    from rich.table import Table

    from commitcraft.config.store import config_path, load_config
    cfg = load_config()
    table = Table(title="commitcraft config", show_header=True)
    table.add_column("Setting", style="cyan")
    table.add_column("Value")
    for key, value in cfg.model_dump().items():
        display = "***" if "api_key" in key and value else str(value)
        table.add_row(key, display)
    console.print(table)
    console.print(f"\n[dim]Config file: {config_path()}[/dim]")


if __name__ == "__main__":
    app()
