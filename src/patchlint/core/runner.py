"""Find files, parse them, run rules."""

from __future__ import annotations

import sys
from collections.abc import Iterable, Iterator
from pathlib import Path

import yaml

from patchlint.core.model import Context, Finding, Instruction
from patchlint.core.registry import load_rules
from patchlint.parsers import dockerfile, github_actions
from patchlint.parsers.github_actions import YMap

SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__"}
MAX_BYTES = 1_000_000  # skip unusually large files rather than risk slow parsing


def file_kind(path: Path, explicit: bool = False) -> str | None:
    """Return "dockerfile", "workflow" or None.

    In a directory scan, YAML only counts inside `.github/workflows/`. A YAML file
    named directly on the command line is always treated as a workflow.
    """
    name = path.name.lower()
    if name == "dockerfile" or name.startswith("dockerfile.") or name.endswith(".dockerfile"):
        return "dockerfile"
    if path.suffix.lower() in (".yml", ".yaml"):
        parts = [p.lower() for p in path.parts]
        in_workflows = len(parts) >= 3 and parts[-3] == ".github" and parts[-2] == "workflows"
        if explicit or in_workflows:
            return "workflow"
    return None


def find_files(root: Path) -> Iterator[tuple[Path, str]]:
    if root.is_file():
        kind = file_kind(root, explicit=True)
        if kind:
            yield root, kind
        return
    for p in sorted(root.rglob("*")):
        if p.is_file() and not (SKIP_DIRS & set(p.parts)):
            kind = file_kind(p)
            if kind:
                yield p, kind


def scan(root: Path, only: Iterable[str] | None = None) -> list[Finding]:
    rules = load_rules()
    selected = set(only) if only else set(rules)
    findings: list[Finding] = []
    for path, kind in find_files(root):
        if path.stat().st_size > MAX_BYTES:
            print(f"warning: skipping {path} (larger than {MAX_BYTES} bytes)", file=sys.stderr)
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        instructions: tuple[Instruction, ...] = ()
        workflow: YMap | None = None
        if kind == "dockerfile":
            instructions = dockerfile.parse(text)
        else:
            try:
                workflow = github_actions.parse(text)
            except yaml.YAMLError as exc:
                print(f"warning: skipping {path}: invalid YAML ({exc})", file=sys.stderr)
                continue
            if workflow is None:
                continue
        lines = tuple(text.splitlines())
        for r in rules.values():
            if r.id not in selected or r.filetype != kind:
                continue
            ctx = Context(path, instructions, workflow, lines, r.id, r.severity)
            findings.extend(r.check(ctx))
    findings.sort(key=lambda f: (f.path, f.line, f.rule_id))
    return findings
