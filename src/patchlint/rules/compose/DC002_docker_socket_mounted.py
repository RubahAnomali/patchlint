from __future__ import annotations

from collections.abc import Iterable

from patchlint.core.model import Context, Finding
from patchlint.core.registry import rule
from patchlint.parsers.compose import iter_services, volume_sources

SOCKETS = ("/var/run/docker.sock", "/run/docker.sock", "//./pipe/docker_engine")


@rule(id="DC002", title="Docker socket mounted into a service", severity="high", cwe=250)
def check(ctx: Context) -> Iterable[Finding]:
    """A compose service mounts the Docker socket (`/var/run/docker.sock`).

    Why it matters: whoever can talk to the Docker socket controls the Docker
    daemon, and can start a privileged container that mounts the host's root
    filesystem. Mounting it, even read-only, gives the service root on the host.

    Fix: don't mount the socket. If a tool truly needs the Docker API, put a
    filtering proxy (for example a socket proxy that only allows the API calls it
    needs) in between, and never expose it to an internet-facing service.
    """
    if ctx.compose is None:
        return
    for name, service in iter_services(ctx.compose):
        start = service.key_lines.get("volumes", service.line)
        for source in volume_sources(service):
            if source.rstrip("/") in SOCKETS:
                yield ctx.finding(
                    ctx.line_of("docker", start) if "docker" in source else start,
                    f"Service `{name}` mounts the Docker socket `{source}`, "
                    "which gives it control of the host.",
                    "Remove the socket mount, or use a filtering socket proxy instead.",
                )
