"""Rule registry: the ``@rule`` decorator and automatic rule discovery."""

from __future__ import annotations

import importlib
import pkgutil
from collections.abc import Callable

from patchlint.core.model import SEVERITIES, CheckFn, Rule

RULES: dict[str, Rule] = {}

# The rule id prefix decides which files a rule runs on.
PREFIX_FILETYPES = {"DL": "dockerfile", "GA": "workflow"}


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


def load_rules() -> dict[str, Rule]:
    """Import every module under ``patchlint.rules`` so decorators run."""
    import patchlint.rules as rules_pkg

    for mod in pkgutil.walk_packages(rules_pkg.__path__, prefix="patchlint.rules."):
        importlib.import_module(mod.name)
    return RULES
