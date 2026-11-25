import json
from pathlib import Path

import pytest

from patchlint.cli import main
from patchlint.core.model import Finding
from patchlint.core.registry import load_rules
from patchlint.sarif import to_sarif, to_uri

FIXTURES = Path(__file__).parent / "fixtures"


def finding(rule_id: str, severity: str, path: str, line: int = 3) -> Finding:
    return Finding(rule_id, severity, "Something is wrong.", path, line, "Do this.")


def test_log_shape_and_rule_metadata() -> None:
    rules = load_rules()
    log = to_sarif([finding("GA002", "high", "wf.yml")], rules, base=Path.cwd())
    assert log["version"] == "2.1.0" and log["$schema"].endswith("sarif-2.1.0.json")
    run = log["runs"][0]
    driver = run["tool"]["driver"]
    assert driver["name"] == "patchlint"
    ids = [r["id"] for r in driver["rules"]]
    assert ids == sorted(rules)
    ga002 = driver["rules"][ids.index("GA002")]
    assert "external/cwe/cwe-78" in ga002["properties"]["tags"]
    assert ga002["properties"]["security-severity"] == "8.0"
    assert ga002["defaultConfiguration"]["level"] == "error"
    assert "Why it matters" in ga002["help"]["text"]


def test_result_points_at_rule_file_and_line() -> None:
    rules = load_rules()
    (result,) = to_sarif([finding("DL002", "medium", "app/Dockerfile", 7)], rules)["runs"][0][
        "results"
    ]
    ids = sorted(rules)
    assert result["ruleId"] == "DL002" and result["ruleIndex"] == ids.index("DL002")
    assert result["level"] == "warning"
    assert result["message"]["text"] == "Something is wrong. Fix: Do this."
    loc = result["locations"][0]["physicalLocation"]
    assert loc["artifactLocation"]["uri"] == "app/Dockerfile"
    assert loc["region"]["startLine"] == 7


@pytest.mark.parametrize(
    ("path", "expected"),
    [(str(Path("a") / "b" / "Dockerfile"), "a/b/Dockerfile"), ("Dockerfile", "Dockerfile")],
)
def test_uri_uses_forward_slashes_on_every_os(path: str, expected: str) -> None:
    # str(Path(...)) uses backslashes on Windows; SARIF URIs must not.
    assert to_uri(path, Path.cwd()) == expected


def test_absolute_path_is_made_relative(tmp_path: Path) -> None:
    assert to_uri(str(tmp_path / "x" / "Dockerfile"), tmp_path) == "x/Dockerfile"


def test_no_findings_gives_empty_results() -> None:
    assert to_sarif([], load_rules())["runs"][0]["results"] == []


def test_cli_sarif_to_file_with_exit_zero(tmp_path: Path) -> None:
    out = tmp_path / "report.sarif"
    bad = FIXTURES / "GA001" / "bad" / "workflow.yml"
    assert main(["scan", str(bad), "--format", "sarif", "-o", str(out), "--exit-zero"]) == 0
    log = json.loads(out.read_text(encoding="utf-8"))
    assert [r["ruleId"] for r in log["runs"][0]["results"]] == ["GA001"]
    # Without --exit-zero, findings still fail the run.
    assert main(["scan", str(bad), "--format", "sarif", "-o", str(out)]) == 1


def test_cli_text_output_unchanged(capsys) -> None:  # type: ignore[no-untyped-def]
    assert main(["scan", str(FIXTURES / "DL002" / "good" / "Dockerfile")]) == 0
    assert capsys.readouterr().out.strip() == "0 finding(s)"
