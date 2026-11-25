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

1. `patchlint new-rule DL003 add_instead_of_copy` creates:
   - `src/patchlint/rules/dockerfile/DL003_add_instead_of_copy.py`
   - `tests/fixtures/DL003/bad/Dockerfile` (**must** trigger the rule)
   - `tests/fixtures/DL003/good/Dockerfile` (**must not** trigger it)
2. Fill in the `@rule(...)` metadata (severity: `low`/`medium`/`high`; CWE if one applies).
3. Implement `check(ctx)`. Use `ctx.instructions` and `yield ctx.finding(line, message, fix)`.
4. Write the docstring with a "Why it matters" and a "Fix" section. It is the rule's documentation (`patchlint explain DL003`).
5. Run `pytest`. Tests are discovered from fixtures, so you do not write test code for a normal rule.

Look at `DL001_root_user.py` for a model rule.

### Rule quality bar

- Low false positives beat catching everything. If unsure, don't flag.
- Message says what is wrong; `fix` says exactly what to do.
- Cite the source (CIS Docker Benchmark, OWASP, Docker docs) in the docstring where relevant.

## Pull requests

- One rule or one change per PR; link the issue (`Closes #12`).
- CI must pass: pytest, ruff, mypy.
- Be kind. See the [Code of Conduct](CODE_OF_CONDUCT.md).

## Not sure where to start?

Open a "Rule proposal" issue or ask in Discussions. No question is too basic.
