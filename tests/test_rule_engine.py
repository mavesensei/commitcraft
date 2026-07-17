from commitcraft.analysis.filters import FilteredDiff
from commitcraft.analysis.rule_engine import RuleResult, apply_rules
from commitcraft.git.diff_parser import DiffFile


def _file(path: str, added: int = 3, removed: int = 1) -> DiffFile:
    return DiffFile(
        path=path, file_type="text", is_new=False, is_deleted=False,
        added_lines=added, removed_lines=removed, raw_hunks="",
        has_function_changes=False, has_class_changes=False,
    )


def _diff(*files: DiffFile) -> FilteredDiff:
    return FilteredDiff(
        files=list(files),
        total_added=sum(f.added_lines for f in files),
        total_removed=sum(f.removed_lines for f in files),
    )


def test_readme_only_matches():
    result = apply_rules(_diff(_file("README.md")))
    assert result.matched is True
    assert result.message == "docs: update README"
    assert result.rule_name == "readme_only"


def test_lockfile_package_lock_matches():
    result = apply_rules(_diff(_file("package-lock.json")))
    assert result.matched is True
    assert "chore" in result.message
    assert result.rule_name == "lockfile_only"


def test_lockfile_poetry_lock_matches():
    result = apply_rules(_diff(_file("poetry.lock")))
    assert result.matched is True
    assert result.rule_name == "lockfile_only"


def test_lockfile_yarn_lock_matches():
    result = apply_rules(_diff(_file("yarn.lock")))
    assert result.matched is True
    assert result.rule_name == "lockfile_only"


def test_requirements_txt_matches_dependency_bump():
    result = apply_rules(_diff(_file("requirements.txt")))
    assert result.matched is True
    assert result.message == "chore: bump dependencies"
    assert result.rule_name == "dependency_bump"


def test_package_json_without_lock_matches_dependency_bump():
    result = apply_rules(_diff(_file("package.json")))
    assert result.matched is True
    assert result.rule_name == "dependency_bump"


def test_docs_directory_only():
    result = apply_rules(_diff(_file("docs/guide.md"), _file("docs/api.md")))
    assert result.matched is True
    assert result.message == "docs: update documentation"
    assert result.rule_name == "docs_only"


def test_single_test_file_only():
    f = _file("tests/test_utils.py")
    result = apply_rules(_diff(f))
    assert result.matched is True
    assert "test" in result.message.lower()
    assert result.rule_name == "single_test_file"


def test_config_file_only():
    result = apply_rules(_diff(_file(".github/workflows/ci.yml")))
    assert result.matched is True
    assert result.rule_name == "config_only"


def test_complex_change_no_match():
    result = apply_rules(
        _diff(_file("src/auth.py"), _file("src/db.py"), _file("tests/test_auth.py"))
    )
    assert result.matched is False
    assert result.message is None
    assert result.rule_name is None


def test_mixed_readme_and_source_no_match():
    result = apply_rules(_diff(_file("README.md"), _file("src/main.py")))
    assert result.matched is False


def test_result_is_rulesresult_type():
    result = apply_rules(_diff(_file("README.md")))
    assert isinstance(result, RuleResult)
