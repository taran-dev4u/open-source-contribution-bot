"""Candidate issue scout for maintained open-source repositories."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import httpx

from src.config import config

logger = logging.getLogger(__name__)

BANNED_ORGS = {"pallets", "gentoo", "Homebrew", "Debian", "torvalds"}


@dataclass
class CandidateIssue:
    repo: str
    number: int
    title: str
    url: str
    labels: list[str]
    created_at: str
    comments_count: int
    is_uncontested: bool = True


class IssueScout:
    def __init__(self, token: str | None = None):
        self.token = token if token is not None else config.gh_token
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "open-source-contribution-bot/0.1.0",
        }
        if self.token:
            self.headers["Authorization"] = f"Bearer {self.token}"

    def scout_repo(self, repo: str, labels: list[str] | None = None) -> list[CandidateIssue]:
        """Scout a single repository for uncontested, high-quality candidate issues."""
        org = repo.split("/")[0]
        if org in BANNED_ORGS:
            logger.info("Skipping banned organization: %s", org)
            return []

        labels = labels or ["good first issue", "help wanted"]
        candidates: list[CandidateIssue] = []

        try:
            with httpx.Client(headers=self.headers, timeout=15.0) as client:
                # Fetch recent open PRs once per repo using core REST API (avoids search API rate limits)
                open_prs_resp = client.get(f"https://api.github.com/repos/{repo}/pulls?state=open&per_page=50")
                open_prs_text = ""
                if open_prs_resp.status_code == 200:
                    prs_json = open_prs_resp.json()
                    open_prs_text = " ".join(
                        f"{p.get('title', '')} {p.get('body', '') or ''}" for p in prs_json
                    )

                seen_numbers = set()
                for label in labels:
                    url = f"https://api.github.com/repos/{repo}/issues"
                    params: dict[str, Any] = {
                        "state": "open",
                        "labels": label,
                        "sort": "updated",
                        "direction": "desc",
                        "per_page": 5,
                    }
                    resp = client.get(url, params=params)
                    if resp.status_code != 200:
                        continue

                    issues = resp.json()
                    for item in issues:
                        # Skip PRs (GitHub issues endpoint returns PRs with 'pull_request' key)
                        if "pull_request" in item:
                            continue

                        # Skip assigned issues
                        if item.get("assignees"):
                            continue

                        issue_num = item["number"]
                        if issue_num in seen_numbers:
                            continue
                        seen_numbers.add(issue_num)

                        # Check if any open PR mentions this issue number
                        is_uncontested = True
                        if open_prs_text and (f"#{issue_num}" in open_prs_text or f"issues/{issue_num}" in open_prs_text):
                            is_uncontested = False

                        candidate = CandidateIssue(
                            repo=repo,
                            number=issue_num,
                            title=item.get("title", ""),
                            url=item.get("html_url", ""),
                            labels=[lbl["name"] for lbl in item.get("labels", []) if isinstance(lbl, dict)],
                            created_at=item.get("created_at", ""),
                            comments_count=item.get("comments", 0),
                            is_uncontested=is_uncontested,
                        )
                        candidates.append(candidate)

        except Exception as exc:
            logger.error("Error scouting repo %s: %s", repo, exc)

        return candidates

    def scout_all(self) -> list[CandidateIssue]:
        """Scout all configured repositories."""
        all_candidates: list[CandidateIssue] = []
        for repo in config.scout_repos:
            all_candidates.extend(self.scout_repo(repo))
        return all_candidates
