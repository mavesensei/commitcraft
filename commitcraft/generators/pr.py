from commitcraft.config.models import CommitcraftConfig
from commitcraft.config.store import get_provider
from commitcraft.context.builder import build_pr_context
from commitcraft.git.history import get_branch_commits, get_current_branch


def generate_pr_description(config: CommitcraftConfig, base: str = "main") -> str:
    branch = get_current_branch()
    commits = get_branch_commits(base=base)
    context = build_pr_context("", branch, commits)
    provider = get_provider(config)
    return provider.generate_pr_description(context)
