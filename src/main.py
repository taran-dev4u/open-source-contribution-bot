"""Main CLI entrypoint for the Cloud Open-Source Contribution Bot."""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

from src.dashboard import generate_readme
from src.fork_sync import ForkSyncEngine
from src.issue_scout import IssueScout
from src.pr_tracker import PRTracker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("contribution_bot")


def run_cycle() -> int:
    """Run one complete monitoring, synchronization, AI analysis, and dashboard cycle."""
    logger.info("Starting Open-Source Cloud Autonomous Contribution Bot cycle...")

    # 1. Multi-Fork Upstream Synchronization
    logger.info("Executing multi-fork upstream synchronization...")
    fork_engine = ForkSyncEngine()
    fork_results = fork_engine.sync_all()
    for fr in fork_results:
        logger.info("[FORK] %s: %s (%s)", fr.fork.fork_repo, fr.status, fr.message)

    # 2. Pull Request Tracking & Review Analysis
    logger.info("Checking active portfolio pull requests...")
    tracker = PRTracker()
    pr_results = tracker.check_all()

    merged_count = 0
    open_count = 0
    telemetry_data = []

    for r in pr_results:
        review_str = r.review_decision or "None"
        logger.info("[%s] %s#%d: %s (Review: %s)", r.state, r.pr.upstream_repo, r.pr.pr_number, r.title, review_str)
        if r.state == "MERGED":
            merged_count += 1
        elif r.state == "OPEN":
            open_count += 1

        telemetry_data.append({
            "repo": r.pr.upstream_repo,
            "pr": r.pr.pr_number,
            "title": r.title,
            "state": r.state,
            "review": review_str,
            "fork_synced": r.fork_synced,
            "ai_analysis": r.ai_analysis,
            "timestamp": datetime.now(UTC).isoformat(),
        })

    # 3. Uncontested Candidate Issue Scouting
    logger.info("Scouting candidate issues across target repositories...")
    scout = IssueScout()
    candidates = scout.scout_all()
    uncontested = [c for c in candidates if c.is_uncontested]
    logger.info("Found %d uncontested candidate issues across target repos.", len(uncontested))

    # 4. Generate README Dashboard & Save Telemetry
    root_dir = Path(__file__).resolve().parent.parent
    readme_path = root_dir / "README.md"
    readme_content = generate_readme(pr_results, fork_results, uncontested)
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(readme_content)

    data_dir = root_dir / "data"
    data_dir.mkdir(exist_ok=True)
    telemetry_file = data_dir / "portfolio_status.json"
    with open(telemetry_file, "w", encoding="utf-8") as f:
        json.dump(telemetry_data, f, indent=2)

    # 5. Export to GitHub Step Summary if running in Actions
    summary_path = os.getenv("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as f:
            f.write(readme_content)

    logger.info(
        "Cycle completed successfully. Active PRs: %d, Merged: %d, Forks: %d, Uncontested Issues: %d",
        open_count,
        merged_count,
        len(fork_results),
        len(uncontested),
    )
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Open-Source Cloud Contribution Bot")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    parser.parse_args()

    sys.exit(run_cycle())


if __name__ == "__main__":
    main()
