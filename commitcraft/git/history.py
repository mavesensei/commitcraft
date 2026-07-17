import re
import subprocess
from collections import Counter


def get_recent_commits(n: int = 10) -> list[str]:
    try:
        result = subprocess.run(
            ["git", "log", f"--max-count={n}", "--pretty=format:%s"],
            capture_output=True, text=True, check=True,
        )
        return [line.strip() for line in result.stdout.splitlines() if line.strip()]
    except subprocess.CalledProcessError:
        return []


def get_branch_commits(base: str = "main", n: int = 20) -> list[str]:
    try:
        result = subprocess.run(
            ["git", "log", f"{base}...HEAD", f"--max-count={n}", "--pretty=format:%s"],
            capture_output=True, text=True, check=True,
        )
        return [line.strip() for line in result.stdout.splitlines() if line.strip()]
    except subprocess.CalledProcessError:
        return []


def get_current_branch() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return "HEAD"


def analyze_commit_patterns(commits: list[str]) -> dict[str, int]:
    types = []
    for msg in commits:
        m = re.match(r"^(\w+)[\(:]", msg)
        if m:
            types.append(m.group(1))
    return dict(Counter(types))


_GENERIC_PATTERNS = [
    re.compile(r"^initial commit$", re.IGNORECASE),
    re.compile(r"^wip$", re.IGNORECASE),
    re.compile(r"^fix$", re.IGNORECASE),
    re.compile(r"^update$", re.IGNORECASE),
    re.compile(r"^changes?$", re.IGNORECASE),
    re.compile(r"^misc$", re.IGNORECASE),
    re.compile(r"^temp$", re.IGNORECASE),
    re.compile(r"^\.+$"),
    re.compile(r"^commit \d+$", re.IGNORECASE),
]


def detect_generic_commits(commits: list[str]) -> list[str]:
    return [c for c in commits if any(p.match(c.strip()) for p in _GENERIC_PATTERNS)]


def get_all_commits(n: int = 100) -> list[str]:
    try:
        result = subprocess.run(
            ["git", "log", f"--max-count={n}", "--pretty=format:%s"],
            capture_output=True, text=True, check=True,
        )
        return [line.strip() for line in result.stdout.splitlines() if line.strip()]
    except subprocess.CalledProcessError:
        return []
