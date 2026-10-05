"""Unit tests for README dashboard generation."""

from __future__ import annotations

from src.config import MonitoredFork, MonitoredPR
from src.dashboard import generate_readme
from src.fork_sync import ForkSyncResult
from src.issue_scout import CandidateIssue
from src.pr_tracker import PRStatusResult


def test_generate_readme_structure():
    pr = MonitoredPR("test/repo", "user/repo", 1, "feat/branch")
    pr_result = PRStatusResult(
        pr=pr,
        state="OPEN",
        title="Sample PR",
        merged_at=None,
        merge_commit_sha=None,
        comments_count=1,
        latest_comment="Nice",
        review_decision="APPROVED",
        ai_analysis="Everything looks clean.",
    )

    fork = MonitoredFork("user/repo", "test/repo")
    fork_result = ForkSyncResult(
        fork=fork,
        status="SYNCED",
        message="Synced",
    )

    issue = CandidateIssue(
        repo="test/repo",
        number=10,
        title="Sample Issue",
        url="https://github.com/test/repo/issues/10",
        labels=["good first issue"],
        created_at="2026-10-01",
        comments_count=0,
    )

    md = generate_readme([pr_result], [fork_result], [issue])

    assert "# 🚀 Open-Source Cloud Autonomous Contribution Engine" in md
    assert "test/repo" in md
    assert "Sample PR" in md
    assert "APPROVED" in md
    assert "Gemini AI Review Advisories" in md
    assert "Everything looks clean." in md
    assert "Sample Issue" in md
