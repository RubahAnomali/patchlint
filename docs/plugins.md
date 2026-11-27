# Writing a rule plugin

Have rules that are specific to your company or project? Ship them as a separate Python package. patchlint loads them automatically, and they work with every output format and the config file.

## 1. Write rules as usual

```python
# acme_patchlint_rules/__init__.py
from collections.abc import Iterable

from patchlint.core.model import Context, Finding
from patchlint.core.registry import rule


@rule(id="DL-acme-1", title="Image not from the ACME registry", severity="medium")
def check(ctx: Context) -> Iterable[Finding]:
    """Base images must come from registry.acme.example.

    Why it matters: only images from our registry are scanned and patched.

    Fix: use `FROM registry.acme.example/...`.
    """
    for ins in ctx.instructions:
        if ins.cmd == "FROM" and not ins.args.startswith("registry.acme.example/"):
            yield ctx.finding(ins.line, "Image is not from the ACME registry.", "Use registry.acme.example.")
```

- The first two letters of the id pick the file type: `DL` Dockerfiles, `GA` GitHub Actions workflows, `DC` docker-compose files. A `GA` rule can also run on composite actions (`action.yml` / `action.yaml`) by passing `extra_filetypes=("action",)` to `@rule`; the document is then in `ctx.action`.
- **Use your own suffix after the prefix** (for example `DL-acme-1`) so your ids never clash with built-in rules like `DL001`.
- Same docstring rules as built-ins: say *why it matters* and *how to fix it*.

## 2. Register the module as an entry point

```toml
# pyproject.toml of your plugin package
[project]
name = "acme-patchlint-rules"
dependencies = ["patchlint>=0.2"]

[project.entry-points."patchlint.rules"]
acme = "acme_patchlint_rules"
```

## 3. Install and check

```bash
pip install -e .
patchlint list-rules        # your rules show "[plugin: acme-patchlint-rules]"
patchlint scan .
```

## Safety behaviour

- A plugin that fails to import prints a warning and is skipped; it never stops a scan.
- A plugin can't replace a built-in rule: a duplicate id is rejected with a warning, and none of that plugin's rules are kept.
- Plugins are ordinary Python packages and run with your permissions, so only install plugins you trust.

Turn plugin rules off like any other rule with `disable = ["DL-acme-1"]` in `.patchlint.toml`.
