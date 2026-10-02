# Open-Source Cloud Autonomous Contribution Runner

Serverless, 24/7 autonomous open-source portfolio tracker and fork synchronizer running entirely in GitHub's cloud without depending on local machines.

## Architecture

- **Schedule:** Automated GitHub Actions cron executing every 2 hours (`0 */2 * * *`).
- **Zero Local Dependency:** Operates independently of local workstation uptime.
- **Automated Lifecycle Synchronization:**
  - Tracks open pull requests across target repositories (`Optuna`, `AquaScope`, `Aeon`, `FlexMeasures`, `Timely-Beliefs`).
  - Detects upstream maintainer merges and automatically synchronizes fork default branches while pruning merged remote feature branches.
  - Monitors maintainer review requests, comments, and approvals.
- **Real-Time Push Alerts:** Dispatches instant notifications via `ntfy.sh` for maintainer actions and merge milestones.
- **Candidate Issue Scouting:** Discovers and validates uncontested `good first issue` / `help wanted` candidates while applying strict collision and anti-AI race guards.

## Workflow Status

- Status: Active
- Runner: GitHub Hosted `ubuntu-latest`
