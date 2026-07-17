from commitcraft.analysis.filters import FilteredDiff


def build_commit_context(filtered: FilteredDiff, recent_commits: list[str]) -> str:
    lines: list[str] = []

    lines.append("=== Changed Files ===")
    for f in filtered.files:
        markers = []
        if f.is_new:
            markers.append("NEW")
        if f.is_deleted:
            markers.append("DELETED")
        if f.has_function_changes:
            markers.append("has function/def changes")
        if f.has_class_changes:
            markers.append("has class changes")
        marker_str = f" [{', '.join(markers)}]" if markers else ""
        lines.append(f"  {f.path} (+{f.added_lines}/-{f.removed_lines}){marker_str}")

    lines.append(
        f"\nTotal: +{filtered.total_added}/-{filtered.total_removed}"
        f" lines across {len(filtered.files)} file(s)"
    )

    if recent_commits:
        lines.append("\n=== Recent Commit Style (follow this format) ===")
        for c in recent_commits[:5]:
            lines.append(f"  {c}")

    lines.append("\n=== Task ===")
    lines.append("Write a single conventional commit message for the changes above.")
    lines.append("Output ONLY the commit message. No explanation.")

    return "\n".join(lines)


def build_pr_context(branch_diff: str, branch_name: str, recent_commits: list[str]) -> str:
    lines: list[str] = []
    lines.append(f"Branch: {branch_name}")
    lines.append("\nRecent commits on this branch:")
    for c in recent_commits[:10]:
        lines.append(f"  {c}")
    lines.append("\n=== Task ===")
    lines.append(
        "Write a GitHub PR description for this branch."
        " Use markdown with ## Summary and ## Changes sections."
    )
    return "\n".join(lines)


def build_release_context(tag_diff: str, tag_range: str) -> str:
    lines: list[str] = [
        f"Release range: {tag_range}",
        "\n=== Task ===",
        "Write structured release notes grouped by: Features, Bug Fixes, Documentation, Other."
        " Use markdown.",
    ]
    return "\n".join(lines)
