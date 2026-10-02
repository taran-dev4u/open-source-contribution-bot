"""Unit tests for IssueScout and push notifier."""

from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import patch
import pytest

from src.issue_scout import CandidateIssue
from src.issue_scout import IssueScout
from src.notifier import send_push_notification


def test_candidate_issue_dataclass():
    cand = CandidateIssue(
        repo="test/repo",
        number=42,
        title="Bug in parser",
        url="https://github.com/test/repo/issues/42",
        labels=["bug", "help wanted"],
        created_at="2026-10-01T12:00:00Z",
        comments_count=1,
        is_uncontested=True,
    )
    assert cand.repo == "test/repo"
    assert cand.number == 42
    assert cand.is_uncontested is True


def test_issue_scout_banned_org():
    scout = IssueScout(token="dummy-token")
    candidates = scout.scout_repo("pallets/flask")
    assert candidates == []


def test_issue_scout_scout_repo_mock():
    scout = IssueScout(token="dummy-token")

    mock_issues_resp = MagicMock()
    mock_issues_resp.status_code = 200
    mock_issues_resp.json.return_value = [
        {
            "number": 101,
            "title": "Add feature X",
            "html_url": "https://github.com/org/repo/issues/101",
            "labels": [{"name": "good first issue"}],
            "created_at": "2026-10-01T10:00:00Z",
            "comments": 0,
            "assignees": [],
        },
        # One PR that should be skipped
        {
            "number": 102,
            "title": "PR that came in issues list",
            "pull_request": {},
        },
    ]

    mock_pulls_resp = MagicMock()
    mock_pulls_resp.status_code = 200
    mock_pulls_resp.json.return_value = [{"title": "fix #999", "body": ""}]

    with patch("httpx.Client.get") as mock_get:
        mock_get.side_effect = [mock_pulls_resp, mock_issues_resp]
        candidates = scout.scout_repo("org/repo", labels=["good first issue"])

        assert len(candidates) == 1
        assert candidates[0].number == 101
        assert candidates[0].is_uncontested is True


def test_notifier_without_topic():
    with patch("src.config.config.ntfy_topic", None):
        result = send_push_notification("Title", "Message")
        assert result is False


def test_notifier_with_topic():
    with patch("src.config.config.ntfy_topic", "test-topic"):
        with patch("httpx.post") as mock_post:
            mock_resp = MagicMock()
            mock_resp.raise_for_status.return_value = None
            mock_post.return_value = mock_resp

            result = send_push_notification("Test Alert", "PR merged!", priority="high", tags=["tada"])
            assert result is True
            mock_post.assert_called_once()
