from pathlib import Path
from typing import Any

import yaml

from patchlint.core.runner import scan
from patchlint.parsers.github_actions import parse

ACTION = Path(__file__).parent.parent / "action.yml"


def load_action() -> Any:
    action = parse(ACTION.read_text(encoding="utf-8"))
    assert action is not None
    return action


def to_plain(node: Any) -> Any:
    """Copy parser maps and lists into plain dicts and lists that yaml can dump."""
    if isinstance(node, dict):
        return {k: to_plain(v) for k, v in node.items()}
    if isinstance(node, list):
        return [to_plain(v) for v in node]
    return node


def run_scripts_with_expressions(steps: list[Any]) -> list[str]:
    """Names of steps whose `run:` script contains a `${{ }}` expression."""
    bad = []
    for i, step in enumerate(steps, 1):
        run = step.get("run")
        if isinstance(run, str) and "${{" in run:
            bad.append(str(step.get("name", f"step {i}")))
    return bad


def test_is_composite_action_with_expected_inputs() -> None:
    action = load_action()
    assert action["runs"]["using"] == "composite"
    inputs = action["inputs"]
    assert inputs["path"]["default"] == "."
    assert inputs["format"]["default"] == "sarif"
    assert inputs["upload-sarif"]["default"] == "true"
    assert "sarif-file" in action["outputs"]


def test_uses_are_pinned_to_commit_shas(tmp_path: Path) -> None:
    steps = to_plain(load_action()["runs"]["steps"])
    workflow = {
        "on": "push",
        "jobs": {"action": {"runs-on": "ubuntu-latest", "steps": steps}},
    }
    wf_file = tmp_path / ".github" / "workflows" / "action.yml"
    wf_file.parent.mkdir(parents=True)
    wf_file.write_text(yaml.safe_dump(workflow), encoding="utf-8")
    assert scan(tmp_path, only=["GA001", "GA002"]) == []


def test_run_scripts_have_no_expressions() -> None:
    bad = run_scripts_with_expressions(load_action()["runs"]["steps"])
    assert not bad, (
        f"run: script in step(s) {bad} contains a ${{{{ }}}} expression; "
        "pass it through env: instead"
    )


def test_expression_check_catches_injection() -> None:
    steps = [
        {"name": "ok", "run": 'echo "$X"'},
        {"name": "bad", "run": "echo ${{ inputs.path }}"},
    ]
    assert run_scripts_with_expressions(steps) == ["bad"]
