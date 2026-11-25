# patchlint

A small, beginner-friendly security linter for config files. Every finding tells you **why** it matters and **how to fix it**.

> Status: early (v0.1 in progress). Supports Dockerfiles; GitHub Actions and docker-compose are on the [roadmap](ROADMAP.md).

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
```

Exit code is `1` when findings exist, so it works in CI. Use `--format json` for machine output.

## Contribute in 30 minutes

Each rule is one small file. Pick an issue labelled
[`good first issue`](../../labels/good%20first%20issue), then:

```bash
pip install -e ".[dev]"
patchlint new-rule DL003 add_instead_of_copy   # creates the rule + fixtures
# edit the rule, edit the two fixtures, then:
pytest
```

Full walkthrough: [CONTRIBUTING.md](CONTRIBUTING.md).

## Project layout

```
src/patchlint/
  rules/dockerfile/   one file per rule (DL001_root_user.py ...)
  parsers/            file-format parsers
  core/               rule registry, runner, data types
tests/fixtures/<ID>/{bad,good}/   every rule needs both
```

## License

MIT, see [LICENSE](LICENSE). Report vulnerabilities privately: see [SECURITY.md](SECURITY.md).
