from commitcraft.analysis.classifier import classify
from commitcraft.analysis.filters import FilteredDiff
from commitcraft.git.diff_parser import DiffFile


def _make_filtered(files_data: list[dict]) -> FilteredDiff:
    files = []
    total_added = total_removed = 0
    for d in files_data:
        f = DiffFile(
            path=d["path"],
            file_type=d.get("file_type", "python"),
            is_new=d.get("is_new", False),
            is_deleted=d.get("is_deleted", False),
            added_lines=d.get("added", 5),
            removed_lines=d.get("removed", 0),
            raw_hunks="",
            has_function_changes=d.get("has_func", False),
            has_class_changes=d.get("has_class", False),
        )
        files.append(f)
        total_added += f.added_lines
        total_removed += f.removed_lines
    return FilteredDiff(files=files, total_added=total_added, total_removed=total_removed)


def test_readme_only_is_simple():
    diff = _make_filtered([{"path": "README.md", "file_type": "markdown", "added": 3}])
    result = classify(diff)
    assert result.is_simple is True
    assert result.score < 30


def test_single_small_change_is_simple():
    diff = _make_filtered([{"path": "src/utils.py", "added": 4, "removed": 2}])
    result = classify(diff)
    assert result.is_simple is True


def test_many_files_is_complex():
    files = [{"path": f"src/module{i}/file.py", "added": 20} for i in range(8)]
    diff = _make_filtered(files)
    result = classify(diff)
    assert result.is_simple is False
    assert result.score >= 30


def test_function_changes_increase_score():
    diff_no_func = _make_filtered([{"path": "src/a.py", "added": 10, "has_func": False}])
    diff_with_func = _make_filtered([{"path": "src/a.py", "added": 10, "has_func": True}])
    assert classify(diff_with_func).score > classify(diff_no_func).score


def test_test_alongside_source_increases_score():
    no_test = _make_filtered([{"path": "src/auth.py", "has_func": True, "added": 15}])
    with_test = _make_filtered([
        {"path": "src/auth.py", "has_func": True, "added": 15},
        {"path": "tests/test_auth.py", "added": 10},
    ])
    assert classify(with_test).score > classify(no_test).score


def test_large_line_count_increases_score():
    small = _make_filtered([{"path": "src/a.py", "added": 5}])
    large = _make_filtered([{"path": "src/a.py", "added": 300}])
    assert classify(large).score > classify(small).score


def test_directory_spread_increases_score():
    same_dir = _make_filtered([
        {"path": "src/a.py", "added": 10},
        {"path": "src/b.py", "added": 10},
    ])
    spread = _make_filtered([
        {"path": "src/auth/a.py", "added": 10},
        {"path": "src/db/b.py", "added": 10},
        {"path": "tests/test_a.py", "added": 5},
    ])
    assert classify(spread).score > classify(same_dir).score


def test_empty_diff_scores_zero():
    diff = FilteredDiff()
    result = classify(diff)
    assert result.score == 0
    assert result.is_simple is True


def test_result_contains_signals():
    diff = _make_filtered([{"path": "src/a.py", "added": 10, "has_func": True}])
    result = classify(diff)
    assert "file_count" in result.signals
    assert "function_changes" in result.signals
    assert "line_count" in result.signals
    assert "directory_spread" in result.signals
    assert "test_alongside_source" in result.signals


def test_custom_threshold():
    diff = _make_filtered([{"path": "src/a.py", "added": 10}])
    result_low = classify(diff, threshold=5)
    result_high = classify(diff, threshold=80)
    assert result_low.is_simple is False
    assert result_high.is_simple is True
