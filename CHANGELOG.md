# Changelog

All notable changes are listed here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.1.0] - 2026-11-25

First public release.

### Added
- Scans **Dockerfiles** and **GitHub Actions workflows**; every finding explains why it matters and how to fix it.
- Rules:
  - `DL001` container runs as root
  - `DL002` base image not pinned
  - `GA001` action not pinned to a commit SHA
  - `GA002` untrusted input in a `run:` script (script injection)
  - `GA003` no top-level `permissions:` block (thanks @ljw1558)
  - `GA004` `pull_request_target` workflow checks out the pull request's code (thanks @ljw1558)
  - `GA008` `secrets: inherit` to a reusable workflow in another repository (thanks @SVR1339)
- Output as text, JSON or SARIF 2.1.0 (`--format sarif`) for GitHub code scanning; `-o FILE` and `--exit-zero`.
- Configuration in `.patchlint.toml` or `[tool.patchlint]`: `disable`, `exclude` and per-rule `[severity]`, with strict validation.
- `patchlint new-rule` scaffold for contributors; fixture-driven tests need no test code per rule.

[Unreleased]: https://github.com/RubahAnomali/patchlint/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/RubahAnomali/patchlint/releases/tag/v0.1.0
