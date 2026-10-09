"""Configuration for the Cloud Contribution Bot."""

from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass, field


def _get_default_token() -> str:
    token = os.getenv("GH_PAT") or os.getenv("GITHUB_TOKEN", "")
    if not token and shutil.which("gh"):
        try:
            res = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, timeout=5)
            if res.returncode == 0:
                token = res.stdout.strip()
        except Exception:
            pass
    return token


@dataclass(frozen=True)
class MonitoredPR:
    upstream_repo: str  # e.g. "optuna/optuna"
    fork_repo: str  # e.g. "taran-dev4u/optuna"
    pr_number: int
    head_branch: str
    default_branch: str = "main"


@dataclass(frozen=True)
class MonitoredFork:
    fork_repo: str
    upstream_repo: str
    branch: str = "main"


@dataclass
class BotConfig:
    gh_token: str = field(default_factory=_get_default_token)
    gemini_api_key: str = field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))
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
                pr_number=257,
                head_branch="fix/db-source-ordering-by-primary-key",
                default_branch="main",
            ),
            MonitoredPR(
                upstream_repo="NVIDIA-NeMo/Automodel",
                fork_repo="taran-dev4u/Automodel",
                pr_number=4154,
                head_branch="docs/embedding-biencoder-tutorial",
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

    monitored_forks: list[MonitoredFork] = field(
        default_factory=lambda: [
            MonitoredFork("taran-dev4u/aquascope", "Rekin226/aquascope", "main"),
            MonitoredFork("taran-dev4u/flexmeasures", "FlexMeasures/flexmeasures", "main"),
            MonitoredFork("taran-dev4u/optuna", "optuna/optuna", "master"),
            MonitoredFork("taran-dev4u/aeon", "aeon-toolkit/aeon", "main"),
            MonitoredFork("taran-dev4u/timely-beliefs", "SeitaBV/timely-beliefs", "main"),
            MonitoredFork("taran-dev4u/Automodel", "NVIDIA-NeMo/Automodel", "main"),
            MonitoredFork("taran-dev4u/docling", "docling-project/docling", "main"),
        ]
    )


config = BotConfig()
