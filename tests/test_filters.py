from commitcraft.analysis.filters import filter_diff
from commitcraft.git.diff_parser import DiffFile, ParsedDiff


def _make_file(path: str, added: int = 5, removed: int = 2) -> DiffFile:
    return DiffFile(
        path=path, file_type="text", is_new=False, is_deleted=False,
        added_lines=added, removed_lines=removed, raw_hunks="",
        has_function_changes=False, has_class_changes=False,
    )


def test_filters_package_lock():
    diff = ParsedDiff(files=[_make_file("package-lock.json")], total_added=5, total_removed=2)
    result = filter_diff(diff)
    assert result.files == []
    assert "package-lock.json" in result.filtered_out


def test_filters_yarn_lock():
    diff = ParsedDiff(files=[_make_file("yarn.lock")], total_added=10, total_removed=0)
    result = filter_diff(diff)
    assert result.files == []


def test_filters_dist_directory():
    diff = ParsedDiff(files=[_make_file("dist/main.js")], total_added=100, total_removed=0)
    result = filter_diff(diff)
    assert result.files == []


def test_filters_next_build():
    diff = ParsedDiff(
        files=[_make_file(".next/server/pages/index.js")], total_added=50, total_removed=0
    )
    result = filter_diff(diff)
    assert result.files == []


def test_filters_minified_js():
    diff = ParsedDiff(files=[_make_file("static/bundle.min.js")], total_added=1, total_removed=1)
    result = filter_diff(diff)
    assert result.files == []


def test_keeps_python_source():
    f = _make_file("src/auth/login.py")
    diff = ParsedDiff(files=[f], total_added=5, total_removed=2)
    result = filter_diff(diff)
    assert len(result.files) == 1
    assert result.files[0].path == "src/auth/login.py"


def test_keeps_readme():
    f = _make_file("README.md")
    diff = ParsedDiff(files=[f], total_added=3, total_removed=0)
    result = filter_diff(diff)
    assert len(result.files) == 1


def test_mixed_keeps_source_filters_lock():
    src = _make_file("src/main.py", added=10, removed=2)
    lock = _make_file("poetry.lock", added=50, removed=30)
    diff = ParsedDiff(files=[src, lock], total_added=60, total_removed=32)
    result = filter_diff(diff)
    assert len(result.files) == 1
    assert result.files[0].path == "src/main.py"
    assert "poetry.lock" in result.filtered_out
    assert result.total_added == 10
    assert result.total_removed == 2


def test_custom_extra_patterns():
    f = _make_file("coverage/index.html")
    diff = ParsedDiff(files=[f], total_added=5, total_removed=0)
    result = filter_diff(diff, extra_patterns=["coverage/"])
    assert result.files == []


def test_filtered_diff_line_counts_exclude_noise():
    src = _make_file("app.py", added=8, removed=3)
    lock = _make_file("package-lock.json", added=200, removed=150)
    diff = ParsedDiff(files=[src, lock], total_added=208, total_removed=153)
    result = filter_diff(diff)
    assert result.total_added == 8
    assert result.total_removed == 3
