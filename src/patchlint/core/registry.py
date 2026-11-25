"""Rule registry: the ``@rule`` decorator, built-in rule discovery and rule plugins."""

from __future__ import annotations

import importlib
import importlib.metadata
import pkgutil
import sys
from collections.abc import Callable, Iterable
from dataclasses import replace
from typing import Any

from patchlint.core.model import SEVERITIES, CheckFn, Rule

RULES: dict[str, Rule] = {}

# The rule id prefix decides which files a rule runs on.
PREFIX_FILETYPES = {"DL": "dockerfile", "GA": "workflow", "DC": "compose"}

# Third-party packages register rule modules under this entry point group:
#   [project.entry-points."patchlint.rules"]
#   acme = "acme_patchlint_rules"
PLUGIN_GROUP = "patchlint.rules"
_plugins_loaded = False


def rule(
    id: str, title: str, severity: str, cwe: int | None = None
) -> Callable[[CheckFn], CheckFn]:
    """Register a check function as a rule.

    The function's docstring is the rule's documentation: explain *why* the
    pattern is dangerous and *how* to fix it.
    """
    if severity not in SEVERITIES:
        raise ValueError(f"severity must be one of {SEVERITIES}, got {severity!r}")
    filetype = PREFIX_FILETYPES.get(id[:2])
    if filetype is None:
        raise ValueError(f"rule id {id!r} must start with one of {sorted(PREFIX_FILETYPES)}")

    def decorator(fn: CheckFn) -> CheckFn:
        if id in RULES:
            raise ValueError(f"duplicate rule id {id}")
        RULES[id] = Rule(
            id=id, title=title, severity=severity, cwe=cwe, filetype=filetype, check=fn
        )
        return fn

    return decorator


def _plugin_entry_points() -> Iterable[Any]:
    return importlib.metadata.entry_points(group=PLUGIN_GROUP)


def _load_plugins() -> None:
    """Import every installed rule plugin once.

    A broken plugin prints a warning and is skipped, so it can never stop a scan
    or replace a built-in rule.
    """
    for ep in _plugin_entry_points():
        before = set(RULES)
        try:
            ep.load()
        except Exception as exc:  # any failure inside third-party code
            for rule_id in set(RULES) - before:
                del RULES[rule_id]  # don't keep half a plugin
            print(f"warning: rule plugin {ep.name!r} failed to load: {exc}", file=sys.stderr)
            continue
        dist = getattr(ep, "dist", None)
        origin = getattr(dist, "name", None) or ep.name
        for rule_id in set(RULES) - before:
            RULES[rule_id] = replace(RULES[rule_id], origin=origin)


def load_rules() -> dict[str, Rule]:
    """Import every built-in rule module, then installed plugins (once)."""
    global _plugins_loaded
    import patchlint.rules as rules_pkg

    for mod in pkgutil.walk_packages(rules_pkg.__path__, prefix="patchlint.rules."):
        importlib.import_module(mod.name)
    if not _plugins_loaded:
        _plugins_loaded = True
        _load_plugins()
    return RULES
