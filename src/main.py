"""Main CLI entrypoint for the Cloud Open-Source Contribution Bot."""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from datetime import timezone
from pathlib import Path

from src.issue_scout import IssueScout
from src.pr_tracker import PRTracker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("contribution_bot")


def run_cycle() -> int:
    """Run one complete monitoring, synchronization, and scouting cycle."""
    logger.info("Starting Open-Source Cloud Contribution Bot cycle...")

    tracker = PRTracker()
    results = tracker.check_all()

    # Build report table
    print("\n=== ACTIVE PULL REQUEST STATUS ===")
    merged_count = 0
    open_count = 0

    markdown_lines = [
        "## 🚀 Open-Source Cloud Contribution Status",
        f"*Run timestamp: {datetime.now(timezone.utc).isoformat()}*",
        "",
        "### 📊 Active Pull Requests",
        "| Repository | PR | Title | Status | Review | Fork Sync |",
        "| :--- | :--- | :--- | :--- | :--- | :--- |",
    ]

    telemetry_data = []

    for r in results:
        status_icon = "🟢" if r.state == "OPEN" else "🎉" if r.state == "MERGED" else "⚪"
        sync_icon = "✅" if r.fork_synced else "—"
        review_str = r.review_decision or "None"

        print(f"[{r.state}] {r.pr.upstream_repo}#{r.pr.pr_number}: {r.title} (Review: {review_str})")
        if r.state == "MERGED":
            merged_count += 1
        elif r.state == "OPEN":
            open_count += 1

        markdown_lines.append(
            f"| `{r.pr.upstream_repo}` | [#{r.pr.pr_number}](https://github.com/{r.pr.upstream_repo}/pull/{r.pr.pr_number}) | {r.title} | {status_icon} `{r.state}` | {review_str} | {sync_icon} |"
        )

        telemetry_data.append({
            "repo": r.pr.upstream_repo,
            "pr": r.pr.pr_number,
            "title": r.title,
            "state": r.state,
            "review": review_str,
            "fork_synced": r.fork_synced,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    # Save telemetry
    data_dir = Path(__file__).resolve().parent.parent / "data"
    data_dir.mkdir(exist_ok=True)
    telemetry_file = data_dir / "portfolio_status.json"
    with open(telemetry_file, "w", encoding="utf-8") as f:
        json.dump(telemetry_data, f, indent=2)

    # Scout for available candidates if any slot opened
    print("\n=== CANDIDATE ISSUE SCOUT ===")
    scout = IssueScout()
    candidates = scout.scout_all()

    uncontested = [c for c in candidates if c.is_uncontested]
    print(f"Found {len(uncontested)} uncontested candidate issues across target repositories.")

    if uncontested:
        markdown_lines.extend([
            "",
            "### 🎯 Uncontested Candidate Issues",
            "| Repository | Issue | Title | Labels |",
            "| :--- | :--- | :--- | :--- |",
        ])
        for c in uncontested[:10]:
            labels_str = ", ".join(f"`{l}`" for l in c.labels)
            markdown_lines.append(f"| `{c.repo}` | [#{c.number}]({c.url}) | {c.title} | {labels_str} |")

    # Export to GitHub Step Summary if running in Actions
    summary_path = os.getenv("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as f:
            f.write("\n".join(markdown_lines) + "\n")

    logger.info("Cycle completed successfully. Active: %d, Merged in this run: %d", open_count, merged_count)
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Open-Source Cloud Contribution Bot")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    args = parser.parse_args()

    sys.exit(run_cycle())


if __name__ == "__main__":
    main()
