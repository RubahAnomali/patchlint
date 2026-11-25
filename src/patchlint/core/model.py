"""Data types shared by rules, the runner and the CLI."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path

SEVERITIES = ("low", "medium", "high")


@dataclass(frozen=True)
class Instruction:
    """One Dockerfile instruction, with continuation lines joined."""

    line: int  # 1-based line where the instruction starts
    cmd: str  # upper-case, e.g. "FROM"
    args: str  # everything after the command


@dataclass(frozen=True)
class Finding:
    rule_id: str
    severity: str
    message: str
    path: str
    line: int
    fix: str


@dataclass(frozen=True)
class Context:
    """What a rule's ``check`` function receives."""

    path: Path
    instructions: tuple[Instruction, ...]
    _rule_id: str
    _severity: str

    def finding(self, line: int, message: str, fix: str) -> Finding:
        return Finding(self._rule_id, self._severity, message, str(self.path), line, fix)


CheckFn = Callable[[Context], Iterable[Finding]]


@dataclass(frozen=True)
class Rule:
    id: str
    title: str
    severity: str
    cwe: int | None
    check: CheckFn

    @property
    def doc(self) -> str:
        return (self.check.__doc__ or "").strip()
