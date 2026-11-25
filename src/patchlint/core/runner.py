"""Find files, parse them, run rules."""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from pathlib import Path

from patchlint.core.model import Context, Finding
from patchlint.core.registry import load_rules
from patchlint.parsers import dockerfile

SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__"}


def is_dockerfile(path: Path) -> bool:
    name = path.name.lower()
    return name == "dockerfile" or name.startswith("dockerfile.") or name.endswith(".dockerfile")


def find_files(root: Path) -> Iterator[Path]:
    if root.is_file():
        yield root
        return
    for p in sorted(root.rglob("*")):
        if p.is_file() and not (SKIP_DIRS & set(p.parts)) and is_dockerfile(p):
            yield p


def scan(root: Path, only: Iterable[str] | None = None) -> list[Finding]:
    rules = load_rules()
    selected = set(only) if only else set(rules)
    findings: list[Finding] = []
    for path in find_files(root):
        if not is_dockerfile(path):
            continue
        instructions = dockerfile.parse(path.read_text(encoding="utf-8", errors="replace"))
        for r in rules.values():
            if r.id not in selected:
                continue
            ctx = Context(path, instructions, r.id, r.severity)
            findings.extend(r.check(ctx))
    findings.sort(key=lambda f: (f.path, f.line, f.rule_id))
    return findings
