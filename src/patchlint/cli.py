"""Command-line interface."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from patchlint import __version__
from patchlint.config import Config, ConfigError, find_config, load_config
from patchlint.core.registry import load_rules
from patchlint.core.runner import scan
from patchlint.sarif import to_sarif
from patchlint.scaffold import new_rule


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="patchlint", description=__doc__)
    p.add_argument("--version", action="version", version=__version__)
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("scan", help="scan a file or directory")
    s.add_argument("path", type=Path, nargs="?", default=Path("."))
    s.add_argument("--format", choices=["text", "json", "sarif"], default="text")
    s.add_argument("--rule", action="append", help="only run this rule id (repeatable)")
    s.add_argument("-o", "--output", type=Path, help="write results to this file, not stdout")
    cfg = s.add_mutually_exclusive_group()
    cfg.add_argument(
        "--config", type=Path, help="config file (default: .patchlint.toml or pyproject.toml)"
    )
    cfg.add_argument("--no-config", action="store_true", help="ignore any config file")
    s.add_argument(
        "--exit-zero",
        action="store_true",
        help="exit 0 even when there are findings (e.g. before uploading SARIF)",
    )

    sub.add_parser("list-rules", help="list all rules")

    e = sub.add_parser("explain", help="show why a rule exists and how to fix it")
    e.add_argument("rule_id")

    n = sub.add_parser("new-rule", help="scaffold a new rule and its fixtures")
    n.add_argument("rule_id", help="e.g. DL003")
    n.add_argument("name", help="lower_snake_case, e.g. add_instead_of_copy")

    args = p.parse_args(argv)

    if args.cmd == "list-rules":
        for r in load_rules().values():
            print(f"{r.id}  {r.severity:<6}  {r.title}")
        return 0

    if args.cmd == "explain":
        found = load_rules().get(args.rule_id.upper())
        if found is None:
            print(f"unknown rule {args.rule_id}", file=sys.stderr)
            return 2
        cwe = f" (CWE-{found.cwe})" if found.cwe else ""
        print(f"{found.id}: {found.title}{cwe}\nSeverity: {found.severity}\n\n{found.doc}")
        return 0

    if args.cmd == "new-rule":
        try:
            created = new_rule(args.rule_id.upper(), args.name, Path.cwd())
        except (ValueError, FileExistsError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        for path in created:
            print(f"created {path}")
        return 0

    rules = load_rules()
    if args.rule:
        unknown = sorted({r.upper() for r in args.rule} - set(rules))
        if unknown:
            print(f"error: unknown rule id(s): {unknown}", file=sys.stderr)
            return 2
    config = Config()
    if not args.no_config:
        config_path = args.config or find_config(args.path)
        if config_path is not None:
            try:
                config = load_config(config_path, rules)
            except (ConfigError, OSError) as exc:
                print(f"error: {exc}", file=sys.stderr)
                return 2
    only = [r.upper() for r in args.rule] if args.rule else None
    findings = scan(args.path, only, config)
    if args.format == "json":
        report = json.dumps([asdict(f) for f in findings], indent=2)
    elif args.format == "sarif":
        report = json.dumps(to_sarif(findings, rules), indent=2)
    else:
        lines = [
            f"{f.path}:{f.line}: [{f.rule_id}/{f.severity}] {f.message}\n    fix: {f.fix}"
            for f in findings
        ]
        report = "\n".join([*lines, f"\n{len(findings)} finding(s)"])
    if args.output:
        args.output.write_text(report + "\n", encoding="utf-8")
        print(f"wrote {len(findings)} finding(s) to {args.output}", file=sys.stderr)
    else:
        print(report)
    return 1 if findings and not args.exit_zero else 0


if __name__ == "__main__":
    raise SystemExit(main())
