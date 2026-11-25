"""Project configuration: `.patchlint.toml`, or `[tool.patchlint]` in `pyproject.toml`.

Example `.patchlint.toml`:

    disable = ["DL002"]                 # rules to turn off
    exclude = ["tests/fixtures/*"]      # paths to skip (globs, relative to the scanned folder)

    [severity]                          # change a rule's severity
    GA001 = "high"
"""

from __future__ import annotations

import sys
from collections.abc import Collection, Mapping
from dataclasses import dataclass, field
from fnmatch import fnmatch
from pathlib import Path
from typing import Any

from patchlint.core.model import SEVERITIES

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover - exercised on Python 3.10 only
    import tomli as tomllib

CONFIG_FILE = ".patchlint.toml"
KNOWN_KEYS = {"disable", "exclude", "severity"}


class ConfigError(ValueError):
    """The configuration file is invalid. The message says what to fix."""


@dataclass(frozen=True)
class Config:
    disable: frozenset[str] = frozenset()
    exclude: tuple[str, ...] = ()
    severity: Mapping[str, str] = field(default_factory=dict)
    source: Path | None = None

    def is_excluded(self, path: Path, root: Path) -> bool:
        """True if `path` matches an exclude glob. `*` also matches `/`."""
        try:
            rel = path.resolve().relative_to(root.resolve()).as_posix()
        except ValueError:
            rel = path.as_posix()
        return any(fnmatch(rel, pattern) for pattern in self.exclude)


def find_config(start: Path) -> Path | None:
    """Look for `.patchlint.toml`, then a `pyproject.toml` with `[tool.patchlint]`,
    in the scanned folder (or the scanned file's folder)."""
    folder = start if start.is_dir() else start.parent
    candidate = folder / CONFIG_FILE
    if candidate.is_file():
        return candidate
    pyproject = folder / "pyproject.toml"
    if pyproject.is_file():
        try:
            data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
        except tomllib.TOMLDecodeError:
            return None  # a broken pyproject.toml is not our problem to report
        if isinstance(data.get("tool"), dict) and "patchlint" in data["tool"]:
            return pyproject
    return None


def load_config(path: Path, known_rules: Collection[str]) -> Config:
    """Read and validate a config file."""
    try:
        data: dict[str, Any] = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"{path}: invalid TOML ({exc})") from exc
    if path.name == "pyproject.toml":
        data = data.get("tool", {}).get("patchlint", {})
        if not isinstance(data, dict):
            raise ConfigError(f"{path}: [tool.patchlint] must be a table")
    return parse_config(data, known_rules, path)


def parse_config(
    data: Mapping[str, Any], known_rules: Collection[str], source: Path | None = None
) -> Config:
    where = str(source) if source else "config"
    unknown = set(data) - KNOWN_KEYS
    if unknown:
        raise ConfigError(
            f"{where}: unknown key(s) {sorted(unknown)}; allowed: {sorted(KNOWN_KEYS)}"
        )

    def rule_list(key: str) -> list[str]:
        value = data.get(key, [])
        if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
            raise ConfigError(f"{where}: `{key}` must be a list of strings")
        return value

    disable = [r.upper() for r in rule_list("disable")]
    bad = sorted(set(disable) - set(known_rules))
    if bad:
        raise ConfigError(f"{where}: unknown rule id(s) in `disable`: {bad}")

    exclude = rule_list("exclude")

    severity_raw = data.get("severity", {})
    if not isinstance(severity_raw, dict):
        raise ConfigError(f"{where}: `[severity]` must be a table like `GA001 = \"high\"`")
    severity: dict[str, str] = {}
    for rule_id, level in severity_raw.items():
        rule_id = rule_id.upper()
        if rule_id not in known_rules:
            raise ConfigError(f"{where}: unknown rule id in `[severity]`: {rule_id}")
        if level not in SEVERITIES:
            raise ConfigError(
                f"{where}: severity for {rule_id} must be one of {list(SEVERITIES)}, got {level!r}"
            )
        severity[rule_id] = level

    return Config(frozenset(disable), tuple(exclude), severity, source)
