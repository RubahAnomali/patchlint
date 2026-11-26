# patchlint

A small, beginner-friendly security linter for config files. Every finding tells you **why** it matters and **how to fix it**.

[![PyPI](https://img.shields.io/pypi/v/patchlint)](https://pypi.org/project/patchlint/) [![CI](https://github.com/RubahAnomali/patchlint/actions/workflows/ci.yml/badge.svg)](https://github.com/RubahAnomali/patchlint/actions/workflows/ci.yml)

> Status: early (v0.4.0), 16 rules. Supports **Dockerfiles**, **GitHub Actions workflows** and **docker-compose files**. See the [roadmap](ROADMAP.md).

| Files | Found by a directory scan | Rule prefix |
|---|---|---|
| Dockerfiles | `Dockerfile`, `Dockerfile.*`, `*.dockerfile` | `DL` |
| GitHub Actions workflows | `.github/workflows/*.yml` / `*.yaml` | `GA` |
| docker-compose files | `compose.yml`, `docker-compose.yml`, `docker-compose.*.yml` (any folder) | `DC` |

## Install and try

```bash
pip install patchlint
patchlint scan .
patchlint list-rules
patchlint explain DL001
```

Example output:

```
Dockerfile:1: [DL001/high] Final stage runs as root (no non-root USER set).
    fix: Add `USER <non-root-user>` after installing packages.
.github/workflows/triage.yml:8: [GA002/high] `github.event.issue.title` is attacker-controlled and is pasted into the script.
    fix: Move it to `env:` and use the variable, quoted, in the script.
```

Exit code is `1` when findings exist, so it works in CI.

| Option | What it does |
|---|---|
| `--format json` | Machine-readable list of findings |
| `--format sarif` | [SARIF 2.1.0](https://docs.oasis-open.org/sarif/sarif/v2.1.0/sarif-v2.1.0.html), for GitHub code scanning and IDEs |
| `-o FILE` | Write the report to a file instead of the terminal |
| `--exit-zero` | Exit `0` even with findings (useful before uploading a report) |
| `--rule ID` | Only run this rule (repeatable); overrides `disable` in the config |
| `--config FILE` / `--no-config` | Use a specific config file, or ignore config files |

## Configuration

Put a `.patchlint.toml` in the folder you scan (or a `[tool.patchlint]` table in `pyproject.toml`):

```toml
disable = ["DL002"]              # turn rules off
exclude = ["tests/fixtures/*"]   # skip paths (globs relative to the scanned folder; * also matches /)

[severity]                       # change a rule's severity: low, medium or high
GA001 = "high"
```

Unknown keys, rule ids or severities stop the scan with an error that says what to fix, so typos never silently disable checks.

## Show findings in GitHub's Security tab

Upload SARIF to GitHub code scanning, and findings appear as alerts on the right lines, including in pull requests. The easiest way is the patchlint action. Add `.github/workflows/patchlint.yml`:

```yaml
name: patchlint
on:
  push:
    branches: [main]
  pull_request:
permissions:
  contents: read
jobs:
  scan:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      security-events: write   # needed to upload SARIF
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with:
          persist-credentials: false
      - uses: RubahAnomali/patchlint@b9f43767f297b686d9625756afd30df666dc0e88 # v0.4.0
```

| Input | Default | What it does |
| --- | --- | --- |
| `path` | `.` | File or folder to scan. |
| `format` | `sarif` | `text`, `json` or `sarif`. Must be `sarif` when `upload-sarif` is `true`. |
| `upload-sarif` | `true` | Upload the SARIF report to code scanning. The job needs `security-events: write`. |

With `upload-sarif: true`, findings become code scanning alerts and the job does not fail. With `upload-sarif: false`, nothing is uploaded and the step fails when there are findings.

Without the action:

```yaml
name: patchlint
on:
  push:
    branches: [main]
  pull_request:
permissions:
  contents: read
jobs:
  scan:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      security-events: write   # needed to upload SARIF
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with:
          persist-credentials: false
      - uses: actions/setup-python@6d4fd22b20465ccc0f7354476588e8df7c9ca0e0 # v7.1.0
        with:
          python-version: "3.12"
      - run: pip install patchlint
      - run: patchlint scan . --format sarif -o patchlint.sarif --exit-zero
      - uses: github/codeql-action/upload-sarif@915412ff23e8b7659517e607487dbeae018f2934 # v4.39.5
        with:
          sarif_file: patchlint.sarif
```

Code scanning is free for public repositories. The actions are pinned to commit SHAs, which is what rule GA001 asks for.

## Rule plugins

Company- or project-specific rules can live in their own package and are loaded automatically through the `patchlint.rules` entry point. See [docs/plugins.md](docs/plugins.md).

## Contribute in 30 minutes

Each rule is one small file. Pick an issue labelled
[`good first issue`](../../labels/good%20first%20issue), then:

```bash
pip install -e ".[dev]"
patchlint new-rule DL003 add_instead_of_copy      # Dockerfile rule + fixtures
patchlint new-rule GA005 unpinned_docker_action   # GitHub Actions rule + fixtures
patchlint new-rule DC005 dangerous_capabilities   # docker-compose rule + fixtures
# edit the rule, edit the two fixtures, then:
pytest
```

Full walkthrough: [CONTRIBUTING.md](CONTRIBUTING.md).

## Project layout

```
src/patchlint/
  rules/dockerfile/       one file per Dockerfile rule (DL001_root_user.py ...)
  rules/github_actions/   one file per workflow rule (GA001_unpinned_action.py ...)
  rules/compose/          one file per docker-compose rule (DC001_privileged_container.py ...)
  parsers/                file-format parsers
  core/               rule registry, runner, data types
tests/fixtures/<ID>/{bad,good}/   one file in each; every rule needs both
```

## License

MIT, see [LICENSE](LICENSE). Report vulnerabilities privately: see [SECURITY.md](SECURITY.md).
