from __future__ import annotations

from collections.abc import Iterable

from patchlint.core.model import Context, Finding
from patchlint.core.registry import rule
from patchlint.parsers.compose import iter_services


@rule(id="DC006", title="Image without a version tag or with `latest`", severity="medium", cwe=1357)
def check(ctx: Context) -> Iterable[Finding]:
    """An `image:` value uses the `latest` tag or no tag at all.

    Why it matters: `latest` changes without warning, so deployments are not
    reproducible and a broken or compromised upstream image flows straight in.

    Fix: pin a specific version tag, or better a digest.

        image: python:3.12-slim
    """
    for service in iter_services(ctx.content):
        # Skip services that use build: without image:
        if "build" in service.data and "image" not in service.data:
            continue
            
        image_line = service.key_lines.get("image")
        if not image_line:
            continue
            
        image = service.data["image"]
        if "@sha256:" in image:
            continue
            
        name = image.rsplit("/", 1)[-1]
        tag = name.split(":", 1)[1] if ":" in name else ""
        if tag in ("", "latest"):
            yield ctx.finding(
                image_line,
                f"Image `{image}` is not pinned to a version.",
                "Pin a specific tag or digest, e.g. `python:3.12-slim`."
            )
