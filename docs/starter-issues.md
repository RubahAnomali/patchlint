# Starter issue backlog (copy into GitHub issues)

Label each `good first issue` + `rule` unless noted. Keep 15+ open at all times.
Issue body template:

> **Why:** one sentence of risk (+ source link).
> **Do:** `patchlint new-rule DLxxx <name>`; implement; add bad/good fixtures.
> **Done when:** `pytest`, `ruff`, `mypy` pass. **Time:** about 1 hour. Ask here if stuck.

## Dockerfile rules (DL003 onward)

- DL003 `ADD` used where `COPY` would do (CIS 4.9)
- DL004 `curl | sh` / `wget | bash` in `RUN`
- DL005 `apt-get install` without `--no-install-recommends`
- DL006 `apt-get update` not combined with install in one `RUN`
- DL007 `sudo` used inside `RUN`
- DL008 Secrets passed via `ENV` or `ARG` (names like PASSWORD, TOKEN, KEY)
- DL009 `EXPOSE 22` (SSH in container)
- DL010 `chmod 777` / `chmod -R 777`
- DL011 `pip install` without `--no-cache-dir` (hygiene, low)
- DL012 `pip install` of unpinned packages
- DL013 Missing `HEALTHCHECK` (low)
- DL014 `COPY . .` without a `.dockerignore` next to the Dockerfile
- DL015 `apk add` without `--no-cache`
- DL016 `--privileged`-style capabilities in `RUN` comments/labels (research first)
- DL017 `ENV` containing `http://` package-index URLs (non-TLS)
- DL018 `RUN` uses `--insecure` / `-k` / `--no-check-certificate`
- DL019 Multiple `CMD`/`ENTRYPOINT` (last wins, likely mistake, low)
- DL020 `WORKDIR` with a relative path
- DL021 `FROM` with `--platform` pinned to emulate, low (discuss first)
- DL022 `USER` set to numeric 0 after non-root (regression of DL001)

## Features and tooling (`help wanted`)

- `--severity` filter flag (`--min-severity high`)
- `# patchlint: ignore DL002` inline suppression comments
- SARIF output format
- `.patchlint.toml` config file
- Pre-commit hook definition (`.pre-commit-hooks.yaml`)
- GitHub Action wrapper
- Colour output (respect `NO_COLOR`)
- Windows path handling tests

## Docs

- "Write your first rule" tutorial with screenshots
- Rule reference page generated from docstrings
- Add a "Why this rule" link (CWE URL) to text output
- Translate README (offer your language)
- Record a 2-minute terminal demo for the README
