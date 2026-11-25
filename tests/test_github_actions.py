from pathlib import Path

import pytest
import yaml

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
    assert [f.rule_id for f in scan(tmp_path)] == ["GA001"]
