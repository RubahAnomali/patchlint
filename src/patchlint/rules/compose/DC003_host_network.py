from __future__ import annotations

from collections.abc import Iterable

from patchlint.core.model import Context, Finding
from patchlint.core.registry import rule
from patchlint.parsers.compose import iter_services


@rule(id="DC003", title="Service uses the host network", severity="medium", cwe=250)
def check(ctx: Context) -> Iterable[Finding]:
    """A compose service sets `network_mode: host`.

    Why it matters: the container stops having a network namespace of its own and
    uses the host's network stack directly. Every port the process listens on is
    open on the host, host firewall rules no longer sit in front of it, and the
    service can reach other things bound to loopback (databases, admin panels,
    the Docker socket's siblings). A compromise of the app is a foothold on the
    host's network rather than a foothold in a box.

    Fix: drop `network_mode: host` and publish only the ports you need, bound to
    loopback unless something outside has to reach it:

        ports:
          - "127.0.0.1:8080:80"

    Note: only the literal value `host` counts. `service:xxx` and
    `container:xxx` share another container's namespace, not the host's.
    """
    if ctx.compose is None:
        return
    for name, service in iter_services(ctx.compose):
        mode = service.get("network_mode")
        if isinstance(mode, str) and mode.strip().lower() == "host":
            yield ctx.finding(
                service.key_lines["network_mode"],
                f"Service `{name}` uses the host network namespace, exposing its "
                "ports and loopback services to everyone on the host.",
                "Remove `network_mode: host`; publish ports explicitly, ideally "
                'bound to 127.0.0.1 (e.g. "127.0.0.1:8080:80").',
            )
