from pathlib import Path

from patchlint.cli import main
from patchlint.parsers.dockerfile import parse


def test_parser_joins_continuations_and_skips_comments() -> None:
    ins = parse("# c\nFROM a:1\nRUN x \\\n  && y\n")
    assert [(i.line, i.cmd, i.args) for i in ins] == [(2, "FROM", "a:1"), (3, "RUN", "x && y")]


def test_cli_exit_codes(tmp_path: Path) -> None:
    bad = tmp_path / "Dockerfile"
    bad.write_text("FROM python:latest\n", encoding="utf-8")
    assert main(["scan", str(bad)]) == 1
    bad.write_text(
        "FROM python:3.12-slim\nUSER app\nHEALTHCHECK CMD true\n", encoding="utf-8"
    )
    assert main(["scan", str(bad)]) == 0


def test_new_rule_scaffold(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.chdir(tmp_path)
    assert main(["new-rule", "DL999", "demo_rule"]) == 0
    assert (tmp_path / "src/patchlint/rules/dockerfile/DL999_demo_rule.py").is_file()
    assert (tmp_path / "tests/fixtures/DL999/bad/Dockerfile").is_file()
    assert main(["new-rule", "bad-id", "x"]) == 2


def test_new_workflow_rule_scaffold(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.chdir(tmp_path)
    assert main(["new-rule", "GA999", "demo_rule"]) == 0
    rule_file = tmp_path / "src/patchlint/rules/github_actions/GA999_demo_rule.py"
    assert "iter_steps" in rule_file.read_text(encoding="utf-8")
    assert (tmp_path / "tests/fixtures/GA999/bad/workflow.yml").is_file()
