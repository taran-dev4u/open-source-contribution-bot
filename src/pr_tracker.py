"""Portfolio pull request tracker and upstream fork synchronizer."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any
import httpx

from src.config import MonitoredPR
from src.config import config
from src.notifier import send_push_notification

logger = logging.getLogger(__name__)


@dataclass
class PRStatusResult:
    pr: MonitoredPR
    state: str  # "OPEN", "MERGED", "CLOSED"
    title: str
    merged_at: str | None
    merge_commit_sha: str | None
    comments_count: int
    latest_comment: str | None
    review_decision: str | None
    fork_synced: bool = False
    branch_deleted: bool = False
    error: str | None = None


class PRTracker:
    def __init__(self, token: str | None = None):
        self.token = token or config.gh_token
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "open-source-contribution-bot/0.1.0",
        }
        if self.token:
            self.headers["Authorization"] = f"Bearer {self.token}"

    def check_pr(self, pr: MonitoredPR) -> PRStatusResult:
        """Check status of a single monitored PR."""
        url = f"https://api.github.com/repos/{pr.upstream_repo}/pulls/{pr.pr_number}"
        try:
            with httpx.Client(headers=self.headers, timeout=15.0) as client:
                resp = client.get(url)
                if resp.status_code == 404:
                    return PRStatusResult(
                        pr=pr,
                        state="NOT_FOUND",
                        title="",
                        merged_at=None,
                        merge_commit_sha=None,
                        comments_count=0,
                        latest_comment=None,
                        review_decision=None,
                        error="PR not found",
                    )
                resp.raise_for_status()
                data = resp.json()

                merged_at = data.get("merged_at")
                state = "MERGED" if merged_at else data.get("state", "open").upper()
                title = data.get("title", "")
                merge_commit_sha = data.get("merge_commit_sha")
                comments_count = data.get("comments", 0) + data.get("review_comments", 0)

                # Fetch reviews if open
                review_decision = None
                latest_comment = None
                if state == "OPEN":
                    reviews_resp = client.get(f"{url}/reviews")
                    if reviews_resp.status_code == 200:
                        reviews = reviews_resp.json()
                        if reviews:
                            latest_review = reviews[-1]
                            review_decision = latest_review.get("state")

                result = PRStatusResult(
                    pr=pr,
                    state=state,
                    title=title,
                    merged_at=merged_at,
                    merge_commit_sha=merge_commit_sha,
                    comments_count=comments_count,
                    latest_comment=latest_comment,
                    review_decision=review_decision,
                )

                if state == "MERGED":
                    self._handle_merged_pr(client, result)

                return result

        except Exception as exc:
            logger.error("Error checking PR %s#%d: %s", pr.upstream_repo, pr.pr_number, exc)
            return PRStatusResult(
                pr=pr,
                state="ERROR",
                title="",
                merged_at=None,
                merge_commit_sha=None,
                comments_count=0,
                latest_comment=None,
                review_decision=None,
                error=str(exc),
            )

    def _handle_merged_pr(self, client: httpx.Client, result: PRStatusResult) -> None:
        """Sync fork default branch and delete merged feature branch."""
        pr = result.pr
        send_push_notification(
            title=f"🎉 PR #{pr.pr_number} MERGED upstream!",
            message=f"{pr.upstream_repo} #{pr.pr_number}: '{result.title}' has been merged!\nSyncing fork {pr.fork_repo}...",
            priority="high",
            tags=["tada", "rocket", "party_popper"],
        )

        if not self.token:
            logger.warning("No GitHub token available to sync fork %s", pr.fork_repo)
            return

        # 1. Sync fork with upstream default branch
        sync_url = f"https://api.github.com/repos/{pr.fork_repo}/merge-upstream"
        try:
            sync_resp = client.post(sync_url, json={"branch": pr.default_branch})
            if sync_resp.status_code in (200, 201):
                logger.info("Fork %s [%s] successfully synced with upstream", pr.fork_repo, pr.default_branch)
                result.fork_synced = True
            elif sync_resp.status_code == 409:
                logger.info("Fork %s is already up to date with upstream", pr.fork_repo)
                result.fork_synced = True
            else:
                logger.warning("Fork sync returned %d: %s", sync_resp.status_code, sync_resp.text)
        except Exception as exc:
            logger.error("Failed to sync fork %s: %s", pr.fork_repo, exc)

        # 2. Delete remote feature branch
        branch_ref_url = f"https://api.github.com/repos/{pr.fork_repo}/git/refs/heads/{pr.head_branch}"
        try:
            del_resp = client.delete(branch_ref_url)
            if del_resp.status_code in (204, 200):
                logger.info("Deleted remote feature branch %s on %s", pr.head_branch, pr.fork_repo)
                result.branch_deleted = True
            elif del_resp.status_code == 404:
                logger.info("Feature branch %s on %s already deleted", pr.head_branch, pr.fork_repo)
                result.branch_deleted = True
            else:
                logger.warning("Branch delete returned %d: %s", del_resp.status_code, del_resp.text)
        except Exception as exc:
            logger.error("Failed to delete branch %s: %s", pr.head_branch, exc)

    def check_all(self) -> list[PRStatusResult]:
        """Check all configured PRs."""
        return [self.check_pr(pr) for pr in config.monitored_prs]
