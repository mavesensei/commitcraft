from commitcraft.analysis.classifier import classify
from commitcraft.analysis.filters import FilteredDiff, filter_diff
from commitcraft.analysis.grouper import (
    CommitGroup,
    bucket_by_rule,
    build_noise_group,
    cluster_by_similarity,
    detect_initial_project,
    should_prompt_initial_project,
)
from commitcraft.analysis.rule_engine import apply_rules
from commitcraft.config.models import CommitcraftConfig
from commitcraft.config.store import get_provider
from commitcraft.context.builder import build_commit_context
from commitcraft.git.diff_parser import DiffFile, parse_diff, read_working_file
from commitcraft.git.history import get_recent_commits

_CONTENT_PREVIEW_CHARS = 2000


def generate_commit_message(staged_diff: str, config: CommitcraftConfig) -> tuple[str, str]:
    if not staged_diff.strip():
        return "", "none"

    parsed = parse_diff(staged_diff)
    filtered = filter_diff(parsed, extra_patterns=config.ignore_patterns)

    if not filtered.files:
        return "chore: update generated/dependency files", "rule_engine"

    rule_result = apply_rules(filtered)
    if rule_result.matched:
        return rule_result.message, "rule_engine"

    classification = classify(filtered, threshold=config.complexity_threshold)
    if classification.is_simple:
        return "chore: minor changes", "rule_engine"

    recent = get_recent_commits(n=5)
    context = build_commit_context(filtered, recent)
    provider = get_provider(config)
    message = provider.generate_commit_message(context)
    return message, provider.name


def prepare_split_groups(
    staged_diff: str, config: CommitcraftConfig
) -> tuple[list[CommitGroup], list[DiffFile], bool]:
    parsed = parse_diff(staged_diff)
    filtered = filter_diff(parsed, extra_patterns=config.ignore_patterns)

    rule_groups, remaining = bucket_by_rule(filtered)
    noise_group = build_noise_group(filtered.filtered_out)
    zero_cost_groups = rule_groups + ([noise_group] if noise_group else [])
    use_content = detect_initial_project(filtered)

    return zero_cost_groups, remaining, use_content


def should_offer_split(staged_diff: str, config: CommitcraftConfig) -> bool:
    parsed = parse_diff(staged_diff)
    filtered = filter_diff(parsed, extra_patterns=config.ignore_patterns)

    if not filtered.files:
        return False

    rule_result = apply_rules(filtered)
    classification = classify(filtered, threshold=config.complexity_threshold)
    return should_prompt_initial_project(filtered, rule_result, classification)


def finish_split_groups(
    remaining_files: list[DiffFile],
    zero_cost_groups: list[CommitGroup],
    config: CommitcraftConfig,
    use_content: bool,
) -> list[CommitGroup]:
    rule_groups = [g for g in zero_cost_groups if g.source != "noise"]
    noise_groups = [g for g in zero_cost_groups if g.source == "noise"]

    if not remaining_files:
        return rule_groups + noise_groups

    provider = get_provider(config)
    files_by_path = {f.path: f for f in remaining_files}
    descriptions: dict[str, str] = {}
    forced_singletons: list[list[str]] = []

    for f in remaining_files:
        try:
            if use_content:
                content = read_working_file(f.path)[:_CONTENT_PREVIEW_CHARS]
                descriptions[f.path] = provider.describe_change(content)
            else:
                descriptions[f.path] = provider.describe_change(f.raw_hunks)
        except Exception:
            forced_singletons.append([f.path])

    clusters = cluster_by_similarity(descriptions) + forced_singletons
    recent = get_recent_commits(n=5)

    semantic_groups: list[CommitGroup] = []
    for cluster_paths in clusters:
        cluster_files = [files_by_path[p] for p in cluster_paths]
        cluster_filtered = FilteredDiff(
            files=cluster_files,
            total_added=sum(f.added_lines for f in cluster_files),
            total_removed=sum(f.removed_lines for f in cluster_files),
        )
        context = build_commit_context(cluster_filtered, recent)
        message = provider.generate_commit_message(context)
        semantic_groups.append(
            CommitGroup(
                files=cluster_files, message=message, source=provider.name, label=message
            )
        )

    return rule_groups + semantic_groups + noise_groups
