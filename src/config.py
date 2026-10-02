"""Configuration for the Cloud Contribution Bot."""

from __future__ import annotations

import os
from dataclasses import dataclass
from dataclasses import field


@dataclass(frozen=True)
class MonitoredPR:
    upstream_repo: str  # e.g. "optuna/optuna"
    fork_repo: str  # e.g. "taran-dev4u/optuna"
    pr_number: int
    head_branch: str
    default_branch: str = "main"


@dataclass
class BotConfig:
    gh_token: str = field(default_factory=lambda: os.getenv("GH_PAT") or os.getenv("GITHUB_TOKEN", ""))
    ntfy_topic: str = field(default_factory=lambda: os.getenv("NTFY_TOPIC", ""))
    user_login: str = "taran-dev4u"

    monitored_prs: list[MonitoredPR] = field(
        default_factory=lambda: [
            MonitoredPR(
                upstream_repo="optuna/optuna",
                fork_repo="taran-dev4u/optuna",
                pr_number=6879,
                head_branch="fix/study-summaries-respect-constraints",
                default_branch="master",
            ),
            MonitoredPR(
                upstream_repo="Rekin226/aquascope",
                fork_repo="taran-dev4u/aquascope",
                pr_number=485,
                head_branch="feat/uk-ea-quality-flags",
                default_branch="main",
            ),
            MonitoredPR(
                upstream_repo="aeon-toolkit/aeon",
                fork_repo="taran-dev4u/aeon",
                pr_number=3828,
                head_branch="fix/dtw-mixed-dtypes-itakura-swap",
                default_branch="main",
            ),
            MonitoredPR(
                upstream_repo="FlexMeasures/flexmeasures",
                fork_repo="taran-dev4u/flexmeasures",
                pr_number=2448,
                head_branch="feat/export-per-commodity-costs",
                default_branch="main",
            ),
            MonitoredPR(
                upstream_repo="FlexMeasures/flexmeasures",
                fork_repo="taran-dev4u/flexmeasures",
                pr_number=2484,
                head_branch="fix/app-logging-config-preserve-caplog",
                default_branch="main",
            ),
            MonitoredPR(
                upstream_repo="SeitaBV/timely-beliefs",
                fork_repo="taran-dev4u/timely-beliefs",
                pr_number=247,
                head_branch="feat/series-event-resolution-retention",
                default_branch="main",
            ),
        ]
    )

    scout_repos: list[str] = field(
        default_factory=lambda: [
            "optuna/optuna",
            "Rekin226/aquascope",
            "NVIDIA-NeMo/Automodel",
            "docling-project/docling",
            "aeon-toolkit/aeon",
            "FlexMeasures/flexmeasures",
            "SeitaBV/timely-beliefs",
        ]
    )


config = BotConfig()
