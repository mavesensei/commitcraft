from unittest.mock import patch

from typer.testing import CliRunner

from commitcraft.analysis.grouper import CommitGroup
from commitcraft.cli import app
from commitcraft.config.models import CommitcraftConfig, ProviderName
from commitcraft.git.diff_parser import DiffFile

runner = CliRunner()

STAGED_DIFF = "diff --git a/a.py b/a.py\n"


def _diff_file(path: str) -> DiffFile:
    return DiffFile(
        path=path, file_type="python", is_new=False, is_deleted=False,
        added_lines=1, removed_lines=0, raw_hunks="+pass",
        has_function_changes=False, has_class_changes=False,
    )


def test_split_flag_commits_each_accepted_group():
    group1 = CommitGroup(
        files=[_diff_file("a.py")], message="feat: add a", source="ollama", label="feat: add a"
    )
    group2 = CommitGroup(
        files=[_diff_file("b.py")], message="feat: add b", source="ollama", label="feat: add b"
    )

    with (
        patch("commitcraft.config.store.load_config", return_value=CommitcraftConfig()),
        patch("commitcraft.git.diff_parser.get_staged_diff", return_value=STAGED_DIFF),
        patch(
            "commitcraft.generators.commit.prepare_split_groups",
            return_value=([], [_diff_file("a.py"), _diff_file("b.py")], False),
        ),
        patch(
            "commitcraft.generators.commit.finish_split_groups",
            return_value=[group1, group2],
        ),
        patch("subprocess.run") as mock_run,
    ):
        result = runner.invoke(app, ["commit", "--split", "--no-stage"], input="y\ny\n")

    assert result.exit_code == 0
    assert "feat: add a" in result.stdout
    assert "feat: add b" in result.stdout
    commit_calls = [c for c in mock_run.call_args_list if c.args[0][1] == "commit"]
    assert len(commit_calls) == 2


def test_split_shows_cost_warning_for_api_provider_and_can_cancel():
    cfg = CommitcraftConfig(provider=ProviderName.OPENAI, openai_api_key="k")

    with (
        patch("commitcraft.config.store.load_config", return_value=cfg),
        patch("commitcraft.git.diff_parser.get_staged_diff", return_value=STAGED_DIFF),
        patch(
            "commitcraft.generators.commit.prepare_split_groups",
            return_value=([], [_diff_file("a.py")], False),
        ),
        patch("commitcraft.generators.commit.finish_split_groups") as mock_finish,
        patch("subprocess.run"),
    ):
        result = runner.invoke(app, ["commit", "--split", "--no-stage"], input="n\n")

    assert result.exit_code == 0
    assert "Split mode will make 1 LLM call" in result.stdout
    mock_finish.assert_not_called()


def test_split_skips_cost_warning_for_ollama():
    cfg = CommitcraftConfig(provider=ProviderName.OLLAMA)
    group = CommitGroup(
        files=[_diff_file("a.py")], message="feat: add a", source="ollama", label="feat: add a"
    )

    with (
        patch("commitcraft.config.store.load_config", return_value=cfg),
        patch("commitcraft.git.diff_parser.get_staged_diff", return_value=STAGED_DIFF),
        patch(
            "commitcraft.generators.commit.prepare_split_groups",
            return_value=([], [_diff_file("a.py")], False),
        ),
        patch("commitcraft.generators.commit.finish_split_groups", return_value=[group]),
        patch("subprocess.run"),
    ):
        result = runner.invoke(app, ["commit", "--split", "--no-stage"], input="y\n")

    assert "LLM call" not in result.stdout
    assert result.exit_code == 0


def test_split_edit_flow_uses_edited_message():
    group = CommitGroup(
        files=[_diff_file("a.py")], message="feat: add a", source="ollama", label="feat: add a"
    )

    with (
        patch("commitcraft.config.store.load_config", return_value=CommitcraftConfig()),
        patch("commitcraft.git.diff_parser.get_staged_diff", return_value=STAGED_DIFF),
        patch(
            "commitcraft.generators.commit.prepare_split_groups",
            return_value=([], [_diff_file("a.py")], False),
        ),
        patch("commitcraft.generators.commit.finish_split_groups", return_value=[group]),
        patch("commitcraft.cli._edit_message", return_value="feat: edited message"),
        patch("subprocess.run") as mock_run,
    ):
        result = runner.invoke(app, ["commit", "--split", "--no-stage"], input="e\n")

    assert result.exit_code == 0
    commit_call = next(c for c in mock_run.call_args_list if c.args[0][1] == "commit")
    assert "feat: edited message" in commit_call.args[0]


def test_split_skip_leaves_group_uncommitted():
    group = CommitGroup(
        files=[_diff_file("a.py")], message="feat: add a", source="ollama", label="feat: add a"
    )

    with (
        patch("commitcraft.config.store.load_config", return_value=CommitcraftConfig()),
        patch("commitcraft.git.diff_parser.get_staged_diff", return_value=STAGED_DIFF),
        patch(
            "commitcraft.generators.commit.prepare_split_groups",
            return_value=([], [_diff_file("a.py")], False),
        ),
        patch("commitcraft.generators.commit.finish_split_groups", return_value=[group]),
        patch("subprocess.run") as mock_run,
    ):
        result = runner.invoke(app, ["commit", "--split", "--no-stage"], input="n\n")

    assert result.exit_code == 0
    assert "skipped" in result.stdout.lower()
    commit_calls = [c for c in mock_run.call_args_list if c.args[0][1] == "commit"]
    assert len(commit_calls) == 0


INITIAL_PROJECT_DIFF = (
    "diff --git a/commitcraft/git/diff_parser.py b/commitcraft/git/diff_parser.py\n"
    "new file mode 100644\n"
    "index 0000000..1234567\n"
    "--- /dev/null\n"
    "+++ b/commitcraft/git/diff_parser.py\n"
    "@@ -0,0 +1,4 @@\n"
    "+def parse_diff(raw):\n"
    "+    pass\n"
    "+\n"
    "+class ParsedDiff:\n"
    "+    pass\n"
    "diff --git a/commitcraft/cli.py b/commitcraft/cli.py\n"
    "new file mode 100644\n"
    "index 0000000..1234567\n"
    "--- /dev/null\n"
    "+++ b/commitcraft/cli.py\n"
    "@@ -0,0 +1,4 @@\n"
    "+def main():\n"
    "+    pass\n"
    "+\n"
    "+class CLI:\n"
    "+    pass\n"
)


def test_plain_commit_offers_split_for_new_project():
    cfg = CommitcraftConfig()
    group1 = CommitGroup(
        files=[_diff_file("commitcraft/git/diff_parser.py")],
        message="feat(diff_parser): implement git diff parser",
        source="ollama", label="x",
    )
    group2 = CommitGroup(
        files=[_diff_file("commitcraft/cli.py")],
        message="feat(cli): initialize CLI",
        source="ollama", label="x",
    )

    with (
        patch("commitcraft.config.store.load_config", return_value=cfg),
        patch(
            "commitcraft.git.diff_parser.get_staged_diff",
            return_value=INITIAL_PROJECT_DIFF,
        ),
        patch(
            "commitcraft.generators.commit.finish_split_groups",
            return_value=[group1, group2],
        ),
        patch("subprocess.run") as mock_run,
    ):
        result = runner.invoke(app, ["commit", "--no-stage"], input="y\ny\ny\n")

    assert result.exit_code == 0
    assert "This looks like a new project" in result.stdout
    commit_calls = [c for c in mock_run.call_args_list if c.args[0][1] == "commit"]
    assert len(commit_calls) == 2


def test_plain_commit_declining_split_falls_back_to_normal_flow():
    cfg = CommitcraftConfig()

    with (
        patch("commitcraft.config.store.load_config", return_value=cfg),
        patch(
            "commitcraft.git.diff_parser.get_staged_diff",
            return_value=INITIAL_PROJECT_DIFF,
        ),
        patch(
            "commitcraft.generators.commit.generate_commit_message",
            return_value=("feat: initial commit", "ollama"),
        ),
        patch("subprocess.run") as mock_run,
    ):
        result = runner.invoke(app, ["commit", "--no-stage"], input="n\ny\n")

    assert result.exit_code == 0
    assert "This looks like a new project" in result.stdout
    commit_calls = [c for c in mock_run.call_args_list if c.args[0][1] == "commit"]
    assert len(commit_calls) == 1
    assert commit_calls[0].args[0] == ["git", "commit", "-m", "feat: initial commit"]


def test_plain_commit_unchanged_when_not_all_new():
    cfg = CommitcraftConfig()
    diff = (
        "diff --git a/README.md b/README.md\n"
        "index 1234567..abcdefg 100644\n"
        "--- a/README.md\n"
        "+++ b/README.md\n"
        "@@ -1,3 +1,4 @@\n"
        " # My Project\n"
        "+Updated description.\n"
    )

    with (
        patch("commitcraft.config.store.load_config", return_value=cfg),
        patch("commitcraft.git.diff_parser.get_staged_diff", return_value=diff),
        patch("subprocess.run") as mock_run,
    ):
        result = runner.invoke(app, ["commit", "--no-stage"], input="y\n")

    assert result.exit_code == 0
    assert "This looks like a new project" not in result.stdout
    commit_calls = [c for c in mock_run.call_args_list if c.args[0][1] == "commit"]
    assert len(commit_calls) == 1
    assert commit_calls[0].args[0] == ["git", "commit", "-m", "docs: update README"]
