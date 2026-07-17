import difflib
from dataclasses import dataclass

from commitcraft.analysis.classifier import ClassificationResult
from commitcraft.analysis.filters import FilteredDiff
from commitcraft.analysis.rule_engine import RuleResult, apply_rules
from commitcraft.git.diff_parser import DiffFile

NOISE_MESSAGE = "chore: update generated/dependency files"


@dataclass
class CommitGroup:
    files: list[DiffFile]
    message: str
    source: str
    label: str


def bucket_by_rule(filtered: FilteredDiff) -> tuple[list[CommitGroup], list[DiffFile]]:
    rule_buckets: dict[tuple[str, str], list[DiffFile]] = {}
    remaining: list[DiffFile] = []

    for f in filtered.files:
        result = apply_rules(FilteredDiff(files=[f]))
        if result.matched and result.rule_name and result.message is not None:
            rule_buckets.setdefault((result.rule_name, result.message), []).append(f)
        else:
            remaining.append(f)

    groups = [
        CommitGroup(files=files, message=message, source="rule_engine", label=message)
        for (_rule_name, message), files in rule_buckets.items()
    ]
    return groups, remaining


def build_noise_group(filtered_out: list[str]) -> CommitGroup | None:
    if not filtered_out:
        return None

    files = [
        DiffFile(
            path=path, file_type="unknown", is_new=False, is_deleted=False,
            added_lines=0, removed_lines=0, raw_hunks="",
            has_function_changes=False, has_class_changes=False,
        )
        for path in filtered_out
    ]
    return CommitGroup(files=files, message=NOISE_MESSAGE, source="noise", label=NOISE_MESSAGE)


def cluster_by_similarity(descriptions: dict[str, str], threshold: float = 0.55) -> list[list[str]]:
    clusters: list[list[str]] = []
    representatives: list[str] = []

    for path, description in descriptions.items():
        joined = False
        for i, rep in enumerate(representatives):
            ratio = difflib.SequenceMatcher(None, description, rep).ratio()
            if ratio >= threshold:
                clusters[i].append(path)
                joined = True
                break
        if not joined:
            clusters.append([path])
            representatives.append(description)

    return clusters


def detect_initial_project(filtered: FilteredDiff) -> bool:
    return bool(filtered.files) and all(f.is_new for f in filtered.files)


def should_prompt_initial_project(
    filtered: FilteredDiff, rule_result: RuleResult, classification: ClassificationResult
) -> bool:
    return (
        detect_initial_project(filtered)
        and len(filtered.files) > 1
        and not rule_result.matched
        and not classification.is_simple
    )
