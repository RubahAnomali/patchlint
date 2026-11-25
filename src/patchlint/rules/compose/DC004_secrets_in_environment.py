from __future__ import annotations

from collections.abc import Iterable

from patchlint.core.model import Context, Finding
from patchlint.core.registry import rule
from patchlint.parsers.compose import iter_services
from patchlint.parsers.github_actions import YList, YMap

NOT_SECRET = ("passwordless", "token_url", "token_endpoint", "api_key_url")


def _normalise(name: str) -> str:
    return name.strip().lower().replace("-", "_").replace(".", "_")


def _is_secret_name(name: str) -> bool:
    norm = _normalise(name)
    if any(norm == bad or norm.endswith(bad) for bad in NOT_SECRET):
        return False
    parts = [p for p in norm.split("_") if p]
    if not parts:
        return False
    for i, part in enumerate(parts):
        # `PASSWORD_HASH_ROUNDS` is a setting about a password, not one.
        setting = ("hash", "rounds", "length", "min", "max", "policy")
        if i + 1 < len(parts) and parts[i + 1] in setting:
            continue
        if part in ("password", "passwd", "secret", "token"):
            return True
        if part == "key" and i > 0 and parts[i - 1] in ("api", "access", "secret", "private"):
            return True
        if part == "key" and i + 1 < len(parts) and parts[i + 1] == "value":
            return True
    joined = norm.replace("_", "")
    return "apikey" in joined or "apisecret" in joined


def _is_literal(value: object) -> bool:
    if not isinstance(value, str):
        return False
    text = value.strip()
    if not text:
        return False
    if "$" in text:
        return False
    return True


def _environment(service: YMap) -> list[tuple[str, object]]:
    raw = service.get("environment")
    out: list[tuple[str, object]] = []
    if isinstance(raw, YList):
        for item in raw:
            if isinstance(item, str) and "=" in item:
                key, _, val = item.partition("=")
                out.append((key.strip(), val))
    elif isinstance(raw, YMap):
        for key, val in raw.items():
            out.append((str(key), val))
    return out


@rule(id="DC004", title="Credential written into a service environment", severity="high", cwe=798)
def check(ctx: Context) -> Iterable[Finding]:
    """A compose service writes a credential literally into `environment`.

    Why it matters: values in `environment` are part of the compose file, so
    they end up in git, in CI logs, in `docker inspect` output and in the
    image's metadata. Anyone who can read the repository or run `inspect` gets
    the password -- and secrets do not get rotated when they leak this way.
    CWE-798 is "use of hard-coded credentials".

    Fix: leave the value out and let compose read it from the environment (or an
    env file that isn't committed), or use a secret store:

        environment:
          DB_PASSWORD: ${DB_PASSWORD:?set DB_PASSWORD}
        # or
        secrets:
          - db_password

    Note: only literal values count. `DB_PASSWORD: ${DB_PASSWORD}` and
    `DB_PASSWORD:` (inherited from the shell) are the recommended shapes.
    """
    if ctx.compose is None:
        return
    for name, service in iter_services(ctx.compose):
        start = service.key_lines.get("environment", service.line)
        hits = [
            key
            for key, value in _environment(service)
            if _is_secret_name(key) and _is_literal(value)
        ]
        if not hits:
            continue
        shown = ", ".join(f"`{key}`" for key in hits)
        yield ctx.finding(
            ctx.line_of(hits[0], start),
            f"Service `{name}` writes a credential ({shown}) literally into its "
            "environment, so it is stored in the compose file.",
            "Replace the literal value with `${VAR}` (or `secrets:`) and keep the "
            "real value outside the repository.",
        )
