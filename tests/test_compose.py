from pathlib import Path

import pytest

from patchlint.cli import main
from patchlint.core.runner import file_kind, scan
from patchlint.parsers.compose import iter_services, volume_sources
from patchlint.parsers.github_actions import parse

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.mark.parametrize(
    "name",
    ["compose.yml", "compose.yaml", "docker-compose.yml", "docker-compose.prod.yaml",
     "compose.override.yml", "Docker-Compose.YML"],
)
def test_compose_files_are_detected_anywhere(name: str) -> None:
    assert file_kind(Path("any/folder") / name) == "compose"


@pytest.mark.parametrize("name", ["composer.yml", "my-compose.yml", "compose.json"])
def test_other_files_are_not_compose(name: str) -> None:
    assert file_kind(Path("any/folder") / name) != "compose"


def test_volume_sources_short_long_and_windows() -> None:
    doc = parse(
        "services:\n  a:\n    volumes:\n"
        "      - /var/run/docker.sock:/var/run/docker.sock:ro\n"
        "      - C:\\data:/data\n"
        "      - named_volume_only\n"
        "      - type: bind\n        source: ./src\n        target: /app\n"
    )
    assert doc is not None
    (_, service), = iter_services(doc)
    assert list(volume_sources(service)) == ["/var/run/docker.sock", "C:\\data", "./src"]


def test_dc002_flags_short_and_long_syntax_on_the_right_lines() -> None:
    findings = scan(FIXTURES / "DC002" / "bad" / "compose.yml", only=["DC002"])
    assert [(f.line, "dashboard" in f.message) for f in findings] == [(6, True), (11, False)]


def test_dc001_points_at_privileged_line() -> None:
    (finding,) = scan(FIXTURES / "DC001" / "bad" / "compose.yml", only=["DC001"])
    assert finding.line == 4


def test_directory_scan_finds_compose_files(tmp_path: Path) -> None:
    (tmp_path / "deploy").mkdir()
    (tmp_path / "deploy" / "docker-compose.prod.yml").write_text(
        "services:\n  x:\n    image: a:1\n    privileged: true\n", encoding="utf-8"
    )
    assert [f.rule_id for f in scan(tmp_path)] == ["DC001"]


def test_new_compose_rule_scaffold(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.chdir(tmp_path)
    assert main(["new-rule", "DC999", "demo_rule"]) == 0
    rule_file = tmp_path / "src/patchlint/rules/compose/DC999_demo_rule.py"
    assert "iter_services" in rule_file.read_text(encoding="utf-8")
    assert (tmp_path / "tests/fixtures/DC999/good/compose.yml").is_file()
