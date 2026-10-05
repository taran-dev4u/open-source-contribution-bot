"""Automated multi-fork upstream synchronizer for cloud autonomous execution."""

from __future__ import annotations

import logging
from dataclasses import dataclass

import httpx

from src.config import MonitoredFork, config
from src.notifier import send_push_notification

logger = logging.getLogger(__name__)


@dataclass
class ForkSyncResult:
    fork: MonitoredFork
    status: str  # "SYNCED", "UP_TO_DATE", "ERROR"
    message: str
    merge_type: str | None = None
    base_branch: str | None = None


class ForkSyncEngine:
    def __init__(self, token: str | None = None):
        self.token = token if token is not None else config.gh_token
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "open-source-contribution-bot/0.1.0",
        }
        if self.token:
            self.headers["Authorization"] = f"Bearer {self.token}"

    def sync_fork(self, fork: MonitoredFork) -> ForkSyncResult:
        """Sync a single fork's default branch with upstream via GitHub REST API."""
        if not self.token:
            return ForkSyncResult(
                fork=fork,
                status="ERROR",
                message="No GitHub token provided; cannot sync fork.",
            )

        url = f"https://api.github.com/repos/{fork.fork_repo}/merge-upstream"
        payload = {"branch": fork.branch}

        try:
            with httpx.Client(headers=self.headers, timeout=20.0) as client:
                resp = client.post(url, json=payload)
                data = resp.json() if resp.status_code != 204 else {}

                if resp.status_code in (200, 201):
                    msg = data.get("message", "Successfully synced with upstream.")
                    merge_type = data.get("merge_type", "fast-forward")
                    base_branch = data.get("base_branch")
                    logger.info("Fork %s [%s] synced: %s", fork.fork_repo, fork.branch, msg)

                    send_push_notification(
                        title=f"🔄 Fork Synced: {fork.fork_repo}",
                        message=f"Synced branch '{fork.branch}' with upstream {fork.upstream_repo} ({merge_type}).",
                        priority="default",
                        tags=["arrows_counterclockwise"],
                    )

                    return ForkSyncResult(
                        fork=fork,
                        status="SYNCED",
                        message=msg,
                        merge_type=merge_type,
                        base_branch=base_branch,
                    )

                elif resp.status_code == 409:
                    msg = data.get("message", "Branch is already up to date with upstream.")
                    logger.debug("Fork %s [%s] is up to date", fork.fork_repo, fork.branch)
                    return ForkSyncResult(
                        fork=fork,
                        status="UP_TO_DATE",
                        message=msg,
                        merge_type="none",
                    )
                else:
                    msg = data.get("message", f"HTTP {resp.status_code}")
                    logger.warning("Fork sync failed for %s: %s", fork.fork_repo, msg)
                    return ForkSyncResult(
                        fork=fork,
                        status="ERROR",
                        message=msg,
                    )

        except Exception as exc:
            logger.error("Exception syncing fork %s: %s", fork.fork_repo, exc)
            return ForkSyncResult(
                fork=fork,
                status="ERROR",
                message=str(exc),
            )

    def sync_all(self) -> list[ForkSyncResult]:
        """Sync all configured forks."""
        return [self.sync_fork(f) for f in config.monitored_forks]
