from pathlib import Path

import pytest
import yaml

from patchlint.core.registry import RULES, rule
from patchlint.core.runner import file_kind, scan
from patchlint.parsers.github_actions import YList, YMap, iter_steps, parse


def test_parser_keeps_line_numbers_and_on_key() -> None:
    wf = parse("on: push\njobs:\n  a:\n    steps:\n      - run: x\n      - uses: y@v1\n")
    assert isinstance(wf, YMap)
    assert "on" in wf and wf.key_lines["jobs"] == 2
    steps = [s for _, s in iter_steps(wf)]
    assert isinstance(wf["jobs"]["a"]["steps"], YList)
    assert [s.line for s in steps] == [5, 6]
    assert steps[1].key_lines["uses"] == 6


def test_parser_rejects_unsafe_tags() -> None:
    with pytest.raises(yaml.YAMLError):
        parse("x: !!python/object/apply:os.system ['echo hi']\n")


def test_non_mapping_yaml_is_ignored() -> None:
    assert parse("- just\n- a list\n") is None


def test_file_kind_detection() -> None:
    assert file_kind(Path("repo/.github/workflows/ci.yml")) == "workflow"
    assert file_kind(Path("repo/config/app.yml")) is None
    assert file_kind(Path("repo/config/app.yml"), explicit=True) == "workflow"
    assert file_kind(Path("repo/Dockerfile")) == "dockerfile"
    assert file_kind(Path("repo/Dockerfile.prod")) == "dockerfile"
    assert file_kind(Path("repo/api.dockerfile")) == "dockerfile"
    # Source files *about* Dockerfiles are not Dockerfiles.
    assert file_kind(Path("src/parsers/dockerfile.py")) is None
    assert file_kind(Path("docs/Dockerfile.md")) is None
    # Composite actions are recognised by name anywhere, in any case.
    assert file_kind(Path("repo/action.yml")) == "action"
    assert file_kind(Path("repo/sub/Action.YAML")) == "action"
    assert file_kind(Path("repo/action.yml"), explicit=True) == "action"
    assert file_kind(Path("repo/.github/workflows/action.yml")) == "workflow"


def test_ga002_points_at_the_injected_line(tmp_path: Path) -> None:
    wf = tmp_path / "wf.yml"
    wf.write_text(
        "on: issues\njobs:\n  t:\n    steps:\n      - run: |\n"
        "          echo ok\n          echo ${{ github.event.issue.body }}\n",
        encoding="utf-8",
    )
    (finding,) = scan(wf, only=["GA002"])
    assert finding.line == 7


def test_invalid_yaml_is_skipped_with_warning(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    wf = tmp_path / "broken.yml"
    wf.write_text("jobs: [unclosed\n", encoding="utf-8")
    assert scan(wf) == []
    assert "invalid YAML" in capsys.readouterr().err


def test_directory_scan_finds_workflows(tmp_path: Path) -> None:
    wf_dir = tmp_path / ".github" / "workflows"
    wf_dir.mkdir(parents=True)
    (wf_dir / "ci.yml").write_text(
        "on: push\njobs:\n  b:\n    steps:\n      - uses: actions/checkout@v4\n", encoding="utf-8"
    )
    (tmp_path / "other.yml").write_text("uses: not/a-workflow@v1\n", encoding="utf-8")
    assert [f.rule_id for f in scan(tmp_path, only=["GA001"])] == ["GA001"]


def test_iter_steps_covers_composite_action_steps() -> None:
    doc = parse("runs:\n  using: composite\n  steps:\n    - run: a\n    - uses: b@v1\n")
    assert doc is not None
    steps = list(iter_steps(doc))
    assert [job_id for job_id, _ in steps] == ["", ""]
    assert [s.line for _, s in steps] == [4, 5]


WORKFLOW_ONLY_ACTION = """\
on: pull_request_target
jobs:
  call:
    uses: other/repo/.github/workflows/x.yml@0123456789abcdef0123456789abcdef01234567
    secrets: inherit
runs:
  using: composite
  steps:
    - uses: actions/checkout@0123456789abcdef0123456789abcdef01234567
      with:
        ref: ${{ github.event.pull_request.head.sha }}
"""


def test_workflow_only_rules_skip_actions(tmp_path: Path) -> None:
    ids = ["GA003", "GA004", "GA008"]
    # Sanity check: the same text does trip them as a workflow.
    wf = tmp_path / "wf.yml"
    wf.write_text(WORKFLOW_ONLY_ACTION, encoding="utf-8")
    assert {f.rule_id for f in scan(wf, only=ids)} == set(ids)
    action_dir = tmp_path / "pkg"
    action_dir.mkdir()
    (action_dir / "action.yml").write_text(WORKFLOW_ONLY_ACTION, encoding="utf-8")
    assert scan(action_dir, only=ids) == []


def test_non_composite_action_has_no_findings(tmp_path: Path) -> None:
    (tmp_path / "action.yml").write_text(
        "name: x\ndescription: y\nruns:\n  using: node20\n  main: index.js\n", encoding="utf-8"
    )
    assert scan(tmp_path) == []


def test_action_inputs_are_untrusted_only_in_actions(tmp_path: Path) -> None:
    body = 'echo "${{ inputs.x }}"'
    wf = tmp_path / "wf.yml"
    wf.write_text(
        f"on: workflow_dispatch\njobs:\n  a:\n    steps:\n      - run: {body}\n", encoding="utf-8"
    )
    assert scan(wf, only=["GA002"]) == []
    action = tmp_path / "action.yml"
    action.write_text(
        f"runs:\n  using: composite\n  steps:\n    - run: {body}\n      shell: bash\n",
        encoding="utf-8",
    )
    (finding,) = scan(action, only=["GA002"])
    assert finding.line == 4 and "inputs.x" in finding.message


def test_rule_rejects_unknown_extra_filetype() -> None:
    before = set(RULES)
    with pytest.raises(ValueError, match="extra_filetypes"):
        rule("GA999", "t", "low", extra_filetypes=("nope",))
    assert set(RULES) == before
