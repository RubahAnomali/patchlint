from pathlib import Path

import pytest

from patchlint.cli import main
from patchlint.config import Config, ConfigError, find_config, load_config, parse_config
from patchlint.core.registry import load_rules
from patchlint.core.runner import scan

RULES = set(load_rules())
UNPINNED = "on: push\npermissions: read-all\njobs:\n  b:\n    steps:\n      - uses: a/b@v1\n"


def make_repo(tmp_path: Path, config: str | None = None, name: str = ".patchlint.toml") -> Path:
    wf = tmp_path / ".github" / "workflows"
    wf.mkdir(parents=True)
    (wf / "ci.yml").write_text(UNPINNED, encoding="utf-8")
    (tmp_path / "Dockerfile").write_text("FROM python:latest\nUSER app\n", encoding="utf-8")
    if config is not None:
        (tmp_path / name).write_text(config, encoding="utf-8")
    return tmp_path


def rule_ids(root: Path, config: Config | None = None) -> list[str]:
    return sorted(f.rule_id for f in scan(root, config=config))


def test_no_config_finds_everything(tmp_path: Path) -> None:
    assert rule_ids(make_repo(tmp_path)) == ["DL002", "GA001"]


def test_disable_turns_a_rule_off(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    assert rule_ids(root, parse_config({"disable": ["ga001"]}, RULES)) == ["DL002"]


def test_only_wins_over_disable(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    config = parse_config({"disable": ["GA001"]}, RULES)
    assert [f.rule_id for f in scan(root, only=["GA001"], config=config)] == ["GA001"]


def test_exclude_skips_matching_paths(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    assert rule_ids(root, parse_config({"exclude": [".github/*"]}, RULES)) == ["DL002"]


def test_severity_override(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    config = parse_config({"severity": {"GA001": "high"}}, RULES)
    (ga001,) = [f for f in scan(root, config=config) if f.rule_id == "GA001"]
    assert ga001.severity == "high"


@pytest.mark.parametrize(
    ("data", "message"),
    [
        ({"disabled": ["GA001"]}, "unknown key"),
        ({"disable": "GA001"}, "must be a list"),
        ({"disable": ["XX999"]}, "unknown rule id"),
        ({"severity": {"GA001": "critical"}}, "must be one of"),
        ({"severity": {"ZZ001": "high"}}, "unknown rule id"),
        ({"severity": ["GA001"]}, "must be a table"),
    ],
)
def test_invalid_config_is_rejected_clearly(data: dict, message: str) -> None:  # type: ignore[type-arg]
    with pytest.raises(ConfigError, match=message):
        parse_config(data, RULES)


def test_find_config_prefers_dotfile_then_pyproject(tmp_path: Path) -> None:
    assert find_config(tmp_path) is None
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'x'\n", encoding="utf-8")
    assert find_config(tmp_path) is None  # no [tool.patchlint] table
    (tmp_path / "pyproject.toml").write_text("[tool.patchlint]\ndisable = []\n", encoding="utf-8")
    assert find_config(tmp_path) == tmp_path / "pyproject.toml"
    (tmp_path / ".patchlint.toml").write_text("", encoding="utf-8")
    assert find_config(tmp_path) == tmp_path / ".patchlint.toml"


def test_load_from_pyproject(tmp_path: Path) -> None:
    path = tmp_path / "pyproject.toml"
    path.write_text('[tool.patchlint]\ndisable = ["DL002"]\n', encoding="utf-8")
    assert load_config(path, RULES).disable == {"DL002"}


def test_invalid_toml_is_a_config_error(tmp_path: Path) -> None:
    path = tmp_path / ".patchlint.toml"
    path.write_text("disable = [\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="invalid TOML"):
        load_config(path, RULES)


def test_cli_uses_config_in_scanned_folder(tmp_path: Path) -> None:
    root = make_repo(tmp_path, 'disable = ["DL002", "GA001"]\n')
    assert main(["scan", str(root)]) == 0
    assert main(["scan", str(root), "--no-config"]) == 1


def test_cli_explicit_config_and_errors(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    root = make_repo(tmp_path)
    good = tmp_path / "custom.toml"
    good.write_text('exclude = ["*"]\n', encoding="utf-8")
    assert main(["scan", str(root), "--config", str(good)]) == 0
    bad = tmp_path / "bad.toml"
    bad.write_text('disable = ["NOPE01"]\n', encoding="utf-8")
    assert main(["scan", str(root), "--config", str(bad)]) == 2
    assert "unknown rule id" in capsys.readouterr().err
    assert main(["scan", str(root), "--rule", "NOPE01"]) == 2
