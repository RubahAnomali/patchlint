"""Fixture-driven tests: adding a rule needs no test code.

For every rule, tests/fixtures/<RULE_ID>/bad/Dockerfile must trigger it and
tests/fixtures/<RULE_ID>/good/Dockerfile must not.
"""

from pathlib import Path

import pytest

from patchlint.core.registry import load_rules
from patchlint.core.runner import scan

FIXTURES = Path(__file__).parent / "fixtures"
RULE_IDS = sorted(load_rules())


@pytest.mark.parametrize("rule_id", RULE_IDS)
def test_rule_has_fixtures(rule_id: str) -> None:
    assert (FIXTURES / rule_id / "bad/Dockerfile").is_file(), "missing bad fixture"
    assert (FIXTURES / rule_id / "good/Dockerfile").is_file(), "missing good fixture"


@pytest.mark.parametrize("rule_id", RULE_IDS)
def test_bad_fixture_triggers_rule(rule_id: str) -> None:
    findings = scan(FIXTURES / rule_id / "bad/Dockerfile", only=[rule_id])
    assert any(f.rule_id == rule_id for f in findings)


@pytest.mark.parametrize("rule_id", RULE_IDS)
def test_good_fixture_is_clean(rule_id: str) -> None:
    assert scan(FIXTURES / rule_id / "good/Dockerfile", only=[rule_id]) == []


@pytest.mark.parametrize("rule_id", RULE_IDS)
def test_rule_is_documented(rule_id: str) -> None:
    doc = load_rules()[rule_id].doc
    assert "Why it matters" in doc and "Fix" in doc
