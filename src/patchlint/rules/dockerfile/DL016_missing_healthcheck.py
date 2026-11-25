from __future__ import annotations

from collections.abc import Iterable

from patchlint.core.model import Context, Finding
from patchlint.core.registry import rule


@rule(id="DL016", title="Image declares no HEALTHCHECK", severity="low")
def check(ctx: Context) -> Iterable[Finding]:
    """The Dockerfile never declares a `HEALTHCHECK`.

    Why it matters: without a health check the container runtime cannot tell a
    running process from a working one. A service that hangs, deadlocks or
    loses its database connection stays "up", keeps receiving traffic, and the
    failure surfaces to users instead of to your orchestration layer.

    Fix: declare a check that actually probes the service.

        HEALTHCHECK --interval=30s --timeout=3s \\
            CMD curl -fsS http://localhost:8000/health || exit 1

    Note that `HEALTHCHECK NONE` also reports here: it explicitly removes the
    check a base image may have inherited, which is the same outcome.
    """
    if not ctx.instructions:
        return

    if any(ins.cmd == "HEALTHCHECK" for ins in ctx.instructions):
        return

    last = ctx.instructions[-1]
    yield ctx.finding(
        last.line,
        "This Dockerfile declares no `HEALTHCHECK`, so a hung or dead service "
        "still looks healthy to the runtime.",
        "Add a check that probes the service, e.g. "
        "`HEALTHCHECK CMD curl -fsS http://localhost:8000/health || exit 1`.",
    )
