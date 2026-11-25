"""Fixture-driven tests: adding a rule needs no test code.

For every rule, the single file in tests/fixtures/<RULE_ID>/bad/ must trigger it
and the single file in tests/fixtures/<RULE_ID>/good/ must not.
"""

from pathlib import Path

import pytest

from patchlint.core.registry import load_rules
from patchlint.core.runner import scan

FIXTURES = Path(__file__).parent / "fixtures"
RULE_IDS = sorted(load_rules())


def fixture_file(rule_id: str, variant: str) -> Path:
    folder = FIXTURES / rule_id / variant
    files = [p for p in folder.iterdir() if p.is_file()] if folder.is_dir() else []
    assert len(files) == 1, f"{folder} must contain exactly one file"
    return files[0]


@pytest.mark.parametrize("rule_id", RULE_IDS)
def test_bad_fixture_triggers_rule(rule_id: str) -> None:
    findings = scan(fixture_file(rule_id, "bad"), only=[rule_id])
    assert any(f.rule_id == rule_id for f in findings)


@pytest.mark.parametrize("rule_id", RULE_IDS)
def test_good_fixture_is_clean(rule_id: str) -> None:
    assert scan(fixture_file(rule_id, "good"), only=[rule_id]) == []


@pytest.mark.parametrize("rule_id", RULE_IDS)
def test_rule_is_documented(rule_id: str) -> None:
    doc = load_rules()[rule_id].doc
    assert "Why it matters" in doc and "Fix" in doc
