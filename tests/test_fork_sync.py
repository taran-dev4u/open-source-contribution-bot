"""Unit tests for ForkSyncEngine."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from src.config import MonitoredFork
from src.fork_sync import ForkSyncEngine, ForkSyncResult


def test_monitored_fork_dataclass():
    fork = MonitoredFork(
        fork_repo="user/test",
        upstream_repo="upstream/test",
        branch="main",
    )
    assert fork.fork_repo == "user/test"
    assert fork.upstream_repo == "upstream/test"
    assert fork.branch == "main"


def test_fork_sync_engine_fast_forward_mock():
    engine = ForkSyncEngine(token="mock-token")
    fork = MonitoredFork(
        fork_repo="user/test",
        upstream_repo="upstream/test",
        branch="main",
    )

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "message": "Successfully fetched and fast-forwarded from upstream.",
        "merge_type": "fast-forward",
        "base_branch": "upstream:main",
    }

    with (
        patch("httpx.Client.post", return_value=mock_resp),
        patch("src.fork_sync.send_push_notification") as mock_notify,
    ):
        res = engine.sync_fork(fork)
        assert isinstance(res, ForkSyncResult)
        assert res.status == "SYNCED"
        assert res.merge_type == "fast-forward"
        mock_notify.assert_called_once()


def test_fork_sync_engine_up_to_date_mock():
    engine = ForkSyncEngine(token="mock-token")
    fork = MonitoredFork(
        fork_repo="user/test",
        upstream_repo="upstream/test",
        branch="main",
    )

    mock_resp = MagicMock()
    mock_resp.status_code = 409
    mock_resp.json.return_value = {
        "message": "This branch is not behind upstream.",
    }

    with patch("httpx.Client.post", return_value=mock_resp):
        res = engine.sync_fork(fork)
        assert res.status == "UP_TO_DATE"
        assert res.merge_type == "none"


def test_fork_sync_no_token():
    engine = ForkSyncEngine(token="")
    fork = MonitoredFork("user/repo", "upstream/repo")
    res = engine.sync_fork(fork)
    assert res.status == "ERROR"
    assert "No GitHub token" in res.message
