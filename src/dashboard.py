"""Live GitHub README dashboard generator for the cloud autonomous runner."""

from __future__ import annotations

from datetime import UTC, datetime

from src.fork_sync import ForkSyncResult
from src.issue_scout import CandidateIssue
from src.pr_tracker import PRStatusResult


def generate_readme(
    pr_results: list[PRStatusResult],
    fork_results: list[ForkSyncResult],
    candidate_issues: list[CandidateIssue],
) -> str:
    """Generate professional, real-time Markdown dashboard for README.md."""
    now_utc = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")

    open_prs = [p for p in pr_results if p.state == "OPEN"]
    merged_prs = [p for p in pr_results if p.state == "MERGED"]
    synced_forks = [f for f in fork_results if f.status == "SYNCED"]

    lines = [
        "# 🚀 Open-Source Cloud Autonomous Contribution Engine",
        "",
        "[![Cloud Runner](https://github.com/taran-dev4u/open-source-contribution-bot/actions/workflows/cloud-runner.yml/badge.svg)](https://github.com/taran-dev4u/open-source-contribution-bot/actions/workflows/cloud-runner.yml)",
        "![Status](https://img.shields.io/badge/Status-Operational%2024%2F7-brightgreen)",
        "![Architecture](https://img.shields.io/badge/Architecture-Serverless%20Cloud-blue)",
        "",
        "Autonomous open-source portfolio maintenance, upstream synchronization, and issue scouting running 24/7 via GitHub Actions and Google Gemini AI.",
        "",
        "---",
        "",
        "## 📊 Real-Time Portfolio Summary",
        "",
        f"- **Last Cloud Execution:** `{now_utc}`",
        f"- **Active Monitored Pull Requests:** `{len(open_prs)}`",
        f"- **Total Successfully Merged:** `{len(merged_prs)}`",
        f"- **Upstream Forks Synchronized:** `{len(fork_results)}` (Synced: `{len(synced_forks)}`, Up-to-Date: `{len(fork_results) - len(synced_forks)}`)",
        f"- **Uncontested Issues Scouted:** `{len(candidate_issues)}`",
        "",
        "---",
        "",
        "## 🌿 Active Pull Requests Across Repositories",
        "",
        "| Repository | PR | Title | State | Review | Fork Sync |",
        "| :--- | :--- | :--- | :--- | :--- | :--- |",
    ]

    for p in pr_results:
        status_badge = (
            "🟢 `OPEN`" if p.state == "OPEN"
            else "🎉 `MERGED`" if p.state == "MERGED"
            else f"`{p.state}`"
        )
        review_badge = (
            "⚠️ `CHANGES_REQUESTED`" if p.review_decision == "CHANGES_REQUESTED"
            else "✅ `APPROVED`" if p.review_decision == "APPROVED"
            else f"`{p.review_decision}`" if p.review_decision
            else "⚪ `AWAITING`"
        )
        sync_badge = "✅ Synced" if p.fork_synced else "—"
        pr_link = f"[#{p.pr.pr_number}](https://github.com/{p.pr.upstream_repo}/pull/{p.pr.pr_number})"

        lines.append(
            f"| `{p.pr.upstream_repo}` | {pr_link} | {p.title} | {status_badge} | {review_badge} | {sync_badge} |"
        )

    # Add AI review advisories if present
    ai_advisories = [p for p in pr_results if p.ai_analysis]
    if ai_advisories:
        lines.extend([
            "",
            "### 🤖 Gemini AI Review Advisories",
            "",
        ])
        for p in ai_advisories:
            lines.extend([
                f"#### `{p.pr.upstream_repo}#{p.pr.pr_number}`: {p.title}",
                "",
                "```markdown",
                p.ai_analysis,
                "```",
                "",
            ])

    lines.extend([
        "",
        "---",
        "",
        "## 🔄 Multi-Fork Upstream Synchronization Status",
        "",
        "| Fork Repository | Upstream | Default Branch | Sync Status |",
        "| :--- | :--- | :--- | :--- |",
    ])

    for f in fork_results:
        status_str = (
            "✅ Fast-forwarded" if f.status == "SYNCED"
            else "✔️ Up to date" if f.status == "UP_TO_DATE"
            else f"❌ {f.message}"
        )
        lines.append(f"| `{f.fork.fork_repo}` | `{f.fork.upstream_repo}` | `{f.fork.branch}` | {status_str} |")

    if candidate_issues:
        lines.extend([
            "",
            "---",
            "",
            "## 🎯 Uncontested Candidate Issues (Next Up)",
            "",
            "| Repository | Issue | Title | Labels |",
            "| :--- | :--- | :--- | :--- |",
        ])
        for c in candidate_issues[:10]:
            labels_str = " ".join(f"`{label}`" for label in c.labels[:3])
            lines.append(f"| `{c.repo}` | [#{c.number}]({c.url}) | {c.title} | {labels_str} |")

    lines.extend([
        "",
        "---",
        "",
        "## ⚙️ Architecture & Automation Lifecycle",
        "",
        "1. **Continuous Serverless Schedule:** GitHub Actions executes every 2 hours (24/7) with zero local workstation dependence.",
        "2. **Multi-Fork Fast-Forwarding:** Calls GitHub REST API to merge upstream changes to forks automatically.",
        "3. **CI & Review Monitoring:** Polls active PR status and inspects maintainer reviews.",
        "4. **AI Review Remediation:** On `CHANGES_REQUESTED`, Gemini generates direct, human-standard remediation steps.",
        "5. **Candidate Scouting:** Scans curated target repos for uncontested issues without competing PRs.",
        "",
        "*Maintained autonomously by [open-source-contribution-bot](https://github.com/taran-dev4u/open-source-contribution-bot).* ",
    ])

    return "\n".join(lines) + "\n"
