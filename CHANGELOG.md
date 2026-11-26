# Changelog

All notable changes are listed here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.5.0] - 2026-11-27

### Added
- GitHub Action (`uses: RubahAnomali/patchlint@<sha>`) that installs patchlint from the pinned commit, scans, and uploads SARIF to code scanning (thanks @PrathamShenoy14).

## [0.4.0] - 2026-11-26

### Added
- docker-compose rules:
  - `DC005` service adds `ALL` or `SYS_ADMIN` through `cap_add` (thanks @UNMFOREVER)
  - `DC007` service sets `pid: host` or `ipc: host` (thanks @UNMFOREVER)
- Dockerfile rule `DL006` `apt-get update` in its own `RUN` layer (thanks @UNMFOREVER)

## [0.3.0] - 2026-11-26

### Added
- docker-compose rules:
  - `DC003` service uses the host network (thanks @techkayacodes; case-insensitive matching from @UNMFOREVER)
  - `DC004` credential written literally into a service's `environment` (thanks @UNMFOREVER)
  - `DC008` `security_opt` turns off seccomp or AppArmor (thanks @UNMFOREVER)
- Dockerfile rule `DL016` image declares no `HEALTHCHECK` (thanks @ljw1558)
- `python -m patchlint` works the same as the `patchlint` command.

## [0.2.0] - 2026-11-25

### Added
- **docker-compose support:** `compose.yml`, `docker-compose.yml` and variants like `docker-compose.prod.yml` are scanned anywhere in the tree.
  - `DC001` service runs in privileged mode
  - `DC002` Docker socket mounted into a service
- `patchlint new-rule DC0xx` scaffold and `iter_services()` / `volume_sources()` helpers for compose rules.
- **Rule plugins:** packages can add rules through the `patchlint.rules` entry point; `list-rules` marks them, and a broken or clashing plugin is skipped with a warning ([docs/plugins.md](docs/plugins.md)).

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

[Unreleased]: https://github.com/RubahAnomali/patchlint/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/RubahAnomali/patchlint/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/RubahAnomali/patchlint/releases/tag/v0.1.0
