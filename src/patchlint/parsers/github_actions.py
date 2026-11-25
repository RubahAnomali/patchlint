"""GitHub Actions workflow parser: safe YAML loading that keeps line numbers."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import yaml


class YMap(dict[str, Any]):
    """A YAML mapping that remembers where it starts and where each key is (1-based)."""

    def __init__(self) -> None:
        super().__init__()
        self.line = 0
        self.key_lines: dict[str, int] = {}


class YList(list[Any]):
    """A YAML sequence that remembers the line it starts on (1-based)."""

    line = 0


class _Loader(yaml.SafeLoader):
    """SafeLoader that builds YMap/YList. Never executes or instantiates anything."""


def _construct_map(loader: _Loader, node: yaml.MappingNode) -> YMap:
    loader.flatten_mapping(node)
    result = YMap()
    result.line = node.start_mark.line + 1
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=True)
        # YAML 1.1 reads the bare key `on` as the boolean True.
        name = "on" if key is True else str(key)
        result[name] = loader.construct_object(value_node, deep=True)
        result.key_lines[name] = key_node.start_mark.line + 1
    return result


def _construct_seq(loader: _Loader, node: yaml.SequenceNode) -> YList:
    result = YList(loader.construct_object(child, deep=True) for child in node.value)
    result.line = node.start_mark.line + 1
    return result


_Loader.add_constructor("tag:yaml.org,2002:map", _construct_map)
_Loader.add_constructor("tag:yaml.org,2002:seq", _construct_seq)


def parse(text: str) -> YMap | None:
    """Parse a workflow file. Returns None if the top level is not a mapping.

    Raises yaml.YAMLError on invalid YAML.
    """
    doc = yaml.load(text, Loader=_Loader)  # _Loader is a SafeLoader subclass
    return doc if isinstance(doc, YMap) else None


def iter_jobs(workflow: YMap) -> Iterator[tuple[str, YMap]]:
    """Yield (job_id, job) for every job in the workflow."""
    jobs = workflow.get("jobs")
    if isinstance(jobs, YMap):
        for job_id, job in jobs.items():
            if isinstance(job, YMap):
                yield job_id, job


def iter_steps(workflow: YMap) -> Iterator[tuple[str, YMap]]:
    """Yield (job_id, step) for every step of every job."""
    for job_id, job in iter_jobs(workflow):
        steps = job.get("steps")
        if isinstance(steps, YList):
            for step in steps:
                if isinstance(step, YMap):
                    yield job_id, step
