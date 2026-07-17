from pathlib import Path

from commitcraft.git.diff_parser import ParsedDiff, parse_diff, read_working_file

FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_single_readme_file():
    raw = (FIXTURES / "simple_readme.diff").read_text()
    result = parse_diff(raw)
    assert isinstance(result, ParsedDiff)
    assert len(result.files) == 1
    assert result.files[0].path == "README.md"
    assert result.files[0].file_type == "markdown"
    assert result.files[0].added_lines == 2
    assert result.files[0].removed_lines == 0
    assert result.files[0].is_new is False
    assert result.files[0].is_deleted is False


def test_parse_lockfile():
    raw = (FIXTURES / "lockfile_only.diff").read_text()
    result = parse_diff(raw)
    assert len(result.files) == 1
    assert result.files[0].path == "package-lock.json"
    assert result.files[0].file_type == "json"


def test_parse_complex_diff_multiple_files():
    raw = (FIXTURES / "complex_multi_file.diff").read_text()
    result = parse_diff(raw)
    assert len(result.files) == 2
    paths = {f.path for f in result.files}
    assert "src/auth/login.py" in paths
    assert "tests/test_auth.py" in paths


def test_detects_new_file():
    raw = (FIXTURES / "complex_multi_file.diff").read_text()
    result = parse_diff(raw)
    test_file = next(f for f in result.files if f.path == "tests/test_auth.py")
    assert test_file.is_new is True


def test_detects_function_changes():
    raw = (FIXTURES / "complex_multi_file.diff").read_text()
    result = parse_diff(raw)
    login_file = next(f for f in result.files if f.path == "src/auth/login.py")
    assert login_file.has_function_changes is True


def test_total_line_counts():
    raw = (FIXTURES / "complex_multi_file.diff").read_text()
    result = parse_diff(raw)
    assert result.total_added > 0
    assert result.total_removed == 0


def test_parse_empty_diff():
    result = parse_diff("")
    assert result.files == []
    assert result.total_added == 0
    assert result.total_removed == 0


def test_read_working_file_returns_content(tmp_path):
    file_path = tmp_path / "example.py"
    file_path.write_text("def foo():\n    pass\n")
    assert read_working_file(str(file_path)) == "def foo():\n    pass\n"
