"""Data types shared by rules, the runner and the CLI."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path

from patchlint.parsers.github_actions import YMap

SEVERITIES = ("low", "medium", "high")
FILETYPES = ("dockerfile", "workflow", "compose", "action")


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
    """What a rule's ``check`` function receives.

    Dockerfile rules use ``instructions``; workflow rules use ``workflow``;
    docker-compose rules use ``compose``. A rule that opted in to composite
    actions (``extra_filetypes=("action",)``) also gets ``action``, the parsed
    ``action.yml``; ``workflow`` is None for those files.
    ``lines`` is the raw file text, one entry per line.
    """

    path: Path
    instructions: tuple[Instruction, ...]
    workflow: YMap | None
    compose: YMap | None
    lines: tuple[str, ...]
    _rule_id: str
    _severity: str
    action: YMap | None = None

    def finding(self, line: int, message: str, fix: str) -> Finding:
        return Finding(self._rule_id, self._severity, message, str(self.path), line, fix)

    def line_of(self, text: str, start: int) -> int:
        """First line at or after ``start`` that contains ``text`` (falls back to ``start``)."""
        for index in range(max(start - 1, 0), len(self.lines)):
            if text in self.lines[index]:
                return index + 1
        return start


CheckFn = Callable[[Context], Iterable[Finding]]


@dataclass(frozen=True)
class Rule:
    id: str
    title: str
    severity: str
    cwe: int | None
    filetype: str
    check: CheckFn
    origin: str = "patchlint"  # the package that provides the rule (plugins set their own)
    filetypes: tuple[str, ...] = ()  # every kind it runs on; empty means just `filetype`

    def __post_init__(self) -> None:
        if not self.filetypes:
            object.__setattr__(self, "filetypes", (self.filetype,))

    @property
    def doc(self) -> str:
        return (self.check.__doc__ or "").strip()
