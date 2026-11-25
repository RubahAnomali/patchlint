# Roadmap

- [x] Rule API, registry, fixture-driven tests, `new-rule` scaffold
- [ ] **v0.1** — 25 Dockerfile rules (CIS Docker Benchmark, Docker best practices), PyPI release
- [ ] v0.2 — GitHub Actions workflow rules
  - [x] Workflow parser with line numbers, GA001 (unpinned actions), GA002 (script injection)
  - [ ] More rules: missing `permissions`, `pull_request_target` checkout, unpinned `docker://` images, and more (see issues labelled `rule`)
- [ ] v0.3 — docker-compose rules (`privileged`, exposed ports, secrets in env)
- [x] SARIF output for GitHub code scanning (`--format sarif`, `-o`, `--exit-zero`)
- [x] Config file (`.patchlint.toml` or `[tool.patchlint]`) to disable rules, exclude paths and set severity
- [ ] Third-party rule packs via entry points

Ideas for rules live in issues labelled `rule`. Open a "Rule proposal" issue to suggest one.
