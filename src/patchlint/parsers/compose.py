"""docker-compose helpers. Files are parsed by the same line-aware safe YAML loader
as workflows (see `github_actions.parse`); this module adds compose-specific helpers."""

from __future__ import annotations

from collections.abc import Iterator

from patchlint.parsers.github_actions import YList, YMap


def iter_services(compose: YMap) -> Iterator[tuple[str, YMap]]:
    """Yield (service_name, service) for every service in a compose file."""
    services = compose.get("services")
    if isinstance(services, YMap):
        for name, service in services.items():
            if isinstance(service, YMap):
                yield name, service


def volume_sources(service: YMap) -> Iterator[str]:
    """Yield the host side of every volume, for both short and long syntax.

    Short: `- /var/run/docker.sock:/var/run/docker.sock:ro` -> `/var/run/docker.sock`
    Long:  `- {type: bind, source: ./data, target: /data}`  -> `./data`
    """
    volumes = service.get("volumes")
    if not isinstance(volumes, YList):
        return
    for entry in volumes:
        if isinstance(entry, str):
            # Split on ":" but keep Windows drive letters like C:\\data intact.
            head, sep, _rest = entry.partition(":")
            if sep and len(head) == 1 and head.isalpha():
                drive_rest = _rest.partition(":")[0]
                yield f"{head}:{drive_rest}"
            elif sep:
                yield head
        elif isinstance(entry, YMap) and isinstance(entry.get("source"), str):
            yield entry["source"]
