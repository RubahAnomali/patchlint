# Roadmap

- [x] Rule API, registry, fixture-driven tests, `new-rule` scaffold
- [x] **v0.1.0** — released on PyPI (7 rules, SARIF, config file)
- [ ] More Dockerfile rules (DL016 `HEALTHCHECK` done; CIS Docker Benchmark, Docker best practices; see issues labelled `rule`)
- [x] **v0.2.0** — GitHub Actions workflow rules, compose support, rule plugins
  - [x] Workflow parser with line numbers, GA001 (unpinned actions), GA002 (script injection)
  - [x] GA003 (missing `permissions`), GA004 (`pull_request_target` checkout), GA008 (`secrets: inherit`)
  - [ ] More rules: unpinned `docker://` images, `write-all` permissions, and more (see issues labelled `rule`)
- [x] **v0.3.0** — docker-compose rules (released on PyPI)
  - [x] Compose file detection, `iter_services()` / `volume_sources()` helpers, DC001 (privileged), DC002 (Docker socket mounted)
  - [x] DC003 (host network), DC004 (secrets in `environment`), DC008 (seccomp/AppArmor off)
  - [ ] More rules: dangerous capabilities, unpinned images, `pid`/`ipc: host`, and more (see issues labelled `rule`)
- [x] SARIF output for GitHub code scanning (`--format sarif`, `-o`, `--exit-zero`)
- [x] Config file (`.patchlint.toml` or `[tool.patchlint]`) to disable rules, exclude paths and set severity
- [x] Third-party rule packs via the `patchlint.rules` entry point ([docs/plugins.md](docs/plugins.md))

Ideas for rules live in issues labelled `rule`. Open a "Rule proposal" issue to suggest one.
