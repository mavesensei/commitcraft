from dataclasses import dataclass
from pathlib import Path

from commitcraft.analysis.filters import FilteredDiff

LOCKFILE_NAMES = {
    "package-lock.json", "yarn.lock", "poetry.lock",
    "Pipfile.lock", "composer.lock", "Gemfile.lock", "pnpm-lock.yaml",
}

DEPENDENCY_MANIFESTS = {
    "requirements.txt", "requirements-dev.txt", "setup.cfg",
    "package.json", "Pipfile", "pyproject.toml",
}

CONFIG_PATTERNS = {".yml", ".yaml", ".json", ".toml", ".ini", ".cfg", ".env"}
CONFIG_DIRS = {".github", ".circleci", ".gitlab", "config", ".husky"}


@dataclass
class RuleResult:
    matched: bool
    message: str | None
    rule_name: str | None


def _all_paths(filtered: FilteredDiff) -> list[str]:
    return [f.path for f in filtered.files]


def _readme_only(paths: list[str]) -> RuleResult | None:
    if len(paths) == 1 and Path(paths[0]).name.upper().startswith("README"):
        return RuleResult(matched=True, message="docs: update README", rule_name="readme_only")
    return None


def _lockfile_only(paths: list[str]) -> RuleResult | None:
    if all(Path(p).name in LOCKFILE_NAMES for p in paths):
        return RuleResult(matched=True, message="chore: update lockfile", rule_name="lockfile_only")
    return None


def _dependency_bump(paths: list[str]) -> RuleResult | None:
    if all(Path(p).name in DEPENDENCY_MANIFESTS for p in paths):
        return RuleResult(
            matched=True, message="chore: bump dependencies", rule_name="dependency_bump"
        )
    return None


def _docs_only(paths: list[str]) -> RuleResult | None:
    doc_exts = {".md", ".rst", ".txt"}
    doc_dirs = {"docs", "doc", "documentation"}
    if all(
        Path(p).suffix.lower() in doc_exts or Path(p).parts[0].lower() in doc_dirs
        for p in paths
    ):
        return RuleResult(matched=True, message="docs: update documentation", rule_name="docs_only")
    return None


def _single_test_file(paths: list[str]) -> RuleResult | None:
    if len(paths) == 1 and "test" in paths[0].lower():
        name = Path(paths[0]).stem
        return RuleResult(
            matched=True, message=f"test: add tests for {name}", rule_name="single_test_file"
        )
    return None


def _config_only(paths: list[str]) -> RuleResult | None:
    def is_config(p: str) -> bool:
        parts = Path(p).parts
        return (
            Path(p).suffix.lower() in CONFIG_PATTERNS
            and (
                parts[0] in CONFIG_DIRS
                or not any("src" in part or "lib" in part for part in parts)
            )
        )
    if paths and all(is_config(p) for p in paths):
        return RuleResult(matched=True, message="chore: update config", rule_name="config_only")
    return None


_RULES = [
    _readme_only, _lockfile_only, _dependency_bump, _docs_only, _single_test_file, _config_only
]


def apply_rules(filtered: FilteredDiff) -> RuleResult:
    if not filtered.files:
        return RuleResult(matched=False, message=None, rule_name=None)

    paths = _all_paths(filtered)
    for rule in _RULES:
        result = rule(paths)
        if result is not None:
            return result

    return RuleResult(matched=False, message=None, rule_name=None)
