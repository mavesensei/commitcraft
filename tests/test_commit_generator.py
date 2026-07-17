from unittest.mock import MagicMock, patch

from commitcraft.analysis.grouper import CommitGroup
from commitcraft.config.models import CommitcraftConfig, ProviderName
from commitcraft.generators.commit import (
    finish_split_groups,
    generate_commit_message,
    prepare_split_groups,
    should_offer_split,
)
from commitcraft.git.diff_parser import DiffFile

README_DIFF = """diff --git a/README.md b/README.md
index 1234567..abcdefg 100644
--- a/README.md
+++ b/README.md
@@ -1,3 +1,5 @@
 # My Project
+Updated description.
"""

COMPLEX_DIFF = """diff --git a/src/auth.py b/src/auth.py
index 1234567..abcdefg 100644
--- a/src/auth.py
+++ b/src/auth.py
@@ -1,5 +1,15 @@
+def authenticate_user(username: str, password: str):
+    pass
diff --git a/tests/test_auth.py b/tests/test_auth.py
new file mode 100644
--- /dev/null
+++ b/tests/test_auth.py
@@ -0,0 +1,5 @@
+def test_authenticate():
+    pass
"""


def test_simple_diff_uses_rule_engine_no_ai():
    cfg = CommitcraftConfig()
    with patch("commitcraft.generators.commit.get_provider") as mock_provider:
        message, source = generate_commit_message(README_DIFF, cfg)
    mock_provider.assert_not_called()
    assert source == "rule_engine"
    assert message == "docs: update README"


def test_complex_diff_calls_provider():
    cfg = CommitcraftConfig(provider=ProviderName.OLLAMA)
    mock_prov = MagicMock()
    mock_prov.generate_commit_message.return_value = "feat: add user authentication"
    mock_prov.name = "ollama"

    with patch("commitcraft.generators.commit.get_provider", return_value=mock_prov):
        with patch("commitcraft.generators.commit.get_recent_commits", return_value=[]):
            message, source = generate_commit_message(COMPLEX_DIFF, cfg)

    mock_prov.generate_commit_message.assert_called_once()
    assert source == "ollama"
    assert message == "feat: add user authentication"


def test_returns_tuple_of_message_and_source():
    cfg = CommitcraftConfig()
    result = generate_commit_message(README_DIFF, cfg)
    assert isinstance(result, tuple)
    assert len(result) == 2


def test_empty_diff_returns_empty():
    cfg = CommitcraftConfig()
    message, source = generate_commit_message("", cfg)
    assert message == ""
    assert source == "none"


SIMPLE_UNMATCHED_DIFF = """diff --git a/src/utils.py b/src/utils.py
index 1234567..abcdefg 100644
--- a/src/utils.py
+++ b/src/utils.py
@@ -1,3 +1,4 @@
 def helper():
     pass
+    # minor edit
"""


def test_simple_unmatched_diff_no_ai():
    cfg = CommitcraftConfig()
    with patch("commitcraft.generators.commit.get_provider") as mock_provider:
        message, source = generate_commit_message(SIMPLE_UNMATCHED_DIFF, cfg)
    mock_provider.assert_not_called()
    assert source == "rule_engine"
    assert message == "chore: minor changes"


SPLIT_MIXED_DIFF = """diff --git a/README.md b/README.md
index 1234567..abcdefg 100644
--- a/README.md
+++ b/README.md
@@ -1,3 +1,4 @@
 # My Project
+New line.
diff --git a/frontend/landing_page.py b/frontend/landing_page.py
index 1234567..abcdefg 100644
--- a/frontend/landing_page.py
+++ b/frontend/landing_page.py
@@ -1,3 +1,6 @@
+def render_hero():
+    pass
diff --git a/frontend/login_page.py b/frontend/login_page.py
index 1234567..abcdefg 100644
--- a/frontend/login_page.py
+++ b/frontend/login_page.py
@@ -1,3 +1,6 @@
+def render_login_form():
+    pass
diff --git a/package-lock.json b/package-lock.json
index 1234567..abcdefg 100644
--- a/package-lock.json
+++ b/package-lock.json
@@ -1,3 +1,4 @@
 {
+  "lockfileVersion": 2
 }
"""

ALL_RULE_MATCHED_DIFF = """diff --git a/README.md b/README.md
index 1234567..abcdefg 100644
--- a/README.md
+++ b/README.md
@@ -1,3 +1,4 @@
 # My Project
+New line.
diff --git a/config/settings.yaml b/config/settings.yaml
index 1234567..abcdefg 100644
--- a/config/settings.yaml
+++ b/config/settings.yaml
@@ -1,2 +1,3 @@
 key: value
+other: value
"""

NOISE_ONLY_DIFF = """diff --git a/package-lock.json b/package-lock.json
index 1234567..abcdefg 100644
--- a/package-lock.json
+++ b/package-lock.json
@@ -1,3 +1,4 @@
 {
+  "lockfileVersion": 2
 }
"""


def test_prepare_split_groups_buckets_readme_and_bundles_noise():
    cfg = CommitcraftConfig()
    zero_cost_groups, remaining, use_content = prepare_split_groups(SPLIT_MIXED_DIFF, cfg)

    messages = {g.message for g in zero_cost_groups}
    assert "docs: update README" in messages
    assert "chore: update generated/dependency files" in messages
    assert len(zero_cost_groups) == 2

    remaining_paths = {f.path for f in remaining}
    assert remaining_paths == {"frontend/landing_page.py", "frontend/login_page.py"}
    assert use_content is False


def test_prepare_split_groups_all_rule_matched_leaves_nothing_remaining():
    cfg = CommitcraftConfig()
    zero_cost_groups, remaining, use_content = prepare_split_groups(ALL_RULE_MATCHED_DIFF, cfg)

    assert remaining == []
    messages = {g.message for g in zero_cost_groups}
    assert messages == {"docs: update README", "chore: update config"}


def test_prepare_split_groups_noise_only_diff():
    cfg = CommitcraftConfig()
    zero_cost_groups, remaining, use_content = prepare_split_groups(NOISE_ONLY_DIFF, cfg)

    assert remaining == []
    assert len(zero_cost_groups) == 1
    assert zero_cost_groups[0].source == "noise"
    assert use_content is False


def test_should_offer_split_true_for_multi_file_new_project():
    cfg = CommitcraftConfig()
    diff = (
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
    assert should_offer_split(diff, cfg) is True


def test_should_offer_split_false_for_readme_only():
    cfg = CommitcraftConfig()
    assert should_offer_split(README_DIFF, cfg) is False


def _diff_file(path: str, raw_hunks: str = "+pass") -> DiffFile:
    return DiffFile(
        path=path, file_type="python", is_new=False, is_deleted=False,
        added_lines=1, removed_lines=0, raw_hunks=raw_hunks,
        has_function_changes=False, has_class_changes=False,
    )


def test_finish_split_groups_clusters_unrelated_files_separately():
    cfg = CommitcraftConfig(provider=ProviderName.OLLAMA)
    remaining = [_diff_file("frontend/landing_page.py"), _diff_file("frontend/login_page.py")]

    mock_prov = MagicMock()
    mock_prov.name = "ollama"
    mock_prov.describe_change.side_effect = [
        "Updates the hero section of the landing page",
        "Adds password validation to the login form",
    ]
    mock_prov.generate_commit_message.side_effect = [
        "feat(frontend): update hero section",
        "feat(frontend): add login validation",
    ]

    with patch("commitcraft.generators.commit.get_provider", return_value=mock_prov):
        with patch("commitcraft.generators.commit.get_recent_commits", return_value=[]):
            groups = finish_split_groups(remaining, [], cfg, use_content=False)

    assert len(groups) == 2
    assert {g.message for g in groups} == {
        "feat(frontend): update hero section",
        "feat(frontend): add login validation",
    }


def test_finish_split_groups_isolates_failed_describe_call():
    cfg = CommitcraftConfig(provider=ProviderName.OLLAMA)
    remaining = [_diff_file("src/utils.py")]

    mock_prov = MagicMock()
    mock_prov.name = "ollama"
    mock_prov.describe_change.side_effect = Exception("provider timed out")
    mock_prov.generate_commit_message.return_value = "fix: adjust utils helper"

    with patch("commitcraft.generators.commit.get_provider", return_value=mock_prov):
        with patch("commitcraft.generators.commit.get_recent_commits", return_value=[]):
            groups = finish_split_groups(remaining, [], cfg, use_content=False)

    assert len(groups) == 1
    assert groups[0].message == "fix: adjust utils helper"
    assert [f.path for f in groups[0].files] == ["src/utils.py"]


def test_finish_split_groups_zero_calls_when_no_remaining_files():
    cfg = CommitcraftConfig(provider=ProviderName.OPENAI, openai_api_key="k")
    rule_group = CommitGroup(
        files=[_diff_file("README.md")], message="docs: update README",
        source="rule_engine", label="docs: update README",
    )

    with patch("commitcraft.generators.commit.get_provider") as mock_get_provider:
        groups = finish_split_groups([], [rule_group], cfg, use_content=False)

    mock_get_provider.assert_not_called()
    assert groups == [rule_group]


def test_finish_split_groups_truncates_content_to_2000_chars():
    cfg = CommitcraftConfig(provider=ProviderName.OLLAMA)
    remaining = [_diff_file("commitcraft/new_module.py")]

    mock_prov = MagicMock()
    mock_prov.name = "ollama"
    mock_prov.describe_change.return_value = "Implements a new module"
    mock_prov.generate_commit_message.return_value = "feat(new_module): add new module"

    with patch("commitcraft.generators.commit.get_provider", return_value=mock_prov):
        with patch("commitcraft.generators.commit.get_recent_commits", return_value=[]):
            with patch(
                "commitcraft.generators.commit.read_working_file",
                return_value="x" * 5000,
            ):
                finish_split_groups(remaining, [], cfg, use_content=True)

    sent_content = mock_prov.describe_change.call_args[0][0]
    assert len(sent_content) == 2000


def test_finish_split_groups_orders_rule_then_semantic_then_noise_last():
    cfg = CommitcraftConfig(provider=ProviderName.OLLAMA)
    rule_group = CommitGroup(
        files=[_diff_file("README.md")], message="docs: update README",
        source="rule_engine", label="docs: update README",
    )
    noise_group = CommitGroup(
        files=[_diff_file("package-lock.json")],
        message="chore: update generated/dependency files",
        source="noise", label="chore: update generated/dependency files",
    )
    zero_cost_groups = [rule_group, noise_group]
    remaining = [_diff_file("frontend/landing_page.py"), _diff_file("frontend/login_page.py")]

    mock_prov = MagicMock()
    mock_prov.name = "ollama"
    mock_prov.describe_change.side_effect = [
        "Updates the hero section of the landing page",
        "Adds password validation to the login form",
    ]
    mock_prov.generate_commit_message.side_effect = [
        "feat(frontend): update hero section",
        "feat(frontend): add login validation",
    ]

    with patch("commitcraft.generators.commit.get_provider", return_value=mock_prov):
        with patch("commitcraft.generators.commit.get_recent_commits", return_value=[]):
            groups = finish_split_groups(remaining, zero_cost_groups, cfg, use_content=False)

    assert len(groups) == 4
    assert groups[0] is rule_group
    assert {g.message for g in groups[1:3]} == {
        "feat(frontend): update hero section",
        "feat(frontend): add login validation",
    }
    assert all(g.source == "ollama" for g in groups[1:3])
    assert groups[3] is noise_group
