from commitcraft.analysis.filters import FilteredDiff
from commitcraft.context.builder import build_commit_context, build_pr_context
from commitcraft.git.diff_parser import DiffFile
from commitcraft.utils.token_estimator import estimate_tokens


def _file(path: str, added: int = 10, removed: int = 3, has_func: bool = False) -> DiffFile:
    return DiffFile(
        path=path, file_type="python", is_new=False, is_deleted=False,
        added_lines=added, removed_lines=removed, raw_hunks=f"@@ hunk for {path} @@\n+new line",
        has_function_changes=has_func, has_class_changes=False,
    )


def test_commit_context_contains_file_list():
    diff = FilteredDiff(
        files=[_file("src/auth.py"), _file("tests/test_auth.py")],
        total_added=20, total_removed=6,
    )
    ctx = build_commit_context(diff, recent_commits=["feat: add login", "fix: fix typo"])
    assert "src/auth.py" in ctx
    assert "tests/test_auth.py" in ctx


def test_commit_context_contains_line_counts():
    diff = FilteredDiff(
        files=[_file("src/a.py", added=15, removed=3)], total_added=15, total_removed=3
    )
    ctx = build_commit_context(diff, recent_commits=[])
    assert "15" in ctx or "+15" in ctx


def test_commit_context_mentions_function_changes():
    diff = FilteredDiff(files=[_file("src/a.py", has_func=True)], total_added=10, total_removed=0)
    ctx = build_commit_context(diff, recent_commits=[])
    assert "function" in ctx.lower() or "def" in ctx.lower()


def test_commit_context_includes_recent_commit_style():
    recent = ["feat: add authentication", "fix: resolve login bug"]
    diff = FilteredDiff(files=[_file("src/a.py")], total_added=5, total_removed=0)
    ctx = build_commit_context(diff, recent_commits=recent)
    assert "feat: add authentication" in ctx


def test_commit_context_is_short():
    diff = FilteredDiff(files=[_file("src/a.py", added=500)], total_added=500, total_removed=0)
    ctx = build_commit_context(diff, recent_commits=[])
    assert estimate_tokens(ctx) < 800


def test_pr_context_contains_branch_name():
    ctx = build_pr_context("diff content", "feature/add-auth", ["feat: add auth"])
    assert "feature/add-auth" in ctx or "add-auth" in ctx


def test_estimate_tokens_rough():
    text = "hello world " * 100  # 200 words ~ 300 tokens
    tokens = estimate_tokens(text)
    assert 150 < tokens < 500
