"""SARIF 2.1.0 output, the format GitHub code scanning and many IDEs read."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from patchlint import __version__
from patchlint.core.model import Finding, Rule

SCHEMA = "https://json.schemastore.org/sarif-2.1.0.json"
INFO_URI = "https://github.com/RubahAnomali/patchlint"

# SARIF result level, and the 0-10 score GitHub uses to label alerts
# (9+ critical, 7+ high, 4+ medium, below that low).
LEVELS = {"high": "error", "medium": "warning", "low": "note"}
SECURITY_SEVERITY = {"high": "8.0", "medium": "5.5", "low": "2.0"}


def to_uri(path: str, base: Path) -> str:
    """Repository-relative, forward-slash path; GitHub needs this to place alerts."""
    p = Path(path)
    if p.is_absolute():
        try:
            p = p.relative_to(base)
        except ValueError:
            return p.as_uri()
    return p.as_posix()


def _rule_descriptor(rule: Rule) -> dict[str, Any]:
    tags = ["security", rule.filetype]
    if rule.cwe:
        tags.append(f"external/cwe/cwe-{rule.cwe}")
    first_line = rule.doc.splitlines()[0] if rule.doc else rule.title
    return {
        "id": rule.id,
        "name": "".join(word.capitalize() for word in rule.title.replace("`", "").split()),
        "shortDescription": {"text": rule.title},
        "fullDescription": {"text": first_line},
        "help": {"text": rule.doc, "markdown": rule.doc},
        "helpUri": f"{INFO_URI}/tree/main/src/patchlint/rules",
        "defaultConfiguration": {"level": LEVELS[rule.severity]},
        "properties": {
            "tags": tags,
            "precision": "high",
            "security-severity": SECURITY_SEVERITY[rule.severity],
        },
    }


def to_sarif(
    findings: Iterable[Finding], rules: Mapping[str, Rule], base: Path | None = None
) -> dict[str, Any]:
    """Build a SARIF log with every known rule and one result per finding."""
    base = (base or Path.cwd()).resolve()
    ordered = sorted(rules.values(), key=lambda r: r.id)
    index = {r.id: i for i, r in enumerate(ordered)}
    results = [
        {
            "ruleId": f.rule_id,
            "ruleIndex": index[f.rule_id],
            "level": LEVELS[f.severity],
            "message": {"text": f"{f.message} Fix: {f.fix}"},
            "locations": [
                {
                    "physicalLocation": {
                        "artifactLocation": {"uri": to_uri(f.path, base)},
                        "region": {"startLine": max(f.line, 1)},
                    }
                }
            ],
        }
        for f in findings
    ]
    return {
        "$schema": SCHEMA,
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "patchlint",
                        "version": __version__,
                        "informationUri": INFO_URI,
                        "rules": [_rule_descriptor(r) for r in ordered],
                    }
                },
                "results": results,
            }
        ],
    }
