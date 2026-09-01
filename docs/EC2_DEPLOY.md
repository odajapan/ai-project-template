# Auto-deploy to a host via a self-hosted GitHub Actions runner

Optional. Use this when the project runs as a long-lived service (a
dashboard, an API) on a host you control, and you want every merge to
`main` to deploy automatically once CI passes. Skip it entirely for CLIs,
libraries, or data pipelines that don't run a persistent service.

## How it fits together

- `.github/workflows/deploy.yml` — triggered by `workflow_run` after the
  `CI` workflow completes successfully on `main` (or manually via
  `workflow_dispatch`). Runs on a **self-hosted** runner.
- `deploy/install_github_runner.sh` — one-time, per host: downloads and
  registers a GitHub Actions runner scoped to this repo, installed as a
  systemd service so it survives reboots.
- `deploy/deploy_ec2.sh` — what the runner actually executes: pull the
  commit CI just tested, reinstall dependencies, restart the service,
  health-check it.
- `deploy/your_project_name.service` — example systemd unit; adjust
  `ExecStart`/`WorkingDirectory` for this project's real entry point.

CI must pass before deploy runs, and the deploy pins to the exact commit
(`TESTED_SHA`) that CI tested — not whatever `main` has moved to by the
time the runner picks up the job. This avoids deploying an untested commit
if a second push lands while the first one is still going through CI.

## One-time setup on the host

1. Provision the host by hand: install conda/Python, clone this repo to a
   persistent path, set up whatever the service needs (env vars, secrets,
   a reverse proxy). This is intentionally not scripted here — it varies
   too much per project to templatize usefully.
2. Give the runner user (e.g. `ubuntu`) NOPASSWD sudo for `systemctl`
   (`deploy_ec2.sh` restarts the service via sudo) and passphrase-less git
   auth for the persistent checkout (a deploy key or PAT — an interactive
   prompt would hang the Actions job).
3. In the repo's GitHub settings, under **Settings → Actions → Fork pull
   request workflows**, require approval before running workflows from
   fork PRs. A self-hosted runner executes whatever a triggered workflow
   says, so an unapproved fork PR must never reach it.
4. Register the runner. The token goes over stdin, not an argument, so it
   never shows up in `ps` or shell history on the deploy host:
   ```bash
   TOKEN=$(gh api -X POST /repos/<org>/<repo>/actions/runners/registration-token --jq .token)
   ssh <deploy-host> \
     'bash ~/path/to/<repo>/deploy/install_github_runner.sh' <<< "$TOKEN"
   ```
5. Verify it's actually online before trusting it:
   ```bash
   gh api /repos/<org>/<repo>/actions/runners
   ```
   Confirm `"status": "online"`. This step is the one most likely to be
   skipped — `deploy.yml` merges cleanly and looks complete, but without a
   registered runner every merge just queues a `Deploy` run that never
   starts (`workflow_run` has no matching `runs-on: self-hosted` runner to
   pick it up). A repo can carry a fully-written, fully-reviewed deploy
   pipeline that has never actually deployed anything.
6. Trigger a manual `workflow_dispatch` run of Deploy and confirm it
   completes successfully end to end before relying on merge-triggered
   deploys.

## Updating the deploy scripts themselves

`deploy.yml`'s "update clone" step pulls the persistent checkout before
running `deploy_ec2.sh`, so a PR that changes `deploy_ec2.sh` takes effect
in the same merge that ships it — no separate rollout step needed.

## Deregistering a runner

```bash
TOKEN=$(gh api -X POST /repos/<org>/<repo>/actions/runners/remove-token --jq .token)
ssh <deploy-host> \
  'cd ~/actions-runner/your_project_name && sudo ./svc.sh uninstall && ./config.sh remove --token '"$TOKEN"
```
