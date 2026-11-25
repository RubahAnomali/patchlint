from __future__ import annotations

from collections.abc import Iterable

from patchlint.core.model import Context, Finding
from patchlint.core.registry import rule
from patchlint.parsers.compose import iter_services


@rule(id="DC001", title="Service runs in privileged mode", severity="high", cwe=250)
def check(ctx: Context) -> Iterable[Finding]:
    """A compose service sets `privileged: true`.

    Why it matters: a privileged container gets every Linux capability and access
    to the host's devices. Code that breaks out of the app (or is injected into it)
    effectively has root on the host, so container isolation is gone.

    Fix: remove `privileged: true` and add only the specific capability the
    service needs, if any:

        cap_add:
          - NET_ADMIN
    """
    if ctx.compose is None:
        return
    for name, service in iter_services(ctx.compose):
        if service.get("privileged") is True:
            yield ctx.finding(
                service.key_lines["privileged"],
                f"Service `{name}` runs privileged, with full access to the host.",
                "Remove `privileged: true`; use `cap_add` for the one capability you need.",
            )
