from __future__ import annotations

from collections.abc import Iterable

from patchlint.core.model import Context, Finding
from patchlint.core.registry import rule
from patchlint.parsers.compose import iter_services
from patchlint.parsers.github_actions import YList, YMap

# Capabilities that give back most or all of what `privileged: true` gives.
# SYS_ADMIN alone can mount host filesystems and call a pile of privileged
# syscalls; ALL is simply everything.
DANGEROUS = ("ALL", "SYS_ADMIN")


def _capabilities(service: YMap) -> list[str]:
    """`cap_add` as a flat list, tolerating a single string instead of a list."""
    raw = service.get("cap_add")
    if isinstance(raw, str):
        return [raw]
    if isinstance(raw, YList):
        return [item for item in raw if isinstance(item, str)]
    return []


@rule(id="DC005", title="Service adds a dangerous capability", severity="high", cwe=250)
def check(ctx: Context) -> Iterable[Finding]:
    """A compose service adds `ALL` or `SYS_ADMIN` through `cap_add`.

    Why it matters: Linux capabilities are the crumbs of root that survive the
    privilege split. `ALL` hands every one of them back, and `SYS_ADMIN` is the
    notorious one -- it can mount filesystems, set up namespaces and poke at
    devices, which in practice is enough to reach the host and undo the
    container boundary. The container is still nominally unprivileged, so this
    slips past rules that only look for `privileged: true`. CWE-250 is
    "execution with unnecessary privileges".

    Fix: drop the broad capability and add only the one the service needs:

        cap_add:
          - NET_ADMIN

    If the service really needs the host that badly, it belongs outside the
    container. Note: matching is exact and case-insensitive, so `NET_ADMIN` or
    `SYS_PTRACE` are not reported.
    """
    if ctx.compose is None:
        return
    for name, service in iter_services(ctx.compose):
        hits = [cap for cap in _capabilities(service) if cap.strip().upper() in DANGEROUS]
        if not hits:
            continue
        start = service.key_lines.get("cap_add", service.line)
        yield ctx.finding(
            ctx.line_of(hits[0], start),
            f"Service `{name}` adds the capability `{', '.join(hits)}`, which is "
            "close to full root on the host.",
            "Remove it from `cap_add`; if the service needs host access, run it "
            "outside the container instead.",
        )
