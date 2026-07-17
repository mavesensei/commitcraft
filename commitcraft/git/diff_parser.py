import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

FUNCTION_PATTERNS = [
    re.compile(r"^\+\s*(def |async def )\w+"),        # Python
    re.compile(r"^\+\s*(function |const \w+ = |let \w+ = |var \w+ = )\w*\s*[\(\{]"),  # JS/TS
    re.compile(r"^\+\s*(public|private|protected|static)?\s+\w+\s+\w+\s*\("),  # Java/C#
    re.compile(r"^\+\s*func \w+"),                     # Go
]

CLASS_PATTERNS = [
    re.compile(r"^\+\s*class \w+"),                    # Python/JS/TS
    re.compile(r"^\+\s*(public|private)?\s*class \w+"), # Java/C#
    re.compile(r"^\+\s*type \w+ struct"),              # Go
]

EXTENSION_TO_TYPE: dict[str, str] = {
    ".py": "python", ".js": "javascript", ".ts": "typescript",
    ".tsx": "typescript", ".jsx": "javascript", ".go": "go",
    ".rs": "rust", ".java": "java", ".cs": "csharp", ".rb": "ruby",
    ".php": "php", ".cpp": "cpp", ".c": "c", ".h": "c",
    ".md": "markdown", ".json": "json", ".yaml": "yaml", ".yml": "yaml",
    ".toml": "toml", ".sh": "shell", ".bash": "shell",
    ".html": "html", ".css": "css", ".scss": "css",
    ".txt": "text", ".lock": "lock",
}


@dataclass
class DiffFile:
    path: str
    file_type: str
    is_new: bool
    is_deleted: bool
    added_lines: int
    removed_lines: int
    raw_hunks: str
    has_function_changes: bool
    has_class_changes: bool


@dataclass
class ParsedDiff:
    files: list[DiffFile] = field(default_factory=list)
    total_added: int = 0
    total_removed: int = 0


def _file_type(path: str) -> str:
    from pathlib import Path
    suffix = Path(path).suffix.lower()
    return EXTENSION_TO_TYPE.get(suffix, "unknown")


def _detect_changes(hunk_text: str) -> tuple[bool, bool]:
    has_func = any(p.search(line) for line in hunk_text.splitlines() for p in FUNCTION_PATTERNS)
    has_class = any(p.search(line) for line in hunk_text.splitlines() for p in CLASS_PATTERNS)
    return has_func, has_class


def parse_diff(raw: str) -> ParsedDiff:
    if not raw.strip():
        return ParsedDiff()

    result = ParsedDiff()
    file_blocks = re.split(r"(?=^diff --git )", raw, flags=re.MULTILINE)

    for block in file_blocks:
        if not block.startswith("diff --git "):
            continue

        header_match = re.match(r"diff --git a/(.+?) b/(.+)", block)
        if not header_match:
            continue

        path = header_match.group(2)
        is_new = bool(
            re.search(r"^new file mode", block, re.MULTILINE)
            or re.search(r"^--- /dev/null", block, re.MULTILINE)
        )
        is_deleted = bool(re.search(r"^deleted file mode", block, re.MULTILINE))

        added = len(re.findall(r"^\+(?!\+\+)", block, re.MULTILINE))
        removed = len(re.findall(r"^-(?!--)", block, re.MULTILINE))

        hunk_text = "\n".join(
            line for line in block.splitlines()
            if line.startswith("+") or line.startswith("-")
        )
        has_func, has_class = _detect_changes(hunk_text)

        diff_file = DiffFile(
            path=path,
            file_type=_file_type(path),
            is_new=is_new,
            is_deleted=is_deleted,
            added_lines=added,
            removed_lines=removed,
            raw_hunks=block,
            has_function_changes=has_func,
            has_class_changes=has_class,
        )
        result.files.append(diff_file)
        result.total_added += added
        result.total_removed += removed

    return result


def get_staged_diff() -> str:
    result = subprocess.run(
        ["git", "diff", "--cached"],
        capture_output=True, text=True, check=True,
    )
    return result.stdout


def get_branch_diff(base: str = "main") -> str:
    result = subprocess.run(
        ["git", "diff", f"{base}...HEAD"],
        capture_output=True, text=True, check=True,
    )
    return result.stdout


def get_tag_diff(tag_range: str) -> str:
    result = subprocess.run(
        ["git", "diff", tag_range],
        capture_output=True, text=True, check=True,
    )
    return result.stdout


def read_working_file(path: str) -> str:
    return Path(path).read_text()
