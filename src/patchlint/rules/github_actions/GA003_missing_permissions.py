from __future__ import annotations

from collections.abc import Iterable

from patchlint.core.model import Context, Finding
from patchlint.core.registry import rule
from patchlint.parsers.github_actions import iter_jobs


@rule(id="GA003", title="No top-level permissions block", severity="medium", cwe=None)
def check(ctx: Context) -> Iterable[Finding]:
    """A workflow sets no top-level ``permissions`` block.

    Why it matters: without ``permissions:`` the workflow's ``GITHUB_TOKEN``
    inherits the repository default, which can be read-write. A compromised
    step can then push commits or edit releases. GitHub's hardening guide
    recommends declaring least privilege explicitly.

    Fix: declare a top-level block, then widen it per job only where a step
    genuinely needs more.

        permissions: read-all
    """
    workflow = ctx.workflow
    if workflow is None or "permissions" in workflow:
        return

    jobs = list(iter_jobs(workflow))
    if jobs and all("permissions" in job for _job_id, job in jobs):
        return

    line = workflow.key_lines.get("on", workflow.line or 1)
    yield ctx.finding(
        line,
        "The workflow has no top-level `permissions:` block, so `GITHUB_TOKEN` "
        "falls back to the repository default, which may be read-write.",
        "Add `permissions: read-all` at the top level, then grant more only in "
        "the jobs that need it.",
    )
