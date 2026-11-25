"""Rule plugins: packages that add rules through the `patchlint.rules` entry point."""

from collections.abc import Callable, Iterable, Iterator
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from patchlint.cli import main
from patchlint.core import registry
from patchlint.core.model import Context, Finding
from patchlint.core.registry import load_rules, rule
from patchlint.core.runner import scan


class FakeEntryPoint:
    def __init__(self, name: str, loader: Callable[[], None], dist: str | None = None) -> None:
        self.name = name
        self._loader = loader
        self.dist = SimpleNamespace(name=dist) if dist else None

    def load(self) -> None:
        self._loader()


@pytest.fixture
def plugins(monkeypatch: pytest.MonkeyPatch) -> Iterator[Callable[..., None]]:
    """Install fake plugins for one test, then restore the registry."""
    load_rules()  # built-ins first
    saved = dict(registry.RULES)

    def install(*eps: Any) -> None:
        monkeypatch.setattr(registry, "_plugin_entry_points", lambda: list(eps))
        monkeypatch.setattr(registry, "_plugins_loaded", False)

    yield install
    registry.RULES.clear()
    registry.RULES.update(saved)
    registry._plugins_loaded = True


def acme_rules() -> None:
    @rule(id="DL-acme-1", title="No EXPOSE 8080", severity="low")
    def check(ctx: Context) -> Iterable[Finding]:
        """Flags EXPOSE 8080.

        Why it matters: example plugin rule.

        Fix: use another port.
        """
        for ins in ctx.instructions:
            if ins.cmd == "EXPOSE" and "8080" in ins.args:
                yield ctx.finding(ins.line, "Port 8080 exposed.", "Use another port.")


def test_plugin_rules_load_and_run(plugins: Callable[..., None], tmp_path: Path) -> None:
    plugins(FakeEntryPoint("acme", acme_rules, dist="acme-patchlint-rules"))
    rules = load_rules()
    assert rules["DL-acme-1"].origin == "acme-patchlint-rules"
    assert rules["DL001"].origin == "patchlint"
    dockerfile = tmp_path / "Dockerfile"
    dockerfile.write_text("FROM python:3.12-slim\nUSER app\nEXPOSE 8080\n", encoding="utf-8")
    assert [f.rule_id for f in scan(dockerfile)] == ["DL-acme-1"]


def test_list_rules_marks_plugin_rules(
    plugins: Callable[..., None], capsys: pytest.CaptureFixture[str]
) -> None:
    plugins(FakeEntryPoint("acme", acme_rules, dist="acme-patchlint-rules"))
    assert main(["list-rules"]) == 0
    out = capsys.readouterr().out
    assert "DL-acme-1" in out and "[plugin: acme-patchlint-rules]" in out


def test_broken_plugin_is_skipped_with_warning(
    plugins: Callable[..., None], capsys: pytest.CaptureFixture[str]
) -> None:
    def broken() -> None:
        @rule(id="DL-broken-1", title="Half registered", severity="low")
        def check(ctx: Context) -> Iterable[Finding]:
            return []

        raise ImportError("missing dependency")

    plugins(FakeEntryPoint("broken", broken), FakeEntryPoint("acme", acme_rules))
    rules = load_rules()
    assert "DL-broken-1" not in rules  # no half-loaded plugin
    assert "DL-acme-1" in rules  # other plugins still load
    assert "rule plugin 'broken' failed to load: missing dependency" in capsys.readouterr().err


def test_plugin_cannot_replace_a_builtin_rule(
    plugins: Callable[..., None], capsys: pytest.CaptureFixture[str]
) -> None:
    def hijack() -> None:
        @rule(id="DL001", title="Fake", severity="low")
        def check(ctx: Context) -> Iterable[Finding]:
            return []

    plugins(FakeEntryPoint("hijack", hijack))
    rules = load_rules()
    assert rules["DL001"].title == "Container runs as root"
    assert rules["DL001"].origin == "patchlint"
    assert "duplicate rule id DL001" in capsys.readouterr().err
