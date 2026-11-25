# patchlint

A small, beginner-friendly security linter for config files. Every finding tells you **why** it matters and **how to fix it**.

> Status: early (v0.1 in progress). Supports **Dockerfiles** and **GitHub Actions workflows**; docker-compose is on the [roadmap](ROADMAP.md).

| Files | Found by a directory scan | Rule prefix |
|---|---|---|
| Dockerfiles | `Dockerfile`, `Dockerfile.*`, `*.dockerfile` | `DL` |
| GitHub Actions workflows | `.github/workflows/*.yml` / `*.yaml` | `GA` |

## Install and try

```bash
pip install patchlint        # once published; for now: pip install -e ".[dev]"
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
| `--rule ID` | Only run this rule (repeatable) |

## Show findings in GitHub's Security tab

Upload SARIF to GitHub code scanning, and findings appear as alerts on the right lines, including in pull requests. Add `.github/workflows/patchlint.yml`:

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

## Contribute in 30 minutes

Each rule is one small file. Pick an issue labelled
[`good first issue`](../../labels/good%20first%20issue), then:

```bash
pip install -e ".[dev]"
patchlint new-rule DL003 add_instead_of_copy   # Dockerfile rule + fixtures
patchlint new-rule GA003 missing_permissions   # GitHub Actions rule + fixtures
# edit the rule, edit the two fixtures, then:
pytest
```

Full walkthrough: [CONTRIBUTING.md](CONTRIBUTING.md).

## Project layout

```
src/patchlint/
  rules/dockerfile/       one file per Dockerfile rule (DL001_root_user.py ...)
  rules/github_actions/   one file per workflow rule (GA001_unpinned_action.py ...)
  parsers/                file-format parsers
  core/               rule registry, runner, data types
tests/fixtures/<ID>/{bad,good}/   one file in each; every rule needs both
```

## License

MIT, see [LICENSE](LICENSE). Report vulnerabilities privately: see [SECURITY.md](SECURITY.md).
