from __future__ import annotations

import re
from collections.abc import Iterable

from patchlint.core.model import Context, Finding
from patchlint.core.registry import rule
from patchlint.parsers.github_actions import YMap, iter_jobs, iter_steps

FULL_SHA = re.compile(r"[0-9a-f]{40}")


@rule(
    id="GA001",
    title="Action not pinned to a commit SHA",
    severity="medium",
    cwe=829,
    extra_filetypes=("action",),
)
def check(ctx: Context) -> Iterable[Finding]:
    """A step or job uses an action or reusable workflow by tag or branch, not a commit SHA.

    Why it matters: tags and branches can be moved. If an action's repository is
    compromised, a re-pointed tag runs the attacker's code inside your workflow,
    with access to its secrets. This happened to tj-actions/changed-files in 2025.

    Fix: pin to the full 40-character commit SHA and keep the version in a
    comment. Dependabot updates both.

        - uses: actions/checkout@<40-character-sha> # v4.2.2
    """
    doc = ctx.workflow if ctx.workflow is not None else ctx.action
    if doc is None:
        return
    for _job_id, job in iter_jobs(doc):
        yield from _check_uses(ctx, job)  # reusable workflow: jobs.<id>.uses
    for _job_id, step in iter_steps(doc):
        yield from _check_uses(ctx, step)


def _check_uses(ctx: Context, node: YMap) -> Iterable[Finding]:
    uses = node.get("uses")
    if not isinstance(uses, str) or uses.startswith(("./", "docker://")):
        return  # local actions are part of this repo; docker images need their own rule
    _name, sep, ref = uses.partition("@")
    if not sep or not FULL_SHA.fullmatch(ref):
        yield ctx.finding(
            node.key_lines["uses"],
            f"`{uses}` is not pinned to a full commit SHA.",
            "Pin it, e.g. `owner/action@<40-character-sha> # v1.2.3`.",
        )
