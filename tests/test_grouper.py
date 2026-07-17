from commitcraft.analysis.classifier import ClassificationResult
from commitcraft.analysis.filters import FilteredDiff
from commitcraft.analysis.grouper import (
    bucket_by_rule,
    build_noise_group,
    cluster_by_similarity,
    detect_initial_project,
    should_prompt_initial_project,
)
from commitcraft.analysis.rule_engine import RuleResult
from commitcraft.git.diff_parser import DiffFile


def _file(path: str, is_new: bool = False) -> DiffFile:
    return DiffFile(
        path=path, file_type="python", is_new=is_new, is_deleted=False,
        added_lines=1, removed_lines=0, raw_hunks="+pass",
        has_function_changes=False, has_class_changes=False,
    )


def test_bucket_by_rule_matches_readme_individually():
    filtered = FilteredDiff(files=[_file("README.md"), _file("src/utils.py")])
    groups, remaining = bucket_by_rule(filtered)

    assert len(groups) == 1
    assert groups[0].message == "docs: update README"
    assert [f.path for f in groups[0].files] == ["README.md"]
    assert [f.path for f in remaining] == ["src/utils.py"]


def test_bucket_by_rule_collapses_multiple_files_matching_same_rule():
    filtered = FilteredDiff(files=[_file("docs/a.md"), _file("docs/b.md")])
    groups, remaining = bucket_by_rule(filtered)

    assert len(groups) == 1
    assert groups[0].message == "docs: update documentation"
    assert {f.path for f in groups[0].files} == {"docs/a.md", "docs/b.md"}
    assert remaining == []


def test_bucket_by_rule_separates_multiple_single_test_files_by_message():
    filtered = FilteredDiff(files=[_file("tests/test_foo.py"), _file("tests/test_bar.py")])
    groups, remaining = bucket_by_rule(filtered)

    assert remaining == []
    assert len(groups) == 2

    messages = {g.message for g in groups}
    assert messages == {"test: add tests for test_foo", "test: add tests for test_bar"}

    for group in groups:
        assert len(group.files) == 1
        if group.message == "test: add tests for test_foo":
            assert group.files[0].path == "tests/test_foo.py"
        else:
            assert group.files[0].path == "tests/test_bar.py"


def test_bucket_by_rule_no_match_leaves_file_in_remaining():
    filtered = FilteredDiff(files=[_file("src/utils.py")])
    groups, remaining = bucket_by_rule(filtered)

    assert groups == []
    assert [f.path for f in remaining] == ["src/utils.py"]


def test_build_noise_group_empty_returns_none():
    assert build_noise_group([]) is None


def test_build_noise_group_bundles_paths():
    group = build_noise_group(["package-lock.json", "dist/bundle.js"])
    assert group is not None
    assert group.message == "chore: update generated/dependency files"
    assert group.source == "noise"
    assert {f.path for f in group.files} == {"package-lock.json", "dist/bundle.js"}


def test_cluster_by_similarity_merges_similar_descriptions():
    descriptions = {
        "frontend/hero.py": "Updates the hero section of the landing page",
        "frontend/hero_styles.py": "Updates styling for the hero section of the landing page",
    }
    clusters = cluster_by_similarity(descriptions, threshold=0.55)
    assert len(clusters) == 1
    assert set(clusters[0]) == set(descriptions.keys())


def test_cluster_by_similarity_keeps_dissimilar_descriptions_separate():
    descriptions = {
        "frontend/landing_page.py": "Updates the hero section of the landing page",
        "frontend/login_page.py": "Adds password validation to the login form",
    }
    clusters = cluster_by_similarity(descriptions, threshold=0.55)
    assert len(clusters) == 2


def test_cluster_by_similarity_empty_input_returns_empty_list():
    assert cluster_by_similarity({}) == []


def test_detect_initial_project_true_when_all_files_new():
    filtered = FilteredDiff(files=[_file("a.py", is_new=True), _file("b.py", is_new=True)])
    assert detect_initial_project(filtered) is True


def test_detect_initial_project_false_when_any_file_not_new():
    filtered = FilteredDiff(files=[_file("a.py", is_new=True), _file("b.py", is_new=False)])
    assert detect_initial_project(filtered) is False


def test_detect_initial_project_false_when_no_files():
    assert detect_initial_project(FilteredDiff(files=[])) is False


def test_should_prompt_initial_project_true_when_llm_would_be_needed():
    filtered = FilteredDiff(files=[_file("a.py", is_new=True), _file("b.py", is_new=True)])
    rule_result = RuleResult(matched=False, message=None, rule_name=None)
    classification = ClassificationResult(score=50, is_simple=False)
    assert should_prompt_initial_project(filtered, rule_result, classification) is True


def test_should_prompt_initial_project_false_for_single_file():
    filtered = FilteredDiff(files=[_file("a.py", is_new=True)])
    rule_result = RuleResult(matched=False, message=None, rule_name=None)
    classification = ClassificationResult(score=50, is_simple=False)
    assert should_prompt_initial_project(filtered, rule_result, classification) is False


def test_should_prompt_initial_project_false_when_rule_engine_already_resolves_it():
    filtered = FilteredDiff(files=[_file("a.py", is_new=True), _file("b.py", is_new=True)])
    rule_result = RuleResult(matched=True, message="chore: update config", rule_name="config_only")
    classification = ClassificationResult(score=10, is_simple=True)
    assert should_prompt_initial_project(filtered, rule_result, classification) is False


def test_should_prompt_initial_project_false_when_classifier_says_simple():
    filtered = FilteredDiff(files=[_file("a.py", is_new=True), _file("b.py", is_new=True)])
    rule_result = RuleResult(matched=False, message=None, rule_name=None)
    classification = ClassificationResult(score=10, is_simple=True)
    assert should_prompt_initial_project(filtered, rule_result, classification) is False
