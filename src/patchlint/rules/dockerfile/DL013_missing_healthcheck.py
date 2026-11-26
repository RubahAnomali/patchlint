from __future__ import annotations

from collections.abc import Iterable

from patchlint.core.model import Context, Finding
from patchlint.core.registry import rule

# Instructions that make an image into something you *run*, rather than
# something you build on top of.
RUNNABLE = {"CMD", "ENTRYPOINT"}

# Stages that are clearly build-time only. A stage named `base` or `builder`
# with no CMD/ENTRYPOINT is an artifact producer, not a service.
BUILD_ONLY_HINT = ("builder", "build", "base", "deps", "compile")


@rule(id="DL013", title="no HEALTHCHECK on a runnable image", severity="low", cwe=1188)
def check(ctx: Context) -> Iterable[Finding]:
    """The Dockerfile defines a service (CMD/ENTRYPOINT) but never a HEALTHCHECK.

    Why it matters: without a health check, Docker (and every orchestrator
    built on it) only knows whether the process is *alive*, not whether it
    *works*. A wedged Node process, a deadlocked worker, an app that is up but
    can no longer reach its database -- all of them look perfectly healthy from
    the outside, so traffic keeps flowing to a container that answers nothing.
    A one-line check turns that into a restart, or at least into an honest
    `unhealthy` status. CWE-1188 is insecure default configuration; this is the
    low end of it -- a missing guard rail, not an open door.

    Fix: tell Docker how to tell "up" from "useful":

        HEALTHCHECK --interval=30s --timeout=3s --retries=3 \\
          CMD curl -fsS http://127.0.0.1:8080/healthz || exit 1

    Note: this is only reported for images that can run on their own, i.e. a
    stage with CMD or ENTRYPOINT. Pure build stages (a `builder`/`base` stage
    with neither) are not reported, and neither is a Dockerfile where the
    runnable stage inherits a health check from a parent image we can see.
    """
    if not ctx.instructions:
        return

    has_runnable = False
    ifr_layer = False
    for ins in ctx.instructions:
        if ins.cmd in RUNNABLE:
            has_runnable = True
        elif ins.cmd == "HEALTHCHECK":
            # `HEALTHCHECK NONE` explicitly opts out -- respect the decision.
            if ins.args.strip().upper().startswith("NONE"):
                return
            ifr_layer = True

    if not has_runnable or ifr_layer:
        return

    # A multi-stage file whose last stage is only there to hold artifacts is
    # not a service; say nothing rather than nag the wrong file.
    last_from = None
    for ins in ctx.instructions:
        if ins.cmd == "FROM":
            last_from = ins
    if last_from is not None:
        args = last_from.args.split()
        if len(args) >= 3 and args[1].lower() == "as":
            stage = args[2].lower()
            if any(hint in stage for hint in BUILD_ONLY_HINT):
                return

    entry = next(
        (ins.line for ins in ctx.instructions if ins.cmd in RUNNABLE),
        ctx.instructions[-1].line,
    )
    yield ctx.finding(
        entry,
        "The image can be run (CMD/ENTRYPOINT) but defines no HEALTHCHECK, so "
        "Docker cannot tell a working container from a wedged one.",
        "Add `HEALTHCHECK --interval=30s --timeout=3s --retries=3 CMD <probe> "
        "|| exit 1`, or `HEALTHCHECK NONE` if this image is deliberately a "
        "build-only artifact.",
    )
