"""`patchlint new-rule`: generate a rule file and its fixtures."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

HEADER = '''from __future__ import annotations

from collections.abc import Iterable

from patchlint.core.model import Context, Finding
from patchlint.core.registry import rule
'''

DOCSTRING = '''    """One sentence: what pattern this rule flags.

    Why it matters: explain the risk in plain language.

    Fix: show the safe version.
    """'''

DOCKERFILE_BODY = '''

@rule(id="{id}", title="{title}", severity="medium", cwe=None)
def check(ctx: Context) -> Iterable[Finding]:
{doc}
    for ins in ctx.instructions:
        if False:  # TODO: replace with your real condition
            yield ctx.finding(ins.line, "What is wrong.", "How to fix it.")
'''

WORKFLOW_BODY = '''from patchlint.parsers.github_actions import iter_steps


@rule(id="{id}", title="{title}", severity="medium", cwe=None)
def check(ctx: Context) -> Iterable[Finding]:
{doc}
    if ctx.workflow is None:
        return
    for _job_id, step in iter_steps(ctx.workflow):
        if False:  # TODO: replace with your real condition
            yield ctx.finding(step.line, "What is wrong.", "How to fix it.")
'''


@dataclass(frozen=True)
class Kind:
    folder: str
    fixture_name: str
    fixture_text: str
    body: str


KINDS = {
    "DL": Kind("dockerfile", "Dockerfile", "FROM python:3.12-slim\n", DOCKERFILE_BODY),
    "GA": Kind(
        "github_actions",
        "workflow.yml",
        "on: push\npermissions: read-all\njobs:\n  build:\n    runs-on: ubuntu-latest\n"
        "    steps:\n      - run: echo hello\n",
        WORKFLOW_BODY,
    ),
}


def new_rule(rule_id: str, slug: str, repo_root: Path) -> list[Path]:
    if not re.fullmatch(r"(DL|GA)\d{3}", rule_id):
        raise ValueError("rule id must look like DL003 (Dockerfile) or GA003 (GitHub Actions)")
    if not re.fullmatch(r"[a-z0-9_]+", slug):
        raise ValueError("name must be lower_snake_case, e.g. add_instead_of_copy")
    kind = KINDS[rule_id[:2]]
    rule_file = repo_root / "src/patchlint/rules" / kind.folder / f"{rule_id}_{slug}.py"
    bad = repo_root / "tests/fixtures" / rule_id / "bad" / kind.fixture_name
    good = repo_root / "tests/fixtures" / rule_id / "good" / kind.fixture_name
    for p in (rule_file, bad, good):
        if p.exists():
            raise FileExistsError(p)
        p.parent.mkdir(parents=True, exist_ok=True)
    title = slug.replace("_", " ").capitalize()
    body = kind.body.format(id=rule_id, title=title, doc=DOCSTRING)
    rule_file.write_text(HEADER + body, encoding="utf-8")
    bad_note = "# This file MUST trigger the rule.\n"
    good_note = "# This file must NOT trigger the rule.\n"
    bad.write_text(bad_note + kind.fixture_text, encoding="utf-8")
    good.write_text(good_note + kind.fixture_text, encoding="utf-8")
    return [rule_file, bad, good]
