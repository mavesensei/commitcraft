import fnmatch
from dataclasses import dataclass, field

from commitcraft.git.diff_parser import DiffFile, ParsedDiff

DEFAULT_IGNORE_PATTERNS: list[str] = [
    "package-lock.json",
    "yarn.lock",
    "poetry.lock",
    "Pipfile.lock",
    "composer.lock",
    "Gemfile.lock",
    "pnpm-lock.yaml",
    "dist/*",
    "build/*",
    ".next/*",
    "node_modules/*",
    "*.min.js",
    "*.min.css",
    "*.map",
    "__pycache__/*",
    "*.pyc",
    ".mypy_cache/*",
    ".ruff_cache/*",
    "coverage/*",
    ".coverage",
    "*.egg-info/*",
    "site-packages/*",
]


@dataclass
class FilteredDiff:
    files: list[DiffFile] = field(default_factory=list)
    filtered_out: list[str] = field(default_factory=list)
    total_added: int = 0
    total_removed: int = 0


def _is_ignored(path: str, patterns: list[str]) -> bool:
    for pattern in patterns:
        if fnmatch.fnmatch(path, pattern):
            return True
        # also match if path starts with a prefix pattern
        # e.g. "dist/*" should match "dist/foo/bar.js"
        prefix = pattern.rstrip("/*")
        if path.startswith(prefix + "/") or path.startswith(prefix + "\\"):
            return True
    return False


def filter_diff(
    parsed: ParsedDiff,
    extra_patterns: list[str] | None = None,
) -> FilteredDiff:
    patterns = DEFAULT_IGNORE_PATTERNS + (extra_patterns or [])
    result = FilteredDiff()

    for f in parsed.files:
        if _is_ignored(f.path, patterns):
            result.filtered_out.append(f.path)
        else:
            result.files.append(f)
            result.total_added += f.added_lines
            result.total_removed += f.removed_lines

    return result
