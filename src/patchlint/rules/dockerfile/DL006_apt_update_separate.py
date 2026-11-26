from __future__ import annotations

import re
from collections.abc import Iterable

from patchlint.core.model import Context, Finding
from patchlint.core.registry import rule


def _strip_comment(command: str) -> str:
    """Drop a trailing ` # ...` comment from a RUN body.

    The parser keeps the whole line, comment and all, so a note that merely
    mentions `apt-get update` would otherwise look like a command. A `#` only
    starts a comment at the beginning or after whitespace.
    """
    for index, char in enumerate(command):
        if char != "#":
            continue
        if index == 0 or command[index - 1].isspace():
            return command[:index]
    return command


def _shell_commands(command: str) -> str:
    """The RUN body with comments removed, folded to single spaces.

    Pasted heredocs are not modelled; this only needs to answer "does this
    layer run update, and does it also run install".
    """
    lines = []
    for line in command.splitlines():
        stripped = _strip_comment(line).strip()
        if stripped:
            lines.append(stripped)
    return " ".join(lines)


# Where a shell command starts: beginning of the body, or after a separator.
# Deliberately *not* "anywhere after whitespace" -- that would match the
# `update` in `echo apt-get update`, which is an argument, not a command.
START = r"(?:^|[;&|(]\s*)"

# `apt-get update` / `apt update` as a command of its own.
UPDATE = re.compile(START + r"(?:apt-get|apt)\s+update\b", re.IGNORECASE)

# `apt-get install` / `apt install` / `apt-get -y install`, same as DL005.
INSTALL = re.compile(
    START + r"(?:apt-get|apt)\s+(?:-[^\s]+\s+)*install\b", re.IGNORECASE
)


@rule(id="DL006", title="apt update in its own RUN layer", severity="low", cwe=1104)
def check(ctx: Context) -> Iterable[Finding]:
    """A `RUN` line runs `apt-get update` without an `apt-get install` beside it.

    Why it matters: every `RUN` becomes a layer, and Docker reuses an old
    layer when the *command text* has not changed -- it does not know that the
    package index has moved on. `RUN apt-get update` in its own layer gets
    cached forever, so a later `install` in a different layer can be pointed at
    a stale index: missing the newest packages, or failing outright when a
    version that used to be listed has been removed upstream. That is the
    classic "it built yesterday" bug. Caching aside, a separate update layer is
    also just one more useless layer in the image.

    Fix: keep them in one step, and clean up in the same step:

        RUN apt-get update \\
         && apt-get install -y --no-install-recommends curl \\
         && rm -rf /var/lib/apt/lists/*

    Note: a `RUN` that has both `update` and `install` is not reported. Only
    `apt-get update` / `apt update` count -- not `apt-get upgrade`, not a
    comment that happens to mention it.
    """
    for ins in ctx.instructions:
        if ins.cmd != "RUN":
            continue
        body = _shell_commands(ins.args)
        if not UPDATE.search(body):
            continue
        if INSTALL.search(body):
            continue
        yield ctx.finding(
            ins.line,
            "`apt-get update` sits in its own RUN layer; the index it fetches "
            "gets cached and goes stale.",
            "Put `apt-get update` and the matching `apt-get install` in the "
            "same RUN, ending with `rm -rf /var/lib/apt/lists/*`.",
        )
