from __future__ import annotations

from collections.abc import Iterable

from patchlint.core.model import Context, Finding
from patchlint.core.registry import rule
from patchlint.parsers.compose import iter_services
from patchlint.parsers.github_actions import YMap


def _options(service: YMap) -> list[str]:
    """Flatten the shapes `security_opt` can take into a list of strings.

    Compose accepts a list (`security_opt: ["seccomp:unconfined"]`), a mapping
    (`security_opt: {seccomp: unconfined}`, which some implementations support)
    and a single string (`security_opt: seccomp:unconfined`).
    """
    raw = service.get("security_opt")
    if raw is None:
        return []
    if isinstance(raw, str):
        return [raw]
    if isinstance(raw, dict):
        return [f"{k}:{v}" for k, v in raw.items()]
    if isinstance(raw, list):
        out: list[str] = []
        for item in raw:
            if isinstance(item, str):
                out.append(item)
            elif isinstance(item, dict):
                out.extend(f"{k}:{v}" for k, v in item.items())
        return out
    return []


@rule(id="DC008", title="Service turns off seccomp or AppArmor", severity="medium", cwe=693)
def check(ctx: Context) -> Iterable[Finding]:
    """A compose service disables its sandbox with `security_opt: ...:unconfined`.

    Why it matters: Docker gives every container a seccomp profile (which system
    calls may run) and, on hosts that support it, an AppArmor profile (what the
    process may touch). `seccomp:unconfined` removes the syscall filter and
    `apparmor:unconfined` removes the mandatory access control, so a bug or an
    injected payload inside the container reaches the host kernel with nothing in
    between. CWE-693 is the general "protection mechanism failure" bucket.

    Fix: keep the defaults, or point at a narrower profile instead of turning the
    mechanism off:

        security_opt:
          - no-new-privileges:true
          - seccomp:./seccomp-app.json
          - apparmor:docker-default
    """
    if ctx.compose is None:
        return
    for name, service in iter_services(ctx.compose):
        hits = [opt for opt in _options(service) if "unconfined" in opt.lower()]
        if not hits:
            continue
        line = service.key_lines.get("security_opt", service.line)
        yield ctx.finding(
            line,
            f"Service `{name}` turns off its sandbox (`{', '.join(hits)}`).",
            "Drop `:unconfined`; keep the default profile or point seccomp/apparmor "
            "at a narrower one.",
        )
