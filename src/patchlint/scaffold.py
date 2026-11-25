"""`patchlint new-rule`: generate a rule file and its fixtures."""

from __future__ import annotations

import re
from pathlib import Path

RULE_TEMPLATE = '''from __future__ import annotations

from collections.abc import Iterable

from patchlint.core.model import Context, Finding
from patchlint.core.registry import rule


@rule(id="{id}", title="{title}", severity="medium", cwe=None)
def check(ctx: Context) -> Iterable[Finding]:
    """One sentence: what pattern this rule flags.

    Why it matters: explain the risk in plain language.

    Fix: show the safe version.
    """
    for ins in ctx.instructions:
        if False:  # TODO: replace with your real condition
            yield ctx.finding(ins.line, "What is wrong.", "How to fix it.")
'''


def new_rule(rule_id: str, slug: str, repo_root: Path) -> list[Path]:
    if not re.fullmatch(r"DL\d{3}", rule_id):
        raise ValueError("rule id must look like DL003 (Dockerfile rules use the DL prefix)")
    if not re.fullmatch(r"[a-z0-9_]+", slug):
        raise ValueError("name must be lower_snake_case, e.g. add_instead_of_copy")
    rule_file = repo_root / "src/patchlint/rules/dockerfile" / f"{rule_id}_{slug}.py"
    bad = repo_root / "tests/fixtures" / rule_id / "bad/Dockerfile"
    good = repo_root / "tests/fixtures" / rule_id / "good/Dockerfile"
    for p in (rule_file, bad, good):
        if p.exists():
            raise FileExistsError(p)
        p.parent.mkdir(parents=True, exist_ok=True)
    rule_file.write_text(
        RULE_TEMPLATE.format(id=rule_id, title=slug.replace("_", " ").capitalize()),
        encoding="utf-8",
    )
    base = "FROM python:3.12-slim\n"
    bad.write_text("# This file MUST trigger the rule.\n" + base, encoding="utf-8")
    good.write_text("# This file must NOT trigger the rule.\n" + base, encoding="utf-8")
    return [rule_file, bad, good]
