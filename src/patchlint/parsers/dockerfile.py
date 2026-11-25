"""A small Dockerfile parser: comments dropped, continuation lines joined."""

from __future__ import annotations

from patchlint.core.model import Instruction


def parse(text: str) -> tuple[Instruction, ...]:
    instructions: list[Instruction] = []
    buf: list[str] = []
    start = 0
    for lineno, raw in enumerate(text.splitlines(), start=1):
        stripped = raw.strip()
        if not buf and (not stripped or stripped.startswith("#")):
            continue
        if not buf:
            start = lineno
        if stripped.startswith("#"):  # comment inside a continuation
            continue
        if stripped.endswith("\\"):
            buf.append(stripped[:-1].strip())
            continue
        buf.append(stripped)
        joined = " ".join(p for p in buf if p)
        buf = []
        cmd, _, args = joined.partition(" ")
        instructions.append(Instruction(start, cmd.upper(), args.strip()))
    if buf:  # file ended mid-continuation
        joined = " ".join(p for p in buf if p)
        cmd, _, args = joined.partition(" ")
        instructions.append(Instruction(start, cmd.upper(), args.strip()))
    return tuple(instructions)
