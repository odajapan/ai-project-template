---
paths:
  - "deploy/**"
  - ".github/workflows/deploy.yml"
---

# EC2 Deploy Rules

`deploy/` and `.github/workflows/deploy.yml` are optional — they only
exist in downstream projects that run a long-lived service (systemd) on
a host with a self-hosted GitHub Actions runner. See
[docs/EC2_DEPLOY.md](../../docs/EC2_DEPLOY.md).

## Conventions

- `deploy_ec2.sh` must be idempotent — it runs on every merge to `main`.
- Pin to `TESTED_SHA` (the commit CI just passed), not a bare `git pull`
  — otherwise a push landing on `main` after CI finishes could deploy
  ahead of its own CI run.
- Never hand-edit the systemd unit on the host — edit `deploy/*.service`
  in the repo and re-run the install step so the unit stays reproducible
  from source.
- Registering the self-hosted runner (`deploy/install_github_runner.sh`)
  is a manual, per-host step that `deploy.yml` cannot trigger for itself.
  After adding or changing this scaffolding, actually SSH in and run it,
  then verify with `gh api /repos/<org>/<repo>/actions/runners` that the
  runner shows `"status": "online"`. Shipping the workflow file alone is
  a silent no-op — merges queue a `Deploy` run that never starts.
