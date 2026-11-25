from __future__ import annotations

from collections.abc import Iterable

from patchlint.core.model import Context, Finding
from patchlint.core.registry import rule


@rule(id="DL001", title="Container runs as root", severity="high", cwe=250)
def check(ctx: Context) -> Iterable[Finding]:
    """The final image stage never switches to a non-root user.

    Why it matters: if an attacker gets code execution inside the container,
    running as root makes escapes and host damage much easier.

    Fix: create an unprivileged user and switch to it before the final CMD.

        RUN useradd --create-home app
        USER app
    """
    froms = [i for i in ctx.instructions if i.cmd == "FROM"]
    if not froms:
        return
    last_from = froms[-1]
    users = [i for i in ctx.instructions if i.cmd == "USER" and i.line > last_from.line]
    if not users or users[-1].args.split(":")[0].strip() in {"root", "0"}:
        yield ctx.finding(
            last_from.line,
            "Final stage runs as root (no non-root USER set).",
            "Add `USER <non-root-user>` after installing packages.",
        )
