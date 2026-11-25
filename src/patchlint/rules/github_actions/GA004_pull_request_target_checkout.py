from __future__ import annotations

from collections.abc import Iterable

from patchlint.core.model import Context, Finding
from patchlint.core.registry import rule
from patchlint.parsers.github_actions import YList, YMap, iter_steps

TRIGGER = "pull_request_target"

UNSAFE_REFS = (
    "github.event.pull_request.head.sha",
    "github.event.pull_request.head.ref",
    "github.head_ref",
)

CHECKOUT = "actions/checkout"


def _listens_for_pr_target(workflow: YMap) -> bool:
    """True when the workflow is triggered by ``pull_request_target``."""
    on = workflow.get("on")
    if isinstance(on, str):
        return on == TRIGGER
    if isinstance(on, YList):
        return any(item == TRIGGER for item in on if isinstance(item, str))
    if isinstance(on, YMap):
        return TRIGGER in on
    return False


@rule(
    id="GA004",
    title="pull_request_target workflow checks out the PR's code",
    severity="high",
    cwe=829,
)
def check(ctx: Context) -> Iterable[Finding]:
    """A ``pull_request_target`` workflow checks out the head of the pull request.

    Why it matters: ``pull_request_target`` runs in the base repository's
    context, with its secrets and a write-scoped ``GITHUB_TOKEN``. Checking out
    ``github.event.pull_request.head.*`` there places code written by the pull
    request author inside that privileged job, so anyone who can open a pull
    request can run arbitrary code with your secrets (the "pwn request"
    pattern).

    Fix: never build or execute the pull request's own code under
    ``pull_request_target``. Check out the base branch and treat the PR as
    data, or move the build into a separate ``pull_request`` workflow that
    receives no secrets.
    """
    if ctx.workflow is None or not _listens_for_pr_target(ctx.workflow):
        return

    for _job_id, step in iter_steps(ctx.workflow):
        uses = step.get("uses")
        if not isinstance(uses, str) or uses.partition("@")[0].strip() != CHECKOUT:
            continue
        options = step.get("with")
        if not isinstance(options, YMap):
            continue
        ref = options.get("ref")
        if not isinstance(ref, str):
            continue
        if not any(pattern in ref for pattern in UNSAFE_REFS):
            continue
        yield ctx.finding(
            options.key_lines.get("ref", step.line),
            f"`pull_request_target` checks out `{ref}`, which is code the pull "
            "request author controls.",
            "Check out the base branch instead and treat the PR as data, or move "
            "the build into a `pull_request` workflow that gets no secrets.",
        )
