from __future__ import annotations

from collections.abc import Iterable

from patchlint.core.model import Context, Finding
from patchlint.core.registry import rule
from patchlint.parsers.compose import iter_services

# Namespaces whose sharing defeats the container boundary: `pid: host` gives a
# view of every process on the host (and a path into places like
# /proc/1/root), `ipc: host` opens up the host's shared memory segments.
DANGEROUS = ("pid", "ipc")


@rule(id="DC007", title="Service shares a host namespace", severity="high", cwe=653)
def check(ctx: Context) -> Iterable[Finding]:
    """A compose service sets `pid: host` or `ipc: host`.

    Why it matters: `pid: host` puts the container in the host's PID namespace,
    so it can see -- and signal -- every process on the machine, and walk into
    `/proc/<pid>/root` to reach the host filesystem. `ipc: host` shares the
    host's SysV/POSIX shared memory, so anything on the host that trusts that
    channel is talking straight to the container. Either one means the
    isolation you think you bought is mostly gone. CWE-653 is "improper
    isolation of compartmentalized functionality".

    Fix: drop the setting. Sharing with a specific sidecar is fine:

        pid: "service:sidecar"
        ipc: shareable

    Note: matching is exact and case-insensitive on `host`; `service:x`,
    `container:x`, `shareable` and `none` are not reported.
    """
    if ctx.compose is None:
        return
    for name, service in iter_services(ctx.compose):
        for key in DANGEROUS:
            value = service.get(key)
            if not isinstance(value, str) or value.strip().lower() != "host":
                continue
            yield ctx.finding(
                service.key_lines.get(key, service.line),
                f"Service `{name}` sets `{key}: host`, putting it in the host's "
                f"{key} namespace and crossing the container boundary.",
                f"Remove `{key}: host`; share with a sidecar only, e.g. "
                f'`{key}: "service:sidecar"`.',
            )
