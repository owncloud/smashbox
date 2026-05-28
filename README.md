# Smashbox

<!-- OSPO-managed README | Generated: 2026-04-16 | v2 -->

[![License](https://img.shields.io/badge/License-AGPL--3.0-blue.svg)](LICENSE) [![ownCloud OSPO](https://img.shields.io/badge/OSPO-ownCloud-blue)](https://kiteworks.com/opensource)

Smashbox is an end-to-end testing framework for validating the core storage functionality of ownCloud-based service installations. It tests sync client behavior across various scenarios including file synchronization, trashbin and versioning operations, sharing of files and folders, and basic protocol compliance, providing automated regression detection for storage operations.

## Part of Infrastructure / Tooling

Smashbox is part of the [ownCloud](https://github.com/owncloud) testing infrastructure. It can be used interactively from the command line, run continuously via cron jobs, or configured for stress and load testing against any ownCloud-based service.

> **Maintenance notice:** This repository is in maintenance mode. It is a fork of the original smashbox project.

## Getting Started

Follow the steps below to set up and run sync tests.

### Docker Quickstart

Find your localhost ownCloud server IP and run:

```bash
docker run \
  -e SMASHBOX_URL=<ip>:<port>/<path-to-oc> \
  -e SMASHBOX_USERNAME=admin \
  -e SMASHBOX_PASSWORD=admin \
  -e SMASHBOX_ACCOUNT_PASSWORD=admin \
  -e SMASHBOX_TEST_NAME=nplusone \
  -v ~/smashdir:/smashdir \
  -v /tmp:/tmp \
  owncloud/smashbox:build
```

Check run logs:

```bash
cat ~/smashdir/log-test_nplusone.log | grep error
```

Check client logs:

```bash
cat ~/smashdir/test_nplusone/worker0-ocsync.step01.cnt000.log | grep error
```

## Documentation

- [ownCloud Testing Documentation](https://doc.owncloud.com/)
- Test cases are in `lib/` under the naming scheme `test_[name].py`

## Test Reference

Details on the sync test framework and its capabilities:

### What It Tests

- Sync clients in various scenarios (basic sync, conflicts, chunked uploads)
- Trashbin and versioning operations
- Sharing of files and folders (user, group, link, resharing, permissions)
- Etag propagation across shared mounts
- Upload/download performance for small and large files

### Key Test Suites

| Test | Description |
|---|---|
| `test_basicSync.py` | File sync from 1kB to 50MB, with/without local state DB |
| `test_concurrentDirRemove.py` | Directory removal during uploads |
| `test_nplusone.py` | Performance: 100 x 1kB files, or 1 x 60MB file |
| `test_shareDir.py` | Directory sharing between users |
| `test_shareFile.py` | File sharing between users |
| `test_shareGroup.py` | File sharing between users and groups |
| `test_shareLink.py` | Sharing by public link |
| `test_sharePermissions.py` | Permission-based sharing behavior |
| `test_shareMountInit.py` | Shared mount sync and PROPFIND performance |

### Command-Line Usage

```bash
bin/smash --help                           # all options
bin/smash lib/test_basicSync.py            # run a basic test
bin/smash -t 0 lib/test_basicSync.py       # specific test index
bin/smash -o nplusone_nfiles=10 lib/test_nplusone.py  # custom parameters
bin/smash --quiet lib/test_*.py            # run all tests, summaries only
```

### Installation from Source

1. Clone the repository
2. Copy `etc/smashbox.conf.template` to `etc/smashbox.conf`
3. Set `oc_sync_cmd` to the ownCloud sync client location
4. Set `oc_account_password`
5. Install dependencies: `pip install -r requirements.txt`

### Monitoring Integration

Supports `local` and `prometheus` monitoring endpoints. Use `-o monitoring_type=local` or `-o monitoring_type=prometheus` with appropriate endpoint and label flags. Custom monitoring variables can be embedded in tests via `commit_to_monitoring()`.

### Project Layout

```
smashbox/
  bin/          # main test driver (smash) and utilities
  etc/          # configuration (smashbox.conf)
  lib/          # test cases (test_*.py)
  protocol/     # sync protocol tests and documentation
  python/       # test API library and utilities
  server/       # server-side procedures
  client/       # ownCloud client helpers
```

## Community & Support

**[Star](https://github.com/owncloud/smashbox)** this repo and **Watch** for release notifications!

- [ownCloud Website](https://owncloud.com)
- [Community Discussions](https://github.com/orgs/owncloud/discussions)
- [Matrix Chat](https://app.element.io/#/room/#owncloud:matrix.org)
- [Documentation](https://doc.owncloud.com)
- [Enterprise Support](https://owncloud.com/contact-us/)
- [OSPO Home](https://kiteworks.com/opensource)

## Contributing

We welcome contributions! Please read the [Contributing Guidelines](CONTRIBUTING.md)
and our [Code of Conduct](CODE_OF_CONDUCT.md) before getting started.

### Workflow

- **Rebase Early, Rebase Often!** We use a rebase workflow. Always rebase on the target branch before submitting a PR.
- **Dependabot**: Automated dependency updates are managed via Dependabot. Review and merge dependency PRs promptly.
- **Signed Commits**: All commits **must** be PGP/GPG signed. See [GitHub's signing guide](https://docs.github.com/en/authentication/managing-commit-signature-verification).
- **DCO Sign-off**: Every commit must carry a `Signed-off-by` line:
  ```
  git commit -s -S -m "your commit message"
  ```
- **GitHub Actions Policy**: Workflows may only use actions that are (a) owned by `owncloud`, (b) created by GitHub (`actions/*`), or (c) verified in the GitHub Marketplace.

## Security

**Do not open a public GitHub issue for security vulnerabilities.**

Report vulnerabilities at **<https://security.owncloud.com>** -- see [SECURITY.md](SECURITY.md).

Bug bounty: [YesWeHack ownCloud Program](https://yeswehack.com/programs/owncloud-bug-bounty-program)

## License

This project is licensed under the [AGPL-3.0](LICENSE).

## About the ownCloud OSPO

The [Kiteworks Open Source Program Office](https://kiteworks.com/opensource), operating under
the [ownCloud](https://owncloud.com) brand, launched on May 5, 2026, to steward the open source
ecosystem around ownCloud's products. The OSPO ensures transparent governance, license compliance,
community health, and sustainable collaboration between the open source community and
[Kiteworks](https://www.kiteworks.com), which acquired ownCloud in 2023.

- **OSPO Home**: <https://kiteworks.com/opensource>
- **GitHub**: <https://github.com/owncloud>
- **ownCloud**: <https://owncloud.com>

For questions about the OSPO or licensing, contact ospo@kiteworks.com.

### License Migration to Apache 2.0

The OSPO is driving a strategic relicensing of ownCloud repositories toward the
[Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0), following
the [Apache Software Foundation's third-party license policy](https://www.apache.org/legal/resolved.html).

Individual repositories will migrate as their audit is completed. The LICENSE file
in each repo reflects its **current** license status (not the target).

**Current license: AGPL-3.0** (Category X per Apache policy -- cannot be included in Apache-2.0 works).

Migration prerequisites for this repository:

- **CLA/DCO coverage**: All past contributors must have signed agreements permitting relicensing
- **Copyleft dependency audit**: All AGPL/GPL dependencies must be replaced or isolated
- **KDE heritage review**: Any code with KDE-era copyrights requires legal analysis
- **Complete relicensing**: AGPL-3.0 is a strong copyleft license; migration requires full relicensing of all files, not just a header change
