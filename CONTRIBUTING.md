# Contributing to patchlint

Thanks for helping! New here? Start with an issue labelled `good first issue`.
Comment "I'll take this" to claim it. Unclaimed after 7 days of silence, it returns to the pool.
We aim to reply to every PR within 48 hours.

## Setup

```bash
git clone <your fork>
cd patchlint
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest && ruff check . && mypy
```

## Add a rule (the most common contribution)

The rule id prefix decides which files the rule checks: `DL` for Dockerfiles, `GA` for GitHub Actions workflows, `DC` for docker-compose files.

1. Run the scaffold for the id in your issue:
   - `patchlint new-rule DL003 add_instead_of_copy` creates `src/patchlint/rules/dockerfile/DL003_add_instead_of_copy.py` plus `tests/fixtures/DL003/bad/Dockerfile` and `good/Dockerfile`.
   - `patchlint new-rule GA005 unpinned_docker_action` creates `src/patchlint/rules/github_actions/GA005_unpinned_docker_action.py` plus `tests/fixtures/GA005/bad/workflow.yml` and `good/workflow.yml`.
   - `patchlint new-rule DC005 dangerous_capabilities` creates `src/patchlint/rules/compose/DC005_dangerous_capabilities.py` plus `tests/fixtures/DC005/bad/compose.yml` and `good/compose.yml`.
   - The `bad` file **must** trigger the rule; the `good` file **must not**.
2. Fill in the `@rule(...)` metadata (severity: `low`/`medium`/`high`; CWE if one applies).
3. Implement `check(ctx)` and `yield ctx.finding(line, message, fix)` for each problem:
   - Dockerfile rules loop over `ctx.instructions` (each has `.line`, `.cmd`, `.args`).
   - Workflow rules use `ctx.workflow` with the helpers `iter_jobs()` and `iter_steps()`.
   - Compose rules use `ctx.compose` with `iter_services()` and `volume_sources()` from `patchlint.parsers.compose`.
   - In workflows and compose files, every mapping has `.line` and `.key_lines["some_key"]`, so findings point at the right line.
4. Write the docstring with a "Why it matters" and a "Fix" section. It is the rule's documentation (`patchlint explain DL003`).
5. Run `pytest`. Tests are discovered from fixtures, so you do not write test code for a normal rule.

Model rules: `DL001_root_user.py` (Dockerfile), `GA001_unpinned_action.py` (workflow) and `DC001_privileged_container.py` (compose).

### Rule quality bar

- Low false positives beat catching everything. If unsure, don't flag.
- Message says what is wrong; `fix` says exactly what to do.
- Cite the source (CIS Docker Benchmark, OWASP, GitHub's security hardening guide) in the docstring where relevant.

## Pull requests

- One rule or one change per PR; link the issue (`Closes #12`).
- CI must pass: pytest, ruff, mypy.
- Be kind. See the [Code of Conduct](CODE_OF_CONDUCT.md).

## Not sure where to start?

Open a "Rule proposal" issue or ask in Discussions. No question is too basic.
