"""Unit tests for the PR tracker and configuration."""

from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import patch
import pytest

from src.config import MonitoredPR
from src.pr_tracker import PRStatusResult
from src.pr_tracker import PRTracker


def test_monitored_pr_dataclass():
    pr = MonitoredPR(
        upstream_repo="test/repo",
        fork_repo="user/repo",
        pr_number=123,
        head_branch="feature",
        default_branch="main",
    )
    assert pr.upstream_repo == "test/repo"
    assert pr.pr_number == 123
    assert pr.default_branch == "main"


def test_pr_tracker_check_pr_mock():
    tracker = PRTracker(token="dummy-token")
    pr = MonitoredPR(
        upstream_repo="test/repo",
        fork_repo="user/repo",
        pr_number=10,
        head_branch="feat/test",
    )

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "state": "open",
        "title": "Fix something",
        "merged_at": None,
        "merge_commit_sha": None,
        "comments": 2,
        "review_comments": 1,
    }

    mock_reviews_resp = MagicMock()
    mock_reviews_resp.status_code = 200
    mock_reviews_resp.json.return_value = [{"state": "APPROVED"}]

    with patch("httpx.Client.get") as mock_get:
        mock_get.side_effect = [mock_resp, mock_reviews_resp]
        result = tracker.check_pr(pr)

        assert isinstance(result, PRStatusResult)
        assert result.state == "OPEN"
        assert result.title == "Fix something"
        assert result.comments_count == 3
        assert result.review_decision == "APPROVED"
