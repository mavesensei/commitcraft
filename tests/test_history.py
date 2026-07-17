import subprocess
from unittest.mock import patch

from commitcraft.git.history import (
    analyze_commit_patterns,
    detect_generic_commits,
    get_all_commits,
    get_branch_commits,
    get_current_branch,
    get_recent_commits,
)


def test_get_recent_commits_returns_list():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = "feat: add login\nfix: null pointer\n"
        mock_run.return_value.returncode = 0
        result = get_recent_commits(n=2)
        assert result == ["feat: add login", "fix: null pointer"]

def test_get_recent_commits_empty_on_error():
    with patch("subprocess.run", side_effect=subprocess.CalledProcessError(128, "git")):
        assert get_recent_commits() == []

def test_get_recent_commits_filters_blank_lines():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = "feat: add login\n\n\nfix: bug\n"
        mock_run.return_value.returncode = 0
        result = get_recent_commits()
        assert "" not in result
        assert len(result) == 2

def test_get_branch_commits_returns_list():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = "feat: branch feature\n"
        mock_run.return_value.returncode = 0
        assert get_branch_commits(base="main") == ["feat: branch feature"]

def test_get_branch_commits_empty_on_error():
    with patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "git")):
        assert get_branch_commits() == []

def test_get_current_branch_returns_branch_name():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = "feature/auth\n"
        mock_run.return_value.returncode = 0
        assert get_current_branch() == "feature/auth"

def test_get_current_branch_returns_head_on_error():
    with patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "git")):
        assert get_current_branch() == "HEAD"

def test_analyze_commit_patterns_counts_types():
    commits = ["feat: add login", "feat: add signup", "fix: null pointer", "chore: update deps"]
    result = analyze_commit_patterns(commits)
    assert result["feat"] == 2
    assert result["fix"] == 1
    assert result["chore"] == 1

def test_analyze_commit_patterns_ignores_non_conventional():
    result = analyze_commit_patterns(["initial commit", "wip", "feat: real change"])
    assert result.get("feat") == 1
    assert "initial" not in result

def test_analyze_commit_patterns_empty_list():
    assert analyze_commit_patterns([]) == {}

def test_detects_initial_commit():
    assert "initial commit" in detect_generic_commits(["initial commit"])

def test_detects_wip():
    assert "wip" in detect_generic_commits(["wip"])

def test_detects_case_insensitive():
    assert "WIP" in detect_generic_commits(["WIP"])
    assert "Initial Commit" in detect_generic_commits(["Initial Commit"])

def test_does_not_flag_conventional_commits():
    commits = ["feat: add auth", "fix: resolve crash", "chore: update deps"]
    assert detect_generic_commits(commits) == []

def test_detects_dots_only():
    assert "..." in detect_generic_commits(["..."])

def test_detects_commit_with_number():
    assert "commit 1" in detect_generic_commits(["commit 1"])

def test_mixed_list_returns_only_generic():
    commits = ["feat: good commit", "wip", "fix: another good one", "update"]
    generic = detect_generic_commits(commits)
    assert "wip" in generic
    assert "update" in generic
    assert "feat: good commit" not in generic

def test_get_all_commits_returns_list():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = "feat: a\nfeat: b\n"
        mock_run.return_value.returncode = 0
        assert len(get_all_commits(n=2)) == 2

def test_get_all_commits_empty_on_error():
    with patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "git")):
        assert get_all_commits() == []
