from __future__ import annotations

from collections.abc import Iterable

from patchlint.core.model import Context, Finding
from patchlint.core.registry import rule


@rule(id="DL002", title="Base image is not pinned", severity="medium", cwe=1357)
def check(ctx: Context) -> Iterable[Finding]:
    """A `FROM` line uses the `latest` tag or no tag at all.

    Why it matters: `latest` changes without warning, so builds are not
    reproducible and a compromised or broken upstream image flows straight in.

    Fix: pin a specific version tag, or better a digest.

        FROM python:3.12-slim
    """
    stages: set[str] = set()
    for ins in ctx.instructions:
        if ins.cmd != "FROM":
            continue
        parts = [p for p in ins.args.split() if not p.startswith("--")]
        image = parts[0] if parts else ""
        if len(parts) >= 3 and parts[1].lower() == "as":
            stages.add(parts[2].lower())
        if not image or image.lower() == "scratch" or image.lower() in stages:
            continue
        if "@sha256:" in image:
            continue
        name = image.rsplit("/", 1)[-1]
        tag = name.split(":", 1)[1] if ":" in name else ""
        if tag in ("", "latest"):
            yield ctx.finding(
                ins.line,
                f"Base image `{image}` is not pinned to a version.",
                "Pin a specific tag or digest, e.g. `python:3.12-slim`.",
            )
