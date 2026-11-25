from __future__ import annotations

from collections.abc import Iterable

from patchlint.core.model import Context, Finding
from patchlint.core.registry import rule
from patchlint.parsers.compose import iter_services


@rule(id="DC003", title="Service uses host network mode", severity="high", cwe=250)
def check(ctx: Context) -> Iterable[Finding]:
    """A compose service sets `network_mode: host`.

    Why it matters: the service shares the host's network stack directly, so it can
    reach every port bound to localhost on the host (databases, admin panels,
    metadata endpoints) and container network isolation no longer applies.

    Fix: remove `network_mode: host` and publish only the specific ports the
    service needs on a dedicated bridge network:

        ports:
          - "127.0.0.1:8080:8080"
    """
    if ctx.compose is None:
        return
    for name, service in iter_services(ctx.compose):
        mode = service.get("network_mode")
        # `service:x` and `container:x` share another container's namespace, not the host's.
        if isinstance(mode, str) and mode.strip().lower() == "host":
            yield ctx.finding(
                service.key_lines["network_mode"],
                f"Service `{name}` uses `network_mode: host`, sharing the host network stack.",
                "Remove `network_mode: host` and expose only required ports via `ports:`.",
            )
