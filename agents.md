# agents.md — smashbox

## Repository Overview

Smashbox is a Python-based end-to-end testing framework for validating ownCloud storage functionality. It tests sync clients, trashbin/versioning, sharing, and protocol compliance. Can run interactively, via cron, or for stress/load testing.

- **Classification:** Infrastructure / Tooling
- **Activity Status:** Maintenance
- **License:** AGPL-3.0
- **Language:** Python

## Architecture & Key Paths

- `lib/` — Test case files (`test_[name].py`)
- `bin/` — Executable scripts
- `python/` — Python library code
- `client/` — Sync client helpers
- `etc/` — Configuration files
- `test/` — Additional test infrastructure
- `protocol/` — Protocol test documentation
- `corruption_test/` — Corruption testing scenarios
- `server-tools/` — Server-side utility scripts
- `requirements.txt` — Python dependencies
- `LICENSE` — AGPL-3.0 license file

## Development Conventions

- Test cases follow `test_[name].py` naming convention in `lib/`
- Docker-based execution is the primary workflow
- Test output goes to mounted `smashdir` volume

## Build & Test Commands

```bash
# Docker-based execution (primary method)
docker run \
  -e SMASHBOX_URL=<ip>:<port>/<path-to-oc> \
  -e SMASHBOX_USERNAME=admin \
  -e SMASHBOX_PASSWORD=admin \
  -e SMASHBOX_ACCOUNT_PASSWORD=admin \
  -e SMASHBOX_TEST_NAME=nplusone \
  -v ~/smashdir:/smashdir \
  -v /tmp:/tmp \
  owncloud/smashbox:build

# Check logs
cat ~/smashdir/log-test_nplusone.log | grep error
```

## Important Constraints

- **AGPL-3.0 copyleft license:** This repository is AGPL-3.0. The OSPO Apache 2.0 migration requires auditing this copyleft license before any relicensing.
- **Fork repository:** This is a fork of the original smashbox project, which carries its upstream AGPL-3.0 license.
- **Docker dependency:** Primary execution requires Docker.
- **Maintenance mode:** Active development is minimal; used for ongoing regression testing.


## OSPO Policy Constraints

### GitHub Actions
- **Only** use actions owned by `owncloud`, created by GitHub (`actions/*`), verified on the GitHub Marketplace, or verified by the ownCloud Maintainers.
- Pin all actions to their full commit SHA (not tags): `uses: actions/checkout@<SHA> # vX.Y.Z`
- Never introduce actions from unverified third parties.

### Dependency Management
- Dependabot is configured for automated dependency updates.
- Review and merge Dependabot PRs as part of regular maintenance.
- Do not introduce new dependencies without discussion in an issue first.

### Git Workflow
- **Rebase policy**: Always rebase; never create merge commits. Use `git pull --rebase` and `git rebase` before pushing.
- **Signed commits**: All commits **must** be PGP/GPG signed (`git commit -S -s`).
- **DCO sign-off**: Every commit needs a `Signed-off-by` line (`git commit -s`).
- **Conventional Commits & Squash Merge**: Use the [Conventional Commits](https://www.conventionalcommits.org/) format where the repository enforces it. Many repos use squash merge, where the PR title becomes the commit message on the default branch — apply Conventional Commits format to PR titles as well. A reusable GitHub Actions workflow enforces this.

## Context for AI Agents

- The primary execution method is via Docker containers.
- Test cases are Python scripts in `lib/` following the `test_[name].py` naming convention.
- The framework requires a running ownCloud instance to test against.
- Logs are written to a mounted `smashdir` volume.
- No Makefile or formal build system; relies on Docker and Python requirements.
