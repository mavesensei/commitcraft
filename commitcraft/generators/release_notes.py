import subprocess

from commitcraft.config.models import CommitcraftConfig
from commitcraft.config.store import get_provider
from commitcraft.context.builder import build_release_context
from commitcraft.git.diff_parser import get_tag_diff


def _get_commits_in_range(tag_range: str) -> list[str]:
    try:
        result = subprocess.run(
            ["git", "log", tag_range, "--pretty=format:%s"],
            capture_output=True, text=True, check=True,
        )
        return [line.strip() for line in result.stdout.splitlines() if line.strip()]
    except subprocess.CalledProcessError:
        return []


def generate_release_notes(tag_range: str, config: CommitcraftConfig) -> str:
    commits = _get_commits_in_range(tag_range)
    tag_diff = get_tag_diff(tag_range)
    context = build_release_context(tag_diff, tag_range)
    context += "\n\n=== Commits in range ===\n" + "\n".join(f"  {c}" for c in commits)
    provider = get_provider(config)
    return provider.generate_release_notes(context)
